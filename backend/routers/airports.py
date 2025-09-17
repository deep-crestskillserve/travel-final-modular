import httpx
from typing import List, Dict, Optional
from shared_utils.logger import get_logger
from backend.utils import get_access_token
from fastapi import APIRouter, HTTPException
logger = get_logger()

router = APIRouter(prefix="/api", tags=["airports"])
BASE_URL = "http://localhost:8000/api"

async def get_airport(location: str):
    """
    Fetch the nearest airports for a given location using the Amadeus API.

    Args:
        location (str): The address or location to find nearby airports (e.g., "New York, NY").

    Returns:
        Optional[List[Dict]]: A list of airport data (with IATA codes) if found, or None if no airports are found.

    Raises:
        ValueError: If the location is invalid or empty.
        HTTPException: If the geolocation or Amadeus API request fails.
    """

    if not location or not location.strip():
        raise ValueError("Location cannot be empty")

    coords = {}
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
        try:
            # response = await client.post(f"{BASE_URL}/geolocation", json={"params": location})
            response = await client.get(f"{BASE_URL}/geolocation", params={"location": location})
            response.raise_for_status()
            result = response.json()
            coords = result
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code}")
            try:
                print(f"Error details: {e.response.json()}")
            except ValueError:
                print(f"Error text: {e.response.text}")
                raise
        except httpx.RequestError as e:
            print(f"Request error occurred: {e}")
            raise

    try:
        if not coords:
            return {"status": 404, "response": {"title": f"NO GEOLOCATION DATA FOUND FOR {location}"}}
        
        lat = coords["latitude"]
        lon = coords["longitude"]
        logger.info(f"Fetched coordinates for {location}: {coords}")
        
        access_token = await get_access_token()
        if not access_token:
            raise HTTPException(status_code=500, detail="Failed to obtain access token")
        
        url = "https://test.api.amadeus.com/v1/reference-data/locations/airports"
        params = {
            "latitude": lat,
            "longitude": lon,
            "radius": 500  # Explicit radius in km
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.get(url, params=params, headers=headers)
            logger.info(f"Amadeus API response status: {response.status_code}")
            response.raise_for_status()

            data = response.json()
            if not data.get("data"):
                raise HTTPException(status_code=404, detail=f"No airports found near {location}")

            return data["data"]
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Amadeus API error: {str(e)}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch airports: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.get("/airports")
async def get_nearest_airports(location: str) -> Optional[List[Dict]]:
    """
    Retrieve a list of airports near a given location.

    Query Parameters:
        location (str): The address or location to find nearby airports (e.g., "New York, NY").

    Returns:
        JSON response with a list of airport data (including IATA codes), or an error if none found.

    Raises:
        HTTPException: If the location is invalid, geolocation fails, or the Amadeus API request fails.
    """

    try:
        logger.info(f"Fetching releavant nearby airports for location: {location}")
        result = await get_airport(location)
        if not result:
            raise HTTPException(status_code=404, detail=f"No airports found near {location}")
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
