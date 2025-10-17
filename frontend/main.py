import gradio as gr
from frontend.utils import book_flight
from frontend.components.ui_manager import UIManager
from backend.agents.travel_agent import TravelAgent
from backend.transcript.main import AssemblyAITranscriber
from frontend.utils import ordinal

MAX_FLIGHTS = 20
MAX_BOOKING_OPTIONS = 20
VIEW_OUTBOUND_CARDS = "outbound cards"
VIEW_RETURN_CARDS = "return cards"
VIEW_OUTBOUND_DETAILS = "outbound details"
VIEW_RETURN_DETAILS = "return details"
VIEW_BOOKING = "booking"

CSS = """
/* Light theme variables - explicitly for light mode */
:root, 
:root[style*="color-scheme: light"],
.light {
    --flight-bg: #f9fafb;
    --flight-surface: #ffffff;
    --flight-surface-hover: #f3f4f6;
    --flight-border: #e5e7eb;
    --flight-text: #111827;
    --flight-text-secondary: #6b7280;
    --flight-accent: #10b981;
    --flight-accent-hover: #059669;
    --flight-error: #ef4444;
    --flight-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --flight-scrollbar-track: #f3f4f6;
    --flight-scrollbar-thumb: #d1d5db;
    --flight-scrollbar-thumb-hover: #9ca3af;
}

/* Dark theme variables - for dark mode AND as fallback */
@media (prefers-color-scheme: dark) {
    :root {
        --flight-bg: #0b0f19;
        --flight-surface: #1a1d29;
        --flight-surface-hover: #252837;
        --flight-border: #374151;
        --flight-text: #f9fafb;
        --flight-text-secondary: #d1d5db;
        --flight-accent: #10b981;
        --flight-accent-hover: #059669;
        --flight-error: #ef4444;
        --flight-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        --flight-scrollbar-track: #0b0f19;
        --flight-scrollbar-thumb: #374151;
        --flight-scrollbar-thumb-hover: #6b7280;
    }
}

:root[style*="color-scheme: dark"],
.dark {
    --flight-bg: #0b0f19;
    --flight-surface: #1a1d29;
    --flight-surface-hover: #252837;
    --flight-border: #374151;
    --flight-text: #f9fafb;
    --flight-text-secondary: #d1d5db;
    --flight-accent: #10b981;
    --flight-accent-hover: #059669;
    --flight-error: #ef4444;
    --flight-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    --flight-scrollbar-track: #0b0f19;
    --flight-scrollbar-thumb: #374151;
    --flight-scrollbar-thumb-hover: #6b7280;
}

/* Flight section container */
#flight-container {
    display: flex !important;
    flex-direction: column !important;
    background: var(--flight-bg) !important;
    border-radius: 8px !important;
    border: 1px solid var(--flight-border) !important;
    padding: 0 !important;
    height: 500px !important;
    overflow: hidden !important;
    box-shadow: var(--flight-shadow) !important;
}

/* Main content area that can scroll */
.flight-content {
    flex: 1 1 auto !important;
    padding: 1rem !important;
    background: var(--flight-bg) !important;
    min-height: 0 !important;
    overflow: visible !important;
}

/* Sticky button container */
.flight-buttons {
    flex: 0 0 auto !important;
    background: var(--flight-surface) !important;
    border-top: 1px solid var(--flight-border) !important;
    padding: 1rem !important;
    position: sticky !important;
    bottom: 0 !important;
    z-index: 20 !important;
    width: 100% !important;
}

/* Flight cards styling */
.card-container {
    background: var(--flight-surface) !important;
    border: 1px solid var(--flight-border) !important;
    border-radius: 6px !important;
    margin: 0.5rem !important;
    transition: all 0.2s ease !important;
    position: relative !important;
    overflow: visible !important;
    max-height: none !important;
    text-align: center;
}

.card-container:hover {
    background: var(--flight-surface-hover) !important;
    border-color: var(--flight-accent) !important;
    transform: translateY(-2px) !important;
    box-shadow: var(--flight-shadow) !important;
}

.card-container.selected {
    border-color: var(--flight-accent) !important;
    background: var(--flight-surface-hover) !important;
    box-shadow: var(--flight-shadow) !important;
}

.logo-chain {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;
}

.route {
    font-weight: 700;
    font-size: 18px;
    color: var(--flight-text) !important;
    margin-bottom: 4px;
}

.price {
    font-weight: 700;
    color: var(--flight-accent) !important;
    font-size: 16px;
    margin-bottom: 4px;
}

.duration {
    font-size: 14px;
    color: var(--flight-text-secondary) !important;
    margin-bottom: 4px;
}

.stops {
    font-size: 14px;
    color: var(--flight-text-secondary) !important;
}

.departure-time {
    font-size: 14px;
    color: var(--flight-text-secondary) !important;
    margin-bottom: 4px;
}

/* Click overlay for cards */
.click-overlay {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    background: transparent !important;
    border: none !important;
    cursor: pointer !important;
    z-index: 10 !important;
}

.flight-view {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
    height: 500px !important;
    overflow: hidden !important;
}

/* Flight details styling */
.flight-details {
    background: var(--flight-surface) !important;
    border: 1px solid var(--flight-border) !important;
    border-radius: 6px !important;
    padding: 1rem !important;
    color: var(--flight-text) !important;
    line-height: 1.6 !important;
    overflow-y: auto !important;
    max-height: 500px !important;
    min-height: calc(500px - 120px) !important;
}

.flight-details h1, .flight-details h2, .flight-details h3 {
    color: var(--flight-text) !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.5rem !important;
}

.flight-details p, .flight-details li {
    color: var(--flight-text-secondary) !important;
    margin-bottom: 0.5rem !important;
}

/* Primary buttons styling */
#confirm-button, .primary-btn {
    background: var(--flight-accent) !important;
    color: white !important;
    border: none !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    min-width: 120px !important;
}

#confirm-button:hover, .primary-btn:hover {
    background: var(--flight-accent-hover) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--flight-shadow) !important;
}

#confirm-button:disabled, .primary-btn:disabled {
    background: #6b7280 !important;
    cursor: not-allowed !important;
    transform: none !important;
}

/* Secondary buttons styling */
.secondary-btn {
    background: var(--flight-surface) !important;
    color: var(--flight-text) !important;
    border: 1px solid var(--flight-border) !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    min-width: 120px !important;
}

.secondary-btn:hover {
    background: var(--flight-surface-hover) !important;
    border-color: var(--flight-accent) !important;
    transform: translateY(-1px) !important;
}

/* Loader styling */
.loader-container {
    background: var(--flight-surface) !important;
    border: 1px solid var(--flight-border) !important;
    border-radius: 6px !important;
    padding: 2rem !important;
    text-align: center !important;
    color: var(--flight-text) !important;
    overflow: visible !important;
    max-height: none !important;
}

.loader {
    border: 3px solid var(--flight-border) !important;
    border-top: 3px solid var(--flight-accent) !important;
    border-radius: 50% !important;
    width: 40px !important;
    height: 40px !important;
    animation: spin 1s linear infinite !important;
    margin: 0 auto 1rem auto !important;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.loader-message {
    color: var(--flight-text-secondary) !important;
    margin: 0 !important;
}

/* Error message styling */
.error-message {
    background: rgba(239, 68, 68, 0.1) !important;
    border: 1px solid var(--flight-error) !important;
    border-radius: 6px !important;
    padding: 1rem !important;
    color: var(--flight-error) !important;
    margin-bottom: 1rem !important;
    overflow: visible !important;
    max-height: none !important;
}

/* Card grid styling */
.cards-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)) !important;
    gap: 1rem !important;
    padding-bottom: 1rem !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    max-height: 500px !important;
    min-height: calc(500px - 120px) !important;
}

/* Button row styling */
.button-row {
    display: flex !important;
    gap: 0.75rem !important;
    justify-content: flex-end !important;
    align-items: center !important;
    flex-wrap: wrap !important;
}

/* Unified scrollbar styling for flight-content, cards-grid, booking-content, and flight-details */
.flight-content::-webkit-scrollbar,
.cards-grid::-webkit-scrollbar,
#booking-content::-webkit-scrollbar,
.flight-details::-webkit-scrollbar {
    width: 12px !important;
}

.flight-content::-webkit-scrollbar-track,
.cards-grid::-webkit-scrollbar-track,
#booking-content::-webkit-scrollbar-track,
.flight-details::-webkit-scrollbar-track {
    background: var(--flight-scrollbar-track) !important;
    border-radius: 6px !important;
}

.flight-content::-webkit-scrollbar-thumb,
.cards-grid::-webkit-scrollbar-thumb,
#booking-content::-webkit-scrollbar-thumb,
.flight-details::-webkit-scrollbar-thumb {
    background: var(--flight-scrollbar-thumb) !important;
    border-radius: 6px !important;
    border: 2px solid var(--flight-scrollbar-track) !important;
}

.flight-content::-webkit-scrollbar-thumb:hover,
.cards-grid::-webkit-scrollbar-thumb:hover,
#booking-content::-webkit-scrollbar-thumb:hover,
.flight-details::-webkit-scrollbar-thumb:hover {
    background: var(--flight-scrollbar-thumb-hover) !important;
}

#booking-content {
    max-height: 500px !important;
    min-height: calc(500px - 40px) !important;
    overflow-y: auto !important;
    padding: 1rem !important;
}

/* Booking options styling */
.booking-option {
    background: var(--flight-surface) !important;
    border: 1px solid var(--flight-border) !important;
    border-radius: 6px !important;
    padding: 1rem !important;
    margin-bottom: 1rem !important;
    overflow: visible !important;
}

.booking-option .markdown:first-child {
    font-size: 1.1em !important;
    font-weight: bold !important;
    color: var(--flight-text) !important;
    margin-bottom: 0.5rem !important;
}

.booking-option .button {
    width: 100% !important;
}

.booking-option .markdown:last-child {
    margin-top: 1rem !important;
    color: var(--flight-text-secondary) !important;
}

.booking-option .button-row {
    display: flex !important;
    gap: 0.75rem !important;
    justify-content: flex-start !important;
    align-items: center !important;
    flex-wrap: wrap !important;
}

/* Responsive design */
@media (max-width: 768px) {
    #flight-container {
        height: auto !important;
        max-height: 80vh !important;
        height: 80vh !important;
    }

    .flight-view {
        height: 80vh !important;
    }

    .cards-grid {
        grid-template-columns: 1fr !important;
        max-height: 350px !important;
        min-height: calc(80vh - 120px) !important;
    }
    
    .card-container {
        max-height: none !important;
    }

    #confirm-button, .primary-btn, .secondary-btn {
        min-width: 100px !important;
        padding: 0.5rem 1rem !important;
    }
    
    #booking-content {
        max-height: 80vh !important;
        min-height: calc(80vh - 40px) !important;
    }

    .flight-details {
        max-height: 80vh !important;
        min-height: calc(80vh - 120px) !important;
        padding: 1rem !important;
    }
}
"""

