from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from colorama import Fore, Back, Style

@dataclass
class ThemeColors:
    """Structure pour définir les couleurs d'un thème."""
    # Couleurs principales
    primary: str = Fore.CYAN
    secondary: str = Fore.BLUE
    success: str = Fore.GREEN
    warning: str = Fore.YELLOW
    error: str = Fore.RED
    info: str = Fore.BLUE
    
    # Couleurs de texte
    text_primary: str = Fore.WHITE
    text_secondary: str = Fore.LIGHTBLACK_EX
    text_muted: str = Fore.LIGHTBLACK_EX
    
    # Couleurs spéciales
    bot: str = Fore.MAGENTA
    user: str = Fore.GREEN
    server: str = Fore.BLUE
    timestamp: str = Fore.LIGHTBLACK_EX
    
    # Couleurs de fond (si supportées)
    background: str = ""
    background_secondary: str = ""

class ThemeManager:
    """Gestionnaire de thèmes pour l'application."""
    
    def __init__(self, config_dir: str = ".config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "theme_config.json"
        self.current_theme = "default"
        self.themes = self._load_default_themes()
        self._load_config()
    
    def _load_default_themes(self) -> Dict[str, ThemeColors]:
        """Charge les thèmes par défaut."""
        return {
            "default": ThemeColors(
                primary=Fore.CYAN,
                secondary=Fore.BLUE,
                success=Fore.GREEN,
                warning=Fore.YELLOW,
                error=Fore.RED,
                info=Fore.BLUE,
                text_primary=Fore.WHITE,
                text_secondary=Fore.LIGHTBLACK_EX,
                text_muted=Fore.LIGHTBLACK_EX,
                bot=Fore.MAGENTA,
                user=Fore.GREEN,
                server=Fore.BLUE,
                timestamp=Fore.LIGHTBLACK_EX
            ),
            "dark": ThemeColors(
                primary=Fore.CYAN,
                secondary=Fore.BLUE,
                success=Fore.GREEN,
                warning=Fore.YELLOW,
                error=Fore.RED,
                info=Fore.BLUE,
                text_primary=Fore.WHITE,
                text_secondary=Fore.LIGHTWHITE_EX,
                text_muted=Fore.LIGHTBLACK_EX,
                bot=Fore.MAGENTA,
                user=Fore.GREEN,
                server=Fore.BLUE,
                timestamp=Fore.LIGHTBLACK_EX
            ),
            "light": ThemeColors(
                primary=Fore.BLUE,
                secondary=Fore.CYAN,
                success=Fore.GREEN,
                warning=Fore.YELLOW,
                error=Fore.RED,
                info=Fore.BLUE,
                text_primary=Fore.BLACK,
                text_secondary=Fore.LIGHTBLACK_EX,
                text_muted=Fore.LIGHTBLACK_EX,
                bot=Fore.MAGENTA,
                user=Fore.GREEN,
                server=Fore.BLUE,
                timestamp=Fore.LIGHTBLACK_EX
            ),
            "neon": ThemeColors(
                primary=Fore.CYAN,
                secondary=Fore.MAGENTA,
                success=Fore.GREEN,
                warning=Fore.YELLOW,
                error=Fore.RED,
                info=Fore.BLUE,
                text_primary=Fore.WHITE,
                text_secondary=Fore.LIGHTWHITE_EX,
                text_muted=Fore.LIGHTBLACK_EX,
                bot=Fore.MAGENTA,
                user=Fore.GREEN,
                server=Fore.CYAN,
                timestamp=Fore.LIGHTBLACK_EX
            ),
            "monochrome": ThemeColors(
                primary=Fore.WHITE,
                secondary=Fore.LIGHTWHITE_EX,
                success=Fore.WHITE,
                warning=Fore.LIGHTWHITE_EX,
                error=Fore.WHITE,
                info=Fore.LIGHTWHITE_EX,
                text_primary=Fore.WHITE,
                text_secondary=Fore.LIGHTWHITE_EX,
                text_muted=Fore.LIGHTBLACK_EX,
                bot=Fore.WHITE,
                user=Fore.LIGHTWHITE_EX,
                server=Fore.WHITE,
                timestamp=Fore.LIGHTBLACK_EX
            )
        }
    
    def _load_config(self) -> None:
        """Charge la configuration depuis le fichier."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_theme = config.get('current_theme', 'default')
                    
                    # Charger les thèmes personnalisés
                    custom_themes = config.get('custom_themes', {})
                    for theme_name, theme_data in custom_themes.items():
                        self.themes[theme_name] = ThemeColors(**theme_data)
            except Exception as e:
                print(f"Erreur lors du chargement de la configuration: {e}")
    
    def _save_config(self) -> None:
        """Sauvegarde la configuration dans le fichier."""
        try:
            config = {
                'current_theme': self.current_theme,
                'custom_themes': {}
            }
            
            # Sauvegarder les thèmes personnalisés
            for theme_name, theme_colors in self.themes.items():
                if theme_name not in ['default', 'dark', 'light', 'neon', 'monochrome']:
                    config['custom_themes'][theme_name] = asdict(theme_colors)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
    
    def get_current_theme(self) -> ThemeColors:
        """Retourne le thème actuel."""
        return self.themes.get(self.current_theme, self.themes['default'])
    
    def set_theme(self, theme_name: str) -> bool:
        """Change le thème actuel."""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self._save_config()
            return True
        return False
    
    def list_themes(self) -> list[str]:
        """Liste tous les thèmes disponibles."""
        return list(self.themes.keys())
    
    def create_custom_theme(self, name: str, colors: Dict[str, str]) -> bool:
        """Crée un thème personnalisé."""
        try:
            self.themes[name] = ThemeColors(**colors)
            self._save_config()
            return True
        except Exception as e:
            print(f"Erreur lors de la création du thème: {e}")
            return False
    
    def delete_custom_theme(self, name: str) -> bool:
        """Supprime un thème personnalisé."""
        if name in ['default', 'dark', 'light', 'neon', 'monochrome']:
            return False  # Ne pas supprimer les thèmes par défaut
        
        if name in self.themes:
            del self.themes[name]
            if self.current_theme == name:
                self.current_theme = 'default'
            self._save_config()
            return True
        return False

# Instance globale du gestionnaire de thèmes
theme_manager = ThemeManager()

def get_color(color_name: str) -> str:
    """Récupère une couleur du thème actuel."""
    theme = theme_manager.get_current_theme()
    return getattr(theme, color_name, Fore.WHITE)

def print_theme_info() -> None:
    """Affiche les informations sur le thème actuel."""
    theme = theme_manager.get_current_theme()
    print(f"Thème actuel: {theme_manager.current_theme}")
    print(f"Couleurs disponibles: {', '.join(theme_manager.list_themes())}")
