"""
Advanced Data Encryption Module
Uses Fernet (symmetric encryption) for sensitive data protection.
"""

import base64
import os
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class DataEncryptor:
    """
    Secure data encryption using Fernet (AES-128-CBC with HMAC).
    Implements key derivation for password-based encryption.
    """
    
    def __init__(self, key: str = None, salt: bytes = None):
        """
        Initialize encryptor with optional key.
        If no key provided, generates a new one.
        """
        self.salt = salt or os.urandom(16)
        self.key = key
        # self._fernet: Optional[Fernet] = None
        
        if key:
            self._initialize_fernet(key)
    
    def _initialize_fernet(self, key: str):
        """Initialize Fernet instance with derived key."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        self._fernet = Fernet(derived_key)
    
    def generate_key(self) -> str:
        """Generate a new secure key."""
        return base64.urlsafe_b64encode(os.urandom(32)).decode()
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        if not self._fernet:
            raise ValueError("Encryptor not initialized. Set key first.")
        try:
            encrypted = self._fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        if not self._fernet:
            raise ValueError("Encryptor not initialized. Set key first.")
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data)
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode()
        except InvalidToken:
            logger.error("Invalid token or wrong key")
            raise ValueError("Decryption failed: Invalid key or corrupted data")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise