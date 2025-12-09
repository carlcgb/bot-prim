import streamlit as st
from agent import PrimAgent
from knowledge_base import collection
import os

st.set_page_config(page_title="PrimLogix Debug Agent", layout="wide")

st.title("🤖 PrimLogix Debug Agent")

# Check if knowledge base is empty
kb_count = collection.count()
if kb_count == 0:
    st.warning("⚠️ **Base de connaissances vide** - Le bot ne peut pas rechercher dans la documentation PrimLogix.")
    st.info("💡 **Solution**: La base de connaissances doit être initialisée. Sur Streamlit Cloud, vous pouvez soit :\n"
            "1. Inclure le dossier `chroma_db/` dans le repository (retirez-le de .gitignore)\n"
            "2. Ou exécuter le script d'ingestion après le déploiement")
    
    with st.expander("🔧 Initialiser la base de connaissances"):
        if st.button("🚀 Lancer l'ingestion de la documentation"):
            with st.spinner("Scraping et ingestion en cours... Cela peut prendre plusieurs minutes."):
                try:
                    from scraper import run_scraper
                    from knowledge_base import add_documents
                    
                    st.write("📥 Scraping de la documentation PrimLogix...")
                    data = run_scraper()
                    
                    st.write(f"💾 Ajout de {len(data)} pages à la base de connaissances...")
                    add_documents(data)
                    
                    st.success(f"✅ Base de connaissances initialisée avec {collection.count()} documents!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'ingestion: {e}")
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
    
    api_key = st.sidebar.text_input(
        "Gemini API Key", 
        value=default_gemini_key, 
        type="password", 
        help="Get it from https://aistudio.google.com/. For Streamlit Cloud, set it in app settings. For other deployments, use GEMINI_API_KEY environment variable."
    )
    base_url = None  # Gemini uses google-generativeai library directly, not OpenAI-compatible endpoint
    model_name = st.sidebar.text_input("Model Name", value="gemini-2.5-flash", help="Available: gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash")
else:
    base_url = st.sidebar.text_input("Base URL", value="http://localhost:11434/v1")
    model_name = st.sidebar.text_input("Model Name", value="llama3.1")
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
                    # Extract image URLs from markdown format ![alt](url)
                    import re
                    image_pattern = r'!\[.*?\]\((.*?)\)'
                    image_urls = re.findall(image_pattern, image_section)
                    
                    if image_urls:
                        st.markdown("**Captures d'écran de la documentation:**")
                        cols = st.columns(min(3, len(image_urls)))  # Max 3 columns
                        for idx, img_url in enumerate(image_urls[:6]):  # Max 6 images
                            col_idx = idx % 3
                            with cols[col_idx]:
                                try:
                                    st.image(img_url, caption=f"Image {idx+1}", use_container_width=True)
                                except Exception as e:
                                    st.markdown(f"[Image]({img_url})")
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
            
            # Display response with images if present
            if "[SCREENSHOTS]" in response:
                # Split content into text and images
                parts = response.split("[SCREENSHOTS]")
                text_content = parts[0].strip()
                image_section = parts[1].strip() if len(parts) > 1 else ""
                
                # Display text content
                if text_content:
                    message_placeholder.markdown(text_content)
                
                # Display images
                if image_section:
                    # Extract image URLs from markdown format ![alt](url)
                    import re
                    image_pattern = r'!\[.*?\]\((.*?)\)'
                    image_urls = re.findall(image_pattern, image_section)
                    
                    if image_urls:
                        st.markdown("**📸 Captures d'écran de la documentation:**")
                        cols = st.columns(min(3, len(image_urls)))  # Max 3 columns
                        for idx, img_url in enumerate(image_urls[:6]):  # Max 6 images
                            col_idx = idx % 3
                            with cols[col_idx]:
                                try:
                                    st.image(img_url, caption=f"Image {idx+1}", use_container_width=True)
                                except Exception as e:
                                    # If image fails to load, show as link
                                    st.markdown(f"[📷 Voir l'image]({img_url})")
            else:
                # Regular content without images
                message_placeholder.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            message_placeholder.error(f"Error: {str(e)}")
