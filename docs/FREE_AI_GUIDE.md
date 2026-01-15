# 🆓 Guide des Options AI Gratuites pour PRIMBOT

PRIMBOT utilise **Google Gemini** pour répondre à vos besoins de débogage et d'assistance.

## 🎯 Option Disponible

### Google Gemini (Recommandé) ⭐

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

## 🚀 Configuration Optimale

### Pour le Développement Local
```bash
export GEMINI_API_KEY="votre_cle"
streamlit run app.py
```

### Pour le Déploiement (Streamlit Cloud)
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

---

## 🔧 Dépannage

### Gemini ne fonctionne pas?
- ✅ Vérifiez que votre clé API est correcte
- ✅ Vérifiez que vous n'avez pas dépassé les limites gratuites
- ✅ Essayez un autre modèle (gemini-2.0-flash)

---

## 📚 Ressources

- **Gemini**: [Google AI Studio](https://aistudio.google.com/)

---

**Dernière mise à jour**: Décembre 2024


