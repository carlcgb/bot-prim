# 🚀 Migration vers Qdrant Cloud

Guide complet pour migrer votre base de connaissances de ChromaDB local vers Qdrant Cloud (gratuit).

## 📋 Prérequis

1. **Compte Qdrant Cloud** (gratuit) : [https://cloud.qdrant.io/](https://cloud.qdrant.io/)
2. **Python 3.8+**
3. **Base de connaissances existante** (optionnel, pour migration)

## 🔧 Étape 1 : Créer un cluster Qdrant Cloud

1. Allez sur [https://cloud.qdrant.io/](https://cloud.qdrant.io/)
2. Créez un compte gratuit (pas de carte de crédit requise)
3. Créez un nouveau cluster :
   - Choisissez une région proche de vous
   - Le plan gratuit offre **1 cluster, 1GB de stockage**
4. Une fois créé, récupérez :
   - **Cluster URL** : `https://xxx.us-east-1-0.aws.cloud.qdrant.io`
   - **API Key** : Cliquez sur votre cluster → "API Keys" → Créez une nouvelle clé

## 📦 Étape 2 : Installer les dépendances

```bash
pip install qdrant-client
```

Ou réinstallez toutes les dépendances :

```bash
pip install -r requirements.txt
```

## 🔑 Étape 3 : Configurer les variables d'environnement

### Option A : Variables d'environnement système

**Windows (PowerShell):**
```powershell
$env:USE_QDRANT="true"
$env:QDRANT_URL="https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333"
$env:QDRANT_API_KEY="votre-api-key"
```

**Linux/Mac:**
```bash
export USE_QDRANT=true
export QDRANT_URL="https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333"
export QDRANT_API_KEY="votre-api-key"
```

### Option B : Fichier `.env` (recommandé pour développement local)

Créez un fichier `.env` à la racine du projet :

```env
USE_QDRANT=true
QDRANT_URL=https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=votre-api-key
```

⚠️ **Important** : Ajoutez `.env` à votre `.gitignore` (déjà fait). Ne commitez jamais vos vraies clés API.

### Option C : GitHub Secrets (pour CI/CD et déploiements)

Pour utiliser Qdrant dans GitHub Actions ou autres services cloud :

1. Allez dans votre repository GitHub → **Settings** → **Secrets and variables** → **Actions**
2. Créez ces secrets :
   - `QDRANT_URL` : `https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333`
   - `QDRANT_API_KEY` : Votre clé API
   - `USE_QDRANT` : `true` (optionnel)

📚 **Guide complet** : Voir [docs/GITHUB_SECRETS.md](docs/GITHUB_SECRETS.md)

### Option D : Streamlit Secrets (pour Streamlit Cloud)

Pour l'interface web sur Streamlit Cloud, ajoutez dans les secrets de votre app :

```toml
[qdrant]
USE_QDRANT = "true"
QDRANT_URL = "https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = "votre-api-key"
```

Les secrets sont automatiquement chargés par `app.py`.

## 📤 Étape 4 : Migrer les données existantes (optionnel)

Si vous avez déjà une base de connaissances ChromaDB locale :

```bash
# 1. Configurez les variables d'environnement (voir étape 3)
# 2. Exécutez le script de migration
python migrate_to_qdrant.py
```

Le script va :
- ✅ Vérifier vos credentials Qdrant
- ✅ Lire toutes les données de ChromaDB
- ✅ Les migrer vers Qdrant Cloud
- ✅ Afficher un résumé de la migration

## 🆕 Étape 5 : Créer une nouvelle base de connaissances

Si vous partez de zéro ou voulez réingérer :

```bash
# Configurez les variables d'environnement d'abord
# Puis exécutez l'ingestion
python ingest.py
```

Les données iront automatiquement dans Qdrant Cloud si `USE_QDRANT=true`.

## ✅ Étape 6 : Vérifier que ça fonctionne

### Test rapide

```python
from knowledge_base import collection, query_knowledge_base

# Vérifier le nombre de documents
print(f"Documents dans la base: {collection.count()}")

# Tester une requête
results = query_knowledge_base("comment ajouter un employé", n_results=5)
print(f"Résultats trouvés: {len(results['documents'][0])}")
```

### Test avec l'interface web

```bash
streamlit run app.py
```

La base de connaissances devrait se connecter automatiquement à Qdrant Cloud.

## 🔄 Retour à ChromaDB local

Pour revenir à ChromaDB local, il suffit de :

1. **Désactiver Qdrant** :
   ```bash
   unset USE_QDRANT  # Linux/Mac
   # ou
   $env:USE_QDRANT="false"  # Windows
   ```

2. Ou supprimer les variables d'environnement Qdrant

Le système basculera automatiquement sur ChromaDB local.

## 📊 Comparaison des backends

| Fonctionnalité | ChromaDB Local | Qdrant Cloud |
|---------------|----------------|-------------|
| **Stockage** | Disque local | Cloud (1GB gratuit) |
| **Accessibilité** | Machine locale uniquement | Accessible partout |
| **Performance** | Rapide (local) | Rapide (cloud) |
| **Gratuit** | ✅ Oui | ✅ Oui (1GB) |
| **Installation** | Simple | Nécessite compte |
| **Backup** | Manuel | Automatique |

## 🆘 Dépannage

### Erreur : "Qdrant credentials not found"

**Solution** : Vérifiez que les variables d'environnement sont bien définies :
```bash
echo $QDRANT_URL
echo $QDRANT_API_KEY
```

### Erreur : "Failed to connect to Qdrant"

**Solutions** :
1. Vérifiez que l'URL du cluster est correcte
2. Vérifiez que l'API key est valide
3. Vérifiez votre connexion internet
4. Vérifiez que le cluster est actif sur [cloud.qdrant.io](https://cloud.qdrant.io/)

### Migration échoue

**Solutions** :
1. Vérifiez que ChromaDB contient des données : `collection.count()`
2. Vérifiez que vous avez assez d'espace dans Qdrant (1GB gratuit)
3. Réessayez la migration (elle est idempotente)

## 📚 Ressources

- [Documentation Qdrant Cloud](https://qdrant.tech/documentation/cloud/)
- [API Qdrant Python](https://qdrant.github.io/qdrant-client/)
- [Support Qdrant](https://qdrant.tech/documentation/support/)

## 🎉 C'est tout !

Votre base de connaissances est maintenant dans le cloud et accessible partout ! 🚀

