import streamlit as st
import os
import re
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Load Qdrant secrets from Streamlit FIRST (before importing knowledge_base)
# This ensures Qdrant Cloud is used when secrets are available
try:
    if hasattr(st, 'secrets'):
        # Check if secrets file exists by trying to access it safely
        try:
            # Use getattr to safely access secrets without KeyError
            qdrant_secrets = getattr(st.secrets, 'qdrant', None)
            if qdrant_secrets is not None:
                # Access individual keys safely
                use_qdrant = getattr(qdrant_secrets, 'USE_QDRANT', None) or getattr(qdrant_secrets, 'get', lambda k, d: d)('USE_QDRANT', 'false')
                qdrant_url = getattr(qdrant_secrets, 'QDRANT_URL', None) or getattr(qdrant_secrets, 'get', lambda k, d: d)('QDRANT_URL', '')
                qdrant_api_key = getattr(qdrant_secrets, 'QDRANT_API_KEY', None) or getattr(qdrant_secrets, 'get', lambda k, d: d)('QDRANT_API_KEY', '')
                
                if use_qdrant and qdrant_url and qdrant_api_key:
                    os.environ['USE_QDRANT'] = str(use_qdrant)
                    os.environ['QDRANT_URL'] = str(qdrant_url)
                    os.environ['QDRANT_API_KEY'] = str(qdrant_api_key)
                    # Log for debugging (only in Streamlit Cloud)
                    if os.environ.get('USE_QDRANT', 'false').lower() == 'true':
                        logger.info(f"Qdrant Cloud configured: URL={os.environ.get('QDRANT_URL', 'N/A')[:50]}...")
        except (KeyError, AttributeError, TypeError) as e:
            # Secrets file doesn't exist or has wrong structure, use environment variables instead
            logger.warning(f"Could not load Qdrant secrets: {e}")
            pass
except Exception as e:
    # If secrets are not available, continue with environment variables
    logger.warning(f"Secrets not available: {e}")
    pass

# Now import knowledge_base (after Qdrant env vars are set)
from agent import PrimAgent
from knowledge_base import collection
from storage_local import get_storage
import json
from pathlib import Path

st.set_page_config(page_title="DEBUGEX - Agent IA PrimLogix", layout="wide")

# Add CSS and JavaScript for image modal
st.markdown("""
<style>
    .image-container {
        position: relative;
        display: inline-block;
        cursor: pointer;
        margin: 15px 0;
        text-align: center;
        width: 100%;
    }
    .image-container img {
        max-width: 400px;
        width: auto;
        height: auto;
        max-height: 300px;
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
        display: block;
        margin: 0 auto;
        object-fit: contain;
    }
    .image-container img:hover {
        opacity: 0.85;
        box-shadow: 0 4px 16px rgba(0,0,0,0.25);
        transform: scale(1.02);
    }
    .image-modal {
        display: none;
        position: fixed;
        z-index: 99999;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.95);
        animation: fadeIn 0.3s;
        overflow: auto;
    }
    .image-modal-content {
        margin: auto;
        display: block;
        width: 95%;
        max-width: 1400px;
        max-height: 90vh;
        object-fit: contain;
        margin-top: 2vh;
        animation: zoomIn 0.3s;
        border-radius: 8px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    .image-modal-close {
        position: absolute;
        top: 20px;
        right: 40px;
        color: #f1f1f1;
        font-size: 40px;
        font-weight: bold;
        cursor: pointer;
        z-index: 10001;
    }
    .image-modal-close:hover {
        color: #fff;
    }
    .image-caption {
        color: #f1f1f1;
        text-align: center;
        padding: 15px 20px;
        font-size: 14px;
        max-width: 1400px;
        margin: 0 auto;
        line-height: 1.5;
    }
    /* Improve chat message readability */
    .stChatMessage {
        padding: 1rem;
    }
    /* Better spacing for content */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    @keyframes fadeIn {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    @keyframes zoomIn {
        from {transform: scale(0.5);}
        to {transform: scale(1);}
    }
</style>
<script>
    // Make functions globally available
    window.openImageModal = function(imgSrc, imgAlt) {
        var modal = document.getElementById('imageModal');
        var modalImg = document.getElementById('modalImage');
        var caption = document.getElementById('imageCaption');
        if (modal && modalImg) {
            modal.style.display = "block";
            modalImg.src = imgSrc;
            if (caption) {
                caption.innerHTML = imgAlt || 'Image';
            }
            // Prevent body scroll when modal is open
            document.body.style.overflow = "hidden";
        } else {
            console.error('Modal elements not found');
        }
    };
    
    window.closeImageModal = function() {
        var modal = document.getElementById('imageModal');
        if (modal) {
            modal.style.display = "none";
            document.body.style.overflow = "auto";
        }
    };
    
    // Use event delegation for click handlers (works better with React)
    function initImageClickHandlers() {
        // Remove old listeners to avoid duplicates
        document.removeEventListener('click', handleImageClick);
        document.addEventListener('click', handleImageClick, true);
    }
    
    function handleImageClick(event) {
        // Check if clicked element is an image container or image inside container
        var target = event.target;
        var container = target.closest('.image-container');
        
        if (container) {
            event.preventDefault();
            event.stopPropagation();
            
            // Get image URL from data attribute or img src
            var imgUrl = container.getAttribute('data-image-url');
            var imgAlt = container.getAttribute('data-image-alt') || 'Image';
            
            if (!imgUrl) {
                var img = container.querySelector('img');
                if (img) {
                    imgUrl = img.src;
                    imgAlt = img.alt || imgAlt;
                }
            }
            
            if (imgUrl) {
                window.openImageModal(imgUrl, imgAlt);
            }
            return false;
        }
        
        // Close modal when clicking outside
        var modal = document.getElementById('imageModal');
        if (modal && event.target === modal) {
            window.closeImageModal();
        }
    }
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            var modal = document.getElementById('imageModal');
            if (modal && modal.style.display === "block") {
                window.closeImageModal();
            }
        }
    });
    
    // Initialize on page load and after Streamlit updates
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initImageClickHandlers);
    } else {
        initImageClickHandlers();
    }
    
    // Re-initialize after Streamlit updates (Streamlit uses MutationObserver)
    var observer = new MutationObserver(function(mutations) {
        initImageClickHandlers();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
</script>
""", unsafe_allow_html=True)

