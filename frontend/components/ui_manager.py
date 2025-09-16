import gradio as gr
from typing import List, Dict
from utils.helpers import format_duration, build_details, ordinal
import json
import httpx
from utils.logger import logger
logger = logger()

MAX_FLIGHTS = 20
MAX_BOOKING_OPTIONS = 10
VIEW_OUTBOUND_CARDS = "outbound cards"
VIEW_RETURN_CARDS = "return cards"
VIEW_OUTBOUND_DETAILS = "outbound details"
VIEW_RETURN_DETAILS = "return details"
VIEW_BOOKING = "booking"
PLACEHOLDER_IMAGE_URL = "https://via.placeholder.com/32"
BASE_URL = "http://localhost:8000/api"

class UIManager:
    @staticmethod
    def get_card_html(idx: int, flight: Dict, selected: bool = False) -> str:
        first = flight["flights"][0] if flight.get("flights") else {}
        last = flight["flights"][-1] if flight.get("flights") else {}
        stops = len(flight.get("flights", [])) - 1
        stops_text = f"{stops} stop{'s' if stops != 1 else ''}" if stops > 0 else "Non-stop"
        logos = "".join(
            f'<img src="{f.get("airline_logo", "")}"'
            f'title="{f.get("airline", "")}"'
            f' onerror="this.src={PLACEHOLDER_IMAGE_URL}">'
            for f in flight.get("flights", [])
        )
        selected_class = "selected" if selected else ""
        return f"""
        <div class="card {selected_class}" id="card-{idx}">
            <div class="logo-chain">{logos}</div>
            <div class="route">{first.get('departure_airport', {}).get('id', '')} → {last.get('arrival_airport', {}).get('id', '')}</div>
            <div class="price">₹{flight.get('price', 'N/A')}</div>
            <div class="duration">{format_duration(flight.get('total_duration'))} total</div>
            <div class="stops">{stops_text}</div>
        </div>
        """

    @staticmethod
    def update_cards(selected: int, flight_data: Dict) -> List[str]:
        if selected is not None:
            print(f"Selected {ordinal(selected + 1)} card, updating highlights")
        else:
            print("Reloading flight cards")

        flights = flight_data.get("flights", []) if flight_data else []
        
        html_updates = []
        for idx in range(MAX_FLIGHTS):
            if idx < len(flights):
                html_updates.append(UIManager.get_card_html(idx, flights[idx], idx == selected))
            else:
                html_updates.append("")
        return html_updates

    @staticmethod
    def update_flight_interface(flight_data: Dict):
        if(flight_data):
            print(f"loading outbound flights")
        
        flights = flight_data.get("flights", []) if flight_data else []

        visible = bool(flights)
        html_updates = []
        visible_updates = []
        for idx in range(MAX_FLIGHTS):
            if idx < len(flights):
                html_updates.append(UIManager.get_card_html(idx, flights[idx]))
                visible_updates.append(gr.update(visible=True))
            else:
                html_updates.append("")
                visible_updates.append(gr.update(visible=False))
        return gr.update(visible=visible), *html_updates, *visible_updates

    @staticmethod
    def update_booking_ui(booking_data: Dict):
        print(f"Loading booking options...")
        
        booking_options = booking_data.get("booking_options", []) if booking_data else []
        group_visibles = []
        info_updates = []
        button_values = []
        for i in range(MAX_BOOKING_OPTIONS):
            if i < len(booking_options):
                option = booking_options[i].get("together", {})
                book_with = option.get("book_with", "Unknown")
                price = option.get("price", "N/A")
                currency = booking_data.get("search_parameters", {}).get("currency", "INR") if booking_data else "INR"
                flight_numbers = ', '.join(option.get("marketed_as", []))
                baggage = ', '.join(option.get("baggage_prices", []))
                info = f"### Option {i+1}: {book_with}\n**Price**: {price} {currency}\n**Flights**: {flight_numbers}\n**Baggage**: {baggage}"
                group_visibles.append(gr.update(visible=True))
                info_updates.append(info)
                button_values.append(gr.update(value=f"Book with {book_with}", visible=True))
            else:
                group_visibles.append(gr.update(visible=False))
                info_updates.append("")
                button_values.append(gr.update(visible=False))
        return group_visibles + info_updates + button_values

    @staticmethod
    def get_flight_details(selected: int, flight_data: Dict, params: Dict):
        
        print(f"Showing flight details for {ordinal(selected)} flight")
        print(f"params: {json.dumps(params, indent=2)}")
        view_return = 1 if flight_data.get("flights")[0].get("departure_token") else 0
        if view_return:
            return VIEW_RETURN_DETAILS, build_details(selected, flight_data)
        else:
            return VIEW_OUTBOUND_DETAILS, build_details(selected, flight_data)
        if params.get("return_date"):
            return VIEW_OUTBOUND_DETAILS, build_details(selected, flight_data)
        else:
            if params.get("departure_token"):
                return VIEW_RETURN_DETAILS, build_details(selected, flight_data)
            elif params.get("booking_token"):
                return VIEW_BOOKING, build_details(selected, flight_data)

    @staticmethod
    async def on_get_return_flights(selected: int, flight_data: Dict, initial_payload: Dict):
        flights = flight_data.get("flights", []) if flight_data else []
        departure_token = flights[selected].get("departure_token", "")
        
        logger.info(f"Selected flight departure token: {departure_token}")
        logger.info(f"Fetching return flights for the {ordinal(selected + 1)} flight")
        
        if not departure_token:
            logger.info("No departure token found for selected flight.")
            return VIEW_RETURN_CARDS, {"error": "No departure token available"}
        
        departure_input = {
            **initial_payload,
            "departure_token": departure_token
        }
        flight_data = {}
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
            try:
                response = await client.get(f"{BASE_URL}/return-flights", params=departure_input)
                response.raise_for_status()
                flight_data = response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"FastAPI server error: {e.response.status_code} - {e.response.text}")
                raise  # Propagate the error to the caller
            except httpx.RequestError as e:
                logger.error(f"Network error contacting FastAPI server: {e}")
                raise 

        print("Return flights loaded")
        return VIEW_RETURN_CARDS, flight_data

    @staticmethod
    async def on_booking_options(selected: int, flight_data: Dict, initial_payload: Dict):
        flights = flight_data.get("flights", []) if flight_data else []

        booking_token = flights[selected].get("booking_token", "")

        print(f"Selected flight booking token: {booking_token}")
        print(f"Fetching booking options for {ordinal(selected)} flight")

        if not booking_token:
            print("no booking token found for the selected flight.")
            return VIEW_BOOKING, {"error": "No booking token available"}

        booking_input = {
            **initial_payload,
            "booking_token": booking_token,
        }
        booking_data = {}
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
            try:
                response = await client.get(f"{BASE_URL}/bookingdata", params=booking_input)
                response.raise_for_status()
                booking_data = response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"FastAPI server error: {e.response.status_code} - {e.response.text}")
                raise  # Propagate the error to the caller
            except httpx.RequestError as e:
                logger.error(f"Network error contacting FastAPI server: {e}")
                raise

        print("Booking options loaded")
        return VIEW_BOOKING, booking_data

    @staticmethod
    def update_view(view: str):
        if view == VIEW_OUTBOUND_CARDS:
            return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
        elif view == VIEW_RETURN_CARDS:
            return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
        elif view == VIEW_OUTBOUND_DETAILS:
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
        elif view == VIEW_RETURN_DETAILS:
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
        elif view == VIEW_BOOKING:
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)