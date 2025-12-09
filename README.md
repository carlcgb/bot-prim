# 🤖 PRIMBOT

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub release](https://img.shields.io/badge/release-v1.0.3-green.svg)](https://github.com/carlcgb/bot-prim/releases)

Assistant intelligent pour la documentation PrimLogix avec Gemini AI et Ollama. **100% gratuit**, aucune carte de crédit requise.

## ✨ Fonctionnalités

- 🔍 Recherche intelligente dans la documentation PrimLogix (10 résultats, scores de pertinence)
- 📸 Captures d'écran pertinentes (filtrage automatique des icônes/logos, jusqu'à 8 images)
- 🤖 Support multi-IA : Gemini (gratuit) et Ollama (100% gratuit, local)
- 💻 Interface CLI et 🌐 Interface Web (Streamlit)
- 🎯 Réponses optimisées pour le débogage avec détails techniques

## 🚀 Installation Rapide

```bash
# Installation depuis GitHub
pip install git+https://github.com/carlcgb/bot-prim.git

# Vérifier l'installation
primbot --help
```

## 📖 Utilisation Rapide

### 1. Configuration (Première fois)

```bash
# Configuration interactive
primbot config

# Ou directement
primbot config --gemini-key VOTRE_CLE_API
```

**Obtenez votre clé API Gemini gratuite :** [Google AI Studio](https://aistudio.google.com/)

### 2. Initialiser la base de connaissances

```bash
primbot ingest  # 5-10 minutes, une seule fois
```

### 3. Utiliser PRIMBOT

```bash
# Question unique
primbot ask "comment changer mon mot de passe"

# Mode interactif (chat)
primbot ask --interactive
```

📖 **Guide complet étape par étape :** [docs/CLI_USAGE.md](docs/CLI_USAGE.md)

## 📋 Commandes Principales

| Commande | Description |
|----------|-------------|
| `primbot config` | Configuration interactive |
| `primbot config --show` | Afficher la configuration |
| `primbot ingest` | Initialiser/mettre à jour la base de connaissances |
| `primbot ask "question"` | Poser une question |
| `primbot ask -i` | Mode interactif (chat) |
| `primbot ask "q" --model MODEL` | Utiliser un modèle spécifique |
| `primbot ask "q" --provider local` | Utiliser Ollama (local) |

## 🌐 Interface Web

```bash
streamlit run app.py
```

Ouvrez votre navigateur à `http://localhost:8501`

## 🔧 Configuration

### Options AI Gratuites

1. **Google Gemini** (Recommandé) - [Obtenir une clé gratuite](https://aistudio.google.com/)
   - 60 requêtes/minute, 1500 requêtes/jour
   - Pas de carte de crédit requise

2. **Ollama** (100% gratuit, local) - [Télécharger](https://ollama.ai/)
   - Fonctionne sur votre machine
   - Aucune clé API requise
   - `ollama pull llama3.1` puis `ollama serve`

📖 **Guide complet :** [docs/FREE_AI_GUIDE.md](docs/FREE_AI_GUIDE.md)

### Variables d'Environnement

```bash
export GEMINI_API_KEY="votre_cle_api"
```

Pour Streamlit Cloud, ajoutez dans les Secrets :
```toml
GEMINI_API_KEY = "votre_cle_api"
```

## 📚 Base de Connaissances

La base de connaissances doit être initialisée avant la première utilisation :

```bash
primbot ingest
```

**Ce qui se passe :**
- Scraping de https://aide.primlogix.com/prim/fr/5-8/
- Extraction du contenu et captures d'écran pertinentes
- Filtrage automatique des icônes/logos (seules les vraies captures d'écran ≥100px)
- Création de la base de données vectorielle ChromaDB

**Durée :** 5-10 minutes (une seule fois)

## 📚 Documentation

- **[CLI_USAGE.md](docs/CLI_USAGE.md)** ⭐ - Guide complet étape par étape
- **[CLI_INSTALLATION.md](docs/CLI_INSTALLATION.md)** - Installation détaillée et PATH
- **[FREE_AI_GUIDE.md](docs/FREE_AI_GUIDE.md)** - Options AI gratuites
- **[AGENT_GUIDE.md](docs/AGENT_GUIDE.md)** - Optimiser vos questions

## 🌐 Déploiement

### Streamlit Cloud

1. Poussez votre code sur GitHub
2. Connectez à [Streamlit Cloud](https://share.streamlit.io)
3. Ajoutez le secret `GEMINI_API_KEY` dans les paramètres
4. Initialisez la base de connaissances via le bouton dans l'interface

## 📁 Structure du Projet

```
bot-prim/
├── app.py                 # Interface Streamlit
├── primbot_cli.py         # Interface CLI
├── agent.py               # Agent AI (Gemini/Ollama)
├── knowledge_base.py      # Base de données vectorielle
├── scraper.py             # Scraping documentation
├── ingest.py              # Script d'ingestion
├── storage_local.py       # Stockage local (SQLite)
├── docs/                  # Documentation
└── chroma_db/             # Base de données (générée localement)
```

## 🛠️ Technologies

- **AI/ML**: Google Gemini API, Ollama (OpenAI-compatible)
- **Vector DB**: ChromaDB
- **Embeddings**: Sentence Transformers
- **Web**: Streamlit
- **Language**: Python 3.8+

## 📖 À Propos

**PRIMBOT** est un assistant intelligent spécialement conçu pour aider les utilisateurs de PrimLogix à résoudre leurs problèmes techniques et naviguer dans la documentation.

- 🎯 **Objectif** : Simplifier l'accès à la documentation PrimLogix
- 🆓 **100% gratuit** : Aucune carte de crédit, plan gratuit généreux
- 📸 **Images pertinentes** : Filtrage intelligent des captures d'écran
- 💻 **Multi-plateforme** : CLI et interface web

Développé par **Dev-NTIC** pour améliorer l'expérience utilisateur PrimLogix.

## 🔒 Sécurité

⚠️ **Important** : Ne commitez JAMAIS de clés API. Utilisez :
- Streamlit secrets (Streamlit Cloud)
- Variables d'environnement (local)
- GitHub Secrets (GitHub Actions)

## 📝 Licence

Propriétaire - Dev-NTIC

## 🤝 Contribution

Les contributions sont les bienvenues ! Ouvrez une [issue](https://github.com/carlcgb/bot-prim/issues) ou une pull request.

## 🆘 Support

- 📖 [Documentation complète](docs/)
- 🐛 [Signaler un bug](https://github.com/carlcgb/bot-prim/issues)
- 💬 [Ouvrir une discussion](https://github.com/carlcgb/bot-prim/discussions)
