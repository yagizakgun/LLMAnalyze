# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLMAnalyze is a modular stock market analysis application that combines technical analysis, LLM-powered insights, and news sentiment to generate trading signals. It provides a FastAPI REST API for analyzing stock symbols.

## Common Commands

```bash
# Install in development mode
uv pip install -e .

# Install with dev dependencies (testing, linting)
uv pip install -e ".[dev]"

# Run the API server
uvicorn src.presentation.api.main:app --reload

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Format code
black .
isort .

# Type checking
mypy src
```

## Architecture

The project follows a layered, SOLID architecture:

```
src/
├── application/services/     # Application layer - orchestrates use cases
├── core/                    # Domain layer - models, interfaces, config
│   ├── domain/             # Domain models and enums
│   └── interfaces/        # Abstract contracts (IMarketDataProvider, ILLMProvider, etc.)
├── infrastructure/          # Infrastructure layer - implementations
│   ├── analysis/          # Technical analysis engine (TA)
│   ├── llm/               # LLM providers (OpenAI, Gemini, Mock)
│   ├── market_data/       # Yahoo Finance integration
│   └── news/              # NewsAPI integration
└── presentation/api/      # Presentation layer - FastAPI
```

### Key Components

| Component | Path | Purpose |
|-----------|------|---------|
| AnalysisService | `src/application/services/analysis_service.py` | Orchestrates full analysis pipeline |
| TAEngine | `src/infrastructure/analysis/ta_engine.py` | Calculates technical indicators (RSI, MACD, Bollinger Bands, SMA, EMA, ATR) |
| LLM Factory | `src/infrastructure/llm/factory.py` | Factory for creating LLM providers |
| YahooFinanceProvider | `src/infrastructure/market_data/yahoo_provider.py` | Market data from Yahoo Finance |
| Config | `src/core/config.py` | Pydantic-based settings management |

### API Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/analysis/{symbol}` - Analyze a stock symbol

### Signal Generation

The system combines three weighted signals:
- Technical analysis (40%)
- LLM analysis (40%)
- News sentiment (20%)

## Configuration

Settings are managed via Pydantic in `src/core/config.py` and loaded from `.env` file:

- `OPENAI_API_KEY`, `GEMINI_API_KEY` - LLM provider keys
- `NEWSAPI_KEY` - NewsAPI key
- `REDIS_URL` - Cache server URL
- `API_HOST`, `API_PORT` - Server configuration

## Dependencies

- **FastAPI** + **uvicorn** for the web framework
- **ta** library for technical analysis indicators
- **yfinance** for market data
- **openai** and **google-genai** for LLM integration
- **SQLAlchemy** + **aiosqlite** for async database
- **redis** for caching
