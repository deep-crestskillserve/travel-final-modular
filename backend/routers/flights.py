import os
import json
import httpx
import urllib.parse
from datetime import date
from typing import Optional, Union
from dotenv import load_dotenv
from shared_utils.logger import get_logger
from backend.utils import merge_flights_fields
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError

logger = get_logger()

load_dotenv(override=True)
router = APIRouter(prefix="/api", tags=["flights"])

serpapi_key = os.getenv("SERPAPI_API_KEY")
if not serpapi_key:
    raise ValueError("SERPAPI_API_KEY environment variable is not set")

BASE_URL = "https://serpapi.com/search.json"
SERPAPI_PARAMETERS = {
    'api_key': serpapi_key,
    'engine': 'google_flights',
    'hl': 'en',
    'gl': 'in',
    'currency': 'INR',
    'deep_search': 'true'
}

class FlightsInput(BaseModel):
    departure_id: str = Field(description='Departure airport code (IATA)')
    arrival_id: str = Field(description='Arrival airport code (IATA)')
    outbound_date: str = Field(description='Outbound date in YYYY-MM-DD format')
    adults: Optional[int] = Field(description="Number of adults", default=1)
    children: Optional[int] = Field(description="Number of children", default=0)
    return_date: Optional[str] = Field(description="Return date in YYYY-MM-DD format", default=None)

    @field_validator("adults", "children", mode="before")
    def validate_integers(cls, v):
        """Ensure that adults and children value is an integer and not a decimal."""
        if isinstance(v, float):
            if v.is_integer():
                return int(v)
            raise ValueError("Value must be a whole number, not a decimal")
        if isinstance(v, str):
            try:
                f = float(v)
                if f.is_integer():
                    return int(f)
                raise ValueError
            except ValueError:
                raise ValueError("Value must be a whole number string, not a decimal")
        return v
    
    @model_validator(mode="before")
    def validate_dates(self):
        """Validate that outbound_date is greater than current date and return_date(if provided) is greater than outbound_date"""
        today = date.today()
        try:
            outbound = date.fromisoformat(self["outbound_date"])
        except (ValueError, KeyError):
            raise ValueError("Invalid outbound_date format. Expected YYYY-MM-DD")
        
        if outbound < today:
            raise ValueError(f"Outbound date ({self['outbound_date']}) cannot be in the past. Please select today or a future date.")
        
        if self.get("return_date"):
            try:
                return_d = date.fromisoformat(self["return_date"])
            except ValueError:
                raise ValueError("Invalid return_date format. Expected YYYY-MM-DD")
            if return_d <= outbound:
                raise ValueError("Return date must be greater than outbound date")
        return self


class ReturnFlightsInput(FlightsInput):
    departure_token: Optional[str] = Field(description="Token for getting return flights", default=None)


class FlightBookingInput(FlightsInput):
    booking_token: Optional[str] = Field(description="Token for flight booking options", default=None)


async def fetch_flights_data(params: Union[FlightsInput, FlightBookingInput, ReturnFlightsInput]):
    """Fetch flight data from SerpAPI based on the provided parameters for outbound flights, return flights, or booking options."""

    params_dict = params.model_dump()
    if params_dict.get("return_date"):
        params_dict["type"] = 1
    else:
        params_dict.pop("return_date", None)
        params_dict["type"] = 2

    if "departure_token" in params_dict and params_dict["departure_token"]:
        params_dict["departure_token"] = urllib.parse.unquote(params_dict["departure_token"])
    if "booking_token" in params_dict and params_dict["booking_token"]:
        params_dict["booking_token"] = urllib.parse.unquote(params_dict["booking_token"])

    query_params = SERPAPI_PARAMETERS | params_dict

    url = f"{BASE_URL}?{urllib.parse.urlencode(query_params, safe='=+/')}"

    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            response_data = response.json()
            return merge_flights_fields(response_data)
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_json = e.response.json()
                if "error" in error_json:
                    error_detail = error_json["error"]
            except:
                pass
            
            logger.error(f"HTTP error from SerpAPI: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=400 if e.response.status_code == 400 else 502,
                detail=f"Flight search failed: {error_detail}. Please verify your search parameters."
            )
        except ValueError as e:
            logger.error(f"Failed to parse SerpAPI response as JSON: {e}")
            raise HTTPException(status_code=502, detail="Failed to parse API response")
        except httpx.RequestError as e:
            logger.error(f"Request error when contacting SerpAPI: {e}")
            raise HTTPException(status_code=503, detail="Flight service temporarily unavailable")


