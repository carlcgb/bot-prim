"""
Script pour créer le fichier .env avec vos identifiants Supabase
"""

import os

# Vos identifiants Supabase
SUPABASE_URL = "https://qwpdehqkxcvsblkwpbop.supabase.co"
SUPABASE_KEY = "sb_publishable_C59Ew0JS7YvEZPoYA1MkWQ_-UEMZuf6"
SUPABASE_DB_URL = "postgresql://postgres:*963.**963.Qwer@db.qwpdehqkxcvsblkwpbop.supabase.co:5432/postgres"

env_content = f"""# Configuration Supabase pour PRIMBOT
# ⚠️ NE COMMITEZ JAMAIS CE FICHIER (déjà dans .gitignore)

# URL de votre projet Supabase
SUPABASE_URL={SUPABASE_URL}

# Clé publique (publishable key)
SUPABASE_KEY={SUPABASE_KEY}

# Connection string PostgreSQL
SUPABASE_DB_URL={SUPABASE_DB_URL}

# Utiliser Supabase au lieu de ChromaDB
USE_SUPABASE=true
FALLBACK_TO_CHROMADB=true
"""

# Vérifier si .env existe déjà
if os.path.exists('.env'):
    response = input("⚠️  Le fichier .env existe déjà. Voulez-vous le remplacer? (o/n): ")
    if response.lower() not in ['o', 'oui', 'y', 'yes']:
        print("❌ Annulé")
        exit(0)

# Créer le fichier .env
try:
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("✅ Fichier .env créé avec succès!")
    print("\n📝 Contenu:")
    print("   - SUPABASE_URL configuré")
    print("   - SUPABASE_KEY configuré")
    print("   - SUPABASE_DB_URL configuré")
    print("\n💡 Prochaines étapes:")
    print("   1. Testez la connexion: python test_supabase_connection.py")
    print("   2. Initialisez la base: python setup_supabase.py")
except Exception as e:
    print(f"❌ Erreur lors de la création du fichier .env: {e}")

