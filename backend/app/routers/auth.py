"""Fyers authentication API router."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse

from app.fyers_client import fyers_client

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/fyers/url")
async def get_fyers_auth_url():
    """Generate and return the Fyers OAuth2 login URL."""
    try:
        url = fyers_client.get_auth_url()
        return {"auth_url": url}
    except Exception as e:
        return {"error": str(e)}


@router.get("/fyers/callback")
async def fyers_callback(
    auth_code: str = Query(None, alias="auth_code"),
    s: str = Query(None),  # Fyers may use 's' param
    code: str = Query(None),
):
    """Handle Fyers OAuth2 callback and exchange auth code for access token."""
    code_val = auth_code or s or code
    if not code_val:
        return {"error": "No auth code received"}

    try:
        token = fyers_client.exchange_auth_code(code_val)
        return {
            "status": "success",
            "message": "Authentication successful. Token stored.",
            "token_preview": token[:20] + "..." if len(token) > 20 else token,
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/fyers/status")
async def fyers_status():
    """Check if Fyers is authenticated."""
    return {
        "authenticated": fyers_client.access_token is not None,
        "client_id": fyers_client.client_id,
    }


@router.post("/fyers/token")
async def set_fyers_token(request: Request):
    """Manually set access token (for dev/testing)."""
    body = await request.json()
    token = body.get("access_token", "")
    if token:
        fyers_client.set_access_token(token)
        return {"status": "success", "message": "Token set successfully"}
    return {"error": "No token provided"}
