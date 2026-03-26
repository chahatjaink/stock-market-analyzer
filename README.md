# PortfolioGuru

Daily AI-powered market briefing delivered to your inbox at 9:00 AM IST.

**Model:** Gemini 2.5 Pro | **Markets:** NSE/BSE India + Global | **Delivery:** Gmail via GitHub Actions

## Setup

### 1. Get API Keys

- **Gemini API Key** — [aistudio.google.com](https://aistudio.google.com)
- **Gmail App Password** — Google Account → Security → 2-Step Verification → App Passwords

### 2. Configure GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions, and add:

| Secret | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key |
| `GMAIL_USER` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not your regular password) |
| `RECIPIENT_EMAIL` | Email address to receive the daily briefing |

### 3. Update Your Portfolio

Edit `config.py` to add/remove your stock and mutual fund holdings. Changes take effect at the next scheduled run.

### 4. Customize Markets

In `config.py`, set `"active": True/False` for each market in `MARKETS_CONFIG` to control which markets appear in your briefing.

### 5. Run

- **Automatic:** Runs Mon-Fri at 9:00 AM IST via GitHub Actions
- **Manual:** Go to Actions tab → "PortfolioGuru Daily Briefing" → Run workflow
- **Local:** Set env vars and run `python market_briefing.py`

## File Structure

```
portfolioguru/
├── .github/workflows/daily-market-email.yml   # Scheduled automation
├── market_briefing.py                          # Main script
├── config.py                                   # Portfolio & market config
├── requirements.txt                            # Python dependencies
└── README.md
```

## Disclaimer

PortfolioGuru is for educational and informational purposes only. This is NOT SEBI-registered investment advice. Always verify data independently and consult a qualified financial advisor before making investment decisions.
