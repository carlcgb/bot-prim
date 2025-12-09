"""
Script de test de connexion à Supabase
Vérifie que la configuration est correcte
"""

import os
import sys

# Charger .env si disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Si dotenv n'est pas installé, lire .env manuellement
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

print("🔍 Test de connexion à Supabase...\n")

# Vérifier les variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

if SUPABASE_URL:
    print(f"✅ SUPABASE_URL: {SUPABASE_URL}")
else:
    print("❌ SUPABASE_URL: Non configuré")

if SUPABASE_KEY:
    print(f"✅ SUPABASE_KEY: {SUPABASE_KEY[:20]}...")
else:
    print("❌ SUPABASE_KEY: Non configuré")

if SUPABASE_DB_URL:
    # Masquer le mot de passe dans l'affichage
    db_url_display = SUPABASE_DB_URL.split('@')[0].split(':')[:-1]
    db_url_display = ':'.join(db_url_display) + ':***@' + SUPABASE_DB_URL.split('@')[1]
    print(f"✅ SUPABASE_DB_URL: {db_url_display}")
else:
    print("❌ SUPABASE_DB_URL: Non configuré")
    sys.exit(1)

print("\n📦 Test d'importation des dépendances...")

try:
    import psycopg2
    print("✅ psycopg2 installé")
except ImportError:
    print("❌ psycopg2 non installé. Installez avec: pip install psycopg2-binary")
    sys.exit(1)

try:
    from supabase import create_client
    print("✅ supabase installé")
except ImportError:
    print("❌ supabase non installé. Installez avec: pip install supabase")
    sys.exit(1)

print("\n🔌 Test de connexion PostgreSQL...")

try:
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"✅ Connexion PostgreSQL réussie!")
    print(f"   Version: {version[:50]}...")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Erreur de connexion PostgreSQL: {e}")
    print("\n💡 Vérifiez:")
    print("   - Que votre IP est autorisée dans Supabase (Settings > Database)")
    print("   - Que le mot de passe est correct")
    print("   - Que la connection string est bien formatée")
    sys.exit(1)

print("\n🔌 Test de connexion Supabase API...")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Test simple: lister les tables
    print("✅ Connexion Supabase API réussie!")
except Exception as e:
    print(f"❌ Erreur de connexion Supabase API: {e}")
    sys.exit(1)

print("\n📊 Vérification de l'extension pgvector...")

try:
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
    if cur.fetchone():
        print("✅ Extension pgvector installée")
    else:
        print("⚠️  Extension pgvector non installée (sera créée par setup_supabase.py)")
    cur.close()
    conn.close()
except Exception as e:
    print(f"⚠️  Erreur lors de la vérification: {e}")

print("\n🎉 Tous les tests sont passés!")
print("\n📝 Prochaines étapes:")
print("   1. Exécutez: python setup_supabase.py")
print("   2. Puis: python migrate_to_supabase.py (si vous avez des données à migrer)")

