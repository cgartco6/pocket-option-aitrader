import os
from cryptography.fernet import Fernet
import base64
import logging
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import binascii

logger = logging.getLogger(_name_)

class SecurityManager:
    def _init_(self):
        self.encryption_key = self.derive_key(os.getenv('ENCRYPTION_KEY'))
        
    def derive_key(self, password):
        """Derive secure key from password using PBKDF2"""
        salt = b'secure_salt_'  # In production, use random salt stored separately
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
    def encrypt(self, data):
        """Encrypt sensitive data"""
        if isinstance(data, str):
            data = data.encode()
        cipher = Fernet(self.encryption_key)
        return cipher.encrypt(data).decode()

    def decrypt(self, encrypted_data):
        """Decrypt sensitive data"""
        try:
            cipher = Fernet(self.encryption_key)
            return cipher.decrypt(encrypted_data.encode()).decode()
        except (binascii.Error, ValueError) as e:
            logger.error(f"Decryption error: {str(e)}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected decryption error: {str(e)}")
            return ""

    def load_encrypted_env(self):
        """Load and decrypt environment variables"""
        encrypted_vars = ['NEWS_API_KEY', 'POCKET_OPTION_KEY', 
                         'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
        
        decrypted = {}
        for var in encrypted_vars:
            encrypted_val = os.getenv(var)
            if encrypted_val:
                try:
                    decrypted[var] = self.decrypt(encrypted_val)
                except Exception as e:
                    logger.error(f"Error decrypting {var}: {str(e)}")
        return decrypted

def generate_encryption_key():
    """Generate a secure encryption key"""
    return Fernet.generate_key().decode()
