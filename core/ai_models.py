import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.neural_network import MLPClassifier
import joblib
import os
import xgboost as xgb
from config import settings
import logging

logger = logging.getLogger(_name_)

MODEL_PATH = settings.MODEL_DIR

class AIModel:
    def _init_(self, instrument_id):
        self.instrument_id = instrument_id
        self.model = None
        self.accuracy = 0
        self.model_file = f"{MODEL_PATH}model_{instrument_id}.pkl"
        
        # Create models directory if not exists
        os.makedirs(MODEL_PATH, exist_ok=True)
        
        # Load model if exists
        if os.path.exists(self.model_file):
            try:
                self.model = joblib.load(self.model_file)
                logger.info(f"Loaded existing model for {instrument_id}")
            except Exception as e:
                logger.error(f"Error loading model for {instrument_id}: {str(e)}")
    
    def create_dataset(self, df):
        """Create training dataset from historical data"""
        # Add technical features
        df['price_change'] = df['close'].pct_change()
        df['volatility'] = df['high'] - df['low']
        
        # Target: next candle direction (1 = up, 0 = down)
        df['Target'] = np.where(df['close'].shift(-1) > df['close'], 1, 0)
        
        # Feature selection
        features = df[[
            'ema5', 'ema20', 'rsi6', 'macd', 'macd_signal', 'macd_hist',
            'price_change', 'volatility'
        ]]
        
        target = df['Target']
        return features[:-1], target[:-1]  # Exclude last row
    
    def train(self, df):
        """Train/re-train model"""
        try:
            X, y = self.create_dataset(df)
            
            if len(X) < 100:
                logger.warning(f"Insufficient data for {self.instrument_id} ({len(X)} samples)")
                return 0
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Choose model based on data size
            if len(X_train) > 1000:
                # Use XGBoost for larger datasets
                self.model = xgb.XGBClassifier(
                    n_estimators=200,
                    max_depth=6,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42
                )
            else:
                # Use Neural Network for smaller datasets
                self.model = MLPClassifier(
                    hidden_layer_sizes=(50, 25, 10),
                    activation='relu',
                    solver='adam',
                    max_iter=500,
                    random_state=42
                )
            
            # Train
            self.model.fit(X_train, y_train)
            
            # Evaluate
            preds = self.model.predict(X_test)
            self.accuracy = accuracy_score(y_test, preds)
            
            # Save model
            joblib.dump(self.model, self.model_file)
            logger.info(f"Model trained for {self.instrument_id} | Accuracy: {self.accuracy:.2%}")
            
            return self.accuracy
        except Exception as e:
            logger.error(f"Error training model for {self.instrument_id}: {str(e)}")
            return 0
    
    def predict(self, features):
        """Make prediction"""
        if not self.model:
            return None
        try:
            return self.model.predict(features.reshape(1, -1))[0]
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return None
    
    def update(self, features, target):
        """Online learning update"""
        if self.model:
            try:
                # For XGBoost models
                if hasattr(self.model, 'partial_fit'):
                    self.model.partial_fit(features.reshape(1, -1), [target])
                # For Neural Networks
                elif hasattr(self.model, 'warm_start'):
                    self.model.warm_start = True
                    self.model.fit(features.reshape(1, -1), [target])
                
                joblib.dump(self.model, self.model_file)
                logger.debug("Model updated with new data point")
            except Exception as e:
                logger.error(f"Model update error: {str(e)}")
