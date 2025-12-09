# PrimLogix Debug Agent

Un agent d'assistance intelligent pour la documentation PrimLogix utilisant Gemini AI.

## Fonctionnalités

- 🔍 Recherche dans la base de connaissances PrimLogix
- 🤖 Support pour Gemini AI, OpenAI et modèles locaux
- 📸 Affichage de captures d'écran de la documentation
- 🇫🇷 Interface en français

## Configuration

### Variables d'environnement

Créez un fichier `.env` ou configurez les variables d'environnement suivantes:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

Pour GitHub Actions / Cloudflare Pages, configurez les secrets dans:
- GitHub: Settings > Secrets and variables > Actions
- Cloudflare Pages: Settings > Environment variables

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

Pour mettre à jour la base de connaissances:

```bash
python ingest.py
```

## Déploiement

### Streamlit Cloud

1. Poussez votre code sur GitHub
2. Connectez votre repo à [Streamlit Cloud](https://streamlit.io/cloud)
3. Configurez la variable d'environnement `GEMINI_API_KEY` dans les paramètres

### Cloudflare Pages / Workers

1. Ajoutez la variable d’environnement `GEMINI_API_KEY` dans **Cloudflare Pages > Settings > Environment variables** (ou dans votre Worker si vous déployez un backend Python).
2. Définissez-la pour les environnements **Preview** et **Production**.
3. Déployez après avoir poussé le code sur GitHub.

> Remarque: Cloudflare Pages est pensé pour les sites statiques. Pour une app Streamlit, vous pouvez aussi considérer Streamlit Cloud (recommandé), Heroku, Railway ou Render.

## Structure du projet

- `app.py` - Interface Streamlit principale
- `agent.py` - Agent AI avec support Gemini/OpenAI
- `knowledge_base.py` - Gestion de la base de données vectorielle
- `scraper.py` - Scraping de la documentation PrimLogix
- `ingest.py` - Script d'ingestion des données

## Licence

Propriétaire - Dev-NTIC

