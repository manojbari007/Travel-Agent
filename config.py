"""
Configuration file for AI Travel Agent
Contains city coordinates, constants, and settings
"""

# City coordinates for Open-Meteo Weather API
CITY_COORDINATES = {
    "Delhi": {"lat": 28.6139, "lon": 77.2090},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Goa": {"lat": 15.2993, "lon": 74.1240},
    "Bangalore": {"lat": 12.9716, "lon": 77.5946},
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873},
}

# Available cities in the dataset
AVAILABLE_CITIES = list(CITY_COORDINATES.keys())

# Place types for filtering
PLACE_TYPES = ["beach", "temple", "fort", "museum", "park", "market", "lake", "monument"]

# Hotel amenities
HOTEL_AMENITIES = ["wifi", "pool", "gym", "breakfast", "parking", "spa"]

# Airlines in dataset
AIRLINES = ["IndiGo", "Air India", "SpiceJet", "Go First", "Vistara"]

# Default daily expense estimate (food, transport, activities)
DEFAULT_DAILY_EXPENSES = 2500  # INR per person

# Weather API
OPEN_METEO_API_URL = "https://api.open-meteo.com/v1/forecast"

# LLM Settings
DEFAULT_MODEL = "gemini-1.5-flash"
DEFAULT_TEMPERATURE = 0.3

# Trip constraints
MIN_TRIP_DAYS = 1
MAX_TRIP_DAYS = 14
MAX_TRAVELERS = 10
