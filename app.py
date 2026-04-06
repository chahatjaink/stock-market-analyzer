"""PortfolioGuru API — Trigger market briefing generation and email delivery."""

import os
from datetime import datetime

import pytz
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv(override=True)

from market_briefing import (
    build_email_prompt, generate_briefing, send_email,
    fetch_all_data,
)
from config import MARKETS_CONFIG, PORTFOLIO

app = FastAPI(title="PortfolioGuru API")
IST = pytz.timezone("Asia/Kolkata")


@app.post("/send-briefing")
def trigger_briefing():
    """Generate a market briefing with Gemini and send it via Resend."""
    now = datetime.now(IST)
    try:
        verified_data = fetch_all_data(PORTFOLIO, MARKETS_CONFIG)
        prompt = build_email_prompt(MARKETS_CONFIG, PORTFOLIO, verified_data)
        html = generate_briefing(prompt)
        subject = (
            f"Daily Market Briefing — "
            f"{now.strftime('%a, %d %b %Y')} | Powered by Gemini 2.5 Pro"
        )
        send_email(html, subject)
        return {
            "status": "sent",
            "recipient": os.environ["RECIPIENT_EMAIL"],
            "time": now.strftime("%I:%M %p IST"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
