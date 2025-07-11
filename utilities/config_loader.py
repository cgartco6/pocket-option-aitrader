import os
from dotenv import load_dotenv

def load_config():
    """Load configuration from environment"""
    load_dotenv()
    return {
        'demo_mode': os.getenv('DEMO_MODE', 'True') == 'True',
        'risk_profile': os.getenv('RISK_PROFILE', 'moderate'),
        'initial_capital': float(os.getenv('INITIAL_CAPITAL', 10000)),
        'payout_threshold': float(os.getenv('PAYOUT_THRESHOLD', 0.92)),
        'trade_interval': int(os.getenv('TRADE_INTERVAL', 60)),
        'early_exit_threshold': float(os.getenv('EARLY_EXIT_THRESHOLD', 0.7)),
        'retrain_interval': int(os.getenv('RETRAIN_INTERVAL', 24)),
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    }
