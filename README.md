# 🛫 Travel Assistant - AI-Powered Flight Booking System

A sophisticated travel assistant application that combines AI-powered conversation with real-time flight search and booking capabilities. Built with FastAPI backend, Gradio frontend, and integrated with Google Flights API through SerpAPI.

## ✨ Features

### 🤖 AI-Powered Travel Assistant
- **Conversational Interface**: Natural language processing for travel queries
- **Voice Input Support**: Real-time speech-to-text transcription using AssemblyAI
- **Smart Airport Detection**: Automatic airport code resolution and suggestions
- **Context-Aware Responses**: Maintains conversation context throughout the booking process

### ✈️ Flight Search & Booking
- **Real-time Flight Search**: Integration with Google Flights via SerpAPI
- **One-way & Round-trip**: Support for both travel types
- **Interactive Flight Cards**: Beautiful, responsive flight selection interface
- **Detailed Flight Information**: Comprehensive flight details with airline logos, stops, duration
- **Booking Integration**: Direct booking links to partner websites

### 🎨 Modern UI/UX
- **Dark Theme**: Sleek, modern interface with dark mode styling
- **Responsive Design**: Optimized for desktop and mobile devices
- **Interactive Components**: Smooth animations and hover effects
- **Real-time Updates**: Dynamic UI updates based on user interactions

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── agents/           # AI agent implementation
├── routers/          # API endpoints
├── tools/            # External service integrations
├── transcript/       # Speech-to-text functionality
└── utils.py          # Utility functions
```

### Frontend (Gradio)
```
frontend/
├── components/       # UI components and managers
└── utils.py         # Frontend utilities
```

### Shared Utilities
```
shared_utils/
├── logger.py        # Logging configuration
└── load_data.py     # Data loading utilities
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- UV package manager (recommended) or pip
- API keys for:
  - Google Generative AI
  - SerpAPI
  - AssemblyAI (for voice features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd travel-git-final-modular
   ```

2. **Install dependencies**
   ```bash
   # Using UV (recommended)
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_google_api_key
   SERPAPI_API_KEY=your_serpapi_key
   ASSEMBLYAI_API_KEY=your_assemblyai_key
   ```

4. **Run the application**
   ```bash
   # Start the backend API
   python backend/main.py
   
   # In another terminal, start the frontend
   python frontend/main.py
   ```

5. **Access the application**
   - Frontend: http://localhost:7860
   - Backend API: http://localhost:8000

## 📋 API Endpoints

### Flight Search
- `GET /api/flights/search` - Search for flights
- `GET /api/airports/search` - Search airports
- `GET /api/geolocation/search` - Get location information

### Request Examples
```python
# Search for flights
{
    "departure_id": "DEL",
    "arrival_id": "BOM", 
    "outbound_date": "2024-02-15",
    "adults": 1,
    "children": 0
}

# Round-trip search
{
    "departure_id": "DEL",
    "arrival_id": "BOM",
    "outbound_date": "2024-02-15", 
    "return_date": "2024-02-20",
    "adults": 1
}
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **LangGraph**: AI agent orchestration and state management
- **Google Generative AI**: Large language model integration
- **SerpAPI**: Google Flights data extraction
- **AssemblyAI**: Real-time speech transcription
- **Pydantic**: Data validation and serialization

### Frontend
- **Gradio**: Rapid UI development for ML applications
- **Custom CSS**: Dark theme and responsive design
- **JavaScript**: Interactive components and animations

### Utilities
- **Python-dotenv**: Environment variable management
- **Logging**: Comprehensive logging system
- **UV**: Fast Python package manager

## 🎯 Usage Examples

### Basic Flight Search
```
User: "I want to fly from Delhi to Mumbai on February 15th"
Assistant: [Shows available flights with prices, airlines, and booking options]
```

### Round-trip Booking
```
User: "Find me flights from Delhi to Mumbai on Feb 15th, returning on Feb 20th"
Assistant: [Shows outbound flights → return flights → booking options]
```

### Voice Input
```
User: [Clicks microphone] "Book a flight to New York next week"
Assistant: [Processes voice input and shows relevant flights]
```

## 🔧 Configuration

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Generative AI API key | Yes |
| `SERPAPI_API_KEY` | SerpAPI key for flight data | Yes |
| `ASSEMBLYAI_API_KEY` | AssemblyAI key for voice features | Yes |

### Customization
- Modify `MAX_FLIGHTS` and `MAX_BOOKING_OPTIONS` in `frontend/main.py`
- Update CSS variables in the `CSS` section for theme customization
- Configure API endpoints in `frontend/components/ui_manager.py`

## 🧪 Development

### Project Structure
```
travel-git-final-modular/
├── backend/                 # FastAPI backend
│   ├── agents/             # AI agent logic
│   ├── routers/            # API routes
│   ├── tools/              # External integrations
│   └── transcript/         # Speech processing
├── frontend/               # Gradio frontend
│   ├── components/         # UI components
│   └── images/             # Static assets
├── shared_utils/           # Shared utilities
├── pyproject.toml          # Project configuration
└── README.md              # This file
```

### Adding New Features
1. **Backend**: Add new routers in `backend/routers/`
2. **Frontend**: Extend UI components in `frontend/components/`
3. **AI Agent**: Modify agent logic in `backend/agents/`

## 🐛 Troubleshooting

### Common Issues
1. **API Key Errors**: Ensure all environment variables are set correctly
2. **Port Conflicts**: Change ports in `main.py` files if 8000/7860 are occupied
3. **Dependency Issues**: Use `uv sync` or `pip install -r requirements.txt`

### Debug Mode
Enable debug logging by setting log level in `shared_utils/logger.py`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**Built with ❤️ using FastAPI, Gradio, and AI technologies**
