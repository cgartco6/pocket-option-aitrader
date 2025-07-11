import psutil
import time
import logging
from utilities.logger import configure_logger
from utilities.security import SecurityManager
from core.telegram_bot import TelegramBot
from config import settings

# Configure logger
configure_logger()
logger = logging.getLogger(_name_)

class SystemMonitor:
    def _init_(self):
        self.bot = TelegramBot()
        self.security = SecurityManager()
        self.thresholds = {
            "cpu": 85,     # %
            "memory": 80,   # %
            "disk": 90,     # %
            "temp": 80      # °C
        }
        self.trading_process = "python main.py"
    
    def check_resources(self):
        """Check system resources"""
        alerts = []
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > self.thresholds["cpu"]:
            alerts.append(f"CPU usage high: {cpu_percent}%")
        
        # Memory usage
        mem = psutil.virtual_memory()
        if mem.percent > self.thresholds["memory"]:
            alerts.append(f"Memory usage high: {mem.percent}%")
        
        # Disk usage
        disk = psutil.disk_usage('/')
        if disk.percent > self.thresholds["disk"]:
            alerts.append(f"Disk usage high: {disk.percent}%")
        
        # Temperature (Linux only)
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                for entry in temps['coretemp']:
                    if entry.current > self.thresholds["temp"]:
                        alerts.append(f"High temperature: {entry.current}°C ({entry.label})")
        except AttributeError:
            pass  # Not available on this system
        
        return alerts
    
    def check_trading_process(self):
        """Check if trading process is running"""
        for proc in psutil.process_iter(['name']):
            if self.trading_process in proc.info['name']:
                return True
        return False
    
    def monitor_loop(self):
        """Continuous monitoring loop"""
        logger.info("Starting system monitor")
        while True:
            try:
                # Check system resources
                alerts = self.check_resources()
                if alerts:
                    message = "🚨 SYSTEM ALERT\n" + "\n".join(alerts)
                    self.bot.send_message(message)
                    logger.warning(f"System alerts: {alerts}")
                
                # Check trading process
                if not self.check_trading_process():
                    self.bot.send_message("❌ TRADING PROCESS DOWN")
                    logger.critical("Trading process not running!")
                
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Monitor error: {str(e)}")
                time.sleep(60)

if _name_ == '_main_':
    monitor = SystemMonitor()
    monitor.monitor_loop()
