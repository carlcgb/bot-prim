#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier l'état de la base de données
"""
import os
from knowledge_base import collection

# Check which backend is being used
USE_QDRANT = os.getenv('USE_QDRANT', 'false').lower() == 'true'

print("🔍 Diagnostic de la base de données\n")
print(f"Backend: {'Qdrant Cloud' if USE_QDRANT else 'ChromaDB Local'}\n")

# Count documents
count = collection.count()
print(f"📊 Nombre total de documents (chunks): {count}")

# Try to get some sample documents to see what's in there
if count > 0:
    print("\n📄 Exemples de documents dans la base:")
    try:
        # Get a few sample results
        results = collection.get(limit=5)
        
        if hasattr(results, 'metadatas'):
            metadatas = results.metadatas
        elif isinstance(results, dict) and 'metadatas' in results:
            metadatas = results['metadatas']
        else:
            metadatas = []
        
        if metadatas:
            unique_urls = set()
            for meta in metadatas:
                if isinstance(meta, dict):
                    url = meta.get('url', 'N/A')
                    title = meta.get('title', 'N/A')
                    if url not in unique_urls:
                        unique_urls.add(url)
                        print(f"  - {title}")
                        print(f"    URL: {url}")
                        if len(unique_urls) >= 5:
                            break
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération d'exemples: {e}")

# Check for specific document
print("\n🔍 Recherche du document 'dlg103.html' (Créer un utilisateur)...")
try:
    # Search for documents about user creation
    from knowledge_base import query_knowledge_base
    results = query_knowledge_base("créer un utilisateur affecter groupe", n_results=10)
    
    if results and len(results) > 0:
        print(f"✅ Trouvé {len(results)} résultats pour 'créer un utilisateur':")
        for i, result in enumerate(results[:5], 1):
            if isinstance(result, dict):
                metadata = result.get('metadata', {})
                url = metadata.get('url', 'N/A')
                title = metadata.get('title', 'N/A')
                distance = result.get('distance', 'N/A')
                print(f"  {i}. {title}")
                print(f"     URL: {url}")
                print(f"     Distance: {distance}")
                if 'dlg103' in url.lower():
                    print("     ✅ Ce document contient 'dlg103'!")
    else:
        print("❌ Aucun résultat trouvé pour 'créer un utilisateur'")
except Exception as e:
    print(f"⚠️ Erreur lors de la recherche: {e}")

print("\n💡 Pour réingérer la base de données:")
print("   primbot ingest")
