# 🚀 Configuration Supabase pour PRIMBOT

Guide rapide pour configurer Supabase avec vos identifiants.

## 📋 Informations de votre projet

- **URL**: `https://qwpdehqkxcvsblkwpbop.supabase.co`
- **Publishable Key**: `sb_publishable_C59Ew0JS7YvEZPoYA1MkWQ_-UEMZuf6`
- **Secret Key**: `sb_secret_tn9Z1hMBUgg2ylo4RF-jfQ_OMfmPOBz` (gardez-la secrète!)

## 🔧 Étape 1 : Obtenir la Connection String

1. Allez sur [Supabase Dashboard](https://supabase.com/dashboard)
2. Sélectionnez votre projet
3. Allez dans **Settings** > **Database**
4. Dans la section **Connection string**, copiez l'URI
5. Remplacez `[YOUR-PASSWORD]` par votre mot de passe de base de données

**Format attendu:**
```
postgresql://postgres:VOTRE_MOT_DE_PASSE@db.qwpdehqkxcvsblkwpbop.supabase.co:5432/postgres
```

## 📦 Étape 2 : Installer les dépendances

```bash
pip install supabase psycopg2-binary
```

Note: `pgvector` est déjà installé sur Supabase, pas besoin de l'installer localement.

## ⚙️ Étape 3 : Configurer les variables d'environnement

Créez un fichier `.env` à la racine du projet :

```bash
# Windows PowerShell
Copy-Item env.example .env

# Linux/macOS
cp env.example .env
```

Puis éditez `.env` et ajoutez votre connection string :

```toml
SUPABASE_URL=https://qwpdehqkxcvsblkwpbop.supabase.co
SUPABASE_KEY=sb_publishable_C59Ew0JS7YvEZPoYA1MkWQ_-UEMZuf6
SUPABASE_DB_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@db.qwpdehqkxcvsblkwpbop.supabase.co:5432/postgres
USE_SUPABASE=true
```

## 🗄️ Étape 4 : Initialiser la base de données

Exécutez le script de setup :

```bash
python setup_supabase.py
```

Ce script va :
- ✅ Activer l'extension pgvector
- ✅ Créer la table `knowledge_base` (pour les embeddings)
- ✅ Créer la table `conversations` (pour l'historique)
- ✅ Créer la table `feedback` (pour l'apprentissage)
- ✅ Créer les index nécessaires

## 📥 Étape 5 : Migrer vos données (optionnel)

Si vous avez déjà une base ChromaDB, migrez-la :

```bash
python migrate_to_supabase.py
```

Sinon, utilisez simplement `primbot ingest` qui utilisera Supabase si configuré.

## ✅ Étape 6 : Vérifier la configuration

Testez que tout fonctionne :

```python
from storage_supabase import get_storage

storage = get_storage()
print(f"Documents dans Supabase: {storage.count()}")
```

## 🔐 Sécurité

⚠️ **Important**: 
- Ne commitez JAMAIS votre fichier `.env` (il est dans `.gitignore`)
- Ne partagez JAMAIS votre Secret Key publiquement
- La Publishable Key peut être utilisée côté client (c'est son rôle)

## 🌐 Pour Streamlit Cloud

Ajoutez ces secrets dans Streamlit Cloud :

1. Allez dans les paramètres de votre app
2. Section **Secrets**
3. Ajoutez :

```toml
SUPABASE_URL = "https://qwpdehqkxcvsblkwpbop.supabase.co"
SUPABASE_KEY = "sb_publishable_C59Ew0JS7YvEZPoYA1MkWQ_-UEMZuf6"
SUPABASE_DB_URL = "postgresql://postgres:VOTRE_MOT_DE_PASSE@db.qwpdehqkxcvsblkwpbop.supabase.co:5432/postgres"
USE_SUPABASE = true
```

## 🎯 Utilisation

Une fois configuré, PRIMBOT utilisera automatiquement Supabase si `USE_SUPABASE=true`.

Vous pouvez aussi utiliser Supabase directement dans votre code :

```python
from storage_supabase import get_storage

storage = get_storage()

# Ajouter des documents
storage.add_documents(pages_data)

# Rechercher
results = storage.query("votre question", n_results=10)

# Sauvegarder une conversation
storage.save_conversation("user123", "Question?", "Réponse...")

# Récupérer l'historique
history = storage.get_conversation_history("user123")
```

## 🆘 Dépannage

### Erreur de connexion
- Vérifiez que votre IP est autorisée dans Supabase (Settings > Database)
- Vérifiez que le mot de passe dans la connection string est correct

### Extension pgvector non trouvée
- L'extension est automatiquement activée par le script `setup_supabase.py`
- Si problème, exécutez manuellement dans Supabase SQL Editor :
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

### Tables déjà existantes
- Le script détecte et ignore les tables existantes
- Pas de problème si vous réexécutez le script

## 📚 Ressources

- [Documentation Supabase](https://supabase.com/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Guide complet de stockage](STORAGE_OPTIONS.md)

