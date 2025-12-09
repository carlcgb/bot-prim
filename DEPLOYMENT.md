# Guide de Déploiement Streamlit Cloud

## Problème : "This repository does not exist"

Si Streamlit Cloud affiche l'erreur "This repository does not exist", cela signifie généralement que :

### 1. Le repository est privé

Streamlit Cloud doit avoir accès à votre repository. Si votre repository est privé :

**Solution :**
1. Allez sur https://github.com/settings/applications
2. Cliquez sur "Authorized GitHub Apps"
3. Trouvez "Streamlit" dans la liste
4. Cliquez sur "Configure" ou "Grant access"
5. Assurez-vous que `carlcgb/bot-prim` est dans la liste des repositories autorisés
6. Si Streamlit n'est pas dans la liste, vous devrez l'autoriser lors du premier déploiement

### 2. Rendre le repository public (Option alternative)

Si vous préférez rendre le repository public :

1. Allez sur https://github.com/carlcgb/bot-prim/settings
2. Faites défiler jusqu'à "Danger Zone"
3. Cliquez sur "Change visibility"
4. Sélectionnez "Make public"

⚠️ **Note** : Assurez-vous qu'aucune clé API ou secret n'est dans le code avant de rendre le repository public.

### 3. Vérifier les permissions GitHub

Assurez-vous que :
- Votre compte GitHub est bien connecté à Streamlit Cloud
- Vous avez les droits d'administration sur le repository `carlcgb/bot-prim`
- Le repository existe bien et est accessible depuis votre compte

### 4. Format correct pour Streamlit Cloud

Dans le formulaire de déploiement Streamlit Cloud :

- **Repository** : `carlcgb/bot-prim` (sans https://github.com/)
- **Branch** : `main`
- **Main file path** : `app.py` (pas `streamlit_app.py`)

### 5. Autoriser Streamlit Cloud lors du premier déploiement

Lorsque vous essayez de déployer pour la première fois, GitHub vous demandera d'autoriser Streamlit Cloud. Assurez-vous de :
- Autoriser l'accès au repository `carlcgb/bot-prim`
- Donner les permissions nécessaires

## Vérification

Pour vérifier que le repository est accessible :

1. Visitez : https://github.com/carlcgb/bot-prim
2. Si vous voyez "404" ou "Page not found", le repository est soit :
   - Privé (normal si vous êtes connecté, mais Streamlit Cloud doit être autorisé)
   - N'existe pas (vérifiez le nom)
   - Vous n'avez pas les permissions

## Solution recommandée

1. **Autoriser Streamlit Cloud** dans les paramètres GitHub (voir étape 1)
2. Utiliser le format : `carlcgb/bot-prim` (sans le préfixe https://)
3. Vérifier que la branche est `main`
4. Utiliser `app.py` comme fichier principal

