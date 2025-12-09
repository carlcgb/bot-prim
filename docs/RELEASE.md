# 📦 Guide de Release PRIMBOT CLI

## Créer une Release GitHub

### Méthode 1 : Via GitHub Web Interface (Recommandé)

1. Allez sur https://github.com/carlcgb/bot-prim/releases/new
2. Cliquez sur "Choose a tag" et créez un nouveau tag (ex: `v1.0.0`)
3. Remplissez les informations :
   - **Tag**: `v1.0.0`
   - **Release title**: `PRIMBOT CLI v1.0.0`
   - **Description**: 
     ```markdown
     ## 🎉 Première release de PRIMBOT CLI
     
     ### Nouvelles fonctionnalités
     - Interface CLI pour utilisation en ligne de commande
     - Mode interactif pour sessions de chat
     - Support Gemini AI
     - Installation via pip depuis GitHub
     
     ### Installation
     ```bash
     pip install git+https://github.com/carlcgb/bot-prim.git
     ```
     
     ### Utilisation
     ```bash
     primbot --interactive
     primbot "votre question"
     ```
     ```
4. Cochez "Set as the latest release"
5. Cliquez sur "Publish release"

### Méthode 2 : Via Git Tags (Automatique)

Le workflow GitHub Actions créera automatiquement la release quand vous poussez un tag :

```bash
# Créer et pousser un tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

Le workflow `.github/workflows/release.yml` va :
- Builder le package Python
- Créer une release GitHub avec les artefacts
- Uploader les fichiers .whl et .tar.gz

## Installation depuis GitHub

Une fois la release créée, les utilisateurs peuvent installer via :

```bash
# Installation depuis GitHub
pip install git+https://github.com/carlcgb/bot-prim.git

# Ou depuis un tag spécifique
pip install git+https://github.com/carlcgb/bot-prim.git@v1.0.0
```

## Tester localement avant release

```bash
# Installer en mode développement
pip install -e .

# Tester la CLI
primbot --help
primbot --interactive

# Builder le package
python -m build

# Vérifier les fichiers créés
ls dist/
```

## Versioning

Utilisez [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0) : Changements incompatibles
- **MINOR** (0.1.0) : Nouvelles fonctionnalités compatibles
- **PATCH** (0.0.1) : Corrections de bugs

## Prochaines étapes

Pour publier sur PyPI (optionnel) :
1. Créer un compte sur https://pypi.org
2. Configurer les credentials dans GitHub Secrets
3. Ajouter l'upload PyPI au workflow

