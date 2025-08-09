from __future__ import annotations

import asyncio
import os
from typing import Awaitable, Callable
import shutil
import re
from datetime import datetime

import httpx
import websockets
from colorama import init, Fore, Back, Style

from .file_sender import send_file
from .file_receiver import download_file
from .runner import run_code
from .theme_manager import theme_manager, get_color
from .progress_bar import create_async_progress_bar
from .auth_manager import auth_manager, login_user, logout_user, get_current_user, is_authenticated

# Initialize colorama for cross-platform colored output
init(autoreset=True)

CommandHandler = Callable[[str], Awaitable[None]]


class UIState:
    """State for terminal UI: status line and grouping."""
    def __init__(self) -> None:
        self.connected: bool = False
        self.username: str | None = None
        self.http_url: str = ""
        self.ws_url: str = ""
        self.online_users: int = 0
        self.last_author: str | None = None
        self.last_minute: str | None = None  # YYYY-MM-DD HH:MM


ui_state = UIState()


def _term_width() -> int:
    try:
        return shutil.get_terminal_size(fallback=(100, 25)).columns
    except Exception:
        return 100


def _print_time_separator(now: datetime) -> None:
    # Safe, minimal separator for Windows terminals
    ts = now.strftime("%Y-%m-%d %H:%M")
    text_color = get_color("text_secondary")
    line_color = get_color("text_muted")
    print(f"{line_color}---- {text_color}{ts}{line_color} ----{Style.RESET_ALL}")


def _maybe_group(author: str) -> None:
    # Safe-mode: avoid layout side-effects in some terminals
    now = datetime.now()
    minute = now.strftime("%Y-%m-%d %H:%M")
    if ui_state.last_minute != minute:
        _print_time_separator(now)
        ui_state.last_minute = minute
        ui_state.last_author = None
    # Do not insert extra blank lines to keep prompt stable
    ui_state.last_author = author


def _format_left(text: str) -> str:
    return text


def _format_right(text: str) -> str:
    width = _term_width()
    if len(text) >= width:
        return text
    return " " * (width - len(text)) + text


def draw_status_line() -> None:
    """Draw a one-line status header."""
    bullet = "●"
    color = get_color("success") if ui_state.connected else get_color("error")
    user = ui_state.username or "(non connecté)"
    theme = theme_manager.current_theme
    info_color = get_color("text_secondary")
    primary = get_color("primary")
    text = (
        f"{color}{bullet}{Style.RESET_ALL} "
        f"{primary}{user}{Style.RESET_ALL}  "
        f"{info_color}Thème:{Style.RESET_ALL} {primary}{theme}{Style.RESET_ALL}  "
        f"{info_color}WS:{Style.RESET_ALL} {ui_state.ws_url}  "
        f"{info_color}HTTP:{Style.RESET_ALL} {ui_state.http_url}  "
        f"{info_color}Online:{Style.RESET_ALL} {ui_state.online_users}"
    )
    print(text)
    # underline
    line = get_color("text_muted") + ("─" * _term_width()) + Style.RESET_ALL
    print(line)


def _prompt() -> str:
    # Plain prompt to avoid PSReadLine rendering issues
    return "V-Send: "

def print_banner():
    """Display a colorful banner when the client starts."""
    primary_color = get_color("primary")
    secondary_color = get_color("secondary")
    text_color = get_color("text_primary")
    
    banner = f"""
{primary_color}{'='*60}
{primary_color}|{primary_color}                    {secondary_color}VISCHENZISCH TERMINAL APP{primary_color}                    {primary_color}|
{primary_color}|{primary_color}                        {get_color("success")}Version 2.0 - by @vischenzisch{primary_color}                        {primary_color}|
{primary_color}{'='*60}
"""
    print(banner)


def print_colored(message: str, color: str = None, prefix: str = ""):
    """Print a colored message with optional prefix."""
    if color is None:
        color = get_color("text_primary")
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    timestamp_color = get_color("timestamp")
    
    if prefix:
        full_message = f"{timestamp_color}[{timestamp}] {color}{prefix} {message}{Style.RESET_ALL}"
    else:
        full_message = f"{timestamp_color}[{timestamp}] {color}{message}{Style.RESET_ALL}"
    
    print(full_message)


def print_success(message: str):
    """Print a success message in green."""
    print_colored(message, get_color("success"), "SUCCESS")


