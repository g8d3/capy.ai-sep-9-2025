from __future__ import annotations

from typing import Dict, Any, Tuple
import os
import pandas as pd
import numpy as np
import pandas_ta as ta
import vectorbt as vbt


def compute_metrics_from_equity(equity: pd.Series, freq: str) -> Dict[str, float]:
    if equity.empty:
        return {}
    returns = equity.pct_change().dropna()
    total_return = equity.iloc[-1] / equity.iloc[0] - 1
    n_days = (equity.index[-1] - equity.index[0]).total_seconds() / 86400
    years = max(n_days / 365.25, 1e-9)
    cagr = (1 + total_return) ** (1 / years) - 1

    # annualization factor
    if freq in ("1h", "1H"):
        periods_per_year = 365 * 24
    else:
        periods_per_year = 252

    vol = returns.std() * np.sqrt(periods_per_year)
    sharpe = returns.mean() / returns.std() * np.sqrt(periods_per_year) if returns.std() != 0 else np.nan

    # max drawdown
    peak = equity.cummax()
    dd = (equity / peak - 1)
    max_dd = dd.min()
    calmar = (cagr / abs(max_dd)) if max_dd != 0 else np.nan

    return {
        "TotalReturn": float(total_return),
        "CAGR": float(cagr),
        "Sharpe": float(sharpe if np.isfinite(sharpe) else np.nan),
        "Volatility": float(vol if np.isfinite(vol) else np.nan),
        "MaxDD": float(max_dd),
        "Calmar": float(calmar if np.isfinite(calmar) else np.nan),
    }


def run_rsi_threshold(
    dfs: Dict[str, pd.DataFrame],
    timeframe: str,
    params: Dict[str, Any],
    fees_bps: float,
    slippage_bps: float,
) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    per_asset_metrics: Dict[str, Any] = {}
    equity_df = pd.DataFrame()
    trades_concat = []

    period = int(params.get("period", 14))
    lower = float(params.get("lower", 30))
    upper = float(params.get("upper", 70))
    fees = fees_bps / 10000.0
    slippage = slippage_bps / 10000.0

    for symbol, df in dfs.items():
        if df.empty:
            continue
        close = df["close"].copy()
        rsi = ta.rsi(close, length=period)
        entries = rsi < lower
        exits = rsi > upper

        pf = vbt.Portfolio.from_signals(
            close=close,
            entries=entries,
            exits=exits,
            fees=fees,
            slippage=slippage,
            freq="1H" if timeframe.lower() == "1h" else None,
            init_cash=100.0,
        )
        stats = pf.stats()
        trades = pf.trades.records_readable
        if isinstance(trades, pd.DataFrame) and not trades.empty:
            t = trades.copy()
            t["symbol"] = symbol
            trades_concat.append(t)

        # per-asset metrics
        per_asset_metrics[symbol] = {
            "CAGR": float(stats.get("CAGR", np.nan)),
            "Sharpe": float(stats.get("Sharpe Ratio", np.nan)),
            "MaxDD": float(stats.get("Max Drawdown [%]", np.nan)) / 100.0 if pd.notna(stats.get("Max Drawdown [%]", np.nan)) else np.nan,
            "WinRate": float(stats.get("Win Rate [%]", np.nan)) / 100.0 if pd.notna(stats.get("Win Rate [%]", np.nan)) else np.nan,
            "Exposure": float(stats.get("Exposure Time [%]", np.nan)) / 100.0 if pd.notna(stats.get("Exposure Time [%]", np.nan)) else np.nan,
            "Volatility": float(stats.get("Volatility (Ann.) [%]", np.nan)) / 100.0 if pd.notna(stats.get("Volatility (Ann.) [%]", np.nan)) else np.nan,
            "Calmar": float(stats.get("Calmar Ratio", np.nan)),
            "Trades": int(stats.get("Total Trades", 0) or 0),
            "TotalReturn": float(stats.get("Total Return [%]", np.nan)) / 100.0 if pd.notna(stats.get("Total Return [%]", np.nan)) else np.nan,
        }

        equity = pf.value()
        equity_df[symbol] = equity

    if equity_df.empty:
        agg_equity = pd.Series(dtype=float)
        trades_df = pd.DataFrame()
    else:
        # Equal-weight aggregate equity normalized to 1 at start
        norm = equity_df / equity_df.iloc[0]
        agg_equity = norm.mean(axis=1)
        trades_df = pd.concat(trades_concat, ignore_index=True) if trades_concat else pd.DataFrame()

    aggregate_metrics = compute_metrics_from_equity(agg_equity, timeframe)
    return {"aggregate": aggregate_metrics, "per_asset": per_asset_metrics}, agg_equity.to_frame(name="equity"), trades_df


def save_backtest_outputs(base_dir: str, backtest_id: int, equity_df: pd.DataFrame, trades_df: pd.DataFrame) -> Dict[str, str]:
    out_dir = os.path.join(base_dir, str(backtest_id))
    os.makedirs(out_dir, exist_ok=True)
    equity_path = os.path.join(out_dir, "equity.csv")
    trades_path = os.path.join(out_dir, "trades.csv")
    equity_df.to_csv(equity_path, index_label="timestamp")
    trades_df.to_csv(trades_path, index=False)
    return {"equity": equity_path, "trades": trades_path}
