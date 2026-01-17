# 🛫 AI Travel Agent

An intelligent travel planning application that creates personalized trip itineraries using natural language input.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)

## ✨ Features

- **Natural Language Input**: Type "Plan a 3 day trip from Mumbai to Goa under 20k"
- **Budget Enforcement**: Strictly respects your budget constraints
- **Fuzzy Matching**: Handles typos like "hyderbad" → "Hyderabad"
- **Memory**: Remembers context across conversation turns
- **Real Weather**: Fetches actual forecasts from Open-Meteo API
- **Smart Recommendations**: Selects best flights, hotels, and places

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## 📁 Project Structure

```
Travel-Agent/
├── app.py                 # Streamlit UI
├── config.py              # Configuration
├── agent/
│   └── travel_agent.py    # Main agent logic
├── tools/
│   ├── flight_tool.py     # Flight search
│   ├── hotel_tool.py      # Hotel recommendations
│   ├── places_tool.py     # Attractions discovery
│   ├── weather_tool.py    # Weather forecasts
│   └── budget_tool.py     # Budget calculation
├── utils/
│   ├── helpers.py         # Utility functions
│   └── query_parser.py    # NL query parser
└── Data/
    ├── flights.json       # 30 flights
    ├── hotels.json        # 40 hotels
    └── places.json        # 40 attractions
```

## 💬 Example Queries

| Query | What It Does |
|-------|--------------|
| "3 day trip Mumbai to Goa" | Plans a balanced budget trip |
| "Budget trip Delhi to Jaipur under 15k" | Finds cheapest options within budget |
| "5 day luxury trip for 2 people" | Premium hotels, higher daily allowance |
| "Weekend getaway to Bangalore" | 2-day trip with fuzzy date handling |

## 🔧 How It Works

1. **Query Parser** extracts: source, destination, days, budget, travelers
2. **Flight Tool** finds cheapest/fastest flights
3. **Hotel Tool** selects best value within budget
4. **Weather Tool** fetches real forecasts
5. **Budget Enforcer** ensures total fits your limit
6. **Itinerary Builder** creates day-wise plan

## 🌍 Available Cities

Delhi, Mumbai, Goa, Bangalore, Chennai, Hyderabad, Kolkata, Jaipur

## ⚙️ Configuration

Edit `config.py` to modify:
- City coordinates
- Default daily expenses (₹2,500)
- Available place types

## 📊 Budget Logic

```
Total = (Flight × 2 × Travelers) + (Hotel × Nights) + (Daily × Days × Travelers)
```

If budget not feasible, agent explains why and suggests minimum needed.

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Agent**: Custom Python (LangChain-compatible)
- **Data**: JSON files
- **Weather API**: Open-Meteo (free)
- **NLP**: Regex + fuzzy matching

## 📝 License

MIT License
