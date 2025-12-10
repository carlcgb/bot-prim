# 🔐 Configuration GitHub Secrets pour Qdrant Cloud

Guide pour configurer les secrets GitHub pour utiliser Qdrant Cloud dans vos workflows CI/CD et déploiements.

## 📋 Secrets à Configurer

Allez dans votre repository GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### Secrets Requis

| Secret Name | Description | Valeur à Configurer |
|------------|-------------|---------------------|
| `QDRANT_URL` | URL de votre cluster Qdrant Cloud | `https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333` |
| `QDRANT_API_KEY` | Clé API de votre cluster Qdrant | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.xc3r32lkaYTKX9ft1KA39KVibKssq8xmebh8WjHrXj4` |
| `USE_QDRANT` | Active Qdrant Cloud (optionnel, défaut: `false`) | `true` |

### Instructions Étape par Étape

1. **Allez sur votre repository GitHub**
2. Cliquez sur **Settings** (en haut du repository)
3. Dans le menu de gauche, cliquez sur **Secrets and variables** → **Actions**
4. Cliquez sur **New repository secret**
5. Pour chaque secret ci-dessus :
   - **Name** : Le nom du secret (ex: `QDRANT_URL`)
   - **Secret** : La valeur (ex: `https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333`)
   - Cliquez sur **Add secret**

## 🔧 Utilisation dans GitHub Actions

### Exemple de Workflow

```yaml
name: Test with Qdrant

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Configure Qdrant
        env:
          USE_QDRANT: true
          QDRANT_URL: ${{ secrets.QDRANT_URL }}
          QDRANT_API_KEY: ${{ secrets.QDRANT_API_KEY }}
        run: |
          python -c "from knowledge_base import collection; print(f'Connected: {collection.count()} docs')"
```

## 🌐 Utilisation avec Streamlit Cloud

Pour déployer sur Streamlit Cloud avec Qdrant :

1. Allez sur [Streamlit Cloud](https://share.streamlit.io)
2. Sélectionnez votre repository
3. Dans **Advanced settings** → **Secrets**, ajoutez :

```toml
[qdrant]
USE_QDRANT = "true"
QDRANT_URL = "https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Puis dans `app.py`, chargez les secrets :

```python
import os
import streamlit as st

# Load Qdrant secrets from Streamlit
if 'qdrant' in st.secrets:
    os.environ['USE_QDRANT'] = st.secrets['qdrant'].get('USE_QDRANT', 'false')
    os.environ['QDRANT_URL'] = st.secrets['qdrant'].get('QDRANT_URL', '')
    os.environ['QDRANT_API_KEY'] = st.secrets['qdrant'].get('QDRANT_API_KEY', '')
```

## 🔒 Sécurité

⚠️ **Important** :
- Ne commitez **JAMAIS** vos vraies clés API dans le code
- Utilisez toujours les secrets GitHub pour les credentials
- Ajoutez `.env` à votre `.gitignore` (déjà fait)
- Utilisez `.env.example` comme template

## ✅ Vérification

Pour vérifier que les secrets sont bien configurés :

```bash
# Dans un workflow GitHub Actions
echo "QDRANT_URL is set: ${{ secrets.QDRANT_URL != '' }}"
echo "QDRANT_API_KEY is set: ${{ secrets.QDRANT_API_KEY != '' }}"
```

## 📚 Ressources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Streamlit Secrets](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Qdrant Cloud Documentation](https://qdrant.tech/documentation/cloud/)

