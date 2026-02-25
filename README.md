# Travel Flight Booking Assistant

A modern, AI-powered flight booking application with an intuitive conversational interface. This application uses Google Gemini AI to understand natural language travel queries and helps users search, compare, and book flights through an interactive web interface.

## 🌟 Features

- **AI-Powered Conversational Interface**: Natural language processing using Google Gemini 2.0 Flash
- **Voice Input Support**: Real-time voice transcription using AssemblyAI
- **Flight Search**: Search for one-way and round-trip flights
- **Airport Discovery**: Intelligent airport lookup with proximity-based suggestions
- **Interactive UI**: Modern Gradio-based interface with dark/light theme support
- **Flight Comparison**: View detailed flight information, prices, durations, and stops
- **Booking Integration**: Direct booking links to partner websites
- **RESTful API**: FastAPI backend with comprehensive flight search endpoints
- **Modular Architecture**: Clean separation of concerns with organized codebase

## 🏗️ Architecture

The application follows a modular architecture:

```
travel-git-final-modular/
├── backend/          # FastAPI backend with routers, agents, and tools
├── frontend/         # Gradio-based UI components
├── shared_utils/     # Shared utilities (logging, data loading)
└── flight_responses/ # Sample flight data and airport codes
```

### Components

- **Backend**: FastAPI application with routers for flights, airports, and geolocation
- **AI Agent**: LangGraph-based travel agent using Google Gemini
- **Tools**: Airport lookup and flight search tools integrated with SerpAPI
- **Frontend**: Gradio interface with voice transcription and interactive flight selection
- **Transcription**: AssemblyAI integration for voice-to-text conversion

## 🛠️ Tech Stack

### Core Technologies
- **Python 3.12+**: Primary programming language
- **FastAPI**: Modern, fast web framework for building APIs
- **Gradio**: User-friendly interface for ML applications
- **LangGraph**: State machine framework for building AI agents
- **LangChain**: Framework for developing applications with LLMs

### AI & ML
- **Google Gemini 2.0 Flash**: Large language model for natural language understanding
- **AssemblyAI**: Real-time speech-to-text transcription

### APIs & Services
- **SerpAPI**: Google Flights search integration
- **Google Search Results**: Additional search capabilities

### Dependencies
- **uvicorn**: ASGI server for FastAPI
- **httpx**: Async HTTP client
- **pydantic**: Data validation
- **python-dotenv**: Environment variable management
- **pyaudio**: Audio input for voice transcription

## 📦 Installation

### Prerequisites

