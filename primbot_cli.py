#!/usr/bin/env python3
"""
PRIMBOT CLI - Command Line Interface for PrimLogix Debug Agent
Usage: primbot [command] [options]
"""

import argparse
import sys
import os
import json
from pathlib import Path
from agent import PrimAgent
from knowledge_base import collection

# Configuration file path
CONFIG_DIR = Path.home() / ".primbot"
CONFIG_FILE = CONFIG_DIR / "config.json"

def ensure_config_dir():
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True)
    return CONFIG_DIR

def load_config():
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(config):
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

def cmd_config(args):
    """Configure API keys and settings."""
    config = load_config()
    
    if args.gemini_key:
        config['gemini_api_key'] = args.gemini_key
        # Also set in environment
        os.environ['GEMINI_API_KEY'] = args.gemini_key
        print("✅ Clé API Gemini configurée")
    
    if args.ollama_url:
        config['ollama_url'] = args.ollama_url
        print(f"✅ URL Ollama configurée: {args.ollama_url}")
    
    if args.model:
        config['default_model'] = args.model
        print(f"✅ Modèle par défaut configuré: {args.model}")
    
    if args.provider:
        config['default_provider'] = args.provider
        print(f"✅ Fournisseur par défaut configuré: {args.provider}")
    
    if args.show:
        print("\n📋 Configuration actuelle:")
        print(f"  Gemini API Key: {'✅ Configurée' if config.get('gemini_api_key') else '❌ Non configurée'}")
        print(f"  Ollama URL: {config.get('ollama_url', 'http://localhost:11434/v1')}")
        print(f"  Modèle par défaut: {config.get('default_model', 'gemini-2.5-flash')}")
        print(f"  Fournisseur par défaut: {config.get('default_provider', 'gemini')}")
        print(f"  Fichier de config: {CONFIG_FILE}")
        return
    
    if not any([args.gemini_key, args.ollama_url, args.model, args.provider]):
        # Interactive configuration
        print("🔧 Configuration interactive de PRIMBOT\n")
        
        # Gemini API Key
        if not config.get('gemini_api_key') and not os.getenv('GEMINI_API_KEY'):
            print("📝 Configuration de Gemini API (gratuit)")
            print("   Obtenez votre clé gratuite sur: https://aistudio.google.com/\n")
            gemini_key = input("Entrez votre clé API Gemini (ou appuyez sur Entrée pour ignorer): ").strip()
            if gemini_key:
                config['gemini_api_key'] = gemini_key
                os.environ['GEMINI_API_KEY'] = gemini_key
                print("✅ Clé API Gemini configurée\n")
        else:
            print("✅ Clé API Gemini déjà configurée\n")
        
        # Ollama URL
        current_ollama = config.get('ollama_url', 'http://localhost:11434/v1')
        print(f"📝 Configuration d'Ollama (100% gratuit, local)")
        print(f"   URL actuelle: {current_ollama}")
        ollama_url = input("Entrez l'URL Ollama (ou appuyez sur Entrée pour garder la valeur actuelle): ").strip()
        if ollama_url:
            config['ollama_url'] = ollama_url
            print("✅ URL Ollama configurée\n")
        
        # Default model
        current_model = config.get('default_model', 'gemini-2.5-flash')
        print(f"📝 Modèle par défaut")
        print(f"   Modèle actuel: {current_model}")
        model = input("Entrez le nom du modèle (ou appuyez sur Entrée pour garder): ").strip()
        if model:
            config['default_model'] = model
            print("✅ Modèle par défaut configuré\n")
        
        # Default provider
        current_provider = config.get('default_provider', 'gemini')
        print(f"📝 Fournisseur par défaut")
        print(f"   Fournisseur actuel: {current_provider}")
        provider = input("Entrez le fournisseur (gemini/local) (ou appuyez sur Entrée pour garder): ").strip()
        if provider in ['gemini', 'local']:
            config['default_provider'] = provider
            print("✅ Fournisseur par défaut configuré\n")
    
    save_config(config)
    print(f"\n💾 Configuration sauvegardée dans: {CONFIG_FILE}")

