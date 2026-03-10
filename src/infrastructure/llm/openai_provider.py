import json
from typing import Dict, List
from openai import AsyncOpenAI
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


class OpenAIProvider(ILLMProvider):
    def __init__(self, api_key: str = "", model: str = "gpt-4o"):
        self.api_key = api_key
        if not self.api_key:
            logger.warning("OPENAI_API_KEY is not set.")
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model

    async def _chat(self, system_prompt: str, user_content: str, temperature: float = 0.2, json_mode: bool = True) -> str:
        """Shared helper for OpenAI chat completions."""
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def analyze_stock(self, context_data: Dict) -> LLMAnalysisResult:
        """Analyzes stock data and technicals, returns JSON structured response."""
        user_prompt = f"Analyze this data:\n{json.dumps(context_data, default=str, indent=2)}"

        try:
            result_json = await self._chat(
                STOCK_ANALYSIS_SYSTEM_PROMPT, user_prompt, temperature=0.2
            )
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
                provider="OpenAI",
            )
        except json.JSONDecodeError as e:
            logger.error(f"OpenAI returned invalid JSON: {e}")
            raise LLMProviderError(f"OpenAI returned invalid JSON: {e}") from e
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return LLMAnalysisResult(
                summary="Analysis failed due to an error.",
                signal=SignalType.HOLD,
                confidence=0.0,
                reasoning=str(e),
                provider="OpenAI",
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

        try:
            result_json = await self._chat(
                SENTIMENT_ANALYSIS_SYSTEM_PROMPT, combined_text, temperature=0.1
            )
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
            logger.error(f"OpenAI sentiment returned invalid JSON: {e}")
            return SentimentResult(
                overall_sentiment=Sentiment.NEUTRAL,
                score=0.0,
                key_themes=[],
                bullish_factors=[],
                bearish_factors=[],
            )
        except Exception as e:
            logger.error(f"OpenAI sentiment analysis failed: {e}")
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

        system_prompt = (
            PER_ARTICLE_SENTIMENT_PROMPT
            + '\n\nWrap the array in a JSON object: {"results": [...]}'
        )

        try:
            result_json = await self._chat(
                system_prompt, articles_text, temperature=0.1
            )
            data = json.loads(result_json)
            items = data.get("results", data) if isinstance(data, dict) else data

            if not isinstance(items, list):
                logger.warning("OpenAI per-article sentiment did not return a list, falling back.")
                return [{"index": i, "sentiment": "NEUTRAL", "score": 0.0} for i in range(len(articles))]

            results = []
            for item in items:
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
            logger.error(f"OpenAI per-article sentiment failed: {e}")
            return [{"index": i, "sentiment": "NEUTRAL", "score": 0.0} for i in range(len(articles))]

    async def generate_report(self, analysis: AnalysisResult) -> str:
        """Generates a comprehensive markdown report using OpenAI."""
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

        user_content = f"Analysis data:\n{json.dumps(context, default=str, indent=2)}"

        try:
            report = await self._chat(
                REPORT_GENERATION_SYSTEM_PROMPT, user_content, temperature=0.3, json_mode=False
            )
            return report
        except Exception as e:
            logger.error(f"OpenAI report generation failed: {e}")
            summary = analysis.llm_analysis.summary if analysis.llm_analysis else "No LLM summary available."
            return f"# Analysis Report for {analysis.symbol}\n\n{summary}"

    async def analyze_news_impact(self, symbol: str, articles: List[NewsArticle]) -> NewsImpactAnalysis:
        if not articles:
            return NewsImpactAnalysis(0.0, "No news", 1.0, "No articles provided.", [])

        articles_text = "\n\n".join(
            f"Title: {a.title}\nSummary: {a.summary or ''}"
            for a in articles[:10]
        )
        system_prompt = NEWS_IMPACT_ANALYSIS_PROMPT.format(symbol=symbol)

        try:
            result_json = await self._chat(system_prompt, articles_text)
            data = json.loads(result_json)

            return NewsImpactAnalysis(
                impact_score=float(data.get("impact_score", 0.0)),
                price_impact_prediction=data.get("price_impact_prediction", "Mixed impact"),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                affected_sectors=data.get("affected_sectors", []),
            )
        except Exception as e:
            logger.error(f"OpenAI news impact analysis failed: {e}")
            return NewsImpactAnalysis(0.0, "Error during analysis", 0.0, str(e), [])

    async def extract_trending_topics(self, articles: List[Dict], limit: int = 5) -> List[TrendingTopic]:
        if not articles:
            return []

        articles_text = "\n\n".join(
            f"Title: {a.get('title', '')}\nSummary: {a.get('summary', '')}"
            for a in articles[:50]
        )
        system_prompt = TRENDING_TOPICS_PROMPT.format(limit=limit)

        try:
            result_json = await self._chat(system_prompt, articles_text)
            data = json.loads(result_json)
            
            # OpenAI might wrap in an object if we aren't careful, but prompt asks for array.
            # Response format json_object is used, so it might be {"topics": [...]} or just [...]
            items = data.get("topics", data) if isinstance(data, dict) else data

            topics = []
            for item in items:
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
            logger.error(f"OpenAI trending topics extraction failed: {e}")
            return []
