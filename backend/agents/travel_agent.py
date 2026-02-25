import os
import sys
import json
import uuid
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel
from langgraph.prebuilt import ToolNode
from typing import Annotated, List, Dict, Tuple
from langgraph.graph.message import add_messages
from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
from backend.tools.airports import get_airport
from backend.tools.flights import get_flights
load_dotenv(override=True)

class State(BaseModel):
    messages: Annotated[List, add_messages]

class TravelAgent:
    google_api_key = os.getenv("google_api_key")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key
    )
    current_year = datetime.now().year
    TOOLS = [get_airport, get_flights]
    graph = None

    def __init__(self):
        system_message = f"""
            you are a smart travel agency agent, use the tool to lookup information.
            Do not ask multiple questions at once.
            You may look up information before asking a follow-up question if required.
            only lookup information when you are sure you want that.
            When gathering details on nearby relevant airports for outbound and inbound locations, list the top 5 options with its information, IATA code, full name, city, and distance/proximity, and let the user select from them.
            Always summarize and list all collected information (e.g., locations, dates, passenger details) clearly, then ask the user for confirmation before proceeding to list flights.
            Once details are finalized, respond with flight options based on them.
            Do not ask the user for the current year; assume it is {self.current_year}.
        """
        self.memory = MemorySaver()
        self.graph = self._build_graph(system_message)

    def _build_graph(self, system_message):
        """ Build the state graph for the travel agent """

        graph_builder = StateGraph(State)
        graph_builder.add_node("worker", lambda state: self._worker(state, system_message))
        graph_builder.add_node("tools", ToolNode(tools=self.TOOLS))
        graph_builder.add_edge(START, "worker")
        graph_builder.add_conditional_edges("worker", self._worker_router, {"tools": "tools", END: END})
        graph_builder.add_edge("tools", "worker")
        return graph_builder.compile(checkpointer=self.memory)

    def _worker(self, state: State, system_message: str):
        """ Worker node to process messages and invoke the LLM with tools """

        messages = [SystemMessage(content=system_message)] + state.messages
        worker_llm = self.llm.bind_tools(self.TOOLS)
        response = worker_llm.invoke(messages)
        return {'messages': [response]}

    def _worker_router(self, state: State) -> str:
        """ Decide whether to invoke tools or end the conversation """

        last_message = state.messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    @staticmethod
    def make_thread_id() -> str:
        """ Generate a unique thread ID """

        return str(uuid.uuid4())

    async def process_message(self, message: str, history: List, thread: str) -> Tuple[List, Dict, Dict]:
        """ Process a user message and return updated history, flight data and original params """
        if not message.strip() and len(history) == 0:
            initial_content = "Hello! Welcome to our travel chatbot. I'm here to help you find and book the perfect flights. Where would you like to go?"
            history = [{"role": "assistant", "content": initial_content}]
            return history, {}, None
            
        config = {"configurable": {"thread_id": thread}}
        # Get previous state to determine the length of existing messages
        previous_state = self.graph.get_state(config)
        previous_messages_len = len(previous_state.values.get("messages", [])) if previous_state and previous_state.values else 0
        
        # Append user to history if not already present (avoids duplicates when UI pre-adds it)
        if len(history) == 0 or not (
            history[-1].get("role") == "user" and 
            history[-1].get("content") == message
        ):
            user = {"role": "user", "content": message}
            history = history + [user]
        
        # As the accumulator is add_message, the state message will be updated automatically
        state = State(messages=[HumanMessage(content=message)])
        try:
            result = await self.graph.ainvoke(state, config=config)
        except Exception as e:
            print(f"Graph error: {e}")
            # Append error to history (which already has user)
            error_reply = {"role": "assistant", "content": f"System error: {str(e)}"}
            history = history + [error_reply]
            return history, {"error": str(e)}, None
        
        ai_msg = result["messages"][-1]
        reply = {"role": "assistant", "content": ai_msg.content}
        history = history + [reply]

        # Check if flights were fetched IN THIS TURN ONLY by slicing new messages
        new_messages = result["messages"][previous_messages_len:]
        flight_data, original_params = self._extract_flight_data_and_params(new_messages)
        flights_fetched_this_turn = self._has_available_flights(flight_data)
        
        if flights_fetched_this_turn:
            print("-"*50, "\n", original_params, "\n", "-"*50)
            history[-1]["content"] += "\n\nI've loaded the available flights in the panel to the right. Please select one to view details and booking options."
            print("**"*50)
            print(json.dumps(state.model_dump(), indent=2, default=str))
            # Return the flight data only if fetched this turn
            return history, flight_data, original_params
        else:
            # Return empty flight data if no new flights were fetched
            return history, {}, None


    def _extract_flight_data_and_params(self, messages: List) -> Tuple[Dict, Optional[Dict]]:
        """ Extract flight data and original params from tool response messages in the current turn """

        flight_data = {}
        original_params = None
        tool_call_id = None

        # Look for ToolMessage from get_flights in the current turn's messages
        for message in reversed(messages):
            if isinstance(message, ToolMessage) and message.name == "get_flights":
                try:
                    flight_data = json.loads(message.content)
                    tool_call_id = message.tool_call_id
                    break
                except json.JSONDecodeError:
                    flight_data = {"error": "Failed to parse flight data"}
                    break

        # If a ToolMessage was found, find the corresponding tool call in the same turn
        if tool_call_id:
            for prev_msg in reversed(messages):
                if hasattr(prev_msg, "tool_calls") and prev_msg.tool_calls:
                    for call in prev_msg.tool_calls:
                        if call.get("id") == tool_call_id and call.get("name") == "get_flights":
                            original_params = call.get("args", {}).get("params", {})
                            return flight_data, original_params

        return flight_data, original_params

    def _has_available_flights(self, flight_data: Dict) -> bool:
        """ Check if flight data contains available flights """
        
        return bool(flight_data.get("flights"))