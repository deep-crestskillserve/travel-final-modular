import gradio as gr
from frontend.utils import book_flight
from frontend.components.ui_manager import UIManager
from backend.agents.travel_agent import TravelAgent

MAX_FLIGHTS = 20
MAX_BOOKING_OPTIONS = 10
VIEW_OUTBOUND_CARDS = "outbound cards"
VIEW_RETURN_CARDS = "return cards"
VIEW_OUTBOUND_DETAILS = "outbound details"
VIEW_RETURN_DETAILS = "return details"
VIEW_BOOKING = "booking"

CSS = """
    .card-container {
        position: relative;
        width: 300px;
        margin: 15px;
        background: #1e293b;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .card {
        padding: 20px;
        color: #f1f5f9;
        text-align: left;
    }

    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    }

    .logo-chain {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 15px;
    }

    .logo-chain img {
        max-height: 40px;
        width: auto;
        filter: brightness(0) invert(1);
    }

    .route {
        font-weight: 600;
        font-size: 16px;
        color: #e2e8f0;
        margin-bottom: 10px;
    }

    .price {
        font-weight: 700;
        color: #34d399;
        font-size: 18px;
        margin-bottom: 10px;
    }

    .duration {
        font-size: 14px;
        color: #94a3b8;
        margin-bottom: 10px;
    }

    .stops {
        font-size: 14px;
        color: #94a3b8;
    }

    .click-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0;
        cursor: pointer;
        transition: opacity 0.3s ease;
    }

    .click-overlay:hover {
        opacity: 0.1;
        background: #ffffff;
    }

    #flight-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 15px;
        background: #0f172a;
        border-radius: 12px;
        border: 1px solid #334155;
    }

    #confirm-button {
        margin-top: 20px;
        width: 100%;
        background-color: #34d399;
        color: #1e293b;
        border: none;
        padding: 10px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }

    #confirm-button:hover {
        background-color: #2dd4bf;
    }

    #details-section {
        margin-top: 20px;
        padding: 15px;
        background: #1e293b;
        border-radius: 12px;
        color: #f1f5f9;
    }

    .chatbot {
        background: #0f172a;
        border-radius: 12px;
        padding: 10px;
        color: #f1f5f9;
    }
"""

