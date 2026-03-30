"""Fundamental data fetcher — scrapes Screener.in for key financial ratios.

Runs weekly. Uses requests + BeautifulSoup4 with a 3-second delay between requests.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Symbol to Screener.in company slug mapping
SYMBOL_TO_SCREENER: Dict[str, str] = {
    "NSE:RELIANCE-EQ": "RELIANCE",
    "NSE:TCS-EQ": "TCS",
    "NSE:HDFCBANK-EQ": "HDFCBANK",
    "NSE:INFY-EQ": "INFY",
    "NSE:ICICIBANK-EQ": "ICICIBANK",
    "NSE:HINDUNILVR-EQ": "HINDUNILVR",
    "NSE:ITC-EQ": "ITC",
    "NSE:SBIN-EQ": "SBIN",
    "NSE:BHARTIARTL-EQ": "BHARTIARTL",
    "NSE:KOTAKBANK-EQ": "KOTAKBANK",
    "NSE:LT-EQ": "LT",
    "NSE:AXISBANK-EQ": "AXISBANK",
    "NSE:BAJFINANCE-EQ": "BAJFINANCE",
    "NSE:ASIANPAINT-EQ": "ASIANPAINT",
    "NSE:MARUTI-EQ": "MARUTI",
    "NSE:HCLTECH-EQ": "HCLTECH",
    "NSE:SUNPHARMA-EQ": "SUNPHARMA",
    "NSE:TITAN-EQ": "TITAN",
    "NSE:WIPRO-EQ": "WIPRO",
    "NSE:ULTRACEMCO-EQ": "ULTRACEMCO",
    "NSE:NESTLEIND-EQ": "NESTLEIND",
    "NSE:BAJAJFINSV-EQ": "BAJAJFINSV",
    "NSE:ONGC-EQ": "ONGC",
    "NSE:NTPC-EQ": "NTPC",
    "NSE:POWERGRID-EQ": "POWERGRID",
    "NSE:M&M-EQ": "M%26M",
    "NSE:TATAMOTORS-EQ": "TATAMOTORS",
    "NSE:TATASTEEL-EQ": "TATASTEEL",
    "NSE:JSWSTEEL-EQ": "JSWSTEEL",
    "NSE:ADANIENT-EQ": "ADANIENT",
    "NSE:ADANIPORTS-EQ": "ADANIPORTS",
    "NSE:COALINDIA-EQ": "COALINDIA",
    "NSE:TECHM-EQ": "TECHM",
    "NSE:CIPLA-EQ": "CIPLA",
    "NSE:DRREDDY-EQ": "DRREDDY",
    "NSE:EICHERMOT-EQ": "EICHERMOT",
    "NSE:APOLLOHOSP-EQ": "APOLLOHOSP",
    "NSE:DIVISLAB-EQ": "DIVISLAB",
    "NSE:BPCL-EQ": "BPCL",
    "NSE:BRITANNIA-EQ": "BRITANNIA",
    "NSE:HEROMOTOCO-EQ": "HEROMOTOCO",
    "NSE:HINDALCO-EQ": "HINDALCO",
    "NSE:TATACONSUM-EQ": "TATACONSUM",
    "NSE:SBILIFE-EQ": "SBILIFE",
    "NSE:HDFCLIFE-EQ": "HDFCLIFE",
    "NSE:BAJAJ-AUTO-EQ": "BAJAJ-AUTO",
    "NSE:LTIM-EQ": "LTIM",
    "NSE:SHRIRAMFIN-EQ": "SHRIRAMFIN",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}


def _parse_number(text: str) -> Optional[float]:
    """Parse a numeric string, handling commas, percentages, and Cr/Lakh suffixes."""
    if not text:
        return None
    text = text.strip().replace(",", "").replace("%", "")
    multiplier = 1.0
    if text.endswith("Cr.") or text.endswith("Cr"):
        text = text.replace("Cr.", "").replace("Cr", "").strip()
        multiplier = 10_000_000  # 1 Crore = 10M
    elif text.endswith("Lakh"):
        text = text.replace("Lakh", "").strip()
        multiplier = 100_000
    try:
        return float(text) * multiplier
    except (ValueError, TypeError):
        return None


async def scrape_company(symbol: str) -> Optional[Dict[str, Any]]:
    """Scrape fundamental data for a single company from Screener.in."""
    screener_slug = SYMBOL_TO_SCREENER.get(symbol)
    if not screener_slug:
        return None

    url = f"https://www.screener.in/company/{screener_slug}/"

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code != 200:
                logger.warning(f"Screener returned {resp.status_code} for {symbol}")
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            data: Dict[str, Any] = {"symbol": symbol}

            # Parse the key ratios section
            ratios_list = soup.select("#top-ratios li")
            for li in ratios_list:
                name_el = li.select_one(".name")
                value_el = li.select_one(".number")
                if not name_el or not value_el:
                    continue

                name = name_el.get_text(strip=True).lower()
                value = value_el.get_text(strip=True)

                if "stock p/e" in name or "price to earning" in name:
                    data["pe_ratio"] = _parse_number(value)
                elif "book value" in name:
                    # PB ratio might need market price / book value
                    bv = _parse_number(value)
                    if bv:
                        data["book_value"] = bv
                elif "roe" in name or "return on equity" in name:
                    data["roe"] = _parse_number(value)
                elif "debt to equity" in name or "debt/equity" in name:
                    data["debt_to_equity"] = _parse_number(value)
                elif "market cap" in name:
                    data["market_cap"] = _parse_number(value)
                elif "eps" in name:
                    data["eps"] = _parse_number(value)
                elif "promoter" in name and "holding" in name:
                    data["promoter_holding"] = _parse_number(value)

            # Try to get PB ratio
            pb_elements = soup.find_all(string=re.compile(r"Price to book", re.I))
            for el in pb_elements:
                parent = el.find_parent()
                if parent:
                    num = parent.find_next(class_="number")
                    if num:
                        data["pb_ratio"] = _parse_number(num.get_text(strip=True))
                        break

            return data

    except Exception as e:
        logger.error(f"Error scraping {symbol}: {e}")
        return None


async def fetch_all_fundamentals() -> List[Dict[str, Any]]:
    """Fetch fundamental data for all NIFTY 50 stocks with rate limiting."""
    results = []

    for symbol in SYMBOL_TO_SCREENER:
        try:
            data = await scrape_company(symbol)
            if data:
                results.append(data)
                logger.info(f"Scraped fundamentals for {symbol}")
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")

        # 3-second delay between requests
        await asyncio.sleep(3)

    return results
