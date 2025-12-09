# 🆓 Guide des Options AI Gratuites pour PRIMBOT

PRIMBOT supporte plusieurs options d'IA gratuites pour répondre à vos besoins de débogage et d'assistance.

## 🎯 Options Disponibles

### 1. Google Gemini (Recommandé) ⭐

**Avantages:**
- ✅ **Plan gratuit généreux** : 60 requêtes/minute, 1500 requêtes/jour
- ✅ **Modèles performants** : Gemini 2.5 Flash (rapide) et Gemini 2.5 Pro (puissant)
- ✅ **Fonction calling** : Support natif pour la recherche dans la base de connaissances
- ✅ **Pas de carte de crédit** requise
- ✅ **API stable** et bien documentée

**Comment obtenir une clé API gratuite:**

1. Allez sur [Google AI Studio](https://aistudio.google.com/)
2. Connectez-vous avec votre compte Google
3. Cliquez sur "Get API Key"
4. Créez un nouveau projet ou sélectionnez un projet existant
5. Copiez votre clé API (commence par `AIza...`)

**Modèles recommandés:**
- `gemini-2.5-flash` : **Recommandé** - Rapide, gratuit, excellent pour la plupart des cas
- `gemini-2.5-pro` : Plus puissant mais peut avoir des limites sur le plan gratuit
- `gemini-2.0-flash` : Alternative stable

**Configuration:**
```bash
# Variable d'environnement
export GEMINI_API_KEY="votre_cle_api"

# Ou dans Streamlit secrets
GEMINI_API_KEY = "votre_cle_api"
```

---

### 2. Ollama (100% Gratuit, Local) 🏠

**Avantages:**
- ✅ **100% gratuit** - Aucune clé API nécessaire
- ✅ **Fonctionne localement** - Vos données restent sur votre machine
- ✅ **Aucune limite** de requêtes
- ✅ **Modèles open-source** performants
- ✅ **Pas de connexion internet** requise (après installation)

**Inconvénients:**
- ⚠️ Nécessite une installation locale
- ⚠️ Requiert des ressources système (RAM, CPU)
- ⚠️ Première installation peut prendre du temps

**Installation:**

1. **Téléchargez Ollama:**
   - Windows: [ollama.ai/download](https://ollama.ai/download)
   - macOS: `brew install ollama`
   - Linux: `curl -fsSL https://ollama.ai/install.sh | sh`

2. **Installez un modèle:**
   ```bash
   # Modèle recommandé (équilibré)
   ollama pull llama3.1
   
   # Ou pour plus de puissance (nécessite plus de RAM)
   ollama pull llama3.1:70b
   
   # Modèle rapide et léger
   ollama pull llama3.2
   ```

3. **Lancez Ollama:**
   ```bash
   ollama serve
   ```

4. **Configurez PRIMBOT:**
   - Dans l'interface Streamlit, sélectionnez "Local (Ollama/LocalAI)"
   - Base URL: `http://localhost:11434/v1`
   - Model: `llama3.1` (ou le modèle que vous avez installé)

**Modèles recommandés:**

| Modèle | Taille | RAM requise | Performance | Usage |
|--------|--------|--------------|-------------|-------|
| `llama3.2` | 2B | ~2 GB | Rapide | Tests rapides |
| `llama3.1` | 8B | ~8 GB | Équilibré | **Recommandé** |
| `llama3.1:70b` | 70B | ~40 GB | Excellent | Production |
| `mistral` | 7B | ~7 GB | Rapide | Alternative |
| `mixtral` | 8x7B | ~26 GB | Très puissant | Cas complexes |

**Vérification:**
```bash
# Vérifier que Ollama fonctionne
curl http://localhost:11434/api/tags

# Tester un modèle
ollama run llama3.1 "Bonjour, comment ça va?"
```

---

## 📊 Comparaison des Options

| Critère | Gemini | Ollama |
|---------|--------|--------|
| **Coût** | Gratuit (limites) | 100% Gratuit |
| **Installation** | Aucune | Requise |
| **Clé API** | Oui (gratuite) | Non |
| **Internet** | Requis | Optionnel |
| **Vitesse** | Très rapide | Dépend du hardware |
| **Qualité** | Excellente | Bonne à excellente |
| **Fonction calling** | Natif | Supporté |
| **Limites** | 60 req/min | Aucune |
| **Confidentialité** | Données envoyées | 100% local |

---

## 🎯 Quelle Option Choisir?

### Choisissez **Gemini** si:
- ✅ Vous voulez une solution **rapide et simple**
- ✅ Vous avez une **connexion internet stable**
- ✅ Vous êtes **débutant** ou préférez ne pas installer de logiciel
- ✅ Vous avez besoin de **réponses très rapides**
- ✅ Vous travaillez sur des **données non sensibles**

### Choisissez **Ollama** si:
- ✅ Vous voulez une solution **100% gratuite sans limites**
- ✅ Vous avez des **données sensibles** (tout reste local)
- ✅ Vous avez un **bon ordinateur** (8GB+ RAM recommandé)
- ✅ Vous voulez **contrôler totalement** votre environnement
- ✅ Vous n'avez pas toujours **internet** disponible

---

## 🚀 Configuration Optimale

### Pour le Développement Local

**Option 1: Gemini (Recommandé pour débuter)**
```bash
export GEMINI_API_KEY="votre_cle"
streamlit run app.py
```

**Option 2: Ollama (Pour la confidentialité)**
```bash
# Terminal 1: Lancer Ollama
ollama serve

# Terminal 2: Lancer PRIMBOT
streamlit run app.py
# Sélectionner "Local (Ollama/LocalAI)" dans l'interface
```

### Pour le Déploiement (Streamlit Cloud)

**Gemini uniquement** (Ollama nécessite un serveur local):
```toml
# Dans Streamlit Cloud secrets
GEMINI_API_KEY = "votre_cle_api"
```

---

## 💡 Conseils d'Optimisation

### Pour Gemini:
1. Utilisez `gemini-2.5-flash` par défaut (rapide et gratuit)
2. Réservez `gemini-2.5-pro` pour les questions complexes
3. Respectez les limites (60 req/min) pour éviter les erreurs

### Pour Ollama:
1. Commencez avec `llama3.1` (8B) - bon équilibre
2. Si vous avez 16GB+ RAM, essayez `llama3.1:70b` pour de meilleures réponses
3. Fermez les autres applications pour libérer de la RAM
4. Utilisez `llama3.2` si vous avez moins de 8GB RAM

---

## 🔧 Dépannage

### Gemini ne fonctionne pas?
- ✅ Vérifiez que votre clé API est correcte
- ✅ Vérifiez que vous n'avez pas dépassé les limites gratuites
- ✅ Essayez un autre modèle (gemini-2.0-flash)

### Ollama ne fonctionne pas?
- ✅ Vérifiez que `ollama serve` est lancé
- ✅ Vérifiez que le modèle est installé: `ollama list`
- ✅ Testez l'API: `curl http://localhost:11434/api/tags`
- ✅ Vérifiez que le port 11434 n'est pas bloqué par un firewall

---

## 📚 Ressources

- **Gemini**: [Google AI Studio](https://aistudio.google.com/)
- **Ollama**: [ollama.ai](https://ollama.ai/)
- **Documentation Ollama**: [github.com/ollama/ollama](https://github.com/ollama/ollama)

---

**Dernière mise à jour**: Décembre 2024

