"""PortfolioGuru — Daily AI-powered market briefing.

Uses a two-step Gemini approach (only 2 API calls total):
  Step 1: Search & extract ALL verified data as JSON (stocks, MFs, indices).
  Step 2: Generate the HTML email using only the verified data.

Sent daily at 9:00 AM IST via Resend.
"""

import json
import os
import re
import time
from datetime import datetime

import pytz
import resend
from dotenv import load_dotenv

load_dotenv()
from google import genai
from google.genai import types

from config import MARKETS_CONFIG, PORTFOLIO

# -- Config -------------------------------------------------------------------
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
RECIPIENT_EMAIL = os.environ["RECIPIENT_EMAIL"]
MODEL = "gemini-2.5-flash"

IST = pytz.timezone("Asia/Kolkata")


# -- Gemini helper ------------------------------------------------------------
def _extract_json(text: str) -> dict:
    """Extract JSON object from text that may contain extra content."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    if start == -1:
        raise ValueError(f"No JSON found: {text[:300]}")

    for end_pos in range(len(text), start, -1):
        if text[end_pos - 1] == "}":
            try:
                return json.loads(text[start:end_pos])
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not parse JSON: {text[:300]}")


def _gemini_call(prompt: str, max_tokens: int = 16384,
                 parse_json: bool = False, retries: int = 2) -> str | dict:
    """Call Gemini with Google Search, with rate-limit retry."""
    client = genai.Client(api_key=GEMINI_API_KEY)

    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.0 if parse_json else 0.2,
                    max_output_tokens=max_tokens,
                ),
            )
            text = response.text.strip()
            if parse_json:
                return _extract_json(text)
            return text
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait = 60
                retry_match = re.search(r"retry\s+in\s+([\d.]+)s", err_str, re.I)
                if retry_match:
                    wait = int(float(retry_match.group(1))) + 5
                if attempt < retries:
                    print(f"    Rate limited. Waiting {wait}s before retry...")
                    time.sleep(wait)
                    continue
            if parse_json and ("JSONDecode" in err_str or "No JSON" in err_str):
                if attempt < retries:
                    print(f"    JSON parse error. Retrying...")
                    continue
            raise


# -- Step 1: Fetch ALL data ---------------------------------------------------
def fetch_all_data(portfolio: dict, markets_config: dict) -> dict:
    """Single Gemini call to fetch all verified market data."""
    stocks = {k: {"name": v.get("name", k),
                   "nse_symbol": v.get("nse_symbol", k),
                   "search_query": v.get("search_query", "")}
              for k, v in portfolio.items() if v.get("asset_type") == "stock"}

    mfs = {k: {"name": v.get("name", k),
                "search_query": v.get("search_query", "")}
           for k, v in portfolio.items() if v.get("asset_type") == "mutual_fund"}

    stock_names = "\n".join(
        f"- {k}: \"{v['name']}\" (NSE: {v['nse_symbol']})"
        + (f" — search: \"{v['search_query']}\"" if v['search_query'] else "")
        for k, v in stocks.items()
    )

    mf_names = "\n".join(
        f"- {k}: \"{v['name']}\""
        + (f" — search: \"{v['search_query']}\"" if v['search_query'] else "")
        for k, v in mfs.items()
    )

    prompt = f"""
You are a financial data researcher. Your ONLY job is to search the web and
return verified financial data as a JSON object.

CRITICAL RULES:
- Perform individual Google searches for each item.
- Every number MUST come from a search result. If not found, use null.
- Do NOT estimate, guess, or fabricate ANY number.
- Return ONLY a JSON object — no explanation, no markdown, no preamble.

=== TASK 1: STOCK DATA ===
For each stock, search "[Stock Name] NSE share price today" and
"[Stock Name] screener.in" or "[Stock Name] moneycontrol".

Stocks:
{stock_names}

For each stock return: current_price, previous_close, day_change,
day_change_pct, 52w_high, 52w_low, pe_ratio, pb_ratio, eps,
debt_to_equity, roe, market_cap_cr, promoter_holding_pct,
fii_holding_pct, dii_holding_pct, 50_dma, 200_dma, rsi_14,
sector, analyst_target_price, analyst_rating, recent_news (1 line).

=== TASK 2: MUTUAL FUND DATA ===
For each fund, search "[Fund Name] NAV moneycontrol" and
"[Fund Name] valueresearchonline".

Funds:
{mf_names}

For each fund return: current_nav, nav_date, return_1y, return_3y,
return_5y, aum_cr, expense_ratio, category_rank, risk_rating.

