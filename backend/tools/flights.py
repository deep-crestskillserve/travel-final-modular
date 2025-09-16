from langchain_core.tools import tool
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import httpx
from utils.logger import logger

logger = logger()

load_dotenv(override=True)

BASE_URL = "http://localhost:8000/api"

class FlightsInput(BaseModel):
    departure_id: str = Field(description='Departure airport code (IATA)')
    arrival_id: str = Field(description='Arrival airport code (IATA)')
    outbound_date: str = Field(description='Outbound date in YYYY-MM-DD format')
    adults: Optional[int] = Field(description="Number of adults", default=1)
    children: Optional[int] = Field(description="Number of children", default=0)
    return_date: Optional[str] = Field(description="Return date in YYYY-MM-DD format", default=None)

class FlightsInputSchema(BaseModel):
    params: FlightsInput

@tool(args_schema=FlightsInputSchema)
async def get_flights(params: FlightsInput):
    """
    Find flights using the Google Flights engine via SerpAPI.

    Args:
        params: FlightsInput object containing departure_id, arrival_id, outbound_date, adults, children, and optional return_date.

    Returns:
        dict: Flight search results containing 'best_flights' or error details.
    
    Raises:
        HTTPException: If the FastAPI server returns an error (e.g., invalid parameters or SerpAPI failure).
        httpx.RequestError: If there is a network error contacting the FastAPI server.
    """
    
    params_dict = params.model_dump(exclude_none=True)
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
        try:
            response = await client.get(f"{BASE_URL}/outbound-flights", params=params_dict)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"FastAPI server error: {e.response.status_code} - {e.response.text}")
            raise  # Propagate the error to the caller
        except httpx.RequestError as e:
            logger.error(f"Network error contacting FastAPI server: {e}")
            raise 