"""
Module de stockage local pour PRIMBOT
Stocke les conversations et feedback localement (JSON/SQLite)
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import sqlite3

# Répertoire de stockage local
STORAGE_DIR = Path.home() / ".primbot" / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Fichier SQLite pour les conversations
DB_FILE = STORAGE_DIR / "conversations.db"


class LocalStorage:
    """Gestionnaire de stockage local pour conversations et feedback."""
    
    def __init__(self):
        """Initialise la base de données locale."""
        self.db_file = DB_FILE
        self._init_database()
    
    def _init_database(self):
        """Crée les tables si elles n'existent pas."""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        # Table conversations
        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                metadata TEXT,  -- JSON string
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table feedback
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        
        # Index pour améliorer les performances
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user_id 
            ON conversations(user_id)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_created_at 
            ON conversations(created_at DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, user_id: str, question: str, answer: str, metadata: Optional[Dict] = None):
        """Sauvegarde une conversation."""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cur.execute("""
            INSERT INTO conversations (user_id, question, answer, metadata)
            VALUES (?, ?, ?, ?)
        """, (user_id, question, answer, metadata_json))
        
        conn.commit()
        conversation_id = cur.lastrowid
        conn.close()
        
        return conversation_id
    
    def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Récupère l'historique des conversations."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, user_id, question, answer, metadata, created_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        rows = cur.fetchall()
        conn.close()
        
        conversations = []
        for row in rows:
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            conversations.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'question': row['question'],
                'answer': row['answer'],
                'metadata': metadata,
                'created_at': row['created_at']
            })
        
        return conversations
    
    def save_feedback(self, conversation_id: int, rating: int, comment: Optional[str] = None):
        """Sauvegarde un feedback."""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO feedback (conversation_id, rating, comment)
            VALUES (?, ?, ?)
        """, (conversation_id, rating, comment))
        
        conn.commit()
        conn.close()
    
    def get_feedback_stats(self) -> Dict:
        """Récupère les statistiques de feedback."""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        # Nombre total de feedbacks
        cur.execute("SELECT COUNT(*) FROM feedback")
        total = cur.fetchone()[0]
        
        # Note moyenne
        cur.execute("SELECT AVG(rating) FROM feedback")
        avg_rating = cur.fetchone()[0] or 0
        
        # Distribution des notes
        cur.execute("""
            SELECT rating, COUNT(*) as count
            FROM feedback
            GROUP BY rating
            ORDER BY rating
        """)
        distribution = {row[0]: row[1] for row in cur.fetchall()}
        
        conn.close()
        
        return {
            'total': total,
            'average_rating': round(avg_rating, 2),
            'distribution': distribution
        }
    
    def get_all_conversations(self, limit: int = 100) -> List[Dict]:
        """Récupère toutes les conversations (pour admin)."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, user_id, question, answer, metadata, created_at
            FROM conversations
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cur.fetchall()
        conn.close()
        
        conversations = []
        for row in rows:
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            conversations.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'question': row['question'],
                'answer': row['answer'],
                'metadata': metadata,
                'created_at': row['created_at']
            })
        
        return conversations
    
    def count(self) -> int:
        """Compte le nombre total de conversations."""
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM conversations")
        count = cur.fetchone()[0]
        
        conn.close()
        return count


# Instance globale
_storage_instance: Optional[LocalStorage] = None

def get_storage() -> LocalStorage:
    """Retourne l'instance de stockage local."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = LocalStorage()
    return _storage_instance

