import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)
from core.trading_engine import TradingEngine
from core.pocket_option_api import PocketOptionAPI
from config import settings
from utilities.security import SecurityManager
from utilities.logger import configure_logger

# Configure logger
configure_logger()
logger = logging.getLogger(_name_)

class TelegramCommandHandler:
    def _init_(self, trading_engine):
        self.engine = trading_engine
        self.security = SecurityManager()
        self.authorized_users = self._load_authorized_users()

    def _load_authorized_users(self):
        """Load authorized user IDs from secure storage"""
        # In real implementation, use encrypted DB or secure storage
        return ["user123", "admin456"]  # Example user IDs

    def authenticate_user(self, user_id):
        """Check if user is authorized"""
        return user_id in self.authorized_users

    def start(self, update: Update, context: CallbackContext):
        """Send welcome message"""
        user_id = update.effective_user.id
        if not self.authenticate_user(user_id):
            update.message.reply_text("⛔ Unauthorized access. Your ID has been logged.")
            logger.warning(f"Unauthorized access attempt: {user_id}")
            return
        
        update.message.reply_markdown(
            "🚀 Trading System Bot\n\n"
            "Available commands:\n"
            "/status - Current system status\n"
            "/performance - Trading performance\n"
            "/risk [profile] - Change risk profile\n"
            "/mode [demo|real] - Switch trading mode\n"
            "/pause - Pause trading\n"
            "/resume - Resume trading\n"
            "/help - Show this help"
        )

    def system_status(self, update: Update, context: CallbackContext):
        """Send system status"""
        user_id = update.effective_user.id
        if not self.authenticate_user(user_id):
            return
        
        status_report = self.engine.get_system_status()
        update.message.reply_markdown(status_report)

    def change_risk(self, update: Update, context: CallbackContext):
        """Change risk profile"""
        user_id = update.effective_user.id
        if not self.authenticate_user(user_id):
            return
        
        args = context.args
        if not args or args[0].lower() not in ["conservative", "moderate", "aggressive"]:
            update.message.reply_text("Usage: /risk [conservative|moderate|aggressive]")
            return
        
        new_profile = args[0].lower()
        self.engine.change_risk_profile(new_profile)
        update.message.reply_text(f"✅ Risk profile changed to {new_profile.title()}")

    def change_mode(self, update: Update, context: CallbackContext):
        """Switch between demo and real mode"""
        user_id = update.effective_user.id
        if not self.authenticate_user(user_id):
            return
        
        args = context.args
        if not args or args[0].lower() not in ["demo", "real"]:
            update.message.reply_text("Usage: /mode [demo|real]")
            return
        
        new_mode = args[0].lower() == "demo"
        self.engine.set_demo_mode(new_mode)
        mode_text = "Demo" if new_mode else "Real"
        update.message.reply_text(f"✅ Trading mode changed to {mode_text}")

    def pause_trading(self, update: Update, context: CallbackContext):
        """Pause trading"""
        user_id = update.effective_user.id
        if not self.authenticate_user(user_id):
            return
        
        self.engine.pause_trading()
        update.message.reply_text("⏸ Trading paused")

    def resume_trading(self, update: Update, context: CallbackContext):
        """Resume trading"""
        user_id = update.effective_user.id
        if not self.authenticate_user(user_id):
            return
        
        self.engine.resume_trading()
        update.message.reply_text("▶ Trading resumed")

    def performance_report(self, update: Update, context: CallbackContext):
        """Send performance report"""
        user_id = update.effective_user.id
        if not self.authenticate_user(user_id):
            return
        
        report = self.engine.get_performance_report()
        update.message.reply_markdown(report)

def main():
    """Start Telegram command listener"""
    # Initialize trading system
    api = PocketOptionAPI()
    engine = TradingEngine(api)
    engine.initialize_models()
    
    # Create command handler
    cmd_handler = TelegramCommandHandler(engine)
    
    # Start Telegram bot
    token = settings.API_KEYS['TELEGRAM_BOT_TOKEN']
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    
    # Register commands
    dp.add_handler(CommandHandler("start", cmd_handler.start))
    dp.add_handler(CommandHandler("status", cmd_handler.system_status))
    dp.add_handler(CommandHandler("performance", cmd_handler.performance_report))
    dp.add_handler(CommandHandler("risk", cmd_handler.change_risk))
    dp.add_handler(CommandHandler("mode", cmd_handler.change_mode))
    dp.add_handler(CommandHandler("pause", cmd_handler.pause_trading))
    dp.add_handler(CommandHandler("resume", cmd_handler.resume_trading))
    dp.add_handler(CommandHandler("help", cmd_handler.start))
    
    # Add error handler
    dp.add_error_handler(lambda u, c: logger.error(c.error))
    
    # Set bot commands
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("status", "System status"),
        BotCommand("performance", "Trading performance"),
        BotCommand("risk", "Change risk profile"),
        BotCommand("mode", "Switch demo/real mode"),
        BotCommand("pause", "Pause trading"),
        BotCommand("resume", "Resume trading"),
        BotCommand("help", "Show help")
    ]
    updater.bot.set_my_commands(commands)
    
    logger.info("Telegram command listener started")
    updater.start_polling()
    updater.idle()

if _name_ == '_main_':
    main()