=== TASK 3: MARKET DATA ===
Search for today's values of: NIFTY 50, SENSEX, NIFTY BANK, NIFTY IT,
NIFTY PHARMA, S&P 500, NASDAQ, Nikkei 225, Gold India 10g, Crude Oil,
USD/INR, India VIX.
Search "FII DII data today" for flows.
Search "NIFTY 50 top gainers losers today" for top 5 each.
Search "Gift Nifty today" for SGX/Gift Nifty.
Search for 5 top financial news headlines for Indian investors.

=== REQUIRED JSON STRUCTURE ===
{{
  "stocks": {{
    "STOCK_KEY": {{
      "current_price": null, "previous_close": null,
      "day_change": null, "day_change_pct": null,
      "52w_high": null, "52w_low": null,
      "pe_ratio": null, "pb_ratio": null, "eps": null,
      "debt_to_equity": null, "roe": null, "market_cap_cr": null,
      "promoter_holding_pct": null, "fii_holding_pct": null,
      "dii_holding_pct": null, "50_dma": null, "200_dma": null,
      "rsi_14": null, "sector": null,
      "analyst_target_price": null, "analyst_rating": null,
      "recent_news": null
    }}
  }},
  "mutual_funds": {{
    "FUND_KEY": {{
      "current_nav": null, "nav_date": null,
      "return_1y": null, "return_3y": null, "return_5y": null,
      "aum_cr": null, "expense_ratio": null,
      "category_rank": null, "risk_rating": null
    }}
  }},
  "indices": {{
    "INDEX_NAME": {{ "value": null, "change": null, "change_pct": null }}
  }},
  "fii_dii": {{ "fii_net_cr": null, "dii_net_cr": null, "date": null }},
  "nifty_gainers": [ {{ "name": "", "price": null, "change_pct": null }} ],
  "nifty_losers": [ {{ "name": "", "price": null, "change_pct": null }} ],
  "gift_nifty": {{ "value": null, "change_pct": null }},
  "india_vix": null,
  "top_news": [ "" ]
}}

IMPORTANT: Include ALL {len(stocks)} stocks and ALL {len(mfs)} mutual funds.
Do NOT omit any. Output ONLY the JSON object, nothing else.
"""
    return _gemini_call(prompt, max_tokens=16384, parse_json=True)


# -- Step 2: Email generation -------------------------------------------------
def build_email_prompt(markets_config: dict, portfolio: dict,
                       verified_data: dict) -> str:
    now = datetime.now(IST)
    active_markets = {
        k: v for k, v in markets_config.items() if v.get("active")
    }

    # Compute P&L for stocks
    stocks_display = {}
    for key, holding in portfolio.items():
        if holding.get("asset_type") != "stock":
            continue
        sd = verified_data.get("stocks", {}).get(key, {})
        cp = sd.get("current_price")
        qty = holding.get("qty", 0)
        avg = holding.get("avg_price", 0)
        invested = round(qty * avg, 2)
        cur_val = round(qty * cp, 2) if cp else None
        pnl = round(cur_val - invested, 2) if cur_val else None
        pnl_pct = round((pnl / invested) * 100, 2) if pnl and invested else None
        stocks_display[key] = {
            **sd, "name": holding.get("name", key),
            "qty": qty, "avg_price": avg, "invested_value": invested,
            "current_value": cur_val, "unrealized_pnl": pnl,
            "unrealized_pnl_pct": pnl_pct,
        }

    # Compute P&L for mutual funds
    mfs_display = {}
    for key, holding in portfolio.items():
        if holding.get("asset_type") != "mutual_fund":
            continue
        md = verified_data.get("mutual_funds", {}).get(key, {})
        nav = md.get("current_nav")
        units = holding.get("units", 0)
        invested = holding.get("invested_value", 0)
        cur_val = round(units * nav, 2) if nav else None
        pnl = round(cur_val - invested, 2) if cur_val else None
        pnl_pct = round((pnl / invested) * 100, 2) if pnl and invested else None
        mfs_display[key] = {
            **md, "name": holding.get("name", key),
            "amc": holding.get("amc", ""), "category": holding.get("category", ""),
            "units": units, "invested_value": invested,
            "current_value": cur_val, "unrealized_pnl": pnl,
            "unrealized_pnl_pct": pnl_pct, "xirr": holding.get("xirr"),
        }

    return f"""
Today is {now.strftime('%A, %d %B %Y')}. Time: {now.strftime('%I:%M %p')} IST.

