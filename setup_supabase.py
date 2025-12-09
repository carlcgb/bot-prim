"""
Script de configuration Supabase pour PRIMBOT
Crée les tables nécessaires et configure la base de données
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuration Supabase
# Charge depuis .env ou variables d'environnement
try:
    from dotenv import load_dotenv
    load_dotenv()  # Charge .env si disponible
except ImportError:
    pass  # dotenv optionnel

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qwpdehqkxcvsblkwpbop.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_C59Ew0JS7YvEZPoYA1MkWQ_-UEMZuf6")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

if not SUPABASE_DB_URL:
    print("⚠️  SUPABASE_DB_URL non configuré!")
    print("\n💡 Essayez Connection Pooling (port 6543) qui est souvent moins bloqué:")
    print("   python setup_supabase_pooling.py")
    print("\nOu configurez manuellement:")
    print("1. Allez sur https://supabase.com/dashboard")
    print("2. Sélectionnez votre projet")
    print("3. Settings > Database")
    print("4. Copiez la 'Connection string' (URI mode)")
    print("5. Remplacez [YOUR-PASSWORD] par votre mot de passe")
    print("\nExemple (port 5432):")
    print("postgresql://postgres:VOTRE_MOT_DE_PASSE@db.qwpdehqkxcvsblkwpbop.supabase.co:5432/postgres")
    print("\nExemple (Connection Pooling, port 6543 - recommandé si firewall):")
    print("postgresql://postgres:VOTRE_MOT_DE_PASSE@db.qwpdehqkxcvsblkwpbop.supabase.co:6543/postgres?pgbouncer=true")
    exit(1)

def setup_database():
    """Crée les tables et extensions nécessaires dans Supabase."""
    print("🔧 Configuration de Supabase pour PRIMBOT...\n")
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(SUPABASE_DB_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("✅ Connexion à Supabase réussie\n")
        
        # 1. Activer l'extension pgvector
        print("📦 Activation de l'extension pgvector...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✅ Extension pgvector activée\n")
        
        # 2. Créer la table knowledge_base
        print("📚 Création de la table knowledge_base...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                url TEXT,
                title TEXT,
                chunk_index INTEGER,
                images JSONB,
                embedding vector(384)
            );
        """)
        print("✅ Table knowledge_base créée")
        
        # Index vectoriel
        print("🔍 Création de l'index vectoriel...")
        try:
            cur.execute("""
                CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx 
                ON knowledge_base USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)
            print("✅ Index vectoriel créé")
        except Exception as e:
            print(f"⚠️  Index déjà existant ou erreur: {e}")
        print()
        
        # 3. Créer la table conversations
        print("💬 Création de la table conversations...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id BIGSERIAL PRIMARY KEY,
                user_id TEXT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("✅ Table conversations créée")
        
        # Index pour conversations
        cur.execute("""
            CREATE INDEX IF NOT EXISTS conversations_user_id_idx 
            ON conversations(user_id);
            
            CREATE INDEX IF NOT EXISTS conversations_created_at_idx 
            ON conversations(created_at DESC);
        """)
        print("✅ Index pour conversations créés\n")
        
        # 4. Créer la table feedback
        print("⭐ Création de la table feedback...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id BIGSERIAL PRIMARY KEY,
                conversation_id BIGINT REFERENCES conversations(id),
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("✅ Table feedback créée\n")
        
        # Vérifier les tables créées
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('knowledge_base', 'conversations', 'feedback');
        """)
        tables = cur.fetchall()
        
        print("📊 Tables créées:")
        for table in tables:
            print(f"   ✅ {table[0]}")
        
        cur.close()
        conn.close()
        
        print("\n🎉 Configuration Supabase terminée avec succès!")
        print("\n📝 Prochaines étapes:")
        print("1. Configurez les variables d'environnement (voir .env.example)")
        print("2. Utilisez storage_supabase.py pour migrer vos données")
        print("3. Testez avec: python -c 'from storage_supabase import get_storage; s = get_storage(); print(s.count())'")
        
    except psycopg2.Error as e:
        print(f"❌ Erreur PostgreSQL: {e}")
        print("\n💡 Vérifiez:")
        print("- Que SUPABASE_DB_URL est correct")
        print("- Que le mot de passe est correct")
        print("- Que votre IP est autorisée dans Supabase (Settings > Database > Connection pooling)")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_database()

