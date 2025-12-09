# 📦 PRIMBOT v1.0.2 - Installation Guide

## 🚀 Installation rapide

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

## 🎯 Première utilisation

### 1. Configuration

```bash
# Configuration interactive
primbot config

# Ou configurer directement la clé API Gemini
primbot config --gemini-key VOTRE_CLE_API
```

**Obtenez votre clé API Gemini gratuite :** https://aistudio.google.com/

### 2. Initialiser la base de connaissances

```bash
primbot ingest
```

Cela va scraper la documentation PrimLogix et créer la base de connaissances (5-10 minutes).

### 3. Utiliser PRIMBOT

```bash
# Question unique
primbot ask "comment changer mon mot de passe"

# Mode interactif (chat)
primbot ask --interactive
```

## 📋 Commandes disponibles

- `primbot config` - Configurer l'API Gemini et Ollama
- `primbot ingest` - Initialiser la base de connaissances
- `primbot ask "question"` - Poser une question
- `primbot ask --interactive` - Mode chat interactif

## 🔧 Configuration

La configuration est sauvegardée dans `~/.primbot/config.json` et inclut :
- Clé API Gemini
- URL Ollama (pour utilisation locale)
- Modèle par défaut
- Fournisseur par défaut

## 📚 Documentation

- **[Guide d'installation CLI](https://github.com/carlcgb/bot-prim/blob/main/docs/CLI_INSTALLATION.md)** - Instructions détaillées pour Windows/Linux/macOS
- **[Guide AI gratuit](https://github.com/carlcgb/bot-prim/blob/main/docs/FREE_AI_GUIDE.md)** - Options AI gratuites (Gemini et Ollama)
- **[Guide de l'agent](https://github.com/carlcgb/bot-prim/blob/main/docs/AGENT_GUIDE.md)** - Obtenir les meilleures réponses

## 🆘 Support

Pour toute question ou problème :
- Ouvrez une [issue sur GitHub](https://github.com/carlcgb/bot-prim/issues)
- Consultez la [documentation complète](https://github.com/carlcgb/bot-prim#readme)

## 🎉 Nouveautés de cette version

- ✨ CLI amélioré avec sous-commandes (`config`, `ingest`, `ask`)
- 📁 Gestion de configuration persistante (`~/.primbot/config.json`)
- 🔧 Support Ollama amélioré (100% gratuit, local)
- 🧹 Code nettoyé et optimisé
- 📦 Package installable via pip

---

**Version:** 1.0.2  
**Date:** 2024  
**Licence:** MIT

