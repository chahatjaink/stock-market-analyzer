"""PortfolioGuru Configuration — Portfolio Holdings & Market Settings.

Edit this file to update your holdings and market preferences.
Changes take effect at the next scheduled run (9:00 AM IST, Mon-Fri).
"""

PORTFOLIO = {
    # -- STOCKS ---------------------------------------------------------------
    "RELIANCE": {
        "name": "Reliance Industries",
        "exchange": "NSE",
        "qty": 50,
        "avg_price": 2450.00,
        "asset_type": "stock",
        "market": "IN",
    },
    "INFY": {
        "name": "Infosys",
        "exchange": "NSE",
        "qty": 100,
        "avg_price": 1680.00,
        "asset_type": "stock",
        "market": "IN",
    },
    "HDFCBANK": {
        "name": "HDFC Bank",
        "exchange": "NSE",
        "qty": 30,
        "avg_price": 1720.00,
        "asset_type": "stock",
        "market": "IN",
    },

    # -- MUTUAL FUNDS ---------------------------------------------------------
    "PPFAS_FLEXI": {
        "name": "Parag Parikh Flexi Cap Fund - Direct Growth",
        "amfi_code": "122639",
        "units": 250.456,
        "avg_nav": 68.50,
        "asset_type": "mutual_fund",
        "market": "IN",
    },
    "MIRAE_LARGECAP": {
        "name": "Mirae Asset Large Cap Fund - Direct Growth",
        "amfi_code": "118834",
        "units": 500.000,
        "avg_nav": 110.25,
        "asset_type": "mutual_fund",
        "market": "IN",
    },
}


MARKETS_CONFIG = {
    # === INDIAN MARKET — DEFAULT, ALWAYS ACTIVE ==============================
    "IN": {
        "label": "Indian Market",
        "active": True,
        "default": True,
        "indices": [
            "NIFTY 50", "SENSEX", "NIFTY BANK", "NIFTY IT",
            "NIFTY PHARMA", "NIFTY AUTO", "NIFTY FMCG",
            "NIFTY MIDCAP 150", "NIFTY SMALLCAP 250",
        ],
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "sources": [
            "nseindia.com", "bseindia.com", "moneycontrol.com",
            "amfiindia.com", "screener.in",
        ],
        "analysis_depth": "full",
        "notes": (
            "Primary market. Includes FII/DII flows, RBI signals, "
            "SGX Nifty pre-open, top gainers/losers, sector rotation."
        ),
    },

    # === ADDITIVE MARKETS ====================================================

    "US": {
        "label": "US Market",
        "active": True,
        "indices": ["S&P 500", "NASDAQ 100", "Dow Jones", "VIX"],
        "currency": "USD",
        "timezone": "America/New_York",
        "sources": ["finance.yahoo.com", "marketwatch.com", "cnbc.com"],
        "analysis_depth": "summary",
        "notes": (
            "US market close data + overnight futures. Focus on IT and "
            "pharma ADRs that are correlated with Indian counterparts."
        ),
    },

    "EU": {
        "label": "European Markets",
        "active": False,
        "indices": ["FTSE 100", "DAX 40", "CAC 40", "Euro Stoxx 50"],
        "currency": "EUR/GBP",
        "timezone": "Europe/London",
        "sources": ["reuters.com", "ft.com"],
        "analysis_depth": "summary",
        "notes": (
            "Useful for global macro context. Include only when European "
            "markets have significant news that may impact Asian open."
        ),
    },

    "ASIA": {
        "label": "Asian Markets",
        "active": True,
        "indices": [
            "Nikkei 225", "Hang Seng", "SGX Nifty",
            "Shanghai Composite", "KOSPI",
        ],
        "currency": "Mixed",
        "timezone": "Asia/Tokyo",
        "sources": ["reuters.com", "bloomberg.com"],
        "analysis_depth": "summary",
        "notes": (
            "SGX Nifty is critical for Indian pre-open. Hang Seng and "
            "Shanghai signal China risk-on/off sentiment."
        ),
    },

    "CRYPTO": {
        "label": "Crypto",
        "active": False,
        "indices": ["BTC/USD", "ETH/USD", "BTC/INR", "Crypto Fear & Greed"],
        "currency": "USD",
        "timezone": "UTC",
        "sources": ["coinmarketcap.com", "coingecko.com"],
        "analysis_depth": "summary",
        "notes": (
            "Include only if you hold or plan to invest in crypto. "
            "Note: Crypto is not regulated by SEBI. Very high risk."
        ),
    },

    "COMMODITIES": {
        "label": "Commodities",
        "active": True,
        "indices": [
            "Gold (MCX)", "Silver (MCX)", "Crude Oil (MCX)",
            "Natural Gas", "Copper",
        ],
        "currency": "INR/USD",
        "timezone": "Asia/Kolkata",
        "sources": ["mcxindia.com", "moneycontrol.com"],
        "analysis_depth": "summary",
        "notes": (
            "Crude oil price is a key macro input for Indian markets. "
            "Gold correlates with USD/INR and serves as safe-haven signal."
        ),
    },

    "FOREX": {
        "label": "Forex",
        "active": True,
        "pairs": [
            "USD/INR", "EUR/INR", "GBP/INR", "JPY/INR",
            "DXY (Dollar Index)",
        ],
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "sources": ["rbi.org.in", "moneycontrol.com"],
        "analysis_depth": "summary",
        "notes": (
            "USD/INR movement directly impacts IT export earnings, "
            "import costs, and FII equity flows."
        ),
    },

    "BONDS": {
        "label": "Bonds & Fixed Income",
        "active": False,
        "indices": [
            "India 10Y Govt Bond Yield", "US 10Y Treasury",
            "RBI Repo Rate", "India Bond Yield Spread",
        ],
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "sources": ["rbi.org.in", "reuters.com"],
        "analysis_depth": "summary",
        "notes": (
            "Bond yields affect bank stocks and debt mutual fund NAVs. "
            "Include when RBI policy meetings are near."
        ),
    },
}
