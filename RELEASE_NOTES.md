# 📦 PRIMBOT v1.0.4 - Release Notes

## 🚀 Installation Rapide

### Option 1: Installation depuis GitHub (Recommandé)

```bash
pip install git+https://github.com/carlcgb/bot-prim.git
```

### Option 2: Installation depuis cette release

1. **Téléchargez les fichiers de cette release :**
   - `primbot-1.0.4-py3-none-any.whl` (recommandé pour Windows/Linux/macOS)
   - ou `primbot-1.0.4.tar.gz` (archive source)

2. **Installez le package :**
   ```bash
   # Pour le fichier .whl
   pip install primbot-1.0.4-py3-none-any.whl
   
   # Pour le fichier .tar.gz
   pip install primbot-1.0.4.tar.gz
   ```

### Option 3: Installation locale (Développement)

```bash
git clone https://github.com/carlcgb/bot-prim.git
cd bot-prim
pip install -r requirements.txt
pip install -e .
```

## ✅ Vérifier l'installation

```bash
primbot --help
```

Si la commande n'est pas trouvée, consultez [docs/CLI_INSTALLATION.md](https://github.com/carlcgb/bot-prim/blob/main/docs/CLI_INSTALLATION.md) pour ajouter `primbot` à votre PATH.

## 🆕 Nouveautés v1.0.4

### ✨ Changements Majeurs

- 🔗 **URLs au lieu d'images** - Les réponses incluent maintenant uniquement des liens directs vers les pages pertinentes de l'aide en ligne, sans afficher d'images
- 🚀 **Performance améliorée** - Réponses plus rapides grâce à l'optimisation de la recherche (6 résultats au lieu de 10, filtrage par pertinence ≥40%)
- 📊 **Chunking optimisé** - Chunks de 800 caractères (au lieu de 1000) pour une meilleure pertinence
- 🔢 **Numérotation des étapes corrigée** - Les étapes commencent toujours par "Étape 1" et sont numérotées séquentiellement
- 🧹 **Code nettoyé** - Suppression du code inutilisé lié aux images

### 🔧 Améliorations Techniques

- ✅ **Optimisation de la recherche** : Réduction de 10 à 6 résultats, filtrage par pertinence ≥40%
- ✅ **Limitation du contexte** : Maximum 8000 caractères par document pour éviter de surcharger le LLM
- ✅ **Chunking optimisé** : 800 caractères avec overlap de 150 (au lieu de 1000/200)
- ✅ **Numérotation forcée** : Instructions système renforcées pour garantir que les étapes commencent toujours par "Étape 1"
- ✅ **Retrait complet des images** : Dans toutes les versions (CLI, Web), seules les URLs vers les pages pertinentes sont affichées
- ✅ **Secrets Qdrant** : Vérification et chargement correct des secrets depuis Streamlit secrets et variables d'environnement

### 📚 Documentation

- ✅ README mis à jour avec les nouvelles fonctionnalités
- ✅ Notes de release complètes

### 🐛 Corrections

- ✅ Correction des erreurs de syntaxe dans `agent.py`
- ✅ Correction de l'indentation des blocs `try/except`
- ✅ Amélioration de la gestion des secrets pour le développement local

## 🎯 Utilisation

### Configuration

```bash
# Configuration interactive
primbot config

# Ou directement
primbot config --gemini-key VOTRE_CLE_API
```

**Obtenez votre clé API Gemini gratuite :** [Google AI Studio](https://aistudio.google.com/)

### Base de Connaissances

**Option A : Qdrant Cloud (Recommandé - déjà migré)**

La base de connaissances est déjà disponible dans Qdrant Cloud (2630 documents). Configurez simplement :

```bash
# Dans votre fichier .env ou variables d'environnement
USE_QDRANT=true
QDRANT_URL=https://votre-cluster.qdrant.io:6333
QDRANT_API_KEY=votre_cle_api
```

**Option B : ChromaDB Local**

```bash
primbot ingest
```

### Poser des Questions

```bash
# Question unique
primbot ask "comment créer un candidat"

# Mode interactif
primbot ask --interactive
```

## 📋 Commandes Disponibles

### Configuration
```bash
primbot config                    # Configuration interactive
primbot config --show            # Afficher la configuration actuelle
primbot config --gemini-key KEY  # Configurer la clé API Gemini
```

### Base de Connaissances
```bash
primbot ingest                   # Initialiser/mettre à jour la base (ChromaDB local)
```

### Questions
```bash
primbot ask "question"           # Poser une question unique
primbot ask --interactive        # Mode chat interactif
```

## 🔗 Liens Utiles

- **[Documentation complète](https://github.com/carlcgb/bot-prim#readme)**
- **[Guide d'utilisation CLI](https://github.com/carlcgb/bot-prim/blob/main/docs/CLI_USAGE.md)**
- **[Guide de migration Qdrant](https://github.com/carlcgb/bot-prim/blob/main/docs/QDRANT_MIGRATION.md)**
- **[Configuration GitHub Secrets](https://github.com/carlcgb/bot-prim/blob/main/docs/GITHUB_SECRETS.md)**

## 🆘 Support

Pour toute question ou problème :
- Ouvrez une [issue sur GitHub](https://github.com/carlcgb/bot-prim/issues)
- Consultez la [documentation complète](https://github.com/carlcgb/bot-prim#readme)

---

**Version:** 1.0.4  
**Date:** Décembre 2024  
**Licence:** MIT
