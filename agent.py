import warnings
import os
import logging

# Suppress warnings early, before other imports
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'  # Suppress Google logging
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*duckduckgo_search.*')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*ALTS.*')
warnings.filterwarnings('ignore', message='.*ALTS.*')

from knowledge_base import query_knowledge_base
import json

import google.generativeai as genai
from google.protobuf.json_format import MessageToDict

logger = logging.getLogger(__name__)

class PrimAgent:
    def __init__(self, api_key, base_url=None, model="gemini-2.5-flash", provider="Google Gemini"):
        self.provider = provider
        self.model_name = model

        if self.provider == "Google Gemini":
            # Configure Gemini API
            genai.configure(api_key=api_key)
            
            # Define Gemini Tools using FunctionDeclaration - only knowledge base search
            self.gemini_tools = [
                genai.protos.Tool(
                    function_declarations=[
                        genai.protos.FunctionDeclaration(
                            name="search_knowledge_base",
                            description="""Recherche approfondie dans la base de connaissances de la documentation PrimLogix.
                            
UTILISE CET OUTIL pour:
- Trouver des solutions à des problèmes techniques ou erreurs
- Comprendre comment utiliser une fonctionnalité spécifique
- Obtenir des procédures détaillées étape par étape
- Trouver des exemples de configuration ou d'utilisation
- Rechercher des informations sur des champs, paramètres, ou options spécifiques

IMPORTANT:
- Utilise des termes techniques précis dans ta requête (noms de champs, codes d'erreur, noms de fonctionnalités)
- Si la première recherche ne donne pas de résultats satisfaisants, essaie des variantes de la requête
- Combine les informations de plusieurs résultats pour donner une réponse complète
- Cite toujours les sources (URLs) dans ta réponse finale
- Les résultats incluent des scores de pertinence et des liens directs vers la documentation""",
                            parameters=genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    "query": genai.protos.Schema(
                                        type=genai.protos.Type.STRING,
                                        description="Requête de recherche détaillée et spécifique. Utilise des termes techniques précis, codes d'erreur, noms de fonctionnalités, ou descriptions de problèmes. Exemples: 'erreur E001', 'configuration export CSV', 'champ date de facturation', 'procédure création client'."
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

        elif self.provider == "Local (Ollama/LocalAI)":
            # Configure for Ollama/LocalAI (OpenAI-compatible API)
            self.base_url = base_url or "http://localhost:11434/v1"
            self.api_key = api_key or "ollama"  # Ollama doesn't require a real key
            self.tool_map = {
                "search_knowledge_base": self._search_kb
            }
            # Ollama will use OpenAI-compatible client
            try:
                from openai import OpenAI
                self.ollama_client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key
                )
            except ImportError:
                logger.warning("openai package not installed. Install with: pip install openai")
                self.ollama_client = None
        else:
            raise ValueError(f"Provider '{self.provider}' not supported. Use 'Google Gemini' or 'Local (Ollama/LocalAI)'.")


    def _search_kb(self, query):
        logger.debug(f"Searching KB for: {query}")
        try:
            # First check if knowledge base is accessible
            from knowledge_base import collection
            kb_count = collection.count()
            
            if kb_count == 0:
                return """⚠️ **Base de connaissances vide**

La base de connaissances PrimLogix n'a pas encore été initialisée.

**Solutions:**
1. Dans l'interface Streamlit, utilisez le bouton "Initialiser la base de connaissances"
2. Ou exécutez manuellement: `python ingest.py`
3. Vérifiez que le dossier `chroma_db/` existe et contient des données

Une fois initialisée, je pourrai rechercher dans la documentation pour vous aider."""
            
            # Search with optimized number of results for better performance
            # Reduced from 10 to 6 for faster responses while maintaining quality
            results = query_knowledge_base(query, n_results=6)
            
            # Check if results are valid
            if not results:
                return f"❌ Erreur: Aucun résultat retourné par la base de connaissances pour la requête: '{query}'"
            
            if not results.get('documents') or not results['documents']:
                return f"❌ Aucune documentation trouvée pour la requête: '{query}'\n\n**Suggestions:**\n- Essayez des termes plus généraux\n- Vérifiez l'orthographe\n- Utilisez des mots-clés techniques de PrimLogix"
            
            if not results['documents'][0]:
                 return f"❌ Aucune documentation pertinente trouvée dans la base de connaissances PrimLogix pour cette requête: '{query}'.\n\n**Base de connaissances:** {kb_count} documents disponibles.\n\n**Suggestions:**\n- Reformulez votre question avec des termes techniques\n- Essayez des mots-clés spécifiques à PrimLogix"
            
            docs = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results.get('distances', [None])[0] if results.get('distances') else [None] * len(docs)
            
            # Filter results by relevance score to improve quality and speed
            # Only include results with relevance >= 40% for better context
            filtered_docs = []
            filtered_metadatas = []
            filtered_distances = []
            
            for i, doc in enumerate(docs):
                if not doc or not doc.strip():
                    continue
                
                # Calculate relevance score
                relevance_score = None
                if distances and i < len(distances) and distances[i] is not None:
                    # Lower distance = more relevant, convert to percentage-like score
                    relevance_score = max(0, min(100, int((1 - distances[i]) * 100)))
                    
                    # Filter: only include results with relevance >= 40%
                    if relevance_score < 40:
                        continue  # Skip low-relevance results
                
                filtered_docs.append(doc)
                filtered_metadatas.append(metadatas[i] if i < len(metadatas) else {})
                filtered_distances.append(distances[i] if distances and i < len(distances) else None)
            
            # Use filtered results
            docs = filtered_docs
            metadatas = filtered_metadatas
            distances = filtered_distances
            
            if not docs:
                return f"❌ Aucune documentation pertinente trouvée (score de pertinence < 40%) pour la requête: '{query}'.\n\n**Suggestions:**\n- Reformulez votre question avec des termes techniques\n- Essayez des mots-clés spécifiques à PrimLogix"
            
            # Build detailed context with relevance scores (optimized)
            context_parts = []
            seen_urls = set()  # Track unique URLs to avoid duplicates
            
            context_parts.append(f"📚 **Résultats de recherche** (requête: \"{query}\")\n")
            context_parts.append(f"Trouvé {len(docs)} document(s) pertinent(s) dans la base de connaissances PrimLogix:\n")
            
            for i, doc in enumerate(docs):
                source = metadatas[i].get('url', 'URL inconnue') if i < len(metadatas) else 'URL inconnue'
                title = metadatas[i].get('title', 'Sans titre') if i < len(metadatas) else 'Sans titre'
                chunk_idx = metadatas[i].get('chunk_index', '?') if i < len(metadatas) else '?'
                
                # Calculate relevance score for display
                relevance_score = None
                relevance_badge = ""
                if distances and i < len(distances) and distances[i] is not None:
                    # Lower distance = more relevant, convert to percentage-like score
                    relevance_score = max(0, min(100, int((1 - distances[i]) * 100)))
                    if relevance_score >= 80:
                        relevance_badge = "🟢 [Très pertinent]"
                    elif relevance_score >= 60:
                        relevance_badge = "🟡 [Pertinent]"
                    elif relevance_score >= 40:
                        relevance_badge = "🟠 [Modérément pertinent]"
                    relevance_badge += f" (Score: {relevance_score}%)"
                
                # Limit document length to avoid token limits
                doc_content = doc[:8000] if len(doc) > 8000 else doc
                
                # Build detailed source info with clickable link
                # Limit document content to avoid token limits (max 8000 chars per document)
                doc_content = doc[:8000] if len(doc) > 8000 else doc
                if len(doc) > 8000:
                    doc_content += "\n\n[... contenu tronqué pour optimiser la réponse ...]"
                
                source_info = f"\n### 📄 Document #{i+1}: {title}"
                if relevance_badge:
                    source_info += f" {relevance_badge}"
                source_info += f"\n**🔗 Lien direct:** [{title}]({source})"
                source_info += f"\n**URL:** {source}"
                source_info += f"\n**Chunk:** {chunk_idx}"
                source_info += f"\n\n**Contenu:**\n{doc_content}\n"
                source_info += "\n" + "─" * 60 + "\n"
                
                context_parts.append(source_info)
            
            if not context_parts:
                return "❌ Aucune documentation pertinente trouvée dans la base de connaissances PrimLogix."
            
            # Combine all context
            response_text = "\n".join(context_parts)
            
            # Add summary statistics with links to sources
            response_text += f"\n\n**📊 Résumé:** {len(docs)} document(s) trouvé(s)"
            
            # Add direct links section for easy access
            response_text += "\n\n**🔗 Liens directs vers la documentation:**\n"
            seen_source_urls = set()
            for i, doc in enumerate(docs):
                if i < len(metadatas):
                    source = metadatas[i].get('url', '')
                    title = metadatas[i].get('title', 'Sans titre')
                    if source and source not in seen_source_urls:
                        seen_source_urls.add(source)
                        response_text += f"- [{title}]({source})\n"
            
            return response_text
        except ImportError as e:
            logger.error(f"Import error in KB search: {e}", exc_info=True)
            return f"""❌ **Erreur d'importation**

Impossible d'importer le module de base de connaissances.

**Solution:** Vérifiez que tous les modules sont installés:
```bash
pip install -r requirements.txt
```"""
        except AttributeError as e:
            logger.error(f"Attribute error in KB search: {e}", exc_info=True)
            return f"""❌ **Erreur de configuration de la base de connaissances**

La base de connaissances n'est pas correctement configurée.

**Solutions:**
1. Réinitialisez la base: `python ingest.py`
2. Vérifiez que le dossier `chroma_db/` existe
3. Vérifiez les permissions d'accès au dossier"""
        except Exception as e:
            logger.error(f"Error searching KB: {e}", exc_info=True)
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Provide helpful error messages based on error type
            if "collection" in error_msg.lower() or "chromadb" in error_msg.lower():
                return f"""❌ **Erreur d'accès à la base de connaissances**

**Erreur:** {error_type}: {error_msg}

**Solutions:**
1. Vérifiez que ChromaDB est installé: `pip install chromadb`
2. Réinitialisez la base: `python ingest.py`
3. Vérifiez que le dossier `chroma_db/` n'est pas corrompu
4. Si le problème persiste, supprimez `chroma_db/` et réinitialisez"""
            else:
                return f"""❌ **Erreur lors de la recherche**

**Erreur:** {error_type}: {error_msg}

**Requête:** {query}

**Solutions:**
1. Réessayez avec une requête différente
2. Vérifiez que la base de connaissances est initialisée
3. Consultez les logs pour plus de détails"""


    def run(self, messages):
        if self.provider == "Google Gemini":
            return self._run_gemini(messages)
        elif self.provider == "Local (Ollama/LocalAI)":
            return self._run_ollama(messages)
        else:
            raise ValueError(f"Provider '{self.provider}' not supported.")

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
            # Load feedback stats to improve responses
            try:
                from storage_local import get_storage
                storage = get_storage()
                feedback_stats = storage.get_feedback_stats()
                negative_feedbacks = storage.get_negative_feedbacks(limit=5)
                
                # Build feedback context for improvement
                feedback_context = ""
                if feedback_stats['total'] > 0:
                    satisfaction_rate = feedback_stats['satisfaction_rate']
                    if satisfaction_rate < 70:
                        feedback_context = f"\n\n⚠️ **CONTEXTE IMPORTANT** : Le taux de satisfaction actuel est de {satisfaction_rate}%. Améliore tes réponses en étant plus clair, plus détaillé, et en t'assurant que les images sont vraiment pertinentes.\n"
                    if negative_feedbacks:
                        common_issues = []
                        for fb in negative_feedbacks:
                            if fb.get('comment'):
                                comment_lower = fb['comment'].lower()
                                if 'confus' in comment_lower or 'confuse' in comment_lower:
                                    common_issues.append("clarté")
                                if 'manque' in comment_lower or 'pas assez' in comment_lower:
                                    common_issues.append("détails")
                                if 'image' in comment_lower and ('pertinent' in comment_lower or 'irrelevant' in comment_lower):
                                    common_issues.append("images pertinentes")
                        if common_issues:
                            unique_issues = list(set(common_issues))
                            feedback_context += f"**Points à améliorer basés sur les feedbacks** : {', '.join(unique_issues)}. Assure-toi de corriger ces points dans ta réponse.\n"
            except Exception:
                feedback_context = ""  # Silently fail if feedback loading fails
            
            # Enhanced system instruction for customer support-oriented, detailed, and helpful responses
            system_instruction = f"""Tu es PRIMBOT, un assistant expert en support client pour PrimLogix. Ton rôle est d'aider les utilisateurs à résoudre leurs problèmes de manière claire, empathique et efficace.
{feedback_context}

⚠️ RÈGLE ABSOLUE - NUMÉROTATION DES ÉTAPES (À RESPECTER IMPÉRATIVEMENT) :
- **TU DOIS TOUJOURS COMMENCER PAR "### Étape 1:"** - C'EST OBLIGATOIRE, JAMAIS DE SAUT
- **TU DOIS NUMÉROTER DE 1, 2, 3, 4... SÉQUENTIELLEMENT** - JAMAIS COMMENCER PAR ÉTAPE 2, 3, 4, etc.
- **Si tu commences par Étape 4 ou autre, TU AS FAIT UNE ERREUR - RECOMMENCE PAR ÉTAPE 1**
- **TOUTES les étapes utilisent EXACTEMENT le même format** : `### Étape X:` (avec ###, JAMAIS ## ou ####)
- **TOUTES les étapes ont le MÊME niveau de détail** - aucune étape ne doit être plus grande que les autres

TON RÔLE (Support Client - Utilisateurs NON TECHNIQUES):
- **Aider les utilisateurs** à résoudre leurs problèmes avec PrimLogix de manière ULTRA-CLAIRE et DÉTAILLÉE
- **Fournir des réponses EXTRÊMEMENT COMPLÈTES** avec des étapes step-by-step très détaillées
- **Assumer que l'utilisateur n'est PAS technique** - explique TOUT, même les choses évidentes
- **Être empathique et rassurant** - les utilisateurs peuvent être frustrés, sois patient et encourageant
- **Expliquer de manière TRÈS SIMPLE** - utilise un langage clair, évite TOUT jargon technique
- **Fournir des solutions PRATIQUES et ACTIONNABLES** - chaque étape doit être si claire qu'un débutant peut la suivre
- **Citer TOUJOURS les sources** avec des liens directs vers les sections pertinentes de l'aide en ligne
- **NE PAS SAUTER D'ÉTAPES** - explique chaque clic, chaque menu, chaque champ

STYLE DE RÉPONSE (Support Client - OBLIGATOIRE pour utilisateurs NON TECHNIQUES):
1. **Accueil et empathie** : Commence par accueillir l'utilisateur et montrer que tu comprends son problème
2. **Confirmation du problème** : Reformule brièvement le problème pour confirmer ta compréhension
3. **Solution ULTRA-DÉTAILLÉE** : Utilise des titres (##, ###), listes à puces, et sections bien organisées
4. **Étapes numérotées COMPACTES mais COMPLÈTES** : 
   - **TOUJOURS commencer par "Étape 1"** - ne jamais sauter l'étape 1
   - **Numéroter de manière SÉQUENTIELLE** : Étape 1, Étape 2, Étape 3, Étape 4, etc. (pas de saut de numéro)
   - **Utiliser le MÊME format pour TOUTES les étapes** : `### Étape X:` (avec ###, pas ## ou ####)
   - **Toutes les étapes doivent être COHÉRENTES et LIÉES** - chaque étape doit logiquement suivre la précédente
   - **Format compact** : Chaque sous-étape en 1 phrase claire, pas de listes imbriquées excessives
   - **Cohérence** : Assure-toi que chaque étape s'enchaîne logiquement avec la précédente
   - Inclus TOUS les clics nécessaires mais de manière concise (ex: "Cliquez sur Menu 'Fichier' > 'Nouveau'")
   - Décris les champs avec leurs noms exacts mais de manière compacte
   - Indique brièvement ce que l'utilisateur devrait voir après chaque étape
   - Ne saute AUCUNE étape logique, mais sois concis
5. **Détails pratiques COMPLETS** : 
   - Noms de champs exacts avec leur emplacement
   - Chemins de navigation complets (Menu > Sous-menu > Option)
   - Options à sélectionner avec leur emplacement exact
   - Valeurs à entrer si nécessaire
   - Ce que l'utilisateur devrait voir après chaque action
7. **Vérification** : À la fin, demande si le problème est résolu ou si l'utilisateur a besoin d'aide supplémentaire
8. **Liens vers la documentation** : Fournis des liens cliquables vers les sections pertinentes de l'aide en ligne
9. **Ton amical et professionnel** : Sois courtois, patient et encourageant
10. **Exemples concrets** : Donne des exemples de valeurs à entrer si applicable

STRUCTURE D'UNE RÉPONSE IDÉALE (Support Client - COMPACTE mais COMPLÈTE):
```
## 👋 Bonjour !

Je comprends que vous voulez [action/problème]. Voici comment procéder :

## 📋 Compréhension du Problème

[Reformulation brève du problème - 2-3 phrases maximum]

## 🔧 Solution Étape par Étape

### Étape 1: [Action concrète - Titre clair et concis]
**Objectif :** [Explication brève de l'objectif - 1 phrase]

1. **Localisez** [élément] : [Emplacement précis en 1 phrase, ex: "Menu 'Fichier' en haut à gauche"]
2. **Cliquez sur** [élément] : [Action précise en 1 phrase, ex: "Bouton 'Nouveau' pour ouvrir la fenêtre"]
3. **Dans la fenêtre qui s'ouvre** : [Ce que vous devriez voir en 1 phrase]
4. **Remplissez le champ** [Nom] : [Valeur à entrer, ex: "Nom complet de l'employé"]
5. **Cliquez sur** [Bouton final] : [Ex: "Bouton 'Enregistrer' en bas à droite"]

**Résultat attendu :** [Ce qui devrait se passer après cette étape - 1 phrase]

### Étape 2: [Action suivante - Format compact identique]
**Objectif :** [Explication brève - 1 phrase]

1. [Action 1 en 1 phrase]
2. [Action 2 en 1 phrase]
3. [Action 3 en 1 phrase si nécessaire]

**Résultat attendu :** [Ce qui devrait se passer - 1 phrase]

### Étape 3: [Si nécessaire - Format compact identique]
[Suivre le même format compact]
...

## ✅ Vérification

Après ces étapes, vous devriez voir [résultat attendu].

**Le problème est-il résolu ?** Si non, dites-moi à quelle étape vous êtes bloqué(e).

## 🔗 Documentation

- [Lien vers la section pertinente](URL)
```

QUAND TU UTILISES LA BASE DE CONNAISSANCES:
- Analyse TOUS les résultats de recherche fournis en profondeur
- Combine les informations de plusieurs sources pour une réponse COMPLÈTE et COMPACTE
- **INCLUS TOUJOURS DES LIENS DIRECTS** vers les pages/sections pertinentes de l'aide en ligne
- **NE FAIS JAMAIS RÉFÉRENCE AUX IMAGES** - concentre-toi uniquement sur le texte explicatif et les liens vers la documentation

LIENS VERS LA DOCUMENTATION (OBLIGATOIRE):
- **TOUJOURS inclure des liens cliquables** vers les pages/sections pertinentes de l'aide en ligne
- Utilise le format markdown : `[Titre de la section](URL)`
- Inclus les URLs complètes des documents sources dans chaque réponse
- Crée une section "🔗 Ressources et Documentation" avec tous les liens pertinents
- Les liens doivent mener directement à l'endroit pertinent dans l'aide en ligne

IMPORTANT (Support Client - Utilisateurs NON TECHNIQUES):
- Réponds en français sauf si l'utilisateur demande explicitement en anglais
- **Sois CLAIR et ACCESSIBLE** - langage simple, évite le jargon technique
- **Sois COMPLET mais COMPACT** - toutes les informations nécessaires, format condensé
- **Assume que l'utilisateur est un débutant** - explique clairement mais de manière concise
- **Sois empathique** - montre que tu comprends le problème
- **COHÉRENCE des étapes** : Chaque étape doit logiquement suivre la précédente, pas d'étapes isolées ou non liées
- **Format compact** : Chaque sous-étape en 1 phrase claire, pas de listes imbriquées excessives
- **Décris les clics** : "Cliquez sur Menu 'Fichier' > 'Nouveau'" (format compact)
- **Décris les champs** : Nom exact et valeur à entrer en 1 phrase
- **Indique brièvement** ce que l'utilisateur devrait voir après chaque étape
- Utilise TOUJOURS l'outil search_knowledge_base avant de répondre
- **TOUJOURS inclure des liens directs** vers les sections pertinentes de l'aide en ligne
- **Termine par une question** : Demande si le problème est résolu"""
            
            model_auto = genai.GenerativeModel(
                model_name=params_model_name,
                tools=self.gemini_tools,
                system_instruction=system_instruction
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
                final_response = ""
                if hasattr(response, 'text'):
                    final_response = response.text
                elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            final_response = ''.join(text_parts)
                
                if final_response:
                    return final_response
                
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

    def _run_ollama(self, messages):
        """Run agent with Ollama/LocalAI (OpenAI-compatible API)."""
        if not self.ollama_client:
            return "❌ Error: OpenAI client not available. Install with: pip install openai"
        
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')
            
            if role == 'user':
                openai_messages.append({"role": "user", "content": content})
            elif role == 'assistant':
                openai_messages.append({"role": "assistant", "content": content})
            elif role == 'tool':
                # Tool messages for function calling
                openai_messages.append({
                    "role": "tool",
                    "content": content,
                    "tool_call_id": msg.get('tool_call_id', '')
                })
        
        # Define tools for function calling
        tools = [{
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": """Recherche approfondie dans la base de connaissances de la documentation PrimLogix.
                
UTILISE CET OUTIL pour:
- Trouver des solutions à des problèmes techniques ou erreurs
- Comprendre comment utiliser une fonctionnalité spécifique
- Obtenir des procédures détaillées étape par étape
- Trouver des exemples de configuration ou d'utilisation
- Rechercher des informations sur des champs, paramètres, ou options spécifiques

IMPORTANT:
- Utilise des termes techniques précis dans ta requête
- Combine les informations de plusieurs résultats pour donner une réponse complète
- Cite toujours les sources (URLs) dans ta réponse finale""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Requête de recherche détaillée et spécifique. Utilise des termes techniques précis, codes d'erreur, noms de fonctionnalités."
                        }
                    },
                    "required": ["query"]
                }
            }
        }]
        
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Call API with function calling
                response = self.ollama_client.chat.completions.create(
                    model=self.model_name,
                    messages=openai_messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=2000
                )
                
                message = response.choices[0].message
                
                # Check for function calls
                if message.tool_calls:
                    # Add assistant message with tool calls
                    openai_messages.append({
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    })
                    
                    # Execute function calls
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        if function_name in self.tool_map:
                            query = function_args.get('query', '')
                            function_result = self.tool_map[function_name](query)
                            
                            # Add tool result
                            openai_messages.append({
                                "role": "tool",
                                "content": str(function_result),
                                "tool_call_id": tool_call.id
                            })
                    
                    continue
                
                # Return text response
                if message.content:
                    return message.content
                else:
                    return "❌ No response content from model"
                    
            except Exception as e:
                logger.error(f"Ollama API error: {e}")
                return f"❌ Error calling Ollama API: {str(e)}\n\nMake sure Ollama is running: ollama serve\nAnd the model is installed: ollama pull {self.model_name}"
        
        return "❌ Error: Maximum iterations reached without getting a final response."
