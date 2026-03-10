import json
import asyncio
from typing import Dict, List
from google import genai
from ...core.interfaces.llm_provider import ILLMProvider
from ...core.domain.models import (
    LLMAnalysisResult,
    SentimentResult,
    SignalType,
    Sentiment,
    AnalysisResult,
    NewsImpactAnalysis,
    NewsArticle,
    TrendingTopic,
)
from ...core.exceptions import LLMProviderError
from .prompts import (
    STOCK_ANALYSIS_SYSTEM_PROMPT,
    SENTIMENT_ANALYSIS_SYSTEM_PROMPT,
    PER_ARTICLE_SENTIMENT_PROMPT,
    NEWS_IMPACT_ANALYSIS_PROMPT,
    TRENDING_TOPICS_PROMPT,
)
import logging

logger = logging.getLogger(__name__)


class GeminiProvider(ILLMProvider):
    def __init__(self, api_key: str = "", model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set.")

        self.client = genai.Client(api_key=self.api_key) if self.api_key else genai.Client()
        self.model = model

    def _clean_json_response(self, text: str) -> str:
        """Cleans markdown JSON formatting from the response."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    def _call_gemini(self, prompt: str) -> str:
        """Synchronous Gemini API call — should be run via asyncio.to_thread."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return response.text

    async def analyze_stock(self, context_data: Dict) -> LLMAnalysisResult:
        """Analyzes stock data and technicals, returns JSON structured response."""
        user_prompt = (
            f"{STOCK_ANALYSIS_SYSTEM_PROMPT}\n\nAnalyze this data:\n"
            f"{json.dumps(context_data, default=str, indent=2)}"
        )

        try:
            raw_text = await asyncio.to_thread(self._call_gemini, user_prompt)

            result_json = self._clean_json_response(raw_text)
            data = json.loads(result_json)

            signal_str = data.get("signal", "HOLD").upper()
            try:
                signal = SignalType(signal_str)
            except ValueError:
                signal = SignalType.HOLD

            return LLMAnalysisResult(
                summary=data.get("summary", ""),
                signal=signal,
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                key_levels=data.get("key_levels", {}),
                provider="Gemini",
            )
        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned invalid JSON: {e}")
            raise LLMProviderError(f"Gemini returned invalid JSON: {e}") from e
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return LLMAnalysisResult(
                summary="Analysis failed due to an error.",
                signal=SignalType.HOLD,
                confidence=0.0,
                reasoning=str(e),
                provider="Gemini",
            )

    async def analyze_sentiment(self, texts: List[str]) -> SentimentResult:
        if not texts:
            return SentimentResult(
                overall_sentiment=Sentiment.NEUTRAL,
                score=0.0,
                key_themes=[],
                bullish_factors=[],
                bearish_factors=[],
            )

        combined_text = "\n\n".join(texts[:10])
        user_prompt = f"{SENTIMENT_ANALYSIS_SYSTEM_PROMPT}\n\nNews data:\n{combined_text}"

        try:
            raw_text = await asyncio.to_thread(self._call_gemini, user_prompt)

            result_json = self._clean_json_response(raw_text)
            data = json.loads(result_json)

            sentiment_str = data.get("overall_sentiment", "NEUTRAL").upper()
            try:
                sentiment = Sentiment(sentiment_str)
            except ValueError:
                sentiment = Sentiment.NEUTRAL

            return SentimentResult(
                overall_sentiment=sentiment,
                score=float(data.get("score", 0.0)),
                key_themes=data.get("key_themes", []),
                bullish_factors=data.get("bullish_factors", []),
                bearish_factors=data.get("bearish_factors", []),
            )
        except json.JSONDecodeError as e:
            logger.error(f"Gemini sentiment returned invalid JSON: {e}")
            return SentimentResult(
                overall_sentiment=Sentiment.NEUTRAL,
                score=0.0,
                key_themes=[],
                bullish_factors=[],
                bearish_factors=[],
            )
        except Exception as e:
            logger.error(f"Gemini sentiment analysis failed: {e}")
            return SentimentResult(
                overall_sentiment=Sentiment.NEUTRAL,
                score=0.0,
                key_themes=[],
                bullish_factors=[],
                bearish_factors=[],
            )

    async def analyze_article_sentiments(self, articles: List[Dict]) -> List[Dict]:
        if not articles:
            return []

        articles_text = "\n\n".join(
            f"[Article {i}]\nTitle: {a.get('title', '')}\nSummary: {a.get('summary', '')}"
            for i, a in enumerate(articles)
        )
        user_prompt = f"{PER_ARTICLE_SENTIMENT_PROMPT}\n\nArticles:\n{articles_text}"

        try:
            raw_text = await asyncio.to_thread(self._call_gemini, user_prompt)
            result_json = self._clean_json_response(raw_text)
            data = json.loads(result_json)

            if not isinstance(data, list):
                logger.warning("Gemini per-article sentiment did not return a list, falling back.")
                return [{"index": i, "sentiment": "NEUTRAL", "score": 0.0} for i in range(len(articles))]

            results = []
            for item in data:
                sent = item.get("sentiment", "NEUTRAL").upper()
                if sent not in ("BULLISH", "BEARISH", "NEUTRAL"):
                    sent = "NEUTRAL"
                score = float(item.get("score", 0.0))
                score = max(-1.0, min(1.0, score))
                
                results.append({
                    "index": item.get("index", len(results)),
                    "sentiment": sent,
                    "score": score,
                    "category": item.get("category", "GENERAL").upper(),
                    "keywords": item.get("keywords", []),
                    "relevance_score": float(item.get("relevance_score", 0.5)),
                })
            return results
        except Exception as e:
            logger.error(f"Gemini per-article sentiment failed: {e}")
            return [{"index": i, "sentiment": "NEUTRAL", "score": 0.0} for i in range(len(articles))]

    async def generate_report(self, analysis: AnalysisResult) -> str:
        """Generates a comprehensive markdown report using Gemini."""
        context = {
            "symbol": analysis.symbol,
            "timeframe": analysis.timeframe.value if analysis.timeframe else "N/A",
            "current_price": analysis.current_price,
            "technical_indicators": vars(analysis.technical_indicators) if analysis.technical_indicators else {},
            "technical_signal": {
                "type": analysis.technical_signal.type.value,
                "strength": analysis.technical_signal.strength,
                "reason": analysis.technical_signal.reason,
            } if analysis.technical_signal else {},
            "news_sentiment": {
                "overall": analysis.news_sentiment.overall_sentiment.value,
                "score": analysis.news_sentiment.score,
                "key_themes": analysis.news_sentiment.key_themes,
            } if analysis.news_sentiment else {},
            "llm_analysis": {
                "summary": analysis.llm_analysis.summary,
                "signal": analysis.llm_analysis.signal.value,
                "confidence": analysis.llm_analysis.confidence,
                "reasoning": analysis.llm_analysis.reasoning,
                "key_levels": analysis.llm_analysis.key_levels,
            } if analysis.llm_analysis else {},
            "contradictions": analysis.contradictions,
        }

        prompt = (
            f"{REPORT_GENERATION_SYSTEM_PROMPT}\n\n"
            f"Analysis data:\n{json.dumps(context, default=str, indent=2)}"
        )

        try:
            report = await asyncio.to_thread(self._call_gemini, prompt)
            return report
        except Exception as e:
            logger.error(f"Gemini report generation failed: {e}")
            # Fallback to simple report
            summary = analysis.llm_analysis.summary if analysis.llm_analysis else "No LLM summary available."
            return f"# Analysis Report for {analysis.symbol}\n\n{summary}"

    async def analyze_news_impact(self, symbol: str, articles: List[NewsArticle]) -> NewsImpactAnalysis:
        if not articles:
            return NewsImpactAnalysis(0.0, "No news", 1.0, "No articles provided.", [])

        articles_text = "\n\n".join(
            f"Title: {a.title}\nSummary: {a.summary or ''}"
            for a in articles[:10]
        )
        user_prompt = f"{NEWS_IMPACT_ANALYSIS_PROMPT.format(symbol=symbol)}\n\nNews:\n{articles_text}"

        try:
            raw_text = await asyncio.to_thread(self._call_gemini, user_prompt)
            result_json = self._clean_json_response(raw_text)
            data = json.loads(result_json)

            return NewsImpactAnalysis(
                impact_score=float(data.get("impact_score", 0.0)),
                price_impact_prediction=data.get("price_impact_prediction", "Mixed impact"),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                affected_sectors=data.get("affected_sectors", []),
            )
        except Exception as e:
            logger.error(f"Gemini news impact analysis failed: {e}")
            return NewsImpactAnalysis(0.0, "Error during analysis", 0.0, str(e), [])

    async def extract_trending_topics(self, articles: List[Dict], limit: int = 5) -> List[TrendingTopic]:
        if not articles:
            return []

        articles_text = "\n\n".join(
            f"Title: {a.get('title', '')}\nSummary: {a.get('summary', '')}"
            for a in articles[:50]
        )
        user_prompt = f"{TRENDING_TOPICS_PROMPT.format(limit=limit)}\n\nArticles:\n{articles_text}"

        try:
            raw_text = await asyncio.to_thread(self._call_gemini, user_prompt)
            result_json = self._clean_json_response(raw_text)
            data = json.loads(result_json)

            topics = []
            for item in data:
                sent_str = item.get("sentiment", "NEUTRAL").upper()
                try:
                    sentiment = Sentiment(sent_str)
                except ValueError:
                    sentiment = Sentiment.NEUTRAL

                topics.append(TrendingTopic(
                    topic=item.get("topic", "Unknown"),
                    mention_count=int(item.get("mention_count", 1)),
                    sentiment=sentiment,
                    related_symbols=item.get("related_symbols", [])
                ))
            return topics
        except Exception as e:
            logger.error(f"Gemini trending topics extraction failed: {e}")
            return []