def cmd_ingest(args):
    """Ingest knowledge base from PrimLogix documentation."""
    print("📥 Initialisation de la base de connaissances PrimLogix\n")
    
    try:
        from scraper import run_scraper
        from knowledge_base import add_documents
        
        print("🔍 Scraping de la documentation PrimLogix...")
        print("   Cela peut prendre 5-10 minutes, veuillez patienter...\n")
        
        data = run_scraper()
        
        print(f"\n💾 Ajout de {len(data)} pages à la base de connaissances...")
        add_documents(data)
        
        final_count = collection.count()
        print(f"\n✅ Base de connaissances initialisée avec {final_count} documents!")
        print(f"📚 Prêt à répondre à vos questions sur PrimLogix!\n")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'ingestion: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_ask(args):
    """Ask a question to PRIMBOT."""
    config = load_config()
    
    # Get API key
    api_key = args.api_key
    if not api_key:
        api_key = config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY', '')
    
    # Get provider
    provider = args.provider or config.get('default_provider', 'gemini')
    
    # Get model
    model = args.model or config.get('default_model')
    if not model:
        model = 'gemini-2.5-flash' if provider == 'gemini' else 'llama3.1'
    
    # Get base URL for Ollama
    base_url = args.base_url
    if not base_url and provider == 'local':
        base_url = config.get('ollama_url', 'http://localhost:11434/v1')
    
    # Prompt for API key if needed
    if not api_key and provider == 'gemini':
        print("🔑 Clé API Gemini requise", file=sys.stderr)
        print("   Configurez-la avec: primbot config --gemini-key VOTRE_CLE", file=sys.stderr)
        print("   Ou obtenez-en une gratuite sur: https://aistudio.google.com/\n", file=sys.stderr)
        api_key = input("Entrez votre clé API Gemini (ou Ctrl+C pour annuler): ").strip()
        if not api_key:
            print("❌ Clé API requise", file=sys.stderr)
            sys.exit(1)
        # Save to config
        config['gemini_api_key'] = api_key
        save_config(config)
    
    # Map provider
    provider_map = {
        'gemini': 'Google Gemini',
        'local': 'Local (Ollama/LocalAI)'
    }
    provider_name = provider_map.get(provider, 'Google Gemini')
    
    # Check knowledge base
    kb_count = collection.count()
    if kb_count == 0:
        print("⚠️  Base de connaissances vide!", file=sys.stderr)
        print("   Initialisez-la avec: primbot ingest\n", file=sys.stderr)
        if not args.query:  # Only prompt in interactive mode
            response = input("Voulez-vous initialiser maintenant? (o/n): ").strip().lower()
            if response in ['o', 'oui', 'y', 'yes']:
                cmd_ingest(argparse.Namespace())
            else:
                print("⚠️  La recherche ne fonctionnera pas sans base de connaissances.", file=sys.stderr)
                sys.exit(1)
    
    # Initialize agent
    try:
        agent = PrimAgent(
            api_key=api_key or 'ollama',
            base_url=base_url,
            model=model,
            provider=provider_name
        )
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de l'agent: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Interactive mode
    if args.interactive or not args.query:
        print("🤖 PRIMBOT CLI - PrimLogix Debug Agent")
        if kb_count > 0:
            print(f"📚 Base de connaissances: {kb_count} documents")
        print(f"🤖 Fournisseur: {provider_name} ({model})")
        print("💡 Tapez 'exit' ou 'quit' pour quitter\n")
        
        messages = []
        while True:
            try:
                query = input("Vous: ").strip()
                if not query:
                    continue
                if query.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Au revoir!")
                    break
                
                messages.append({"role": "user", "content": query})
                print("PRIMBOT: ", end="", flush=True)
                
                response = agent.run(messages.copy())
                print(response)
                print()  # Empty line
                
                messages.append({"role": "assistant", "content": response})
                
            except KeyboardInterrupt:
                print("\n\n👋 Au revoir!")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}", file=sys.stderr)
    
    # Single query mode
    else:
        try:
            messages = [{"role": "user", "content": args.query}]
            response = agent.run(messages)
            print(response)
        except Exception as e:
            print(f"❌ Erreur: {e}", file=sys.stderr)
            sys.exit(1)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='PRIMBOT CLI - PrimLogix Debug Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  primbot config                    # Configuration interactive
  primbot config --gemini-key KEY   # Configurer la clé Gemini
  primbot ingest                    # Initialiser la base de connaissances
  primbot ask "comment changer mon mot de passe"
  primbot ask --interactive         # Mode interactif
  primbot ask "question" --provider local --model llama3.1
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configurer PRIMBOT')
    config_parser.add_argument('--gemini-key', help='Clé API Gemini')
    config_parser.add_argument('--ollama-url', help='URL Ollama (défaut: http://localhost:11434/v1)')
    config_parser.add_argument('--model', help='Modèle par défaut')
    config_parser.add_argument('--provider', choices=['gemini', 'local'], help='Fournisseur par défaut')
    config_parser.add_argument('--show', action='store_true', help='Afficher la configuration actuelle')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Initialiser la base de connaissances')
    
    # Ask command (main command)
    ask_parser = subparsers.add_parser('ask', help='Poser une question à PRIMBOT (commande par défaut)')
    ask_parser.add_argument('query', nargs='?', help='Question à poser')
    ask_parser.add_argument('--provider', choices=['gemini', 'local'], help='Fournisseur AI (gemini/local)')
    ask_parser.add_argument('--api-key', '--key', dest='api_key', help='Clé API (prioritaire sur config)')
    ask_parser.add_argument('--model', help='Nom du modèle')
    ask_parser.add_argument('--base-url', help='URL de base pour Ollama')
    ask_parser.add_argument('--interactive', '-i', action='store_true', help='Mode interactif')
    
    # Legacy support: if no command, treat as 'ask'
    args = parser.parse_args()
    
    if not args.command:
        # No command provided, treat as 'ask' for backward compatibility
        # Re-parse with query as positional argument
        ask_args = argparse.Namespace()
        ask_args.query = None
        ask_args.provider = None
        ask_args.api_key = None
        ask_args.model = None
        ask_args.base_url = None
        ask_args.interactive = False
        
        # Parse remaining args
        remaining = sys.argv[1:]
        if remaining:
            if remaining[0] in ['--interactive', '-i']:
                ask_args.interactive = True
            elif remaining[0] in ['--help', '-h']:
                parser.print_help()
                return
            elif not remaining[0].startswith('--'):
                ask_args.query = remaining[0]
            
            # Parse other options
            i = 1
            while i < len(remaining):
                if remaining[i] == '--provider' and i + 1 < len(remaining):
                    ask_args.provider = remaining[i + 1]
                    i += 2
                elif remaining[i] in ['--key', '--api-key'] and i + 1 < len(remaining):
                    ask_args.api_key = remaining[i + 1]
                    i += 2
                elif remaining[i] == '--model' and i + 1 < len(remaining):
                    ask_args.model = remaining[i + 1]
                    i += 2
                elif remaining[i] == '--base-url' and i + 1 < len(remaining):
                    ask_args.base_url = remaining[i + 1]
                    i += 2
                elif remaining[i] in ['--interactive', '-i']:
                    ask_args.interactive = True
                    i += 1
                else:
                    i += 1
        
        cmd_ask(ask_args)
        return
    
    # Execute command
    if args.command == 'config':
        cmd_config(args)
    elif args.command == 'ingest':
        cmd_ingest(args)
    elif args.command == 'ask':
        cmd_ask(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
