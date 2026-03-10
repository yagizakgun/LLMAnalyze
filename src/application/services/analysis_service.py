import asyncio
from typing import Any, Optional
from ...core.domain.models import AnalysisResult, Signal, SignalType, TimeFrame
from ...core.domain.enums import LLMProviderType, Sentiment, MarketDataProviderType
from ...infrastructure.llm.factory import LLMFactory
from ...core.interfaces.market_data import IMarketDataProvider
from ...core.interfaces.news_provider import INewsProvider
from ...core.interfaces.technical_analyzer import ITechnicalAnalyzer
import logging

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(
        self,
        llm_factory: LLMFactory,
        market_data: IMarketDataProvider,
        news: INewsProvider,
        ta: ITechnicalAnalyzer,
        market_provider_override: Optional[IMarketDataProvider] = None
    ):
        self.llm_factory = llm_factory
        self.market_data = market_data
        self.news = news
        self.ta = ta
        self.market_provider_override = market_provider_override

    def _get_market_provider(self, provider_type: Optional[MarketDataProviderType] = None) -> IMarketDataProvider:
        """Returns the market provider - override takes precedence, then fallback to default."""
        if self.market_provider_override:
            return self.market_provider_override
        if provider_type and provider_type == MarketDataProviderType.BORSAPY:
            from ...infrastructure.market_data.borsapy_provider import BorsapyProvider
            return BorsapyProvider()
        return self.market_data

    async def run_full_analysis(
        self,
        symbol: str,
        timeframe: TimeFrame,
        llm_provider: LLMProviderType = LLMProviderType.OPENAI,
        market_provider: Optional[MarketDataProviderType] = None
    ) -> AnalysisResult:
        """Runs the complete analysis pipeline sequentially/concurrently where possible."""
        logger.info(f"Starting full analysis for {symbol} on {timeframe} using {llm_provider}, market_provider={market_provider}")

        try:
            # Resolve LLM Provider
            llm = self.llm_factory.get_provider(llm_provider)

            # Get the market data provider (using override if set, otherwise use requested type)
            market_data = self._get_market_provider(market_provider)

            # 1. Fetch Market Data & Technical Analysis
            price_task = market_data.get_current_price(symbol)
            ohlcv_task = market_data.get_stock_data(symbol, timeframe, limit=500)
            news_task = self.news.get_news_for_symbol(symbol, limit=5)
            
            # Run IO bound tasks concurrently
            current_price, ohlcv_data, news_articles = await asyncio.gather(
                price_task, ohlcv_task, news_task
            )
            
            # Calculate Indicators
            indicators = self.ta.calculate_indicators(ohlcv_data)
            ta_signal = self.ta.generate_signal(symbol, ohlcv_data, indicators)

            # 2. Setup Context for LLM
            # Fetch Borsapy-specific data if using Borsapy provider
            borsapy_data = {}
            if market_provider == MarketDataProviderType.BORSAPY:
                fundamentals_task = market_data.get_stock_fundamentals(symbol)
                analyst_task = market_data.get_analyst_data(symbol)
                fundamentals, analyst = await asyncio.gather(fundamentals_task, analyst_task)
                borsapy_data = {
                    "fundamentals": fundamentals,
                    "analyst_data": analyst
                }

            context_data = {
                "symbol": symbol,
                "current_price": current_price,
                "recent_candles": [
                    {"time": str(d.timestamp), "close": d.close, "volume": d.volume}
                    for d in ohlcv_data[-5:]
                ],
                "indicators": {
                    "rsi": indicators.rsi_14,
                    "macd": indicators.macd_line,
                    "sma_20": indicators.sma_20,
                    "sma_50": indicators.sma_50,
                    "sma_200": indicators.sma_200
                },
                "news_headlines": [a.title for a in news_articles],
                "borsapy_data": borsapy_data if borsapy_data else None
            }
            
            # 3. Analyze Sentiment & Provide LLM Interpretation
            article_dicts = [
                {"title": a.title, "summary": a.summary or ""} for a in news_articles
            ]
            sentiment_task = llm.analyze_sentiment([a.title + " " + (a.summary or "") for a in news_articles])
            article_sentiment_task = llm.analyze_article_sentiments(article_dicts)
            llm_analysis_task = llm.analyze_stock(context_data)
            
            # Run LLM calls concurrently
            sentiment_result, article_sentiments, llm_result = await asyncio.gather(
                sentiment_task, article_sentiment_task, llm_analysis_task
            )
            
            # Update articles with individual sentiment scores
            sentiment_map = {item["index"]: item for item in article_sentiments}
            for i, article in enumerate(news_articles):
                if i in sentiment_map:
                    entry = sentiment_map[i]
                    try:
                        article.sentiment = Sentiment(entry["sentiment"])
                    except ValueError:
                        article.sentiment = Sentiment.NEUTRAL
                    article.sentiment_score = entry["score"]
                else:
                    article.sentiment = sentiment_result.overall_sentiment
                    article.sentiment_score = sentiment_result.score
                
            # 4. Resolve Contradictions & Final Signal
            contradictions = []
            if ta_signal.type != llm_result.signal and SignalType.HOLD not in (ta_signal.type, llm_result.signal):
                contradictions.append(
                    f"Technical Signal ({ta_signal.type}) contradicts LLM Signal ({llm_result.signal})."
                )
                
            final_signal = self._determine_final_signal(symbol, ta_signal, llm_result, sentiment_result)
            
            return AnalysisResult(
                symbol=symbol,
                timeframe=timeframe,
                current_price=current_price,
                technical_indicators=indicators,
                technical_signal=ta_signal,
                news=news_articles,
                news_sentiment=sentiment_result,
                llm_analysis=llm_result,
                final_signal=final_signal,
                contradictions=contradictions,
                borsapy_data=borsapy_data if borsapy_data else None
            )
        except Exception as e:
            logger.error(f"Analysis failed for {symbol}: {e}")
            raise

    def _determine_final_signal(self, symbol: str, ta_signal: Signal, llm: Any, sent: Any) -> Signal:
        # Simple weighted logic
        score = 0
        
        # TA 40%
        if ta_signal.type == SignalType.BUY: score += 4
        elif ta_signal.type == SignalType.SELL: score -= 4
        
        # LLM 40%
        if llm.signal == SignalType.BUY: score += 4
        elif llm.signal == SignalType.SELL: score -= 4
        
        # Sentiment 20%
        score += (sent.score * 2) # sentiment score is -1 to 1, scaled to -2 to 2
        
        final_type = SignalType.HOLD
        if score > 3:
            final_type = SignalType.BUY
        elif score < -3:
            final_type = SignalType.SELL
            
        return Signal(
            symbol=symbol,
            type=final_type,
            strength=min(abs(score) / 10.0, 1.0),
            reason=f"Aggregated score: {score:.1f}",
            source="ENSEMBLE"
        )
