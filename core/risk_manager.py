import pandas as pd
import numpy as np
from datetime import datetime
from config import settings
import logging

logger = logging.getLogger(_name_)

class RiskManager:
    def _init_(self, initial_capital):
        self.capital = initial_capital
        self.equity_curve = [initial_capital]
        self.trade_history = []
        self.daily_stats = {
            'date': datetime.now().date(),
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'profit': 0,
            'max_drawdown': 0
        }
        self.update_risk_profile()
    
    def update_risk_profile(self):
        """Update risk parameters based on selected profile"""
        profile = settings.RISK_PROFILES[settings.SETTINGS["RISK_PROFILE"]]
        self.risk_per_trade = profile["risk_per_trade"]
        self.max_daily_loss = profile["max_daily_loss"]
        self.max_concurrent_trades = profile["max_concurrent_trades"]
        logger.info(f"Risk profile updated to {settings.SETTINGS['RISK_PROFILE']}")
    
    def calculate_position_size(self):
        """Calculate position size based on risk management"""
        return self.capital * self.risk_per_trade
    
    def can_trade(self):
        """Check if trading is allowed based on risk rules"""
        # Check daily loss limit
        if self.daily_stats['profit'] < -self.capital * self.max_daily_loss:
            return False, "Daily loss limit reached"
        
        # Check max concurrent trades
        active_trades = sum(1 for trade in self.trade_history if trade['status'] == 'active')
        if active_trades >= self.max_concurrent_trades:
            return False, "Max concurrent trades reached"
        
        return True, ""
    
    def update_trade_result(self, trade_id, result, profit):
        """Update trade result in history"""
        for trade in self.trade_history:
            if trade['id'] == trade_id and trade['status'] == 'active':
                trade['result'] = result
                trade['profit'] = profit
                trade['status'] = 'closed'
                trade['exit_time'] = datetime.now()
                break
        
        # Update capital and equity curve
        self.capital += profit
        self.equity_curve.append(self.capital)
        
        # Update daily stats
        self.daily_stats['trades'] += 1
        self.daily_stats['profit'] += profit
        if profit > 0:
            self.daily_stats['wins'] += 1
        else:
            self.daily_stats['losses'] += 1
        
        # Update max drawdown
        peak = max(self.equity_curve)
        trough = min(self.equity_curve[-10:])  # Last 10 trades
        if peak > 0:
            drawdown = (peak - trough) / peak
            self.daily_stats['max_drawdown'] = max(self.daily_stats['max_drawdown'], drawdown)
    
    def start_new_day(self):
        """Reset daily statistics"""
        today = datetime.now().date()
        if today != self.daily_stats['date']:
            self.daily_stats = {
                'date': today,
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'profit': 0,
                'max_drawdown': 0
            }
            logger.info("New trading day started")
    
    def get_performance_report(self):
        """Generate performance report"""
        total_trades = self.daily_stats['trades']
        win_rate = (self.daily_stats['wins'] / total_trades * 100) if total_trades > 0 else 0
        profit_factor = -self.daily_stats['wins'] / self.daily_stats['losses'] if self.daily_stats['losses'] < 0 else float('inf')
        
        return {
            "date": self.daily_stats['date'].strftime('%Y-%m-%d'),
            "capital": self.capital,
            "daily_profit": self.daily_stats['profit'],
            "total_trades": total_trades,
            "wins": self.daily_stats['wins'],
            "losses": self.daily_stats['losses'],
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown": self.daily_stats['max_drawdown'],
            "risk_profile": settings.SETTINGS["RISK_PROFILE"]
        }
    
    def get_risk_parameters(self):
        """Get current risk parameters"""
        return {
            "risk_per_trade": self.risk_per_trade,
            "max_daily_loss": self.max_daily_loss,
            "max_concurrent_trades": self.max_concurrent_trades
        }
