"""
auto_deploy.py - Automated deployment script
Sets up environment, installs dependencies, and launches system
"""

import os
import sys
import subprocess
import logging
from utilities.logger import configure_logger

configure_logger()
logger = logging.getLogger(_name_)

class AutoDeploy:
    def _init_(self, mode='demo', risk='moderate', capital=10000):
        self.mode = mode
        self.risk = risk
        self.capital = capital
        self.processes = []
        
    def run_command(self, command, cwd=None):
        """Execute system command"""
        logger.info(f"Executing: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                logger.error(f"Command failed: {result.stderr}")
            else:
                logger.info(f"Command output: {result.stdout}")
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            return False
    
    def setup_environment(self):
        """Set up Python environment"""
        # Create virtual environment
        if not os.path.exists("venv"):
            logger.info("Creating virtual environment")
            if not self.run_command("python -m venv venv"):
                return False
        
        # Install dependencies
        logger.info("Installing dependencies")
        pip_cmd = "venv\\Scripts\\pip" if sys.platform == "win32" else "venv/bin/pip"
        if not self.run_command(f"{pip_cmd} install -r requirements.txt"):
            return False
            
        return True
    
    def start_process(self, command, name):
        """Start a background process"""
        logger.info(f"Starting {name} process")
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append((process, name))
            return True
        except Exception as e:
            logger.error(f"Failed to start {name}: {str(e)}")
            return False
    
    def monitor_processes(self):
        """Monitor running processes"""
        logger.info("Monitoring system processes...")
        try:
            while True:
                for i, (process, name) in enumerate(self.processes):
                    if process.poll() is not None:
                        logger.error(f"{name} process exited with code {process.returncode}")
                        # Restart process
                        self.processes.pop(i)
                        self.start_process(" ".join(process.args), name)
                
                # Check every 30 seconds
                time.sleep(30)
        except KeyboardInterrupt:
            logger.info("Stopping process monitoring")
    
    def deploy(self):
        """Main deployment routine"""
        # Setup environment
        if not self.setup_environment():
            logger.error("Environment setup failed")
            return False
        
        # Start main components
        python_cmd = "venv\\Scripts\\python" if sys.platform == "win32" else "venv/bin/python"
        
        # Main trading system
        main_cmd = f"{python_cmd} main.py --mode {self.mode} --risk {self.risk} --capital {self.capital}"
        self.start_process(main_cmd, "Trading System")
        
        # Telegram listener
        telegram_cmd = f"{python_cmd} scripts/telegram_listener.py"
        self.start_process(telegram_cmd, "Telegram Listener")
        
        # System monitor
        monitor_cmd = f"{python_cmd} scripts/system_monitor.py"
        self.start_process(monitor_cmd, "System Monitor")
        
        # Start process monitoring
        self.monitor_processes()
        
        return True

if _name_ == "_main_":
    import argparse
    parser = argparse.ArgumentParser(description="Auto Deploy Trading System")
    parser.add_argument('--mode', choices=['demo', 'real'], default='demo')
    parser.add_argument('--risk', choices=['conservative', 'moderate', 'aggressive'], default='moderate')
    parser.add_argument('--capital', type=float, default=10000)
    args = parser.parse_args()
    
    deployer = AutoDeploy(args.mode, args.risk, args.capital)
    if deployer.deploy():
        logger.info("Deployment completed successfully")
    else:
        logger.error("Deployment failed")
