from __future__ import annotations

import json
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class User:
    """Structure pour représenter un utilisateur."""
    username: str
    password_hash: str
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    permissions: list[str] = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.permissions is None:
            self.permissions = ["user"]

class AuthManager:
    """Gestionnaire d'authentification pour l'application."""
    
    def __init__(self, config_dir: str = ".config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.users_file = self.config_dir / "users.json"
        self.tokens_file = self.config_dir / "tokens.json"
        self.secret_key = self._load_or_generate_secret()
        self.current_user: Optional[User] = None
        self.current_token: Optional[str] = None
        self.users = self._load_users()
        self.active_tokens = self._load_tokens()
    
    def _load_or_generate_secret(self) -> str:
        """Charge ou génère une clé secrète pour JWT."""
        secret_file = self.config_dir / "secret.key"
        if secret_file.exists():
            return secret_file.read_text().strip()
        else:
            secret = secrets.token_hex(32)
            secret_file.write_text(secret)
            return secret
    
    def _load_users(self) -> Dict[str, User]:
        """Charge les utilisateurs depuis le fichier."""
        if not self.users_file.exists():
            # Créer un utilisateur par défaut
            default_user = User(
                username="admin",
                password_hash=self._hash_password("admin"),
                created_at=datetime.now(),
                permissions=["admin"]
            )
            self._save_users({"admin": default_user})
            return {"admin": default_user}
        
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                users = {}
                for username, user_data in data.items():
                    user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
                    if user_data.get('last_login'):
                        user_data['last_login'] = datetime.fromisoformat(user_data['last_login'])
                    users[username] = User(**user_data)
                return users
        except Exception as e:
            print(f"Erreur lors du chargement des utilisateurs: {e}")
            return {}
    
    def _save_users(self, users: Dict[str, User]) -> None:
        """Sauvegarde les utilisateurs dans le fichier."""
        try:
            data = {}
            for username, user in users.items():
                user_dict = asdict(user)
                user_dict['created_at'] = user.created_at.isoformat()
                if user.last_login:
                    user_dict['last_login'] = user.last_login.isoformat()
                data[username] = user_dict
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des utilisateurs: {e}")
    
    def _load_tokens(self) -> Dict[str, Dict[str, Any]]:
        """Charge les tokens actifs."""
        if not self.tokens_file.exists():
            return {}
        
        try:
            with open(self.tokens_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement des tokens: {e}")
            return {}
    
    def _save_tokens(self) -> None:
        """Sauvegarde les tokens actifs."""
        try:
            with open(self.tokens_file, 'w', encoding='utf-8') as f:
                json.dump(self.active_tokens, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des tokens: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash un mot de passe avec salt."""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256()
        hash_obj.update((password + salt).encode('utf-8'))
        return f"{salt}${hash_obj.hexdigest()}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Vérifie un mot de passe contre son hash."""
        try:
            # Séparer le salt et le hash
            parts = password_hash.split('$', 1)
            if len(parts) != 2:
                return False
            
            salt, hash_value = parts
            
            # Recréer le hash avec le même salt
            hash_obj = hashlib.sha256()
            hash_obj.update((password + salt).encode('utf-8'))
            calculated_hash = hash_obj.hexdigest()
            
            # Comparer les hashes
            return calculated_hash == hash_value
        except Exception as e:
            print(f"Erreur lors de la vérification du mot de passe: {e}")
            return False
    
    def register(self, username: str, password: str, email: Optional[str] = None) -> bool:
        """Enregistre un nouvel utilisateur."""
        if username in self.users:
            return False
        
        user = User(
            username=username,
            password_hash=self._hash_password(password),
            email=email,
            created_at=datetime.now(),
            permissions=["user"]
        )
        
        self.users[username] = user
        self._save_users(self.users)
        return True
    
    def login(self, username: str, password: str) -> Optional[str]:
        """Connecte un utilisateur et retourne un token JWT."""
        if username not in self.users:
            return None
        
        user = self.users[username]
        if not user.is_active:
            return None
        
        if not self._verify_password(password, user.password_hash):
            return None
        
        # Mettre à jour la dernière connexion
        user.last_login = datetime.now()
        self._save_users(self.users)
        
        # Générer un token JWT
        token = jwt.encode(
            {
                'username': username,
                'exp': datetime.utcnow() + timedelta(hours=24),
                'iat': datetime.utcnow()
            },
            self.secret_key,
            algorithm='HS256'
        )
        
        # Sauvegarder le token
        self.active_tokens[token] = {
            'username': username,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
        }
        self._save_tokens()
        
        self.current_user = user
        self.current_token = token
        return token
    
    def logout(self) -> bool:
        """Déconnecte l'utilisateur actuel."""
        if self.current_token:
            if self.current_token in self.active_tokens:
                del self.active_tokens[self.current_token]
                self._save_tokens()
            
            self.current_user = None
            self.current_token = None
            return True
        return False
    
    def verify_token(self, token: str) -> Optional[User]:
        """Vérifie un token JWT et retourne l'utilisateur."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            username = payload['username']
            
            if username not in self.users:
                return None
            
            user = self.users[username]
            if not user.is_active:
                return None
            
            # Vérifier si le token est dans la liste des tokens actifs
            if token not in self.active_tokens:
                return None
            
            return user
        except jwt.ExpiredSignatureError:
            # Token expiré, le supprimer
            if token in self.active_tokens:
                del self.active_tokens[token]
                self._save_tokens()
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_current_user(self) -> Optional[User]:
        """Retourne l'utilisateur actuellement connecté."""
        return self.current_user
    
    def has_permission(self, permission: str) -> bool:
        """Vérifie si l'utilisateur actuel a une permission."""
        if not self.current_user:
            return False
        return permission in self.current_user.permissions
    
    def list_users(self) -> list[str]:
        """Liste tous les utilisateurs (admin seulement)."""
        if not self.has_permission("admin"):
            return []
        return list(self.users.keys())
    
    def delete_user(self, username: str) -> bool:
        """Supprime un utilisateur (admin seulement)."""
        if not self.has_permission("admin"):
            return False
        
        if username in self.users:
            del self.users[username]
            self._save_users(self.users)
            return True
        return False

# Instance globale du gestionnaire d'authentification
auth_manager = AuthManager()

def login_user(username: str, password: str) -> Optional[str]:
    """Fonction utilitaire pour connecter un utilisateur."""
    return auth_manager.login(username, password)

def logout_user() -> bool:
    """Fonction utilitaire pour déconnecter un utilisateur."""
    return auth_manager.logout()

def get_current_user() -> Optional[User]:
    """Fonction utilitaire pour obtenir l'utilisateur actuel."""
    return auth_manager.get_current_user()

def is_authenticated() -> bool:
    """Vérifie si un utilisateur est connecté."""
    return auth_manager.current_user is not None
