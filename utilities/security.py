import os
from cryptography.fernet import Fernet
import base64
from config import settings

class SecurityManager:
    def _init_(self):
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY not set in environment")
        
        # Ensure key is 32 bytes URL-safe base64-encoded
        key = base64.urlsafe_b64encode(self.encryption_key.encode()[:32].ljust(32, b'='))
        self.cipher = Fernet(key)

    def encrypt(self, data):
        """Encrypt sensitive data"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode()

    def decrypt(self, encrypted_data):
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def load_encrypted_env(self):
        """Load and decrypt environment variables"""
        encrypted_vars = ['NEWS_API_KEY', 'POCKET_OPTION_KEY', 
                         'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
        
        decrypted = {}
        for var in encrypted_vars:
            encrypted_val = os.getenv(var)
            if encrypted_val:
                decrypted[var] = self.decrypt(encrypted_val)
        return decrypted

def generate_encryption_key():
    """Generate a secure encryption key"""
    return Fernet.generate_key().decode()

# Example usage:
# security = SecurityManager()
# encrypted = security.encrypt("my_secret")
# decrypted = security.decrypt(encrypted)