You are PortfolioGuru. Generate a complete daily market briefing HTML email.

=== ACTIVE MARKETS ===
{json.dumps(active_markets, indent=2)}

=== VERIFIED DATA (use EXACT numbers — do NOT change any value) ===

Indices: {json.dumps(verified_data.get("indices", {}), indent=2)}
FII/DII: {json.dumps(verified_data.get("fii_dii", {}), indent=2)}
NIFTY Gainers: {json.dumps(verified_data.get("nifty_gainers", []), indent=2)}
NIFTY Losers: {json.dumps(verified_data.get("nifty_losers", []), indent=2)}
Gift Nifty: {json.dumps(verified_data.get("gift_nifty", {}), indent=2)}
India VIX: {verified_data.get("india_vix")}
Stocks: {json.dumps(stocks_display, indent=2)}
Mutual Funds: {json.dumps(mfs_display, indent=2)}
News: {json.dumps(verified_data.get("top_news", []), indent=2)}

=== TASKS ===

CRITICAL: Use ONLY the numbers above. If null, show "N/A". NEVER invent data.

1. Index data table, FII/DII, gainers/losers, Gift Nifty, VIX.
2. Non-Indian market outlook (3 sentences each).
3. Market sentiment analysis.
4. 3-5 SHORT-TERM stock picks (entry/target/SL/risk).
5. 2-3 LONG-TERM ideas.

6. **PORTFOLIO DEEP ANALYSIS (MOST IMPORTANT):**

   For EACH stock:
   a) Price, day change, P&L (from data)
   b) 50-DMA, 200-DMA, RSI (from data)
   c) P/E, P/B, EPS, D/E, ROE, holdings (from data)
   d) Your analysis: trend, valuation vs peers
   e) News, analyst target (from data)
   f) ACTION: ADD/HOLD/TRIM/EXIT + reasoning
   g) RISK: Low/Medium/High/Very High

   For EACH mutual fund:
   a) NAV, P&L (from data)
   b) Returns 1Y/3Y/5Y (from data)
   c) AUM, expense ratio, rank (from data)
   d) SIP ACTION: BUY/HOLD/REVIEW/EXIT + reasoning
   e) 1-2 alternatives if underperforming

   DO NOT SKIP ANY HOLDING.

7. News headlines.
8. Return ONLY valid HTML. Start with <!DOCTYPE html>, end with </html>.

=== DESIGN ===
- Fonts: 'Outfit' headings, 'Inter' body via @import
- Header: #0A1628 navy, white "PortfolioGuru"
- Green (#00C853) bullish, Red (#FF1744) bearish, Amber (#FFB300) neutral
- 600px max, mobile responsive, rounded cards, alternating table rows
- Emoji section headers: 📊 🟢 📈 📉 💼 🏦 🌍 📰 ⚠️
- SEBI disclaimer footer
"""


def generate_briefing(prompt: str) -> str:
    """Step 2: Generate the HTML email."""
    result = _gemini_call(prompt, max_tokens=32768, parse_json=False)
    html = result.strip()
    if html.startswith("```"):
        html = html.split("```")[1]
        if html.startswith("html"):
            html = html[4:]
    return html.strip()


# -- Send Email ---------------------------------------------------------------
def send_email(html_body: str, subject: str):
    resend.api_key = RESEND_API_KEY
    resend.Emails.send({
        "from": "PortfolioGuru <onboarding@resend.dev>",
        "to": [RECIPIENT_EMAIL],
        "subject": subject,
        "html": html_body,
    })


# -- Main ---------------------------------------------------------------------
if __name__ == "__main__":
    now = datetime.now(IST)

    print("Step 1: Fetching all verified data via Gemini + Google Search...")
    verified_data = fetch_all_data(PORTFOLIO, MARKETS_CONFIG)
    stock_count = len(verified_data.get("stocks", {}))
    mf_count = len(verified_data.get("mutual_funds", {}))
    idx_count = len(verified_data.get("indices", {}))
    print(f"  -> {stock_count} stocks, {mf_count} MFs, {idx_count} indices")

    print("Step 2: Generating HTML email...")
    prompt = build_email_prompt(MARKETS_CONFIG, PORTFOLIO, verified_data)
    html = generate_briefing(prompt)

    subject = (
        f"Daily Market Briefing — "
        f"{now.strftime('%a, %d %b %Y')} | Powered by Gemini 2.5 Pro"
    )
    send_email(html, subject)
    print(f"Briefing sent at {now.strftime('%I:%M %p IST')}")
