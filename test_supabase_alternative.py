"""
Test de connexion alternative avec différentes méthodes
"""

import os
import urllib.parse

# Charger .env
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

print("🔍 Test de différentes méthodes de connexion...\n")

# Méthode 1: Connection string directe
print("1️⃣  Test avec connection string directe...")
print(f"   URL: {SUPABASE_DB_URL[:50]}...")

try:
    import psycopg2
    conn = psycopg2.connect(SUPABASE_DB_URL, connect_timeout=10)
    print("   ✅ Connexion réussie!")
    conn.close()
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Méthode 2: Utiliser le connection pooling (port 6543)
print("\n2️⃣  Test avec connection pooling (port 6543)...")
pool_url = SUPABASE_DB_URL.replace(':5432/', ':6543/')
print(f"   URL: {pool_url[:50]}...")

try:
    conn = psycopg2.connect(pool_url, connect_timeout=10)
    print("   ✅ Connexion réussie avec pooling!")
    conn.close()
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Méthode 3: Parser l'URL et utiliser les paramètres séparés
print("\n3️⃣  Test avec paramètres séparés...")
try:
    from urllib.parse import urlparse
    parsed = urlparse(SUPABASE_DB_URL)
    
    # Décoder le mot de passe
    password = urllib.parse.unquote(parsed.password)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path[1:] if parsed.path.startswith('/') else parsed.path,
        user=parsed.username,
        password=password,
        connect_timeout=10
    )
    print("   ✅ Connexion réussie avec paramètres séparés!")
    conn.close()
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print("\n💡 Si toutes les méthodes échouent:")
print("   1. Vérifiez votre connexion Internet")
print("   2. Vérifiez que votre IP est autorisée dans Supabase")
print("   3. Essayez depuis un autre réseau")
print("   4. Vérifiez le hostname dans Supabase Dashboard")

