"""
Configuration Supabase avec Connection Pooling (port 6543)
Le Connection Pooling est souvent moins bloqué par les firewalls
"""

import os
import urllib.parse

# Configuration
SUPABASE_URL = "https://qwpdehqkxcvsblkwpbop.supabase.co"
SUPABASE_KEY = "sb_publishable_C59Ew0JS7YvEZPoYA1MkWQ_-UEMZuf6"
password = "*963.**963.Qwer"
encoded_password = urllib.parse.quote(password, safe='')

# Connection string avec Connection Pooling (port 6543)
# Le Connection Pooling utilise le port 6543 qui est souvent moins bloqué
# Note: Pour PgBouncer, on utilise le port 6543 sans paramètre supplémentaire
POOLING_DB_URL = f"postgresql://postgres:{encoded_password}@db.qwpdehqkxcvsblkwpbop.supabase.co:6543/postgres"

print("🔧 Configuration Supabase avec Connection Pooling\n")

# Mettre à jour .env
env_content = f"""# Configuration Supabase pour PRIMBOT
# ⚠️ NE COMMITEZ JAMAIS CE FICHIER (déjà dans .gitignore)

# URL de votre projet Supabase
SUPABASE_URL={SUPABASE_URL}

# Clé publique (publishable key)
SUPABASE_KEY={SUPABASE_KEY}

# Connection string PostgreSQL avec Connection Pooling (port 6543)
# Le Connection Pooling est souvent moins bloqué par les firewalls
SUPABASE_DB_URL={POOLING_DB_URL}

# Utiliser Supabase au lieu de ChromaDB
USE_SUPABASE=true
FALLBACK_TO_CHROMADB=true
"""

# Sauvegarder
with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print("✅ Fichier .env mis à jour avec Connection Pooling (port 6543)")
print(f"\n📝 Connection string: {POOLING_DB_URL[:60]}...")
print("\n💡 Le Connection Pooling utilise:")
print("   - Port 6543 (souvent moins bloqué que 5432)")
print("   - PgBouncer pour la gestion des connexions")
print("   - Meilleure compatibilité avec les firewalls")
print("\n🧪 Testez maintenant: python test_supabase_connection.py")

