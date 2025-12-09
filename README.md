# PrimLogix Debug Agent

Un agent d'assistance intelligent pour la documentation PrimLogix utilisant Gemini AI.

## Fonctionnalités

- 🔍 Recherche dans la base de connaissances PrimLogix
- 🤖 Support pour Gemini AI, OpenAI et modèles locaux
- 📸 Affichage de captures d'écran de la documentation
- 🇫🇷 Interface en français

## Configuration

### Variables d'environnement / Secrets

Le bot utilise les secrets/variables d'environnement suivants :

- `GEMINI_API_KEY` - Clé API Google Gemini (requis pour le provider Gemini)

#### Pour le développement local

Créez un fichier `.streamlit/secrets.toml` (utilisez `.streamlit/secrets.toml.example` comme modèle) :

```toml
GEMINI_API_KEY = "votre_cle_api_gemini"
```

#### Pour Streamlit Cloud

1. Allez dans les paramètres de votre app Streamlit Cloud
2. Section "Secrets"
3. Ajoutez :
   ```toml
   GEMINI_API_KEY = "votre_cle_api_gemini"
   ```

#### Pour GitHub Actions / Cloudflare Pages

Configurez les secrets dans :
- **GitHub**: Settings > Secrets and variables > Actions > New repository secret
  - Nom: `GEMINI_API_KEY`
  - Valeur: votre clé API Gemini
- **Cloudflare Pages**: Settings > Environment variables
  - Nom: `GEMINI_API_KEY`
  - Valeur: votre clé API Gemini

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

### Développement local

```bash
streamlit run app.py
```

### Ingestion de la documentation

Pour mettre à jour la base de connaissances :

```bash
python ingest.py
```

## Déploiement

### Streamlit Cloud (Recommandé)

**⚠️ IMPORTANT : Si vous voyez "This repository does not exist"**

Votre repository est probablement **privé**. Streamlit Cloud doit être autorisé à y accéder :

1. **Autoriser Streamlit Cloud** :
   - Allez sur https://github.com/settings/applications
   - Cliquez sur "Authorized GitHub Apps" (ou "Installed GitHub Apps")
   - Trouvez "Streamlit" et cliquez sur "Configure"
   - Assurez-vous que `carlcgb/bot-prim` est dans la liste des repositories autorisés
   - Si Streamlit n'apparaît pas, vous serez invité à l'autoriser lors du premier déploiement

2. **Déployer sur Streamlit Cloud** :
   - Allez sur [Streamlit Cloud](https://share.streamlit.io)
   - Cliquez sur "New app"
   - **Repository** : `carlcgb/bot-prim` (sans https://github.com/)
   - **Branch** : `main`
   - **Main file path** : `app.py` (⚠️ pas `streamlit_app.py`)
   - Cliquez sur "Deploy"

3. **Configurer les secrets** :
   - Dans les paramètres de l'app, section "Secrets", ajoutez :
     ```toml
     GEMINI_API_KEY = "votre_cle_api_gemini"
     ```

**Alternative : Rendre le repository public**
- Si vous préférez, vous pouvez rendre le repository public dans les paramètres GitHub
- ⚠️ Assurez-vous qu'aucune clé API n'est dans le code (déjà fait ✅)

### Cloudflare Pages

Note: Cloudflare Pages est principalement pour les sites statiques. Pour une app Streamlit, considérez:
- Streamlit Cloud (recommandé)
- Heroku
- Railway
- Render

Si vous utilisez Cloudflare Workers/Pages avec une API backend, configurez la variable d'environnement `GEMINI_API_KEY` dans les paramètres.

## Structure du projet

- `app.py` - Interface Streamlit principale
- `agent.py` - Agent AI avec support Gemini/OpenAI
- `knowledge_base.py` - Gestion de la base de données vectorielle
- `scraper.py` - Scraping de la documentation PrimLogix
- `ingest.py` - Script d'ingestion des données
- `.streamlit/config.toml` - Configuration Streamlit
- `.streamlit/secrets.toml.example` - Exemple de fichier secrets (local)

## Sécurité

⚠️ **Important**: Ne commitez JAMAIS de clés API dans le code. Utilisez toujours :
- Streamlit secrets pour Streamlit Cloud
- Variables d'environnement pour les autres plateformes
- GitHub Secrets pour GitHub Actions

Le fichier `.gitignore` est configuré pour exclure les fichiers contenant des secrets.

## Licence

Propriétaire - Dev-NTIC
