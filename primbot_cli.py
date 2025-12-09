#!/usr/bin/env python3
"""
PRIMBOT CLI - Command Line Interface for PrimLogix Debug Agent
Usage: primbot [query] [options]
"""

import argparse
import sys
import os
from agent import PrimAgent
from knowledge_base import collection

def main():
    parser = argparse.ArgumentParser(
        description='PRIMBOT CLI - PrimLogix Debug Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  primbot "comment changer mon mot de passe"
  primbot "comment programmer les API" --model gemini-2.5-flash
  primbot "erreur de connexion" --provider openai --key YOUR_KEY
        """
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        help='Question or query about PrimLogix'
    )
    
    parser.add_argument(
        '--provider',
        choices=['gemini', 'openai', 'local'],
        default='gemini',
        help='LLM provider to use (default: gemini)'
    )
    
    parser.add_argument(
        '--key',
        '--api-key',
        dest='api_key',
        default=None,
        help='API key for the selected provider (or set GEMINI_API_KEY/OPENAI_API_KEY env var)'
    )
    
    parser.add_argument(
        '--model',
        default=None,
        help='Model name (default: gemini-2.5-flash for Gemini, gpt-3.5-turbo for OpenAI)'
    )
    
    parser.add_argument(
        '--base-url',
        default=None,
        help='Base URL for local/OpenAI-compatible APIs'
    )
    
    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Run in interactive mode (chat session)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='PRIMBOT CLI 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Determine API key
    api_key = args.api_key
    if not api_key:
        if args.provider == 'gemini':
            api_key = os.getenv('GEMINI_API_KEY', '')
        elif args.provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY', '')
        else:
            api_key = 'ollama'  # Dummy for local
    
    # Prompt for API key if not provided and required
    if not api_key and args.provider != 'local':
        print(f"\n🔑 Clé API requise pour {args.provider}", file=sys.stderr)
        print(f"Vous pouvez la définir via:", file=sys.stderr)
        print(f"  - Variable d'environnement: {args.provider.upper()}_API_KEY", file=sys.stderr)
        print(f"  - Option --key lors de l'appel", file=sys.stderr)
        print(f"  - Ou la saisir maintenant (recommandé pour la première utilisation)\n", file=sys.stderr)
        
        api_key = input(f"Entrez votre clé API {args.provider.upper()}: ").strip()
        
        if not api_key:
            print(f"❌ Erreur: Clé API requise pour {args.provider}.", file=sys.stderr)
            sys.exit(1)
        
        # Optionally save to environment for this session
        if args.provider == 'gemini':
            os.environ['GEMINI_API_KEY'] = api_key
        elif args.provider == 'openai':
            os.environ['OPENAI_API_KEY'] = api_key
        
        print("✅ Clé API configurée\n", file=sys.stderr)
    
    # Determine model
    if not args.model:
        if args.provider == 'gemini':
            args.model = 'gemini-2.5-flash'
        elif args.provider == 'openai':
            args.model = 'gpt-3.5-turbo'
        else:
            args.model = 'llama3.1'
    
    # Map provider names
    provider_map = {
        'gemini': 'Google Gemini',
        'openai': 'OpenAI',
        'local': 'Local (Ollama/LocalAI)'
    }
    provider = provider_map[args.provider]
    
    # Check knowledge base and initialize if empty
    kb_count = collection.count()
    if kb_count == 0:
        print("⚠️  Base de connaissances vide détectée.", file=sys.stderr)
        response = input("Voulez-vous initialiser la base de connaissances maintenant? (o/n): ").strip().lower()
        if response in ['o', 'oui', 'y', 'yes']:
            print("\n📥 Scraping de la documentation PrimLogix...")
            try:
                from scraper import run_scraper
                from knowledge_base import add_documents
                
                data = run_scraper()
                print(f"💾 Ajout de {len(data)} pages à la base de connaissances...")
                add_documents(data)
                print(f"✅ Base de connaissances initialisée avec {collection.count()} documents!\n")
            except Exception as e:
                print(f"❌ Erreur lors de l'ingestion: {e}", file=sys.stderr)
                print("Vous pouvez continuer, mais la recherche dans la base de connaissances ne fonctionnera pas.", file=sys.stderr)
        else:
            print("⚠️  La base de connaissances est vide. La recherche ne fonctionnera pas.\n", file=sys.stderr)
    else:
        print(f"📚 Base de connaissances: {kb_count} documents chargés\n", file=sys.stderr)
    
    # Initialize agent
    try:
        agent = PrimAgent(
            api_key=api_key,
            base_url=args.base_url,
            model=args.model,
            provider=provider
        )
    except Exception as e:
        print(f"Error initializing agent: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Interactive mode
    if args.interactive or not args.query:
        print("🤖 PRIMBOT CLI - PrimLogix Debug Agent")
        if kb_count > 0:
            print(f"📚 Base de connaissances: {kb_count} documents")
        print("Type 'exit' or 'quit' to end the session\n")
        
        messages = []
        while True:
            try:
                query = input("You: ").strip()
                if not query:
                    continue
                if query.lower() in ['exit', 'quit', 'q']:
                    print("\nGoodbye!")
                    break
                
                messages.append({"role": "user", "content": query})
                print("PRIMBOT: ", end="", flush=True)
                
                response = agent.run(messages.copy())
                print(response)
                print()  # Empty line for readability
                
                messages.append({"role": "assistant", "content": response})
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
    
    # Single query mode
    else:
        try:
            messages = [{"role": "user", "content": args.query}]
            response = agent.run(messages)
            print(response)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()

