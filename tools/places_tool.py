"""
Places Discovery Tool for AI Travel Agent
Searches places.json dataset for attractions and points of interest
"""

import json
import os
from typing import Optional, List
from langchain_core.tools import tool
from pydantic import BaseModel, Field


# Get the data file path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data")
PLACES_FILE = os.path.join(DATA_DIR, "places.json")


def load_places():
    """Load places data from JSON file"""
    with open(PLACES_FILE, "r") as f:
        return json.load(f)


class PlacesSearchInput(BaseModel):
    """Input schema for places search"""
    city: str = Field(description="City to search places in (e.g., 'Goa', 'Jaipur')")
    place_types: Optional[List[str]] = Field(
        default=None,
        description="Types of places to find (e.g., ['beach', 'temple', 'museum']). Available types: beach, temple, fort, museum, park, market, lake, monument"
    )
    min_rating: float = Field(default=0.0, description="Minimum rating (0.0 to 5.0)")
    max_results: int = Field(default=10, description="Maximum number of results to return")


def search_places(
    city: str,
    place_types: Optional[List[str]] = None,
    min_rating: float = 0.0,
    max_results: int = 10
) -> dict:
    """
    Search for places/attractions in a city.
    
    Args:
        city: City to search in
        place_types: List of place types to filter by
        min_rating: Minimum rating threshold
        max_results: Maximum results to return
        
    Returns:
        Dictionary with places and reasoning for day planning
    """
    places = load_places()
    
    # Filter by city (case-insensitive)
    matching_places = [
        p for p in places
        if p["city"].lower() == city.lower()
    ]
    
    if not matching_places:
        return {
            "success": False,
            "message": f"No places found in {city}",
            "places": [],
            "reasoning": f"The dataset doesn't contain attractions in {city}."
        }
    
    # Filter by place types
    if place_types:
        type_set = set(t.lower() for t in place_types)
        matching_places = [
            p for p in matching_places
            if p["type"].lower() in type_set
        ]
    
    # Filter by minimum rating
    matching_places = [p for p in matching_places if p["rating"] >= min_rating]
    
    if not matching_places:
        return {
            "success": False,
            "message": f"No places in {city} match your criteria",
            "places": [],
            "reasoning": "Try lowering the rating threshold or including more place types."
        }
    
    # Sort by rating (highest first)
    matching_places.sort(key=lambda x: x["rating"], reverse=True)
    
    # Get top results
    top_places = matching_places[:max_results]
    
    # Format results
    formatted_places = []
    for i, p in enumerate(top_places):
        formatted_places.append({
            "rank": i + 1,
            "place_id": p["place_id"],
            "name": p["name"],
            "city": p["city"],
            "type": p["type"],
            "type_emoji": get_type_emoji(p["type"]),
            "rating": p["rating"],
            "rating_display": f"{'⭐' * int(p['rating'])} ({p['rating']})"
        })
    
    # Group places for day-wise planning (2-3 places per day)
    places_per_day = 3
    day_wise_plan = []
    for i in range(0, len(formatted_places), places_per_day):
        day_num = (i // places_per_day) + 1
        day_places = formatted_places[i:i + places_per_day]
        day_wise_plan.append({
            "day": day_num,
            "places": day_places,
            "place_names": [p["name"] for p in day_places]
        })
    
    # Get unique types found
    types_found = list(set(p["type"] for p in top_places))
    
    return {
        "success": True,
        "message": f"Found {len(matching_places)} places in {city}",
        "total_found": len(matching_places),
        "places": formatted_places,
        "day_wise_plan": day_wise_plan,
        "types_available": types_found,
        "reasoning": f"Found {len(types_found)} types of attractions: {', '.join(types_found)}. Sorted by rating for best experiences.",
        "recommended_days": len(day_wise_plan)
    }


def get_type_emoji(place_type: str) -> str:
    """Get emoji for place type"""
    emoji_map = {
        "beach": "🏖️",
        "temple": "🛕",
        "fort": "🏰",
        "museum": "🏛️",
        "park": "🌳",
        "market": "🛒",
        "lake": "🌊",
        "monument": "🗿"
    }
    return emoji_map.get(place_type.lower(), "📍")


@tool(args_schema=PlacesSearchInput)
def PlacesDiscoveryTool(
    city: str,
    place_types: Optional[List[str]] = None,
    min_rating: float = 0.0,
    max_results: int = 10
) -> str:
    """
    Discover places and attractions in a city. Returns places sorted by rating with day-wise grouping.
    Use this tool when you need to find tourist attractions for itinerary planning.
    """
    result = search_places(city, place_types, min_rating, max_results)
    return json.dumps(result, indent=2)