def create_travel_app():
    """ Create the Gradio travel app with all components and interactions """

    travel_agent = TravelAgent()
    transcriber = AssemblyAITranscriber()

    # Async function to initialize chat with welcome message
    async def init_chat(thread_id):
        initial_history, _, _ = await travel_agent.process_message("", [], thread_id)
        return initial_history

    def toggle_transcription(is_recording, current_message):
        if is_recording:
            transcriber.stop()
            transcript = transcriber.get_transcript()
            return False, transcript, gr.update(value="🎤")
        else:
            transcriber.start()
            return True, "", gr.update(value="🔴")
    
    def get_post_data(option_index):
        """Gives post_data for separate tickets and together tickets."""

        def extract_post_data(booking_data):

            post_data = ""
            departure_post_data = ""
            return_post_data = ""
            booking_phone = ""
            departure_booking_phone = ""
            return_booking_phone = ""

            booking_options = booking_data.get("booking_options", []) if booking_data else []
            
            if option_index >= len(booking_options):
                return post_data, departure_post_data, return_post_data, booking_phone, departure_booking_phone, return_booking_phone
            
            option = booking_options[option_index]
            
            # Handle separate tickets (departing and returning legs)
            if option.get("departing") and option.get("returning"):
                departure_post_data = option.get("departing", {}).get("booking_request", {}).get("post_data", "")
                departure_booking_phone = option.get("departing", {}).get("booking_phone", "")
                return_post_data = option.get("returning", {}).get("booking_request", {}).get("post_data", "")
                return_booking_phone = option.get("returning", {}).get("booking_phone", "")
            # Handle together tickets
            elif option.get("together"):
                post_data = option.get("together", {}).get("booking_request", {}).get("post_data", "")
                booking_phone = option.get("together", {}).get("booking_phone", "")
            
            return post_data, departure_post_data, return_post_data, booking_phone, departure_booking_phone, return_booking_phone
        
        return extract_post_data

    def create_booking_handler(option_index):
        """Create booking handler for specific option."""
        def handle_booking(booking_data):
            """Handle booking for a specific option."""
            print('\n'*5)
            print(f"option index: {option_index}")
            print('\n'*5)
            gr.Info(f"Processing booking for {ordinal(option_index + 1)} option...")
            booking_options = booking_data.get("booking_options", []) if booking_data else []
            if option_index >= len(booking_options):
                return "⚠️ Invalid option", ""

            post_data, departure_post_data, return_post_data, booking_phone, departure_booking_phone, return_booking_phone = get_post_data(option_index)(booking_data)

            if departure_post_data and return_post_data:
                # Handle round-trip booking with separate legs
                result_depart = book_flight(departure_post_data, departure_booking_phone)
                result_return = book_flight(return_post_data, return_booking_phone)
                if result_depart["success"] and result_return["success"]:
                    message = (
                        f"Departure: {result_depart['message']}<br>"
                        f'[Click here to book departure fligths]({result_depart["url"]})<br><br>'
                        f"Return: {result_return['message']}<br>"
                        f'[Click here to book return flights]({result_return["url"]})'
                    )
                    return message, f"Departure: {result_depart['url']} | Return: {result_return['url']}"
                else:
                    msg = f"Departure: {result_depart['message']}<br>Return: {result_return['message']}"
                    return msg, ""
            else:
                # Handle one-way or together booking
                result = book_flight(post_data, booking_phone)
                if result["success"]:
                    # Format as markdown with hyperlink (target="_blank" for new tab)
                    message = (
                        f"{result['message']}<br>"
                        f'[Click here to continue booking]({result["url"]})'
                    )
                    return message, result["url"]
                else:
                    return result["message"], ""

        return handle_booking

    def update_button_visibility(params):
        """ Update button visibility of outbound_flight_cards buttons based on trip type """

        if not params:
            return gr.update(visible=False), gr.update(visible=False)
        has_return_date = params.get("return_date") is not None
        
        if has_return_date:  # Round-trip
            # Show "Get Return Flights" button, hide "Finalise Flight" button
            return gr.update(visible=False), gr.update(visible=True)
        else:  # One-way
            # Show "Finalise Flight" button, hide "Get Return Flights" button
            return gr.update(visible=True), gr.update(visible=False)
    
    def reset_chatbot():
        """ Reset all chatbot-related states and UI components """
        new_thread_id = travel_agent.make_thread_id()
        return (
            "",  # message
            [],  # chatbot
            new_thread_id,  # thread_id_state
            False,  # is_recording
            ""  # user_message_state
        )

    def reset_flight_section():
        """ Reset all flight section-related states and UI components """
        # Create empty card updates
        empty_card_html = [""] * MAX_FLIGHTS
        hidden_card_containers = [gr.update(visible=False)] * MAX_FLIGHTS

        # Create empty booking updates
        hidden_booking_groups = [gr.update(visible=False)] * MAX_BOOKING_OPTIONS
        empty_info_updates = [""] * MAX_BOOKING_OPTIONS
        hidden_booking_buttons = [gr.update(visible=False)] * MAX_BOOKING_OPTIONS
        empty_booking_results = [""] * MAX_BOOKING_OPTIONS
        empty_booking_urls = [""] * MAX_BOOKING_OPTIONS
        
        return (
            # State variables
            VIEW_OUTBOUND_CARDS,  # current_view
            {},  # initial_flight_payload
            {},  # outbound_flights_state
            None,  # selected_outbound_index
            {},  # return_flights_state
            None,  # selected_return_index
            {},  # booking_data_state
            
            # UI visibility
            gr.update(visible=False),  # flight_section
            
            # Outbound flight cards
            *empty_card_html,  # outbound_card_html_components
            *hidden_card_containers,  # outbound_card_containers
            gr.update(interactive=False),  # outbound_view_flight_button
            
            # Outbound flight details
            "Select a flight to see details",  # outbound_flight_details_box
            gr.update(visible=False),  # outbound_booking_options_button
            gr.update(visible=False),  # get_return_flights_button
            
            # Return flight cards
            *empty_card_html,  # return_card_html_components
            *hidden_card_containers,  # return_card_containers
            gr.update(interactive=False),  # return_view_flight_button
            
            # Return flight details
            "Select a return flight to see details",  # return_flight_details_box
            
            # Booking section
            *hidden_booking_groups,  # booking_groups visibility
            *empty_info_updates,  # info_mds content
            *hidden_booking_buttons,  # booking_buttons visibility
            *empty_booking_results,  # booking_results content
            *empty_booking_urls, # booking_urls content
            gr.update(visible=False),  # loader_group
            gr.update(value=""),  # loader_message
            gr.update(visible=False)  # error_message
        )

    def complete_reset():
        """ Complete reset of all states and UI components by calling modular reset functions """
        chatbot_outputs = reset_chatbot()
        flight_outputs = reset_flight_section()
        return (*chatbot_outputs, *flight_outputs)

    def handle_new_flight_data(flights_state, payload_state):
        """
        Check if new flights were fetched. If yes, reset flight section and return new data.
        Otherwise, return unchanged states.
        """
        has_new_flights = bool(flights_state.get("flights"))
        
        if has_new_flights:
            # Reset everything and update with new flight data
            reset_outputs = reset_flight_section()
            # Override the states that need new data
            return (
                VIEW_OUTBOUND_CARDS,  # current_view
                payload_state,  # initial_flight_payload (NEW)
                flights_state,  # outbound_flights_state (NEW)
                *reset_outputs[3:]  # Rest of the reset outputs (selected indices, return flights, booking data, UI components)
            )
        else:
            # No new flights, return no-change updates
            return (
                VIEW_OUTBOUND_CARDS,  # current_view - no change
                {},  # initial_flight_payload - no change
                {},  # outbound_flights_state - no change
                *([gr.State()] * (len(reset_flight_section()) - 3))  # Rest unchanged
            )

    with gr.Blocks(theme=gr.themes.Default(primary_hue="emerald"), css=CSS) as demo:
        gr.Markdown("Enter your travel query")
        
        thread_id_state = gr.State(travel_agent.make_thread_id())
        user_message_state = gr.State("")
        
        current_view = gr.State(value=VIEW_OUTBOUND_CARDS)
        initial_flight_payload = gr.State(value={})
        outbound_flights_state = gr.State(value={})
        selected_outbound_index = gr.State(value=None)
        return_flights_state = gr.State(value={})
        selected_return_index = gr.State(value=None)
        booking_data_state = gr.State(value={})
        is_recording = gr.State(False)
        
        with gr.Row():
            with gr.Column():
                chatbot = gr.Chatbot(label="Travel Chatbot", height=500, type="messages")
            
            with gr.Column(visible=False, scale=1) as flight_section:
                with gr.Group():                    
                    with gr.Column(elem_id="flight-container", scale=1):
                        # Added: Loader group with spinner and dynamic message
                        with gr.Group(elem_classes=["loader-container"], visible=False) as loader_group:
                            loader = gr.HTML('<div class="loader"></div>')
                            loader_message = gr.Markdown("", elem_classes=["loader-message"])
                        # Added: Error message component
                        error_message = gr.Markdown(visible=False, elem_classes=["error-message"])

                        with gr.Column(visible=True, elem_classes=["flight-view"]) as outbound_flight_cards:
                            with gr.Column(elem_classes=["flight-content"]):
                                with gr.Column(elem_classes=["cards-grid"]):
                                    outbound_card_html_components = []
                                    outbound_card_containers = []
                                    for card_index in range(MAX_FLIGHTS):
                                        with gr.Column(elem_classes=["card-container"], visible=False) as card_col:
                                            card_html = gr.HTML("")
                                            card_button = gr.Button("", elem_classes=["click-overlay"])
                                            outbound_card_html_components.append(card_html)
                                            # the button is being binded to function upon click event
                                            card_button.click(
                                                fn=lambda x=card_index: x,
                                                outputs=selected_outbound_index
                                            ).then(
                                                fn=UIManager.update_cards,
                                                inputs=[selected_outbound_index, outbound_flights_state],
                                                outputs=outbound_card_html_components
                                            )
                                        outbound_card_containers.append(card_col)

                            with gr.Column(elem_classes=["flight-buttons"]):
                                outbound_view_flight_button = gr.Button("View Flight", interactive=False, elem_id="confirm-button") 
                        
                        with gr.Column(visible=False, elem_classes=["flight-view"]) as outbound_flight_details:
                            with gr.Column(elem_classes=["flight-content"]):
                                with gr.Column(elem_classes=["flight-details"]):
                                    outbound_flight_details_box = gr.Markdown()
                                
                            with gr.Column(elem_classes=["flight-buttons"]):
                                with gr.Row(elem_classes=["button-row"]):
                                    outbound_details_go_back_button = gr.Button("Go Back", elem_classes=["secondary-btn"])
                                    outbound_booking_options_button = gr.Button("Finalise Flight", visible=False, elem_classes=["primary-btn"])
                                    get_return_flights_button = gr.Button("Get Return Flights", visible=False, elem_classes=["primary-btn"])
                                
                        with gr.Column(visible=False, elem_classes=["flight-view"]) as return_flight_cards:
                            with gr.Column(elem_classes=["flight-content"]):
                                with gr.Column(elem_classes=["cards-grid"]):
                                    return_card_html_components = []
                                    return_card_containers = []
                                    for card_index in range(MAX_FLIGHTS):
                                        with gr.Column(elem_classes=["card-container"], visible=False) as card_col:
                                            card_html = gr.HTML("")
                                            card_button = gr.Button("", elem_classes=["click-overlay"])
                                            return_card_html_components.append(card_html)
                                            # the button is being binded to function upon click event
                                            card_button.click(
                                                fn=lambda x=card_index: x,
                                                outputs=selected_return_index
                                            ).then(
                                                fn=UIManager.update_cards,
                                                inputs=[selected_return_index, return_flights_state],
                                                outputs=return_card_html_components
                                            )
                                        return_card_containers.append(card_col)

                            with gr.Column(elem_classes=["flight-buttons"]):
                                with gr.Row(elem_classes=["button-row"]):
                                    return_flights_go_back_button = gr.Button("Go Back", elem_classes=["secondary-btn"])
                                    return_view_flight_button = gr.Button("View Flight", interactive=False, elem_id="confirm-button")
                        
                        with gr.Column(visible=False, elem_classes=["flight-view"]) as return_flight_details:
                            with gr.Column(elem_classes=["flight-content"]):
                                with gr.Column(elem_classes=["flight-details"]):
                                    return_flight_details_box = gr.Markdown()

                            with gr.Column(elem_classes=["flight-buttons"]):
                                with gr.Row(elem_classes=["button-row"]):
                                    return_details_go_back_button = gr.Button("Go Back", elem_classes=["secondary-btn"])
                                    return_booking_options_button = gr.Button("Finalise Flight", elem_classes=["primary-btn"])
                        
                        with gr.Column(visible=False, elem_classes=["flight-view"]) as flight_booking_section:
                            with gr.Column(elem_id="booking-content"):
                                with gr.Column(elem_classes=["booking-content"]):
                                    gr.Markdown("# Flight Booking Options")
                                    gr.Markdown("Select a booking option to proceed to the booking partner's website.")
                                
                                    booking_groups = []
                                    info_mds = []
                                    booking_buttons = []
                                    booking_results = []
                                    booking_urls = []
                                
                                    for i in range(MAX_BOOKING_OPTIONS):
                                        with gr.Group(visible=False, elem_classes=["booking-option"]) as group:
                                            info_md = gr.Markdown("")
                                            # Row for Book button only
                                            with gr.Row(elem_classes=["button-row"]):
                                                btn = gr.Button("Book", elem_classes=["primary-btn"])
                                            result = gr.Markdown(label=f"Booking Result {i+1}", show_label=False)
                                            booking_url = gr.Textbox(
                                                value="",
                                                visible=False,
                                                elem_id=f"booking_url_{i}",
                                                show_label=False
                                            )
                                        
                                            info_mds.append(info_md)
                                            booking_buttons.append(btn)
                                            booking_results.append(result)
                                            booking_urls.append(booking_url)
                                        
                                            # Book button click - get booking URL and show markdown link
                                            btn.click(
                                                fn=create_booking_handler(i),
                                                inputs=booking_data_state,
                                                outputs=[booking_results[i], booking_urls[i]]
                                            ).then(
                                                fn=lambda url: gr.Info(f"Booking URL generated") if url else None,
                                                inputs=booking_urls[i],
                                                outputs=None  # Debug: Show URL in Gradio notification
                                            )
                                        booking_groups.append(group)

                            with gr.Column(elem_classes=["flight-buttons"]):
                                with gr.Row(elem_classes=["button-row"]):
                                    booking_done_button = gr.Button("Done", elem_id="confirm-button")

        with gr.Group():
            with gr.Row():
                message = gr.Textbox(show_label=False, placeholder="Enter your travel query", scale=5)
                mic_button = gr.Button("🎤", scale=0.5, min_width=80)

        with gr.Row():
            reset_button = gr.Button("Reset", variant="stop")
            go_button = gr.Button("Go!", variant="primary")
        
        mic_button.click(
            fn=toggle_transcription,
            inputs=[is_recording, message],
            outputs=[is_recording, message, mic_button]
        )

        
        # (0) user clicks on "go" button or "enter" inside the textbox -> message is processed and flight cards are shown if available
        message.submit(
            fn=lambda msg, hist: (
                msg,  # user_message_state
                hist + [{"role": "user", "content": msg}],  # chatbot (append user immediately)
                "",  # message (clear input)
                gr.update(visible=True),  # loader_group
                gr.update(value="Fetching outbound flights..."),  # loader_message
                gr.update(visible=False)  # error_message
            ),
            inputs=[message, chatbot],
            outputs=[user_message_state, chatbot, message, loader_group, loader_message, error_message]
        ).then(
            fn=travel_agent.process_message,
            inputs=[user_message_state, chatbot, thread_id_state],
            outputs=[chatbot, outbound_flights_state, initial_flight_payload]
        ).then(
            # NEW: Handle potential flight section reset if new flights were fetched
            fn=handle_new_flight_data,
            inputs=[outbound_flights_state, initial_flight_payload],
            outputs=[
                current_view,
                initial_flight_payload,
                outbound_flights_state,
                selected_outbound_index,
                return_flights_state,
                selected_return_index,
                booking_data_state,
                flight_section,
                *outbound_card_html_components,
                *outbound_card_containers,
                outbound_view_flight_button,
                outbound_flight_details_box,
                outbound_booking_options_button,
                get_return_flights_button,
                *return_card_html_components,
                *return_card_containers,
                return_view_flight_button,
                return_flight_details_box,
                *booking_groups,
                *info_mds,
                *booking_buttons,
                *booking_results,
                *booking_urls,
                loader_group,
                loader_message,
                error_message
            ]
        ).then(
            fn=lambda view, data: gr.update(visible=True, value=data.get("error", "")) if data.get("error") else gr.update(visible=False),
            inputs=[current_view, outbound_flights_state],
            outputs=error_message
        ).then(
            fn=UIManager.update_flight_interface,
            inputs=outbound_flights_state,
            outputs=[flight_section] + outbound_card_html_components + outbound_card_containers
        ).then(
            fn=update_button_visibility,
            inputs=initial_flight_payload,
            outputs=[outbound_booking_options_button, get_return_flights_button]
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        ).then(
            fn=lambda: (gr.update(visible=False), gr.update(value="")),
            outputs=[loader_group, loader_message]
        ).then(
            fn=lambda: (gr.update(value=""), gr.update(value="")),
            outputs=[message, user_message_state]
        )

        go_button.click(
            fn=lambda msg, hist: (
                msg,  # user_message_state
                hist + [{"role": "user", "content": msg}],  # chatbot (append user immediately)
                "",  # message (clear input)
                gr.update(visible=True),  # loader_group
                gr.update(value="Fetching outbound flights..."),  # loader_message
                gr.update(visible=False)  # error_message
            ),
            inputs=[message, chatbot],
            outputs=[user_message_state, chatbot, message, loader_group, loader_message, error_message]
        ).then(
            fn=travel_agent.process_message,
            inputs=[user_message_state, chatbot, thread_id_state],
            outputs=[chatbot, outbound_flights_state, initial_flight_payload]
        ).then(
            # NEW: Handle potential flight section reset if new flights were fetched
            fn=handle_new_flight_data,
            inputs=[outbound_flights_state, initial_flight_payload],
            outputs=[
                current_view,
                initial_flight_payload,
                outbound_flights_state,
                selected_outbound_index,
                return_flights_state,
                selected_return_index,
                booking_data_state,
                flight_section,
                *outbound_card_html_components,
                *outbound_card_containers,
                outbound_view_flight_button,
                outbound_flight_details_box,
                outbound_booking_options_button,
                get_return_flights_button,
                *return_card_html_components,
                *return_card_containers,
                return_view_flight_button,
                return_flight_details_box,
                *booking_groups,
                *info_mds,
                *booking_buttons,
                *booking_results,
                *booking_urls,
                loader_group,
                loader_message,
                error_message
            ]
        ).then(
            fn=lambda view, data: gr.update(visible=True, value=data.get("error", "")) if data.get("error") else gr.update(visible=False),
            inputs=[current_view, outbound_flights_state],
            outputs=error_message
        ).then(
            fn=UIManager.update_flight_interface,
            inputs=outbound_flights_state,
            outputs=[flight_section] + outbound_card_html_components + outbound_card_containers
        ).then(
            fn=update_button_visibility,
            inputs=initial_flight_payload,
            outputs=[outbound_booking_options_button, get_return_flights_button]
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        ).then(
            fn=lambda: (gr.update(visible=False), gr.update(value="")),
            outputs=[loader_group, loader_message]
        ).then(
            fn=lambda: (gr.update(value=""), gr.update(value="")),
            outputs=[message, user_message_state]
        )
        
        # (1) User clicks on the outbound flights cards -> view flight button becomes interactive
        selected_outbound_index.change(
            fn=lambda idx: gr.update(interactive=idx is not None),
            inputs=selected_outbound_index,
            outputs=outbound_view_flight_button
        )
        
        # (2) User clicks on the "view flight" button -> flight details are shown
        outbound_view_flight_button.click(
            fn=UIManager.get_flight_details,
            inputs=[selected_outbound_index, outbound_flights_state, initial_flight_payload],
            outputs=[current_view, outbound_flight_details_box]
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        )

        # (3) User clicks on the "go back" button -> outbound flight cards are shown again
        outbound_details_go_back_button.click(
            fn=lambda: (None, VIEW_OUTBOUND_CARDS),
            outputs=[selected_outbound_index, current_view]
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        ).then(
            fn=UIManager.update_cards,
            inputs=[selected_outbound_index, outbound_flights_state],
            outputs=outbound_card_html_components
        )

        # (4) user clicks on "finalise flight" button -> booking options are shown (type = 2)
        outbound_booking_options_button.click(
            fn=lambda: (gr.update(visible=True), gr.update(value="Fetching booking options..."), gr.update(visible=False)),
            outputs=[loader_group, loader_message, error_message]
        ).then(
            fn=UIManager.on_booking_options,
            inputs=[selected_outbound_index, outbound_flights_state, initial_flight_payload],
            outputs=[current_view, booking_data_state]
        ).then(
            fn=lambda view, data: gr.update(visible=True, value=data.get("error", "")) if data.get("error") else gr.update(visible=False),
            inputs=[current_view, booking_data_state],
            outputs=error_message
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        ).then(
            fn=UIManager.update_booking_ui,
            inputs=booking_data_state,
            outputs=booking_groups + info_mds + booking_buttons + booking_urls
        ).then(
            fn=lambda: (gr.update(visible=False), gr.update(value="")),
            outputs=[loader_group, loader_message]
        )

        # (5) user clicks on "get return flights" button -> return flight cards are show (type = 1)
        get_return_flights_button.click(
            fn=lambda: (gr.update(visible=True), gr.update(value="Fetching return flights..."), gr.update(visible=False)),
            outputs=[loader_group, loader_message, error_message]
        ).then(
            fn=UIManager.on_get_return_flights,
            inputs=[selected_outbound_index, outbound_flights_state, initial_flight_payload],
            outputs=[current_view, return_flights_state]
        ).then(
            fn=lambda view, data: gr.update(visible=True, value=data.get("error", "")) if data.get("error") else gr.update(visible=False),
            inputs=[current_view, return_flights_state],
            outputs=error_message
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        ).then(
            fn=UIManager.update_flight_interface,
            inputs=return_flights_state,
            outputs=[flight_section] + return_card_html_components + return_card_containers
        ).then(
            fn=lambda: (gr.update(visible=False), gr.update(value="")),
            outputs=[loader_group, loader_message]
        )

        # (6) user clicks on any of the return flight cards -> view flight button becomes interactive
        selected_return_index.change(
            fn=lambda idx: gr.update(interactive=idx is not None),
            inputs=selected_return_index,
            outputs=return_view_flight_button
        )

        # (7) use clicks on "go back" button -> outbound flight details are shown again
        return_flights_go_back_button.click(
            fn=UIManager.get_flight_details,
            inputs=[selected_outbound_index, outbound_flights_state, initial_flight_payload],
            outputs=[current_view, outbound_flight_details_box]
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        )

        # (8) user clicks on "view flight" button -> return flight details are shown
        return_view_flight_button.click(
            fn=UIManager.get_flight_details,
            inputs=[selected_return_index, return_flights_state, initial_flight_payload],
            outputs=[current_view, return_flight_details_box]
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        )

        # (9) use clicks on "go back" button -> return flight cards are shown again
        return_details_go_back_button.click(
            fn=lambda: (None, VIEW_RETURN_CARDS),
            outputs=[selected_return_index, current_view]
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        ).then(
            fn=UIManager.update_cards,
            inputs=[selected_return_index, return_flights_state],
            outputs=return_card_html_components
        )

        # (10) user clicks on "finalise flight" button -> booking options are shown
        return_booking_options_button.click(
            fn=lambda: (gr.update(visible=True), gr.update(value="Fetching booking options..."), gr.update(visible=False)),
            outputs=[loader_group, loader_message, error_message]
        ).then(
            fn=UIManager.on_booking_options,
            inputs=[selected_return_index, return_flights_state, initial_flight_payload],
            outputs=[current_view, booking_data_state]
        ).then(
            fn=lambda view, data: gr.update(visible=True, value=data.get("error", "")) if data.get("error") else gr.update(visible=False),
            inputs=[current_view, booking_data_state],
            outputs=error_message
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        ).then(
            fn=UIManager.update_booking_ui,
            inputs=booking_data_state,
            outputs=booking_groups + info_mds + booking_buttons + booking_urls
        ).then(
            fn=lambda: (gr.update(visible=False), gr.update(value="")),
            outputs=[loader_group, loader_message]
        )

        # (11) user clicks on "reset" button -> everything is reset
        reset_button.click(
            fn=complete_reset,
            outputs=[
                # Basic inputs/outputs
                message, chatbot, thread_id_state, is_recording, user_message_state,

                # State variables
                current_view, initial_flight_payload, outbound_flights_state,
                selected_outbound_index, return_flights_state, selected_return_index, booking_data_state,
                
                # UI visibility
                flight_section,
                
                # Outbound flight cards
                *outbound_card_html_components, *outbound_card_containers, outbound_view_flight_button,
                
                # Outbound flight details
                outbound_flight_details_box, outbound_booking_options_button, get_return_flights_button,
                
                # Return flight cards
                *return_card_html_components, *return_card_containers, return_view_flight_button,
                
                # Return flight details
                return_flight_details_box,
                
                # Booking section
                *booking_groups, *info_mds, *booking_buttons, *booking_results, *booking_urls,
                loader_group, loader_message, error_message
            ]
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        )

        # (12) user clicks on "done" button in booking section -> reset entire flight section
        booking_done_button.click(
            fn=reset_flight_section,
            outputs=[
                current_view,
                initial_flight_payload,
                outbound_flights_state,
                selected_outbound_index,
                return_flights_state,
                selected_return_index,
                booking_data_state,
                flight_section,
                *outbound_card_html_components,
                *outbound_card_containers,
                outbound_view_flight_button,
                outbound_flight_details_box,
                outbound_booking_options_button,
                get_return_flights_button,
                *return_card_html_components,
                *return_card_containers,
                return_view_flight_button,
                return_flight_details_box,
                *booking_groups,
                *info_mds,
                *booking_buttons,
                *booking_results,
                *booking_urls,
                loader_group,
                loader_message,
                error_message
            ]
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        )

        demo.load(init_chat, inputs=thread_id_state, outputs=chatbot)

    return demo

if __name__ == "__main__":
    demo = create_travel_app()
    demo.launch()