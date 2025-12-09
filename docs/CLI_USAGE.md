# 📖 Guide d'Utilisation du CLI PRIMBOT - Étape par Étape

Guide complet pour utiliser PRIMBOT en ligne de commande, de l'installation à l'utilisation avancée.

## 🚀 Installation Complète (Première Fois)

### Étape 1: Installer PRIMBOT

```bash
# Installation depuis GitHub (recommandé)
pip install git+https://github.com/carlcgb/bot-prim.git
```

**Vérification:**
```bash
primbot --help
```

Si la commande n'est pas trouvée, consultez [CLI_INSTALLATION.md](CLI_INSTALLATION.md) pour ajouter `primbot` à votre PATH.

### Étape 2: Obtenir une Clé API Gemini (Gratuite)

1. Allez sur [Google AI Studio](https://aistudio.google.com/)
2. Connectez-vous avec votre compte Google
3. Cliquez sur "Get API Key"
4. Créez une nouvelle clé API ou utilisez une existante
5. Copiez la clé (format: `AIzaSy...`)

**Note:** Le plan gratuit offre 60 requêtes/minute et 1500 requêtes/jour - largement suffisant pour un usage personnel.

### Étape 3: Configurer PRIMBOT

**Option A: Configuration Interactive (Recommandée)**
```bash
primbot config
```

Vous serez guidé étape par étape:
- Entrez votre clé API Gemini
- (Optionnel) Configurez Ollama si vous l'utilisez
- Choisissez votre modèle par défaut
- Choisissez votre fournisseur par défaut

**Option B: Configuration Directe**
```bash
# Configurer uniquement la clé Gemini
primbot config --gemini-key AIzaSyVOTRE_CLE_ICI
```

**Vérifier la configuration:**
```bash
primbot config --show
```

### Étape 4: Initialiser la Base de Connaissances

Cette étape scrape la documentation PrimLogix et crée la base de données locale.

```bash
primbot ingest
```

**Ce qui se passe:**
1. ✅ Scraping de https://aide.primlogix.com/prim/fr/5-8/
2. ✅ Extraction du contenu textuel
3. ✅ Extraction des captures d'écran pertinentes (filtrage automatique des icônes/logos)
4. ✅ Création de la base de données vectorielle ChromaDB
5. ✅ Indexation pour la recherche rapide

**Durée:** 5-10 minutes selon votre connexion internet

**Note:** Cette étape n'est nécessaire qu'une seule fois. La base de connaissances est sauvegardée localement dans `chroma_db/`.

### Étape 5: Tester PRIMBOT

```bash
# Poser votre première question
primbot ask "comment changer mon mot de passe"
```

Si tout fonctionne, vous devriez voir une réponse détaillée avec des sources de documentation.

---

## 📋 Utilisation Quotidienne

### Poser une Question Simple

```bash
primbot ask "votre question ici"
```

**Exemples:**
```bash
primbot ask "comment créer un utilisateur"
primbot ask "erreur de connexion à la base de données"
primbot ask "comment personnaliser l'interface"
```

### Mode Interactif (Chat)

Pour avoir une conversation avec PRIMBOT:

```bash
primbot ask --interactive
# ou simplement
primbot ask -i
```

**Utilisation:**
- Tapez votre question et appuyez sur Entrée
- PRIMBOT répond avec des détails et des sources
- Continuez la conversation en posant des questions de suivi
- Tapez `quit`, `exit`, ou `q` pour quitter

**Exemple de session:**
```
$ primbot ask -i
🤖 PRIMBOT - Mode interactif
Tapez 'quit' pour quitter.

> comment configurer les permissions
[PRIMBOT répond avec détails...]

> et pour un utilisateur spécifique?
[PRIMBOT répond en contexte...]

> merci
> quit
Au revoir!
```

### Options Avancées

**Choisir un modèle spécifique:**
```bash
primbot ask "question" --model gemini-2.5-pro
```

**Choisir un fournisseur:**
```bash
# Utiliser Gemini (par défaut)
primbot ask "question" --provider gemini

# Utiliser Ollama (local, 100% gratuit)
primbot ask "question" --provider local --model llama3.1
```

**Combinaison d'options:**
```bash
primbot ask "question complexe" --model gemini-2.5-pro --provider gemini
```

---

## 🔧 Commandes de Configuration

### Afficher la Configuration Actuelle

```bash
primbot config --show
```

Affiche:
- Clé API Gemini (masquée)
- URL Ollama
- Modèle par défaut
- Fournisseur par défaut

### Modifier la Configuration

**Changer la clé API Gemini:**
```bash
primbot config --gemini-key NOUVELLE_CLE
```

**Configurer Ollama (pour usage local):**
```bash
# Si Ollama est sur le port par défaut
primbot config --ollama-url http://localhost:11434/v1

# Si Ollama est sur un autre port
primbot config --ollama-url http://localhost:8080/v1
```

**Changer le modèle par défaut:**
```bash
primbot config --model gemini-2.5-flash
```

**Changer le fournisseur par défaut:**
```bash
primbot config --provider local  # Pour utiliser Ollama par défaut
```

### Configuration Interactive Complète

```bash
primbot config
```

Suivez les prompts pour configurer tous les paramètres.

---

## 📚 Commandes de Base de Connaissances

### Réinitialiser la Base de Connaissances

Si vous voulez mettre à jour la documentation:

```bash
primbot ingest
```

**Note:** Cela va remplacer la base existante. Le processus prend 5-10 minutes.

### Vérifier l'État de la Base

La base de connaissances est vérifiée automatiquement à chaque question. Si elle est vide, PRIMBOT vous demandera de l'initialiser.

---

## 🎯 Cas d'Usage Courants

### 1. Résolution de Problème Technique

```bash
# Décrivez votre problème
primbot ask "je ne peux pas me connecter à l'application"

# Suivez les suggestions de PRIMBOT
# Posez des questions de suivi si nécessaire
primbot ask -i
> comment vérifier les logs
> où trouver les paramètres de connexion
```

### 2. Apprendre une Fonctionnalité

```bash
# Demandez comment faire quelque chose
primbot ask "comment créer un rapport personnalisé"

# PRIMBOT vous donnera des étapes détaillées avec des captures d'écran
```

### 3. Recherche Rapide

```bash
# Questions courtes pour des informations rapides
primbot ask "raccourcis clavier"
primbot ask "format de date"
primbot ask "limites de taille de fichier"
```

### 4. Mode Interactif pour Problèmes Complexes

```bash
# Pour des problèmes complexes, utilisez le mode interactif
primbot ask -i

> j'ai une erreur lors de l'import de données
[PRIMBOT répond...]

> le fichier fait 50MB
[PRIMBOT donne plus de détails...]

> comment le diviser?
[PRIMBOT explique la solution...]
```

---

## 🔍 Astuces et Bonnes Pratiques

### 1. Formuler des Questions Efficaces

✅ **Bon:**
- "comment créer un utilisateur avec des permissions spécifiques"
- "erreur 'connection refused' lors de la connexion"
- "comment exporter les données au format CSV"

❌ **Moins efficace:**
- "ça marche pas" (trop vague)
- "bug" (pas assez de contexte)
- "aide" (pas de question spécifique)

### 2. Utiliser le Mode Interactif pour les Problèmes Complexes

Le mode interactif permet à PRIMBOT de garder le contexte de la conversation, ce qui améliore la qualité des réponses.

### 3. Vérifier les Sources

PRIMBOT cite toujours ses sources. Vérifiez les URLs pour plus de détails si nécessaire.

### 4. Mettre à Jour la Base de Connaissances

Si la documentation PrimLogix est mise à jour, réinitialisez la base:

```bash
primbot ingest
```

---

## 🆘 Dépannage

### "Base de connaissances vide"

**Solution:**
```bash
primbot ingest
```

### "API key not found"

**Solution:**
```bash
primbot config --gemini-key VOTRE_CLE
# ou
primbot config  # Configuration interactive
```

### "Command not found"

**Solution:** Consultez [CLI_INSTALLATION.md](CLI_INSTALLATION.md) pour ajouter `primbot` à votre PATH.

### Réponses peu pertinentes

**Solutions:**
1. Reformulez votre question avec plus de détails
2. Utilisez des termes techniques de PrimLogix
3. Vérifiez que la base de connaissances est bien initialisée

---

## 📖 Commandes de Référence Rapide

```bash
# Configuration
primbot config                    # Configuration interactive
primbot config --show            # Afficher la config
primbot config --gemini-key KEY  # Configurer Gemini
primbot config --ollama-url URL  # Configurer Ollama

# Base de connaissances
primbot ingest                   # Initialiser/mettre à jour

# Questions
primbot ask "question"            # Question unique
primbot ask -i                   # Mode interactif
primbot ask "q" --model MODEL    # Avec modèle spécifique
primbot ask "q" --provider PROV  # Avec fournisseur spécifique

# Aide
primbot --help                   # Aide générale
primbot config --help           # Aide pour config
primbot ask --help              # Aide pour ask
```

---

## 🎓 Exemples Complets

### Exemple 1: Première Utilisation Complète

```bash
# 1. Installation
pip install git+https://github.com/carlcgb/bot-prim.git

# 2. Configuration
primbot config
# Entrez votre clé API Gemini quand demandé

# 3. Initialisation
primbot ingest
# Attendez 5-10 minutes

# 4. Première question
primbot ask "comment me connecter à PrimLogix"
```

### Exemple 2: Résolution de Problème

```bash
# Démarrer en mode interactif
primbot ask -i

> je reçois une erreur "permission denied"
[PRIMBOT explique les causes possibles...]

> comment vérifier mes permissions?
[PRIMBOT donne les étapes...]

> et si je suis administrateur?
[PRIMBOT explique les permissions admin...]

> quit
```

### Exemple 3: Utilisation avec Ollama (Local)

```bash
# 1. Installer Ollama (voir docs/FREE_AI_GUIDE.md)
# 2. Lancer Ollama: ollama serve
# 3. Télécharger un modèle: ollama pull llama3.1

# 4. Configurer PRIMBOT
primbot config --ollama-url http://localhost:11434/v1
primbot config --provider local
primbot config --model llama3.1

# 5. Utiliser
primbot ask "question"  # Utilise Ollama automatiquement
```

---

## 📚 Documentation Complémentaire

- **[CLI_INSTALLATION.md](CLI_INSTALLATION.md)** - Installation détaillée et ajout au PATH
- **[FREE_AI_GUIDE.md](FREE_AI_GUIDE.md)** - Guide complet des options AI gratuites
- **[AGENT_GUIDE.md](AGENT_GUIDE.md)** - Optimiser vos questions pour de meilleures réponses
- **[README.md](../README.md)** - Documentation principale du projet

---

## 🆘 Support

Pour toute question ou problème:
- Ouvrez une [issue sur GitHub](https://github.com/carlcgb/bot-prim/issues)
- Consultez la [documentation complète](../README.md)

