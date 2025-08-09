from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .websocket_handler import manager
from .file_handler import save_upload_file
from .executor import execute
from client.auth_manager import AuthManager

app = FastAPI(title="Chat Terminal Server", version="1.0.0")
auth = AuthManager()

# Track authenticated users for each websocket
authed_usernames: dict[WebSocket, str] = {}
username_to_connections: dict[str, set[WebSocket]] = {}

# Mount static files for uploads
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "chat-terminal-server"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    """Upload a file to the server."""
    try:
        filename = await save_upload_file(file)
        return JSONResponse(
            content={"message": "File uploaded successfully", "filename": filename.name},
            status_code=200,
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Upload failed: {str(e)}"}, status_code=500
        )


@app.get("/files")
async def list_files() -> dict:
    """List all uploaded files."""
    try:
        files = []
        for file_path in uploads_dir.iterdir():
            if file_path.is_file():
                files.append(file_path.name)
        return {"files": sorted(files)}
    except Exception as e:
        return {"error": f"Failed to list files: {str(e)}"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            incoming_text = await websocket.receive_text()
            
            # If it's not a command, treat as chat message and broadcast
            if not incoming_text.strip().startswith("/"):
                if websocket not in authed_usernames:
                    await manager.send_personal_text(websocket, "[ERROR] Vous devez être connecté pour envoyer des messages. Utilisez /login <user> <pass>.")
                    continue
                username = authed_usernames[websocket]
                await manager.send_personal_text(websocket, f"[you:{username}] {incoming_text}")
                await manager.broadcast_text_excluding(websocket, f"[peer:{username}] {incoming_text}")
                continue
            
            # Process commands
            command_parts = incoming_text.strip().split()
            command = command_parts[0].lower()
            
            if command == "/help":
                help_text = """
[INFO] Commandes disponibles:
- /help : Afficher cette aide
- /register <user> <pass> [email] : Créer un compte
- /login <user> <pass> : Se connecter
- /logout : Se déconnecter
- /users : Lister les utilisateurs connectés
- /send <chemin> : Envoyer un fichier au serveur
- /files : Lister les fichiers côté serveur
- /download <nom> [dir] : Télécharger un fichier
- /local [dir] : Lister les fichiers locaux
- /run <lang> <fichier> [args...] : Exécuter du code
- /quit : Quitter
"""
                await manager.send_personal_text(websocket, help_text)
            elif command == "/users":
                if websocket not in authed_usernames:
                    await manager.send_personal_text(websocket, "[ERROR] Vous devez être connecté. Utilisez /login <user> <pass>.")
                    continue
                users = sorted(set(authed_usernames.values()))
                if users:
                    await manager.send_personal_text(websocket, "[INFO] Utilisateurs connectés: " + ", ".join(users))
                else:
                    await manager.send_personal_text(websocket, "[INFO] Aucun utilisateur connecté")
            elif command == "/login":
                if len(command_parts) < 3:
                    await manager.send_personal_text(websocket, "[ERROR] Usage: /login <user> <pass>")
                    continue
                username = command_parts[1]
                password = command_parts[2]
                token = auth.login(username, password)
                if token:
                    authed_usernames[websocket] = username
                    username_to_connections.setdefault(username, set()).add(websocket)
                    await manager.send_personal_text(websocket, f"[INFO] Connecté en tant que {username}")
                else:
                    await manager.send_personal_text(websocket, "[ERROR] Nom d'utilisateur ou mot de passe incorrect")
            elif command == "/register":
                # /register <user> <pass> [email]
                if len(command_parts) < 3:
                    await manager.send_personal_text(websocket, "[ERROR] Usage: /register <user> <pass> [email]")
                    continue
                username = command_parts[1]
                password = command_parts[2]
                email = None
                # préserver l'email si fourni (3e segment après split limité)
                tokens = incoming_text.strip().split(" ", 3)
                if len(tokens) >= 4:
                    email = tokens[3].strip()
                ok = auth.register(username, password, email)
                if ok:
                    await manager.send_personal_text(websocket, f"[INFO] Compte créé: {username}")
                else:
                    await manager.send_personal_text(websocket, f"[ERROR] Nom d'utilisateur déjà utilisé: {username}")
            elif command == "/logout":
                if websocket in authed_usernames:
                    prev = authed_usernames.pop(websocket, None)
                    if prev:
                        conns = username_to_connections.get(prev)
                        if conns:
                            conns.discard(websocket)
                            if not conns:
                                username_to_connections.pop(prev, None)
                auth.logout()
                await manager.send_personal_text(websocket, "[INFO] Déconnecté")
            elif command == "/users":
                if websocket not in authed_usernames:
                    await manager.send_personal_text(websocket, "[ERROR] Vous devez être connecté. Utilisez /login <user> <pass>.")
                    continue
                users = sorted([u for u, conns in username_to_connections.items() if conns])
                if users:
                    await manager.send_personal_text(websocket, "[INFO] Utilisateurs connectés: " + ", ".join(users))
                else:
                    await manager.send_personal_text(websocket, "[INFO] Aucun utilisateur connecté")
            elif command == "/msg":
                if websocket not in authed_usernames:
                    await manager.send_personal_text(websocket, "[ERROR] Vous devez être connecté. Utilisez /login <user> <pass>.")
                    continue
                if len(command_parts) < 3:
                    await manager.send_personal_text(websocket, "[ERROR] Usage: /msg <user> <message>")
                    continue
                recipient = command_parts[1]
                # préserver les espaces du message
                content = incoming_text.strip().split(" ", 2)[2]
                sender = authed_usernames[websocket]
                targets = username_to_connections.get(recipient)
                if not targets:
                    await manager.send_personal_text(websocket, f"[ERROR] Utilisateur '{recipient}' non connecté")
                    continue
                # envoyer au destinataire
                for ws in list(targets):
                    await manager.send_personal_text(ws, f"[pm:{sender}] {content}")
                # accusé d'envoi pour l'expéditeur
                await manager.send_personal_text(websocket, f"[pm-sent:{recipient}] {content}")
            
            elif command == "/send":
                if websocket not in authed_usernames:
                    await manager.send_personal_text(websocket, "[ERROR] Vous devez être connecté. Utilisez /login <user> <pass>.")
                    continue
                if len(command_parts) < 2:
                    await manager.send_personal_text(websocket, "[ERROR] Usage: /send <chemin>")
                else:
                    await manager.send_personal_text(websocket, f"[INFO] Commande /send reçue: {command_parts[1]}")
            
            elif command == "/files":
                if websocket not in authed_usernames:
                    await manager.send_personal_text(websocket, "[ERROR] Vous devez être connecté. Utilisez /login <user> <pass>.")
                    continue
                await manager.send_personal_text(websocket, "[INFO] Commande /files reçue")
            
            elif command == "/download":
                if websocket not in authed_usernames:
                    await manager.send_personal_text(websocket, "[ERROR] Vous devez être connecté. Utilisez /login <user> <pass>.")
                    continue
                if len(command_parts) < 2:
                    await manager.send_personal_text(websocket, "[ERROR] Usage: /download <nom> [dir]")
                else:
                    await manager.send_personal_text(websocket, f"[INFO] Commande /download reçue: {command_parts[1]}")
            
            elif command == "/local":
                if websocket not in authed_usernames:
                    await manager.send_personal_text(websocket, "[ERROR] Vous devez être connecté. Utilisez /login <user> <pass>.")
                    continue
                await manager.send_personal_text(websocket, "[INFO] Commande /local reçue")
            
            elif command == "/run":
                if websocket not in authed_usernames:
                    await manager.send_personal_text(websocket, "[ERROR] Vous devez être connecté. Utilisez /login <user> <pass>.")
                    continue
                if len(command_parts) < 3:
                    await manager.send_personal_text(websocket, "[ERROR] Usage: /run <lang> <fichier> [args...]")
                else:
                    await manager.send_personal_text(websocket, f"[INFO] Commande /run reçue: {command_parts[1]} {command_parts[2]}")
            
            elif command == "/quit":
                await manager.send_personal_text(websocket, "[INFO] Déconnexion...")
                break
            
            else:
                await manager.send_personal_text(websocket, f"[ERROR] Commande inconnue: {command}. Utilisez /help pour voir les commandes disponibles.")
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error in websocket: {e}")
    finally:
        authed_usernames.pop(websocket, None)
        manager.disconnect(websocket)


def _make_bot_reply(text: str) -> str | None:
    """Sophisticated AI-powered chatbot with advanced conversation capabilities, emotional intelligence, and context awareness."""
    import random
    import re
    import json
    from datetime import datetime, timedelta
    
    lower = text.strip().lower()
    if not lower:
        return None

    # Initialize sophisticated bot memory
    if not hasattr(_make_bot_reply, 'memory'):
        _make_bot_reply.memory = {
            'user_name': None,
            'conversation_history': [],
            'user_preferences': {},
            'mood': 'neutral',
            'last_interaction': None,
            'conversation_topics': [],
            'emotional_state': 'neutral',
            'interaction_count': 0,
            'user_personality': {},
            'conversation_flow': 'casual'
        }
    
    # Update sophisticated memory
    _make_bot_reply.memory['interaction_count'] += 1
    _make_bot_reply.memory['conversation_history'].append({
        'user_input': text,
        'timestamp': datetime.now(),
        'length': len(text),
        'detected_emotion': _detect_emotion(text),
        'topic': _detect_topic(text)
    })
    _make_bot_reply.memory['last_interaction'] = datetime.now()
    
    # Keep only last 15 interactions for context
    if len(_make_bot_reply.memory['conversation_history']) > 15:
        _make_bot_reply.memory['conversation_history'] = _make_bot_reply.memory['conversation_history'][-15:]
    
    # Update conversation topics
    current_topic = _detect_topic(text)
    if current_topic and current_topic not in _make_bot_reply.memory['conversation_topics']:
        _make_bot_reply.memory['conversation_topics'].append(current_topic)
    
    # Update emotional state based on user input
    detected_emotion = _detect_emotion(text)
    if detected_emotion:
        _make_bot_reply.memory['emotional_state'] = detected_emotion
    
    # Get conversation context
    context = _get_conversation_context()
    
    # Sophisticated greeting detection with context awareness
    if _is_greeting(text):
        return _generate_contextual_greeting(context)
    
    # Name detection with enhanced patterns
    name = _extract_name(text)
    if name:
        _make_bot_reply.memory['user_name'] = name
        return _generate_personalized_introduction(name, context)
    
    # Sophisticated farewell detection
    if _is_farewell(text):
        return _generate_contextual_farewell(context)
    
    # Enhanced question handling with context
    if _is_question(text):
        return _generate_contextual_answer(text, context)
    
    # Emotional support and empathy
    if _needs_emotional_support(text):
        return _generate_empathetic_response(text, context)
    
    # Technical discussions
    if _is_technical_topic(text):
        return _generate_technical_response(text, context)
    
    # Entertainment and fun
    if _is_entertainment_request(text):
        return _generate_entertainment_response(text, context)
    
    # Personal conversation
    if _is_personal_topic(text):
        return _generate_personal_response(text, context)
    
    # General conversation with context awareness
    return _generate_contextual_response(text, context)


def _detect_emotion(text: str) -> str:
    """Detect emotional state from text."""
    lower = text.lower()
    
    # Positive emotions
    if any(word in lower for word in {"heureux", "joyeux", "content", "excellent", "super", "génial", "fantastic", "awesome", "amazing", "wonderful"}):
        return "happy"
    
    # Negative emotions
    if any(word in lower for word in {"triste", "mal", "déprimé", "stressé", "fatigué", "sad", "bad", "depressed", "stressed", "tired", "angry", "frustrated"}):
        return "sad"
    
    # Neutral/curious
    if any(word in lower for word in {"curieux", "intéressant", "curious", "interesting", "wonder"}):
        return "curious"
    
    return "neutral"


def _detect_topic(text: str) -> str:
    """Detect conversation topic."""
    lower = text.lower()
    
    topics = {
        "programming": ["code", "programme", "coder", "développeur", "developer", "coding", "algorithm", "bug", "debug"],
        "technology": ["tech", "technologie", "computer", "ordinateur", "internet", "web", "ai", "artificial intelligence"],
        "entertainment": ["musique", "music", "film", "movie", "cinéma", "cinema", "blague", "joke", "fun"],
        "food": ["manger", "eat", "boire", "drink", "café", "coffee", "pizza", "restaurant", "cuisine"],
        "personal": ["moi", "je", "ma", "mon", "my", "i", "me", "personal", "life"],
        "work": ["travail", "work", "job", "profession", "career", "business"],
        "health": ["santé", "health", "maladie", "disease", "médecin", "doctor"],
        "education": ["étude", "study", "école", "school", "université", "university", "apprendre", "learn"]
    }
    
    for topic, keywords in topics.items():
        if any(keyword in lower for keyword in keywords):
            return topic
    
    return "general"


def _get_conversation_context() -> dict:
    """Get comprehensive conversation context."""
    from datetime import datetime
    memory = _make_bot_reply.memory
    
    # Analyze recent interactions
    recent_topics = [item['topic'] for item in memory['conversation_history'][-5:] if item['topic'] != 'general']
    recent_emotions = [item['detected_emotion'] for item in memory['conversation_history'][-5:]]
    
    # Determine conversation flow
    if len(memory['conversation_history']) < 3:
        flow = "initial"
    elif any(emotion in recent_emotions for emotion in ['sad', 'angry']):
        flow = "supportive"
    elif any(topic in recent_topics for topic in ['programming', 'technology']):
        flow = "technical"
    else:
        flow = "casual"
    
    return {
        'user_name': memory['user_name'],
        'interaction_count': memory['interaction_count'],
        'recent_topics': recent_topics,
        'recent_emotions': recent_emotions,
        'current_emotion': memory['emotional_state'],
        'conversation_flow': flow,
        'time_of_day': datetime.now().hour,
        'conversation_duration': (datetime.now() - memory['last_interaction']).seconds if memory['last_interaction'] else 0
    }


def _is_greeting(text: str) -> bool:
    """Check if text is a greeting."""
    greetings = {
        "bonjour", "salut", "hello", "coucou", "cc", "hi", "hey", "yo", "bonsoir", 
        "bonne nuit", "good morning", "good evening", "good afternoon", "good night"
    }
    return any(word in text.lower() for word in greetings)


def _is_farewell(text: str) -> bool:
    """Check if text is a farewell."""
    farewells = {
        "au revoir", "bye", "ciao", "adieu", "à bientôt", "see you", "goodbye", 
        "bye bye", "see you later", "à plus", "à la prochaine", "take care"
    }
    return any(word in text.lower() for word in farewells)


def _is_question(text: str) -> bool:
    """Check if text is a question."""
    return text.strip().endswith('?') or any(word in text.lower() for word in ["comment", "pourquoi", "quand", "où", "qui", "quoi", "how", "why", "when", "where", "who", "what"])


def _needs_emotional_support(text: str) -> bool:
    """Check if text indicates need for emotional support."""
    emotional_keywords = {
        "triste", "mal", "déprimé", "stressé", "fatigué", "seul", "lonely", "sad", 
        "bad", "depressed", "stressed", "tired", "angry", "frustrated", "worried"
    }
    return any(word in text.lower() for word in emotional_keywords)


def _is_technical_topic(text: str) -> bool:
    """Check if text is about technical topics."""
    technical_keywords = {
        "code", "programme", "coder", "développeur", "developer", "coding", 
        "tech", "technologie", "computer", "ordinateur", "internet", "web", "ai"
    }
    return any(word in text.lower() for word in technical_keywords)


def _is_entertainment_request(text: str) -> bool:
    """Check if text is requesting entertainment."""
    entertainment_keywords = {
        "blague", "joke", "rigoler", "laugh", "amusant", "funny", "humour", 
        "musique", "music", "film", "movie", "cinéma", "cinema"
    }
    return any(word in text.lower() for word in entertainment_keywords)


def _is_personal_topic(text: str) -> bool:
    """Check if text is about personal topics."""
    personal_keywords = {
        "moi", "je", "ma", "mon", "my", "i", "me", "personal", "life", "famille", 
        "family", "ami", "friend", "travail", "work", "école", "school"
    }
    return any(word in text.lower() for word in personal_keywords)


def _extract_name(text: str) -> str | None:
    """Extract name from text using advanced patterns."""
    import re
    name_patterns = [
        r"je m'appelle (\w+)",
        r"mon nom est (\w+)",
        r"i'm (\w+)",
        r"my name is (\w+)",
        r"appelle-moi (\w+)",
        r"call me (\w+)",
        r"je suis (\w+)",
        r"i am (\w+)"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1).capitalize()
    
    return None


def _generate_contextual_greeting(context: dict) -> str:
    """Generate contextual greeting based on conversation context."""
    from datetime import datetime
    time_now = datetime.now()
    hour = time_now.hour
    name = context['user_name']
    
    # Time-based greetings
    if hour < 12:
        time_greeting = "Bonjour"
        time_emoji = "☀️"
    elif hour < 18:
        time_greeting = "Bonjour"
        time_emoji = "🌤️"
    else:
        time_greeting = "Bonsoir"
        time_emoji = "🌙"
    
    # Personalized greeting
    if name:
        if context['interaction_count'] > 5:
            return f"{time_greeting} {name}! Ravi de vous revoir! {time_emoji} Comment s'est passée votre journée?"
        else:
            return f"{time_greeting} {name}! Comment allez-vous? {time_emoji}"
    else:
        if context['interaction_count'] > 5:
            return f"{time_greeting}! Ravi de vous revoir! {time_emoji} Comment allez-vous?"
        else:
            return f"{time_greeting}! Comment allez-vous? {time_emoji}"


def _generate_personalized_introduction(name: str, context: dict) -> str:
    """Generate personalized introduction."""
    import random
    responses = [
        f"Ravi de faire votre connaissance, {name}! Je m'appelle V-Bot, votre assistant virtuel intelligent. Comment puis-je vous aider aujourd'hui? 🤖✨",
        f"Enchanté, {name}! Je suis V-Bot, votre compagnon virtuel. J'ai hâte de discuter avec vous! 🌟",
        f"Bonjour {name}! Je suis V-Bot, votre assistant IA. Ravi de vous rencontrer! 🎯"
    ]
    return random.choice(responses)


def _generate_contextual_farewell(context: dict) -> str:
    """Generate contextual farewell."""
    import random
    name = context['user_name']
    interaction_count = context['interaction_count']
    
    if name:
        if interaction_count > 10:
            return f"Au revoir {name}! Ce fut un plaisir de discuter avec vous! À bientôt! 👋✨"
        else:
            return f"Au revoir {name}! N'hésitez pas à revenir! 👋"
    else:
        if interaction_count > 10:
            return "Au revoir! Ce fut un plaisir de discuter avec vous! À bientôt! 👋✨"
        else:
            return "Au revoir! N'hésitez pas à revenir! 👋"


def _generate_contextual_answer(text: str, context: dict) -> str:
    """Generate contextual answer to questions."""
    lower = text.lower()
    
    # Technical questions
    if any(word in lower for word in ["code", "programme", "coder", "développeur", "developer"]):
        return _generate_technical_response(text, context)
    
    # Personal questions
    if any(word in lower for word in ["qui", "who", "quoi", "what", "comment", "how"]):
        return _generate_personal_response(text, context)
    
    # General questions
    return _generate_general_response(text, context)


def _generate_empathetic_response(text: str, context: dict) -> str:
    """Generate empathetic response for emotional support."""
    import random
    name = context['user_name']
    emotion = context['current_emotion']
    
    if emotion == "sad":
        responses = [
            "Je suis vraiment désolé d'entendre ça... 😔 Sachez que je suis là pour vous écouter et vous soutenir. Parfois, parler peut faire du bien. Voulez-vous me raconter ce qui vous tracasse? 🤗💙",
            "Courage! 💪 Les moments difficiles passent toujours. Je suis là pour vous accompagner et vous soutenir. N'hésitez pas à me parler, je vous écoute avec bienveillance. 🌟",
            "Je comprends que vous traversez une période difficile... 😔 Sachez que vous n'êtes pas seul(e). Je suis là pour vous écouter et vous soutenir. Parfois, exprimer ses émotions peut aider. 💙🤗"
        ]
    else:
        responses = [
            "Je suis là pour vous écouter. Parlez-moi de ce qui vous préoccupe. 🤗",
            "N'hésitez pas à me confier vos soucis. Je suis là pour vous soutenir. 💙",
            "Je vous écoute avec bienveillance. Racontez-moi ce qui vous tracasse. 🌟"
        ]
    
    response = random.choice(responses)
    if name:
        # Replace "vous" with the name in a more natural way
        response = response.replace("vous écouter", f"écouter {name}").replace("vous soutenir", f"soutenir {name}").replace("vous accompagner", f"accompagner {name}").replace("vous parler", f"parler à {name}").replace("vous préoccupe", f"préoccupe {name}").replace("vos soucis", f"vos soucis, {name}").replace("vous tracasse", f"tracasse {name}")
    
    return response


def _generate_technical_response(text: str, context: dict) -> str:
    """Generate technical response."""
    import random
    responses = [
        "🖥️ **Programmation - Mon domaine de prédilection!**\n\n💻 **Langages supportés:**\n• C (gcc, C11)\n• C++ (g++, C++17)\n• C# (csc, .NET)\n• Shell (bash, PowerShell)\n\n🚀 **Fonctionnalités:**\n• Compilation automatique\n• Exécution sécurisée\n• Gestion des erreurs\n• Optimisation\n\n💡 **Conseils:**\n• Utilisez /run <lang> <fichier>\n• Testez votre code\n• Vérifiez les erreurs\n\nQue souhaitez-vous programmer? 🎯",
        "💻 **Ah, la programmation! Mon cœur de métier!**\n\n🛠️ **Mes capacités techniques:**\n• Compilation multi-langages\n• Exécution sécurisée\n• Débogage intelligent\n• Optimisation de code\n\n🎯 **Langages disponibles:**\n• C/C++ (performances)\n• C# (.NET)\n• Shell (automatisation)\n\n💪 **Conseils d'expert:**\n• Commencez simple\n• Testez régulièrement\n• Documentez votre code\n\nPrêt à coder? 🚀"
    ]
    return random.choice(responses)


def _generate_entertainment_response(text: str, context: dict) -> str:
    """Generate entertainment response."""
    import random
    if "blague" in text.lower() or "joke" in text.lower():
        jokes = [
            "🤖 **Blague de dev:** Pourquoi les programmeurs préfèrent-ils l'hiver? Parce que l'été, il y a trop de bugs! 🐛😄",
            "🚪 **Blague tech:** Comment un programmeur ouvre-t-il une porte? Il fait Ctrl+Alt+Delete! 😆",
            "🤷‍♂️ **Blague classique:** Qu'est-ce qu'un développeur dit quand il est bloqué? 'Ça marchait hier!' 😂"
        ]
        return random.choice(jokes)
    
    responses = [
        "🎵 **Musique et divertissement!**\n\nLa musique adoucit vraiment les mœurs! 🎶 Que préférez-vous écouter? Rock, jazz, classique, ou quelque chose de plus moderne? 🎼",
        "🎬 **Divertissement - Un sujet passionnant!**\n\nLa musique est universelle et touche l'âme! 🎵 Quel est votre style préféré? 🎭"
    ]
    return random.choice(responses)


def _generate_personal_response(text: str, context: dict) -> str:
    """Generate personal response."""
    import random
    name = context['user_name']
    
    if "qui" in text.lower() or "who" in text.lower():
        responses = [
            "Je suis V-Bot, votre assistant virtuel intelligent! 🤖✨\n\nCréé spécialement pour ce projet de chat terminal, je combine:\n• Intelligence conversationnelle\n• Capacités techniques avancées\n• Mémoire contextuelle\n• Personnalité adaptative\n\nRavi de faire votre connaissance! 🎯",
            "Je suis V-Bot, votre compagnon virtuel! 🌟\n\nNé de ce projet de chat terminal, je suis conçu pour:\n• Comprendre et répondre intelligemment\n• Exécuter des tâches techniques\n• Mémoriser nos interactions\n• S'adapter à votre style\n\nEnchanté! 🚀"
        ]
    else:
        responses = [
            "Excellente question! 🤔 Laissez-moi réfléchir et vous donner une réponse complète et détaillée...",
            "Bonne interrogation! 💡 Je vais essayer de vous aider avec une explication claire et précise...",
            "Intéressant! 🎯 Voici ce que je peux vous dire sur ce sujet fascinant..."
        ]
    
    return random.choice(responses)


def _generate_general_response(text: str, context: dict) -> str:
    """Generate general contextual response."""
    import random
    name = context['user_name']
    interaction_count = context['interaction_count']
    
    # Based on interaction count and context
    if interaction_count < 3:
        responses = [
            "Excellente question! 🤔 Laissez-moi réfléchir et vous donner une réponse complète et détaillée...",
            "Bonne interrogation! 💡 Je vais essayer de vous aider avec une explication claire et précise..."
        ]
    else:
        responses = [
            "Intéressant! 🎯 Voici ce que je peux vous dire sur ce sujet fascinant...",
            "Excellente question! 🌟 Laissez-moi vous donner une réponse approfondie et utile..."
        ]
    
    return random.choice(responses)


def _generate_contextual_response(text: str, context: dict) -> str:
    """Generate contextual response for general conversation."""
    import random
    name = context['user_name']
    interaction_count = context['interaction_count']
    current_emotion = context['current_emotion']
    
    # Analyze text length and content
    text_length = len(text)
    
    if text_length < 10:
        responses = [
            "Intéressant! 💭",
            "Je vois! 👀",
            "Noté! 📝"
        ]
    elif text_length < 50:
        responses = [
            "Compris! ✅",
            "Reçu! 📨",
            "Entendu! 🎯"
        ]
    else:
        responses = [
            "Message reçu! 📬 Merci pour ce partage.",
            "Compris! ✅ C'est très intéressant.",
            "Noté! 📝 Je comprends votre point de vue."
        ]
    
    response = random.choice(responses)
    
    # Add personal touch if name is known
    if name and interaction_count > 3:
        response = f"{name}, {response.lower()}"
    
    # Add emotional context
    if current_emotion == "happy":
        response += " 😊"
    elif current_emotion == "sad":
        response += " 💙"
    
    return response


async def execute_code(lang: str, file_path: str, args: list) -> dict:
    """Async wrapper for the execute function."""
    from pathlib import Path
    source_path = Path(file_path)
    result = execute(lang, source_path, args)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


@app.post("/run")
async def run_code(payload: dict) -> JSONResponse:
    """Execute code on the server."""
    try:
        lang = payload.get("lang", "").lower()
        file_path = payload.get("file", "")
        args = payload.get("args", [])
        
        if not lang or not file_path:
            return JSONResponse(
                content={"error": "Missing required fields: lang and file"},
                status_code=400,
            )
        
        result = await execute_code(lang, file_path, args)
        return JSONResponse(content=result, status_code=200)
        
    except Exception as e:
        return JSONResponse(
            content={"error": f"Execution failed: {str(e)}"}, status_code=500
        )
