"""
Script pour résoudre les problèmes de connexion PostgreSQL à Supabase
Teste différentes méthodes et configurations
"""

import os
import urllib.parse
import socket
import time

# Charger .env
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

if not SUPABASE_DB_URL:
    print("❌ SUPABASE_DB_URL non configuré dans .env")
    exit(1)

print("🔧 Diagnostic de connexion PostgreSQL à Supabase\n")
print("=" * 60)

# 1. Test de résolution DNS
print("\n1️⃣  Test de résolution DNS...")
hostname = "db.qwpdehqkxcvsblkwpbop.supabase.co"
try:
    ip = socket.gethostbyname(hostname)
    print(f"   ✅ Hostname résolu: {ip}")
except socket.gaierror as e:
    print(f"   ❌ Erreur DNS: {e}")
    print("   💡 Vérifiez votre connexion Internet")
    exit(1)

# 2. Test de connexion TCP (port 5432)
print("\n2️⃣  Test de connexion TCP (port 5432)...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((hostname, 5432))
    sock.close()
    if result == 0:
        print("   ✅ Port 5432 accessible")
    else:
        print(f"   ❌ Port 5432 bloqué (code: {result})")
        print("   💡 Le firewall bloque probablement le port 5432")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# 3. Test de connexion TCP (port 6543 - Connection Pooling)
print("\n3️⃣  Test de connexion TCP (port 6543 - Connection Pooling)...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((hostname, 6543))
    sock.close()
    if result == 0:
        print("   ✅ Port 6543 accessible (Connection Pooling disponible!)")
        USE_POOLING = True
    else:
        print(f"   ❌ Port 6543 aussi bloqué (code: {result})")
        USE_POOLING = False
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    USE_POOLING = False

# 4. Test avec différentes connection strings
print("\n4️⃣  Test de connexion PostgreSQL...")

# Parser l'URL actuelle
from urllib.parse import urlparse
parsed = urlparse(SUPABASE_DB_URL)
password = urllib.parse.unquote(parsed.password)

# Méthode 1: Connection directe (port 5432)
print("\n   a) Connection directe (port 5432)...")
try:
    import psycopg2
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=5432,
        database=parsed.path[1:] if parsed.path.startswith('/') else parsed.path,
        user=parsed.username,
        password=password,
        connect_timeout=10
    )
    print("      ✅ Connexion réussie!")
    conn.close()
    print("\n🎉 La connexion PostgreSQL fonctionne!")
    exit(0)
except psycopg2.OperationalError as e:
    if "could not translate host name" in str(e):
        print("      ❌ Erreur DNS (hostname non résolu)")
    elif "timeout" in str(e).lower():
        print("      ❌ Timeout (port probablement bloqué)")
    elif "connection refused" in str(e).lower():
        print("      ❌ Connexion refusée (port bloqué ou service non disponible)")
    else:
        print(f"      ❌ Erreur: {e}")
except Exception as e:
    print(f"      ❌ Erreur: {e}")

# Méthode 2: Connection Pooling (port 6543)
if USE_POOLING:
    print("\n   b) Connection Pooling (port 6543)...")
    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=6543,
            database=parsed.path[1:] if parsed.path.startswith('/') else parsed.path,
            user=parsed.username,
            password=password,
            connect_timeout=10
        )
        print("      ✅ Connexion réussie avec Connection Pooling!")
        
        # Mettre à jour .env avec le port 6543
        new_url = SUPABASE_DB_URL.replace(':5432/', ':6543/')
        print(f"\n💡 Mise à jour de .env avec Connection Pooling...")
        
        # Lire .env
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer l'URL
        content = content.replace(SUPABASE_DB_URL, new_url)
        
        # Écrire .env
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("      ✅ .env mis à jour avec Connection Pooling (port 6543)")
        print("\n🎉 La connexion PostgreSQL fonctionne avec Connection Pooling!")
        conn.close()
        exit(0)
    except Exception as e:
        print(f"      ❌ Erreur: {e}")

# 5. Solutions alternatives
print("\n" + "=" * 60)
print("💡 Solutions alternatives:\n")

print("Option 1: Utiliser Connection Pooling (si disponible)")
print("   - Le port 6543 est parfois moins bloqué que 5432")
print("   - Modifiez SUPABASE_DB_URL pour utiliser le port 6543")
print("   - Format: postgresql://...@db.xxxxx.supabase.co:6543/postgres")

print("\nOption 2: Autoriser votre IP dans Supabase")
print("   1. Allez sur https://supabase.com/dashboard")
print("   2. Sélectionnez votre projet")
print("   3. Settings > Database")
print("   4. Vérifiez les restrictions IP")
print("   5. Ajoutez votre IP publique si nécessaire")

print("\nOption 3: Utiliser un VPN ou un autre réseau")
print("   - Testez depuis votre réseau personnel")
print("   - Utilisez un hotspot mobile")
print("   - Configurez un VPN")

print("\nOption 4: Utiliser l'API Supabase (déjà fonctionnelle)")
print("   - L'API fonctionne via HTTPS (port 443)")
print("   - Parfait pour conversations et feedback")
print("   - Pour la recherche vectorielle, il faudra résoudre PostgreSQL")

print("\nOption 5: Configuration hybride")
print("   - API Supabase pour conversations/feedback")
print("   - ChromaDB local pour recherche vectorielle")
print("   - Migrer vers Supabase PostgreSQL plus tard")

# 6. Obtenir l'IP publique
print("\n" + "=" * 60)
print("📋 Votre IP publique (pour autorisation dans Supabase):")
try:
    import requests
    ip = requests.get('https://api.ipify.org', timeout=5).text
    print(f"   {ip}")
    print(f"\n💡 Ajoutez cette IP dans Supabase > Settings > Database > Allowed IPs")
except:
    print("   (Impossible de récupérer l'IP publique)")

print("\n" + "=" * 60)

