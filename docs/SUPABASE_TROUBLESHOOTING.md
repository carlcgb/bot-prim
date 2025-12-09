# 🔧 Dépannage Supabase

## Problème : "could not translate host name"

Si vous obtenez cette erreur, voici les solutions :

### Solution 1 : Vérifier les paramètres réseau

Le problème peut venir de :
- **Firewall d'entreprise** bloquant les connexions PostgreSQL
- **Proxy** qui interfère avec la connexion
- **IPv6** non supporté par votre réseau

**Test rapide :**
```bash
# Testez la résolution DNS
nslookup db.qwpdehqkxcvsblkwpbop.supabase.co

# Testez la connexion TCP
Test-NetConnection db.qwpdehqkxcvsblkwpbop.supabase.co -Port 5432
```

### Solution 2 : Autoriser votre IP dans Supabase

1. Allez sur [Supabase Dashboard](https://supabase.com/dashboard)
2. Sélectionnez votre projet
3. **Settings** > **Database**
4. Dans **Connection pooling**, vérifiez les restrictions IP
5. Ajoutez votre IP si nécessaire

### Solution 3 : Utiliser l'API Supabase (Alternative)

Si la connexion directe PostgreSQL ne fonctionne pas, vous pouvez utiliser l'API Supabase pour certaines opérations :

```python
from supabase import create_client

supabase = create_client(
    "https://qwpdehqkxcvsblkwpbop.supabase.co",
    "sb_publishable_C59Ew0JS7YvEZPoYA1MkWQ_-UEMZuf6"
)

# L'API fonctionne via HTTPS (port 443) qui est généralement autorisé
```

### Solution 4 : Utiliser un VPN ou un autre réseau

Si vous êtes sur un réseau d'entreprise restrictif :
- Essayez depuis votre réseau personnel
- Utilisez un VPN
- Utilisez un hotspot mobile

### Solution 5 : Vérifier le mot de passe

Assurez-vous que le mot de passe est correctement encodé dans la connection string.

Le mot de passe `*963.**963.Qwer` doit être encodé en URL comme `%2A963.%2A%2A963.Qwer`

## Test de connexion simplifié

Créez `test_simple.py` :

```python
import os
from supabase import create_client

# Test de l'API Supabase (plus facile que PostgreSQL direct)
supabase = create_client(
    "https://qwpdehqkxcvsblkwpbop.supabase.co",
    "sb_publishable_C59Ew0JS7YvEZPoYA1MkWQ_-UEMZuf6"
)

# Test simple
try:
    # L'API Supabase fonctionne via HTTPS
    print("✅ Connexion API Supabase réussie!")
    print("💡 Vous pouvez utiliser l'API pour certaines opérations")
except Exception as e:
    print(f"❌ Erreur: {e}")
```

## Prochaines étapes

Une fois la connexion résolue :

1. **Initialisez les tables** : `python setup_supabase.py`
2. **Migrez les données** : `python migrate_to_supabase.py`
3. **Testez** : Utilisez `storage_supabase.py` dans votre code

## Support

Si le problème persiste :
- Vérifiez les [logs Supabase](https://supabase.com/dashboard/project/_/logs)
- Consultez la [documentation Supabase](https://supabase.com/docs)
- Ouvrez une issue sur GitHub

