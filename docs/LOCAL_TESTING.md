# 🧪 Test Local du Bot

Guide complet pour tester PRIMBOT localement avec Qdrant Cloud ou ChromaDB local.

## 📋 Prérequis

1. **Python 3.8+** installé
2. **Clé API Gemini** (gratuite) : [Google AI Studio](https://aistudio.google.com/)
3. **Qdrant Cloud** (optionnel) : [cloud.qdrant.io](https://cloud.qdrant.io/)

## 🚀 Installation Rapide

```bash
# Cloner le repository
git clone https://github.com/carlcgb/bot-prim.git
cd bot-prim

# Installer les dépendances
pip install -r requirements.txt
```

## ⚙️ Configuration

### Option 1 : Avec Qdrant Cloud (Recommandé)

1. **Créez un fichier `.env`** à la racine du projet :

```env
# Gemini API
GEMINI_API_KEY=votre_cle_gemini

# Qdrant Cloud
USE_QDRANT=true
QDRANT_URL=https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=votre_cle_qdrant
```

2. **Ou configurez les variables d'environnement** :

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="votre_cle_gemini"
$env:USE_QDRANT="true"
$env:QDRANT_URL="https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333"
$env:QDRANT_API_KEY="votre_cle_qdrant"
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY="votre_cle_gemini"
export USE_QDRANT="true"
export QDRANT_URL="https://d521bd67-bc88-4cf5-9140-23a0744ab85d.us-east4-0.gcp.cloud.qdrant.io:6333"
export QDRANT_API_KEY="votre_cle_qdrant"
```

### Option 2 : Avec ChromaDB Local

Si vous n'utilisez pas Qdrant, le bot utilisera automatiquement ChromaDB local :

```env
# Gemini API uniquement
GEMINI_API_KEY=votre_cle_gemini
```

## 📦 Initialiser la Base de Connaissances

### Avec Qdrant Cloud (déjà migré)

Si vous avez déjà migré vers Qdrant Cloud, la base de connaissances est prête ! Vérifiez simplement :

```bash
python -c "from knowledge_base import collection; print(f'Documents: {collection.count()}')"
```

Vous devriez voir : `Documents: 2630`

### Avec ChromaDB Local

Si vous utilisez ChromaDB local, initialisez la base :

```bash
# Via CLI
primbot ingest

# Ou directement
python ingest.py
```

Cela prend 5-10 minutes et ne doit être fait qu'une seule fois.

## 🧪 Tester le Bot

### Test 1 : Interface Web (Streamlit)

```bash
streamlit run app.py
```

Ouvrez votre navigateur à `http://localhost:8501`

**Fonctionnalités à tester :**
- ✅ Poser une question dans le chat
- ✅ Vérifier que la réponse contient des liens vers la documentation
- ✅ Vérifier que les images affichées sont pertinentes (pas d'icônes)
- ✅ Tester le système de feedback (👍👎)
- ✅ Vérifier les statistiques dans la sidebar

### Test 2 : CLI (Ligne de Commande)

```bash
# Question unique
primbot ask "comment ajouter un employé"

# Mode interactif
primbot ask --interactive

# Avec un modèle spécifique
primbot ask "question" --model gemini-2.0-flash-exp
```

### Test 3 : Test Python Direct

```python
from agent import PrimAgent
from knowledge_base import collection

# Vérifier la base de connaissances
print(f"Documents dans la base: {collection.count()}")

# Créer l'agent
agent = PrimAgent(api_key="votre_cle_gemini")

# Poser une question
response = agent.chat("comment créer un nouveau client?")
print(response)
```

## ✅ Checklist de Test

### Fonctionnalités de Base
- [ ] Le bot se connecte à la base de connaissances
- [ ] Les questions retournent des réponses pertinentes
- [ ] Les réponses contiennent des liens vers la documentation
- [ ] Les réponses sont structurées et détaillées (step-by-step)

### Images
- [ ] Maximum 2-3 images par réponse
- [ ] Les images sont des captures d'écran (pas d'icônes)
- [ ] Les images sont pertinentes à la question
- [ ] Les images ont des descriptions claires

### Feedback
- [ ] Les boutons 👍👎 apparaissent après chaque réponse
- [ ] Le feedback est sauvegardé
- [ ] Les statistiques s'affichent dans la sidebar

### Base de Connaissances
- [ ] Qdrant Cloud : Vérifier la connexion
- [ ] ChromaDB Local : Vérifier que `chroma_db/` contient des données
- [ ] Les recherches retournent des résultats pertinents

## 🔍 Tests de Requêtes Exemples

Testez avec ces questions pour vérifier différents aspects :

```bash
# Test de recherche basique
primbot ask "comment ajouter un employé"

# Test de recherche spécifique
primbot ask "procédure pour créer une facture avec tous les champs obligatoires"

# Test de recherche d'erreur
primbot ask "erreur lors de l'export CSV le champ date facturation est vide"

# Test de recherche de fonctionnalité
primbot ask "comment configurer les paramètres de paie pour un nouveau dossier candidat"
```

## 🐛 Dépannage

### Erreur : "Base de connaissances vide"

**Solution :**
```bash
# Vérifiez la connexion Qdrant
python -c "from knowledge_base import collection; print(collection.count())"

# Si 0, réingérez les données
python ingest.py
```

### Erreur : "Qdrant credentials not found"

**Solution :**
- Vérifiez que les variables d'environnement sont définies
- Vérifiez le fichier `.env` existe et contient les bonnes valeurs
- Pour Windows PowerShell, utilisez `$env:VARIABLE="value"`

### Erreur : "Failed to connect to Qdrant"

**Solutions :**
1. Vérifiez votre connexion internet
2. Vérifiez que l'URL et la clé API sont correctes
3. Vérifiez que le cluster Qdrant est actif sur [cloud.qdrant.io](https://cloud.qdrant.io/)

### Les images ne s'affichent pas

**Solutions :**
1. Vérifiez que les images sont bien dans les métadonnées
2. Vérifiez que les URLs d'images sont absolues
3. Vérifiez la console du navigateur pour les erreurs

### Les réponses ne sont pas assez détaillées

**Solutions :**
1. Vérifiez que le système d'instructions est bien chargé
2. Testez avec des questions plus spécifiques
3. Vérifiez les logs pour voir si la base de connaissances est bien consultée

## 📊 Vérification de la Performance

```python
import time
from agent import PrimAgent
from knowledge_base import query_knowledge_base

# Test de vitesse de recherche
start = time.time()
results = query_knowledge_base("employé", n_results=10)
print(f"Recherche: {time.time() - start:.2f}s")

# Test de vitesse de réponse
agent = PrimAgent(api_key="votre_cle")
start = time.time()
response = agent.chat("comment ajouter un employé")
print(f"Réponse complète: {time.time() - start:.2f}s")
```

## 🎯 Prochaines Étapes

Une fois les tests locaux réussis :

1. **Déployer sur Streamlit Cloud** : Voir [README.md](../README.md#déploiement)
2. **Configurer GitHub Secrets** : Voir [docs/GITHUB_SECRETS.md](GITHUB_SECRETS.md)
3. **Contribuer** : Ouvrir une issue ou une pull request

## 📚 Ressources

- [README Principal](../README.md)
- [Guide de Migration Qdrant](QDRANT_MIGRATION.md)
- [Configuration GitHub Secrets](GITHUB_SECRETS.md)
- [Guide CLI](CLI_USAGE.md)

