# 💾 Options de Stockage Gratuites pour PRIMBOT

Ce guide présente les meilleures solutions **100% gratuites** pour héberger :
- 📚 **Base de connaissances** (vectorielle)
- 💬 **Historique des conversations** (questions/réponses)
- 🧠 **Données d'apprentissage** (feedback, améliorations)

## 🏆 Recommandation : Architecture Hybride

### Option 1 : Supabase (Recommandé) ⭐

**Pourquoi Supabase ?**
- ✅ **PostgreSQL gratuit** (500 MB) + **pgvector** (extensions vectorielles)
- ✅ **Storage gratuit** (1 GB) pour fichiers/images
- ✅ **API REST automatique**
- ✅ **Authentification incluse** (si besoin)
- ✅ **Tout dans un seul service**

**Limites gratuites :**
- 500 MB base de données
- 1 GB stockage fichiers
- 2 GB bande passante/mois
- 50,000 requêtes API/mois

**Architecture :**
```
Supabase PostgreSQL
├── Table: knowledge_base (pgvector pour embeddings)
├── Table: conversations (historique Q/A)
├── Table: feedback (apprentissage)
└── Storage: images/screenshots
```

**Avantages :**
- Une seule plateforme pour tout
- pgvector = recherche vectorielle native PostgreSQL
- Facile à migrer depuis ChromaDB
- API REST automatique
- Dashboard web intégré

**Inconvénients :**
- Limite de 500 MB (mais extensible)
- Nécessite migration depuis ChromaDB

---

### Option 2 : Qdrant Cloud + Supabase

**Qdrant Cloud** (Base vectorielle dédiée)
- ✅ **1 GB gratuit** pour embeddings
- ✅ **Performance optimale** pour recherche vectorielle
- ✅ **API simple**
- ✅ **Déjà utilisé par de grandes entreprises**

**Supabase** (Pour conversations/feedback)
- ✅ PostgreSQL pour données relationnelles
- ✅ Storage pour fichiers

**Architecture :**
```
Qdrant Cloud → Base de connaissances (vectorielle)
Supabase → Conversations + Feedback + Images
```

**Avantages :**
- Meilleure performance pour recherche vectorielle
- Séparation des préoccupations
- Scalable

**Inconvénients :**
- Deux services à gérer
- Plus complexe à configurer

---

### Option 3 : MongoDB Atlas + LanceDB

**MongoDB Atlas** (Gratuit)
- ✅ **512 MB gratuit**
- ✅ **Flexible** (NoSQL)
- ✅ **Parfait pour conversations** (documents JSON)

**LanceDB** (Vectorielle)
- ✅ **Serverless gratuit**
- ✅ **Simple à utiliser**
- ✅ **Compatible avec ChromaDB**

**Avantages :**
- MongoDB excellent pour conversations
- LanceDB gratuit et performant
- Facile à migrer

**Inconvénients :**
- Deux services
- LanceDB moins mature que Qdrant

---

## 📊 Comparaison Détaillée

| Solution | Base Vectorielle | Base Conversations | Stockage Fichiers | Limite Gratuite | Difficulté |
|----------|-----------------|-------------------|------------------|----------------|------------|
| **Supabase** | ✅ pgvector | ✅ PostgreSQL | ✅ 1 GB | 500 MB DB | ⭐⭐ Facile |
| **Qdrant + Supabase** | ✅ Qdrant (1 GB) | ✅ Supabase | ✅ Supabase | 1 GB + 500 MB | ⭐⭐⭐ Moyen |
| **MongoDB + LanceDB** | ✅ LanceDB | ✅ MongoDB | ⚠️ Limité | 512 MB + Serverless | ⭐⭐⭐ Moyen |
| **Weaviate Cloud** | ✅ Weaviate | ⚠️ Intégré | ⚠️ Limité | 1 GB | ⭐⭐⭐ Difficile |
| **Pinecone** | ✅ Pinecone | ❌ Non | ❌ Non | 1 projet gratuit | ⭐⭐ Facile |

---

## 🚀 Guide d'Implémentation : Supabase (Recommandé)

### Étape 1 : Créer un compte Supabase

