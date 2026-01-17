"""
Weather Lookup Tool for AI Travel Agent
Uses Open-Meteo API (free, no API key required) to get weather forecasts
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import CITY_COORDINATES, OPEN_METEO_API_URL


class WeatherLookupInput(BaseModel):
    """Input schema for weather lookup"""
    city: str = Field(description="City to get weather for (e.g., 'Goa', 'Delhi')")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    num_days: int = Field(default=3, description="Number of days to forecast (1-14)")


def get_weather_code_description(code: int) -> tuple:
    """Convert WMO weather code to description and emoji"""
    weather_codes = {
        0: ("Clear sky", "☀️"),
        1: ("Mainly clear", "🌤️"),
        2: ("Partly cloudy", "⛅"),
        3: ("Overcast", "☁️"),
        45: ("Foggy", "🌫️"),
        48: ("Depositing rime fog", "🌫️"),
        51: ("Light drizzle", "🌧️"),
        53: ("Moderate drizzle", "🌧️"),
        55: ("Dense drizzle", "🌧️"),
        61: ("Slight rain", "🌧️"),
        63: ("Moderate rain", "🌧️"),
        65: ("Heavy rain", "🌧️"),
        71: ("Slight snow", "🌨️"),
        73: ("Moderate snow", "🌨️"),
        75: ("Heavy snow", "🌨️"),
        77: ("Snow grains", "🌨️"),
        80: ("Slight rain showers", "🌦️"),
        81: ("Moderate rain showers", "🌦️"),
        82: ("Violent rain showers", "⛈️"),
        85: ("Slight snow showers", "🌨️"),
        86: ("Heavy snow showers", "🌨️"),
        95: ("Thunderstorm", "⛈️"),
        96: ("Thunderstorm with slight hail", "⛈️"),
        99: ("Thunderstorm with heavy hail", "⛈️"),
    }
    return weather_codes.get(code, ("Unknown", "🌡️"))


def get_weather(
    city: str,
    start_date: str,
    num_days: int = 3
) -> dict:
    """
    Get weather forecast for a city and date range.
    
    Args:
        city: City name
        start_date: Start date (YYYY-MM-DD)
        num_days: Number of days to forecast
        
    Returns:
        Dictionary with weather data for each day
    """
    # Get city coordinates
    city_title = city.title()
    if city_title not in CITY_COORDINATES:
        return {
            "success": False,
            "message": f"City '{city}' not found in database",
            "available_cities": list(CITY_COORDINATES.keys()),
            "forecast": []
        }
    
    coords = CITY_COORDINATES[city_title]
    
    # Calculate end date
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = start + timedelta(days=num_days - 1)
        end_date = end.strftime("%Y-%m-%d")
    except ValueError:
        return {
            "success": False,
            "message": "Invalid date format. Use YYYY-MM-DD",
            "forecast": []
        }
    
    # Make API request
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_probability_max"],
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "Asia/Kolkata"
    }
    
    try:
        response = requests.get(OPEN_METEO_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        # Return mock data if API fails (for development/demo)
        return get_mock_weather(city, start_date, num_days)
    
    # Parse response
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    weather_codes = daily.get("weather_code", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    precipitation = daily.get("precipitation_probability_max", [])
    
    forecast = []
    for i, date in enumerate(dates):
        code = weather_codes[i] if i < len(weather_codes) else 0
        description, emoji = get_weather_code_description(code)
        
        forecast.append({
            "day": i + 1,
            "date": date,
            "condition": description,
            "emoji": emoji,
            "temperature_max": max_temps[i] if i < len(max_temps) else 30,
            "temperature_min": min_temps[i] if i < len(min_temps) else 20,
            "temperature_display": f"{max_temps[i] if i < len(max_temps) else 30}°C / {min_temps[i] if i < len(min_temps) else 20}°C",
            "precipitation_chance": precipitation[i] if i < len(precipitation) else 0
        })
    
    # Generate weather summary
    avg_max = sum(f["temperature_max"] for f in forecast) / len(forecast) if forecast else 30
    conditions = [f["condition"] for f in forecast]
    
    return {
        "success": True,
        "city": city_title,
        "start_date": start_date,
        "end_date": end_date,
        "num_days": num_days,
        "forecast": forecast,
        "summary": f"Average high of {avg_max:.1f}°C. Conditions: {', '.join(set(conditions))}.",
        "recommendations": get_weather_recommendations(forecast)
    }


def get_mock_weather(city: str, start_date: str, num_days: int) -> dict:
    """Generate mock weather data for demo/fallback"""
    import random
    
    conditions = [
        ("Clear sky", "☀️", 32, 24),
        ("Partly cloudy", "⛅", 30, 23),
        ("Mainly clear", "🌤️", 31, 22),
        ("Slight rain showers", "🌦️", 28, 21),
    ]
    
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    except:
        start = datetime.now()
    
    forecast = []
    for i in range(num_days):
        condition = random.choice(conditions)
        date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        forecast.append({
            "day": i + 1,
            "date": date,
            "condition": condition[0],
            "emoji": condition[1],
            "temperature_max": condition[2] + random.randint(-2, 2),
            "temperature_min": condition[3] + random.randint(-2, 2),
            "temperature_display": f"{condition[2]}°C / {condition[3]}°C",
            "precipitation_chance": random.randint(0, 30)
        })
    
    return {
        "success": True,
        "city": city.title(),
        "start_date": start_date,
        "num_days": num_days,
        "forecast": forecast,
        "summary": "Weather data (simulated for demo).",
        "recommendations": get_weather_recommendations(forecast),
        "note": "Using simulated weather data"
    }


def get_weather_recommendations(forecast: list) -> list:
    """Generate packing/activity recommendations based on weather"""
    recommendations = []
    
    max_temps = [f["temperature_max"] for f in forecast]
    conditions = [f["condition"].lower() for f in forecast]
    
    if any(t > 30 for t in max_temps):
        recommendations.append("🧴 Pack sunscreen and stay hydrated")
    if any(t < 20 for t in max_temps):
        recommendations.append("🧥 Bring a light jacket for cooler evenings")
    if any("rain" in c for c in conditions):
        recommendations.append("☔ Pack an umbrella or rain jacket")
    if any("clear" in c or "sunny" in c for c in conditions):
        recommendations.append("🕶️ Great weather for outdoor activities!")
    
    if not recommendations:
        recommendations.append("👍 Weather looks pleasant for your trip!")
    
    return recommendations


@tool(args_schema=WeatherLookupInput)
def WeatherLookupTool(
    city: str,
    start_date: str,
    num_days: int = 3
) -> str:
    """
    Get weather forecast for a destination city and travel dates.
    Uses the free Open-Meteo API for accurate forecasts.
    Use this tool to check weather conditions for travel planning.
    """
    result = get_weather(city, start_date, num_days)
    return json.dumps(result, indent=2)
