# 📦 PRIMBOT v1.0.3 - Guide d'Installation et Utilisation

## 🚀 Installation Rapide

### Option 1: Installation depuis GitHub (Recommandé)

```bash
pip install git+https://github.com/carlcgb/bot-prim.git
```

### Option 2: Installation depuis cette release

1. **Téléchargez les fichiers de cette release :**
   - `primbot-1.0.2-py3-none-any.whl` (recommandé pour Windows/Linux/macOS)
   - ou `primbot-1.0.2.tar.gz` (archive source)

2. **Installez le package :**
   ```bash
   # Pour le fichier .whl
   pip install primbot-1.0.2-py3-none-any.whl
   
   # Pour le fichier .tar.gz
   pip install primbot-1.0.2.tar.gz
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

## 🎯 Première Utilisation - Guide Étape par Étape

### Étape 1: Obtenir une Clé API Gemini (Gratuite)

1. Allez sur [Google AI Studio](https://aistudio.google.com/)
2. Connectez-vous avec votre compte Google
3. Cliquez sur "Get API Key"
4. Créez une nouvelle clé API
5. Copiez la clé (format: `AIzaSy...`)

**Note:** Le plan gratuit offre 60 requêtes/minute et 1500 requêtes/jour.

### Étape 2: Configurer PRIMBOT

**Option A: Configuration Interactive (Recommandée)**
```bash
primbot config
```
Suivez les prompts pour entrer votre clé API Gemini.

**Option B: Configuration Directe**
```bash
primbot config --gemini-key AIzaSyVOTRE_CLE_ICI
```

**Vérifier la configuration:**
```bash
primbot config --show
```

### Étape 3: Initialiser la Base de Connaissances

```bash
primbot ingest
```

**Ce qui se passe:**
- ✅ Scraping de la documentation PrimLogix
- ✅ Extraction du contenu et des captures d'écran pertinentes
- ✅ Création de la base de données vectorielle
- ✅ Indexation pour la recherche rapide

**Durée:** 5-10 minutes (une seule fois)

### Étape 4: Utiliser PRIMBOT

**Question unique:**
```bash
primbot ask "comment changer mon mot de passe"
```

**Mode interactif (chat):**
```bash
primbot ask --interactive
# ou
primbot ask -i
```

**Exemple de session interactive:**
```
$ primbot ask -i
🤖 PRIMBOT - Mode interactif
Tapez 'quit' pour quitter.

> comment créer un utilisateur
[PRIMBOT répond avec détails et captures d'écran...]

> et lui donner des permissions spécifiques?
[PRIMBOT répond en contexte...]

> quit
Au revoir!
```

📖 **Guide complet:** Consultez [docs/CLI_USAGE.md](docs/CLI_USAGE.md) pour un guide détaillé étape par étape.

## 📋 Commandes Disponibles

### Configuration
```bash
primbot config                    # Configuration interactive
primbot config --show            # Afficher la configuration actuelle
primbot config --gemini-key KEY  # Configurer la clé API Gemini
primbot config --ollama-url URL  # Configurer Ollama (local)
```

### Base de Connaissances
```bash
primbot ingest                   # Initialiser/mettre à jour la base
```

### Questions
```bash
primbot ask "question"           # Poser une question unique
primbot ask --interactive        # Mode chat interactif
primbot ask "q" --model MODEL    # Utiliser un modèle spécifique
primbot ask "q" --provider PROV  # Utiliser un fournisseur spécifique
```

### Aide
```bash
primbot --help                   # Aide générale
primbot config --help           # Aide pour config
primbot ask --help              # Aide pour ask
```

## 🔧 Configuration

La configuration est sauvegardée dans `~/.primbot/config.json` et inclut :
- Clé API Gemini
- URL Ollama (pour utilisation locale)
- Modèle par défaut
- Fournisseur par défaut

## 📚 Documentation

- **[Guide d'utilisation CLI](https://github.com/carlcgb/bot-prim/blob/main/docs/CLI_USAGE.md)** ⭐ - **Guide complet étape par étape** (installation, configuration, utilisation, exemples)
- **[Guide d'installation CLI](https://github.com/carlcgb/bot-prim/blob/main/docs/CLI_INSTALLATION.md)** - Instructions détaillées pour Windows/Linux/macOS et ajout au PATH
- **[Guide AI gratuit](https://github.com/carlcgb/bot-prim/blob/main/docs/FREE_AI_GUIDE.md)** - Options AI gratuites (Gemini et Ollama)
- **[Guide de l'agent](https://github.com/carlcgb/bot-prim/blob/main/docs/AGENT_GUIDE.md)** - Obtenir les meilleures réponses

## 🆘 Support

Pour toute question ou problème :
- Ouvrez une [issue sur GitHub](https://github.com/carlcgb/bot-prim/issues)
- Consultez la [documentation complète](https://github.com/carlcgb/bot-prim#readme)

## 🎉 Nouveautés de cette version

- ✨ **CLI amélioré** avec sous-commandes (`config`, `ingest`, `ask`)
- 📁 **Configuration persistante** (`~/.primbot/config.json`)
- 🔧 **Support Ollama amélioré** (100% gratuit, local)
- 📸 **Filtrage intelligent des images** - Seules les captures d'écran pertinentes (exclusion automatique des icônes/logos)
- 🎯 **Images pertinentes uniquement** - Filtrage par taille (≥100px) et mots-clés
- 🧹 **Code nettoyé et optimisé**
- 📦 **Package installable via pip**
- 📖 **Documentation complète** - Guide étape par étape dans `docs/CLI_USAGE.md`

---

## 🆕 Nouveautés v1.0.3

### ✨ Améliorations Majeures

- 📸 **Filtrage intelligent des images** - Exclusion automatique des icônes et logos, seules les vraies captures d'écran pertinentes sont incluses
- 🖼️ **Affichage d'images optimisé** - Préservation du ratio d'aspect, pas de déformation ou d'étirement
- 📖 **Documentation complète** - Nouveau guide étape par étape (`docs/CLI_USAGE.md`) avec exemples pratiques
- 📋 **Section ABOUT** - Présentation complète du projet dans le README
- 🧹 **Nettoyage du code** - Suppression des fichiers inutilisés, code optimisé
- 🗄️ **Gestion de la base de données** - Exclusion de la base de données du repository Git pour éviter de remplir GitHub

### 🔧 Corrections

- ✅ Correction de l'affichage des images (stretching résolu)
- ✅ Amélioration de la pertinence des images retournées
- ✅ Conversion automatique des URLs d'images relatives en absolues
- ✅ Meilleure gestion des erreurs et messages d'aide

### 📚 Documentation

- ✅ Guide complet d'utilisation CLI (`docs/CLI_USAGE.md`)
- ✅ Instructions étape par étape dans RELEASE_NOTES.md
- ✅ Section ABOUT dans le README
- ✅ Exemples pratiques et cas d'usage

---

**Version:** 1.0.3  
**Date:** Décembre 2024  
**Licence:** MIT

