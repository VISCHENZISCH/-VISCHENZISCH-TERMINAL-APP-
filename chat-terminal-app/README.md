## Chat Terminal App

Application de chat en temps réel (WebSocket) avec envoi/réception de fichiers, **système de thèmes personnalisables** et **barres de progression avancées**.

### 🌟 Nouvelles Fonctionnalités (v2.1)

#### 🎨 Système de Thèmes
- **5 thèmes prédéfinis** : Default, Dark, Light, Neon, Monochrome
- **Personnalisation complète** : Couleurs pour tous les éléments
- **Persistance** : Sauvegarde automatique des préférences
- **Commandes** : `/theme <nom>` et `/themes`

#### 📊 Barres de Progression
- **Upload/Download** : Progression en temps réel
- **Informations détaillées** : Vitesse, ETA, pourcentage
- **Interface visuelle** : Barres avec caractères Unicode
- **Couleurs adaptatives** : S'adapte au thème actuel

### Fonctionnalités
- Chat temps réel via WebSocket
- Upload de fichiers vers le serveur (HTTP POST /upload)
- Listing et téléchargement de fichiers (HTTP GET /files et /uploads/<nom>)
- Exécution côté serveur de code C, C++, C# et Shell (endpoint POST /run)
- **Système de thèmes personnalisables**
- **Barres de progression pour les transferts**
 

### Prérequis
- Python 3.10+

### Installation
```bash
cd chat-terminal-app
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

### Lancer le serveur
```bash
uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
```

Le serveur expose:
- WS: ws://127.0.0.1:8000/ws
- HTTP: http://127.0.0.1:8000
  - POST /upload (form-data, champ "file")
  - GET /files (JSON)
  - GET /uploads/<nom_fichier> (statique)

### Lancer le client (terminal)
```bash
python -m client.main --http http://127.0.0.1:8000 --ws ws://127.0.0.1:8000/ws
```

Sur Windows, vous pouvez aussi utiliser le script:
```bat
run-client.bat
```

Variables d'environnement pour override:
- `HTTP_URL` (ex: `set HTTP_URL=http://192.168.1.10:8000`)
- `WS_URL` (ex: `set WS_URL=ws://192.168.1.10:8000/ws`)
Ou passer des arguments additionnels: `run-client.bat --http http://... --ws ws://...`

### 🎨 Utilisation des Thèmes

#### Changer de Thème
```bash
/theme dark          # Thème sombre
/theme light         # Thème clair
/theme neon          # Thème néon
/theme monochrome    # Thème monochrome
/theme default       # Thème par défaut
```

#### Lister les Thèmes
```bash
/themes
```

### 📊 Barres de Progression

Les barres de progression s'affichent automatiquement lors des transferts de fichiers :

#### Upload
```bash
/send mon_fichier.txt
```
Affiche : `Envoi de mon_fichier.txt: [████████████████████░░░░░░░░░░] 60.0% (1.2MB/2.0MB) 500KB/s ETA: 1.6s`

#### Download
```bash
/download fichier_serveur.txt
```
Affiche : `Téléchargement de fichier_serveur.txt: [████████████████████████████████████████] 100.0% (1.8MB/1.8MB) 800KB/s ETA: 0s`

### Commandes Disponibles

#### 🔐 Authentification
```bash
/login <username> <password>     # Se connecter avec un compte existant
/logout                          # Se déconnecter
/register <username> <password> [email]  # Créer un nouveau compte
/whoami                          # Afficher l'utilisateur actuel et ses informations
```

#### 🎨 Thèmes et Interface
```bash
/theme <nom>                     # Changer le thème (default, dark, light, neon, monochrome)
/themes                          # Lister tous les thèmes disponibles
/clear                           # Nettoyer l'écran
```

#### 📁 Gestion de Fichiers
```bash
/send <chemin>                   # Envoyer un fichier vers le serveur
/files                           # Lister les fichiers sur le serveur
/download <nom> [dir]           # Télécharger un fichier depuis le serveur
/local [dir]                     # Lister les fichiers locaux
```

#### 💻 Exécution de Code
```bash
/run <lang> <fichier> [args..]   # Compiler/Exécuter code côté serveur
```

 

#### 🆘 Aide
```bash
/help                            # Afficher l'aide complète
/quit                            # Quitter l'application
```

### Messagerie
- Tapez un message sans `/` pour l'envoyer à tous les clients connectés.
- Les messages que vous envoyez sont préfixés par `[you]` côté client.
- Messages privés: `/msg <user> <message>`
- Lister les utilisateurs connectés: `/users`

### 🎯 Exemples d'Utilisation

#### 1. Changement de Thème
```
V-Send: /theme dark
[SUCCESS] Thème changé vers: dark
```

#### 2. Upload avec Progression
```
V-Send: /send document.pdf
[INFO] Envoi du fichier: document.pdf
Envoi de document.pdf: [████████████████████████████████████████] 100.0% (2.5MB/2.5MB) 1.2MB/s ETA: 0s
[SUCCESS] Fichier envoyé avec succès: document.pdf
```

#### 3. Download avec Progression
```
V-Send: /download image.jpg
[INFO] Téléchargement de: image.jpg
Téléchargement de image.jpg: [████████████████████████████████████████] 100.0% (1.8MB/1.8MB) 800KB/s ETA: 0s
[SUCCESS] Fichier téléchargé: /path/to/image.jpg
```

### 🔧 Configuration

#### Fichier de Configuration des Thèmes
```
.config/theme_config.json
```

Structure :
```json
{
  "current_theme": "dark",
  "custom_themes": {
    "mon_theme_personnalise": {
      "primary": "\\x1b[36m",
      "secondary": "\\x1b[34m",
      "success": "\\x1b[32m",
      "warning": "\\x1b[33m",
      "error": "\\x1b[31m",
      "info": "\\x1b[34m",
      "text_primary": "\\x1b[37m",
      "text_secondary": "\\x1b[90m",
      "text_muted": "\\x1b[90m",
      "bot": "\\x1b[35m",
      "user": "\\x1b[32m",
      "server": "\\x1b[34m",
      "timestamp": "\\x1b[90m"
    }
  }
}
```

### 🐛 Dépannage

#### Problèmes de Thèmes
- Vérifiez que le nom du thème est correct avec `/themes`
- Redémarrez l'application si nécessaire
- Vérifiez les permissions du fichier de configuration

#### Problèmes de Barres de Progression
- Assurez-vous que votre terminal supporte les caractères Unicode
- Vérifiez que la taille du fichier est correctement détectée
- Redémarrez l'application

### 📚 Documentation Complète

Pour plus de détails sur les thèmes et barres de progression :
- [Guide des Thèmes et Barres de Progression](THEMES_AND_PROGRESS.md)

### 🚀 Futures Améliorations

- Thèmes dynamiques (changement automatique selon l'heure)
- Thèmes saisonniers
- Barres de progression avancées
- Interface graphique pour l'édition de thèmes
- Partage de thèmes entre utilisateurs


