import os
import sys
from utilities.security import SecurityManager, generate_encryption_key
from dotenv import load_dotenv

def main():
    """Encrypt sensitive values for storage"""
    load_dotenv()
    
    if not os.getenv('ENCRYPTION_KEY'):
        print("ENCRYPTION_KEY not found in .env")
        key = generate_encryption_key()
        print(f"Generated new encryption key: {key}")
        print("Please add this to your .env file as ENCRYPTION_KEY")
        return
    
    security = SecurityManager()
    
    print("Pocket Option Secrets Encryption")
    print("=" * 40)
    
    secrets = {
        'NEWS_API_KEY': "Enter your NewsAPI key: ",
        'POCKET_OPTION_KEY': "Enter your PocketOption API key: ",
        'TELEGRAM_BOT_TOKEN': "Enter your Telegram bot token: ",
        'TELEGRAM_CHAT_ID': "Enter your Telegram chat ID: "
    }
    
    encrypted_values = {}
    
    for key, prompt in secrets.items():
        value = input(prompt).strip()
        if value:
            encrypted = security.encrypt(value)
            encrypted_values[key] = encrypted
    
    print("\nEncrypted values for .env:")
    print("=" * 40)
    for key, value in encrypted_values.items():
        print(f"{key}={value}")
    
    print("\nCopy these to your .env file")

if _name_ == '_main_':
    main()
