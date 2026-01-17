"""
Hotel Recommendation Tool for AI Travel Agent
Searches hotels.json dataset with filtering and ranking capabilities
"""

import json
import os
from typing import Optional, List, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field


# Get the data file path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data")
HOTELS_FILE = os.path.join(DATA_DIR, "hotels.json")


def load_hotels():
    """Load hotels data from JSON file"""
    with open(HOTELS_FILE, "r") as f:
        return json.load(f)


class HotelSearchInput(BaseModel):
    """Input schema for hotel search"""
    city: str = Field(description="City to search hotels in (e.g., 'Goa', 'Delhi')")
    min_stars: int = Field(default=1, description="Minimum star rating (1-5)")
    max_price: Optional[int] = Field(default=None, description="Maximum price per night in INR")
    required_amenities: Optional[List[str]] = Field(
        default=None,
        description="Required amenities (e.g., ['wifi', 'pool', 'breakfast'])"
    )
    sort_by: Literal["price", "stars", "value"] = Field(
        default="value",
        description="Sort by 'price' (low to high), 'stars' (high to low), or 'value' (best stars per price)"
    )
    max_results: int = Field(default=3, description="Maximum number of results to return")


def search_hotels(
    city: str,
    min_stars: int = 1,
    max_price: Optional[int] = None,
    required_amenities: Optional[List[str]] = None,
    sort_by: str = "value",
    max_results: int = 3
) -> dict:
    """
    Search for hotels in a city with various filters.
    
    Args:
        city: City to search in
        min_stars: Minimum star rating
        max_price: Maximum price per night
        required_amenities: List of required amenities
        sort_by: Sort method ('price', 'stars', 'value')
        max_results: Maximum results to return
        
    Returns:
        Dictionary with hotel options and reasoning
    """
    hotels = load_hotels()
    
    # Filter by city (case-insensitive)
    matching_hotels = [
        h for h in hotels
        if h["city"].lower() == city.lower()
    ]
    
    if not matching_hotels:
        return {
            "success": False,
            "message": f"No hotels found in {city}",
            "hotels": [],
            "reasoning": f"The dataset doesn't contain hotels in {city}."
        }
    
    # Filter by minimum stars
    matching_hotels = [h for h in matching_hotels if h["stars"] >= min_stars]
    
    # Filter by max price
    if max_price:
        matching_hotels = [h for h in matching_hotels if h["price_per_night"] <= max_price]
    
    # Filter by required amenities
    if required_amenities:
        required_set = set(a.lower() for a in required_amenities)
        matching_hotels = [
            h for h in matching_hotels
            if required_set.issubset(set(a.lower() for a in h["amenities"]))
        ]
    
    if not matching_hotels:
        return {
            "success": False,
            "message": f"No hotels in {city} match your criteria",
            "hotels": [],
            "reasoning": "Try relaxing filters (lower stars, higher budget, fewer amenities)."
        }
    
    # Calculate value score (stars per 1000 INR)
    for hotel in matching_hotels:
        hotel["value_score"] = round(hotel["stars"] / (hotel["price_per_night"] / 1000), 2)
    
    # Sort based on preference
    if sort_by == "price":
        matching_hotels.sort(key=lambda x: x["price_per_night"])
        reasoning = "Sorted by lowest price to stay within budget."
    elif sort_by == "stars":
        matching_hotels.sort(key=lambda x: x["stars"], reverse=True)
        reasoning = "Sorted by highest star rating for best quality."
    else:  # value
        matching_hotels.sort(key=lambda x: x["value_score"], reverse=True)
        reasoning = "Sorted by best value (star rating relative to price)."
    
    # Get top results
    top_hotels = matching_hotels[:max_results]
    
    # Format results
    formatted_hotels = []
    for i, h in enumerate(top_hotels):
        formatted_hotels.append({
            "rank": i + 1,
            "hotel_id": h["hotel_id"],
            "name": h["name"],
            "city": h["city"],
            "stars": h["stars"],
            "stars_display": "⭐" * h["stars"],
            "price_per_night": h["price_per_night"],
            "price_formatted": f"₹{h['price_per_night']:,}/night",
            "amenities": h["amenities"],
            "value_score": h["value_score"]
        })
    
    # Generate selection reasoning
    if top_hotels:
        best = top_hotels[0]
        selection_reason = (
            f"Selected {best['name']} ({best['stars']}-star) at ₹{best['price_per_night']:,}/night. "
            f"Amenities: {', '.join(best['amenities'])}. "
            f"Value score: {best['value_score']} (higher is better)."
        )
    else:
        selection_reason = "No hotels available for selection."
    
    return {
        "success": True,
        "message": f"Found {len(matching_hotels)} hotels in {city}",
        "total_found": len(matching_hotels),
        "hotels": formatted_hotels,
        "reasoning": reasoning,
        "selection_reason": selection_reason,
        "recommended": formatted_hotels[0] if formatted_hotels else None
    }


@tool(args_schema=HotelSearchInput)
def HotelRecommendationTool(
    city: str,
    min_stars: int = 1,
    max_price: Optional[int] = None,
    required_amenities: Optional[List[str]] = None,
    sort_by: str = "value",
    max_results: int = 3
) -> str:
    """
    Search for hotels in a city with filters for stars, price, and amenities.
    Use this tool when you need to find accommodation options for travel planning.
    """
    result = search_hotels(city, min_stars, max_price, required_amenities, sort_by, max_results)
    return json.dumps(result, indent=2)
