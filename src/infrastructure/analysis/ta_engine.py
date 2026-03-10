import pandas as pd
import ta
import numpy as np
from typing import List
from ...core.interfaces.technical_analyzer import ITechnicalAnalyzer
from ...core.domain.models import OHLCV, TechnicalIndicators, Signal
from ...core.domain.enums import SignalType
import logging

logger = logging.getLogger(__name__)

class TAEngine(ITechnicalAnalyzer):
    def calculate_indicators(self, data: List[OHLCV]) -> TechnicalIndicators:
        if len(data) < 20:
             logger.warning("Not enough data to calculate reliable indicators.")
             return TechnicalIndicators()
             
        # Convert to DataFrame
        df = pd.DataFrame([vars(d) for d in data])
        
        # Calculate Indicators
        try:
            # RSI
            rsi = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi().iloc[-1]
            
            # MACD
            macd = ta.trend.MACD(close=df['close'])
            macd_line = macd.macd().iloc[-1]
            macd_signal = macd.macd_signal().iloc[-1]
            macd_hist = macd.macd_diff().iloc[-1]
            
            # SMA / EMA
            sma_20 = ta.trend.SMAIndicator(close=df['close'], window=20).sma_indicator().iloc[-1]
            sma_50 = ta.trend.SMAIndicator(close=df['close'], window=50).sma_indicator().iloc[-1]
            
            sma_200 = None
            if len(data) >= 200:
                sma_200 = ta.trend.SMAIndicator(close=df['close'], window=200).sma_indicator().iloc[-1]
            
            ema_20 = ta.trend.EMAIndicator(close=df['close'], window=20).ema_indicator().iloc[-1]
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
            bb_upper = bb.bollinger_hband().iloc[-1]
            bb_middle = bb.bollinger_mavg().iloc[-1]
            bb_lower = bb.bollinger_lband().iloc[-1]
            
            # ATR
            atr = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14).average_true_range().iloc[-1]
            
            return TechnicalIndicators(
                rsi_14=float(rsi) if not pd.isna(rsi) else None,
                macd_line=float(macd_line) if not pd.isna(macd_line) else None,
                macd_signal=float(macd_signal) if not pd.isna(macd_signal) else None,
                macd_histogram=float(macd_hist) if not pd.isna(macd_hist) else None,
                sma_20=float(sma_20) if not pd.isna(sma_20) else None,
                sma_50=float(sma_50) if not pd.isna(sma_50) else None,
                sma_200=float(sma_200) if not pd.isna(sma_200) else None,
                ema_20=float(ema_20) if not pd.isna(ema_20) else None,
                bb_upper=float(bb_upper) if not pd.isna(bb_upper) else None,
                bb_middle=float(bb_middle) if not pd.isna(bb_middle) else None,
                bb_lower=float(bb_lower) if not pd.isna(bb_lower) else None,
                atr_14=float(atr) if not pd.isna(atr) else None
            )
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return TechnicalIndicators()

    def generate_signal(self, symbol: str, data: List[OHLCV], indicators: TechnicalIndicators) -> Signal:
        score = 0
        reasons = []
        
        if not data:
            return Signal(symbol=symbol, type=SignalType.HOLD, strength=0.0, reason="No data", source="TECHNICAL")
            
        current_price = data[-1].close
        
        # 1. RSI Logic
        if indicators.rsi_14 is not None:
            if indicators.is_oversold_rsi:
                score += 2
                reasons.append("RSI is oversold (<30).")
            elif indicators.is_overbought_rsi:
                score -= 2
                reasons.append("RSI is overbought (>70).")
                
        # 2. MACD Logic
        if indicators.macd_line is not None and indicators.macd_signal is not None:
            if indicators.macd_line > indicators.macd_signal and indicators.macd_histogram and indicators.macd_histogram > 0:
                score += 1
                reasons.append("MACD is bullish (Line > Signal).")
            elif indicators.macd_line < indicators.macd_signal and indicators.macd_histogram and indicators.macd_histogram < 0:
                score -= 1
                reasons.append("MACD is bearish (Line < Signal).")
                
        # 3. Moving Averages
        if indicators.sma_20 is not None and indicators.sma_50 is not None:
            if current_price > indicators.sma_20 and indicators.sma_20 > indicators.sma_50:
                score += 1
                reasons.append("Price is in short-term uptrend (Price > SMA20 > SMA50).")
            elif current_price < indicators.sma_20 and indicators.sma_20 < indicators.sma_50:
                score -= 1
                reasons.append("Price is in short-term downtrend (Price < SMA20 < SMA50).")
                
        # Determine final signal
        signal_type = SignalType.HOLD
        strength = abs(score) / 4.0 # Normalize 0-1 loosely
        if strength > 1.0: strength = 1.0
        
        if score >= 2:
            signal_type = SignalType.BUY
        elif score <= -2:
            signal_type = SignalType.SELL
            
        reason_str = " ".join(reasons) if reasons else "Neutral technicals."
        
        return Signal(
            symbol=symbol,
            type=signal_type,
            strength=strength,
            reason=reason_str,
            source="TECHNICAL"
        )