def print_error(message: str):
    """Print an error message in red."""
    print_colored(message, get_color("error"), "ERROR")


def print_info(message: str):
    """Print an info message in blue."""
    print_colored(message, get_color("info"), "INFO")


def print_warning(message: str):
    """Print a warning message in yellow."""
    print_colored(message, get_color("warning"), "WARNING")


## Bot printing removed (chatbot feature removed)


def print_user(message: str):
    """Print a user message with special styling."""
    _maybe_group("you")
    timestamp = datetime.now().strftime("%H:%M:%S")
    timestamp_color = get_color("timestamp")
    user_color = get_color("user")
    text_color = get_color("text_primary")
    user_label = f"{user_color}V-You:{Style.RESET_ALL}"
    content = f"{timestamp_color}[{timestamp}] {user_label} {text_color}{message}{Style.RESET_ALL}"
    # Safe-mode: no right alignment to avoid prompt overlap on Windows
    print(content)


def print_server(message: str):
    """Print a server message with special styling."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    timestamp_color = get_color("timestamp")
    server_color = get_color("server")
    text_color = get_color("text_primary")
    
    server_message = f"{timestamp_color}[{timestamp}] {server_color}Serveur: {text_color}{message}{Style.RESET_ALL}"
    print(server_message)


def print_peer(username: str, message: str):
    """Print a peer user message with special styling."""
    _maybe_group(username or "peer")
    timestamp = datetime.now().strftime("%H:%M:%S")
    timestamp_color = get_color("timestamp")
    user_color = get_color("user")
    text_color = get_color("text_primary")
    peer_message = f"{timestamp_color}[{timestamp}] {user_color}{username}: {text_color}{message}{Style.RESET_ALL}"
    print(_format_left(peer_message))

async def _print_files(http_base_url: str) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(http_base_url.rstrip("/") + "/files")
        response.raise_for_status()
        files = response.json().get("files", [])
        if not files:
            print_info("Aucun fichier côté serveur.")
        else:
            print_info(f"Fichiers côté serveur ({len(files)} fichiers):")
            primary_color = get_color("primary")
            text_color = get_color("text_primary")
            name_width = max((len(n) for n in files), default=10)
            header = f"{primary_color}{'Nom'.ljust(name_width)}  {text_color}Taille   Date"
            print(header)
            print(get_color('text_muted') + '─' * (name_width + 18) + Style.RESET_ALL)
            for name in files:
                # Taille/Date non disponibles via /files actuel; placeholders
                line = f"{text_color}{name.ljust(name_width)}  --      --"
                print(line)


async def _print_local_files(directory: str = ".") -> None:
    """List files in the local directory."""
    try:
        import os
        from pathlib import Path
        
        dir_path = Path(directory).expanduser().resolve()
        if not dir_path.exists():
            print_error(f"Le répertoire {directory} n'existe pas.")
            return
            
        files = [f for f in dir_path.iterdir() if f.is_file()]
        if not files:
            print_info(f"Aucun fichier dans le répertoire: {dir_path}")
        else:
            print_info(f"Fichiers locaux dans {dir_path} ({len(files)} fichiers):")
            primary_color = get_color("primary")
            text_color = get_color("text_primary")
            warning_color = get_color("warning")
            for i, file_path in enumerate(sorted(files), 1):
                file_size = file_path.stat().st_size
                file_line = f"{primary_color}  {i:2d}. {text_color}{file_path.name} {warning_color}({file_size} bytes)"
                print(file_line)
    except Exception as exc:
        print_error(f"Erreur lors de la lecture des fichiers locaux: {exc}")


async def chat_send_loop(websocket, http_base_url: str) -> None:
    """Reads user input, handles slash-commands, or sends text over WS."""
    primary_color = get_color("primary")
    secondary_color = get_color("secondary")
    success_color = get_color("success")
    text_color = get_color("text_primary")
    
    help_text = f"""
{primary_color}{'='*60}
{primary_color}|{primary_color}                        {secondary_color}COMMANDES DISPONIBLES{primary_color}                        {primary_color}|
{primary_color}{'='*60}
{primary_color}|{primary_color} {success_color}/help{primary_color}                   Afficher cette aide                        {primary_color}|
{primary_color}|{primary_color} {success_color}/login <user> <pass>{primary_color}     Se connecter                              {primary_color}|
{primary_color}|{primary_color} {success_color}/logout{primary_color}                  Se déconnecter                            {primary_color}|
{primary_color}|{primary_color} {success_color}/register <user> <pass> [email]{primary_color} Créer un compte                    {primary_color}|
{primary_color}|{primary_color} {success_color}/whoami{primary_color}                  Afficher l'utilisateur actuel            {primary_color}|
{primary_color}|{primary_color} {success_color}/users{primary_color}                   Lister les utilisateurs connectés         {primary_color}|
{primary_color}|{primary_color} {success_color}/msg <user> <message>{primary_color}    Envoyer un message privé                 {primary_color}|
{primary_color}|{primary_color} {success_color}/send <chemin>{primary_color}          Envoyer un fichier vers le serveur        {primary_color}|
{primary_color}|{primary_color} {success_color}/files{primary_color}                  Lister les fichiers sur le serveur        {primary_color}|
{primary_color}|{primary_color} {success_color}/download <nom> [dir]{primary_color}  Télécharger un fichier depuis le serveur  {primary_color}|
{primary_color}|{primary_color} {success_color}/local [dir]{primary_color}            Lister les fichiers locaux                {primary_color}|
{primary_color}|{primary_color} {success_color}/run <lang> <fichier> [args..]{primary_color}   Compiler/Exécuter code côté serveur {primary_color}|
{primary_color}|{primary_color} {success_color}/theme <nom>{primary_color}            Changer le thème                          {primary_color}|
{primary_color}|{primary_color} {success_color}/themes{primary_color}                 Lister les thèmes disponibles            {primary_color}|
{primary_color}|{primary_color} {success_color}/clear{primary_color}                  Nettoyer l'écran                          {primary_color}|
{primary_color}|{primary_color} {success_color}/quit{primary_color}                   Quitter                                   {primary_color}|
{primary_color}{'='*60}
"""
    print(help_text)
    
    # Print a simple prompt (safe for Windows/PSReadLine)
    prompt = _prompt()
    
    while True:
        try:
            # Reprint prompt before each input to keep it visible
            print(prompt, end="", flush=True)
            user_input = await asyncio.to_thread(input)
        except (EOFError, KeyboardInterrupt):
            break

        stripped = user_input.strip()
        if not stripped:
            continue

        if stripped.lower() in {"/quit", "/exit"}:
            print_success("Fermeture du client...")
            break

        if stripped.lower() == "/clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            print_banner()
            print(help_text)
            continue

        if stripped.lower() == "/help":
            print(help_text)
            continue

       

        if stripped.lower().startswith("/theme "):
            theme_name = stripped.split(" ", 1)[1].strip()
            if theme_manager.set_theme(theme_name):
                print_success(f"Thème changé vers: {theme_name}")
                # Re-afficher le banner avec le nouveau thème
                print_banner()
            else:
                print_error(f"Thème '{theme_name}' non trouvé. Utilisez /themes pour voir les thèmes disponibles.")
            continue

        if stripped.lower() == "/themes":
            themes = theme_manager.list_themes()
            current_theme = theme_manager.current_theme
            print_info(f"Thème actuel: {current_theme}")
            print_info("Thèmes disponibles:")
            primary_color = get_color("primary")
            text_color = get_color("text_primary")
            for theme in themes:
                if theme == current_theme:
                    print(f"{primary_color}  * {text_color}{theme} (actuel)")
                else:
                    print(f"{primary_color}    {text_color}{theme}")
            continue

        # Commandes d'authentification (traitement côté serveur)
        if stripped.lower().startswith("/login "):
            parts = stripped.split(" ", 2)
            if len(parts) < 3:
                print_error("Usage: /login <username> <password>")
                continue
            try:
                await websocket.send(stripped)
            except Exception as e:
                print_error(f"Erreur lors de l'envoi de la commande de connexion: {e}")
            continue

        if stripped.lower() == "/logout":
            try:
                await websocket.send("/logout")
                logout_user()
                print_success("Déconnexion réussie")
            except Exception as e:
                print_error(f"Erreur lors de la déconnexion: {e}")
            continue

        if stripped.lower().startswith("/register "):
            parts = stripped.split(" ", 2)
            if len(parts) < 3:
                print_error("Usage: /register <username> <password> [email]")
                continue
            try:
                await websocket.send(stripped)
                print_info("Demande de création de compte envoyée au serveur")
            except Exception as e:
                print_error(f"Erreur lors de l'envoi de la commande d'inscription: {e}")
            continue

        if stripped.lower() == "/whoami":
            try:
                user = get_current_user()
                if user:
                    print_info(f"Utilisateur actuel: {user.username}")
                    if user.email:
                        print_info(f"Email: {user.email}")
                    print_info(f"Permissions: {', '.join(user.permissions)}")
                    if user.last_login:
                        print_info(f"Dernière connexion: {user.last_login.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print_warning("Aucun utilisateur connecté")
            except Exception as e:
                print_error(f"Erreur lors de la récupération des informations: {e}")
            continue

        # Envoi de message (messagerie) quand ce n'est pas une commande
        if not stripped.startswith("/"):
            try:
                print_user(stripped)
                await websocket.send(stripped)
            except Exception as exc:  # noqa: BLE001
                print_error(f"Erreur d'envoi du message: {exc}")
            continue

        # Commandes serveur (envoyées au serveur)
        if stripped.lower().startswith("/send "):
            path = stripped.split(" ", 1)[1].strip().strip('"')
            try:
                print_info(f"Envoi du fichier: {path}")
                filename = await send_file_with_progress(http_base_url, path)
                print_success(f"Fichier envoyé avec succès: {filename}")
            except Exception as exc:  # noqa: BLE001
                print_error(f"Échec de l'envoi: {exc}")
            continue

        if stripped.lower() == "/files":
            try:
                await _print_files(http_base_url)
            except Exception as exc:  # noqa: BLE001
                print_error(f"Erreur lors de la lecture des fichiers: {exc}")
            continue

        if stripped.lower().startswith("/local"):
            args = stripped.split()
            directory = args[1] if len(args) >= 2 else "."
            try:
                await _print_local_files(directory)
            except Exception as exc:  # noqa: BLE001
                print_error(f"Erreur lors de la lecture des fichiers locaux: {exc}")
            continue

        if stripped.lower().startswith("/download "):
            args = stripped.split()
            if len(args) >= 2:
                filename = args[1]
                dest_dir = args[2] if len(args) >= 3 else "."
                try:
                    print_info(f"Téléchargement de: {filename}")
                    saved = await download_file_with_progress(http_base_url, filename, dest_dir)
                    print_success(f"Fichier téléchargé: {saved}")
                    
                    # Afficher les fichiers locaux après téléchargement
                    print_info("Fichiers locaux après téléchargement:")
                    await _print_local_files(dest_dir)
                    
                except Exception as exc:  # noqa: BLE001
                    print_error(f"Échec du téléchargement: {exc}")
            else:
                print_warning("Usage: /download <nom> [dir]")
            continue

        if stripped.lower().startswith("/run "):
            # /run <lang> <file> [args...]
            parts = stripped.split()
            if len(parts) >= 3:
                lang = parts[1]
                file_path = parts[2]
                run_args = parts[3:]
                try:
                    print_info(f"Exécution: {lang} - {file_path}")
                    result = await run_code(http_base_url, lang, file_path, run_args)
                    
                    # Color-coded output based on return code
                    if result['returncode'] == 0:
                        print_success(f"Exécution réussie (rc={result['returncode']})")
                    else:
                        print_warning(f"Exécution terminée avec code {result['returncode']}")
                    
                    if result['stdout']:
                        stdout_text = f"{get_color('success')}STDOUT:{Style.RESET_ALL}\n{result['stdout']}"
                        print(stdout_text)
                    if result['stderr']:
                        stderr_text = f"{get_color('error')}STDERR:{Style.RESET_ALL}\n{result['stderr']}"
                        print(stderr_text)
                        
                except Exception as exc:  # noqa: BLE001
                    print_error(f"Erreur d'exécution: {exc}")
            else:
                print_warning("Usage: /run <lang> <fichier> [args...]")
            continue

        # Autres commandes serveur (envoyées au serveur)
        if stripped.startswith("/"):
            
            try:
                await websocket.send(stripped)
            except Exception as exc:  # noqa: BLE001
                print_error(f"Erreur d'envoi de la commande: {exc}")
                continue

        # Sécurité (ne devrait pas arriver)
        print_error(f"Commande inconnue: '{stripped}'. Utilisez /help pour voir les commandes disponibles.")


async def send_file_with_progress(http_base_url: str, file_path: str) -> str:
    """Send a file with progress bar."""
    from pathlib import Path
    
    path = Path(file_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Fichier introuvable: {path}")
    
    file_size = path.stat().st_size
    progress_bar = create_async_progress_bar(file_size, f"Envoi de {path.name}")
    
    # la progression (dans un vrai cas, il faudrait intercepter les chunks)
    chunk_size = 8192
    sent_bytes = 0
    
    url = http_base_url.rstrip("/") + "/upload"
    async with httpx.AsyncClient(timeout=60) as client:
        with path.open("rb") as fp:
            files = {"file": (path.name, fp, "application/octet-stream")}
            response = await client.post(url, files=files)
            response.raise_for_status()
            
            # Marquer comme terminé
            await progress_bar.set_progress(file_size)
            await progress_bar.finish()
            
            return response.json().get("filename", path.name)


async def download_file_with_progress(http_base_url: str, filename: str, destination_dir: str) -> Path:
    """Download a file with progress bar."""
    from pathlib import Path
    
    destination_directory = Path(destination_dir).expanduser().resolve()
    destination_directory.mkdir(parents=True, exist_ok=True)
    
    url = http_base_url.rstrip("/") + f"/uploads/{filename}"
    destination_path = destination_directory / filename
    
    async with httpx.AsyncClient(timeout=60) as client:
        # D'abord, obtenir la taille du fichier
        head_response = await client.head(url)
        if head_response.status_code == 200:
            content_length = head_response.headers.get('content-length')
            total_size = int(content_length) if content_length else 0
        else:
            total_size = 0
        
        progress_bar = create_async_progress_bar(total_size, f"Téléchargement de {filename}")
        
        response = await client.get(url)
        response.raise_for_status()
        
        # Écrire le fichier
        destination_path.write_bytes(response.content)
        
        # Marquer comme terminé
        await progress_bar.set_progress(len(response.content))
        await progress_bar.finish()
        
        return destination_path


async def chat_receive_loop(websocket) -> None:
    try:
        async for message in websocket:
            if message.startswith("[ERROR]"):
                # Error message
                print_error(message[8:])  # Remove "[ERROR] " prefix
            elif message.startswith("[INFO]"):
                # Info message
                print_info(message[7:])  # Remove "[INFO] " prefix
            else:
                # Generic parser for tagged messages: [tag:name] text
                import re as _re
                m = _re.match(r"^\[(?P<tag>[^:\]]+):(?P<name>[^\]]+)\]\s?(?P<text>.*)$", message)
                if m:
                    tag = m.group("tag")
                    name = m.group("name")
                    text = m.group("text")
                    if tag == "you":
                        # already printed locally
                        continue
                    if tag == "peer":
                        print_peer(name, text)
                    elif tag == "pm":
                        print_peer(f"(privé) {name}", text)
                    elif tag == "pm-sent":
                        print_info(f"Message privé envoyé à {name}: {text}")
                    else:
                        if tag == "peer":
                            print_peer(name, text)
                        elif tag == "pm":
                            print_peer(f"(privé) {name}", text)
                        elif tag == "pm-sent":
                            print_info(f"Message privé envoyé à {name}: {text}")
                        else:
                            print_server(message)
                else:
                    # Regular server message
                    print_server(message)
    except websockets.ConnectionClosedOK:
        print_info("Connexion WebSocket fermée proprement")
    except websockets.ConnectionClosedError:
        print_error("Erreur de connexion WebSocket")
    except Exception as e:
        print_error(f"Erreur inattendue: {e}")


async def run_chat(websocket_url: str, http_base_url: str) -> None:
    print_banner()
    print_info(f"Connexion au serveur: {websocket_url}")
    print_info(f"Base URL HTTP: {http_base_url}")
    print_info(f"Thème actuel: {theme_manager.current_theme}")
    
    # Afficher l'état de l'authentification
    user = get_current_user()
    if user:
        print_success(f"Utilisateur connecté: {user.username}")
    else:
        print_info("Aucun utilisateur connecté. Utilisez /login pour vous connecter.")
    
    print()
    
    async with websockets.connect(
        websocket_url, ping_interval=20, ping_timeout=20
    ) as websocket:
        print_success("Connexion WebSocket établie!")
        print()
        
        sender_task = asyncio.create_task(chat_send_loop(websocket, http_base_url))
        receiver_task = asyncio.create_task(chat_receive_loop(websocket))
        done, pending = await asyncio.wait(
            {sender_task, receiver_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()


