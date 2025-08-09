# 🔐 Guide d'Authentification - Chat Terminal App

## 🚀 Démarrage Rapide

### 1. Installation des Dépendances
```bash
# Activer l'environnement virtuel
.venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Lancement du Client
```bash
# Avec l'environnement virtuel
.venv\Scripts\python.exe -m client.main

# Ou utiliser le script batch
run-client.bat
```

## 🔑 Commandes d'Authentification

### Connexion
```bash
/login <username> <password>
```
**Exemple :**
```bash
/login admin admin
```

### Création de Compte
```bash
/register <username> <password> [email]
```
**Exemples :**
```bash
/register john secret123
/register alice password123 alice@example.com
```

### Vérification de l'Utilisateur
```bash
/whoami
```
Affiche les informations de l'utilisateur connecté :
- Nom d'utilisateur
- Email
- Permissions
- Date de création
- Dernière connexion

### Déconnexion
```bash
/logout
```

## 👥 Utilisateur par Défaut

Un utilisateur administrateur est créé automatiquement :
- **Nom d'utilisateur :** `admin`
- **Mot de passe :** `admin`
- **Permissions :** `admin`

## 🎨 Thèmes Disponibles

```bash
/themes                    # Lister tous les thèmes
/theme <nom>              # Changer de thème
```

**Thèmes disponibles :**
- `default` - Thème par défaut
- `dark` - Thème sombre
- `light` - Thème clair
- `neon` - Thème néon
- `monochrome` - Thème monochrome

## 📁 Commandes de Fichiers

```bash
/send <chemin>            # Envoyer un fichier
/files                    # Lister les fichiers serveur
/download <nom> [dir]     # Télécharger un fichier
/local [dir]              # Lister les fichiers locaux
```

## 💻 Exécution de Code

```bash
/run <lang> <fichier> [args..]
```

**Langages supportés :**
- `c` - C
- `cpp` - C++
- `cs` ou `c#` - C#
- `shell` - Scripts shell

 

## 🆘 Aide

```bash
/help                     # Afficher l'aide complète
/clear                    # Nettoyer l'écran
/quit                     # Quitter l'application
```

## 🔧 Dépannage

### Problème : Module JWT non trouvé
```bash
# Installer PyJWT dans l'environnement virtuel
.venv\Scripts\activate
pip install PyJWT==2.8.0
```

### Problème : Imports relatifs
Assurez-vous d'utiliser l'environnement virtuel :
```bash
.venv\Scripts\python.exe -m client.main
```

### Problème : Connexion échouée
1. Vérifiez que le serveur est démarré
2. Vérifiez les URLs de connexion
3. Utilisez les commandes `/login` pour vous connecter

## 📊 Exemples d'Utilisation

### Session Complète
```bash
# 1. Lancer le client
.venv\Scripts\python.exe -m client.main

# 2. Se connecter
/login admin admin

# 3. Vérifier l'utilisateur
/whoami

# 4. Changer de thème
/theme dark

# 5. Lister les fichiers
/files

# 6. Envoyer un fichier
/send mon_fichier.txt

# 7. Se déconnecter
/logout

# 8. Quitter
/quit
```

## 🔒 Sécurité

- Les mots de passe sont hashés avec salt
- Les tokens JWT expirent après 24h
- Les données sont persistées dans `.config/`
- Chaque utilisateur a ses propres permissions

## 📝 Notes

- L'authentification est locale (pas de serveur d'auth externe)
- Les données sont stockées dans le répertoire `.config/`
- L'utilisateur `admin` a toutes les permissions
- Les nouveaux utilisateurs ont les permissions `user` par défaut
