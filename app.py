import streamlit as st
from agent import PrimAgent
from knowledge_base import collection
from storage_local import get_storage
import os
import json
from pathlib import Path

st.set_page_config(page_title="PrimLogix Debug Agent", layout="wide")

# Load Qdrant secrets from Streamlit (for Streamlit Cloud deployment)
# Only try to access secrets if they exist (to avoid errors in local development)
try:
    if hasattr(st, 'secrets'):
        # Check if secrets file exists by trying to access it safely
        try:
            if 'qdrant' in st.secrets:
                os.environ['USE_QDRANT'] = str(st.secrets['qdrant'].get('USE_QDRANT', 'false'))
                os.environ['QDRANT_URL'] = st.secrets['qdrant'].get('QDRANT_URL', '')
                os.environ['QDRANT_API_KEY'] = st.secrets['qdrant'].get('QDRANT_API_KEY', '')
        except Exception:
            # Secrets file doesn't exist, use environment variables or .env file instead
            pass
except Exception:
    # If secrets are not available, continue with environment variables
    pass

st.title("🤖 PrimLogix Debug Agent")

# Auto-initialize knowledge base if empty (only once per session)
if "kb_initialized" not in st.session_state:
    kb_count = collection.count()
    if kb_count == 0:
        # Try to initialize automatically in background
        st.session_state.kb_initialized = False
        st.session_state.kb_auto_init_attempted = False
    else:
        st.session_state.kb_initialized = True
        st.session_state.kb_auto_init_attempted = True

