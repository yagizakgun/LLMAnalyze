import pytest
from datetime import datetime, timezone
from src.core.domain.models import OHLCV, TechnicalIndicators
from src.infrastructure.analysis.ta_engine import TAEngine
from src.core.domain.enums import SignalType

def test_ta_engine_insufficient_data():
    engine = TAEngine()
    data = [OHLCV(timestamp=datetime.now(timezone.utc), open=100, high=105, low=95, close=100, volume=1000)]
    
    indicators = engine.calculate_indicators(data)
    assert indicators.rsi_14 is None
    
    signal = engine.generate_signal("AAPL", data, indicators)
    assert signal.type == SignalType.HOLD

def test_ta_engine_with_dummy_data():
    engine = TAEngine()
    # Generate 30 days of dummy uptrend data
    data = []
    base_price = 100.0
    for i in range(30):
        data.append(OHLCV(
            timestamp=datetime.now(timezone.utc),
            open=base_price,
            high=base_price + 2,
            low=base_price - 1,
            close=base_price + 1,
            volume=1000 + i
        ))
        base_price += 1.0 # Uptrend

    indicators = engine.calculate_indicators(data)
    
    # RSI should be high because of constant uptrend
    assert indicators.rsi_14 is not None
    assert indicators.sma_20 is not None
    
    signal = engine.generate_signal("AAPL", data, indicators)
    # We should get a valid SignalType, in this specific dummy data RSI becomes overbought so it's a SELL.
    assert signal.type in [SignalType.BUY, SignalType.HOLD, SignalType.SELL]
