import os
from dotenv import load_dotenv
from utilities.security import SecurityManager

# Load environment variables
load_dotenv()

# Initialize security manager
security = SecurityManager()
decrypted_secrets = security.load_encrypted_env()

# Risk Management Settings
RISK_PROFILES = {
    "conservative": {
        "risk_per_trade": 0.005,
        "max_daily_loss": 0.02,
        "max_concurrent_trades": 2
    },
    "moderate": {
        "risk_per_trade": 0.01,
        "max_daily_loss": 0.05,
        "max_concurrent_trades": 4
    },
    "aggressive": {
        "risk_per_trade": 0.02,
        "max_daily_loss": 0.10,
        "max_concurrent_trades": 6
    }
}

# Trading Settings
SETTINGS = {
    "DEMO_MODE": os.getenv('DEMO_MODE', 'True') == 'True',
    "RISK_PROFILE": os.getenv('RISK_PROFILE', 'moderate'),
    "PAYOUT_THRESHOLD": float(os.getenv('PAYOUT_THRESHOLD', 0.92)),
    "TRADE_INTERVAL": int(os.getenv('TRADE_INTERVAL', 60)),
    "EARLY_EXIT_THRESHOLD": float(os.getenv('EARLY_EXIT_THRESHOLD', 0.7)),
    "RETRAIN_INTERVAL": int(os.getenv('RETRAIN_INTERVAL', 24)),
    "INITIAL_CAPITAL": float(os.getenv('INITIAL_CAPITAL', 10000)),
    "BROKER": os.getenv('BROKER', 'POCKET_OPTION'),
    "TELEGRAM_ENABLED": os.getenv('TELEGRAM_ENABLED', 'True') == 'True',
    "LOG_LEVEL": os.getenv('LOG_LEVEL', 'INFO'),
    "SECURE_MODE": os.getenv('SECURE_MODE', 'True') == 'True'
}

# API Keys
API_KEYS = {
    'NEWS_API': decrypted_secrets.get('NEWS_API_KEY', ''),
    'POCKET_OPTION': decrypted_secrets.get('POCKET_OPTION_KEY', ''),
    'TELEGRAM_BOT_TOKEN': decrypted_secrets.get('TELEGRAM_BOT_TOKEN', ''),
    'TELEGRAM_CHAT_ID': decrypted_secrets.get('TELEGRAM_CHAT_ID', '')
}

# Directories
MODEL_DIR = "data/models/"
HISTORICAL_DIR = "data/historical/"
LOG_DIR = "data/logs/"