@router.get("/outbound-flights")
async def get_outbound_flights(
    departure_id: str = Query(description="Departure airport code (IATA)"),
    arrival_id: str = Query(description="Arrival airport code (IATA)"),
    outbound_date: str = Query(description="Outbound date in YYYY-MM-DD format"),
    adults: Optional[int] = Query(description="Number of adults", default=1),
    children: Optional[int] = Query(description="Number of children", default=0),
    return_date: Optional[str] = Query(description="Return date in YYYY-MM-DD format", default=None)
):
    """
    ## Retrieve a list of outbound flights

    ### Query Parameters
    - **departure_id**: IATA code of departure airport  
    - **arrival_id**: IATA code of arrival airport  
    - **adults**: Number of adults travelling  
    - **children**: Number of children travelling  
    - **outbound_date**: Outbound date in YYYY-MM-DD format  
    - **return_date**: Return date in YYYY-MM-DD format  

    ### Returns
    JSON response with:
    - search_metadata
    - search_parameters
    - price_insights  
    - airports  
    - flights

    ### Raises
    - **HTTPException**: If the params are invalid or SerpAPI fails  
    """
    
    try:
        params = FlightsInput(
            departure_id=departure_id,
            arrival_id=arrival_id,
            outbound_date=outbound_date,
            adults=adults,
            children=children,
            return_date=return_date
        )
    except ValidationError as e:
        logger.warning(f"Validation error in outbound flights: {e}")
        # Extract user-friendly messages
        error_messages = []
        for error in e.errors():
            if "Value error" in str(error.get("msg", "")):
                # Extract the actual validation message
                error_messages.append(str(error["msg"]))
            else:
                error_messages.append(f"{error['loc'][0]}: {error['msg']}")
        
        raise HTTPException(
            status_code=422,
            detail="; ".join(error_messages) or "Invalid flight search parameters"
        )
    
    try:
        logger.info("Fetching outbound flights")
        logger.info(f"params: {json.dumps(params.model_dump(), indent=2)}")
        result = await fetch_flights_data(params)
        return result
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching outbound flights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/return-flights")
async def get_return_flights(
    departure_id: str = Query(description="Departure airport code (IATA)"),
    arrival_id: str = Query(description="Arrival airport code (IATA)"),
    outbound_date: str = Query(description="Outbound date in YYYY-MM-DD format"),
    adults: Optional[int] = Query(description="Number of adults", default=1),
    children: Optional[int] = Query(description="Number of children", default=0),
    return_date: Optional[str] = Query(description="Return date in YYYY-MM-DD format", default=None),
    departure_token: str = Query(description="Token for getting return flights")
):
    """
    ## Retrieve a list of return flights

    ### Query Parameters
    - **departure_id**: IATA code of departure airport  
    - **arrival_id**: IATA code of arrival airport  
    - **outbound_date**: Outbound date in YYYY-MM-DD format  
    - **adults**: Number of adults travelling  
    - **children**: Number of children travelling  
    - **return_date**: Return date in YYYY-MM-DD format  
    - **departure_token**: Token for getting return flights

    ### Returns
    JSON response with:
    - search_metadata
    - search_parameters  
    - airports  
    - flights

    ### Raises
    - **HTTPException**: If the params are invalid or SerpAPI fails  
    """
    
    params = ReturnFlightsInput (
        departure_id=departure_id,
        arrival_id=arrival_id,
        outbound_date=outbound_date,
        adults=adults,
        children=children,
        return_date=return_date,
        departure_token=departure_token
    )
    
    try:
        logger.info("Fetching return flights")
        logger.info(f"params: {json.dumps(params.model_dump(), indent=2)}")
        result = await fetch_flights_data(params)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching return flights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/bookingdata")
async def get_bookingdata(
    departure_id: str = Query(description="Departure airport code (IATA)"),
    arrival_id: str = Query(description="Arrival airport code (IATA)"),
    outbound_date: str = Query(description="Outbound date in YYYY-MM-DD format"),
    adults: Optional[int] = Query(description="Number of adults", default=1),
    children: Optional[int] = Query(description="Number of children", default=0),
    return_date: Optional[str] = Query(description="Return date in YYYY-MM-DD format", default=None),
    booking_token: str = Query(description="Token for getting flight options data")
):
    """
    ## Retrieve a list of booking options for selected flights

    ### Query Parameters
    - **departure_id**: IATA code of departure airport  
    - **arrival_id**: IATA code of arrival airport  
    - **outbound_date**: Outbound date in YYYY-MM-DD format  
    - **adults**: Number of adults travelling  
    - **children**: Number of children travelling  
    - **return_date**: Return date in YYYY-MM-DD format 
    - **booking_token**: Token for getting flight booking options 

    ### Returns
    JSON response with:
    - search_metadata
    - search_parameters
    - selected_flights
    - baggage_prices 
    - booking_options

    ### Raises
    - **HTTPException**: If the params are invalid or SerpAPI fails  
    """

    params = FlightBookingInput (
        departure_id=departure_id,
        arrival_id=arrival_id,
        outbound_date=outbound_date,
        adults=adults,
        children=children,
        return_date=return_date,
        booking_token=booking_token
    )
    
    try:
        logger.info("Fetching booking options")
        logger.info(f"params: {json.dumps(params.model_dump(), indent=2)}")
        result = await fetch_flights_data(params)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching booking data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")