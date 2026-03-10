from enum import Enum, auto

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class LLMProviderType(str, Enum):
    OPENAI = "OPENAI"
    MOCK = "MOCK"
    GEMINI = "GEMINI"

class MarketDataProviderType(str, Enum):
    YAHOO = "yahoo"
    BORSAPY = "borsapy"

class TimeFrame(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1wk"
    MO1 = "1mo"

class Sentiment(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"

class AlertType(str, Enum):
    PRICE_ABOVE = "PRICE_ABOVE"
    PRICE_BELOW = "PRICE_BELOW"
    VOLUME_SPIKE = "VOLUME_SPIKE"
    RSI_OVERSOLD = "RSI_OVERSOLD"
    RSI_OVERBOUGHT = "RSI_OVERBOUGHT"
    MACD_CROSSOVER = "MACD_CROSSOVER"
    STRONG_BUY_SIGNAL = "STRONG_BUY_SIGNAL"

class NewsCategory(str, Enum):
    EARNINGS = "EARNINGS"
    MARKET = "MARKET"
    SECTOR = "SECTOR"
    COMPANY = "COMPANY"
    MACRO = "MACRO"
    CRYPTO = "CRYPTO"
    GENERAL = "GENERAL"
