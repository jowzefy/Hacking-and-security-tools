"""
Repository pattern for persisting scan results.
Supports encryption if enabled in config.
"""

import json
import os
import time
from typing import Any, Dict
from core.security.encryptor import DataEncryptor
from app.config import AppConfig


class ScanRepository:
    """Handles saving and loading scan results."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.output_dir = config.output.output_dir
        self.encryptor = None
        if config.security.encrypt_output:
            key = config.security.encryption_key or os.getenv('GWM_ENCRYPTION_KEY')
            if not key:
                # Generate a key for the session (not persistent, for demo)
                key = DataEncryptor().generate_key()
                print(f"⚠️  Encryption key not set, using temporary key: {key[:10]}...")
            self.encryptor = DataEncryptor(key=key)

    def save(self, data: Dict[str, Any], filename: str) -> str:
        """Save data to JSON file, optionally encrypted."""
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, filename)
        
        json_str = json.dumps(data, indent=4, ensure_ascii=False)
        
        if self.encryptor:
            encrypted_data = self.encryptor.encrypt(json_str)
            with open(filepath + '.enc', 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
            return filepath + '.enc'
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
            return filepath

    def load(self, filepath: str) -> Dict[str, Any]:
        """Load and possibly decrypt data."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if filepath.endswith('.enc') and self.encryptor:
            json_str = self.encryptor.decrypt(content)
            return json.loads(json_str)
        else:
            return json.loads(content)