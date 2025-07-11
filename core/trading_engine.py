# Add these methods to the TradingEngine class
class TradingEngine:
    # ... existing code ...
    
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
        
        return (
            f"📊 SYSTEM STATUS\n"
            f"• *Mode*: {'DEMO' if settings.SETTINGS['DEMO_MODE'] else 'REAL'}\n"
            f"• *Status*: {'ACTIVE' if self.trading_active else 'PAUSED'}\n"
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
            f"• *Risk Profile*: {report['risk_profile'].title()}\n"
            f"• *Best Performer*: {report.get('best_instrument', 'N/A')}\n"
            f"• *Worst Performer*: {report.get('worst_instrument', 'N/A')}"
        )
    
    # ... existing code ...
