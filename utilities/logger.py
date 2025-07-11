import logging
import os
from datetime import datetime
from config import settings

def configure_logger():
    """Configure logging system"""
    log_level = settings.SETTINGS["LOG_LEVEL"].upper()
    log_dir = settings.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log filename with timestamp
    log_file = os.path.join(
        log_dir, 
        f"trading_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Add colors for console output
    logging.addLevelName(
        logging.WARNING, 
        f"\033[93m{logging.getLevelName(logging.WARNING)}\033[0m"
    )
    logging.addLevelName(
        logging.ERROR, 
        f"\033[91m{logging.getLevelName(logging.ERROR)}\033[0m"
    )
    logging.addLevelName(
        logging.INFO, 
        f"\033[94m{logging.getLevelName(logging.INFO)}\033[0m"
    )
    logging.addLevelName(
        logging.DEBUG, 
        f"\033[90m{logging.getLevelName(logging.DEBUG)}\033[0m"
    )
    
    logging.info("Logger configured successfully")
