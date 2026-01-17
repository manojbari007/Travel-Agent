"""
Flight Search Tool for AI Travel Agent
Searches flights.json dataset with filtering and ranking capabilities
"""

import json
import os
from typing import Optional, Literal
from datetime import datetime
from langchain_core.tools import tool
from pydantic import BaseModel, Field


# Get the data file path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data")
FLIGHTS_FILE = os.path.join(DATA_DIR, "flights.json")


def load_flights():
    """Load flights data from JSON file"""
    with open(FLIGHTS_FILE, "r") as f:
        return json.load(f)


class FlightSearchInput(BaseModel):
    """Input schema for flight search"""
    source: str = Field(description="Departure city (e.g., 'Delhi', 'Mumbai')")
    destination: str = Field(description="Arrival city (e.g., 'Goa', 'Bangalore')")
    sort_by: Literal["cheapest", "fastest"] = Field(
        default="cheapest",
        description="Sort flights by 'cheapest' price or 'fastest' duration"
    )
    max_results: int = Field(default=3, description="Maximum number of results to return")


def search_flights(
    source: str,
    destination: str,
    sort_by: str = "cheapest",
    max_results: int = 3
) -> dict:
    """
    Search for flights between two cities.
    
    Args:
        source: Departure city
        destination: Arrival city  
        sort_by: Sort by 'cheapest' or 'fastest'
        max_results: Maximum results to return
        
    Returns:
        Dictionary with flight options and reasoning
    """
    flights = load_flights()
    
    # Filter by source and destination (case-insensitive)
    matching_flights = [
        f for f in flights
        if f["from"].lower() == source.lower() 
        and f["to"].lower() == destination.lower()
    ]
    
    if not matching_flights:
        return {
            "success": False,
            "message": f"No flights found from {source} to {destination}",
            "flights": [],
            "reasoning": f"The dataset doesn't contain direct flights from {source} to {destination}."
        }
    
    # Calculate duration for each flight
    for flight in matching_flights:
        dep = datetime.fromisoformat(flight["departure_time"])
        arr = datetime.fromisoformat(flight["arrival_time"])
        duration_hours = (arr - dep).total_seconds() / 3600
        flight["duration_hours"] = round(duration_hours, 1)
    
    # Sort based on preference
    if sort_by == "cheapest":
        matching_flights.sort(key=lambda x: x["price"])
        reasoning = "Sorted by lowest price to maximize savings."
    else:
        matching_flights.sort(key=lambda x: x["duration_hours"])
        reasoning = "Sorted by shortest duration to save travel time."
    
    # Get top results
    top_flights = matching_flights[:max_results]
    
    # Format results
    formatted_flights = []
    for i, f in enumerate(top_flights):
        formatted_flights.append({
            "rank": i + 1,
            "flight_id": f["flight_id"],
            "airline": f["airline"],
            "from": f["from"],
            "to": f["to"],
            "departure_time": f["departure_time"],
            "arrival_time": f["arrival_time"],
            "duration_hours": f["duration_hours"],
            "price": f["price"],
            "price_formatted": f"₹{f['price']:,}"
        })
    
    # Generate selection reasoning
    if top_flights:
        best = top_flights[0]
        selection_reason = (
            f"Selected {best['airline']} at ₹{best['price']:,} "
            f"({best['duration_hours']}h flight) as the {'cheapest' if sort_by == 'cheapest' else 'fastest'} option."
        )
    else:
        selection_reason = "No flights available for selection."
    
    return {
        "success": True,
        "message": f"Found {len(matching_flights)} flights from {source} to {destination}",
        "total_found": len(matching_flights),
        "flights": formatted_flights,
        "reasoning": reasoning,
        "selection_reason": selection_reason,
        "recommended": formatted_flights[0] if formatted_flights else None
    }


@tool(args_schema=FlightSearchInput)
def FlightSearchTool(
    source: str,
    destination: str,
    sort_by: str = "cheapest",
    max_results: int = 3
) -> str:
    """
    Search for flights between two cities. Returns available flights sorted by price or duration.
    Use this tool when you need to find flight options for travel planning.
    """
    result = search_flights(source, destination, sort_by, max_results)
    return json.dumps(result, indent=2)
