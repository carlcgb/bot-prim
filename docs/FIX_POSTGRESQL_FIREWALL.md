# 🔧 Résoudre les Problèmes de Firewall PostgreSQL

## Problème : Connexion PostgreSQL bloquée par le firewall

Si vous obtenez des erreurs comme :
- `could not translate host name`
- `Connection timeout`
- `Connection refused`

Voici les solutions par ordre de priorité :

## ✅ Solution 1 : Connection Pooling (Port 6543) - RECOMMANDÉ

Le **Connection Pooling** utilise le port **6543** qui est souvent moins bloqué que le port 5432.

### Configuration automatique

```bash
python setup_supabase_pooling.py
```

Cela configure automatiquement votre `.env` avec le port 6543.

### Configuration manuelle

Modifiez votre `.env` :

```toml
# Au lieu de port 5432
SUPABASE_DB_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@db.qwpdehqkxcvsblkwpbop.supabase.co:5432/postgres

# Utilisez le port 6543 (Connection Pooling)
SUPABASE_DB_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@db.qwpdehqkxcvsblkwpbop.supabase.co:6543/postgres
```

### Avantages du Connection Pooling

- ✅ Port 6543 souvent moins bloqué
- ✅ PgBouncer gère les connexions efficacement
- ✅ Meilleure compatibilité avec les firewalls
- ✅ Même performance pour la plupart des cas

### Limitations

⚠️ **Note importante** : Avec Connection Pooling, certaines fonctionnalités PostgreSQL avancées peuvent être limitées :
- Pas de transactions multiples
- Pas de `PREPARE` statements
- Certaines extensions peuvent ne pas fonctionner

Pour PRIMBOT, cela devrait fonctionner parfaitement car nous utilisons des requêtes simples.

---

## ✅ Solution 2 : Autoriser votre IP dans Supabase

1. **Obtenez votre IP publique** :
   ```bash
   # Windows PowerShell
   (Invoke-WebRequest -Uri "https://api.ipify.org").Content
   
   # Linux/macOS
   curl https://api.ipify.org
   ```

2. **Autorisez l'IP dans Supabase** :
   - Allez sur [Supabase Dashboard](https://supabase.com/dashboard)
   - Sélectionnez votre projet
   - **Settings** > **Database**
   - Section **Connection pooling** ou **Network restrictions**
   - Ajoutez votre IP publique

3. **Testez** :
   ```bash
   python test_supabase_connection.py
   ```

---

## ✅ Solution 3 : Utiliser un VPN ou un autre réseau

Si vous êtes sur un réseau d'entreprise restrictif :

1. **Testez depuis votre réseau personnel**
2. **Utilisez un hotspot mobile**
3. **Configurez un VPN** (si autorisé)

Cela permet de confirmer si c'est bien un problème de firewall.

---

## ✅ Solution 4 : Configuration hybride (Temporaire)

En attendant de résoudre le problème PostgreSQL :

- **API Supabase** (fonctionne) : Pour conversations et feedback
- **ChromaDB local** : Pour la recherche vectorielle
- **Migration future** : Vers Supabase PostgreSQL quand disponible

### Code exemple

```python
import os

# Utiliser Supabase API pour conversations
USE_SUPABASE_API = True

# Utiliser ChromaDB pour recherche vectorielle
USE_CHROMADB = True

if USE_SUPABASE_API:
    from storage_supabase import get_storage
    storage = get_storage()
    # Sauvegarder conversations
    storage.save_conversation(user_id, question, answer)

if USE_CHROMADB:
    from knowledge_base import query_knowledge_base
    # Recherche vectorielle
    results = query_knowledge_base(query)
```

---

## 🔍 Diagnostic

Exécutez le script de diagnostic :

```bash
python fix_postgresql_connection.py
```

Ce script teste :
- ✅ Résolution DNS
- ✅ Connexion TCP port 5432
- ✅ Connexion TCP port 6543 (Connection Pooling)
- ✅ Connexion PostgreSQL directe
- ✅ Connexion PostgreSQL avec Pooling

---

## 📋 Checklist de dépannage

- [ ] Testé Connection Pooling (port 6543)
- [ ] IP autorisée dans Supabase
- [ ] Testé depuis un autre réseau
- [ ] Vérifié les paramètres firewall/proxy
- [ ] Testé avec `fix_postgresql_connection.py`
- [ ] Vérifié que le mot de passe est correctement encodé

---

## 🆘 Si rien ne fonctionne

1. **Utilisez l'API Supabase** (déjà fonctionnelle) pour :
   - Conversations
   - Feedback
   - Données relationnelles

2. **Gardez ChromaDB local** pour :
   - Recherche vectorielle
   - Base de connaissances

3. **Migrez plus tard** quand la connexion PostgreSQL sera disponible

---

## 📚 Ressources

- [Supabase Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Supabase Network Restrictions](https://supabase.com/docs/guides/database/network-restrictions)
- [PgBouncer Documentation](https://www.pgbouncer.org/)

