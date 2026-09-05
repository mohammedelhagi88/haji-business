"""Trading analysis and safety-gated orchestration module."""

from .approval import ApprovedTrade, TradingApprovalBridge
from .binance_market import BinancePublicMarketData
from .broker import Broker, ExecutionResult, PaperBroker
from .config import TradingConfig
from .engine import MarketSnapshot, TradingEngine
from .indicators import atr, bollinger_bands, ema, obv, rsi, sma, vwap, wma
from .market_data import MarketBar, MarketDataProvider, MarketSnapshotRequest, validate_bars
from .selector import TradeCandidate, TradeSelector, build_levels
from .service import TradeOpportunity, TradingService
from .signals import SignalResult, composite_signal

__all__ = [
    "TradingConfig", "MarketSnapshot", "TradingEngine", "TradeCandidate",
    "TradeSelector", "SignalResult", "build_levels", "composite_signal",
    "TradingApprovalBridge", "ApprovedTrade", "TradingService", "TradeOpportunity",
    "MarketBar", "MarketDataProvider", "MarketSnapshotRequest", "validate_bars",
    "BinancePublicMarketData", "Broker", "ExecutionResult", "PaperBroker",
    "atr", "bollinger_bands", "ema", "obv", "rsi", "sma", "vwap", "wma",
]