def create_travel_app():
    """ Create the Gradio travel app with all components and interactions """

    travel_agent = TravelAgent()

    def create_booking_handler(option_index):
        """ Create booking handler for specific option """

        def handle_booking(booking_data):
            booking_options = booking_data.get("booking_options", []) if booking_data else []
            if option_index < len(booking_options):
                post_data = booking_options[option_index].get("together", {}).get("booking_request", {}).get("post_data", "")
                return book_flight(post_data)
            return "⚠️ Invalid option"
        return handle_booking

    def update_button_visibility(params):
        """ Update button visibility of outbound_flight_cards buttons based on trip type """

        if not params:
            return gr.update(visible=False), gr.update(visible=False)
        
        has_return_date = params.get("return_date") is not None
        
        if has_return_date: # Round-trip
            # Show "Get Return Flights" button, hide "Finalise Flight" button
            return gr.update(visible=False), gr.update(visible=True)
        else:  # One-way
            # Show "Finalise Flight" button, hide "Get Return Flights" button
            return gr.update(visible=True), gr.update(visible=False)
    
    def complete_reset():
        """ Complete reset of all states and UI components """

        # Reset all state variables
        new_thread_id = travel_agent.make_thread_id()
        
        # Create empty card updates
        empty_card_html = [""] * MAX_FLIGHTS
        hidden_card_containers = [gr.update(visible=False)] * MAX_FLIGHTS
        
        # Create empty booking updates
        hidden_booking_groups = [gr.update(visible=False)] * MAX_BOOKING_OPTIONS
        empty_info_updates = [""] * MAX_BOOKING_OPTIONS
        hidden_booking_buttons = [gr.update(visible=False)] * MAX_BOOKING_OPTIONS
        empty_booking_results = [""] * MAX_BOOKING_OPTIONS
        
        return (
            # Basic inputs/outputs
            "",  # message
            [],  # chatbot
            new_thread_id,  # thread_id_state
            
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
        )

    with gr.Blocks(theme=gr.themes.Default(primary_hue="emerald"), css=CSS) as demo:
        gr.Markdown("Enter your travel query")
        
        thread_id_state = gr.State(travel_agent.make_thread_id())
        current_view = gr.State(value=VIEW_OUTBOUND_CARDS)
        initial_flight_payload = gr.State(value={})
        outbound_flights_state = gr.State(value={})
        selected_outbound_index = gr.State(value=None)
        return_flights_state = gr.State(value={})
        selected_return_index = gr.State(value=None)
        booking_data_state = gr.State(value={})
        
        with gr.Row():
            with gr.Column():
                chatbot = gr.Chatbot(label="Travel Chatbot", height=600, type="messages")
            
            with gr.Column(visible=False, scale=1) as flight_section:
                with gr.Group():                    
                    with gr.Column(elem_id="flight-container", scale=1):

                        with gr.Column(visible=True) as outbound_flight_cards:
                            with gr.Row():
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
                            outbound_view_flight_button = gr.Button("View Flight", interactive=False, elem_id="confirm-button")
                        
                        with gr.Column(visible=False) as outbound_flight_details:
                            outbound_flight_details_box = gr.Markdown()
                            with gr.Row():
                                outbound_details_go_back_button = gr.Button("Go Back")
                                outbound_booking_options_button = gr.Button("Finalise Flight", visible=False)
                                get_return_flights_button = gr.Button("Get Return Flights", visible=False)
                                
                        with gr.Column(visible=False) as return_flight_cards:
                            with gr.Row():
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

                            with gr.Row():
                                return_flights_go_back_button = gr.Button("Go Back")
                                return_view_flight_button = gr.Button("View Flight", interactive=False, elem_id="confirm-button")
                        
                        with gr.Column(visible=False) as return_flight_details:
                            return_flight_details_box = gr.Markdown()
                            with gr.Row():
                                return_details_go_back_button = gr.Button("Go Back")
                                return_booking_options_button = gr.Button("Finalise Flight")
                        
                        with gr.Column(visible=False) as flight_booking_section:
                            gr.Markdown("# Flight Booking Options")
                            gr.Markdown("Select a booking option to proceed to the booking partner's website.")
                            
                            booking_groups = []
                            info_mds = []
                            booking_buttons = []
                            booking_results = []
                            
                            for i in range(MAX_BOOKING_OPTIONS):
                                with gr.Group(visible=False) as group:
                                    info_md = gr.Markdown("")
                                    btn = gr.Button("Book")
                                    result = gr.Markdown(label=f"Booking Result {i+1}")
                                    
                                    info_mds.append(info_md)
                                    booking_buttons.append(btn)
                                    booking_results.append(result)
                                    
                                    btn.click(
                                        fn=create_booking_handler(i),
                                        inputs=booking_data_state,
                                        outputs=booking_results[i]
                                    )
                                booking_groups.append(group)

        with gr.Group():
            with gr.Row():
                message = gr.Textbox(show_label=False, placeholder="Enter your travel query")
        with gr.Row():
            reset_button = gr.Button("Reset", variant="stop")
            go_button = gr.Button("Go!", variant="primary")

        # (0) user clicks on "go" button or "enter" inside the textbox -> message is processed and flight cards are shown if available
        message.submit(
            fn=travel_agent.process_message,
            inputs=[message, chatbot, thread_id_state],
            outputs=[chatbot, outbound_flights_state, initial_flight_payload]
        ).then(
            fn=UIManager.update_flight_interface,
            inputs=outbound_flights_state,
            outputs=[flight_section] + outbound_card_html_components + outbound_card_containers
        ).then(
            fn=update_button_visibility,
            inputs=initial_flight_payload,
            outputs=[outbound_booking_options_button, get_return_flights_button]
        )

        go_button.click(
            fn=travel_agent.process_message,
            inputs=[message, chatbot, thread_id_state],
            outputs=[chatbot, outbound_flights_state, initial_flight_payload]
        ).then(
            fn=UIManager.update_flight_interface,
            inputs=outbound_flights_state,
            outputs=[flight_section] + outbound_card_html_components + outbound_card_containers
        ).then(
            fn=update_button_visibility,
            inputs=initial_flight_payload,
            outputs=[outbound_booking_options_button, get_return_flights_button]
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
            fn=UIManager.on_booking_options,
            inputs=[selected_outbound_index, outbound_flights_state, initial_flight_payload],
            outputs=[current_view, booking_data_state]
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        ).then(
            fn=UIManager.update_booking_ui,
            inputs=booking_data_state,
            outputs=booking_groups + info_mds + [b for b in booking_buttons]
        )

        # (5) user clicks on "get return flights" button -> return flight cards are show (type = 1)
        get_return_flights_button.click(
            fn=UIManager.on_get_return_flights,
            inputs=[selected_outbound_index, outbound_flights_state, initial_flight_payload],
            outputs=[current_view, return_flights_state]
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        ).then(
            fn=UIManager.update_flight_interface,
            inputs=return_flights_state,
            outputs=[flight_section] + return_card_html_components + return_card_containers
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
            fn=UIManager.on_booking_options,
            inputs=[selected_return_index, return_flights_state, initial_flight_payload],
            outputs=[current_view, booking_data_state]
        ).then(
            fn=UIManager.update_view,
            inputs=current_view,
            outputs=[outbound_flight_cards, return_flight_cards, outbound_flight_details, return_flight_details, flight_booking_section]
        ).then(
            fn=UIManager.update_booking_ui,
            inputs=booking_data_state,
            outputs=booking_groups + info_mds + [b for b in booking_buttons]
        )

        # (11) user clicks on "reset" button -> everything is reset
        reset_button.click(
            fn=complete_reset,
            outputs=[
                # Basic inputs/outputs
                message, chatbot, thread_id_state,

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
                *booking_groups, *info_mds, *booking_buttons, *booking_results
            ]
        )

    return demo

if __name__ == "__main__":
    demo = create_travel_app()
    demo.launch()