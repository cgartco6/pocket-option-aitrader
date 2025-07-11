import argparse
from core.pocket_option_api import PocketOptionAPI
from core.trading_engine import TradingEngine
from utilities.logger import configure_logger
import logging

def parse_args():
    parser = argparse.ArgumentParser(description="Pocket Option Trading System")
    parser.add_argument('--mode', choices=['demo', 'real'], default='demo',
                        help='Trading mode: demo or real account')
    parser.add_argument('--risk', choices=['conservative', 'moderate', 'aggressive'], 
                        default='moderate', help='Risk management profile')
    parser.add_argument('--capital', type=float, default=10000,
                        help='Initial trading capital')
    return parser.parse_args()

if _name_ == "_main_":
    # Configure logger
    configure_logger()
    logger = logging.getLogger(_name_)
    
    # Parse command line arguments
    args = parse_args()
    
    # Update settings based on command line arguments
    os.environ['DEMO_MODE'] = str(args.mode == 'demo')
    os.environ['RISK_PROFILE'] = args.risk
    os.environ['INITIAL_CAPITAL'] = str(args.capital)
    
    # Initialize API
    api = PocketOptionAPI()
    
    # Initialize trading engine
    engine = TradingEngine(api)
    
    # Initialize AI models
    try:
        engine.initialize_models()
    except Exception as e:
        logger.error(f"Model initialization failed: {str(e)}")
        exit(1)
    
    # Start trading
    try:
        engine.run()
    except Exception as e:
        logger.critical(f"Fatal error in trading engine: {str(e)}")
