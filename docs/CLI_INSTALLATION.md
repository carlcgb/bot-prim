# 📦 Guide d'Installation du CLI PRIMBOT

Ce guide vous explique comment installer PRIMBOT CLI et l'ajouter à votre PATH pour l'utiliser depuis n'importe où.

## 🚀 Installation

### Option 1: Installation depuis GitHub (Recommandé)

```bash
pip install git+https://github.com/carlcgb/bot-prim.git
```

Cette commande installe automatiquement `primbot` dans votre environnement Python et l'ajoute au PATH si pip est correctement configuré.

### Option 2: Installation locale

```bash
# Cloner le repository
git clone https://github.com/carlcgb/bot-prim.git
cd bot-prim

# Installer les dépendances
pip install -r requirements.txt

# Installer le package en mode développement
pip install -e .
```

## ✅ Vérifier l'installation

Après l'installation, vérifiez que `primbot` est disponible:

```bash
primbot --help
```

Si vous obtenez une erreur `command not found`, suivez les instructions ci-dessous.

## 🔧 Ajouter primbot au PATH

### Windows

#### Méthode 1: Automatique (si pip est dans PATH)

L'installation avec `pip install` devrait automatiquement ajouter `primbot` au PATH. Si ce n'est pas le cas:

1. Trouvez où pip installe les scripts:
   ```powershell
   python -m site --user-base
   ```
   Cela affiche quelque chose comme: `C:\Users\VotreNom\AppData\Roaming\Python\Python313`

2. Ajoutez le dossier `Scripts` au PATH:
   - Ouvrez "Variables d'environnement" dans Windows
   - Ajoutez `C:\Users\VotreNom\AppData\Roaming\Python\Python313\Scripts` à la variable PATH utilisateur

#### Méthode 2: Manuel

1. Trouvez l'emplacement de l'installation:
   ```powershell
   python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
   ```

2. Ajoutez ce chemin à votre PATH utilisateur dans les variables d'environnement Windows

#### Méthode 3: Via PowerShell (temporaire pour la session)

```powershell
$env:Path += ";$(python -m site --user-base)\Scripts"
```

Pour le rendre permanent, ajoutez cette ligne à votre profil PowerShell:
```powershell
notepad $PROFILE
```

### Linux / macOS

#### Méthode 1: Automatique (si pip est dans PATH)

L'installation avec `pip install` devrait automatiquement ajouter `primbot` au PATH.

#### Méthode 2: Vérifier et ajouter manuellement

1. Trouvez où pip installe les scripts:
   ```bash
   python -m site --user-base
   ```
   Cela affiche quelque chose comme: `/home/username/.local`

2. Ajoutez au PATH dans votre `~/.bashrc` ou `~/.zshrc`:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

3. Rechargez votre shell:
   ```bash
   source ~/.bashrc  # ou source ~/.zshrc
   ```

#### Méthode 3: Installation système (nécessite sudo)

```bash
sudo pip install git+https://github.com/carlcgb/bot-prim.git
```

## 🧪 Tester l'installation

Après avoir ajouté au PATH, testez:

```bash
# Vérifier que primbot est disponible
primbot --help

# Vérifier la version
primbot --version

# Tester une commande
primbot config --show
```

## 📋 Configuration initiale

Une fois installé, configurez PRIMBOT:

```bash
# 1. Configurer l'API Gemini (gratuit)
primbot config --gemini-key VOTRE_CLE_API
# Ou configuration interactive:
primbot config

# 2. Initialiser la base de connaissances
primbot ingest

# 3. Tester avec une question
primbot ask "comment changer mon mot de passe"
```

## 🔍 Dépannage

### "command not found" après installation

1. **Vérifiez que pip a bien installé le script:**
   ```bash
   # Windows
   python -m site --user-base
   # Vérifiez que primbot.exe existe dans le dossier Scripts
   
   # Linux/macOS
   ls ~/.local/bin/primbot
   ```

2. **Vérifiez votre PATH:**
   ```bash
   # Windows PowerShell
   $env:Path -split ';' | Select-String "Python"
   
   # Linux/macOS
   echo $PATH | tr ':' '\n' | grep -i python
   ```

3. **Réinstallez si nécessaire:**
   ```bash
   pip uninstall primbot
   pip install git+https://github.com/carlcgb/bot-prim.git
   ```

### Le script existe mais n'est pas dans PATH

Ajoutez manuellement le chemin trouvé avec `python -m site --user-base` à votre PATH (voir instructions ci-dessus).

### Utiliser avec un environnement virtuel

Si vous utilisez un environnement virtuel, activez-le d'abord:

```bash
# Activer l'environnement virtuel
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows

# Installer
pip install git+https://github.com/carlcgb/bot-prim.git

# primbot sera disponible uniquement quand l'environnement est activé
```

## 📝 Notes importantes

- **Windows**: Assurez-vous que Python est dans votre PATH avant d'installer
- **Linux/macOS**: Utilisez `pip install --user` si vous n'avez pas les droits sudo
- **Environnements virtuels**: `primbot` sera disponible uniquement quand l'environnement est activé
- **Configuration**: La configuration est sauvegardée dans `~/.primbot/config.json`

## 🆘 Support

Si vous rencontrez des problèmes:
1. Vérifiez que Python 3.8+ est installé: `python --version`
2. Vérifiez que pip est à jour: `pip install --upgrade pip`
3. Consultez les issues sur [GitHub](https://github.com/carlcgb/bot-prim/issues)

