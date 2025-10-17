import re
import certifi
import requests
from urllib3.util.retry import Retry
from typing import Optional, List, Dict
from requests.adapters import HTTPAdapter
from shared_utils.logger import get_logger
logger = get_logger()
def format_duration(minutes: Optional[int]) -> str:
    if minutes is None:
        return ""
    hours, mins = divmod(int(minutes), 60)
    if hours and mins:
        return f"{hours} hr {mins} min"
    elif hours:
        return f"{hours} hr"
    else:
        return f"{mins} min"

def extract_redirect_url(html_content: str) -> Optional[str]:
    """ Extracts the redirect URL from HTML meta refresh tag. """

    match = re.search(r"content=\"0;url='(.*?)'\"", html_content, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def book_flight(post_data: str, booking_phone: str) -> dict:
    """ 
    Initiates flight booking by posting to Google and extracting the redirect URL.
    Returns a dict with:
    - 'success': bool
    - 'url': str or None (redirect URL if successful)
    - 'message': str (success or error message)
    """
    
    if not post_data and not booking_phone:
        return {"success": False, "url": None, "message": "No booking data available for this flight option"}
    if not post_data:
        return {"success": False, "url": None, "message": f"Booking phone number provided: {booking_phone}. Please visit the airline's website to complete your booking."}
    url = "https://www.google.com/travel/clk/f"
    if post_data.startswith("u="):
        post_data_value = post_data[2:]
    else:
        post_data_value = post_data

    # Configure headers to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }

    # Set up a session with retry logic
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        response = requests.post(
            url, 
            data={"u": post_data_value},
            headers=headers,
            verify=certifi.where(), 
            timeout=10
        )
        if response.status_code == 200:
            redirect_url = extract_redirect_url(response.text)
            if redirect_url:
                print(f"Redirect URL: {redirect_url}")
                return {"success": True, "url": redirect_url, "message": "Booking request processed successfully!"}
            else:
                return {"success": False, "url": None, "message": "Failed to extract redirect URL from response."}
        else:
            return {"success": False, "url": None, "message": f"Failed to initiate booking. Status code: {response.status_code}"}
    except requests.exceptions.SSLError as ssl_err:
        return {"success": False, "url": None, "message": f"SSL Error during booking: {str(ssl_err)}. Check your network"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "url": None, "message": f"Error during booking: {str(e)}. Possible network issue or Google blocking the request."}

def build_details(index: Optional[int], flights: List[Dict]) -> str:
    """ Build detailed markdown for a selected flight option. """

    if index is None or index < 0 or index >= len(flights):
        return "Select a flight below to see full details"
    logger.info(f"Building details for {ordinal(index + 1)} flight")
    flight = flights[index]
    details = f"## ✈️ Flight Option {index+1}\n"
    details += f"**Total Duration:** {format_duration(flight.get('total_duration'))}<br>"
    details += f"**Price:** ₹{flight.get('price', 'N/A')}<br>"
    details += f"**Type:** {flight.get('type', 'N/A')}<br>"
    carbon = flight.get('carbon_emissions', {})
    details += f"**Carbon Emissions:** {carbon.get('this_flight', 'N/A')} g (vs {carbon.get('typical_for_this_route', 'N/A')}; difference: {carbon.get('difference_percent', 'N/A')}%) <br>"

    for i, f in enumerate(flight.get("flights", []), 1):
        details += "\n"
        details += f"### Leg {i}\n"
        dep = f.get('departure_airport', {})
        arr = f.get('arrival_airport', {})
        details += f"- **Route:** {dep.get('name')} ({dep.get('id')}, {dep.get('time')}) → {arr.get('name')} ({arr.get('id')}, {arr.get('time')})\n"
        details += f"- **Airline:** {f.get('airline')} ({f.get('flight_number')})\n"
        if 'ticket_also_sold_by' in f and f['ticket_also_sold_by']:
            details += f"- **Also Sold By:** {', '.join(f['ticket_also_sold_by'])}\n"
        details += f"- **Aircraft:** {f.get('airplane')} | **Class:** {f.get('travel_class')}\n"
        details += f"- **Duration:** {format_duration(f.get('duration'))}\n"
        details += f"- **Legroom:** {f.get('legroom', 'N/A')}\n"
        details += f"- **Extensions:** {', '.join(f.get('extensions', []))}\n"
        if 'overnight' in f and f['overnight']:
            details += "- **Overnight:** Yes\n\n"
        else:
            details += "\n"

    if "layovers" in flight and flight["layovers"]:
        details += "## Layovers\n"
        for layover in flight["layovers"]:
            overnight = " (Overnight)" if 'overnight' in layover and layover['overnight'] else ""
            details += f"- {layover.get('name')} ({layover.get('id')}): {format_duration(layover.get('duration'))} {overnight}\n"

    return details

def ordinal(n: int) -> str:
    """ Convert integer into its ordinal representation (1 -> 1st, 2 -> 2nd, etc). """

    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"