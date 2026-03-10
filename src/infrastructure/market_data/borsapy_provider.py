import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Union
import logging

import borsapy as bp
import pandas as pd
from ...core.interfaces.market_data import IMarketDataProvider
from ...core.domain.models import OHLCV, StockInfo
from ...core.domain.enums import TimeFrame
from ...core.exceptions import MarketDataError

logger = logging.getLogger(__name__)


class BorsapyProvider(IMarketDataProvider):
    """Market data provider for Turkish BIST stocks using borsapy."""

    def _map_timeframe(self, tf: TimeFrame) -> str:
        """Map LLMAnalyze TimeFrame to borsapy period string."""
        mapping = {
            TimeFrame.D1: "1gün",
            TimeFrame.W1: "1hafta",
            TimeFrame.MO1: "1ay",
        }
        return mapping.get(tf, "1gün")

    def _map_period_short(self, tf: TimeFrame) -> str:
        """Map to shorter period for intraday."""
        mapping = {
            TimeFrame.M1: "1gün",
            TimeFrame.M5: "1gün",
            TimeFrame.M15: "1gün",
            TimeFrame.M30: "1gün",
            TimeFrame.H1: "1hafta",
            TimeFrame.D1: "1ay",
            TimeFrame.W1: "3ay",
            TimeFrame.MO1: "1yıl",
        }
        return mapping.get(tf, "1ay")

    def _convert_to_ohlcv(self, data: pd.DataFrame, symbol: str) -> List[OHLCV]:
        """Convert borsapy DataFrame to OHLCV list."""
        result = []
        try:
            if data is None or data.empty:
                return []

            for idx, row in data.iterrows():
                # Handle index as timestamp
                ts = idx
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                elif pd.isna(ts):
                    continue

                # Ensure timezone aware UTC
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                else:
                    ts = ts.astimezone(timezone.utc)

                # Extract OHLC values - borsapy uses Turkish column names
                try:
                    o = float(row.get('Açılış', row.get('Open', 0)))
                    h = float(row.get('Yüksek', row.get('High', 0)))
                    l = float(row.get('Düşük', row.get('Low', 0)))
                    c = float(row.get('Kapanış', row.get('Close', 0)))
                    v = int(row.get('Hacim', row.get('Volume', 0)))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse OHLC for {symbol}: {e}")
                    continue

                result.append(OHLCV(
                    timestamp=ts,
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    volume=v,
                ))
        except Exception as e:
            logger.error(f"Error converting data for {symbol}: {e}")
            raise MarketDataError(f"Failed to convert data for {symbol}: {e}") from e

        return result

    async def get_stock_data(
        self, symbol: str, timeframe: TimeFrame, limit: int = 100
    ) -> List[OHLCV]:
        """Fetches historical price and volume data for BIST stocks."""
        period = self._map_timeframe(timeframe)

        try:
            def _fetch():
                ticker = bp.Ticker(symbol)
                return ticker.history(period=period)

            data = await asyncio.to_thread(_fetch)

            if data is None or (hasattr(data, 'empty') and data.empty):
                return []

            # Limit the data
            if len(data) > limit:
                data = data.tail(limit)

            return self._convert_to_ohlcv(data, symbol)

        except Exception as e:
            logger.error(f"Error fetching data for {symbol} from borsapy: {e}")
            raise MarketDataError(f"Failed to fetch stock data for {symbol}: {e}") from e

    async def get_current_price(self, symbol: str) -> float:
        """Fetches the latest price for a BIST stock."""
        try:
            def _fetch():
                ticker = bp.Ticker(symbol)
                info = ticker.info
                if info is not None:
                    # EnrichedInfo has 'last' attribute
                    if hasattr(info, 'last'):
                        return float(info.last)
                    # Try dict-like access
                    if hasattr(info, 'get'):
                        return float(info.get('last', info.get('close', 0)))
                return 0.0

            return await asyncio.to_thread(_fetch)

        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            raise MarketDataError(f"Failed to fetch current price for {symbol}: {e}") from e

    async def get_stock_info(self, symbol: str) -> StockInfo:
        """Fetches company profile and basic info for BIST stocks."""
        try:
            def _fetch():
                ticker = bp.Ticker(symbol)
                info = ticker.info
                if info is None:
                    return StockInfo(symbol=symbol, company_name=symbol)

                # Use todict() to get dict from EnrichedInfo
                if hasattr(info, 'todict'):
                    data = info.todict()
                    return StockInfo(
                        symbol=symbol,
                        company_name=data.get('description', symbol),
                        sector=data.get('sector'),
                        industry=data.get('industry'),
                        market_cap=data.get('marketCap'),
                    )
                return StockInfo(symbol=symbol, company_name=symbol)

            return await asyncio.to_thread(_fetch)

        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            return StockInfo(symbol=symbol, company_name=symbol)
