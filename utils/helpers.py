"""
Helper functions for AI Travel Agent
"""

from datetime import datetime, timedelta
from typing import Tuple, Optional


def format_currency(amount: int, currency: str = "INR") -> str:
    """Format amount as currency string."""
    if currency == "INR":
        return f"₹{amount:,}"
    return f"{amount:,} {currency}"


def format_date(date_str: str, output_format: str = "%b %d, %Y") -> str:
    """Format date string to human-readable format."""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.strftime(output_format)
    except ValueError:
        return date_str


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime object."""
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def validate_date_range(start_date: str, num_days: int) -> Tuple[bool, str]:
    """
    Validate that date range is acceptable.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    start = parse_date(start_date)
    if not start:
        return False, "Invalid date format. Use YYYY-MM-DD"
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Check if date is not too far in past
    if start < today - timedelta(days=1):
        return False, "Start date cannot be in the past"
    
    # Check if date is not too far in future (weather API limit)
    if start > today + timedelta(days=365):
        return False, "Start date cannot be more than 1 year in advance"
    
    # Check number of days
    if num_days < 1:
        return False, "Trip must be at least 1 day"
    
    if num_days > 14:
        return False, "Trip cannot exceed 14 days"
    
    return True, ""


def get_city_emoji(city: str) -> str:
    """Get emoji representing a city."""
    city_emojis = {
        "delhi": "🏛️",
        "mumbai": "🌆",
        "goa": "🏖️",
        "bangalore": "💻",
        "chennai": "🛕",
        "hyderabad": "🍗",
        "kolkata": "🎭",
        "jaipur": "🏰"
    }
    return city_emojis.get(city.lower(), "🌍")


def calculate_trip_stats(trip_plan: dict) -> dict:
    """Calculate additional statistics for a trip plan."""
    if not trip_plan.get("success"):
        return {}
    
    budget = trip_plan.get("budget", {})
    itinerary = trip_plan.get("itinerary", [])
    places = trip_plan.get("places", [])
    
    # Count activities
    total_activities = sum(len(day.get("activities", [])) for day in itinerary)
    
    # Count place types
    place_types = {}
    for place in places:
        ptype = place.get("type", "other")
        place_types[ptype] = place_types.get(ptype, 0) + 1
    
    # Average rating of places
    ratings = [p.get("rating", 0) for p in places if p.get("rating")]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    return {
        "total_activities": total_activities,
        "place_types": place_types,
        "avg_place_rating": round(avg_rating, 1),
        "num_places": len(places),
        "cost_per_day": budget.get("total", 0) / len(itinerary) if itinerary else 0
    }


def format_itinerary_for_export(trip_plan: dict) -> str:
    """Format trip plan for text export."""
    if not trip_plan.get("success"):
        return "Trip planning failed"
    
    lines = []
    summary = trip_plan["trip_summary"]
    
    lines.append("=" * 50)
    lines.append(summary["title"].upper())
    lines.append("=" * 50)
    lines.append(f"From: {summary['from']} → To: {summary['to']}")
    lines.append(f"Dates: {summary['dates']}")
    lines.append(f"Travelers: {summary['travelers']}")
    lines.append("")
    
    # Flight
    flight = trip_plan["flight"]
    lines.append("FLIGHT DETAILS")
    lines.append("-" * 30)
    lines.append(f"Airline: {flight['airline']}")
    lines.append(f"Departure: {flight['departure']}")
    lines.append(f"Price: {flight['price_formatted']}")
    lines.append("")
    
    # Hotel
    hotel = trip_plan["hotel"]
    lines.append("HOTEL DETAILS")
    lines.append("-" * 30)
    lines.append(f"Name: {hotel['name']}")
    lines.append(f"Rating: {'⭐' * hotel['stars']}")
    lines.append(f"Price: {hotel['price_formatted']}")
    lines.append(f"Amenities: {', '.join(hotel['amenities'])}")
    lines.append("")
    
    # Itinerary
    lines.append("DAILY ITINERARY")
    lines.append("-" * 30)
    for day in trip_plan["itinerary"]:
        lines.append(f"\nDay {day['day']} - {day['date_display']}")
        lines.append(f"Weather: {day['weather_display']}")
        for activity in day["activities"]:
            lines.append(f"  • {activity}")
    lines.append("")
    
    # Budget
    budget = trip_plan["budget"]
    lines.append("BUDGET BREAKDOWN")
    lines.append("-" * 30)
    lines.append(f"Total: {budget['total_formatted']}")
    lines.append(f"Per Person: {budget['per_person_formatted']}")
    lines.append("")
    
    return "\n".join(lines)
