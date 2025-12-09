# 📚 Déploiement de la Base de Connaissances

## Option 1 : Inclure la base dans le repository (Recommandé)

La base de connaissances fait environ **34 MB**, ce qui est acceptable pour GitHub.

### Étapes :

1. **Retirer `chroma_db/` de `.gitignore`** :
   ```bash
   # Éditez .gitignore et commentez ou supprimez ces lignes :
   # chroma_db/
   # *.db
   # *.sqlite3
   ```

2. **Ajouter la base de connaissances** :
   ```bash
   git add chroma_db/
   git commit -m "Add knowledge base database for deployment"
   git push origin main
   ```

3. **Avantages** :
   - ✅ Base disponible immédiatement après déploiement
   - ✅ Pas besoin d'attendre l'ingestion
   - ✅ Fonctionne même si le scraping échoue

### Note sur la taille

- GitHub accepte les fichiers jusqu'à 100 MB
- La base fait ~34 MB, donc c'est acceptable
- Si elle grandit trop, considérez l'Option 2

## Option 2 : Initialisation automatique au démarrage

L'app inclut maintenant un bouton d'initialisation automatique qui :
- Scrape la documentation PrimLogix
- Ingère les données dans ChromaDB
- Prend 5-10 minutes la première fois

### Avantages :
- ✅ Repository plus léger
- ✅ Toujours à jour avec la dernière documentation
- ✅ Pas besoin de gérer la base manuellement

### Inconvénients :
- ⚠️ Doit être réexécuté à chaque redéploiement (Streamlit Cloud ne persiste pas les données)
- ⚠️ Prend du temps au premier démarrage

## Option 3 : Initialisation via script au démarrage (Avancé)

Vous pouvez créer un script qui s'exécute automatiquement :

```python
# Dans app.py, au début :
import subprocess
import os

if not os.path.exists("chroma_db") or collection.count() == 0:
    subprocess.run(["python", "init_kb.py"])
```

## Recommandation

Pour Streamlit Cloud, je recommande **l'Option 1** (inclure la base dans le repo) car :
- Plus rapide au démarrage
- Plus fiable (pas de dépendance au scraping)
- Fonctionne même si le site PrimLogix est temporairement inaccessible

