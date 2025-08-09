from __future__ import annotations

import asyncio
import os
import sys
from typing import Optional, Callable
from datetime import datetime

from .theme_manager import get_color

class ProgressBar:
    """Barre de progression pour les uploads et downloads."""
    
    def __init__(self, total: int, description: str = "Progression", width: int = 50):
        self.total = total
        self.description = description
        self.width = width
        self.current = 0
        self.start_time = datetime.now()
        self.last_update = 0
        
    def update(self, amount: int = 1) -> None:
        """Met à jour la progression."""
        self.current += amount
        self._display()
    
    def set_progress(self, current: int) -> None:
        """Définit la progression actuelle."""
        self.current = min(current, self.total)
        self._display()
    
    def _display(self) -> None:
        """Affiche la barre de progression."""
        if self.total <= 0:
            return
        
        # Calculer le pourcentage
        percentage = (self.current / self.total) * 100
        
        # Calculer la largeur de la barre
        filled_width = int(self.width * self.current // self.total)
        bar = '█' * filled_width + '░' * (self.width - filled_width)
        
        # Calculer la vitesse
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed > 0:
            speed = self.current / elapsed
            eta = (self.total - self.current) / speed if speed > 0 else 0
        else:
            speed = 0
            eta = 0
        
        # Formater les tailles
        current_size = self._format_size(self.current)
        total_size = self._format_size(self.total)
        speed_str = self._format_size(speed) + "/s" if speed > 0 else "0 B/s"
        eta_str = self._format_time(eta) if eta > 0 else "∞"
        
        # Couleurs
        primary_color = get_color("primary")
        success_color = get_color("success")
        text_color = get_color("text_primary")
        
        # Afficher la barre
        progress_line = (
            f"\r{primary_color}{self.description}: "
            f"{text_color}[{success_color}{bar}{text_color}] "
            f"{primary_color}{percentage:5.1f}% "
            f"{text_color}({current_size}/{total_size}) "
            f"{primary_color}{speed_str} "
            f"{text_color}ETA: {eta_str}"
        )
        
        # Effacer la ligne et afficher
        sys.stdout.write('\033[K')  # Effacer la ligne
        sys.stdout.write(progress_line)
        sys.stdout.flush()
    
    def finish(self) -> None:
        """Termine la barre de progression."""
        self.current = self.total
        self._display()
        print()  # Nouvelle ligne
    
    def _format_size(self, size_bytes: float) -> str:
        """Formate une taille en bytes en format lisible."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _format_time(self, seconds: float) -> str:
        """Formate un temps en secondes en format lisible."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

class AsyncProgressBar:
    """Barre de progression asynchrone pour les opérations de fichiers."""
    
    def __init__(self, total: int, description: str = "Progression", width: int = 50):
        self.progress_bar = ProgressBar(total, description, width)
    
    async def update(self, amount: int = 1) -> None:
        """Met à jour la progression de manière asynchrone."""
        self.progress_bar.update(amount)
        await asyncio.sleep(0)  # Permettre à d'autres tâches de s'exécuter
    
    async def set_progress(self, current: int) -> None:
        """Définit la progression actuelle de manière asynchrone."""
        self.progress_bar.set_progress(current)
        await asyncio.sleep(0)
    
    async def finish(self) -> None:
        """Termine la barre de progression de manière asynchrone."""
        self.progress_bar.finish()

def create_progress_bar(total: int, description: str = "Progression", width: int = 50) -> ProgressBar:
    """Crée une nouvelle barre de progression."""
    return ProgressBar(total, description, width)

def create_async_progress_bar(total: int, description: str = "Progression", width: int = 50) -> AsyncProgressBar:
    """Crée une nouvelle barre de progression asynchrone."""
    return AsyncProgressBar(total, description, width)
