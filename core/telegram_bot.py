import requests
import datetime
import logging
from config import settings

logger = logging.getLogger(_name_)

class TelegramBot:
    def _init_(self):
        self.token = settings.API_KEYS['TELEGRAM_BOT_TOKEN']
        self.chat_id = settings.API_KEYS['TELEGRAM_CHAT_ID']
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, text, parse_mode='Markdown'):
        """Send message to Telegram channel"""
        if not settings.SETTINGS["TELEGRAM_ENABLED"] or not self.token or not self.chat_id:
            return False
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                logger.error(f"Telegram API error: {response.text}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Telegram send error: {str(e)}")
            return False
    
    def send_signal(self, symbol, signal, price, confidence):
        """Format and send trading signal"""
        emoji = "🚀" if signal == "BUY" else "📉"
        text = (
            f"{emoji} NEW TRADING SIGNAL {emoji}\n"
            f"• *Instrument*: {symbol}\n"
            f"• *Signal*: {signal}\n"
            f"• *Entry Price*: {price:.5f}\n"
            f"• *Confidence*: {confidence:.0%}\n"
            f"• *Time*: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self.send_message(text)
    
    def send_trade_result(self, symbol, signal, result, profit, balance):
        """Format and send trade result"""
        if profit >= 0:
            emoji = "✅"
            result_text = f"WIN +{profit:.2f}"
        else:
            emoji = "❌"
            result_text = f"LOSS {profit:.2f}"
        
        text = (
            f"{emoji} TRADE RESULT {emoji}\n"
            f"• *Instrument*: {symbol}\n"
            f"• *Direction*: {signal}\n"
            f"• *Result*: {result_text}\n"
            f"• *Account Balance*: ${balance:.2f}\n"
            f"• *Time*: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self.send_message(text)
    
    def send_performance_report(self, report):
        """Send daily performance report"""
        profit_emoji = "📈" if report['daily_profit'] >= 0 else "📉"
        text = (
            f"📊 DAILY PERFORMANCE REPORT\n"
            f"• *Date*: {report['date']}\n"
            f"• *Balance*: ${report['capital']:.2f}\n"
            f"• *Daily P/L*: {profit_emoji} ${report['daily_profit']:.2f}\n"
            f"• *Trades*: {report['total_trades']}\n"
            f"• *Win Rate*: {report['win_rate']:.2f}%\n"
            f"• *Profit Factor*: {report['profit_factor']:.2f}\n"
            f"• *Max Drawdown*: {report['max_drawdown']:.2%}\n"
            f"• *Risk Profile*: {report['risk_profile'].title()}"
        )
        return self.send_message(text)
    
    def send_alert(self, message):
        """Send important system alert"""
        text = f"🚨 SYSTEM ALERT 🚨\n{message}"
        return self.send_message(text)
