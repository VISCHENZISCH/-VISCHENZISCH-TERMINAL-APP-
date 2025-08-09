#!/usr/bin/env python3
"""
Interface graphique pour l'application de chat terminal.
Utilise tkinter pour créer une interface moderne et intuitive.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import asyncio
import threading
import json
from pathlib import Path
from typing import Optional, Dict, Any
import websockets
import httpx

from .theme_manager import theme_manager, get_color
from .auth_manager import auth_manager, login_user, logout_user, get_current_user

class ChatTerminalGUI:
    """Interface graphique principale pour l'application de chat terminal."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Chat Terminal App - GUI")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Variables
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.http_base_url = "http://127.0.0.1:8000"
        self.websocket_url = "ws://127.0.0.1:8000/ws"
        self.is_connected = False
        # Chatbot removed
        
        # Configuration du thème
        self.setup_theme()
        
        # Interface utilisateur
        self.setup_ui()
        
        # Événements
        self.setup_events()
        
        # Connexion automatique
        self.connect_to_server()
    
    def setup_theme(self):
        """Configure le thème de l'interface."""
        style = ttk.Style()
        
        # Thème sombre par défaut
        self.root.configure(bg='#2b2b2b')
        style.theme_use('clam')
        
        # Configuration des couleurs
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='#ffffff')
        style.configure('TButton', background='#404040', foreground='#ffffff')
        style.configure('TEntry', fieldbackground='#404040', foreground='#ffffff')
        style.configure('TText', background='#404040', foreground='#ffffff')
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Barre d'outils
        self.setup_toolbar(main_frame)
        
        # Frame principal divisé
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Panel gauche (chat et commandes)
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=2)
        
        # Panel droit (fichiers et infos)
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=1)
        
        # Configuration des panels
        self.setup_left_panel(left_frame)
        self.setup_right_panel(right_frame)
    
    def setup_toolbar(self, parent):
        """Configure la barre d'outils."""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # Boutons de connexion
        self.connect_btn = ttk.Button(toolbar, text="Connecter", command=self.connect_to_server)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.disconnect_btn = ttk.Button(toolbar, text="Déconnecter", command=self.disconnect_from_server)
        self.disconnect_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Statut de connexion
        self.status_label = ttk.Label(toolbar, text="Déconnecté")
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Séparateur
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Thèmes
        ttk.Label(toolbar, text="Thème:").pack(side=tk.LEFT, padx=(0, 5))
        self.theme_var = tk.StringVar(value="dark")
        theme_combo = ttk.Combobox(toolbar, textvariable=self.theme_var, 
                                 values=["default", "dark", "light", "neon", "monochrome"],
                                 state="readonly", width=10)
        theme_combo.pack(side=tk.LEFT, padx=(0, 5))
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        
        # Utilisateur
        self.user_label = ttk.Label(toolbar, text="Non connecté")
        self.user_label.pack(side=tk.RIGHT)
    
    def setup_left_panel(self, parent):
        """Configure le panel gauche (chat et commandes)."""
        # Zone de chat
        chat_frame = ttk.LabelFrame(parent, text="Chat")
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Zone de messages
        self.chat_text = scrolledtext.ScrolledText(chat_frame, height=20, wrap=tk.WORD)
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_text.config(state=tk.DISABLED)
        
        # Zone de saisie
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind('<Return>', self.send_message)
        
        self.send_btn = ttk.Button(input_frame, text="Envoyer", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT)
        
        # Commandes rapides
        commands_frame = ttk.LabelFrame(parent, text="Commandes Rapides")
        commands_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Boutons de commandes
        cmd_buttons = [
            ("Aide", "/help"),
            ("Fichiers", "/files"),
            # Chatbot button removed
            ("Thèmes", "/themes"),
            ("Clear", "/clear")
        ]
        
        for i, (text, cmd) in enumerate(cmd_buttons):
            btn = ttk.Button(commands_frame, text=text, 
                           command=lambda c=cmd: self.execute_command(c))
            btn.grid(row=0, column=i, padx=5, pady=5, sticky='ew')
        
        commands_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)
    
    def setup_right_panel(self, parent):
        """Configure le panel droit (fichiers et infos)."""
        # Notebook pour les onglets
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglet Fichiers
        files_frame = ttk.Frame(notebook)
        notebook.add(files_frame, text="Fichiers")
        self.setup_files_tab(files_frame)
        
        # Onglet Utilisateurs
        users_frame = ttk.Frame(notebook)
        notebook.add(users_frame, text="Utilisateurs")
        self.setup_users_tab(users_frame)
        
        # Onglet Paramètres
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Paramètres")
        self.setup_settings_tab(settings_frame)
    
    def setup_files_tab(self, parent):
        """Configure l'onglet fichiers."""
        # Boutons d'action
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(actions_frame, text="Upload", command=self.upload_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_frame, text="Download", command=self.download_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_frame, text="Rafraîchir", command=self.refresh_files).pack(side=tk.LEFT)
        
        # Liste des fichiers
        files_frame = ttk.Frame(parent)
        files_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Treeview pour les fichiers
        columns = ('Nom', 'Taille', 'Date')
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show='headings')
        
        for col in columns:
            self.files_tree.heading(col, text=col)
            self.files_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_users_tab(self, parent):
        """Configure l'onglet utilisateurs."""
        # Informations utilisateur actuel
        current_user_frame = ttk.LabelFrame(parent, text="Utilisateur Actuel")
        current_user_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.current_user_info = ttk.Label(current_user_frame, text="Non connecté")
        self.current_user_info.pack(padx=5, pady=5)
        
        # Actions utilisateur
        user_actions_frame = ttk.Frame(parent)
        user_actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(user_actions_frame, text="Se connecter", command=self.show_login_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(user_actions_frame, text="Se déconnecter", command=self.logout_user).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(user_actions_frame, text="S'inscrire", command=self.show_register_dialog).pack(side=tk.LEFT)
    
    def setup_settings_tab(self, parent):
        """Configure l'onglet paramètres."""
        # Paramètres de connexion
        connection_frame = ttk.LabelFrame(parent, text="Connexion")
        connection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(connection_frame, text="URL HTTP:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.http_url_entry = ttk.Entry(connection_frame)
        self.http_url_entry.insert(0, self.http_base_url)
        self.http_url_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        ttk.Label(connection_frame, text="URL WebSocket:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.ws_url_entry = ttk.Entry(connection_frame)
        self.ws_url_entry.insert(0, self.websocket_url)
        self.ws_url_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        connection_frame.columnconfigure(1, weight=1)
        
        # Paramètres d'interface
        interface_frame = ttk.LabelFrame(parent, text="Interface")
        interface_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(interface_frame, text="Thème:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.settings_theme_var = tk.StringVar(value="dark")
        settings_theme_combo = ttk.Combobox(interface_frame, textvariable=self.settings_theme_var,
                                          values=["default", "dark", "light", "neon", "monochrome"],
                                          state="readonly")
        settings_theme_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        settings_theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        
        interface_frame.columnconfigure(1, weight=1)
    
    def setup_events(self):
        """Configure les événements."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def connect_to_server(self):
        """Se connecte au serveur."""
        try:
            # Mise à jour des URLs
            self.http_base_url = self.http_url_entry.get()
            self.websocket_url = self.ws_url_entry.get()
            
            # Connexion WebSocket (simulation)
            self.is_connected = True
            self.status_label.config(text="Connecté")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            
            self.add_message("Système", "Connecté au serveur", "info")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de se connecter: {e}")
    
    def disconnect_from_server(self):
        """Se déconnecte du serveur."""
        self.is_connected = False
        self.status_label.config(text="Déconnecté")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.add_message("Système", "Déconnecté du serveur", "info")
    
    def send_message(self, event=None):
        """Envoie un message."""
        message = self.input_entry.get().strip()
        if not message:
            return
        
        self.input_entry.delete(0, tk.END)
        
        if message.startswith('/'):
            self.execute_command(message)
        else:
            self.add_message("Vous", message, "user")
            # Ici, on enverrait le message au serveur
    
    def execute_command(self, command):
        """Exécute une commande."""
        self.add_message("Commande", command, "system")
        
        if command == "/help":
            self.show_help()
        elif command == "/files":
            self.refresh_files()
        # Chatbot command removed
        elif command == "/themes":
            self.show_themes()
        elif command == "/clear":
            self.clear_chat()
    
    def add_message(self, sender: str, message: str, msg_type: str = "normal"):
        """Ajoute un message à la zone de chat."""
        self.chat_text.config(state=tk.NORMAL)
        
        # Couleurs selon le type de message
        colors = {
            "normal": "#ffffff",
            "user": "#00ff00",
            "system": "#ffff00",
            "error": "#ff0000",
            "info": "#00ffff"
        }
        
        color = colors.get(msg_type, "#ffffff")
        
        # Timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format du message
        formatted_message = f"[{timestamp}] {sender}: {message}\n"
        
        self.chat_text.insert(tk.END, formatted_message)
        self.chat_text.tag_add(msg_type, f"end-2l", "end-1c")
        self.chat_text.tag_config(msg_type, foreground=color)
        
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)
    
    def show_help(self):
        """Affiche l'aide."""
        help_text = """
Commandes disponibles:
- /help : Afficher cette aide
- /send <chemin> : Envoyer un fichier
- /files : Lister les fichiers
- /download <nom> : Télécharger un fichier
- /theme <nom> : Changer le thème
- /clear : Nettoyer le chat
- /quit : Quitter
        """
        self.add_message("Aide", help_text, "info")
    
    def refresh_files(self):
        """Rafraîchit la liste des fichiers."""
        # Simulation - dans une vraie implémentation, on ferait un appel HTTP
        self.files_tree.delete(*self.files_tree.get_children())
        
        # Fichiers d'exemple
        sample_files = [
            ("document.pdf", "2.5 MB", "2024-12-19"),
            ("image.jpg", "1.8 MB", "2024-12-19"),
            ("script.py", "15 KB", "2024-12-19")
        ]
        
        for file_info in sample_files:
            self.files_tree.insert('', tk.END, values=file_info)
    
    def upload_file(self):
        """Ouvre le dialogue d'upload de fichier."""
        filename = filedialog.askopenfilename()
        if filename:
            self.add_message("Système", f"Upload de {filename}", "info")
    
    def download_file(self):
        """Télécharge le fichier sélectionné."""
        selection = self.files_tree.selection()
        if selection:
            item = self.files_tree.item(selection[0])
            filename = item['values'][0]
            self.add_message("Système", f"Download de {filename}", "info")
        else:
            messagebox.showwarning("Attention", "Veuillez sélectionner un fichier")
    
    # Chatbot toggling removed
    
    def show_themes(self):
        """Affiche les thèmes disponibles."""
        themes = theme_manager.list_themes()
        current_theme = theme_manager.current_theme
        themes_text = f"Thème actuel: {current_theme}\nThèmes disponibles: {', '.join(themes)}"
        self.add_message("Thèmes", themes_text, "info")
    
    def clear_chat(self):
        """Nettoie la zone de chat."""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete(1.0, tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def change_theme(self, event=None):
        """Change le thème."""
        theme_name = self.theme_var.get()
        if theme_manager.set_theme(theme_name):
            self.add_message("Système", f"Thème changé vers: {theme_name}", "info")
        else:
            messagebox.showerror("Erreur", f"Thème '{theme_name}' non trouvé")
    
    def show_login_dialog(self):
        """Affiche le dialogue de connexion."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Connexion")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Nom d'utilisateur:").pack(pady=5)
        username_entry = ttk.Entry(dialog)
        username_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Mot de passe:").pack(pady=5)
        password_entry = ttk.Entry(dialog, show="*")
        password_entry.pack(pady=5)
        
        def do_login():
            username = username_entry.get()
            password = password_entry.get()
            
            if login_user(username, password):
                self.update_user_info()
                dialog.destroy()
                messagebox.showinfo("Succès", "Connexion réussie")
            else:
                messagebox.showerror("Erreur", "Nom d'utilisateur ou mot de passe incorrect")
        
        ttk.Button(dialog, text="Se connecter", command=do_login).pack(pady=10)
    
    def show_register_dialog(self):
        """Affiche le dialogue d'inscription."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Inscription")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Nom d'utilisateur:").pack(pady=5)
        username_entry = ttk.Entry(dialog)
        username_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Mot de passe:").pack(pady=5)
        password_entry = ttk.Entry(dialog, show="*")
        password_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Email (optionnel):").pack(pady=5)
        email_entry = ttk.Entry(dialog)
        email_entry.pack(pady=5)
        
        def do_register():
            username = username_entry.get()
            password = password_entry.get()
            email = email_entry.get() if email_entry.get() else None
            
            if auth_manager.register(username, password, email):
                dialog.destroy()
                messagebox.showinfo("Succès", "Inscription réussie")
            else:
                messagebox.showerror("Erreur", "Nom d'utilisateur déjà utilisé")
        
        ttk.Button(dialog, text="S'inscrire", command=do_register).pack(pady=10)
    
    def logout_user(self):
        """Déconnecte l'utilisateur."""
        if logout_user():
            self.update_user_info()
            messagebox.showinfo("Succès", "Déconnexion réussie")
        else:
            messagebox.showerror("Erreur", "Aucun utilisateur connecté")
    
    def update_user_info(self):
        """Met à jour les informations utilisateur."""
        user = get_current_user()
        if user:
            self.user_label.config(text=f"Connecté: {user.username}")
            self.current_user_info.config(text=f"Utilisateur: {user.username}\nPermissions: {', '.join(user.permissions)}")
        else:
            self.user_label.config(text="Non connecté")
            self.current_user_info.config(text="Non connecté")
    
    def on_closing(self):
        """Gère la fermeture de l'application."""
        if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter?"):
            self.disconnect_from_server()
            self.root.destroy()

def launch_gui():
    """Lance l'interface graphique."""
    root = tk.Tk()
    app = ChatTerminalGUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
