import requests
import websocket
import threading
import json
import time
import random
import logging
import sqlite3
from config import settings
from data.historical.realtime_store import RealTimeStore

logger = logging.getLogger(_name_)

class PocketOptionAPI:
    def _init_(self):
        self.base_url = "https://api.pocketoption.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {settings.API_KEYS["POCKET_OPTION"]}'
        })
        self.demo_mode = settings.SETTINGS["DEMO_MODE"]
        self.ws = None
        self.realtime_prices = {}
        self.ws_thread = None
        self.ws_connected = False
        self.data_store = RealTimeStore()
        
    def start_websocket(self):
        """Start WebSocket connection for real-time prices"""
        if self.demo_mode:
            logger.info("Skipping WebSocket in demo mode")
            return
            
        def on_open(ws):
            logger.info("WebSocket connection opened")
            self.ws_connected = True
            # Subscribe to all OTC instruments
            instruments = self.get_instruments()
            for inst in instruments:
                ws.send(json.dumps({
                    "name": "subscribe",
                    "asset": inst['id'].split('-')[0].replace('/', '')
                }))
            
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get('name') == 'ticker':
                    asset = data['msg']['asset']
                    price = float(data['msg']['price'])
                    volume = float(data['msg'].get('volume', 0))
                    
                    # Update real-time cache
                    self.realtime_prices[asset] = {
                        'price': price,
                        'timestamp': time.time()
                    }
                    
                    # Save to persistent storage
                    self.data_store.save_tick(asset, price, volume, "ws")
            except Exception as e:
                logger.error(f"WebSocket message error: {str(e)}")
                
        def on_error(ws, error):
            logger.error(f"WebSocket error: {str(error)}")
            
        def on_close(ws, close_status_code, close_msg):
            logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
            self.ws_connected = False
            # Attempt reconnect
            time.sleep(5)
            self.start_websocket()
            
        # Create WebSocket connection
        self.ws = websocket.WebSocketApp(
            "wss://api.pocketoption.com/",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Start in a separate thread
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        logger.info("WebSocket connection started")
        
    def get_realtime_price(self, instrument_id):
        """Get real-time price from WebSocket"""
        if self.demo_mode:
            # Generate simulated price
            return 100.0 + random.uniform(-1, 1)
            
        if not self.ws_connected:
            return None
            
        # Use only the base symbol (EUR/USD-OTC -> EURUSD)
        symbol = instrument_id.split('-')[0].replace('/', '')
        price_data = self.realtime_prices.get(symbol)
        
        if price_data and time.time() - price_data['timestamp'] < 5:
            return price_data['price']
        return None
        
    def get_last_price(self, instrument_id):
        """Get last price with real-time fallback"""
        # First try real-time WebSocket price
        realtime_price = self.get_realtime_price(instrument_id)
        if realtime_price is not None:
            return realtime_price
            
        # Fallback to historical API
        hist_data = self.get_historical_data(instrument_id, limit=1)
        return float(hist_data[0]['close']) if hist_data else 0
        
    # ... rest of existing PocketOptionAPI class ...
