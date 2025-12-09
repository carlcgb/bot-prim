import streamlit as st
from agent import PrimAgent
from knowledge_base import collection
import os

st.set_page_config(page_title="PrimLogix Debug Agent", layout="wide")

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

# Sidebar Configuration
st.sidebar.header("⚙️ Configuration")

provider_type = st.sidebar.radio("LLM Provider", ["Google Gemini", "Local (Ollama/LocalAI)"])

api_key = ""
base_url = None
model_name = "gemini-2.5-flash"

if provider_type == "Google Gemini":
    # Get Gemini API key from Streamlit secrets (for Streamlit Cloud) or environment variable (for other deployments)
    # Priority: Streamlit secrets > Environment variable > User input
    default_gemini_key = ""
    if hasattr(st.secrets, "GEMINI_API_KEY"):
        # Streamlit Cloud secrets
        default_gemini_key = st.secrets.GEMINI_API_KEY
    elif "GEMINI_API_KEY" in os.environ:
        # Environment variable (GitHub Actions, Cloudflare, etc.)
        default_gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    st.sidebar.info("🆓 **Gratuit** : Gemini offre un plan gratuit généreux. Obtenez votre clé sur [Google AI Studio](https://aistudio.google.com/)")
    
    api_key = st.sidebar.text_input(
        "Gemini API Key", 
        value=default_gemini_key, 
        type="password", 
        help="Get your FREE API key from https://aistudio.google.com/. No credit card required!"
    )
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
            
            # Check if content contains screenshots section
            if "[SCREENSHOTS]" in content:
                # Split content into text and images
                parts = content.split("[SCREENSHOTS]")
                text_content = parts[0].strip()
                image_section = parts[1].strip() if len(parts) > 1 else ""
                
                # Display text content
                if text_content:
                    st.markdown(text_content)
                
                # Display images
                if image_section:
                    # Extract image URLs and captions from markdown format ![alt](url)
                    import re
                    # Match full markdown image syntax to get both caption and URL
                    image_pattern = r'!\[(.*?)\]\((.*?)\)'
                    image_matches = re.findall(image_pattern, image_section)
                    
                    if image_matches:
                        st.markdown("### 📸 Captures d'écran de la documentation")
                        st.markdown(f"*{len(image_matches)} capture(s) d'écran disponible(s)*")
                        
                        # Filter and validate URLs with captions
                        valid_images = []
                        for caption, img_url in image_matches[:12]:  # Increased to 12 images
                            img_url = img_url.strip()
                            if img_url and (img_url.startswith('http://') or img_url.startswith('https://')):
                                valid_images.append((caption.strip() or f"Capture {len(valid_images)+1}", img_url))
                        
                        if valid_images:
                            # Display images in a grid (2 columns for better visibility)
                            num_cols = min(2, len(valid_images))
                            cols = st.columns(num_cols)
                            
                            for idx, (caption, img_url) in enumerate(valid_images):
                                col_idx = idx % num_cols
                                with cols[col_idx]:
                                    try:
                                        # Try to display image with timeout
                                        import requests
                                        from io import BytesIO
                                        from PIL import Image
                                        
                                        # Download image with better error handling
                                        headers = {
                                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                                        }
                                        img_response = requests.get(img_url, headers=headers, timeout=10, stream=True)
                                        img_response.raise_for_status()
                                        
                                        # Load and display
                                        img = Image.open(BytesIO(img_response.content))
                                        
                                        # Use caption from markdown or default
                                        display_caption = caption if caption and not caption.startswith("Capture d'écran") else f"Capture {idx+1}"
                                        
                                        st.image(img, caption=display_caption, use_container_width=True)
                                        
                                        # Add link to original image
                                        st.caption(f"[🔗 Ouvrir l'image]({img_url})")
                                    except requests.exceptions.Timeout:
                                        st.warning(f"⏱️ Timeout lors du chargement")
                                        st.markdown(f"[📷 Voir l'image]({img_url})")
                                    except requests.exceptions.RequestException as e:
                                        st.warning(f"⚠️ Erreur de chargement")
                                        st.markdown(f"[📷 Voir l'image]({img_url})")
                                    except Exception as e:
                                        # If image fails to load, show as link
                                        st.warning(f"⚠️ Impossible d'afficher l'image")
                                        st.markdown(f"[📷 Voir l'image]({img_url})")
                                        if "PIL" not in str(e):  # Don't show PIL errors to user
                                            st.caption(f"Erreur: {str(e)[:50]}")
            else:
                # Regular content without images
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
            
            # Display response with images parsed inline
            # Parse markdown images and display them inline with the text
            import re
            
            # Find all markdown images in the response
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            image_matches = list(re.finditer(image_pattern, response))
            
            if image_matches:
                # Split response into parts (text and images)
                parts = []
                last_end = 0
                images_to_display = []
                
                for match in image_matches:
                    # Add text before image
                    if match.start() > last_end:
                        parts.append(("text", response[last_end:match.start()]))
                    
                    # Extract image info
                    alt_text = match.group(1)
                    img_url = match.group(2).strip()
                    
                    if img_url and (img_url.startswith('http://') or img_url.startswith('https://')):
                        images_to_display.append({
                            "url": img_url,
                            "alt": alt_text,
                            "position": match.start()
                        })
                        # Add placeholder for image
                        parts.append(("image", len(images_to_display) - 1))
                    
                    last_end = match.end()
                
                # Add remaining text
                if last_end < len(response):
                    parts.append(("text", response[last_end:]))
                
                # Display parts in order (text and images inline)
                for part_type, content in parts:
                    if part_type == "text" and content.strip():
                        message_placeholder.markdown(content)
                    elif part_type == "image":
                        img_idx = content
                        img_info = images_to_display[img_idx]
                        
                        try:
                            # Download and display image inline
                            import requests
                            from io import BytesIO
                            from PIL import Image
                            
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                            }
                            img_response = requests.get(img_info["url"], headers=headers, timeout=10, stream=True)
                            img_response.raise_for_status()
                            
                            img = Image.open(BytesIO(img_response.content))
                            caption = img_info["alt"] if img_info["alt"] else f"Capture d'écran {img_idx + 1}"
                            
                            st.image(img, caption=caption, use_container_width=True)
                            st.caption(f"[🔗 Ouvrir l'image]({img_info['url']})")
                        except Exception as e:
                            # If image fails, show as markdown link
                            st.markdown(f"[📷 {img_info['alt'] or 'Voir l\'image'}]({img_info['url']})")
            else:
                # No images, display regular content
                message_placeholder.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
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
