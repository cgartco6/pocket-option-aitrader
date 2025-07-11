"""
secrets.py - Secure secrets management
Uses environment variables and encryption for sensitive data
"""

import os
from cryptography.fernet import Fernet
from utilities.security import SecurityManager

class SecretStore:
    def _init_(self):
        self.security = SecurityManager()
        self.secrets = self._load_secrets()
        
    def _load_secrets(self):
        """Load and decrypt secrets from environment"""
        return {
            'news_api': self.security.decrypt(os.getenv('NEWS_API_KEY', '')),
            'pocket_option': self.security.decrypt(os.getenv('POCKET_OPTION_KEY', '')),
            'telegram_token': self.security.decrypt(os.getenv('TELEGRAM_BOT_TOKEN', '')),
            'telegram_chat': self.security.decrypt(os.getenv('TELEGRAM_CHAT_ID', ''))
        }
    
    def get(self, key, default=None):
        """Get decrypted secret"""
        return self.secrets.get(key, default)
    
    def rotate_keys(self):
        """Rotate encryption keys (for security maintenance)"""
        # This would typically be run during scheduled maintenance
        new_key = Fernet.generate_key().decode()
        print(f"New encryption key: {new_key}")
        print("Update ENCRYPTION_KEY in .env and re-encrypt all secrets")

# Singleton instance
secrets = SecretStore()
