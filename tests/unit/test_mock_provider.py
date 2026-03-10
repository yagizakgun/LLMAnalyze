import pytest
from src.infrastructure.llm.mock_provider import MockLLMProvider
from src.core.domain.models import LLMAnalysisResult, SentimentResult
from src.core.domain.enums import SignalType, Sentiment


@pytest.mark.asyncio
async def test_mock_analyze_stock():
    provider = MockLLMProvider()
    result = await provider.analyze_stock({"symbol": "AAPL"})
    assert isinstance(result, LLMAnalysisResult)
    assert result.signal == SignalType.BUY
    assert result.provider == "Mock"
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.summary, str)
    assert isinstance(result.reasoning, str)
    assert isinstance(result.key_levels, dict)


@pytest.mark.asyncio
async def test_mock_analyze_sentiment():
    provider = MockLLMProvider()
    result = await provider.analyze_sentiment(["Good earnings report"])
    assert isinstance(result, SentimentResult)
    assert result.overall_sentiment == Sentiment.BULLISH
    assert isinstance(result.bullish_factors, list)
    assert isinstance(result.bearish_factors, list)
    assert isinstance(result.key_themes, list)
    assert -1.0 <= result.score <= 1.0


@pytest.mark.asyncio
async def test_mock_generate_report():
    provider = MockLLMProvider()
    report = await provider.generate_report(None)
    assert isinstance(report, str)
    assert len(report) > 0


@pytest.mark.asyncio
async def test_mock_analyze_article_sentiments():
    provider = MockLLMProvider()
    articles = [
        {"title": "Stock surges on earnings beat", "summary": "Company reports strong Q4"},
        {"title": "Market drops amid recession fears", "summary": "Economic data disappoints"},
        {"title": "Fed holds rates steady", "summary": "No change in monetary policy"},
    ]
    result = await provider.analyze_article_sentiments(articles)
    assert isinstance(result, list)
    assert len(result) == 3
    for item in result:
        assert "index" in item
        assert "sentiment" in item
        assert "score" in item
        assert item["sentiment"] in ("BULLISH", "NEUTRAL", "BEARISH")
        assert -1.0 <= item["score"] <= 1.0
    # Verify different sentiments (mock cycles through BULLISH, NEUTRAL, BEARISH)
    assert result[0]["sentiment"] == "BULLISH"
    assert result[1]["sentiment"] == "NEUTRAL"
    assert result[2]["sentiment"] == "BEARISH"


@pytest.mark.asyncio
async def test_mock_analyze_article_sentiments_empty():
    provider = MockLLMProvider()
    result = await provider.analyze_article_sentiments([])
    assert result == []
