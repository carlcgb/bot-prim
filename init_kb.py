"""
Script d'initialisation automatique de la base de connaissances
Peut être exécuté au démarrage de l'app pour s'assurer que la KB est chargée
"""

import os
from knowledge_base import collection

def ensure_knowledge_base():
    """Vérifie et initialise la base de connaissances si nécessaire."""
    kb_count = collection.count()
    
    if kb_count == 0:
        print("⚠️  Base de connaissances vide. Initialisation...")
        try:
            from scraper import run_scraper
            from knowledge_base import add_documents
            
            print("📥 Scraping de la documentation PrimLogix...")
            data = run_scraper()
            
            print(f"💾 Ajout de {len(data)} pages à la base de connaissances...")
            add_documents(data)
            
            final_count = collection.count()
            print(f"✅ Base de connaissances initialisée avec {final_count} documents!")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    else:
        print(f"✅ Base de connaissances déjà chargée: {kb_count} documents")
        return True

if __name__ == "__main__":
    ensure_knowledge_base()

