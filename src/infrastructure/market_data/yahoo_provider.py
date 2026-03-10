import asyncio
import yfinance as yf
from typing import List
from datetime import datetime, timedelta, timezone
from ...core.interfaces.market_data import IMarketDataProvider
from ...core.domain.models import OHLCV, StockInfo
from ...core.domain.enums import TimeFrame
from ...core.exceptions import MarketDataError
import logging

logger = logging.getLogger(__name__)


class YahooFinanceProvider(IMarketDataProvider):
    def _map_timeframe(self, tf: TimeFrame) -> str:
        mapping = {
            TimeFrame.M1: "1m",
            TimeFrame.M5: "5m",
            TimeFrame.M15: "15m",
            TimeFrame.M30: "30m",
            TimeFrame.H1: "1h",
            TimeFrame.D1: "1d",
            TimeFrame.W1: "1wk",
            TimeFrame.MO1: "1mo",
        }
        return mapping.get(tf, "1d")

    def _determine_period(self, tf: TimeFrame, limit: int) -> str:
        if tf in [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15, TimeFrame.M30]:
            return "1mo"
        elif tf in [TimeFrame.H1, TimeFrame.H4]:
            return "6mo"
        elif tf == TimeFrame.D1:
            return "2y"
        else:
            return "10y"

    async def get_stock_data(
        self, symbol: str, timeframe: TimeFrame, limit: int = 100
    ) -> List[OHLCV]:
        """Fetches historical price and volume data using yfinance."""
        interval = self._map_timeframe(timeframe)
        period = self._determine_period(timeframe, limit)

        try:
            def _fetch():
                ticker = yf.Ticker(symbol)
                return ticker.history(interval=interval, period=period)

            df = await asyncio.to_thread(_fetch)

            if df.empty:
                return []

            df = df.tail(limit)

            result = []
            for index, row in df.iterrows():
                ts = index.to_pydatetime()
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                else:
                    ts = ts.astimezone(timezone.utc)

                result.append(
                    OHLCV(
                        timestamp=ts,
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=int(row["Volume"]),
                    )
                )
            return result
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} from yfinance: {e}")
            raise MarketDataError(f"Failed to fetch stock data for {symbol}: {e}") from e

    async def get_current_price(self, symbol: str) -> float:
        try:
            def _fetch():
                ticker = yf.Ticker(symbol)
                return float(ticker.fast_info.get("lastPrice", 0.0))

            return await asyncio.to_thread(_fetch)
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            raise MarketDataError(f"Failed to fetch current price for {symbol}: {e}") from e

    async def get_stock_info(self, symbol: str) -> StockInfo:
        try:
            def _fetch():
                ticker = yf.Ticker(symbol)
                return ticker.info

            info = await asyncio.to_thread(_fetch)
            return StockInfo(
                symbol=symbol,
                company_name=info.get("shortName", symbol),
                sector=info.get("sector"),
                industry=info.get("industry"),
                market_cap=info.get("marketCap"),
            )
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            # Fallback with basic info
            return StockInfo(symbol=symbol, company_name=symbol)
