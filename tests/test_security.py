import unittest
from unittest.mock import MagicMock, patch
from core.trading_engine import TradingEngine
from core.pocket_option_api import PocketOptionAPI
from core.risk_manager import RiskManager

class TestTradingSystem(unittest.TestCase):
    def setUp(self):
        self.mock_api = MagicMock(spec=PocketOptionAPI)
        self.engine = TradingEngine(self.mock_api)
        self.engine.risk_manager = MagicMock(spec=RiskManager)
        self.engine.telegram_bot = MagicMock()
        
    def test_initialization(self):
        self.assertIsNotNone(self.engine)
        self.assertIsInstance(self.engine.risk_manager, MagicMock)
        
    def test_risk_profile_change(self):
        self.engine.change_risk_profile("conservative")
        self.engine.risk_manager.update_risk_profile.assert_called()
        
    def test_trading_mode_switch(self):
        self.engine.set_demo_mode(True)
        self.assertTrue(self.engine.demo_mode)
        
    @patch('core.trading_engine.datetime')
    def test_performance_reporting(self, mock_datetime):
        mock_datetime.utcnow.return_value.hour = 10  # Within trading hours
        self.engine.performance_reporting()
        self.engine.telegram_bot.send_performance_report.assert_called()

if _name_ == '_main_':
    unittest.main()
