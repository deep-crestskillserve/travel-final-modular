import httpx
from datetime import date
from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from shared_utils.logger import get_logger

logger = get_logger()

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


def validate_dates_client_side(outbound_date: str, return_date: Optional[str] = None) -> Union[Dict[str, Any], None]:
    """
    Client-side validation for flight dates.
    Returns error dict if validation fails, None if valid.
    """
    try:
        today = date.today()
        outbound = date.fromisoformat(outbound_date)
        
        if outbound < today:
            return {
                "error": "invalid_date",
                "message": f"The outbound date ({outbound_date}) is in the past. Please select today ({today}) or a future date."
            }
        
        if return_date:
            try:
                return_d = date.fromisoformat(return_date)
            except ValueError:
                return {
                    "error": "invalid_date",
                    "message": f"Invalid return date format: {return_date}. Expected YYYY-MM-DD format."
                }
            
            if return_d <= outbound:
                return {
                    "error": "invalid_date",
                    "message": f"Return date ({return_date}) must be after outbound date ({outbound_date})."
                }
    except ValueError:
        return {
            "error": "invalid_date",
            "message": f"Invalid outbound date format: {outbound_date}. Expected YYYY-MM-DD format."
        }
    
    return None


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
    
    # Client-side date validation (defense in depth)
    date_error = validate_dates_client_side(params.outbound_date, params.return_date)
    if date_error:
        logger.warning(f"Client-side date validation failed: {date_error}")
        return date_error
    
    params_dict = params.model_dump(exclude_none=True)
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
        try:
            response = await client.get(f"{BASE_URL}/outbound-flights", params=params_dict)
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            logger.error(f"FastAPI server error: {e.response.status_code} - {e.response.text}")
            
            # Try to parse the error response
            try:
                error_detail = e.response.json()
                error_message = error_detail.get("detail", "Unknown error")
                
                # Handle validation errors (422)
                if e.response.status_code == 422:
                    return {
                        "error": "validation_error",
                        "message": str(error_message)
                    }
                
                # Handle bad request errors (400)
                if e.response.status_code == 400:
                    return {
                        "error": "invalid_request",
                        "message": str(error_message)
                    }
                
                # Handle gateway errors (502, 503)
                if e.response.status_code in [502, 503]:
                    return {
                        "error": "service_error",
                        "message": "Flight service is temporarily unavailable. Please try again later."
                    }
                
                # Generic error handling
                return {
                    "error": "api_error",
                    "message": f"Unable to fetch flights: {error_message}"
                }
            
            except Exception as parse_error:
                logger.error(f"Failed to parse error response: {parse_error}")
                return {
                    "error": "api_error",
                    "message": f"Unable to fetch flights. Server returned error: {e.response.status_code}"
                }
        
        except httpx.RequestError as e:
            logger.error(f"Network error contacting FastAPI server: {e}")
            return {
                "error": "network_error",
                "message": "Unable to connect to the flight search service. Please check your connection and try again."
            }
        
        except Exception as e:
            logger.error(f"Unexpected error in get_flights: {e}", exc_info=True)
            return {
                "error": "unexpected_error",
                "message": "An unexpected error occurred while searching for flights. Please try again."
            }