import httpx
from langchain_core.tools import tool
from shared_utils.logger import get_logger

BASE_URL = "http://localhost:8000/api"

logger = get_logger()

@tool
async def get_airport(location: str):
    """
    Fetch the nearest airports information for a given location.
    Provides with IATA code required for making call to "get_flights" tools
    """

    payload = {"location": location}
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
        try:
            response = await client.get(f"{BASE_URL}/airports", params=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"FastAPI server error: {e.response.status_code} - {e.response.text}")
            raise  # Propagate the error to the caller
        except httpx.RequestError as e:
            logger.error(f"Network error contacting FastAPI server: {e}")
            raise 