# Check if knowledge base is empty
kb_count = collection.count()
if kb_count == 0:
    st.warning("⚠️ **Base de connaissances vide** - Le bot ne peut pas rechercher dans la documentation PrimLogix.")
    
    # Auto-initialization option
    if not st.session_state.get("kb_auto_init_attempted", False):
        st.info("💡 **Initialisation automatique disponible** - Cliquez sur le bouton ci-dessous pour initialiser automatiquement la base de connaissances.")
    
    with st.expander("🔧 Initialiser la base de connaissances", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **Options d'initialisation :**
            
            1. **Automatique (Recommandé)** : Cliquez sur le bouton ci-dessous pour scraper et ingérer la documentation
            2. **Manuelle** : Incluez le dossier `chroma_db/` dans le repository GitHub
            """)
        
        if st.button("🚀 Lancer l'ingestion automatique de la documentation", type="primary", use_container_width=True):
            st.session_state.kb_auto_init_attempted = True
            with st.spinner("Scraping et ingestion en cours... Cela peut prendre 5-10 minutes. Veuillez patienter..."):
                try:
                    from scraper import run_scraper
                    from knowledge_base import add_documents
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("📥 Étape 1/2 : Scraping de la documentation PrimLogix...")
                    progress_bar.progress(30)
                    data = run_scraper()
                    
                    status_text.text(f"💾 Étape 2/2 : Ajout de {len(data)} pages à la base de connaissances...")
                    progress_bar.progress(70)
                    add_documents(data)
                    
                    progress_bar.progress(100)
                    final_count = collection.count()
                    status_text.text(f"✅ Terminé ! {final_count} documents chargés")
                    
                    st.success(f"✅ Base de connaissances initialisée avec {final_count} documents!")
                    st.session_state.kb_initialized = True
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'ingestion: {e}")
                    st.info("💡 **Alternative** : Vous pouvez inclure le dossier `chroma_db/` dans le repository GitHub pour éviter l'initialisation à chaque déploiement.")
else:
    st.sidebar.success(f"📚 Base de connaissances: {kb_count} documents")
    
    # Afficher le nombre de conversations sauvegardées et statistiques de feedback
    try:
        storage = get_storage()
        conv_count = storage.count()
        if conv_count > 0:
            st.sidebar.info(f"💬 Conversations sauvegardées: {conv_count}")
        
        # Afficher les statistiques de feedback
        feedback_stats = storage.get_feedback_stats()
        if feedback_stats['total'] > 0:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 📊 Feedback")
            st.sidebar.metric("👍 Utile", feedback_stats['thumbs_up'])
            st.sidebar.metric("👎 Pas utile", feedback_stats['thumbs_down'])
            st.sidebar.metric("Satisfaction", f"{feedback_stats['satisfaction_rate']}%")
    except Exception:
        pass

# Sidebar Configuration
st.sidebar.header("⚙️ Configuration")

provider_type = st.sidebar.radio("LLM Provider", ["OpenAI", "Google Gemini", "Local (Ollama/LocalAI)"])

api_key = ""
base_url = None
model_name = "gpt-3.5-turbo"

if provider_type == "OpenAI":
    # Get OpenAI API key with priority: Streamlit secrets > CLI config > Environment variable > User input
    default_openai_key = ""
    
    # Priority 1: Streamlit Cloud secrets
    if hasattr(st, 'secrets') and hasattr(st.secrets, 'OPENAI_API_KEY'):
        default_openai_key = st.secrets.OPENAI_API_KEY
    # Priority 2: CLI config file (~/.primbot/config.json)
    elif not default_openai_key:
        try:
            config_file = Path.home() / ".primbot" / "config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    cli_config = json.load(f)
                    if cli_config.get('openai_api_key'):
                        default_openai_key = cli_config['openai_api_key']
        except Exception:
            pass
    # Priority 3: Environment variable
    if not default_openai_key and "OPENAI_API_KEY" in os.environ:
        default_openai_key = os.getenv("OPENAI_API_KEY", "")
    
    st.sidebar.info("💳 **OpenAI** : Utilisez votre clé API OpenAI. Obtenez votre clé sur [platform.openai.com](https://platform.openai.com/api-keys)")
    
    api_key = st.sidebar.text_input(
        "OpenAI API Key", 
        value=default_openai_key, 
        type="password", 
        help="Get your API key from https://platform.openai.com/api-keys"
    )
    
    # Save to CLI config if user enters a new key
    if api_key and api_key != default_openai_key:
        try:
            config_file = Path.home() / ".primbot" / "config.json"
            config_file.parent.mkdir(exist_ok=True)
            config = {}
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            config['openai_api_key'] = api_key
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass
    base_url = None  # Use default OpenAI endpoint
    model_name = st.sidebar.selectbox(
        "Model Name", 
        ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"],
        index=0,
        help="gpt-3.5-turbo: Fast and affordable. gpt-4: Most capable but slower and more expensive."
    )
elif provider_type == "Google Gemini":
    # Get Gemini API key with priority: Streamlit secrets > CLI config > Environment variable > User input
    default_gemini_key = ""
    
    # Priority 1: Streamlit Cloud secrets
    if hasattr(st.secrets, "GEMINI_API_KEY"):
        default_gemini_key = st.secrets.GEMINI_API_KEY
    # Priority 2: CLI config file (~/.primbot/config.json)
    elif not default_gemini_key:
        try:
            config_file = Path.home() / ".primbot" / "config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    cli_config = json.load(f)
                    if cli_config.get('gemini_api_key'):
                        default_gemini_key = cli_config['gemini_api_key']
        except Exception:
            pass  # Silently fail if config file doesn't exist or can't be read
    # Priority 3: Environment variable
    if not default_gemini_key and "GEMINI_API_KEY" in os.environ:
        default_gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    st.sidebar.info("🆓 **Gratuit** : Gemini offre un plan gratuit généreux. Obtenez votre clé sur [Google AI Studio](https://aistudio.google.com/)")
    
    api_key = st.sidebar.text_input(
        "Gemini API Key", 
        value=default_gemini_key, 
        type="password", 
        help="Get your FREE API key from https://aistudio.google.com/. No credit card required!"
    )
    
    # Save to CLI config if user enters a new key
    if api_key and api_key != default_gemini_key:
        try:
            config_file = Path.home() / ".primbot" / "config.json"
            config_file.parent.mkdir(exist_ok=True)
            config = {}
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            config['gemini_api_key'] = api_key
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass  # Silently fail if can't save config
    base_url = None  # Gemini uses google-generativeai library directly, not OpenAI-compatible endpoint
    model_name = st.sidebar.selectbox(
        "Model Name", 
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        index=0,
        help="gemini-2.5-flash: Fastest and free. gemini-2.5-pro: Most capable (may have rate limits on free tier)"
    )
else:
    st.sidebar.info("🆓 **100% Gratuit** : Ollama fonctionne localement, aucune clé API nécessaire!")
    st.sidebar.markdown("**Installation:**\n1. Téléchargez [Ollama](https://ollama.ai/)\n2. Installez un modèle: `ollama pull llama3.1`\n3. Lancez: `ollama serve`")
    
    base_url = st.sidebar.text_input(
        "Base URL", 
        value="http://localhost:11434/v1",
        help="URL de votre instance Ollama (par défaut: http://localhost:11434/v1)"
    )
    model_name = st.sidebar.selectbox(
        "Model Name", 
        ["llama3.1", "llama3.1:8b", "llama3.2", "mistral", "mixtral", "codellama"],
        index=0,
        help="Modèles recommandés: llama3.1 (équilibré), mistral (rapide), mixtral (puissant)"
    )
    api_key = "ollama" # Dummy key for local

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat
for message in st.session_state.messages:
    if message["role"] != "system" and message["role"] != "tool":
        with st.chat_message(message["role"]):
            content = message["content"]
            
            # Remove images and "Captures d'écran de l'interface" section from content
            import re
            # Remove markdown image syntax: ![alt](url)
            content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', content)
            # Remove "Captures d'écran de l'interface" section header and content
            content = re.sub(r'##\s*📸\s*Captures\s*d\'écran\s*de\s*l\'interface.*?(?=\n##|\n---|$)', '', content, flags=re.IGNORECASE | re.DOTALL)
            # Remove image sections and references
            content = re.sub(r'(?i)(image\s*\d+|capture\s*d\'écran\s*\d+|screenshot\s*\d+)[:：]?\s*[^\n]*\n?', '', content)
            # Clean up multiple empty lines
            content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
            # Display content (now without images, only URLs)
            st.markdown(content)

# Chat Input
if prompt := st.chat_input("Describe the problem..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Agent Response
    if not api_key:
        st.error("Please enter an API Key.")
        st.stop()

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 Thinking...")
        
        try:
            # Check knowledge base before initializing agent
            kb_count = collection.count()
            if kb_count == 0:
                message_placeholder.warning("⚠️ **Base de connaissances vide** - Le bot ne peut pas rechercher dans la documentation. Utilisez le bouton d'initialisation dans la sidebar.")
                st.session_state.messages.append({"role": "assistant", "content": "⚠️ Je ne peux pas accéder à la base de connaissances car elle n'est pas initialisée. Veuillez utiliser le bouton d'initialisation dans la sidebar pour charger la documentation PrimLogix."})
                st.stop()
            
            # Initialize Agent
            agent = PrimAgent(api_key=api_key, base_url=base_url, model=model_name, provider=provider_type)
            
            # Prepare messages logic (filtering out tools for initial pass if needed, but OpenAI handles history)
            # We pass full history so it has context
            # We filter out UI-specific keys if we added any, but here we stick to standard role/content
            
            # Simple wrapper to handle the conversation
            # For this simple implementation, we just pass the history. 
            # Note: We might need to handle the tool messages carefully in history regeneration, 
            # but for now we'll rely on the agent.run taking the current thread.
            # actually agent.run expects a list of messages. We should pass a copy.
            
            response = agent.run(st.session_state.messages.copy())
            
            # Remove images and "Captures d'écran de l'interface" section from response
            import re
            # Remove markdown image syntax: ![alt](url)
            response = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', response)
            # Remove "Captures d'écran de l'interface" section header and content
            response = re.sub(r'##\s*📸\s*Captures\s*d\'écran\s*de\s*l\'interface.*?(?=\n##|\n---|$)', '', response, flags=re.IGNORECASE | re.DOTALL)
            # Remove image sections and references
            response = re.sub(r'(?i)(image\s*\d+|capture\s*d\'écran\s*\d+|screenshot\s*\d+)[:：]?\s*[^\n]*\n?', '', response)
            # Clean up multiple empty lines
            response = re.sub(r'\n\s*\n\s*\n+', '\n\n', response)
            
            # Display response (now without images, only URLs)
            message_placeholder.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Sauvegarder la conversation localement et obtenir conversation_id pour feedback
            conversation_id = None
            try:
                storage = get_storage()
                user_id = "streamlit_user"  # Vous pouvez personnaliser selon votre système d'authentification
                conversation_id = storage.save_conversation(user_id, prompt, response, metadata={
                    "provider": provider_type,
                    "model": model_name
                })
            except Exception as save_error:
                # Ne pas bloquer si la sauvegarde échoue
                st.sidebar.warning(f"⚠️ Impossible de sauvegarder la conversation: {save_error}")
            
            # Ajouter les boutons de feedback (thumbs up/down) après la réponse
            if conversation_id:
                st.markdown("---")
                # Améliorer l'alignement des boutons avec un meilleur espacement
                col1, col2 = st.columns([1, 1])
                with col1:
                    thumbs_up_key = f"thumbs_up_{conversation_id}_{len(st.session_state.messages)}"
                    thumbs_up = st.button("👍 Utile", key=thumbs_up_key, help="Cette réponse était utile", use_container_width=True)
                with col2:
                    thumbs_down_key = f"thumbs_down_{conversation_id}_{len(st.session_state.messages)}"
                    thumbs_down = st.button("👎 Pas utile", key=thumbs_down_key, help="Cette réponse n'était pas utile", use_container_width=True)
                
                # Gérer le feedback thumbs up
                if thumbs_up:
                    try:
                        storage = get_storage()
                        storage.save_feedback(conversation_id, rating=1, question=prompt, answer=response)
                        st.success("✅ Merci pour votre feedback ! Cela nous aide à améliorer PRIMBOT.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de la sauvegarde du feedback: {e}")
                
                # Gérer le feedback thumbs down
                if thumbs_down:
                    # Demander un commentaire optionnel
                    with st.expander("💬 Pourquoi cette réponse n'était pas utile ?", expanded=True):
                        comment_key = f"comment_{conversation_id}_{len(st.session_state.messages)}"
                        comment = st.text_area(
                            "Votre commentaire (optionnel) :",
                            placeholder="Ex: La réponse était confuse, manquait d'informations, images non pertinentes, pas assez de détails, etc.",
                            key=comment_key,
                            height=100
                        )
                        submit_key = f"submit_feedback_{conversation_id}_{len(st.session_state.messages)}"
                        submit_feedback = st.button("Envoyer le feedback", key=submit_key, type="primary")
                        
                        if submit_feedback:
                            try:
                                storage = get_storage()
                                storage.save_feedback(conversation_id, rating=-1, comment=comment, question=prompt, answer=response)
                                st.success("✅ Merci pour votre feedback détaillé ! Nous utiliserons ces informations pour améliorer PRIMBOT.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur lors de la sauvegarde du feedback: {e}")
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            # Provide helpful error messages
            if "API" in error_msg or "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                detailed_error = f"""❌ **Erreur d'authentification API**

**Erreur:** {error_type}

**Solutions:**
1. Vérifiez que votre clé API est correcte
2. Pour Gemini: Obtenez une clé gratuite sur [Google AI Studio](https://aistudio.google.com/)
3. Vérifiez que la clé API est bien configurée dans les secrets/variables d'environnement
4. Pour Ollama: Assurez-vous que `ollama serve` est lancé"""
            elif "model" in error_msg.lower() or "404" in error_msg or "not found" in error_msg.lower():
                detailed_error = f"""❌ **Modèle non trouvé**

**Erreur:** {error_type}: {error_msg}

**Solutions:**
1. Vérifiez que le nom du modèle est correct
2. Pour Gemini: Essayez `gemini-2.5-flash` ou `gemini-2.0-flash`
3. Pour Ollama: Vérifiez que le modèle est installé: `ollama list`"""
            elif "knowledge" in error_msg.lower() or "base" in error_msg.lower() or "chromadb" in error_msg.lower():
                detailed_error = f"""❌ **Erreur de base de connaissances**

**Erreur:** {error_type}: {error_msg}

**Solutions:**
1. Vérifiez que la base de connaissances est initialisée
2. Utilisez le bouton d'initialisation dans la sidebar
3. Ou exécutez: `python ingest.py`
4. Vérifiez que ChromaDB est installé: `pip install chromadb`"""
            else:
                detailed_error = f"""❌ **Erreur inattendue**

**Erreur:** {error_type}: {error_msg}

**Solutions:**
1. Vérifiez les logs pour plus de détails
2. Réessayez votre requête
3. Vérifiez que toutes les dépendances sont installées: `pip install -r requirements.txt`"""
            
            message_placeholder.error(detailed_error)
            st.session_state.messages.append({"role": "assistant", "content": detailed_error})
