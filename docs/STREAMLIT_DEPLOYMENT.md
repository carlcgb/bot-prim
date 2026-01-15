# 🚀 Guide de Déploiement Streamlit Cloud

Guide complet pour déployer PRIMBOT sur Streamlit Cloud.

## 📋 Prérequis

1. **Compte GitHub** avec votre repository `bot-prim`
2. **Compte Streamlit Cloud** (gratuit) : [share.streamlit.io](https://share.streamlit.io)
3. **Clé API Gemini** : [Google AI Studio](https://aistudio.google.com/)

## 🔧 Étape 1 : Préparer le Repository

### 1.1 Vérifier les fichiers nécessaires

Assurez-vous que ces fichiers sont présents dans votre repository :

```
bot-prim/
├── app.py                    # ✅ Interface Streamlit principale
├── agent.py                  # ✅ Agent AI
├── knowledge_base.py         # ✅ Base de connaissances
├── knowledge_base_qdrant.py  # ✅ Support Qdrant Cloud
├── scraper.py                # ✅ Scraping documentation
├── storage_local.py          # ✅ Stockage local
├── requirements.txt          # ✅ Dépendances
├── .streamlit/
│   └── config.toml          # ✅ Configuration Streamlit
└── README.md                 # ✅ Documentation
```

### 1.2 Vérifier requirements.txt

Votre `requirements.txt` doit inclure :

```txt
streamlit
beautifulsoup4
chromadb
qdrant-client
sentence-transformers
html2text
requests
google-genai
pillow
ddgs
```

## 🔑 Étape 2 : Configurer les Secrets Streamlit

### 2.1 Accéder aux Secrets

1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Connectez-vous avec votre compte GitHub
3. Sélectionnez votre repository `bot-prim`
4. Cliquez sur **"Settings"** (⚙️) dans le menu
5. Allez dans la section **"Secrets"**

### 2.2 Ajouter les Secrets

Ajoutez les secrets suivants dans l'éditeur :

```toml
# Gemini API Key
GEMINI_API_KEY = "..."

# Qdrant Cloud
[qdrant]
USE_QDRANT = "true"
QDRANT_URL = "https://your-cluster.qdrant.io:6333"
QDRANT_API_KEY = "your_qdrant_api_key"
```

**⚠️ Important :** Ne commitez JAMAIS ces secrets dans votre repository !

## 📦 Étape 3 : Déployer l'Application

### 3.1 Nouveau Déploiement

1. Sur [share.streamlit.io](https://share.streamlit.io), cliquez sur **"New app"**
2. Sélectionnez votre repository : `carlcgb/bot-prim`
3. **Main file path** : `app.py`
4. **App URL** : Choisissez un nom unique (ex: `primbot`)
5. Cliquez sur **"Deploy"**

### 3.2 Mise à Jour

Si l'application est déjà déployée :
- Les mises à jour sont automatiques à chaque push sur GitHub
- Ou cliquez sur **"Reboot app"** dans les paramètres pour forcer un redémarrage

## 🗄️ Étape 4 : Initialiser la Base de Connaissances

### Option A : Qdrant Cloud (Recommandé)

Si vous utilisez Qdrant Cloud :

1. Configurez les secrets Qdrant (voir Étape 2.2)
2. La base de connaissances est déjà disponible dans le cloud
3. Aucune initialisation nécessaire !

### Option B : ChromaDB Local

Si vous utilisez ChromaDB local :

1. Une fois l'application déployée, ouvrez-la
2. Si la base de connaissances est vide, un message d'avertissement apparaîtra
3. Cliquez sur **"🚀 Lancer l'ingestion automatique de la documentation"**
4. Attendez 5-10 minutes pendant le scraping et l'ingestion
5. ⚠️ **Note** : La base de connaissances sera réinitialisée à chaque redéploiement

**💡 Astuce** : Pour éviter la réinitialisation, utilisez Qdrant Cloud ou incluez le dossier `chroma_db/` dans votre repository (non recommandé pour les gros volumes).

## ✅ Étape 5 : Vérifier le Déploiement

### 5.1 Vérifications

1. ✅ L'application se charge sans erreur
2. ✅ La base de connaissances est initialisée (ou connectée à Qdrant)
3. ✅ Vous pouvez poser une question et obtenir une réponse
4. ✅ Les boutons de feedback fonctionnent

### 5.2 Tests

Testez avec ces questions :

- "Comment créer un employé ?"
- "Comment configurer l'export CSV ?"
- "Quels sont les champs obligatoires pour une facture ?"

## 🐛 Dépannage

### Erreur : "API Key not found"

**Solution :**
- Vérifiez que les secrets sont correctement configurés dans Streamlit Cloud
- Vérifiez l'orthographe : `GEMINI_API_KEY`
- Redémarrez l'application après avoir ajouté les secrets

### Erreur : "Base de connaissances vide"

**Solution :**
- Si vous utilisez Qdrant : Vérifiez que les secrets Qdrant sont configurés
- Si vous utilisez ChromaDB : Lancez l'ingestion automatique via le bouton dans l'interface

### Erreur : "Module not found"

**Solution :**
- Vérifiez que `requirements.txt` contient toutes les dépendances
- Redéployez l'application pour réinstaller les dépendances

### L'application est lente

**Solutions :**
- Utilisez Qdrant Cloud au lieu de ChromaDB local
- Utilisez un modèle plus rapide (gemini-2.5-flash)
- Vérifiez que la base de connaissances est bien initialisée

## 🔒 Sécurité

### Bonnes Pratiques

1. ✅ **Ne commitez JAMAIS** les secrets dans votre repository
2. ✅ Utilisez **toujours** les secrets Streamlit pour les clés API
3. ✅ **Ne partagez pas** votre URL d'application publiquement si elle contient des données sensibles
4. ✅ **Révisez régulièrement** les accès et permissions

### Secrets Recommandés

```toml
# Minimum requis
OPENAI_API_KEY = "sk-..."

# Optionnel mais recommandé
[qdrant]
USE_QDRANT = "true"
QDRANT_URL = "https://..."
QDRANT_API_KEY = "..."
```

## 📊 Monitoring

### Logs Streamlit

1. Dans Streamlit Cloud, cliquez sur **"Manage app"**
2. Allez dans l'onglet **"Logs"**
3. Consultez les logs pour diagnostiquer les problèmes

### Métriques

- **Temps de réponse** : Surveillez dans les logs
- **Utilisation API** : Surveillez sur [platform.openai.com](https://platform.openai.com/usage)
- **Base de connaissances** : Vérifiez le nombre de documents dans l'interface

## 🔄 Mises à Jour

### Mettre à Jour le Code

1. Faites vos modifications localement
2. Commitez et poussez sur GitHub
3. Streamlit Cloud redéploie automatiquement

### Mettre à Jour les Secrets

1. Allez dans **Settings > Secrets**
2. Modifiez les secrets nécessaires
3. Cliquez sur **"Save"**
4. L'application redémarre automatiquement

## 📚 Ressources

- [Documentation Streamlit Cloud](https://docs.streamlit.io/streamlit-community-cloud)
- [Documentation Qdrant Cloud](https://qdrant.tech/documentation/cloud/)

## 🆘 Support

Si vous rencontrez des problèmes :

1. Consultez les [logs Streamlit](#logs-streamlit)
2. Vérifiez la [documentation complète](../README.md)
3. Ouvrez une [issue sur GitHub](https://github.com/carlcgb/bot-prim/issues)

---

**Dernière mise à jour** : Décembre 2024

