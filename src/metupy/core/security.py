# metupy/core/security.py
"""Security Manager - Keamanan Metupy."""

from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature,
    SignatureExpired,
)
from typing import Optional, Dict, Any
import hashlib
import secrets
import re

class SecurityManager:
    """Manages security features."""
    
    def __init__(self, engine):
        self.engine = engine
        self.secret_key = engine.config.SECRET_KEY
        self.serializer = URLSafeTimedSerializer(self.secret_key)
        self.csrf_tokens = {}
        
    def generate_token(self, data: Dict[str, Any], expiry: int = None) -> str:
        """Generate signed token."""
        if expiry:
            return self.serializer.dumps(data, salt='metupy-token', expires_in=expiry)
        return self.serializer.dumps(data, salt='metupy-token')
        
    def verify_token(self, token: str, expiry: int = None) -> Optional[Dict]:
        """Verify signed token."""
        try:
            if expiry:
                return self.serializer.loads(token, salt='metupy-token', max_age=expiry)
            return self.serializer.loads(token, salt='metupy-token')
        except SignatureExpired:
            print("Token expired")
            return None
        except BadSignature:
            print("Invalid token")
            return None
            
    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token."""
        token = secrets.token_urlsafe(32)
        self.csrf_tokens[session_id] = token
        return token
        
    def verify_csrf_token(self, session_id: str, token: str) -> bool:
        """Verify CSRF token."""
        return self.csrf_tokens.get(session_id) == token
        
    def hash_password(self, password: str) -> str:
        """Hash password."""
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256(
            (password + salt).encode()
        ).hexdigest()
        return f"{salt}${hashed}"
        
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password."""
        try:
            salt, original_hash = hashed_password.split('$')
            new_hash = hashlib.sha256(
                (password + salt).encode()
            ).hexdigest()
            return new_hash == original_hash
        except:
            return False
            
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input."""
        # Remove HTML tags
        text = re.sub(r'<[^>]*>', '', text)
        
        # Remove JavaScript
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        
        # Remove SQL injection patterns
        text = re.sub(r'(\b)(select|insert|update|delete|drop|union)(\b)', 
                      '', text, flags=re.IGNORECASE)
        
        # Remove script tags
        text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
        
        return text.strip()
        
    def validate_email(self, email: str) -> bool:
        """Validate email address."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
        
    def validate_url(self, url: str) -> bool:
        """Validate URL."""
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(pattern, url) is not None
        
    def generate_session_id(self) -> str:
        """Generate session ID."""
        return secrets.token_urlsafe(32)
        
    def encrypt_data(self, data: str) -> str:
        """Encrypt data."""
        # Simple encryption using secret key
        from cryptography.fernet import Fernet
        import base64
        
        key = base64.urlsafe_b64encode(
            hashlib.sha256(self.secret_key.encode()).digest()
        )
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()
        
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data."""
        from cryptography.fernet import Fernet
        import base64
        
        key = base64.urlsafe_b64encode(
            hashlib.sha256(self.secret_key.encode()).digest()
        )
        f = Fernet(key)
        return f.decrypt(encrypted_data.encode()).decode()