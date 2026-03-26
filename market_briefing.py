"""PortfolioGuru — Daily AI-powered market briefing.

Uses Gemini 2.5 Pro with Google Search grounding to generate a comprehensive
HTML email report covering Indian and global markets, portfolio analysis,
and actionable recommendations. Sent daily at 9:00 AM IST via Gmail.
"""

import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz
from google import genai
from google.genai import types

from config import MARKETS_CONFIG, PORTFOLIO

# -- Config -------------------------------------------------------------------
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASS = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENT_EMAIL = os.environ["RECIPIENT_EMAIL"]
MODEL = "gemini-2.5-pro-preview-06-05"

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)


# -- Prompt -------------------------------------------------------------------
def build_prompt(markets_config: dict, portfolio: dict) -> str:
    active_markets = {
        k: v for k, v in markets_config.items() if v.get("active")
    }
    return f"""
Today is {now.strftime('%A, %d %B %Y')}. Time: {now.strftime('%I:%M %p')} IST.

You are PortfolioGuru. Generate a complete daily market briefing HTML email.

=== ACTIVE MARKETS ===
{json.dumps(active_markets, indent=2)}

=== MY PORTFOLIO ===
{json.dumps(portfolio, indent=2)}

=== YOUR TASKS ===
1. Search and fetch live data for every active market listed above.
2. For Indian markets: fetch NIFTY 50, SENSEX, NIFTY BANK, sector indices,
   FII/DII data, top 5 gainers and losers.
3. For each active non-Indian market: fetch the primary index, top movers,
   and a 3-sentence outlook in the context of Indian investor interest.
4. Analyze market sentiment (Fear & Greed equivalent for each market).
5. Recommend 3-5 SHORT-TERM stocks (entry / target / stop-loss / risk rating).
6. Recommend 2-3 LONG-TERM investment ideas with fundamental metrics.
7. Analyze 3 mutual funds: performance, SIP action (BUY / HOLD / REVIEW).
8. Build the PORTFOLIO section using the portfolio data above - for each
   holding fetch the current price, compute unrealized P&L (INR and %),
   and give a one-line action: ADD / HOLD / TRIM / EXIT with brief reason.
9. Compile top 5 macro/financial news items relevant to an Indian investor.
10. Return ONLY a complete, valid HTML email. No markdown. No preamble.
    Start with <!DOCTYPE html> and end with </html>.

=== HTML EMAIL DESIGN SPEC ===
- Fonts: Google Font 'Outfit' (headings), 'Inter' (body) via @import
- Header: Deep navy background (#0A1628), white logo text "PortfolioGuru"
- Green (#00C853) = bullish / buy / gain
- Red (#FF1744)   = bearish / sell / loss
- Amber (#FFB300) = neutral / watch / caution
- Max width 600px, mobile responsive, single column on small screens
- Rounded cards (8px), subtle box-shadows, alternate-row table shading
- Sections with emoji headers: 📊 🟢 📈 📉 💼 🏦 🌍 📰 ⚠️
- End with SEBI disclaimer footer
"""


# -- Generate -----------------------------------------------------------------
def generate_briefing(prompt: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.3,
            max_output_tokens=8192,
        ),
    )
    html = response.text.strip()
    # Strip accidental markdown fences if model adds them
    if html.startswith("```"):
        html = html.split("```")[1]
        if html.startswith("html"):
            html = html[4:]
    return html.strip()


# -- Send Email ---------------------------------------------------------------
def send_email(html_body: str, subject: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASS)
        server.send_message(msg)


# -- Main ---------------------------------------------------------------------
if __name__ == "__main__":
    prompt = build_prompt(MARKETS_CONFIG, PORTFOLIO)
    html = generate_briefing(prompt)
    subject = (
        f"📊 Daily Market Briefing — "
        f"{now.strftime('%a, %d %b %Y')} | Powered by Gemini 2.5 Pro"
    )
    send_email(html, subject)
    print(f"✅ Briefing sent at {now.strftime('%I:%M %p IST')}")
