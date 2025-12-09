# Guide de Déploiement Streamlit Cloud - Base de Connaissances

## Problème : Base de connaissances vide

Par défaut, le dossier `chroma_db/` est exclu du repository (dans `.gitignore`), donc la base de connaissances n'est pas déployée sur Streamlit Cloud.

## Solutions

### Solution 1 : Inclure la base de connaissances dans le repository (Recommandé)

1. **Retirer `chroma_db/` de `.gitignore`** :
   ```bash
   # Commentez ou supprimez ces lignes dans .gitignore:
   # chroma_db/
   # *.db
   # *.sqlite3
   ```

2. **Ajouter la base de connaissances au repository** :
   ```bash
   git add chroma_db/
   git commit -m "Add knowledge base database for deployment"
   git push origin main
   ```

3. **Note** : Le dossier `chroma_db/` fait environ quelques MB. Assurez-vous que GitHub accepte la taille.

### Solution 2 : Initialiser après déploiement (Alternative)

L'app Streamlit inclut maintenant un bouton pour initialiser la base de connaissances :

1. Déployez l'app sur Streamlit Cloud
2. Ouvrez l'app déployée
3. Cliquez sur "Initialiser la base de connaissances" dans le panneau d'avertissement
4. Attendez que le scraping et l'ingestion se terminent (peut prendre 5-10 minutes)

⚠️ **Note** : Cette méthode doit être répétée à chaque redéploiement, car Streamlit Cloud ne persiste pas les données entre les redéploiements.

### Solution 3 : Utiliser un stockage externe (Avancé)

Pour une solution plus robuste, vous pouvez :
- Utiliser ChromaDB avec un backend distant (PostgreSQL, etc.)
- Stocker la base sur un service cloud (S3, etc.)
- Utiliser un volume persistant si disponible

## Vérification

Pour vérifier que la base de connaissances est chargée :
- L'avertissement "Base de connaissances vide" ne devrait plus apparaître
- Le sidebar devrait afficher "📚 Base de connaissances: X documents"
- Les recherches devraient retourner des résultats

