"""
Travel Agent - LangChain ReAct Agent for Trip Planning
Uses multiple tools to create optimized travel itineraries with budget enforcement
"""

import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tools.flight_tool import search_flights
from tools.hotel_tool import search_hotels
from tools.places_tool import search_places
from tools.weather_tool import get_weather
from tools.budget_tool import estimate_budget
from config import DEFAULT_DAILY_EXPENSES, AVAILABLE_CITIES


class TravelAgent:
    """
    AI Travel Agent that creates optimized trip itineraries.
    Enforces budget constraints strictly.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
    
    def plan_trip(
        self,
        source: str,
        destination: str,
        start_date: str,
        num_days: int,
        num_travelers: int = 1,
        budget_preference: str = "balanced",
        min_hotel_stars: int = 3,
        preferred_activities: Optional[list] = None,
        max_budget: Optional[int] = None
    ) -> Dict[str, Any]:
        """Plan a complete trip with strict budget enforcement."""
        
        reasoning = []
        
        # Step 1: Find cheapest flight
        reasoning.append("🔍 Searching for flights...")
        flight_result = search_flights(source, destination, sort_by="cheapest")
        
        if not flight_result["success"]:
            return {
                "success": False,
                "error": f"No direct flights from {source} to {destination}",
                "suggestion": f"Try: {', '.join(AVAILABLE_CITIES)}",
                "reasoning": reasoning
            }
        
        selected_flight = flight_result["recommended"]
        flight_cost = selected_flight["price"] * 2 * num_travelers  # Round trip
        reasoning.append(f"✈️ Found flight: {selected_flight['airline']} at ₹{selected_flight['price']:,}")
        
        # Step 2: Calculate remaining budget for hotel
        nights = num_days - 1
        if max_budget:
            # Calculate what we can afford for hotel
            # Budget = Flight + Hotel + Daily expenses
            daily_expense = 1500 if budget_preference == "budget" else DEFAULT_DAILY_EXPENSES
            daily_cost = daily_expense * num_days * num_travelers
            remaining_for_hotel = max_budget - flight_cost - daily_cost
            max_hotel_price = remaining_for_hotel // nights if nights > 0 else remaining_for_hotel
            
            if max_hotel_price < 1000:
                # Can't afford any reasonable hotel
                return {
                    "success": False,
                    "error": f"Budget too low",
                    "budget_analysis": {
                        "your_budget": max_budget,
                        "flight_cost": flight_cost,
                        "min_daily_expenses": daily_cost,
                        "remaining_for_hotel": remaining_for_hotel,
                        "nights": nights,
                        "per_night_available": max_hotel_price
                    },
                    "suggestion": f"Minimum budget needed: ₹{flight_cost + (1500 * nights) + daily_cost:,}. Consider fewer days or different route.",
                    "reasoning": reasoning + [f"❌ After flights (₹{flight_cost:,}) and expenses (₹{daily_cost:,}), only ₹{remaining_for_hotel:,} left for {nights} nights = ₹{max_hotel_price:,}/night (too low)"]
                }
            
            reasoning.append(f"💰 Budget: ₹{max_budget:,}. After flights & expenses, ₹{max_hotel_price:,}/night for hotel.")
        else:
            max_hotel_price = None
        
        # Step 3: Find hotel within budget
        reasoning.append("🔍 Searching for hotels...")
        
        # Try to find cheapest hotel that fits budget
        hotel_sort = "price" if (budget_preference == "budget" or max_budget) else "value"
        hotel_stars = 1 if budget_preference == "budget" else min_hotel_stars
        
        hotel_result = search_hotels(
            destination,
            min_stars=hotel_stars,
            max_price=max_hotel_price,
            sort_by=hotel_sort
        )
        
        # If no hotels found, try without star restriction
        if not hotel_result["success"] and hotel_stars > 1:
            hotel_result = search_hotels(destination, min_stars=1, max_price=max_hotel_price, sort_by="price")
        
        if not hotel_result["success"]:
            return {
                "success": False,
                "error": f"No hotels in {destination} within ₹{max_hotel_price:,}/night",
                "suggestion": "Increase budget or reduce trip duration",
                "reasoning": reasoning
            }
        
        selected_hotel = hotel_result["recommended"]
        hotel_cost = selected_hotel["price_per_night"] * nights
        reasoning.append(f"🏨 Found: {selected_hotel['name']} ({selected_hotel['stars']}⭐) at ₹{selected_hotel['price_per_night']:,}/night")
        
        # Step 4: Calculate actual budget
        daily_expense = 1500 if budget_preference == "budget" else DEFAULT_DAILY_EXPENSES
        total_daily = daily_expense * num_days * num_travelers
        total_cost = flight_cost + hotel_cost + total_daily
        
        # Verify within budget
        if max_budget and total_cost > max_budget:
            # Try to reduce daily expenses
            reduced_daily = 1000  # Minimum
            total_daily = reduced_daily * num_days * num_travelers
            total_cost = flight_cost + hotel_cost + total_daily
            daily_expense = reduced_daily
            
            if total_cost > max_budget:
                return {
                    "success": False,
                    "error": f"Cannot plan trip within ₹{max_budget:,}",
                    "closest_option": {
                        "cost": total_cost,
                        "flight": flight_cost,
                        "hotel": hotel_cost,
                        "expenses": total_daily
                    },
                    "suggestion": f"Minimum possible: ₹{total_cost:,}. Need ₹{total_cost - max_budget:,} more, or try fewer days.",
                    "reasoning": reasoning
                }
            
            reasoning.append(f"💡 Reduced daily expenses to ₹{reduced_daily:,} to fit budget")
        
        reasoning.append(f"✅ Total: ₹{total_cost:,} {'(within budget!)' if max_budget and total_cost <= max_budget else ''}")
        
        # Step 5: Get places
        reasoning.append("🔍 Finding attractions...")
        places_result = search_places(destination, min_rating=3.5, max_results=num_days * 2)
        
        # Step 6: Get weather
        reasoning.append("🌤️ Checking weather...")
        weather_result = get_weather(destination, start_date, num_days)
        
        # Build itinerary
        itinerary = self._build_itinerary(
            destination, num_days,
            places_result.get("places", []),
            weather_result.get("forecast", []),
            start_date
        )
        
        # Determine trip category
        per_person = total_cost / num_travelers
        if per_person < 8000:
            category = {"name": "Budget", "emoji": "💚", "description": "💚 Budget Trip"}
        elif per_person < 15000:
            category = {"name": "Mid-Range", "emoji": "💛", "description": "💛 Mid-Range Trip"}
        else:
            category = {"name": "Premium", "emoji": "💎", "description": "💎 Premium Trip"}
        
        return {
            "success": True,
            "trip_summary": {
                "title": f"Your {num_days}-Day Trip to {destination}",
                "dates": f"{start_date} ({num_days} days)",
                "travelers": num_travelers,
                "from": source,
                "to": destination
            },
            "flight": {
                "airline": selected_flight["airline"],
                "flight_id": selected_flight["flight_id"],
                "departure": selected_flight["departure_time"],
                "arrival": selected_flight["arrival_time"],
                "duration": f"{selected_flight['duration_hours']}h",
                "price": selected_flight["price"],
                "price_formatted": f"₹{selected_flight['price']:,}",
                "round_trip_cost": flight_cost,
                "reason": "Cheapest available flight"
            },
            "hotel": {
                "name": selected_hotel["name"],
                "stars": selected_hotel.get("stars", 3),
                "price_per_night": selected_hotel.get("price_per_night", 3000),
                "price_formatted": f"₹{selected_hotel['price_per_night']:,}/night",
                "amenities": selected_hotel.get("amenities", []),
                "total_cost": hotel_cost,
                "reason": "Best value within budget" if max_budget else "Best value"
            },
            "weather": {
                "forecast": weather_result.get("forecast", []),
                "summary": weather_result.get("summary", ""),
                "recommendations": weather_result.get("recommendations", [])
            },
            "places": places_result.get("places", []),
            "itinerary": itinerary,
            "budget": {
                "breakdown": {
                    "flights": {"total": flight_cost, "formatted": f"₹{flight_cost:,}", "description": f"Round-trip × {num_travelers}"},
                    "accommodation": {"total": hotel_cost, "formatted": f"₹{hotel_cost:,}", "description": f"{nights} nights"},
                    "daily_expenses": {"total": total_daily, "formatted": f"₹{total_daily:,}", "description": f"₹{daily_expense:,}/day × {num_days} days"}
                },
                "total": total_cost,
                "total_formatted": f"₹{total_cost:,}",
                "per_person": round(per_person),
                "per_person_formatted": f"₹{round(per_person):,}/person",
                "category": category,
                "within_budget": max_budget is None or total_cost <= max_budget,
                "max_budget": max_budget,
                "savings": max_budget - total_cost if max_budget and total_cost <= max_budget else 0
            },
            "reasoning": reasoning
        }
    
    def _build_itinerary(self, destination: str, num_days: int, places: list, weather: list, start_date: str) -> list:
        from datetime import datetime, timedelta
        
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        except:
            start = datetime.now()
        
        itinerary = []
        places_per_day = max(1, len(places) // num_days) if places else 0
        
        for day in range(num_days):
            date = start + timedelta(days=day)
            start_idx = day * places_per_day
            end_idx = start_idx + places_per_day
            day_places = places[start_idx:end_idx] if places else []
            day_weather = weather[day] if day < len(weather) else None
            
            activities = []
            if day == 0:
                activities.append(f"🛬 Arrive in {destination}")
            
            for p in day_places:
                activities.append(f"{p.get('type_emoji', '📍')} {p['name']}")
            
            if not day_places:
                activities.append(f"🚶 Explore {destination}")
            
            activities.append("🍽️ Local food")
            
            if day == num_days - 1:
                activities.append("🛫 Departure")
            
            itinerary.append({
                "day": day + 1,
                "date": date.strftime("%Y-%m-%d"),
                "date_display": date.strftime("%a, %b %d"),
                "places": day_places,
                "weather": day_weather,
                "weather_display": f"{day_weather['emoji']} {day_weather['condition']} ({day_weather['temperature_max']}°C)" if day_weather else "—",
                "activities": activities
            })
        
        return itinerary


def create_travel_agent(api_key: Optional[str] = None) -> TravelAgent:
    return TravelAgent(api_key=api_key)
