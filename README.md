# 🤖 PRIMBOT

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/release/carlcgb/bot-prim.svg)](https://github.com/carlcgb/bot-prim/releases)
[![Streamlit](https://img.shields.io/badge/Streamlit-Cloud-orange.svg)](https://primbot.streamlit.app/)

Un agent d'assistance intelligent pour la documentation PrimLogix utilisant Gemini AI.

## ✨ Fonctionnalités

- 🔍 **Recherche intelligente** dans la base de connaissances PrimLogix (10 résultats pour meilleur contexte)
- 🤖 **Support Gemini AI** pour des réponses détaillées et structurées
- 📊 **Scores de pertinence** pour évaluer la qualité des résultats
- 📸 **Affichage de captures d'écran** de la documentation (jusqu'à 8 images)
- 🎯 **Réponses optimisées pour le débogage** avec détails techniques et exemples
- 🇫🇷 **Interface en français**
- 💻 **Interface CLI** pour utilisation en ligne de commande
- 🌐 **Interface Web** via Streamlit

## 🚀 Installation

### Option 1: Installation depuis GitHub (Recommandé)

```bash
pip install git+https://github.com/carlcgb/bot-prim.git
```

### Option 2: Installation locale

```bash
git clone https://github.com/carlcgb/bot-prim.git
cd bot-prim
pip install -r requirements.txt
pip install -e .
```

## 📖 Utilisation

### Interface CLI (Ligne de commande)

Une fois installé, utilisez la commande `primbot` :

```bash
# Mode interactif (chat) - Recommandé pour la première utilisation
primbot --interactive

# Le CLI va :
# 1. Demander votre clé API Gemini si non configurée
# 2. Vérifier et initialiser la base de connaissances si vide
# 3. Lancer une session de chat interactive

# Question unique
primbot "comment changer mon mot de passe"

# Avec options
primbot "erreur de connexion" --model gemini-2.5-flash

# Aide
primbot --help
```

#### Variables d'environnement pour CLI

```bash
# Pour Gemini (par défaut)
export GEMINI_API_KEY="votre_cle_api_gemini"

# Puis utilisez simplement
primbot --interactive
```

### Interface Web (Streamlit)

```bash
streamlit run app.py
```

Puis ouvrez votre navigateur à l'adresse indiquée (généralement `http://localhost:8501`).

## 🔧 Configuration

### Variables d'environnement / Secrets

Le bot utilise les secrets/variables d'environnement suivants :

- `GEMINI_API_KEY` - Clé API Google Gemini (requis)

#### Pour le développement local

Créez un fichier `.streamlit/secrets.toml` :

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
- **Cloudflare Pages**: Settings > Environment variables

## 📚 Base de connaissances

### État actuel

✅ **La base de connaissances est incluse dans le repository** (2630 documents, ~34 MB)
- Disponible immédiatement après déploiement
- Pas besoin d'initialisation manuelle
- Fonctionne même si le site PrimLogix est temporairement inaccessible

### Initialisation manuelle

Si vous devez réinitialiser ou mettre à jour la base :

```bash
python ingest.py
```

Cela va :
1. Scraper la documentation PrimLogix depuis https://aide.primlogix.com/prim/fr/5-8/
2. Extraire le contenu et les images
3. Créer/mettre à jour la base de données vectorielle avec ChromaDB

### Via l'interface Streamlit

L'app inclut un bouton d'initialisation automatique dans l'interface si la base est vide.

## 🌐 Déploiement

### Streamlit Cloud (Recommandé)

1. Poussez votre code sur GitHub
2. Connectez votre repo à [Streamlit Cloud](https://share.streamlit.io)
3. **Pour l'URL GitHub**, utilisez l'une de ces options :
   - **Option A (Recommandée)** : Cliquez sur "Switch to interactive picker" et sélectionnez votre repo et le fichier `app.py`
   - **Option B** : Utilisez l'URL directe : `https://github.com/carlcgb/bot-prim/blob/main/app.py`
4. Dans les paramètres de l'app, section "Secrets", ajoutez :
   ```toml
   GEMINI_API_KEY = "votre_cle_api_gemini"
   ```

✅ **Base de connaissances incluse** : La base de connaissances (2630 documents) est maintenant incluse dans le repository, donc elle sera automatiquement disponible après le déploiement sur Streamlit Cloud.

Si vous voyez "Base de connaissances vide", utilisez le bouton d'initialisation dans l'interface pour re-scraper la documentation.

## 📚 Documentation

- **[AGENT_GUIDE.md](AGENT_GUIDE.md)** : Guide complet pour obtenir les meilleures réponses de l'agent, comprendre les scores de pertinence, et optimiser vos questions
- **[RELEASE.md](RELEASE.md)** : Instructions pour créer des releases CLI

## 📁 Structure du projet

```
bot-prim/
├── app.py                 # Interface Streamlit principale
├── primbot_cli.py         # Interface CLI
├── agent.py               # Agent AI avec support Gemini
├── knowledge_base.py       # Gestion de la base de données vectorielle
├── scraper.py             # Scraping de la documentation PrimLogix
├── ingest.py              # Script d'ingestion des données
├── requirements.txt       # Dépendances Python
├── setup.py               # Configuration pour installation pip
└── README.md              # Ce fichier
```

## 🔒 Sécurité

⚠️ **Important**: Ne commitez JAMAIS de clés API dans le code. Utilisez toujours :
- Streamlit secrets pour Streamlit Cloud
- Variables d'environnement pour les autres plateformes
- GitHub Secrets pour GitHub Actions

Le fichier `.gitignore` est configuré pour exclure les fichiers contenant des secrets.

## 📝 Licence

Propriétaire - Dev-NTIC

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📞 Support

Pour toute question ou problème, ouvrez une issue sur [GitHub](https://github.com/carlcgb/bot-prim/issues).
