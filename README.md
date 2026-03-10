# LLMAnalyze

A modular, SOLID Python bot for stock market analysis using LLMs, technical indicators, and news sentiment.

## Features
- **Technical Analysis**: RSI, MACD, Bollinger Bands, Moving Averages.
- **LLM Integration**: OpenAI (GPT-4) for interpreting signals and sentiment analysis.
- **News Sentiment**: Fetches real-time news and calculates sentiment.
- **FastAPI Backend**: A fully functional REST API.

## Setup
1. Clone the repository.
2. `uv pip install -e .` (veya development için `uv pip install -e .[dev]`)
3. Copy `.env.example` to `.env` and fill in your API keys (OpenAI, NewsAPI).
4. Run the API: `uvicorn src.presentation.api.main:app --reload`
