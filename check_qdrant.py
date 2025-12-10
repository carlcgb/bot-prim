#!/usr/bin/env python3
"""
Script pour vérifier l'état de la base de données Qdrant Cloud
"""
import os
from pathlib import Path

# Load Qdrant configuration
def load_qdrant_config():
    """Load Qdrant configuration from environment variables or .env file."""
    use_qdrant = os.getenv('USE_QDRANT', 'false').lower() == 'true'
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    
    # If not in environment, try to load from .env file
    if not use_qdrant or not qdrant_url or not qdrant_api_key:
        env_file = Path('.env')
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key == 'USE_QDRANT':
                                use_qdrant = value.lower() == 'true'
                            elif key == 'QDRANT_URL':
                                qdrant_url = value
                            elif key == 'QDRANT_API_KEY':
                                qdrant_api_key = value
            except Exception as e:
                print(f"⚠️ Could not load .env file: {e}")
    
    if use_qdrant and qdrant_url and qdrant_api_key:
        os.environ['USE_QDRANT'] = 'true'
        os.environ['QDRANT_URL'] = qdrant_url
        os.environ['QDRANT_API_KEY'] = qdrant_api_key
        return True, qdrant_url, qdrant_api_key
    return False, None, None

print("🔍 Vérification de la base de données Qdrant Cloud\n")

# Load config
qdrant_enabled, qdrant_url, qdrant_api_key = load_qdrant_config()

if not qdrant_enabled:
    print("❌ Qdrant Cloud n'est pas configuré")
    print("\n💡 Pour configurer Qdrant, créez un fichier .env avec:")
    print("   USE_QDRANT=true")
    print("   QDRANT_URL=https://votre-cluster.qdrant.io:6333")
    print("   QDRANT_API_KEY=votre_cle_api")
    exit(1)

print(f"✅ Qdrant Cloud configuré")
print(f"   URL: {qdrant_url}\n")

# Now import knowledge_base (after env vars are set)
from knowledge_base import collection

try:
    # Count documents
    count = collection.count()
    print(f"📊 Nombre total de documents (chunks): {count}")
    
    # Expected count (from previous runs, we had ~2630-3212 documents)
    # Let's check if it's reasonable
    if count == 0:
        print("\n❌ Base de données vide!")
        print("   Exécutez: primbot ingest")
    elif count < 2000:
        print(f"\n⚠️  Base de données semble incomplète ({count} documents)")
        print("   Attendu: ~2600-3200 documents")
        print("   Exécutez: primbot ingest pour réingérer")
    elif count >= 2000:
        print(f"\n✅ Base de données semble complète ({count} documents)")
        print("   Nombre attendu: ~2600-3200 documents")
    
    # Try to get some sample documents
    if count > 0:
        print("\n📄 Exemples de documents dans la base:")
        try:
            # Query for a common term to get samples
            from knowledge_base import query_knowledge_base
            results = query_knowledge_base("utilisateur", n_results=5)
            
            if results:
                if isinstance(results, dict):
                    docs = results.get('documents', [])
                    metadatas = results.get('metadatas', [])
                    if docs and metadatas:
                        unique_urls = set()
                        for i, doc in enumerate(docs[0][:5] if isinstance(docs[0], list) else docs[:5]):
                            if i < len(metadatas[0] if isinstance(metadatas[0], list) else metadatas):
                                meta = metadatas[0][i] if isinstance(metadatas[0], list) else metadatas[i]
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
        from knowledge_base import query_knowledge_base
        results = query_knowledge_base("créer un utilisateur affecter groupe dlg103", n_results=10)
        
        if results:
            found_dlg103 = False
            if isinstance(results, dict):
                metadatas = results.get('metadatas', [])
                if metadatas:
                    for meta_list in (metadatas[0] if isinstance(metadatas[0], list) else [metadatas]):
                        for meta in (meta_list if isinstance(meta_list, list) else [meta_list]):
                            if isinstance(meta, dict):
                                url = meta.get('url', '')
                                if 'dlg103' in url.lower():
                                    found_dlg103 = True
                                    print(f"  ✅ Document dlg103.html trouvé!")
                                    print(f"     URL: {url}")
                                    break
                        if found_dlg103:
                            break
            
            if not found_dlg103:
                print("  ⚠️  Document dlg103.html non trouvé dans les résultats")
                print("     (Il pourrait être présent mais avec un score de pertinence faible)")
        else:
            print("  ❌ Aucun résultat trouvé")
    except Exception as e:
        print(f"⚠️ Erreur lors de la recherche: {e}")
    
    print("\n" + "="*60)
    print("📋 Résumé:")
    print(f"   Backend: Qdrant Cloud")
    print(f"   Documents: {count}")
    if count >= 2000:
        print("   Statut: ✅ Complète")
    elif count > 0:
        print("   Statut: ⚠️  Incomplète (réingérer recommandé)")
    else:
        print("   Statut: ❌ Vide")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ Erreur lors de la vérification: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

