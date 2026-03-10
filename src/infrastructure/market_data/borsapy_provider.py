import asyncio
from datetime import datetime, timezone
from typing import Any, List, Optional, Union
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

    async def get_stock_fundamentals(self, symbol: str) -> Optional[dict]:
        """Fetches fundamental analysis data (P/E, P/B, dividend yield, etc.) from borsapy."""
        try:
            def _fetch():
                ticker = bp.Ticker(symbol)
                info = ticker.info
                fast_info = ticker.fast_info

                if info is None and fast_info is None:
                    return None

                result = {}

                # Extract from info (EnrichedInfo)
                if info is not None:
                    data = info.todict() if hasattr(info, 'todict') else {}
                    logger.debug(f"Borsapy info keys for {symbol}: {list(data.keys()) if data else 'empty'}")

                    # Try multiple field names for P/E ratio
                    pe_value = (
                        data.get('pe_ratio') or
                        data.get('trailingPE') or
                        data.get('forwardPE') or
                        data.get('pe')
                    )

                    # Try multiple field names for P/B ratio
                    pb_value = (
                        data.get('pb_ratio') or
                        data.get('priceToBook') or
                        data.get('pb')
                    )

                    # Try multiple field names for dividend yield
                    div_value = (
                        data.get('dividend_yield') or
                        data.get('dividendYield') or
                        data.get('dividend_yield_percent')
                    )

                    result.update({
                        "pe_ratio": pe_value,
                        "pb_ratio": pb_value,
                        "dividend_yield": div_value,
                        "dividend_rate": data.get('dividend_rate'),
                        "eps": data.get('eps'),
                        "book_value": data.get('book_value'),
                        "market_cap": data.get('marketCap'),
                        "free_float": data.get('free_float'),
                        "foreign_ratio": data.get('foreign_ratio'),
                        "sector": data.get('sector'),
                        "industry": data.get('industry'),
                        "description": data.get('description'),
                        "website": data.get('website'),
                    })

                # Extract from fast_info
                if fast_info is not None:
                    fast_data = fast_info.todict() if hasattr(fast_info, 'todict') else {}
                    logger.debug(f"Borsapy fast_info keys for {symbol}: {list(fast_data.keys()) if fast_data else 'empty'}")
                    # Merge fast_info if not already present
                    for key in ['market_cap', 'free_float', 'foreign_ratio']:
                        if key not in result or result[key] is None:
                            result[key] = fast_data.get(key)

                # Clean up None values
                result = {k: v for k, v in result.items() if v is not None}

                logger.debug(f"Borsapy fundamentals result for {symbol}: {result}")
                return result if result else None

            return await asyncio.to_thread(_fetch)

        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return None

    async def get_analyst_data(self, symbol: str) -> Optional[dict]:
        """Fetches analyst price targets and recommendations from borsapy."""
        try:
            def _fetch():
                ticker = bp.Ticker(symbol)
                result = {}

                # Get analyst price targets - try multiple method names
                methods_tried = []
                targets_found = False

                for method_name in ['analyst_price_targets', 'analysis', 'analyst', 'price_targets']:
                    try:
                        methods_tried.append(method_name)
                        targets = getattr(ticker, method_name, None)
                        if targets is not None and targets != {}:
                            targets_dict = targets.todict() if hasattr(targets, 'todict') else (targets if isinstance(targets, dict) else {})
                            logger.debug(f"Borsapy analyst method '{method_name}' result for {symbol}: {targets_dict}")
                            result.update({
                                "target_low": targets_dict.get('low'),
                                "target_mid": targets_dict.get('mid'),
                                "target_high": targets_dict.get('high'),
                                "target_mean": targets_dict.get('mean'),
                            })
                            targets_found = True
                            break
                    except Exception as e:
                        logger.debug(f"Method '{method_name}' failed for {symbol}: {e}")

                if not targets_found:
                    logger.debug(f"Tried analyst methods {methods_tried} for {symbol}, none returned data")

                # Get recommendations summary - try multiple method names
                rec_methods_tried = []
                rec_found = False

                for method_name in ['recommendations_summary', 'recommendations', 'analyst_recommendations']:
                    try:
                        rec_methods_tried.append(method_name)
                        recommendations = getattr(ticker, method_name, None)
                        if recommendations is not None and recommendations != {}:
                            rec_dict = recommendations.todict() if hasattr(recommendations, 'todict') else (recommendations if isinstance(recommendations, dict) else {})
                            logger.debug(f"Borsapy recommendations method '{method_name}' result for {symbol}: {rec_dict}")
                            result.update({
                                "strong_buy": rec_dict.get('strongBuy', 0),
                                "buy": rec_dict.get('buy', 0),
                                "hold": rec_dict.get('hold', 0),
                                "sell": rec_dict.get('sell', 0),
                                "strong_sell": rec_dict.get('strongSell', 0),
                            })
                            rec_found = True
                            break
                    except Exception as e:
                        logger.debug(f"Method '{method_name}' failed for {symbol}: {e}")

                if not rec_found:
                    logger.debug(f"Tried recommendation methods {rec_methods_tried} for {symbol}, none returned data")

                logger.debug(f"Borsapy analyst_data result for {symbol}: {result}")
                return result if result else None

            return await asyncio.to_thread(_fetch)

        except Exception as e:
            logger.error(f"Error fetching analyst data for {symbol}: {e}")
            return None
