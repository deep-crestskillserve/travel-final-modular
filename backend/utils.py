import os
import time
import httpx
from dotenv import load_dotenv
load_dotenv(override=True)
_access_token = None
_token_expiry = 0

async def get_access_token():
    """ Fetches OAuth2 access token from Amadeus API. """

    global _access_token, _token_expiry
    if _access_token and time.time() < _token_expiry:
        return _access_token

    AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
    AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
    if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
        raise ValueError("Amadeus API credentials not found")
    
    async with httpx.AsyncClient(timeout=float(os.getenv("HTTP_TIMEOUT", 90.0))) as client:
        token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": AMADEUS_CLIENT_ID,
            "client_secret": AMADEUS_CLIENT_SECRET,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = await client.post(token_url, data=payload, headers=headers)
        response.raise_for_status()        
        token_data = response.json()
    
    _access_token = token_data["access_token"]
    _token_expiry = time.time() + token_data["expires_in"] - 10
    return _access_token

def merge_flights_fields(data: dict) -> dict:
    """" Merging 'best_flights' and 'other_flights' into single 'flights' list. """

    best = data.get("best_flights", [])
    other = data.get("other_flights", [])

    if best or other:
        data["flights"] = best + other

    # Remove only if present
    data.pop("best_flights", None)
    data.pop("other_flights", None)

    return data
