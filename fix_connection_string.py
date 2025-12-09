"""
Script pour encoder correctement le mot de passe dans la connection string
"""

import urllib.parse

# Votre mot de passe avec caractères spéciaux
password = "*963.**963.Qwer"

# Encoder le mot de passe pour URL
encoded_password = urllib.parse.quote(password, safe='')

print(f"Mot de passe original: {password}")
print(f"Mot de passe encodé: {encoded_password}")

# Connection string avec mot de passe encodé
connection_string = f"postgresql://postgres:{encoded_password}@db.qwpdehqkxcvsblkwpbop.supabase.co:5432/postgres"

print(f"\nConnection string encodée:")
print(connection_string)

# Mettre à jour le fichier .env
env_content = f"""# Configuration Supabase pour PRIMBOT
# ⚠️ NE COMMITEZ JAMAIS CE FICHIER (déjà dans .gitignore)

# URL de votre projet Supabase
SUPABASE_URL=https://qwpdehqkxcvsblkwpbop.supabase.co

# Clé publique (publishable key)
SUPABASE_KEY=sb_publishable_C59Ew0JS7YvEZPoYA1MkWQ_-UEMZuf6

# Connection string PostgreSQL (mot de passe encodé)
SUPABASE_DB_URL={connection_string}

# Utiliser Supabase au lieu de ChromaDB
USE_SUPABASE=true
FALLBACK_TO_CHROMADB=true
"""

with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print("\n✅ Fichier .env mis à jour avec le mot de passe encodé")
print("\n💡 Testez maintenant: python test_supabase_connection.py")

