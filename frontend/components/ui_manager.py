from utils.helpers import format_duration, build_details, ordinal
from utils.logger import logger
from typing import List, Dict
import gradio as gr
import requests

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
            f' onerror="this.src=\'{PLACEHOLDER_IMAGE_URL}\'">'
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
            logger.info(f"Selected {ordinal(selected + 1)} card, updating highlights")
        else:
            logger.info("Reloading flight cards")

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
        flights = flight_data.get("flights", []) if flight_data else []
        if not flights:
            return gr.update(visible=False), *[""]*MAX_FLIGHTS, *[gr.update(visible=False)]*MAX_FLIGHTS
        
        if flights[0].get("departure_token"):
            logger.info("displaying return flights")
        else:
            logger.info("displaying outbound flights")

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
        logger.info(f"Loading booking options...")
        
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
        flights = flight_data.get("flights", []) if flight_data else []

        if not flight_data or not flight_data.get("flights"):
            return VIEW_OUTBOUND_CARDS, "No flight data available"
        
        if selected < 0 or selected >= len(flights):
            return VIEW_OUTBOUND_CARDS, {"error": "Invalid flight selection"}

        next_view = ""
        if params.get("return_date"):
            # Round-trip: Check if these are return flights (no departure_token) or outbound flights (have departure_token)
            if flights[0].get("departure_token"):
                next_view = VIEW_OUTBOUND_DETAILS
            else:
                next_view = VIEW_RETURN_DETAILS
        else:
            # One-way: Always outbound
            next_view = VIEW_OUTBOUND_DETAILS
        
        if selected < 0 or selected >= len(flights):
            if next_view == VIEW_OUTBOUND_DETAILS:
                return VIEW_OUTBOUND_CARDS, "Invalid flight selection"
            else:
                return VIEW_RETURN_CARDS, "Invalid flight selection"
        logger.info(f"Showing flight details for {ordinal(selected + 1)} flight")

        details = build_details(selected, flights)
        return next_view, details

    @staticmethod
    def on_get_return_flights(selected: int, flight_data: Dict, initial_payload: Dict):
        
        flights = flight_data.get("flights", []) if flight_data else []
        
        if selected < 0 or selected >= len(flights):
            logger.error("Invalid flight selection for return flights")
            return VIEW_RETURN_CARDS, {"error": "Invalid flight selection"}
        
        departure_token = flights[selected].get("departure_token", "")
        if not departure_token:
            logger.error(f"No departure token found for the {ordinal(selected + 1)} flight.")
            return VIEW_RETURN_CARDS, {"error": f"No departure token available for {ordinal(selected + 1)} flight"}
        
        logger.info(f"Selected flight departure token: {departure_token}")
        logger.info(f"Fetching return flights for the {ordinal(selected + 1)} flight")
        
        departure_input = {
            **initial_payload,
            "departure_token": departure_token
        }

        try:
            response = requests.get(f"{BASE_URL}/return-flights", params=departure_input, timeout=90)
            response.raise_for_status()
            return_flight_data = response.json()
            logger.info("Return flights loaded")
            return VIEW_RETURN_CARDS, return_flight_data
        except requests.RequestException as e:
            logger.error(f"Error fetching return flights: {e}")
            return VIEW_RETURN_CARDS, {"error": f"Failed to fetch return flights: {str(e)}"}

    @staticmethod
    def on_booking_options(selected: int, flight_data: Dict, initial_payload: Dict):
        
        flights = flight_data.get("flights", []) if flight_data else []
        
        error_view = ""
        if initial_payload.get("return_date"):
            error_view = VIEW_RETURN_DETAILS
        else:
            error_view = VIEW_OUTBOUND_DETAILS
        if selected < 0 or selected >= len(flights):
            return error_view, {"error": "Invalid flight selection for booking option"}

        booking_token = flights[selected].get("booking_token", "")
        if not booking_token:
            logger.error(f"No booking token found for the {ordinal(selected + 1)} flight.")
            return VIEW_RETURN_DETAILS, {"error": f"No booking token available for {ordinal(selected + 1)} flight"}

        logger.info(f"Selected flight booking token: {booking_token}")
        logger.info(f"Fetching booking options for {ordinal(selected + 1)} flight")

        booking_input = {
            **initial_payload,
            "booking_token": booking_token,
        }

        try:
            response = requests.get(f"{BASE_URL}/bookingdata", params=booking_input, timeout=90)
            response.raise_for_status()
            booking_data = response.json()
            logger.info("Booking options loaded")
            return VIEW_BOOKING, booking_data
        except requests.RequestException as e:
            logger.error(f"Error fetching booking options: {e}")
            return VIEW_BOOKING, {"error": f"Failed to fetch booking options: {str(e)}"}

    @staticmethod
    def update_view(view: str):
        """Update visibility of different view sections"""
        if view == VIEW_OUTBOUND_CARDS:
            return (
                gr.update(visible=True),   # outbound_flight_cards
                gr.update(visible=False),  # return_flight_cards
                gr.update(visible=False),  # outbound_flight_details
                gr.update(visible=False),  # return_flight_details
                gr.update(visible=False)   # flight_booking_section
            )
        elif view == VIEW_RETURN_CARDS:
            return (
                gr.update(visible=False),  # outbound_flight_cards
                gr.update(visible=True),   # return_flight_cards
                gr.update(visible=False),  # outbound_flight_details
                gr.update(visible=False),  # return_flight_details
                gr.update(visible=False)   # flight_booking_section
            )
        elif view == VIEW_OUTBOUND_DETAILS:
            return (
                gr.update(visible=False),  # outbound_flight_cards
                gr.update(visible=False),  # return_flight_cards
                gr.update(visible=True),   # outbound_flight_details
                gr.update(visible=False),  # return_flight_details
                gr.update(visible=False)   # flight_booking_section
            )
        elif view == VIEW_RETURN_DETAILS:
            return (
                gr.update(visible=False),  # outbound_flight_cards
                gr.update(visible=False),  # return_flight_cards
                gr.update(visible=False),  # outbound_flight_details
                gr.update(visible=True),   # return_flight_details
                gr.update(visible=False)   # flight_booking_section
            )
        elif view == VIEW_BOOKING:
            return (
                gr.update(visible=False),  # outbound_flight_cards
                gr.update(visible=False),  # return_flight_cards
                gr.update(visible=False),  # outbound_flight_details
                gr.update(visible=False),  # return_flight_details
                gr.update(visible=True)    # flight_booking_section
            )