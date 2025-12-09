"""
Script de migration depuis ChromaDB vers Supabase
Migre la base de connaissances existante
"""

import os
from storage_supabase import SupabaseStorage
from scraper import run_scraper
import sys

def migrate_knowledge_base():
    """Migre la base de connaissances depuis ChromaDB vers Supabase."""
    print("🔄 Migration de la base de connaissances vers Supabase...\n")
    
    try:
        # Initialiser Supabase
        print("1️⃣  Initialisation de Supabase...")
        storage = SupabaseStorage()
        
        # Créer les tables si nécessaire
        print("2️⃣  Configuration de la base de données...")
        storage.setup_database()
        
        # Vérifier si la base est déjà peuplée
        count = storage.count()
        if count > 0:
            response = input(f"\n⚠️  La base Supabase contient déjà {count} documents.\n"
                           "Voulez-vous continuer et ajouter de nouveaux documents? (o/n): ")
            if response.lower() not in ['o', 'oui', 'y', 'yes']:
                print("❌ Migration annulée")
                return
        
        # Scraper la documentation
        print("\n3️⃣  Scraping de la documentation PrimLogix...")
        print("   Cela peut prendre 5-10 minutes...\n")
        pages_data = run_scraper()
        
        print(f"\n4️⃣  Ajout de {len(pages_data)} pages à Supabase...")
        storage.add_documents(pages_data)
        
        final_count = storage.count()
        print(f"\n✅ Migration terminée!")
        print(f"📊 {final_count} documents dans Supabase")
        print("\n💡 Vous pouvez maintenant utiliser Supabase au lieu de ChromaDB")
        print("   Configurez USE_SUPABASE=true dans vos variables d'environnement")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    migrate_knowledge_base()

