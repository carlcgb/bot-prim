"""
Script de test pour vérifier le filtrage des images
"""
import json
from agent import PrimAgent
from knowledge_base import collection
import os

# Test du filtrage des images
def test_image_filtering():
    print("🧪 Test du filtrage des images...")
    print(f"📚 Base de connaissances: {collection.count()} documents\n")
    
    # Vérifier que la base est initialisée
    if collection.count() == 0:
        print("❌ Base de connaissances vide. Exécutez d'abord: python ingest.py")
        return
    
    # Obtenir une clé API Gemini depuis les variables d'environnement
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️  GEMINI_API_KEY non définie. Le test nécessite une clé API.")
        print("   Définissez-la avec: export GEMINI_API_KEY='votre_cle'")
        return
    
    # Initialiser l'agent
    agent = PrimAgent(api_key=api_key, model="gemini-2.5-flash", provider="Google Gemini")
    
    # Test avec une question qui devrait retourner des images
    test_questions = [
        "comment créer un utilisateur",
        "interface de connexion",
        "fenêtre principale"
    ]
    
    print("📝 Test avec plusieurs questions...\n")
    
    for question in test_questions:
        print(f"❓ Question: {question}")
        print("-" * 60)
        
        messages = [{"role": "user", "content": question}]
        
        try:
            response = agent.run(messages)
            
            # Compter les images dans la réponse
            import re
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            images = re.findall(image_pattern, response)
            
            print(f"✅ Réponse reçue ({len(images)} image(s) trouvée(s))")
            
            # Afficher les URLs des images trouvées
            if images:
                print("\n📸 Images trouvées:")
                for idx, (alt, url) in enumerate(images, 1):
                    print(f"  {idx}. {alt[:50]}...")
                    print(f"     URL: {url[:80]}...")
                    
                    # Vérifier que ce n'est pas une icône/flèche
                    url_lower = url.lower()
                    excluded_patterns = ['icon', 'arrow', 'fleche', 'chevron', 'emoji', 'logo', 'button']
                    if any(pattern in url_lower for pattern in excluded_patterns):
                        # Mais vérifier si c'est quand même une capture d'écran
                        if any(x in url_lower for x in ['screenshot', 'capture', 'interface', 'images/']):
                            print(f"     ✅ Acceptée (contient des mots-clés de screenshot)")
                        else:
                            print(f"     ⚠️  Potentiellement exclue (contient des patterns d'icônes)")
                    else:
                        print(f"     ✅ Acceptée")
            else:
                print("ℹ️  Aucune image dans la réponse")
            
            # Vérifier la présence de liens source
            if "**Source:**" in response or "Source:" in response:
                print("\n🔗 Liens source détectés dans la réponse ✅")
            else:
                print("\n⚠️  Aucun lien source détecté")
            
            print("\n" + "=" * 60 + "\n")
            
        except Exception as e:
            print(f"❌ Erreur: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("✅ Test terminé!")

if __name__ == "__main__":
    test_image_filtering()

