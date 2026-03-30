"""Option chain API router."""

from fastapi import APIRouter, Query

from app.fyers_client import fyers_client

router = APIRouter(prefix="/api/optionchain", tags=["optionchain"])


@router.get("")
async def get_option_chain(
    symbol: str = Query(..., description="Underlying symbol, e.g. NIFTY or BANKNIFTY"),
    expiry: str = Query("", description="Expiry date YYYY-MM-DD"),
):
    """Fetch full option chain with OI and greeks from Fyers."""
    try:
        data = fyers_client.get_option_chain(symbol, expiry)
        return data
    except Exception as e:
        return {"error": str(e)}
