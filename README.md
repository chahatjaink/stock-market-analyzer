# PortfolioGuru

Daily AI-powered market briefing delivered to your inbox at 9:00 AM IST.

**Model:** Gemini 2.5 Flash | **Markets:** NSE/BSE India + Global | **Delivery:** Email via Resend + GitHub Actions

## How It Works

1. **Step 1:** Gemini searches Google for live market data (stock prices, NAVs, indices, FII/DII, technicals) and returns verified JSON.
2. **Step 2:** Gemini takes the verified data, computes P&L for your portfolio, and generates a comprehensive HTML email with analysis and recommendations.

Only **2 API calls** per briefing — fits within Gemini's free tier for daily use.

## Setup

### 1. Get API Keys

- **Gemini API Key** — [aistudio.google.com](https://aistudio.google.com)
- **Resend API Key** — [resend.com](https://resend.com)

### 2. Configure Environment Variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key |
| `RESEND_API_KEY` | Resend email API key |
| `RECIPIENT_EMAIL` | Email address to receive the daily briefing |
| `PORTFOLIO_JSON` | Your portfolio holdings as a JSON string (see below) |

### 3. Configure GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions, and add the same 4 variables as repository secrets:

- `GEMINI_API_KEY`
- `RESEND_API_KEY`
- `RECIPIENT_EMAIL`
- `PORTFOLIO_JSON`

### 4. Portfolio Format

`PORTFOLIO_JSON` is a single JSON string containing all your holdings. See `.env.example` for the full structure.

**Stock fields:**
```json
{
  "HDFCBANK": {
    "name": "HDFC Bank Ltd",
    "nse_symbol": "HDFCBANK",
    "exchange": "NSE",
    "qty": 12,
    "avg_price": 727.50,
    "asset_type": "stock",
    "market": "IN"
  }
}
```

**Mutual fund fields:**
```json
{
  "HDFC_MIDCAP": {
    "name": "HDFC Mid-Cap Opportunities Fund Direct Plan Growth",
    "amc": "HDFC Mutual Fund",
    "category": "Equity - Mid Cap",
    "units": 200.575,
    "invested_value": 39998.06,
    "asset_type": "mutual_fund",
    "market": "IN"
  }
}
```

Optional fields: `search_query` (helps Gemini find the right data), `nse_symbol`, `xirr`.

### 5. Customize Markets

In `config.py`, set `"active": True/False` for each market in `MARKETS_CONFIG` to control which markets appear in your briefing (US, Asia, Commodities, Forex, etc.).

### 6. Run

- **Automatic:** Runs Mon-Fri at 9:00 AM IST via GitHub Actions
- **Manual:** Go to Actions tab → "PortfolioGuru Daily Briefing" → Run workflow
- **Local:**
  ```bash
  pip install -r requirements.txt
  python market_briefing.py
  ```
- **API:**
  ```bash
  uvicorn app:app --reload
  curl -X POST http://localhost:8000/send-briefing
  ```

## What's in the Briefing

- **Market Overview** — NIFTY 50, SENSEX, NIFTY BANK, sector indices, FII/DII flows, top gainers/losers, India VIX
- **Global Markets** — S&P 500, NASDAQ, Nikkei, commodities, forex (USD/INR)
- **Portfolio Deep Analysis** — For each holding: current price, P&L, technicals (RSI, DMAs), fundamentals (P/E, ROE, D/E), FII/DII activity, analyst targets, and actionable recommendation (ADD/HOLD/TRIM/EXIT)
- **Mutual Fund Analysis** — NAV, returns vs benchmark, AUM, expense ratio, category rank, SIP action
- **Stock Picks** — Short-term and long-term recommendations
- **Top News** — 5 macro/financial headlines relevant to Indian investors

## File Structure

```
portfolioguru/
├── .github/workflows/daily-market-email.yml   # Scheduled automation
├── market_briefing.py                          # Main script (2-step Gemini)
├── config.py                                   # Market config + portfolio loader
├── app.py                                      # FastAPI endpoint
├── requirements.txt                            # Python dependencies
├── .env.example                                # Environment variable template
├── .gitignore
└── README.md
```

## Rate Limits

The free Gemini API tier allows 20 requests/day for gemini-2.5-flash. Each briefing uses 2 calls, so you can run up to 10 briefings per day. For higher limits, enable billing on your Google Cloud project.

## Disclaimer

PortfolioGuru is for educational and informational purposes only. This is NOT SEBI-registered investment advice. Always verify data independently and consult a qualified financial advisor before making investment decisions.
