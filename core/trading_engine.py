import pandas as pd
import numpy as np
import time
import threading
import queue
import logging
from datetime import datetime, timedelta
from . import utils
from .ai_models import AIModel
from .risk_manager import RiskManager
from .telegram_bot import TelegramBot
from .pocket_option_api import PocketOptionAPI
from config import settings
import random

logger = logging.getLogger(_name_)

class TradingEngine:
    def _init_(self, api: PocketOptionAPI):
        self.api = api
        self.ai_models = {}
        self.risk_manager = RiskManager(settings.SETTINGS["INITIAL_CAPITAL"])
        self.telegram_bot = TelegramBot()
        self.active_trades = {}
        self.last_retrain = datetime.now()
        self.trading_active = True
        self.last_signal_time = None
        self.price_queue = queue.Queue()
        self.api.start_websocket()
        
        # Send startup message
        if settings.SETTINGS["DEMO_MODE"]:
            self.telegram_bot.send_message("🚀 TRADING SYSTEM STARTED (DEMO MODE)")
        else:
            self.telegram_bot.send_message("🚀 TRADING SYSTEM STARTED (REAL ACCOUNT)")
    
    def initialize_models(self):
        """Initialize AI models for all instruments"""
        instruments = self.api.get_instruments()
        for instrument in instruments:
            try:
                self.ai_models[instrument['id']] = AIModel(instrument['id'])
                logger.info(f"Initialized model for {instrument['symbol']}")
                
                # Initial training if no model exists
                if not self.ai_models[instrument['id']].model:
                    hist_data = self.api.get_historical_data(instrument['id'], limit=200)
                    if hist_data:
                        df = pd.DataFrame(hist_data)
                        df = utils.calculate_indicators(df)
                        self.ai_models[instrument['id']].train(df)
            except Exception as e:
                logger.error(f"Error initializing model for {instrument['symbol']}: {str(e)}")
    
    def retrain_models(self):
        """Periodically retrain all models"""
        while True:
            try:
                current_time = datetime.now()
                hours_since = (current_time - self.last_retrain).total_seconds() / 3600
                
                if hours_since >= settings.SETTINGS["RETRAIN_INTERVAL"]:
                    logger.info("Starting model retraining")
                    self.telegram_bot.send_message("🔄 Retraining AI models with new market data")
                    
                    for instrument_id, model in self.ai_models.items():
                        try:
                            hist_data = self.api.get_historical_data(instrument_id, limit=500)
                            if not hist_data:
                                continue
                                
                            df = pd.DataFrame(hist_data)
                            df = utils.calculate_indicators(df)
                            accuracy = model.train(df)
                            logger.info(f"Retrained {instrument_id} | Accuracy: {accuracy:.2%}")
                        except Exception as e:
                            logger.error(f"Error retraining {instrument_id}: {str(e)}")
                    
                    self.last_retrain = datetime.now()
                    self.telegram_bot.send_message("✅ Model retraining completed successfully")
                
                # Update risk manager at midnight
                self.risk_manager.start_new_day()
                time.sleep(3600)  # Check hourly
            except Exception as e:
                logger.error(f"Error in retrain thread: {str(e)}")
                time.sleep(60)
    
    def generate_signal(self, instrument):
        """Generate trading signal with AI and technical analysis"""
        instrument_id = instrument['id']
        symbol = instrument['symbol']
        
        # Get historical data
        hist_data = self.api.get_historical_data(instrument_id)
        if not hist_data or len(hist_data) < 30:
            return None, None, 0
            
        df = pd.DataFrame(hist_data)
        df = utils.calculate_indicators(df)
        if len(df) < 2:
            return None, None, 0
        
        # Get market sentiment
        sentiment = utils.get_market_sentiment(symbol.split('-')[0])
        
        # Detect breakout patterns
        breakout = utils.detect_breakout(df)
        
        # Get AI prediction
        ai_model = self.ai_models.get(instrument_id)
        if ai_model:
            try:
                current_features = df.iloc[-1][['ema5', 'ema20', 'rsi6', 'macd', 'macd_signal', 'macd_hist']].values
                ai_prediction = ai_model.predict(current_features)
            except Exception as e:
                logger.error(f"AI prediction error: {str(e)}")
                ai_prediction = None
        else:
            ai_prediction = None
        
        # Signal generation logic
        signal = None
        confidence = 0
        
        # AI + Breakout combination
        if breakout == 'bullish' or (ai_prediction == 1 and sentiment in ['bullish', 'neutral']):
            signal = 'BUY'
            confidence = 0.9 if breakout and ai_prediction == 1 else 0.7
        elif breakout == 'bearish' or (ai_prediction == 0 and sentiment in ['bearish', 'neutral']):
            signal = 'SELL'
            confidence = 0.9 if breakout and ai_prediction == 0 else 0.7
        
        return signal, df, confidence
    
    def monitor_trade(self, trade_id, instrument_id, entry_price, direction, payout):
        """Real-time trade monitoring with early exit"""
        start_time = datetime.now()
        duration = settings.SETTINGS["TRADE_INTERVAL"]
        exit_threshold = settings.SETTINGS["EARLY_EXIT_THRESHOLD"] * duration
        last_price = entry_price
        profit_factor = 0
        
        logger.info(f"Monitoring trade {trade_id} for {instrument_id} ({direction} at {entry_price})")
        
        while (datetime.now() - start_time).seconds < duration:
            if not self.trading_active:
                logger.info(f"Trade {trade_id} paused by system")
                time.sleep(1)
                continue
                
            # Get real-time price
            current_price = self.api.get_last_price(instrument_id)
            if current_price is None or current_price <= 0:
                time.sleep(0.1)
                continue
                
            # Calculate profit factor
            if direction == 'BUY':
                profit_factor = (current_price - entry_price) / entry_price
            else:  # SELL
                profit_factor = (entry_price - current_price) / entry_price
            
            # Track last price
            last_price = current_price
            
            # Check exit conditions
            elapsed = (datetime.now() - start_time).seconds
            if profit_factor < -0.003 and elapsed > exit_threshold:
                logger.info(f"Early exit triggered for trade {trade_id} at {current_price}")
                return "early_loss", profit_factor
                
            time.sleep(0.2)  # Check 5 times per second
        
        # Final calculation
        current_price = last_price
        if direction == 'BUY':
            profit_factor = (current_price - entry_price) / entry_price
        else:
            profit_factor = (entry_price - current_price) / entry_price
            
        result = "win" if profit_factor > 0 else "loss"
        logger.info(f"Trade {trade_id} completed with result: {result}")
        return result, profit_factor
        
    def execute_trade(self, instrument, signal, confidence):
        """Execute and monitor trade with real-time processing"""
        if not self.trading_active:
            logger.info("Trading paused, skipping trade execution")
            return
            
        instrument_id = instrument['id']
        symbol = instrument['symbol']
        payout = instrument['payout']
        
        # Check risk management
        can_trade, reason = self.risk_manager.can_trade()
        if not can_trade:
            logger.warning(f"Trade blocked: {reason}")
            self.telegram_bot.send_message(f"⛔ TRADE BLOCKED\n{reason}")
            return
        
        position_size = self.risk_manager.calculate_position_size()
        duration = settings.SETTINGS["TRADE_INTERVAL"]  # Seconds
        
        # Place trade
        if settings.SETTINGS["DEMO_MODE"]:
            trade_id = f"DEMO_{int(time.time())}_{random.randint(1000,9999)}"
            entry_price = self.api.get_last_price(instrument_id)
            logger.info(f"Demo trade placed: {symbol} {signal} at {entry_price}")
        else:
            trade = self.api.place_trade(
                instrument_id=instrument_id,
                amount=position_size,
                direction=signal.lower(),
                duration=duration
            )
            if not trade.get('success'):
                logger.error(f"Trade failed for {symbol}")
                self.telegram_bot.send_message(f"❌ TRADE FAILED\n{instrument['symbol']} {signal}")
                return
            trade_id = trade['trade_id']
            entry_price = trade['entry_price']
            logger.info(f"Real trade placed: {trade_id} {symbol} {signal} at {entry_price}")
        
        # Register trade with risk manager
        self.risk_manager.trade_history.append({
            'id': trade_id,
            'instrument': symbol,
            'direction': signal,
            'entry_price': entry_price,
            'size': position_size,
            'payout': payout,
            'status': 'active',
            'entry_time': datetime.now()
        })
        
        # Add to active trades
        self.active_trades[trade_id] = {
            'instrument': symbol,
            'entry_price': entry_price,
            'direction': signal,
            'size': position_size,
            'start_time': datetime.now()
        }
        
        # Send signal to Telegram
        self.telegram_bot.send_signal(symbol, signal, entry_price, confidence)
        self.last_signal_time = datetime.now()
        
        # Monitor trade
        result, profit_factor = self.monitor_trade(
            trade_id, 
            instrument_id, 
            entry_price, 
            signal,
            payout
        )
        
        # Calculate P&L
        if result == "win":
            profit = position_size * payout * profit_factor
        else:
            profit = -position_size
        
        # Update risk manager
        self.risk_manager.update_trade_result(trade_id, result, profit)
        
        # Remove from active trades
        if trade_id in self.active_trades:
            del self.active_trades[trade_id]
        
        # Update AI model
        ai_model = self.ai_models.get(instrument_id)
        if ai_model:
            try:
                # Get latest features
                hist_data = self.api.get_historical_data(instrument_id, limit=1)
                if hist_data:
                    df = pd.DataFrame(hist_data)
                    df = utils.calculate_indicators(df)
                    if not df.empty:
                        features = df.iloc[-1][['ema5', 'ema20', 'rsi6', 'macd', 'macd_signal', 'macd_hist']].values
                        target = 1 if result == "win" else 0
                        ai_model.update(features, target)
            except Exception as e:
                logger.error(f"Model update error: {str(e)}")
        
        # Send result to Telegram
        self.telegram_bot.send_trade_result(
            symbol, 
            signal, 
            result, 
            profit, 
            self.risk_manager.capital
        )
        
        # Log result
        result_text = (f"{symbol} | {signal} | {result.upper()} | "
                       f"Profit: {profit:.2f} | Balance: {self.risk_manager.capital:.2f}")
        logger.info(result_text)
    
    def close_trade(self, trade_id):
        """Close trade early"""
        if not settings.SETTINGS["DEMO_MODE"]:
            self.api.close_trade(trade_id)
        
        # Mark as closed in risk manager
        for trade in self.risk_manager.trade_history:
            if trade['id'] == trade_id and trade['status'] == 'active':
                trade['status'] = 'closed'
                trade['exit_time'] = datetime.now()
                logger.info(f"Trade {trade_id} closed early")
                break
    
    def run(self):
        """Main trading loop"""
        # Initialize models
        self.initialize_models()
        
        # Start retraining thread
        retrain_thread = threading.Thread(target=self.retrain_models, daemon=True)
        retrain_thread.start()
        
        # Start performance reporting thread
        report_thread = threading.Thread(target=self.performance_reporting, daemon=True)
        report_thread.start()
        
        logger.info("=== TRADING SYSTEM ACTIVE ===")
        logger.info(f"Initial Balance: {self.risk_manager.capital:.2f}")
        logger.info(f"Risk Profile: {settings.SETTINGS['RISK_PROFILE'].title()}")
        
        try:
            while True:
                if not self.trading_active:
                    logger.info("Trading paused...")
                    time.sleep(10)
                    continue
                    
                instruments = self.api.get_instruments()
                logger.info(f"Scanning {len(instruments)} instruments...")
                
                for instrument in instruments:
                    if not self.trading_active:
                        break
                        
                    if len(self.active_trades) >= self.risk_manager.max_concurrent_trades:
                        logger.info("Max concurrent trades reached")
                        break
                    
                    signal, df, confidence = self.generate_signal(instrument)
                    if not signal or confidence < 0.7:
                        continue
                    
                    logger.info(f"Strong signal detected for {instrument['symbol']}: {signal} (Confidence: {confidence:.0%})")
                    
                    # Execute trade in separate thread
                    trade_thread = threading.Thread(
                        target=self.execute_trade,
                        args=(instrument, signal, confidence)
                    )
                    trade_thread.daemon = True
                    trade_thread.start()
                    time.sleep(1)  # Stagger trade starts
                
                time.sleep(30)  # Wait before next scan
        
        except KeyboardInterrupt:
            logger.info("\nShutting down trading system...")
            self.display_performance()
        except Exception as e:
            logger.critical(f"Fatal error in trading loop: {str(e)}")
            self.telegram_bot.send_message(f"🚨 CRITICAL ERROR\n{str(e)}")
    
    def performance_reporting(self):
        """Send periodic performance reports"""
        while True:
            try:
                # Send hourly update during trading hours (08:00-20:00 UTC)
                now = datetime.utcnow()
                if 8 <= now.hour < 20:
                    report = self.risk_manager.get_performance_report()
                    if report['total_trades'] > 0:
                        self.telegram_bot.send_performance_report(report)
                        logger.info("Sent hourly performance report")
                
                # Sleep for 1 hour
                time.sleep(3600)
            except Exception as e:
                logger.error(f"Performance reporting error: {str(e)}")
                time.sleep(60)
    
    def display_performance(self):
        """Show performance statistics"""
        report = self.risk_manager.get_performance_report()
        total_trades = report['total_trades']
        win_rate = report['win_rate']
        
        logger.info("\n" + "="*50)
        logger.info("FINAL PERFORMANCE REPORT")
        logger.info("="*50)
        logger.info(f"Date: {report['date']}")
        logger.info(f"Final Balance: {report['capital']:.2f}")
        logger.info(f"Daily P/L: {report['daily_profit']:.2f}")
        logger.info(f"Total Trades: {total_trades}")
        logger.info(f"Successful Trades: {report['wins']}")
        logger.info(f"Failed Trades: {report['losses']}")
        logger.info(f"Win Rate: {win_rate:.2f}%")
        logger.info(f"Profit Factor: {report['profit_factor']:.2f}")
        logger.info(f"Max Drawdown: {report['max_drawdown']:.2%}")
        logger.info(f"Risk Profile: {report['risk_profile'].title()}")
        logger.info("="*50)
        
        # Send final report to Telegram
        self.telegram_bot.send_performance_report(report)
    
    def pause_trading(self):
        """Pause trading activities"""
        self.trading_active = False
        self.telegram_bot.send_message("⏸ TRADING PAUSED")
        logger.warning("Trading paused by user command")
    
    def resume_trading(self):
        """Resume trading activities"""
        self.trading_active = True
        self.telegram_bot.send_message("▶ TRADING RESUMED")
        logger.warning("Trading resumed by user command")
    
    def change_risk_profile(self, profile):
        """Change risk management profile"""
        if profile not in ["conservative", "moderate", "aggressive"]:
            logger.error(f"Invalid risk profile: {profile}")
            return False
        
        self.risk_manager.update_risk_profile(profile)
        logger.info(f"Risk profile changed to {profile}")
        self.telegram_bot.send_message(
            f"🛡 RISK PROFILE UPDATED\n"
            f"Changed to {profile.upper()} mode"
        )
        return True
    
    def set_demo_mode(self, demo_mode):
        """Switch between demo and real trading"""
        settings.SETTINGS["DEMO_MODE"] = demo_mode
        mode = "DEMO" if demo_mode else "REAL"
        logger.info(f"Trading mode changed to {mode}")
        self.telegram_bot.send_message(
            f"🔄 TRADING MODE CHANGED\n"
            f"Now trading in {mode} mode"
        )
    
    def get_system_status(self):
        """Generate system status report"""
        report = self.risk_manager.get_performance_report()
        active_trades = len(self.active_trades)
        model_status = "Operational" if self.ai_models else "Initializing"
        trading_status = "ACTIVE" if self.trading_active else "PAUSED"
        
        return (
            f"📊 SYSTEM STATUS\n"
            f"• *Mode*: {'DEMO' if settings.SETTINGS['DEMO_MODE'] else 'REAL'}\n"
            f"• *Status*: {trading_status}\n"
            f"• *Balance*: ${report['capital']:.2f}\n"
            f"• *Active Trades*: {active_trades}\n"
            f"• *Risk Profile*: {settings.SETTINGS['RISK_PROFILE'].title()}\n"
            f"• *AI Status*: {model_status}\n"
            f"• *Last Signal*: {self.last_signal_time.strftime('%Y-%m-%d %H:%M') if self.last_signal_time else 'N/A'}"
        )
    
    def get_performance_report(self):
        """Generate detailed performance report"""
        report = self.risk_manager.get_performance_report()
        return (
            f"📈 PERFORMANCE REPORT\n"
            f"• *Date*: {report['date']}\n"
            f"• *Balance*: ${report['capital']:.2f}\n"
            f"• *Daily P/L*: ${report['daily_profit']:.2f}\n"
            f"• *Trades*: {report['total_trades']}\n"
            f"• *Win Rate*: {report['win_rate']:.2f}%\n"
            f"• *Profit Factor*: {report['profit_factor']:.2f}\n"
            f"• *Max Drawdown*: {report['max_drawdown']:.2%}\n"
            f"• *Risk Profile*: {report['risk_profile'].title()}"
        )
