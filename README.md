# 🤖 PRIMBOT

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/release/carlcgb/bot-prim.svg)](https://github.com/carlcgb/bot-prim/releases)
[![Streamlit](https://img.shields.io/badge/Streamlit-Cloud-orange.svg)](https://primbot.streamlit.app/)

Un agent d'assistance intelligent pour la documentation PrimLogix utilisant Gemini AI.

## 📖 À Propos

**PRIMBOT** est un assistant intelligent spécialement conçu pour aider les utilisateurs de PrimLogix à résoudre leurs problèmes techniques et à naviguer dans la documentation.

### 🎯 Objectif

PRIMBOT vise à :
- **Simplifier l'accès** à la documentation PrimLogix
- **Accélérer la résolution** des problèmes techniques
- **Fournir des réponses contextuelles** avec captures d'écran pertinentes
- **Offrir une solution 100% gratuite** sans nécessiter de carte de crédit

### ✨ Caractéristiques Principales

- 🔍 **Recherche intelligente** dans toute la documentation PrimLogix
- 📸 **Captures d'écran pertinentes** extraites automatiquement de l'aide en ligne
- 🤖 **Support multi-IA** : Gemini (gratuit) et Ollama (100% gratuit, local)
- 💻 **Interface CLI** pour utilisation en ligne de commande
- 🌐 **Interface Web** via Streamlit pour une utilisation intuitive
- 🎯 **Réponses optimisées** pour le débogage avec détails techniques

### 🛠️ Technologies Utilisées

- **AI/ML**: Google Gemini API, Ollama (OpenAI-compatible)
- **Vector Database**: ChromaDB pour la recherche sémantique
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Web Framework**: Streamlit pour l'interface web
- **Scraping**: BeautifulSoup4, html2text
- **Language**: Python 3.8+

### 👥 Public Cible

- Utilisateurs de PrimLogix cherchant de l'aide
- Administrateurs système PrimLogix
- Support technique
- Développeurs intégrant PrimLogix

### 🆓 Gratuit et Open Source

PRIMBOT est **100% gratuit** :
- ✅ Aucune carte de crédit requise
- ✅ Plan gratuit Gemini généreux (60 req/min, 1500 req/jour)
- ✅ Option Ollama 100% locale et gratuite
- ✅ Code source ouvert sur GitHub

### 📊 Statistiques

- 📚 **Documentation indexée** : Toute la documentation PrimLogix (aide.primlogix.com/prim/fr/5-8/)
- 🖼️ **Images filtrées** : Seules les captures d'écran pertinentes (≥100px, filtrage automatique des icônes)
- 🔍 **Recherche** : 10 résultats par requête pour un contexte optimal
- 📸 **Images par réponse** : Jusqu'à 8 captures d'écran les plus pertinentes

### 🚀 Développement

Développé par **Dev-NTIC** pour améliorer l'expérience utilisateur PrimLogix.

**Contributions bienvenues !** N'hésitez pas à ouvrir une issue ou une pull request.

## ✨ Fonctionnalités

- 🔍 **Recherche intelligente** dans la base de connaissances PrimLogix (10 résultats pour meilleur contexte)
- 🤖 **Support multi-IA gratuit** : Gemini (gratuit) et Ollama (100% gratuit, local)
- 📊 **Scores de pertinence** pour évaluer la qualité des résultats
- 📸 **Affichage de captures d'écran pertinentes** de la documentation (jusqu'à 8 images, filtrage automatique des icônes/logos)
- 🎯 **Réponses optimisées pour le débogage** avec détails techniques et exemples
- 🆓 **100% gratuit** - Aucune carte de crédit requise
- 🇫🇷 **Interface en français**
- 💻 **Interface CLI** pour utilisation en ligne de commande
- 🌐 **Interface Web** via Streamlit

## 🚀 Installation

### Option 1: Installation depuis GitHub (Recommandé)

```bash
pip install git+https://github.com/carlcgb/bot-prim.git
```

Après l'installation, la commande `primbot` sera disponible dans votre terminal.

### Option 2: Installation depuis une release GitHub

1. Téléchargez la dernière release depuis [GitHub Releases](https://github.com/carlcgb/bot-prim/releases)
2. Installez le package :
   ```bash
   pip install primbot-*.whl
   # ou
   pip install primbot-*.tar.gz
   ```

### Option 3: Installation locale (Développement)

```bash
git clone https://github.com/carlcgb/bot-prim.git
cd bot-prim
pip install -r requirements.txt
pip install -e .
```

### ✅ Vérifier l'installation

```bash
primbot --help
```

Si la commande n'est pas trouvée, consultez [docs/CLI_INSTALLATION.md](docs/CLI_INSTALLATION.md) pour ajouter `primbot` à votre PATH.

## 📖 Utilisation

### Interface CLI (Ligne de commande)

Une fois installé, la commande `primbot` est disponible dans votre terminal.

#### 🚀 Première utilisation (Setup rapide)

```bash
# 1. Configurer l'API Gemini (gratuit)
primbot config --gemini-key VOTRE_CLE_API
# Ou configuration interactive:
primbot config

# 2. Initialiser la base de connaissances
primbot ingest

# 3. Poser une question
primbot ask "comment changer mon mot de passe"
```

#### 📋 Commandes disponibles

**Configuration:**
```bash
# Configuration interactive
primbot config

# Configurer la clé API Gemini
primbot config --gemini-key VOTRE_CLE

# Configurer Ollama (100% gratuit, local)
primbot config --ollama-url http://localhost:11434/v1

# Afficher la configuration actuelle
primbot config --show
```

**Base de connaissances:**
```bash
# Initialiser/mettre à jour la base de connaissances
primbot ingest
```

**Poser des questions:**
```bash
# Question unique
primbot ask "comment changer mon mot de passe"

# Mode interactif (chat)
primbot ask --interactive
# ou simplement
primbot ask -i

# Avec options
primbot ask "erreur de connexion" --model gemini-2.5-flash --provider gemini

# Utiliser Ollama (local, 100% gratuit)
primbot ask "question" --provider local --model llama3.1
```

**Compatibilité (ancien format):**
```bash
# Les anciennes commandes fonctionnent toujours
primbot "comment changer mon mot de passe"
primbot --interactive
```

#### 🔧 Configuration

La configuration est sauvegardée dans `~/.primbot/config.json` et inclut:
- Clé API Gemini
- URL Ollama
- Modèle par défaut
- Fournisseur par défaut

#### Variables d'environnement

Vous pouvez aussi utiliser des variables d'environnement:

```bash
# Pour Gemini
export GEMINI_API_KEY="votre_cle_api_gemini"

# Puis utilisez simplement
primbot ask "question"
```

### Interface Web (Streamlit)

```bash
streamlit run app.py
```

Puis ouvrez votre navigateur à l'adresse indiquée (généralement `http://localhost:8501`).

## 🔧 Configuration

### Options AI Gratuites

PRIMBOT supporte deux options gratuites :

1. **Google Gemini** (Recommandé) - Plan gratuit généreux, rapide, facile à configurer
   - Obtenez votre clé gratuite sur [Google AI Studio](https://aistudio.google.com/)
   - 60 requêtes/minute, 1500 requêtes/jour gratuitement
   - Pas de carte de crédit requise

2. **Ollama** (100% gratuit, local) - Fonctionne sur votre machine, aucune clé API
   - Téléchargez sur [ollama.ai](https://ollama.ai/)
   - Installez un modèle: `ollama pull llama3.1`
   - Lancez: `ollama serve`

📖 **Guide complet**: Voir [docs/FREE_AI_GUIDE.md](docs/FREE_AI_GUIDE.md) pour tous les détails.

### Variables d'environnement / Secrets

Le bot utilise les secrets/variables d'environnement suivants :

- `GEMINI_API_KEY` - Clé API Google Gemini (optionnel, seulement pour Gemini)

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

### Initialisation

La base de connaissances doit être initialisée avant la première utilisation :

**Via CLI:**
```bash
primbot ingest
```

**Via Streamlit:**
L'app inclut un bouton d'initialisation automatique dans l'interface si la base est vide.

**Manuellement:**
```bash
python ingest.py
```

Cela va :
1. Scraper la documentation PrimLogix depuis https://aide.primlogix.com/prim/fr/5-8/
2. Extraire le contenu et les **captures d'écran pertinentes** (filtrage automatique des icônes/logos)
3. Créer/mettre à jour la base de données vectorielle avec ChromaDB

### Filtrage intelligent des images

Le système filtre automatiquement :
- ✅ **Inclus** : Vraies captures d'écran de l'interface (≥100px, avec mots-clés pertinents)
- ❌ **Exclus** : Icônes, logos, boutons (<100px, patterns d'icônes dans le nom)

Seules les images pertinentes et de qualité sont stockées pour compléter les réponses.

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

⚠️ **Note importante** : La base de connaissances n'est **pas** incluse dans le repository pour éviter de remplir GitHub. Vous devez l'initialiser après le déploiement :

1. Utilisez le bouton d'initialisation dans l'interface Streamlit
2. Ou exécutez `primbot ingest` via le CLI

## 📚 Documentation

Toute la documentation est disponible dans le dossier [`docs/`](docs/) :

- **[docs/CLI_USAGE.md](docs/CLI_USAGE.md)** ⭐ : **Guide complet étape par étape** pour utiliser le CLI (installation, configuration, utilisation)
- **[docs/CLI_INSTALLATION.md](docs/CLI_INSTALLATION.md)** : Guide d'installation du CLI et ajout au PATH
- **[docs/FREE_AI_GUIDE.md](docs/FREE_AI_GUIDE.md)** ⭐ : Guide complet des options AI gratuites (Gemini et Ollama)
- **[docs/AGENT_GUIDE.md](docs/AGENT_GUIDE.md)** : Guide complet pour obtenir les meilleures réponses de l'agent, comprendre les scores de pertinence, et optimiser vos questions
- **[docs/RELEASE.md](docs/RELEASE.md)** : Instructions pour créer des releases CLI
- **[docs/DEPLOY_KB.md](docs/DEPLOY_KB.md)** : Guide de déploiement de la base de connaissances

## 📁 Structure du projet

```
bot-prim/
├── app.py                 # Interface Streamlit principale
├── primbot_cli.py         # Interface CLI
├── agent.py               # Agent AI avec support Gemini
├── knowledge_base.py      # Gestion de la base de données vectorielle
├── scraper.py             # Scraping de la documentation PrimLogix
├── ingest.py              # Script d'ingestion des données
├── requirements.txt       # Dépendances Python
├── setup.py               # Configuration pour installation pip
├── pyproject.toml         # Configuration Python moderne
├── MANIFEST.in            # Fichiers à inclure dans le package
├── packages.txt           # Dépendances système (Streamlit Cloud)
├── docs/                  # Documentation
│   ├── AGENT_GUIDE.md
│   ├── RELEASE.md
│   └── DEPLOY_KB.md
├── chroma_db/             # Base de données vectorielle (générée localement, non versionnée)
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