# Add modal HTML structure
st.markdown("""
<div id="imageModal" class="image-modal">
    <span class="image-modal-close" id="imageModalClose">&times;</span>
    <img class="image-modal-content" id="modalImage">
    <div class="image-caption" id="imageCaption"></div>
</div>
""", unsafe_allow_html=True)

# Add click handler for close button using JavaScript
st.markdown("""
<script>
    // Attach close button handler
    function attachCloseButton() {
        var closeBtn = document.getElementById('imageModalClose');
        if (closeBtn && !closeBtn.hasAttribute('data-handler-attached')) {
            closeBtn.addEventListener('click', function() {
                window.closeImageModal();
            });
            closeBtn.setAttribute('data-handler-attached', 'true');
        }
    }
    
    // Initialize close button
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', attachCloseButton);
    } else {
        attachCloseButton();
    }
    
    // Re-attach after Streamlit updates
    var closeObserver = new MutationObserver(function() {
        attachCloseButton();
    });
    closeObserver.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

st.title("🦸‍♂️ DEBUGEX")
st.caption("Agent IA pour l'aide en ligne PrimLogix")

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

# Check which backend is being used
USE_QDRANT = os.getenv('USE_QDRANT', 'false').lower() == 'true'
backend_type = "Qdrant Cloud" if USE_QDRANT else "ChromaDB Local"

# Check if knowledge base is empty
kb_count = collection.count()
if kb_count == 0:
    if USE_QDRANT:
        st.error("⚠️ **Base de connaissances Qdrant Cloud vide** - La base de connaissances devrait déjà contenir des documents. Vérifiez la configuration Qdrant ou contactez l'administrateur.")
        st.info("💡 **Note** : Si vous utilisez Qdrant Cloud, les données devraient déjà être présentes. L'ingestion n'est nécessaire que pour ChromaDB local.")
    else:
        st.warning("⚠️ **Base de connaissances vide** - Le bot ne peut pas rechercher dans la documentation PrimLogix.")
        
        # Auto-initialization option (only for ChromaDB local)
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
    st.sidebar.info(f"🔧 Backend: {backend_type}")
    
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

# Gemini is now mandatory
provider_type = "Google Gemini"
api_key = ""
base_url = None
model_name = "gemini-2.5-flash"

# Get Gemini API key with priority: Streamlit secrets > CLI config > Environment variable > User input
default_gemini_key = ""

# Priority 1: Streamlit Cloud secrets
if hasattr(st, 'secrets') and hasattr(st.secrets, 'GEMINI_API_KEY'):
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

if True:  # Always Gemini
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
    base_url = None  # Gemini uses google-generativeai library directly
    model_name = st.sidebar.selectbox(
        "Model Name", 
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        index=0,
        help="gemini-2.5-flash: Fastest and free. gemini-2.5-pro: Most capable (may have rate limits on free tier)"
    )

def convert_images_to_clickable(content):
    """Convert markdown images to clickable HTML images with modal."""
    # Find all markdown images: ![alt](url)
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_image(match):
        alt_text = match.group(1) or 'Image'
        img_url = match.group(2)
        
        # Escape quotes in alt text for HTML attribute
        escaped_alt = alt_text.replace('"', '&quot;').replace("'", '&#39;')
        
        # SVG placeholder for error handling (base64 encoded)
        svg_placeholder = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZSBub24gZGlzcG9uaWJsZTwvdGV4dD48L3N2Zz4='
        
        # Return HTML with clickable image - NO onclick attribute (use event delegation instead)
        # The JavaScript will handle clicks via event delegation
        return (f'<div class="image-container" data-image-url="{img_url}" data-image-alt="{escaped_alt}">'
                f'<img src="{img_url}" alt="{alt_text}" '
                f'onerror="this.onerror=null; this.src=\'{svg_placeholder}\';" /></div>')
    
    # Replace all markdown images with clickable HTML
    html_content = re.sub(pattern, replace_image, content)
    return html_content

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat
for message in st.session_state.messages:
    if message["role"] != "system" and message["role"] != "tool":
        with st.chat_message(message["role"]):
            content = message["content"]
            
            # Remove "Captures d'écran de l'interface" section header at the end (but keep images in steps)
            content = re.sub(r'##\s*📸\s*Captures\s*d\'écran\s*pertinentes\s*de\s*l\'interface\s*PrimLogix.*?(?=\n##|\n---|$)', '', content, flags=re.IGNORECASE | re.DOTALL)
            # Clean up multiple empty lines
            content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
            
            # Split content into parts: markdown text and images
            # First, extract images and replace with placeholders
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            images_found = re.findall(image_pattern, content)
            
            if images_found:
                # Convert images to clickable HTML
                html_content = convert_images_to_clickable(content)
                # Display with HTML support
                st.markdown(html_content, unsafe_allow_html=True)
            else:
                # No images, just display markdown normally
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
            
            # Prepare messages logic
            # We pass full history so it has context
            # We filter out UI-specific keys if we added any, but here we stick to standard role/content
            
            # Simple wrapper to handle the conversation
            # actually agent.run expects a list of messages. We should pass a copy.
            
            response = agent.run(st.session_state.messages.copy())
            
            # Keep images but clean up other unwanted content
            # Remove "Captures d'écran de l'interface" section header at the end (but keep images in steps)
            response = re.sub(r'##\s*📸\s*Captures\s*d\'écran\s*pertinentes\s*de\s*l\'interface\s*PrimLogix.*?(?=\n##|\n---|$)', '', response, flags=re.IGNORECASE | re.DOTALL)
            # Remove duplicate image sections at the end, but keep images within steps
            # Clean up multiple empty lines
            response = re.sub(r'\n\s*\n\s*\n+', '\n\n', response)
            
            # Check if response contains images
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            has_images = re.search(image_pattern, response)
            
            if has_images:
                # Convert images to clickable HTML
                html_response = convert_images_to_clickable(response)
                # Display response with clickable images
                message_placeholder.markdown(html_response, unsafe_allow_html=True)
            else:
                # No images, display normally
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
1. Vérifiez que votre clé API Gemini est correcte
2. Obtenez une clé gratuite sur [Google AI Studio](https://aistudio.google.com/)
3. Vérifiez que la clé API est bien configurée dans les secrets/variables d'environnement"""
            elif "model" in error_msg.lower() or "404" in error_msg or "not found" in error_msg.lower():
                detailed_error = f"""❌ **Modèle non trouvé**

**Erreur:** {error_type}: {error_msg}

**Solutions:**
1. Vérifiez que le nom du modèle Gemini est correct
2. Essayez `gemini-2.5-flash` ou `gemini-2.0-flash`
3. Consultez la [liste des modèles disponibles](https://ai.google.dev/models/gemini)"""
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