1. Allez sur [supabase.com](https://supabase.com)
2. Créez un compte gratuit
3. Créez un nouveau projet
4. Notez votre URL et API key

### Étape 2 : Installer les dépendances

```bash
pip install supabase pgvector psycopg2-binary
```

### Étape 3 : Configuration

Créez `storage_config.py` :

```python
import os
from supabase import create_client, Client
import psycopg2
from psycopg2.extras import execute_values
import json

# Configuration Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")  # Connection string PostgreSQL

# Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

### Étape 4 : Migration depuis ChromaDB

Créez `migrate_to_supabase.py` :

```python
from knowledge_base import collection, query_knowledge_base
from storage_config import supabase, SUPABASE_DB_URL
import psycopg2
import json

def migrate_knowledge_base():
    """Migre la base ChromaDB vers Supabase avec pgvector."""
    
    # 1. Créer la table avec pgvector
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cur = conn.cursor()
    
    # Activer l'extension pgvector
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # Créer la table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            url TEXT,
            title TEXT,
            chunk_index INTEGER,
            images JSONB,
            embedding vector(384)  -- Dimension pour all-MiniLM-L6-v2
        );
        
        CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx 
        ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
    """)
    
    conn.commit()
    
    # 2. Migrer les données depuis ChromaDB
    # (Récupérer tous les documents et les embeddings)
    # Note: ChromaDB ne permet pas d'exporter facilement les embeddings
    # Il faudra les recalculer avec sentence-transformers
    
    print("✅ Migration terminée")
    cur.close()
    conn.close()
```

### Étape 5 : Nouveau module de stockage

Créez `storage_supabase.py` :

```python
from storage_config import supabase
from sentence_transformers import SentenceTransformer
import json

# Modèle d'embedding (même que ChromaDB)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def add_documents_to_supabase(pages_data):
    """Ajoute des documents à Supabase avec pgvector."""
    from storage_config import SUPABASE_DB_URL
    import psycopg2
    
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cur = conn.cursor()
    
    for page in pages_data:
        url = page['url']
        title = page['title']
        content = page['content']
        images = page.get('images', [])
        
        # Chunking (même logique que ChromaDB)
        chunks = chunk_text(content)
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            
            # Générer l'embedding
            embedding = embedding_model.encode(chunk).tolist()
            
            # Insérer dans Supabase
            chunk_id = f"{url}_{i}"
            cur.execute("""
                INSERT INTO knowledge_base 
                (id, content, url, title, chunk_index, images, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding
            """, (
                chunk_id,
                chunk,
                url,
                title,
                i,
                json.dumps(images),
                str(embedding)
            ))
    
    conn.commit()
    cur.close()
    conn.close()

def query_supabase(query, n_results=10):
    """Recherche dans Supabase avec pgvector."""
    from storage_config import SUPABASE_DB_URL
    import psycopg2
    
    # Générer l'embedding de la requête
    query_embedding = embedding_model.encode(query).tolist()
    
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cur = conn.cursor()
    
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
    cur.close()
    conn.close()
    
    # Formater comme ChromaDB
    return {
        'documents': [[r[1]] for r in results],
        'metadatas': [[{
            'url': r[2],
            'title': r[3],
            'chunk_index': r[4],
            'images': r[5] if r[5] else ''
        }] for r in results],
        'distances': [[r[6]] for r in results],
        'ids': [[r[0]] for r in results]
    }

def save_conversation(user_id, question, answer, metadata=None):
    """Sauvegarde une conversation dans Supabase."""
    supabase.table('conversations').insert({
        'user_id': user_id,
        'question': question,
        'answer': answer,
        'metadata': metadata or {},
        'created_at': 'now()'
    }).execute()

def get_conversation_history(user_id, limit=50):
    """Récupère l'historique des conversations."""
    response = supabase.table('conversations')\
        .select('*')\
        .eq('user_id', user_id)\
        .order('created_at', desc=True)\
        .limit(limit)\
        .execute()
    
    return response.data

def save_feedback(conversation_id, rating, comment=None):
    """Sauvegarde un feedback pour l'apprentissage."""
    supabase.table('feedback').insert({
        'conversation_id': conversation_id,
        'rating': rating,  # 1-5 étoiles
        'comment': comment,
        'created_at': 'now()'
    }).execute()
```

### Étape 6 : Tables Supabase

Exécutez ce SQL dans le SQL Editor de Supabase :

```sql
-- Table pour la base de connaissances (avec pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_base (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    url TEXT,
    title TEXT,
    chunk_index INTEGER,
    images JSONB,
    embedding vector(384)
);

CREATE INDEX knowledge_base_embedding_idx 
ON knowledge_base USING ivfflat (embedding vector_cosine_ops);

-- Table pour les conversations
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX conversations_user_id_idx ON conversations(user_id);
CREATE INDEX conversations_created_at_idx ON conversations(created_at DESC);

-- Table pour le feedback/apprentissage
CREATE TABLE IF NOT EXISTS feedback (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT REFERENCES conversations(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔄 Migration Progressive

Vous pouvez migrer progressivement :

1. **Phase 1** : Garder ChromaDB, ajouter Supabase pour conversations
2. **Phase 2** : Migrer la base de connaissances vers Supabase
3. **Phase 3** : Retirer ChromaDB

---

## 📝 Variables d'Environnement

Ajoutez dans `.streamlit/secrets.toml` ou variables d'environnement :

```toml
# Supabase
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "your-anon-key"
SUPABASE_DB_URL = "postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres"

# Optionnel: Garder ChromaDB en fallback
USE_SUPABASE = true
FALLBACK_TO_CHROMADB = true
```

---

## 🎯 Recommandation Finale

**Pour PRIMBOT, je recommande Supabase** car :

1. ✅ **Tout-en-un** : Base vectorielle + conversations + storage
2. ✅ **Gratuit et généreux** : 500 MB + 1 GB storage
3. ✅ **Facile à migrer** : Compatible avec votre code actuel
4. ✅ **Scalable** : Facilement extensible si besoin
5. ✅ **Dashboard intégré** : Visualisation des données
6. ✅ **API REST automatique** : Pas besoin de backend custom

**Limites :**
- 500 MB suffit pour ~10,000 documents avec embeddings
- Si vous dépassez, upgrade à $25/mois pour 8 GB

---

## 📚 Ressources

- [Supabase Documentation](https://supabase.com/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Qdrant Cloud](https://cloud.qdrant.io/)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)

---

## 🆘 Support

Pour toute question sur la migration, ouvrez une issue sur GitHub.

