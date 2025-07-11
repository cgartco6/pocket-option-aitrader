import requests
import config
import logging
import time
import random

logger = logging.getLogger(_name_)

class PocketOptionAPI:
    def _init_(self):
        self.base_url = "https://api.pocketoption.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.API_KEYS["POCKET_OPTION"]}'
        })
        self.demo_mode = config.SETTINGS["DEMO_MODE"]
    
    def get_instruments(self):
        """Retrieve OTC instruments with 92%+ payout"""
        if self.demo_mode:
            return self.get_demo_instruments()
            
        try:
            response = self.session.get(f"{self.base_url}/instruments", timeout=10)
            instruments = response.json().get('data', [])
            
            return [
                {
                    'id': i['id'],
                    'symbol': i['name'],
                    'payout': i['payoff'] / 100,
                    'type': 'crypto' if 'crypto' in i['group'] else 'currency'
                }
                for i in instruments 
                if i['payoff'] >= config.SETTINGS["PAYOUT_THRESHOLD"] * 100
                and ('otc' in i['group'] or 'crypto' in i['group'])
            ]
        except Exception as e:
            logger.error(f"Error fetching instruments: {str(e)}")
            return []
    
    def get_demo_instruments(self):
        """Simulated instruments for demo mode"""
        return [
            {'id': 'EURUSD-OTC', 'symbol': 'EUR/USD-OTC', 'payout': 0.93, 'type': 'currency'},
            {'id': 'GBPJPY-OTC', 'symbol': 'GBP/JPY-OTC', 'payout': 0.925, 'type': 'currency'},
            {'id': 'BTCUSD-OTC', 'symbol': 'BTC/USD-OTC', 'payout': 0.94, 'type': 'crypto'},
            {'id': 'ETHUSD-OTC', 'symbol': 'ETH/USD-OTC', 'payout': 0.935, 'type': 'crypto'},
            {'id': 'XRPUSD-OTC', 'symbol': 'XRP/USD-OTC', 'payout': 0.92, 'type': 'crypto'}
        ]
    
    def get_historical_data(self, instrument_id, interval='1m', limit=200):
        """Fetch historical price data"""
        if self.demo_mode:
            return self.get_demo_historical_data()
            
        try:
            params = {
                'instrument_id': instrument_id,
                'interval': interval,
                'limit': limit
            }
            response = self.session.get(f"{self.base_url}/chart", params=params, timeout=10)
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return []
    
    def get_demo_historical_data(self):
        """Generate simulated historical data"""
        # In real implementation, use real data source
        return [{
            'time': int(time.time()) - i*60,
            'open': 100.0 + i*0.1 + random.uniform(-0.5, 0.5),
            'high': 100.0 + i*0.1 + random.uniform(0, 1),
            'low': 100.0 + i*0.1 + random.uniform(-1, 0),
            'close': 100.0 + i*0.1 + random.uniform(-0.5, 0.5),
            'volume': 10000 + random.randint(-5000, 5000)
        } for i in range(200, 0, -1)]
    
    def place_trade(self, instrument_id, amount, direction, duration):
        """Place a trade"""
        if self.demo_mode:
            return {
                'success': True,
                'trade_id': f"DEMO_{int(time.time())}_{random.randint(1000,9999)}",
                'payout': 0.92,
                'entry_price': 100.0 + random.uniform(-1, 1)
            }
        
        try:
            payload = {
                'instrument_id': instrument_id,
                'amount': amount,
                'direction': direction,
                'duration': duration
            }
            response = self.session.post(f"{self.base_url}/trade", json=payload, timeout=10)
            return response.json()
        except Exception as e:
            logger.error(f"Trade placement error: {str(e)}")
            return {'success': False}
    
    def close_trade(self, trade_id):
        """Close trade early"""
        if self.demo_mode:
            return {'success': True}
        
        try:
            payload = {'trade_id': trade_id}
            response = self.session.post(f"{self.base_url}/close", json=payload, timeout=10)
            return response.json()
        except Exception as e:
            logger.error(f"Trade close error: {str(e)}")
            return {'success': False}
