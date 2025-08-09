# 🎨 Thèmes et Barres de Progression - Guide Utilisateur

## 🌈 Système de Thèmes

### Vue d'Ensemble

L'application dispose maintenant d'un système de thèmes complet permettant de personnaliser l'apparence de l'interface. Les thèmes incluent des couleurs pour tous les éléments de l'interface.

### Thèmes Disponibles

#### 1. **Default** (Par défaut)
- Couleurs classiques cyan/bleu
- Interface claire et professionnelle
- Idéal pour un usage quotidien

#### 2. **Dark** (Sombre)
- Thème sombre avec des couleurs vives
- Réduit la fatigue oculaire
- Parfait pour les environnements peu éclairés

#### 3. **Light** (Clair)
- Interface claire avec des couleurs douces
- Texte noir sur fond clair
- Excellente lisibilité

#### 4. **Neon** (Néon)
- Couleurs vives et flashy
- Style cyberpunk/futuriste
- Pour les utilisateurs qui aiment les couleurs vives

#### 5. **Monochrome** (Monochrome)
- Interface en noir et blanc
- Style minimaliste
- Compatible avec tous les terminaux

### Commandes de Thèmes

#### Changer de Thème
```bash
/theme <nom_du_thème>
```

Exemples :
```bash
/theme dark          # Passer au thème sombre
/theme light         # Passer au thème clair
/theme neon          # Passer au thème néon
/theme monochrome    # Passer au thème monochrome
/theme default       # Revenir au thème par défaut
```

#### Lister les Thèmes Disponibles
```bash
/themes
```

Cette commande affiche :
- Le thème actuel (marqué avec *)
- Tous les thèmes disponibles

### Personnalisation Avancée

#### Créer un Thème Personnalisé
```python
# Exemple de création d'un thème personnalisé
from client.theme_manager import theme_manager

custom_colors = {
    "primary": Fore.RED,
    "secondary": Fore.GREEN,
    "success": Fore.BLUE,
    "warning": Fore.YELLOW,
    "error": Fore.MAGENTA,
    "info": Fore.CYAN,
    "text_primary": Fore.WHITE,
    "text_secondary": Fore.LIGHTWHITE_EX,
    "text_muted": Fore.LIGHTBLACK_EX,
    "bot": Fore.RED,
    "user": Fore.GREEN,
    "server": Fore.BLUE,
    "timestamp": Fore.LIGHTBLACK_EX
}

theme_manager.create_custom_theme("mon_theme", custom_colors)
```

## 📊 Barres de Progression

### Vue d'Ensemble

Les barres de progression offrent un retour visuel en temps réel lors des opérations de transfert de fichiers (upload/download).

### Fonctionnalités

#### 1. **Affichage en Temps Réel**
- Pourcentage de progression
- Vitesse de transfert (B/s, KB/s, MB/s)
- Temps restant estimé (ETA)
- Taille transférée / Taille totale

#### 2. **Interface Visuelle**
- Barre de progression avec caractères Unicode
- Couleurs adaptées au thème actuel
- Mise à jour fluide

#### 3. **Informations Détaillées**
```
Envoi de fichier.txt: [████████████████████░░░░░░░░░░] 60.0% (1.2MB/2.0MB) 500KB/s ETA: 1.6s
```

### Utilisation

#### Upload avec Progression
```bash
/send mon_fichier.txt
```

L'application affiche automatiquement :
- Nom du fichier
- Barre de progression
- Pourcentage
- Vitesse de transfert
- Temps restant

#### Download avec Progression
```bash
/download fichier_serveur.txt
```

Même affichage que pour l'upload, mais pour le téléchargement.

### Exemples d'Affichage

#### Upload en Cours
```
[INFO] Envoi du fichier: document.pdf
Envoi de document.pdf: [████████████████████████████████████████] 100.0% (2.5MB/2.5MB) 1.2MB/s ETA: 0s
[SUCCESS] Fichier envoyé avec succès: document.pdf
```

#### Download en Cours
```
[INFO] Téléchargement de: image.jpg
Téléchargement de image.jpg: [████████████████████████████████████████] 100.0% (1.8MB/1.8MB) 800KB/s ETA: 0s
[SUCCESS] Fichier téléchargé: /path/to/image.jpg
```

## 🔧 Configuration

### Fichier de Configuration

Les thèmes sont sauvegardés dans :
```
.config/theme_config.json
```

Structure du fichier :
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

### Variables d'Environnement

Aucune variable d'environnement spécifique n'est requise pour ces fonctionnalités.

## 🎯 Bonnes Pratiques

### Choix de Thème

1. **Environnement de travail** : Utilisez le thème "dark" pour réduire la fatigue oculaire
2. **Présentation** : Le thème "light" est idéal pour les démonstrations
3. **Accessibilité** : Le thème "monochrome" est compatible avec tous les terminaux
4. **Style personnel** : Créez votre propre thème avec `/theme create`

### Utilisation des Barres de Progression

1. **Fichiers volumineux** : Les barres de progression sont particulièrement utiles pour les gros fichiers
2. **Monitoring** : Surveillez la vitesse de transfert pour détecter les problèmes réseau
3. **Planification** : Utilisez l'ETA pour planifier vos activités

## 🐛 Dépannage

### Problèmes Courants

#### Thème ne s'applique pas
- Vérifiez que le nom du thème est correct avec `/themes`
- Redémarrez l'application si nécessaire
- Vérifiez les permissions du fichier de configuration

#### Barre de progression ne s'affiche pas
- Assurez-vous que votre terminal supporte les caractères Unicode
- Vérifiez que la taille du fichier est correctement détectée
- Redémarrez l'application

#### Couleurs incorrectes
- Vérifiez que votre terminal supporte les couleurs ANSI
- Testez avec le thème "monochrome" pour la compatibilité
- Mettez à jour votre terminal si nécessaire

### Support

Pour toute question ou problème :
1. Consultez ce guide
2. Testez avec `/themes` et `/theme default`
3. Vérifiez la compatibilité de votre terminal
4. Contactez le support technique

## 🚀 Futures Améliorations

### Fonctionnalités Prévues

1. **Thèmes dynamiques** : Changement automatique selon l'heure
2. **Thèmes saisonniers** : Couleurs adaptées aux saisons
3. **Barres de progression avancées** : Plus d'options de personnalisation
4. **Thèmes communautaires** : Partage de thèmes entre utilisateurs
5. **Interface graphique** : Éditeur de thèmes visuel

### Contribution

Les contributions sont les bienvenues ! Vous pouvez :
- Créer de nouveaux thèmes
- Améliorer les barres de progression
- Ajouter de nouvelles fonctionnalités
- Corriger des bugs

---

*Dernière mise à jour : Décembre 2024*
