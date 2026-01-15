# 📦 PRIMBOT v1.0.4 - Release Notes

## 🚀 Installation Rapide

### Installation locale (Streamlit)

```bash
git clone https://github.com/carlcgb/bot-prim.git
cd bot-prim
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 🆕 Nouveautés v1.0.4

### ✨ Changements Majeurs

- 🔗 **URLs au lieu d'images** - Les réponses incluent maintenant uniquement des liens directs vers les pages pertinentes de l'aide en ligne, sans afficher d'images
- 📝 **Réponses compactes** - Format optimisé : chaque sous-étape en 1 phrase claire, pas de verbosité excessive
- 🔢 **Cohérence des étapes** - Chaque étape suit logiquement la précédente, pas d'étapes isolées ou non liées
- 🚀 **Performance améliorée** - Réponses plus rapides grâce à l'optimisation de la recherche (6 résultats au lieu de 10, filtrage par pertinence ≥40%)
- 📊 **Chunking optimisé** - Chunks de 800 caractères (au lieu de 1000) pour une meilleure pertinence
- 🔢 **Numérotation des étapes corrigée** - Les étapes commencent toujours par "Étape 1" et sont numérotées séquentiellement
- 🧹 **Code nettoyé** - Suppression complète du code lié aux images (plus de 200 lignes supprimées)

### 🔧 Améliorations Techniques

- ✅ **Optimisation de la recherche** : Réduction de 10 à 6 résultats, filtrage par pertinence ≥40%
- ✅ **Limitation du contexte** : Maximum 8000 caractères par document pour éviter de surcharger le LLM
- ✅ **Chunking optimisé** : 800 caractères avec overlap de 150 (au lieu de 1000/200)
- ✅ **Format compact** : Instructions système mises à jour pour des réponses concises mais complètes
- ✅ **Cohérence des étapes** : Instructions renforcées pour garantir que chaque étape suit logiquement la précédente
- ✅ **Numérotation forcée** : Instructions système renforcées pour garantir que les étapes commencent toujours par "Étape 1"
- ✅ **Retrait complet des images** : Dans l'interface web, seules les URLs vers les pages pertinentes sont affichées. Toutes les références aux images retirées des instructions système
- ✅ **Secrets Qdrant** : Vérification et chargement correct des secrets depuis Streamlit secrets et variables d'environnement
- ✅ **Nettoyage du code** : Suppression de plus de 200 lignes de code lié au traitement d'images

### 📚 Documentation

- ✅ README mis à jour avec les nouvelles fonctionnalités
- ✅ Notes de release complètes

### 🐛 Corrections

- ✅ Correction des erreurs de syntaxe dans `agent.py`
- ✅ Correction de l'indentation des blocs `try/except`
- ✅ Amélioration de la gestion des secrets pour le développement local

## 🎯 Utilisation

### Configuration

Créez un fichier `.env` à la racine :

```bash
GEMINI_API_KEY=votre_cle_gemini
USE_QDRANT=true
QDRANT_URL=https://votre-cluster.qdrant.io:6333
QDRANT_API_KEY=votre_cle_api
```

**Obtenez votre clé API Gemini gratuite :** [Google AI Studio](https://aistudio.google.com/)

### Base de Connaissances

La base Qdrant Cloud est déjà prête (≈2630 documents).  
Pour ré-ingérer (mise à jour) :

```bash
python ingest.py
```

### Démarrer l'interface web

```bash
streamlit run app.py
```

## 🔗 Liens Utiles

- **[Documentation complète](https://github.com/carlcgb/bot-prim#readme)**
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
