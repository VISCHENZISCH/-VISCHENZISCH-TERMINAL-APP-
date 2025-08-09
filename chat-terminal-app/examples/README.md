# Exemples de fichiers pour Chat Terminal App

Ce dossier contient des fichiers d'exemple pour tester les fonctionnalités d'upload et d'exécution de code.

## 📁 Fichiers disponibles

### 🖥️ Code source
- **`hello.c`** - Programme C simple (Hello World)
- **`hello.cpp`** - Programme C++ simple (Hello World)
- **`Program.cs`** - Programme C# simple (Hello World)

### 🐚 Scripts
- **`test.sh`** - Script Bash (Linux/macOS)
- **`test.ps1`** - Script PowerShell (Windows)

## 🚀 Comment utiliser

### Upload de fichiers
```bash
# Depuis le client, utilisez :
/send "examples/hello.c"
/send "examples/hello.cpp"
/send "examples/Program.cs"
/send "examples/test.sh"
/send "examples/test.ps1"
```

### Exécution de code
```bash
# Après upload, exécutez :
/run c hello.c
/run cpp hello.cpp
/run cs Program.cs
/run shell test.sh
/run powershell test.ps1
```

### Téléchargement
```bash
# Pour télécharger un fichier :
/download hello.c
/download hello.cpp
/download Program.cs
```

## 📝 Notes

- Les fichiers sont créés pour tester les fonctionnalités
- Assurez-vous que les compilateurs sont installés (gcc, g++, csc)
- Les scripts shell nécessitent les permissions d'exécution appropriées
