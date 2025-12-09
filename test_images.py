"""
Script de test pour vérifier que les images sont bien extraites et incluses dans les réponses
"""

from knowledge_base import query_knowledge_base, collection
import json

print("🧪 Test d'extraction d'images de la base de connaissances\n")
print("=" * 60)

# Vérifier que la base de connaissances contient des données
kb_count = collection.count()
print(f"📚 Documents dans la base: {kb_count}")

if kb_count == 0:
    print("\n❌ La base de connaissances est vide!")
    print("💡 Exécutez: python ingest.py")
    exit(1)

# Test avec une requête qui devrait retourner des images
test_queries = [
    "interface utilisateur",
    "menu",
    "bouton",
    "écran",
    "fenêtre"
]

print("\n🔍 Test de recherche avec images...\n")

for query in test_queries:
    print(f"📝 Requête: '{query}'")
    results = query_knowledge_base(query, n_results=5)
    
    if not results or not results.get('documents'):
        print(f"   ⚠️  Aucun résultat pour '{query}'\n")
        continue
    
    docs = results['documents'][0]
    metadatas = results['metadatas'][0]
    
    total_images = 0
    images_found = []
    
    for i, metadata in enumerate(metadatas):
        images_json = metadata.get('images', '')
        if images_json:
            try:
                images = json.loads(images_json)
                total_images += len(images)
                for img in images:
                    if img['url'] not in [i['url'] for i in images_found]:
                        images_found.append(img)
            except:
                pass
    
    print(f"   ✅ {len(docs)} document(s) trouvé(s)")
    print(f"   📸 {total_images} image(s) trouvée(s) dans les métadonnées")
    print(f"   🖼️  {len(images_found)} image(s) unique(s)")
    
    if images_found:
        print(f"\n   📋 Exemples d'images trouvées:")
        for idx, img in enumerate(images_found[:3], 1):
            print(f"      {idx}. {img.get('alt', 'Sans description')[:50]}")
            print(f"         URL: {img['url'][:70]}...")
    print()

# Test de la fonction _search_kb de l'agent
print("\n" + "=" * 60)
print("🤖 Test de la fonction _search_kb de l'agent\n")

try:
    from agent import PrimAgent
    
    # Créer un agent de test (sans API key nécessaire pour tester _search_kb)
    print("📝 Test avec la requête: 'comment utiliser l'interface'")
    
    # On peut tester _search_kb directement sans initialiser complètement l'agent
    # Créons un agent minimal juste pour tester
    agent = PrimAgent(api_key="test", model="gemini-2.5-flash", provider="Google Gemini")
    
    result = agent._search_kb("comment utiliser l'interface")
    
    # Vérifier si des images sont présentes dans le résultat
    import re
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    image_matches = re.findall(image_pattern, result)
    
    print(f"\n✅ Résultat de _search_kb:")
    print(f"   Longueur: {len(result)} caractères")
    print(f"   📸 Images trouvées dans le résultat: {len(image_matches)}")
    
    if image_matches:
        print(f"\n   🖼️  Images extraites:")
        for idx, (alt, url) in enumerate(image_matches[:5], 1):
            print(f"      {idx}. {alt[:50] if alt else 'Sans description'}")
            print(f"         {url[:70]}...")
    else:
        print("\n   ⚠️  Aucune image trouvée dans le format markdown")
        # Vérifier si le texte contient des références aux images
        if "📸" in result or "image" in result.lower() or "captures" in result.lower():
            print("   💡 Le texte mentionne des images mais elles ne sont pas au format markdown")
    
    # Afficher un extrait du résultat
    print(f"\n   📄 Extrait du résultat (premiers 500 caractères):")
    print(f"   {result[:500]}...")
    
except Exception as e:
    print(f"❌ Erreur lors du test: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ Test terminé!")
print("\n💡 Pour tester dans l'interface:")
print("   1. Lancez: streamlit run app.py")
print("   2. Posez une question sur l'interface PrimLogix")
print("   3. Vérifiez que les images s'affichent dans la réponse")

