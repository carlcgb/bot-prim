"""
Module de stockage Supabase pour PRIMBOT
Remplace ou complète ChromaDB pour un stockage cloud gratuit
"""

import os
from typing import List, Dict, Optional
import json
from sentence_transformers import SentenceTransformer

# Modèle d'embedding (même que ChromaDB pour compatibilité)
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
EMBEDDING_DIM = 384  # Dimension pour all-MiniLM-L6-v2

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase non installé. Installez avec: pip install supabase")

try:
    import psycopg2
    from psycopg2.extras import execute_values
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("⚠️ psycopg2 non installé. Installez avec: pip install psycopg2-binary")


class SupabaseStorage:
    """Gestionnaire de stockage Supabase pour PRIMBOT."""
    
    def __init__(self):
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase n'est pas installé. pip install supabase")
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 n'est pas installé. pip install psycopg2-binary")
        
        # Configuration depuis variables d'environnement
        # Valeurs par défaut pour faciliter le setup
        self.supabase_url = os.getenv("SUPABASE_URL", "https://qwpdehqkxcvsblkwpbop.supabase.co")
        self.supabase_key = os.getenv("SUPABASE_KEY", "sb_publishable_C59Ew0JS7YvEZPoYA1MkWQ_-UEMZuf6")
        self.db_url = os.getenv("SUPABASE_DB_URL")
        
        if not self.db_url:
            raise ValueError(
                "SUPABASE_DB_URL manquant!\n\n"
                "Pour obtenir la connection string:\n"
                "1. Allez sur https://supabase.com/dashboard\n"
                "2. Sélectionnez votre projet\n"
                "3. Settings > Database\n"
                "4. Copiez la 'Connection string' (URI mode)\n"
                "5. Remplacez [YOUR-PASSWORD] par votre mot de passe\n\n"
                "Exemple:\n"
                "postgresql://postgres:VOTRE_MOT_DE_PASSE@db.qwpdehqkxcvsblkwpbop.supabase.co:5432/postgres"
            )
        
        # Clients
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.embedding_model = EMBEDDING_MODEL
        
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Découpe le texte en chunks avec overlap."""
        if not text:
            return []
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += (chunk_size - overlap)
        return chunks
    
    def setup_database(self):
        """Initialise les tables dans Supabase."""
        if not self.db_url:
            raise ValueError("SUPABASE_DB_URL non configuré")
        
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        
        try:
            # Activer pgvector
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Table knowledge_base
            cur.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    url TEXT,
                    title TEXT,
                    chunk_index INTEGER,
                    images JSONB,
                    embedding vector(%s)
                );
            """, (EMBEDDING_DIM,))
            
            # Index vectoriel
            cur.execute("""
                CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx 
                ON knowledge_base USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)
            
            # Table conversations
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id BIGSERIAL PRIMARY KEY,
                    user_id TEXT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS conversations_user_id_idx 
                ON conversations(user_id);
                
                CREATE INDEX IF NOT EXISTS conversations_created_at_idx 
                ON conversations(created_at DESC);
            """)
            
            # Table feedback
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id BIGSERIAL PRIMARY KEY,
                    conversation_id BIGINT REFERENCES conversations(id),
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            conn.commit()
            print("✅ Tables Supabase initialisées avec succès")
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Erreur lors de l'initialisation: {e}")
        finally:
            cur.close()
            conn.close()
    
    def add_documents(self, pages_data: List[Dict]):
        """Ajoute des documents à la base de connaissances."""
        if not self.db_url:
            raise ValueError("SUPABASE_DB_URL non configuré")
        
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        
        total_added = 0
        
        try:
            for page in pages_data:
                url = page['url']
                title = page['title']
                content = page['content']
                images = page.get('images', [])
                
                chunks = self.chunk_text(content)
                
                for i, chunk in enumerate(chunks):
                    if not chunk.strip():
                        continue
                    
                    # Générer l'embedding
                    embedding = self.embedding_model.encode(chunk).tolist()
                    
                    # ID unique
                    chunk_id = f"{url}_{i}"
                    
                    # Insérer ou mettre à jour
                    cur.execute("""
                        INSERT INTO knowledge_base 
                        (id, content, url, title, chunk_index, images, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            images = EXCLUDED.images
                    """, (
                        chunk_id,
                        chunk,
                        url,
                        title,
                        i,
                        json.dumps(images),
                        str(embedding)
                    ))
                    
                    total_added += 1
            
            conn.commit()
            print(f"✅ {total_added} documents ajoutés à Supabase")
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Erreur lors de l'ajout: {e}")
        finally:
            cur.close()
            conn.close()
    
    def query(self, query: str, n_results: int = 10) -> Dict:
        """Recherche dans la base de connaissances."""
        if not self.db_url:
            raise ValueError("SUPABASE_DB_URL non configuré")
        
        # Générer l'embedding de la requête
        query_embedding = self.embedding_model.encode(query).tolist()
        
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        
        try:
            # Recherche vectorielle avec cosine similarity
            cur.execute("""
                SELECT 
                    id, content, url, title, chunk_index, images,
                    1 - (embedding <=> %s::vector) as distance
                FROM knowledge_base
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (str(query_embedding), str(query_embedding), n_results))
            
            results = cur.fetchall()
            
            # Formater comme ChromaDB pour compatibilité
            return {
                'documents': [[r[1]] for r in results],
                'metadatas': [[{
                    'url': r[2] or '',
                    'title': r[3] or '',
                    'chunk_index': r[4] or 0,
                    'images': r[5] if r[5] else ''
                }] for r in results],
                'distances': [[r[6]] for r in results],
                'ids': [[r[0]] for r in results]
            }
            
        except Exception as e:
            raise Exception(f"Erreur lors de la recherche: {e}")
        finally:
            cur.close()
            conn.close()
    
    def count(self) -> int:
        """Compte le nombre de documents."""
        if not self.db_url:
            return 0
        
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT COUNT(*) FROM knowledge_base")
            count = cur.fetchone()[0]
            return count
        except Exception:
            return 0
        finally:
            cur.close()
            conn.close()
    
    def save_conversation(self, user_id: str, question: str, answer: str, metadata: Optional[Dict] = None):
        """Sauvegarde une conversation."""
        try:
            self.supabase.table('conversations').insert({
                'user_id': user_id,
                'question': question,
                'answer': answer,
                'metadata': metadata or {}
            }).execute()
        except Exception as e:
            print(f"⚠️ Erreur lors de la sauvegarde de conversation: {e}")
    
    def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Récupère l'historique des conversations."""
        try:
            response = self.supabase.table('conversations')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"⚠️ Erreur lors de la récupération de l'historique: {e}")
            return []
    
    def save_feedback(self, conversation_id: int, rating: int, comment: Optional[str] = None):
        """Sauvegarde un feedback."""
        try:
            self.supabase.table('feedback').insert({
                'conversation_id': conversation_id,
                'rating': rating,
                'comment': comment
            }).execute()
        except Exception as e:
            print(f"⚠️ Erreur lors de la sauvegarde du feedback: {e}")


# Instance globale (optionnel)
_storage_instance: Optional[SupabaseStorage] = None

def get_storage() -> SupabaseStorage:
    """Retourne l'instance de stockage Supabase."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = SupabaseStorage()
    return _storage_instance

