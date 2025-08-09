# Changelog

## [2.2.0] - 2025-08-08

### 🔐 Authentification Intégrée
- **Système d'authentification complet** en ligne de commande
- **Commandes d'authentification** : `/login`, `/logout`, `/register`, `/whoami`
- **Gestion des utilisateurs** avec JWT et hash sécurisé
- **Persistance des données** dans `.config/users.json` et `.config/tokens.json`
- **Utilisateur par défaut** : `admin/admin` créé automatiquement
- **Permissions par utilisateur** (admin, user)

### 🎯 Améliorations Techniques
- **Intégration complète** de l'authentification dans l'interface CLI
- **Gestion des erreurs** améliorée pour l'authentification
- **Affichage de l'état** de connexion au démarrage
- **Documentation mise à jour** avec les nouvelles commandes

### 📝 Documentation
- **README mis à jour** avec les commandes d'authentification
- **Scripts de test** : `test_auth.py` et `demo_auth.py`
- **Exemples d'utilisation** pour l'authentification

### 🔧 Corrections
- **Correction de la classe User** pour compatibilité dataclass
- **Ajout de PyJWT** dans requirements.txt
- **Gestion des valeurs par défaut** dans les dataclasses

## [2.1.0] - 2024-12-19

### 🌟 Nouvelles Fonctionnalités

#### 🎨 Système de Thèmes Complet
- **5 thèmes prédéfinis** : Default, Dark, Light, Neon, Monochrome
- **Personnalisation complète** : Couleurs pour tous les éléments de l'interface
- **Persistance automatique** : Sauvegarde des préférences dans `.config/theme_config.json`
- **Commandes intégrées** : `/theme <nom>` et `/themes`
- **Thèmes personnalisables** : Possibilité de créer des thèmes personnalisés
- **Compatibilité** : Support de tous les terminaux (fallback monochrome)

#### 📊 Barres de Progression Avancées
- **Upload/Download** : Progression en temps réel pour tous les transferts de fichiers
- **Informations détaillées** : Vitesse de transfert, ETA, pourcentage, taille
- **Interface visuelle** : Barres avec caractères Unicode (█ et ░)
- **Couleurs adaptatives** : S'adapte automatiquement au thème actuel
- **Performance** : Mise à jour fluide sans impact sur les performances

### 🔧 Améliorations Techniques

#### Architecture
- **Module de thèmes** : `client/theme_manager.py` - Gestion complète des thèmes
- **Module de progression** : `client/progress_bar.py` - Barres de progression asynchrones
- **Intégration** : Mise à jour de `chat_handler.py` pour utiliser les nouveaux modules
- **Compatibilité** : Maintien de la compatibilité avec l'existant

#### Interface Utilisateur
- **Couleurs dynamiques** : Tous les éléments s'adaptent au thème
- **Banner personnalisable** : Couleurs adaptées au thème
- **Messages colorés** : Timestamps, succès, erreurs, warnings avec couleurs du thème
- **Prompt adaptatif** : Couleurs du prompt selon le thème

### 📁 Nouveaux Fichiers

- `client/theme_manager.py` - Gestionnaire de thèmes
- `client/progress_bar.py` - Barres de progression
- `THEMES_AND_PROGRESS.md` - Documentation complète
- `test_theme_progress.py` - Tests des nouvelles fonctionnalités
- `test_simple.py` - Tests simplifiés
- `CHANGELOG.md` - Ce fichier

### 🎯 Commandes Ajoutées

- `/theme <nom>` - Changer le thème
- `/themes` - Lister les thèmes disponibles

### 🔄 Modifications

#### Fichiers Modifiés
- `client/chat_handler.py` - Intégration des thèmes et barres de progression
- `client/file_sender.py` - Ajout des barres de progression pour l'upload
- `client/file_receiver.py` - Ajout des barres de progression pour le download
- `README.md` - Documentation mise à jour

### 🐛 Corrections

- **Imports relatifs** : Correction des imports dans les modules
- **Compatibilité** : Support de tous les terminaux
- **Gestion d'erreurs** : Meilleure gestion des erreurs de thèmes

### 📚 Documentation

- **Guide complet** : `THEMES_AND_PROGRESS.md` avec exemples détaillés
- **README mis à jour** : Nouvelles fonctionnalités documentées
- **Exemples** : Exemples d'utilisation pour chaque fonctionnalité

### 🧪 Tests

- **Tests unitaires** : `test_simple.py` pour les fonctionnalités de base
- **Tests complets** : `test_theme_progress.py` pour tous les aspects
- **Validation** : Tests de compatibilité et de performance

### 🚀 Performance

- **Thèmes** : Chargement rapide et mise en cache
- **Barres de progression** : Mise à jour fluide sans impact
- **Mémoire** : Gestion optimisée des ressources

### 🔮 Futures Améliorations

- **Thèmes dynamiques** : Changement automatique selon l'heure
- **Thèmes saisonniers** : Couleurs adaptées aux saisons
- **Interface graphique** : Éditeur de thèmes visuel
- **Partage de thèmes** : Système de partage entre utilisateurs
- **Barres de progression avancées** : Plus d'options de personnalisation

---

## [2.0.0] - 2024-12-18

### 🌟 Fonctionnalités Majeures
- Chat temps réel via WebSocket
- Upload/download de fichiers
- Exécution de code côté serveur
- Chatbot interactif avec IA avancée

### 🔧 Améliorations
- Interface utilisateur améliorée
- Gestion d'erreurs robuste
- Documentation complète

---

## [1.0.0] - 2024-12-17

### 🎉 Version Initiale
- Application de chat de base
- Support WebSocket
- Upload de fichiers simple
