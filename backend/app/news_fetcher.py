"""News fetcher module — fetches from RSS feeds and optionally NewsAPI.org.

Runs every 10 minutes via APScheduler. Performs sentiment analysis using VADER.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import feedparser
import httpx
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.config import settings

logger = logging.getLogger(__name__)

# VADER sentiment analyzer (free, runs locally)
analyzer = SentimentIntensityAnalyzer()

# RSS feed sources (free, no API key, no rate limits)
RSS_FEEDS = [
    {"url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "source": "Economic Times"},
    {"url": "https://www.moneycontrol.com/rss/marketreports.xml", "source": "Moneycontrol"},
    {"url": "https://www.livemint.com/rss/markets", "source": "LiveMint"},
]

# Company name to symbol mapping for keyword matching
COMPANY_ALIASES: Dict[str, List[str]] = {
    "NSE:RELIANCE-EQ": ["reliance", "ril", "reliance industries"],
    "NSE:TCS-EQ": ["tcs", "tata consultancy"],
    "NSE:HDFCBANK-EQ": ["hdfc bank", "hdfcbank"],
    "NSE:INFY-EQ": ["infosys", "infy"],
    "NSE:ICICIBANK-EQ": ["icici bank", "icicibank"],
    "NSE:HINDUNILVR-EQ": ["hindustan unilever", "hul", "hindunilvr"],
    "NSE:ITC-EQ": ["itc"],
    "NSE:SBIN-EQ": ["sbi", "state bank"],
    "NSE:BHARTIARTL-EQ": ["bharti airtel", "airtel"],
    "NSE:KOTAKBANK-EQ": ["kotak", "kotak mahindra"],
    "NSE:LT-EQ": ["larsen", "l&t", "larsen & toubro"],
    "NSE:AXISBANK-EQ": ["axis bank"],
    "NSE:BAJFINANCE-EQ": ["bajaj finance"],
    "NSE:ASIANPAINT-EQ": ["asian paints"],
    "NSE:MARUTI-EQ": ["maruti", "maruti suzuki"],
    "NSE:HCLTECH-EQ": ["hcl tech", "hcl technologies"],
    "NSE:SUNPHARMA-EQ": ["sun pharma", "sun pharmaceutical"],
    "NSE:TITAN-EQ": ["titan"],
    "NSE:WIPRO-EQ": ["wipro"],
    "NSE:ULTRACEMCO-EQ": ["ultratech", "ultratech cement"],
    "NSE:NESTLEIND-EQ": ["nestle"],
    "NSE:BAJAJFINSV-EQ": ["bajaj finserv"],
    "NSE:ONGC-EQ": ["ongc"],
    "NSE:NTPC-EQ": ["ntpc"],
    "NSE:POWERGRID-EQ": ["power grid"],
    "NSE:M&M-EQ": ["mahindra", "m&m"],
    "NSE:TATAMOTORS-EQ": ["tata motors"],
    "NSE:TATASTEEL-EQ": ["tata steel"],
    "NSE:JSWSTEEL-EQ": ["jsw steel"],
    "NSE:ADANIENT-EQ": ["adani enterprises", "adani"],
    "NSE:ADANIPORTS-EQ": ["adani ports"],
    "NSE:COALINDIA-EQ": ["coal india"],
    "NSE:TECHM-EQ": ["tech mahindra"],
    "NSE:CIPLA-EQ": ["cipla"],
    "NSE:DRREDDY-EQ": ["dr reddy", "dr. reddy"],
    "NSE:EICHERMOT-EQ": ["eicher", "royal enfield"],
    "NSE:APOLLOHOSP-EQ": ["apollo hospitals"],
    "NSE:DIVISLAB-EQ": ["divi's", "divis lab"],
    "NSE:BPCL-EQ": ["bpcl", "bharat petroleum"],
    "NSE:BRITANNIA-EQ": ["britannia"],
    "NSE:HEROMOTOCO-EQ": ["hero motocorp", "hero"],
    "NSE:HINDALCO-EQ": ["hindalco"],
    "NSE:TATACONSUM-EQ": ["tata consumer"],
    "NSE:SBILIFE-EQ": ["sbi life"],
    "NSE:HDFCLIFE-EQ": ["hdfc life"],
    "NSE:BAJAJ-AUTO-EQ": ["bajaj auto"],
    "NSE:LTIM-EQ": ["lt mindtree", "ltim"],
    "NSE:SHRIRAMFIN-EQ": ["shriram finance"],
}


def match_symbols(headline: str) -> List[str]:
    """Match company names/aliases in a headline to symbols."""
    headline_lower = headline.lower()
    matched = []
    for symbol, aliases in COMPANY_ALIASES.items():
        for alias in aliases:
            if alias in headline_lower:
                matched.append(symbol)
                break
    # Also check for general market terms
    market_terms = ["nifty", "sensex", "market", "nse", "bse"]
    for term in market_terms:
        if term in headline_lower:
            if "NSE:NIFTY50-INDEX" not in matched:
                matched.append("MARKET")
            break
    return matched


def compute_sentiment(text: str) -> float:
    """Compute VADER sentiment compound score (-1 to +1)."""
    scores = analyzer.polarity_scores(text)
    return scores["compound"]


async def fetch_rss_news() -> List[Dict[str, Any]]:
    """Fetch news from all RSS feeds."""
    articles = []

    for feed_config in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_config["url"])
            for entry in feed.entries[:20]:  # Latest 20 per feed
                headline = entry.get("title", "")
                if not headline:
                    continue

                published = entry.get("published_parsed")
                pub_dt = None
                if published:
                    try:
                        pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                    except Exception:
                        pub_dt = datetime.now(timezone.utc)

                url = entry.get("link", "")
                summary = entry.get("summary", "")
                full_text = f"{headline} {summary}"

                sentiment = compute_sentiment(full_text)
                symbols = match_symbols(full_text)

                articles.append({
                    "headline": headline,
                    "source": feed_config["source"],
                    "published_at": pub_dt or datetime.now(timezone.utc),
                    "url": url,
                    "related_symbols": symbols if symbols else None,
                    "sentiment_score": sentiment,
                })
        except Exception as e:
            logger.error(f"Error fetching RSS from {feed_config['source']}: {e}")

    return articles


async def fetch_newsapi_news() -> List[Dict[str, Any]]:
    """Fetch news from NewsAPI.org (optional, requires API key)."""
    if not settings.NEWSAPI_KEY:
        return []

    articles = []
    queries = ["NSE stock market India", "NIFTY", "Indian stock market"]

    async with httpx.AsyncClient(timeout=30) as client:
        for query in queries:
            try:
                resp = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": query,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": 10,
                        "apiKey": settings.NEWSAPI_KEY,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for article in data.get("articles", []):
                        headline = article.get("title", "")
                        if not headline:
                            continue

                        pub_str = article.get("publishedAt", "")
                        pub_dt = None
                        if pub_str:
                            try:
                                pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                            except Exception:
                                pub_dt = datetime.now(timezone.utc)

                        description = article.get("description", "") or ""
                        full_text = f"{headline} {description}"
                        sentiment = compute_sentiment(full_text)
                        symbols = match_symbols(full_text)

                        articles.append({
                            "headline": headline,
                            "source": article.get("source", {}).get("name", "NewsAPI"),
                            "published_at": pub_dt or datetime.now(timezone.utc),
                            "url": article.get("url", ""),
                            "related_symbols": symbols if symbols else None,
                            "sentiment_score": sentiment,
                        })
            except Exception as e:
                logger.error(f"Error fetching NewsAPI for query '{query}': {e}")

    return articles


async def fetch_all_news() -> List[Dict[str, Any]]:
    """Fetch news from all sources."""
    rss_articles = await fetch_rss_news()
    newsapi_articles = await fetch_newsapi_news()

    # De-duplicate by headline
    seen = set()
    unique = []
    for article in rss_articles + newsapi_articles:
        headline = article["headline"].strip().lower()
        if headline not in seen:
            seen.add(headline)
            unique.append(article)

    return unique
