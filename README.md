# 🤖 PRIMBOT

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub release](https://img.shields.io/badge/release-v1.0.4-green.svg)](https://github.com/carlcgb/bot-prim/releases)

Assistant intelligent en support client pour la documentation PrimLogix avec Gemini AI et Ollama. **100% gratuit**, aucune carte de crédit requise.

## ✨ Fonctionnalités

- 🔍 **Recherche intelligente** : 6 résultats optimisés avec scores de pertinence dans la documentation PrimLogix
- 🔗 **Liens directs** : URLs vers les pages pertinentes de l'aide en ligne (sans images)
- 🤖 **Support multi-IA** : Gemini (gratuit) et Ollama (100% gratuit, local)
- 💻 **Multi-interface** : CLI et interface Web (Streamlit)
- 🎯 **Réponses orientées support client** : Compactes, complètes, avec étapes cohérentes et logiquement liées
- 📝 **Format uniforme** : Toutes les étapes utilisent le même format, numérotées séquentiellement (Étape 1, 2, 3...)
- 👍👎 **Système de feedback** : Amélioration continue basée sur vos retours

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

La clé API est automatiquement sauvegardée et pré-remplie dans l'interface web.

### 2. Configurer la base de connaissances

**Option A : Qdrant Cloud (Recommandé - déjà migré)**

La base de connaissances est déjà disponible dans Qdrant Cloud (2630 documents). Configurez simplement :

```bash
# Créez un fichier .env
USE_QDRANT=true
QDRANT_URL=https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=votre_cle_qdrant
GEMINI_API_KEY=votre_cle_gemini
```

**Option B : ChromaDB Local**

```bash
primbot ingest  # 5-10 minutes, une seule fois
```

**Ce qui se passe :**
- Scraping de https://aide.primlogix.com/prim/fr/5-8/
- Extraction du contenu textuel de la documentation
- Création de la base de données vectorielle ChromaDB locale

### 3. Tester le Bot

**Interface Web (Recommandé) :**
```bash
streamlit run app.py
```
Ouvrez votre navigateur à `http://localhost:8501`

**CLI :**
```bash
# Question unique
primbot ask "comment ajouter un employé"

# Mode interactif (chat)
primbot ask --interactive
```

**Fonctionnalités de l'interface web :**
- 💬 Chat interactif avec historique
- 👍👎 Feedback après chaque réponse
- 📊 Statistiques de satisfaction en temps réel
- 🔗 Liens directs vers la documentation

📚 **Guide de test complet** : Voir [docs/LOCAL_TESTING.md](docs/LOCAL_TESTING.md)

## 📋 Commandes CLI

| Commande | Description |
|----------|-------------|
| `primbot config` | Configuration interactive |
| `primbot config --show` | Afficher la configuration |
| `primbot ingest` | Initialiser/mettre à jour la base de connaissances |
| `primbot ask "question"` | Poser une question |
| `primbot ask -i` | Mode interactif (chat) |
| `primbot ask "q" --model MODEL` | Utiliser un modèle spécifique |
| `primbot ask "q" --provider local` | Utiliser Ollama (local) |

## 🔧 Configuration

### Options AI Gratuites

1. **Google Gemini** (Recommandé) - [Obtenir une clé gratuite](https://aistudio.google.com/)
   - 60 requêtes/minute, 1500 requêtes/jour
   - Pas de carte de crédit requise
   - Clé automatiquement sauvegardée et pré-remplie

2. **Ollama** (100% gratuit, local) - [Télécharger](https://ollama.ai/)
   - Fonctionne sur votre machine
   - Aucune clé API requise
   - `ollama pull llama3.1` puis `ollama serve`

### Variables d'Environnement

```bash
# Windows PowerShell
$env:GEMINI_API_KEY="votre_cle_api"

# Linux/Mac
export GEMINI_API_KEY="votre_cle_api"
```

Pour Streamlit Cloud, ajoutez dans les Secrets :
```toml
GEMINI_API_KEY = "votre_cle_api"
```

## 🎯 Caractéristiques Avancées

### Système de Feedback
- 👍👎 **Boutons de feedback** après chaque réponse
- 📊 **Statistiques en temps réel** : Taux de satisfaction affiché dans la sidebar
- 🔄 **Amélioration continue** : Le bot s'adapte automatiquement aux feedbacks
- 💬 **Commentaires détaillés** : Possibilité d'expliquer pourquoi une réponse n'était pas utile

### Performance Optimisée
- ✅ **Recherche rapide** : 6 résultats optimisés (au lieu de 10) pour des réponses plus rapides
- ✅ **Filtrage par pertinence** : Seulement les résultats avec score ≥40%
- ✅ **Contexte limité** : Maximum 8000 caractères par document
- ✅ **Chunking optimisé** : 800 caractères pour une meilleure pertinence

### Réponses Orientées Support Client
- 👋 **Accueil empathique** : Ton amical et professionnel
- 📋 **Structure claire** : Étapes numérotées compactes mais complètes (format uniforme)
- 🔗 **Liens directs** : Accès immédiat aux sections pertinentes de l'aide en ligne
- 🔢 **Cohérence** : Chaque étape suit logiquement la précédente, pas d'étapes isolées
- ✅ **Vérification** : Demande si le problème est résolu

## 💡 Conseils pour Obtenir les Meilleures Réponses

### Soyez Spécifique
- ❌ "Ça ne marche pas" → ✅ "Erreur lors de l'export CSV : le champ 'Date facturation' est vide"
- ❌ "Comment faire un client ?" → ✅ "Procédure détaillée pour créer un nouveau client avec tous les champs obligatoires"

### Utilisez des Termes Techniques
- Noms de champs exacts (ex: "Date facturation", "ID candidat")
- Codes d'erreur (ex: "E001", "Erreur 404")
- Noms de fonctionnalités (ex: "Export CSV", "Gestion des absences")

### Donnez du Contexte
- Décrivez ce que vous avez déjà essayé
- Mentionnez les messages d'erreur exacts
- Indiquez où vous êtes dans l'interface

## 📚 Documentation Complémentaire

- **[LOCAL_TESTING.md](docs/LOCAL_TESTING.md)** ⭐ - Guide complet pour tester localement
- **[CLI_USAGE.md](docs/CLI_USAGE.md)** ⭐ - Guide complet étape par étape
- **[CLI_INSTALLATION.md](docs/CLI_INSTALLATION.md)** - Installation détaillée et PATH
- **[FREE_AI_GUIDE.md](docs/FREE_AI_GUIDE.md)** - Options AI gratuites
- **[AGENT_GUIDE.md](docs/AGENT_GUIDE.md)** - Conseils avancés pour optimiser vos questions
- **[QDRANT_MIGRATION.md](docs/QDRANT_MIGRATION.md)** - Migration vers Qdrant Cloud (gratuit)
- **[GITHUB_SECRETS.md](docs/GITHUB_SECRETS.md)** - Configuration GitHub Secrets

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
- **Vector DB**: ChromaDB (local) ou Qdrant Cloud (gratuit, 1GB)
- **Embeddings**: Sentence Transformers
- **Web**: Streamlit
- **Language**: Python 3.8+

## 📖 À Propos

**PRIMBOT** est un assistant intelligent en support client spécialement conçu pour aider les utilisateurs de PrimLogix à résoudre leurs problèmes techniques et naviguer dans la documentation.

- 🎯 **Objectif** : Simplifier l'accès à la documentation PrimLogix avec un support client de qualité
- 🆓 **100% gratuit** : Aucune carte de crédit, plan gratuit généreux
- 📝 **Réponses optimisées** : Format compact, étapes cohérentes, liens directs vers la documentation
- 💻 **Multi-plateforme** : CLI et interface web
- 🔄 **Amélioration continue** : Système de feedback pour s'améliorer constamment

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
