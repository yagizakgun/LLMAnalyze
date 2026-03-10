import pytest
from datetime import datetime
from src.core.domain.models import StockInfo, Signal, SignalType, TechnicalIndicators

def test_signal_creation():
    sig = Signal(
        symbol="AAPL",
        type=SignalType.BUY,
        strength=0.9,
        reason="Strong MACD crossover",
        source="TECHNICAL"
    )
    assert sig.symbol == "AAPL"
    assert sig.type == SignalType.BUY
    assert sig.strength == 0.9

def test_technical_indicators_properties():
    ti = TechnicalIndicators(rsi_14=20.0)
    assert ti.is_oversold_rsi is True
    assert ti.is_overbought_rsi is False
    
    ti2 = TechnicalIndicators(rsi_14=80.0)
    assert ti2.is_oversold_rsi is False
    assert ti2.is_overbought_rsi is True
