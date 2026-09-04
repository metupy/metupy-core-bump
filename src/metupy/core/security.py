"""
Security manager for Metupy.

Provides authentication, token generation, password hashing,
and input sanitization without heavy dependencies.
"""

import re
import base64
import hashlib
import secrets
from typing import Any, Dict, Optional

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


class SecurityManager:
    """Manage security features for Metupy."""

    def __init__(self, engine):
        """
        Initialize SecurityManager.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.secret_key = getattr(engine.config, 'SECRET_KEY', 'dev-secret-key')
        self.serializer = URLSafeTimedSerializer(self.secret_key)
        self.csrf_tokens: Dict[str, str] = {}

    def generate_token(self, data: Dict[str, Any], expiry: int = 3600) -> str:
        """
        Generate signed token for authentication.

        Args:
            data: Data to encode in token.
            expiry: Token expiration in seconds.

        Returns:
            Signed token string.
        """
        return self.serializer.dumps(data, salt='metupy-token', expires_in=expiry)

    def verify_token(self, token: str, expiry: int = 3600) -> Optional[Dict]:
        """
        Verify signed token.

        Args:
            token: Token to verify.
            expiry: Maximum token age in seconds.

        Returns:
            Decoded data if valid, None otherwise.
        """
        try:
            return self.serializer.loads(token, salt='metupy-token', max_age=expiry)
        except (SignatureExpired, BadSignature):
            return None

    def generate_csrf_token(self, session_id: str) -> str:
        """
        Generate CSRF token for session.

        Args:
            session_id: Session identifier.

        Returns:
            CSRF token string.
        """
        token = secrets.token_urlsafe(32)
        self.csrf_tokens[session_id] = token
        return token

    def verify_csrf_token(self, session_id: str, token: str) -> bool:
        """
        Verify CSRF token.

        Args:
            session_id: Session identifier.
            token: Token to verify.

        Returns:
            True if token matches, False otherwise.
        """
        return self.csrf_tokens.get(session_id) == token

    def hash_password(self, password: str) -> str:
        """
        Hash password using multiple rounds of SHA-256.

        Args:
            password: Plain password.

        Returns:
            Salted hash string.
        """
        salt = secrets.token_hex(16)
        hashed = password + salt
        for _ in range(1000):
            hashed = hashlib.sha256(hashed.encode()).hexdigest()
        return f"{salt}${hashed}"

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.

        Args:
            password: Plain password to check.
            hashed_password: Stored hash.

        Returns:
            True if password matches, False otherwise.
        """
        try:
            salt, original_hash = hashed_password.split('$')
            hashed = password + salt
            for _ in range(1000):
                hashed = hashlib.sha256(hashed.encode()).hexdigest()
            return hashed == original_hash
        except (ValueError, AttributeError):
            return False

    def encrypt_data(self, data: str) -> str:
        """
        Encrypt string using XOR with secret key.

        Args:
            data: Plain text to encrypt.

        Returns:
            Base64-encoded encrypted string.
        """
        key = hashlib.sha256(self.secret_key.encode()).digest()
        data_bytes = data.encode()
        encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data_bytes))
        return base64.b64encode(encrypted).decode()

    def decrypt_data(self, encrypted_b64: str) -> str:
        """
        Decrypt XOR-encrypted string.

        Args:
            encrypted_b64: Base64-encoded encrypted string.

        Returns:
            Decrypted plain text.
        """
        try:
            key = hashlib.sha256(self.secret_key.encode()).digest()
            encrypted = base64.b64decode(encrypted_b64)
            decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted))
            return decrypted.decode()
        except (ValueError, UnicodeDecodeError):
            return ""

    def sanitize_input(self, text: str) -> str:
        """
        Sanitize user input by removing HTML and scripts.

        Args:
            text: Raw user input.

        Returns:
            Sanitized text.
        """
        text = re.sub(r'<[^>]*>', '', text)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
        return text.strip()

    def validate_email(self, email: str) -> bool:
        """
        Validate email address format.

        Args:
            email: Email to validate.

        Returns:
            True if valid, False otherwise.
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_url(self, url: str) -> bool:
        """
        Validate URL format.

        Args:
            url: URL to validate.

        Returns:
            True if valid, False otherwise.
        """
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(pattern, url) is not None

    def generate_session_id(self) -> str:
        """
        Generate random session ID.

        Returns:
            URL-safe random string.
        """
        return secrets.token_urlsafe(32)