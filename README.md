# 🦸‍♂️ DEBUGEX

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub release](https://img.shields.io/badge/release-v1.0.4-green.svg)](https://github.com/carlcgb/bot-prim/releases)

Agent IA pour l'aide en ligne PrimLogix avec Gemini AI. **100% gratuit**, aucune carte de crédit requise.

## ✨ Fonctionnalités

- 🔍 **Recherche intelligente optimisée** : Expansion automatique des requêtes avec synonymes, 8 résultats optimisés avec scores de pertinence
- 🔗 **Liens précis** : URLs exactes vers les sections spécifiques de l'aide en ligne utilisées dans la réponse
- 📸 **Images contextuelles prioritaires** : Captures d'écran complètes de l'interface PrimLogix priorisées (max 400×300px) avec modal plein écran au clic. Système de scoring intelligent pour exclure emojis/icônes et prioriser les vraies captures d'écran.
- 🌙 **Mode sombre** : Interface Streamlit en mode sombre par défaut
- 🤖 **Gemini AI** : Support exclusif Gemini (gratuit, 60 req/min, 1500 req/jour)
- 💻 **Interface Web (Streamlit)** : Application cloud et locale
- 🎯 **Réponses step-by-step détaillées** : Navigation complète avec chemins exacts (Menu > Sous-menu > Option)
- 📝 **Format uniforme** : Toutes les étapes utilisent le même format, numérotées séquentiellement (Étape 1, 2, 3...)
- 🌐 **Recherche internet complémentaire** : Utilisation automatique de DuckDuckGo pour compléter les détails techniques (ports SMTP, serveurs, etc.)
- 👍👎 **Système de feedback** : Amélioration continue basée sur vos retours

## 🚀 Installation

### Local (développement)

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 📖 Utilisation Rapide

### 1. Configuration (Première fois)

Créez un fichier `.env` à la racine du projet :

```bash
GEMINI_API_KEY=votre_cle_gemini
USE_QDRANT=true
QDRANT_URL=https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=votre_cle_qdrant
```

**Obtenez votre clé API Gemini gratuite :** [Google AI Studio](https://aistudio.google.com/)

### 2. Base de connaissances (Qdrant Cloud)

La base de connaissances est déjà disponible dans Qdrant Cloud (≈2630 documents).  
Pour ré-ingérer (mise à jour) :

```bash
python ingest.py
```

### 3. Démarrer l'interface web

```bash
streamlit run app.py
```

Ouvrez votre navigateur à `http://localhost:8501`

**Fonctionnalités de l'interface web :**
- 💬 Chat interactif avec historique
- 👍👎 Feedback après chaque réponse
- 📊 Statistiques de satisfaction en temps réel
- 🔗 Liens directs vers la documentation

📚 **Guide de test complet** : Voir [docs/LOCAL_TESTING.md](docs/LOCAL_TESTING.md)

## 🔧 Configuration

### Options AI Gratuites

1. **Google Gemini** (Recommandé) - [Obtenir une clé gratuite](https://aistudio.google.com/)
   - 60 requêtes/minute, 1500 requêtes/jour
   - Pas de carte de crédit requise
   - Clé automatiquement sauvegardée et pré-remplie


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
- ✅ **Recherche rapide** : Expansion intelligente des requêtes avec synonymes, 8 variations de requête pour une meilleure couverture
- ✅ **Filtrage par pertinence** : Seulement les résultats avec score ≥30% (seuil abaissé pour plus de résultats pertinents)
- ✅ **Contexte optimisé** : Maximum 6000 caractères pour documents très pertinents (≥70%), 4000 pour pertinents (≥50%), 3000 pour modérés
- ✅ **Chunking optimisé** : 800 caractères pour une meilleure pertinence
- ✅ **Recherches multiples** : 4 variations de requête pour une meilleure couverture
- ✅ **Priorisation images** : Système de scoring pour prioriser les captures d'écran complètes de l'interface plutôt que les emojis/icônes

### Réponses Orientées Support Client
- 👋 **Accueil empathique** : Ton amical et professionnel
- 📋 **Structure claire** : Étapes numérotées compactes mais complètes (format uniforme)
- 🗺️ **Navigation détaillée** : Chemins complets pour chaque action (ex: "Administration > Paramètres > Configuration E-mail > Protocoles de courriel")
- 🔗 **Liens précis** : URLs exactes vers les sections spécifiques utilisées dans la réponse
- 📸 **Images contextuelles** : Captures d'écran de l'interface PrimLogix (max 400×300px) avec modal plein écran au clic
- 🔢 **Cohérence** : Chaque étape suit logiquement la précédente, pas d'étapes isolées
- ✅ **Vérification** : Demande si le problème est résolu
- 🌐 **Compléments techniques** : Recherche internet automatique pour ports SMTP, serveurs, etc. si non disponibles dans la doc

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
├── agent.py               # Agent AI (Gemini)
├── knowledge_base.py      # Base de données vectorielle
├── scraper.py             # Scraping documentation
├── ingest.py              # Script d'ingestion
├── storage_local.py       # Stockage local (SQLite)
├── docs/                  # Documentation
└── chroma_db/             # Base de données locale (fallback)
```

## 🛠️ Technologies

- **AI/ML**: Google Gemini API (exclusif)
- **Vector DB**: ChromaDB (local par défaut) ou Qdrant Cloud (optionnel, gratuit 1GB)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Web**: Streamlit (mode sombre, layout centered)
- **Internet Search**: ddgs (DuckDuckGo Search - pour compléments techniques)
- **Language**: Python 3.8+
- **Robustesse**: Gestion d'erreurs avancée avec fallback automatique vers ChromaDB si Qdrant échoue

## 📖 À Propos

**DEBUGEX** est un agent IA intelligent spécialement conçu pour aider les utilisateurs de PrimLogix à résoudre leurs problèmes techniques et naviguer dans la documentation de l'aide en ligne.

- 🎯 **Objectif** : Simplifier l'accès à la documentation PrimLogix avec un support client de qualité
- 🆓 **100% gratuit** : Aucune carte de crédit, plan gratuit généreux
- 📝 **Réponses optimisées** : Format compact, étapes cohérentes, liens directs vers la documentation
- 💻 **Interface web** : Streamlit (cloud/local)
- 🔄 **Amélioration continue** : Système de feedback pour s'améliorer constamment
- 🛡️ **Robuste** : Gestion d'erreurs avancée, fallback automatique, import sécurisé

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