- Python 3.12 or higher
- `uv` package manager (recommended) or `pip`
- API keys for:
  - Google Gemini API
  - SerpAPI
  - AssemblyAI (for voice transcription)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone [<repository-url>](https://github.com/deep-crestskillserve/travel-final-modular.git)
   cd travel-git-final-modular
   ```

2. **Install dependencies using uv (recommended)**
   ```bash
   uv sync
   ```

   Or using pip:
   ```bash
   pip install -e .
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   google_api_key=your_google_gemini_api_key
   SERPAPI_API_KEY=your_serpapi_key
   ASSEMBLYAI_API_KEY=your_assemblyai_key
   ```

4. **Verify installation**
   ```bash
   python -c "import fastapi, gradio, langchain; print('Dependencies installed successfully!')"
   ```

## 🚀 Usage

### Running the Application

1. **Start the FastAPI backend** (in one terminal):
   ```bash
   python backend/main.py
   ```
   The API will be available at `http://localhost:8000`

2. **Start the Gradio frontend** (in another terminal):
   ```bash
   python frontend/main.py
   ```
   The UI will be available at `http://localhost:7860` (or the URL shown in the terminal)

### Using the Application

1. **Text Input**: Type your travel query in natural language, e.g.:
   - "I want to fly from New York to London on March 15th"
   - "Find flights from Mumbai to Delhi for 2 adults on 2024-12-20"
   - "Show me round trip flights from Paris to Tokyo leaving on May 1st and returning on May 15th"

2. **Voice Input**: Click the microphone button (🎤) to start voice recording, then click again to stop and transcribe

3. **Flight Selection**: 
   - Browse available flights in the interactive cards
   - Click on a flight card to view detailed information
   - For round trips, select outbound flight first, then return flight

4. **Booking**: 
   - Click "Finalise Flight" after selecting your preferred flight
   - Review booking options from different partners
   - Click "Book" to get redirected to the booking partner's website

## 📡 API Documentation

### FastAPI Endpoints

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

#### Main Endpoints

- **GET `/api/outbound-flights`**: Search for outbound flights
  - Query parameters: `departure_id`, `arrival_id`, `outbound_date`, `adults`, `children`, `return_date`
  
- **GET `/api/return-flights`**: Search for return flights (round trip)
  - Query parameters: `departure_id`, `arrival_id`, `outbound_date`, `return_date`, `adults`, `children`, `departure_token`
  
- **GET `/api/bookingdata`**: Get booking options for selected flights
  - Query parameters: `departure_id`, `arrival_id`, `outbound_date`, `adults`, `children`, `return_date`, `booking_token`

- **GET `/api/airports`**: Search for airports by location
- **GET `/api/geolocation`**: Get geolocation data for locations

### API Workflow

1. **One-Way Flights**:
   - Call `/api/outbound-flights` → Get `booking_token`
   - Call `/api/bookingdata` with `booking_token` → Get booking options

2. **Round-Trip Flights**:
   - Call `/api/outbound-flights` with `return_date` → Get `departure_token`
   - Call `/api/return-flights` with `departure_token` → Get `booking_token`
   - Call `/api/bookingdata` with `booking_token` → Get booking options

## 📁 Project Structure

```
travel-git-final-modular/
├── backend/
│   ├── agents/
│   │   └── travel_agent.py      # LangGraph-based AI travel agent
│   ├── routers/
│   │   ├── flights.py            # Flight search API endpoints
│   │   ├── airports.py           # Airport lookup endpoints
│   │   └── geolocation.py        # Geolocation endpoints
│   ├── tools/
│   │   ├── flights.py            # Flight search tool for AI agent
│   │   └── airports.py           # Airport lookup tool for AI agent
│   ├── transcript/
│   │   └── main.py               # AssemblyAI transcription service
│   ├── utils.py                 # Backend utility functions
│   └── main.py                   # FastAPI application entry point
├── frontend/
│   ├── components/
│   │   └── ui_manager.py        # UI state management and updates
│   ├── images/                  # UI assets (icons, etc.)
│   ├── utils.py                 # Frontend utility functions
│   └── main.py                   # Gradio application entry point
├── shared_utils/
│   ├── logger.py                # JSON-formatted logging utility
│   └── load_data.py             # Shared data loading utilities
├── flight_responses/            # Sample flight data and test responses
├── pyproject.toml               # Project dependencies and metadata
├── uv.lock                      # Dependency lock file
└── README.md                    # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `google_api_key` | Google Gemini API key | Yes |
| `SERPAPI_API_KEY` | SerpAPI key for flight searches | Yes |
| `ASSEMBLYAI_API_KEY` | AssemblyAI key for voice transcription | Optional |

### API Configuration

The application uses the following default settings:
- **Currency**: INR (Indian Rupees)
- **Language**: English (en)
- **Country**: India (in)
- **Deep Search**: Enabled for comprehensive flight results

```

### Code Structure

- **Modular Design**: Each component (backend, frontend, shared_utils) is self-contained
- **Type Safety**: Uses Pydantic models for data validation
- **Async/Await**: Backend uses async/await for better performance
- **State Management**: LangGraph for AI agent state, Gradio State for UI state

### Logging

The application uses JSON-formatted logging. Logs are output to stdout with the following structure:
```json
{
  "timestamp": "2024-01-01 12:00:00.000",
  "message": "Log message",
  "module": "module_name",
  "line": 123
}
```

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- SerpAPI for flight search integration
- AssemblyAI for voice transcription
- Gradio for the user interface framework
- LangChain and LangGraph for AI agent framework

## 📞 Support

For issues, questions, or contributions, please open an issue on the repository.

---

**Note**: Make sure to keep your API keys secure and never commit them to version control. Use environment variables or a `.env` file (which should be in `.gitignore`).
