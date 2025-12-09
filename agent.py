import warnings
import os
import logging

# Suppress warnings early, before other imports
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'  # Suppress Google logging
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*duckduckgo_search.*')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*ALTS.*')
warnings.filterwarnings('ignore', message='.*ALTS.*')

from openai import OpenAI

from knowledge_base import query_knowledge_base
import json

import google.generativeai as genai
from google.generativeai.types import content_types
from google.protobuf.json_format import MessageToDict
from collections import defaultdict

logger = logging.getLogger(__name__)

class PrimAgent:
    def __init__(self, api_key, base_url=None, model="gpt-3.5-turbo", provider="OpenAI"):
        self.provider = provider
        self.model_name = model
        
        # Tools definition for OpenAI - only knowledge base search
        self.openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "Recherche dans la base de connaissances de la documentation PrimLogix pour obtenir de l'aide sur les fonctionnalités du logiciel PRIM, les questions, les erreurs ou les procédures. Utilisez cet outil pour trouver des informations dans la documentation d'aide PrimLogix. Répondez toujours en français et citez les sources trouvées.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "La requête de recherche liée à la documentation PrimLogix."
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

        if self.provider == "Google Gemini":
            # Configure Gemini API
            genai.configure(api_key=api_key)
            
            # Define Gemini Tools using FunctionDeclaration - only knowledge base search
            self.gemini_tools = [
                genai.protos.Tool(
                    function_declarations=[
                        genai.protos.FunctionDeclaration(
                            name="search_knowledge_base",
                            description="Recherche dans la base de connaissances de la documentation PrimLogix pour obtenir de l'aide sur les fonctionnalités du logiciel PRIM, les questions, les erreurs ou les procédures. Utilisez cet outil pour trouver des informations dans la documentation d'aide PrimLogix. Répondez toujours en français et citez les sources trouvées.",
                            parameters=genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    "query": genai.protos.Schema(
                                        type=genai.protos.Type.STRING,
                                        description="La requête de recherche liée à la documentation PrimLogix."
                                    )
                                },
                                required=["query"]
                            )
                        )
                    ]
                )
            ]
            
            # Map for execution
            self.tool_map = {
                "search_knowledge_base": self._search_kb
            }

        else:
            self.client = OpenAI(api_key=api_key, base_url=base_url)


    def _search_kb(self, query):
        print(f"DEBUG: Searching KB for '{query}'")
        try:
            # Search with more results for better coverage
            results = query_knowledge_base(query, n_results=5)
            if not results['documents'] or not results['documents'][0]:
                 return "Aucune documentation pertinente trouvée dans la base de connaissances PrimLogix."
            
            docs = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results.get('distances', [None])[0] if results.get('distances') else [None] * len(docs)
            
            context = ""
            all_images = []  # Collect all images from results
            
            for i, doc in enumerate(docs):
                if not doc or not doc.strip():
                    continue
                    
                source = metadatas[i].get('url', 'URL inconnue') if i < len(metadatas) else 'URL inconnue'
                title = metadatas[i].get('title', 'Sans titre') if i < len(metadatas) else 'Sans titre'
                
                # Extract images from metadata
                images_json = metadatas[i].get('images', '') if i < len(metadatas) else ''
                if images_json:
                    try:
                        images = json.loads(images_json)
                        all_images.extend(images)
                    except:
                        pass
                
                # Add relevance info if available
                relevance = ""
                if distances and i < len(distances) and distances[i] is not None:
                    # Lower distance = more relevant, convert to percentage-like score
                    score = max(0, min(100, int((1 - distances[i]) * 100)))
                    if score > 50:  # Only show if reasonably relevant
                        relevance = f" [Pertinence: {score}%]"
                
                context += f"\n**Source: {title}**{relevance}\nURL: {source}\n\nContenu:\n{doc}\n\n---\n"
            
            if not context.strip():
                return "Aucune documentation pertinente trouvée dans la base de connaissances PrimLogix."
            
            # Add image information to response
            response_text = f"Résultats de la recherche dans la documentation PrimLogix:\n{context}"
            
            # Add image URLs at the end in a special format that can be parsed
            if all_images:
                # Remove duplicates while preserving order
                seen_urls = set()
                unique_images = []
                for img in all_images:
                    if img['url'] not in seen_urls:
                        seen_urls.add(img['url'])
                        unique_images.append(img)
                
                if unique_images:
                    image_section = "\n\n[SCREENSHOTS]\n"
                    for img in unique_images[:5]:  # Limit to 5 images
                        image_section += f"![{img.get('alt', 'Screenshot')}]({img['url']})\n"
                    response_text += image_section
            
            return response_text
        except Exception as e:
            logger.error(f"Error searching KB: {e}")
            return f"Erreur lors de la recherche dans la base de connaissances: {e}"


    def run(self, messages):
        if self.provider == "Google Gemini":
            return self._run_gemini(messages)
        else:
            return self._run_openai(messages)

    def _run_openai(self, messages):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=self.openai_tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            messages.append(message)
            
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                result_content = ""
                if function_name == "search_knowledge_base":
                    result_content = self._search_kb(arguments['query'])
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": result_content
                })
            
            final_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return final_response.choices[0].message.content
        
        return message.content

    def _run_gemini(self, messages):
        # Convert OpenAI messages to Gemini History
        history = []
        for msg in messages[:-1]:  # All but last
            role = msg.get('role')
            content = msg.get('content', '')
            
            # Skip tool messages in history for now (Gemini handles this differently)
            if role == 'tool':
                continue
                
            if role == 'user':
                history.append({'role': 'user', 'parts': [content]})
            elif role == 'assistant':
                history.append({'role': 'model', 'parts': [content]})
        
        last_msg = messages[-1]
        last_content = last_msg.get('content', '')
        
        def attempt_chat(params_model_name):
            model_auto = genai.GenerativeModel(
                model_name=params_model_name,
                tools=self.gemini_tools
            )
            chat_auto = model_auto.start_chat(history=history)
            
            # Send message and handle function calls manually
            response = chat_auto.send_message(last_content)
            
            # Handle function calls in a loop until we get a text response
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Check if response has function calls
                if hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        
                        # Check if any part is a function call
                        function_call_part = None
                        for part in parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                function_call_part = part
                                break
                        
                        if function_call_part:
                            function_call = function_call_part.function_call
                            function_name = function_call.name
                            
                            # Extract arguments
                            function_args = {}
                            if hasattr(function_call, 'args'):
                                # args is a Struct (protobuf), convert to dict
                                try:
                                    # Try MessageToDict first (works for most protobuf types)
                                    function_args = MessageToDict(function_call.args, preserving_proto_field_name=True)
                                except (AttributeError, TypeError) as e:
                                    # If that fails (e.g., MapComposite issue), try alternative methods
                                    try:
                                        # Method 1: Try dict() constructor if it's dict-like
                                        if isinstance(function_call.args, dict):
                                            function_args = function_call.args
                                        # Method 2: Try accessing as a mapping
                                        elif hasattr(function_call.args, 'keys'):
                                            function_args = {k: function_call.args[k] for k in function_call.args.keys()}
                                        # Method 3: Try __dict__ access
                                        elif hasattr(function_call.args, '__dict__'):
                                            function_args = {k: v for k, v in function_call.args.__dict__.items() 
                                                           if not k.startswith('_') and v is not None}
                                        # Method 4: Try direct attribute access for common fields
                                        else:
                                            # Try to get 'query' field directly
                                            if hasattr(function_call.args, 'query'):
                                                function_args['query'] = getattr(function_call.args, 'query')
                                            # Try other common field names
                                            for attr in ['text', 'input', 'message', 'prompt']:
                                                if hasattr(function_call.args, attr):
                                                    function_args['query'] = getattr(function_call.args, attr)
                                                    break
                                    except Exception as e2:
                                        # If all methods fail, log and use empty dict
                                        logger.warning(f"Could not extract function arguments: {e2}")
                                        function_args = {}
                            
                            # Execute the function
                            if function_name in self.tool_map:
                                # Handle query parameter
                                query = function_args.get('query', '')
                                function_result = self.tool_map[function_name](query)
                            else:
                                function_result = f"Unknown function: {function_name}"
                            
                            # Send function response back to Gemini
                            function_response = genai.protos.FunctionResponse(
                                name=function_name,
                                response={"result": str(function_result)}
                            )
                            response = chat_auto.send_message(
                                genai.protos.Part(function_response=function_response)
                            )
                            continue
                
                # No function call, return text response
                if hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            return ''.join(text_parts)
                
                # If we get here, something unexpected happened
                break
            
            return "Error: Could not get a valid response from Gemini after multiple iterations."

        # Try common Gemini model names in order of preference
        # Remove -latest suffix if present, as it's not a valid model name format
        base_model_name = self.model_name.replace("-latest", "").strip()
        
        # Standard model names to try (in order of preference)
        # Updated to use Gemini 2.x models which are currently available
        model_names_to_try = [
            base_model_name,  # Try the user's model name first (without -latest)
            "gemini-2.5-flash",  # Latest and fastest
            "gemini-2.5-pro",   # Latest and most capable
            "gemini-2.0-flash", # Stable 2.0 version
            "gemini-2.0-flash-exp", # Experimental
            "gemini-pro",  # Fallback to older model
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        model_names_to_try = [m for m in model_names_to_try if m not in seen and not seen.add(m)]
        
        last_error = None
        last_model_tried = None
        for model_name_to_try in model_names_to_try:
            last_model_tried = model_name_to_try
            try:
                return attempt_chat(model_name_to_try)
            except Exception as e:
                last_error = e
                error_str = str(e)
                # Check if it's a model not found error
                is_model_error = ("404" in error_str or 
                                 "not found" in error_str.lower() or 
                                 "is not found" in error_str.lower() or
                                 "not supported" in error_str.lower())
                
                if not is_model_error:
                    # If it's not a model not found error, don't try other models
                    return f"Gemini Error: {last_error}"
                # Continue to next model if it's a model not found error
                continue
        
        # If we get here, all models failed - try to list available models
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # Extract just the model name (remove 'models/' prefix if present)
                    model_name_clean = m.name.replace('models/', '')
                    available_models.append(model_name_clean)
            
            if available_models:
                available_models_str = ", ".join(available_models[:5])  # Show first 5
                return f"Gemini Error: Model '{last_model_tried}' not found. Last error: {last_error}. Available models: {available_models_str}. Please update the model name in the sidebar."
            else:
                return f"Gemini Error: Model '{last_model_tried}' not found. Last error: {last_error}. Please check your API key and try using 'gemini-1.5-flash', 'gemini-1.5-pro', or 'gemini-pro'."
        except Exception as list_error:
            return f"Gemini Error: Model '{last_model_tried}' not found. Last error: {last_error}. Could not list available models (error: {list_error}). Please check your API key and try using 'gemini-1.5-flash', 'gemini-1.5-pro', or 'gemini-pro'."
