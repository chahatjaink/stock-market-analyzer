"""Programmatic market data for the non-Gemini path (no web search).

Sources (no API keys):
- yfinance: NSE stocks (.NS), global indices, FX, commodities proxies
- AMFI India: daily NAV file (https://www.amfiindia.com/spages/NAVAll.txt)

Fields not available from these sources remain null (e.g. FII/DII, Nifty
gainers/losers, Gift Nifty, analyst targets). The HTML step should show N/A.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

import requests
import yfinance as yf

AMFI_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

# Optional hints when AMC renames schemes (portfolio name -> extra match substrings)
_MF_EXTRA_TERMS: dict[str, tuple[str, ...]] = {
    "axis bluechip fund direct plan growth": (
        "axis large cap fund",
        "axis bluechip",
    ),
}

# Yahoo Finance symbols for macro / indices (best-effort; some are proxies).
_INDEX_YF = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY IT": "^CNXIT",
    "NIFTY PHARMA": "^CNXPHARMA",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Nikkei 225": "^N225",
    "Gold India 10g": "GOLDBEES.NS",  # listed gold ETF (proxy; not physical 10g)
    "Crude Oil": "CL=F",  # WTI USD/bbl
    "USD/INR": "USDINR=X",
    "India VIX": "INDIAVIX.NS",
}


def _safe_float(x: Any) -> float | None:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _rsi_closes(closes, period: int = 14) -> float | None:
    if closes is None or len(closes) < period + 1:
        return None
    series = closes.astype(float)
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    if avg_loss.iloc[-1] == 0:
        return 100.0 if avg_gain.iloc[-1] > 0 else None
    rs = avg_gain.iloc[-1] / avg_loss.iloc[-1]
    return float(100.0 - (100.0 / (1.0 + rs)))


def _normalize_name(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[-–—]+", " ", s)
    return s


def _download_amfi_nav_text() -> str:
    r = requests.get(
        AMFI_NAV_URL,
        timeout=60,
        headers={"User-Agent": "PortfolioGuru/1.0"},
    )
    r.raise_for_status()
    return r.text


def _parse_amfi_schemes(nav_text: str) -> list[tuple[str, float, str]]:
    """Return list of (scheme_name, nav, date_str)."""
    rows: list[tuple[str, float, str]] = []
    for line in nav_text.splitlines():
        line = line.strip()
        if not line or line.startswith("Open Ended") or line.startswith("Close Ended"):
            continue
        if line.count(";") < 5:
            continue
        parts = line.split(";")
        if len(parts) < 6:
            continue
        code = parts[0].strip()
        if not code.isdigit():
            continue
        name = parts[3].strip()
        nav_s = parts[4].strip()
        date_s = parts[5].strip()
        nav = _safe_float(nav_s)
        if nav is None or not name:
            continue
        rows.append((name, nav, date_s))
    return rows


def _best_amfi_match(
    target_name: str, schemes: list[tuple[str, float, str]]
) -> tuple[str, float, str] | None:
    t = _normalize_name(target_name)
    want_direct = "direct" in t
    want_growth = "growth" in t
    extras = _MF_EXTRA_TERMS.get(t, ())

    best: tuple[str, float, str] | None = None
    best_score = 0.0
    for name, nav, date_s in schemes:
        n = _normalize_name(name)
        score = SequenceMatcher(None, t, n).ratio()
        for hint in extras:
            if hint in n:
                score += 0.12
        if want_direct and "direct" in n:
            score += 0.08
        elif want_direct and "regular" in n:
            score -= 0.12
        if want_growth and "growth" in n:
            score += 0.08
        if want_growth and "idcw" in n:
            score -= 0.25
        if t[:18] and (t[:18] in n or n[:18] in t):
            score += 0.04
        if score > best_score:
            best_score = score
            best = (name, nav, date_s)
    if best is None or best_score < 0.42:
        return None
    return best


def _fetch_stock_row(symbol: str) -> dict[str, Any]:
    """One NSE stock: metrics from yfinance (best-effort)."""
    sym = symbol.strip().upper()
    t = yf.Ticker(f"{sym}.NS")
    out: dict[str, Any] = {
        "current_price": None,
        "previous_close": None,
        "day_change": None,
        "day_change_pct": None,
        "52w_high": None,
        "52w_low": None,
        "pe_ratio": None,
        "pb_ratio": None,
        "eps": None,
        "debt_to_equity": None,
        "roe": None,
        "market_cap_cr": None,
        "promoter_holding_pct": None,
        "fii_holding_pct": None,
        "dii_holding_pct": None,
        "50_dma": None,
        "200_dma": None,
        "rsi_14": None,
        "sector": None,
        "analyst_target_price": None,
        "analyst_rating": None,
        "recent_news": None,
    }
    try:
        info = t.info or {}
        hist = t.history(period="400d", auto_adjust=True)
    except Exception:
        return out

    if hist is not None and len(hist) > 0:
        close = hist["Close"]
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) > 1 else last
        out["current_price"] = round(last, 2)
        out["previous_close"] = round(prev, 2)
        out["day_change"] = round(last - prev, 2)
        out["day_change_pct"] = round(((last - prev) / prev) * 100, 2) if prev else None
        if len(close) >= 50:
            out["50_dma"] = round(float(close.iloc[-50:].mean()), 2)
        if len(close) >= 200:
            out["200_dma"] = round(float(close.iloc[-200:].mean()), 2)
        rsi = _rsi_closes(close, 14)
        if rsi is not None:
            out["rsi_14"] = round(rsi, 2)

    out["52w_high"] = _safe_float(info.get("fiftyTwoWeekHigh"))
    out["52w_low"] = _safe_float(info.get("fiftyTwoWeekLow"))
    if out["52w_high"] is not None:
        out["52w_high"] = round(out["52w_high"], 2)
    if out["52w_low"] is not None:
        out["52w_low"] = round(out["52w_low"], 2)

    out["pe_ratio"] = _safe_float(info.get("trailingPE") or info.get("forwardPE"))
    out["pb_ratio"] = _safe_float(info.get("priceToBook"))
    out["eps"] = _safe_float(info.get("trailingEps"))
    out["debt_to_equity"] = _safe_float(info.get("debtToEquity"))
    out["roe"] = _safe_float(info.get("returnOnEquity"))
    mcap = _safe_float(info.get("marketCap"))
    if mcap is not None:
        out["market_cap_cr"] = round(mcap / 1e7, 2)  # INR Cr

    out["sector"] = info.get("sector") or info.get("industry")

    # Holdings rarely populated for NSE on yfinance
    out["promoter_holding_pct"] = _safe_float(
        info.get("heldPercentInsiders")
    ) or _safe_float(info.get("percentHeldByInsiders"))
    out["fii_holding_pct"] = _safe_float(info.get("heldPercentInstitutions"))
    out["dii_holding_pct"] = None

    if out["current_price"] is None:
        out["current_price"] = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))

    return out


def _fetch_index_snapshot(label: str, yf_symbol: str) -> dict[str, Any]:
    row = {"value": None, "change": None, "change_pct": None}
    try:
        t = yf.Ticker(yf_symbol)
        hist = t.history(period="5d", auto_adjust=True)
        if hist is None or len(hist) < 1:
            return row
        close = hist["Close"]
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) > 1 else last
        row["value"] = round(last, 2)
        row["change"] = round(last - prev, 2)
        row["change_pct"] = round(((last - prev) / prev) * 100, 2) if prev else None
    except Exception:
        pass
    return row


def fetch_verified_data_programmatic(portfolio: dict) -> dict[str, Any]:
    """Build the same structure as Gemini step-1 JSON using public feeds."""
    stocks_out: dict[str, Any] = {}
    mfs_out: dict[str, Any] = {}

    for key, holding in portfolio.items():
        if holding.get("asset_type") == "stock":
            sym = holding.get("nse_symbol") or key
            stocks_out[key] = _fetch_stock_row(str(sym))

    amfi_text = ""
    schemes: list[tuple[str, float, str]] = []
    try:
        amfi_text = _download_amfi_nav_text()
        schemes = _parse_amfi_schemes(amfi_text)
    except Exception:
        schemes = []

    for key, holding in portfolio.items():
        if holding.get("asset_type") != "mutual_fund":
            continue
        name = holding.get("name") or key
        mfs_out[key] = {
            "current_nav": None,
            "nav_date": None,
            "return_1y": None,
            "return_3y": None,
            "return_5y": None,
            "aum_cr": None,
            "expense_ratio": None,
            "category_rank": None,
            "risk_rating": None,
        }
        if not schemes:
            continue
        match = _best_amfi_match(name, schemes)
        if match:
            _, nav, date_s = match
            mfs_out[key]["current_nav"] = round(float(nav), 4)
            mfs_out[key]["nav_date"] = date_s

    indices: dict[str, Any] = {}
    for label, ysym in _INDEX_YF.items():
        indices[label] = _fetch_index_snapshot(label, ysym)

    return {
        "stocks": stocks_out,
        "mutual_funds": mfs_out,
        "indices": indices,
        "fii_dii": {"fii_net_cr": None, "dii_net_cr": None, "date": None},
        "nifty_gainers": [],
        "nifty_losers": [],
        "gift_nifty": {"value": None, "change_pct": None},
        "india_vix": indices.get("India VIX", {}).get("value"),
        "top_news": [],
    }
