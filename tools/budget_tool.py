"""
Budget Estimation Tool for AI Travel Agent
Calculates total trip cost including flights, hotels, and daily expenses
"""

import json
from typing import Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import DEFAULT_DAILY_EXPENSES


class BudgetEstimationInput(BaseModel):
    """Input schema for budget estimation"""
    flight_price: int = Field(description="Price of selected flight in INR")
    hotel_price_per_night: int = Field(description="Hotel price per night in INR")
    num_nights: int = Field(description="Number of nights staying")
    num_travelers: int = Field(default=1, description="Number of travelers")
    daily_expenses: int = Field(
        default=DEFAULT_DAILY_EXPENSES,
        description="Estimated daily expenses per person (food, transport, activities) in INR"
    )
    include_return_flight: bool = Field(
        default=True,
        description="Whether to include return flight cost (doubles flight price)"
    )


def estimate_budget(
    flight_price: int,
    hotel_price_per_night: int,
    num_nights: int,
    num_travelers: int = 1,
    daily_expenses: int = DEFAULT_DAILY_EXPENSES,
    include_return_flight: bool = True
) -> dict:
    """
    Calculate total trip budget with itemized breakdown.
    
    Args:
        flight_price: One-way flight price
        hotel_price_per_night: Hotel cost per night
        num_nights: Number of nights
        num_travelers: Number of people
        daily_expenses: Daily per-person expenses
        include_return_flight: Include return journey
        
    Returns:
        Dictionary with detailed budget breakdown
    """
    # Calculate flight costs
    flight_multiplier = 2 if include_return_flight else 1
    total_flight_cost = flight_price * flight_multiplier * num_travelers
    
    # Calculate hotel costs
    total_hotel_cost = hotel_price_per_night * num_nights
    
    # Calculate daily expenses (food, transport, activities)
    num_days = num_nights + 1  # Usually one more day than nights
    total_daily_expenses = daily_expenses * num_days * num_travelers
    
    # Calculate totals
    grand_total = total_flight_cost + total_hotel_cost + total_daily_expenses
    per_person_total = grand_total / num_travelers if num_travelers > 0 else grand_total
    
    # Build breakdown
    breakdown = {
        "flights": {
            "description": f"{'Round-trip' if include_return_flight else 'One-way'} flight × {num_travelers} traveler(s)",
            "unit_price": flight_price,
            "quantity": flight_multiplier * num_travelers,
            "total": total_flight_cost,
            "formatted": f"₹{total_flight_cost:,}"
        },
        "accommodation": {
            "description": f"Hotel for {num_nights} night(s)",
            "unit_price": hotel_price_per_night,
            "quantity": num_nights,
            "total": total_hotel_cost,
            "formatted": f"₹{total_hotel_cost:,}"
        },
        "daily_expenses": {
            "description": f"Food, transport & activities ({num_days} days × {num_travelers} person(s))",
            "unit_price": daily_expenses,
            "quantity": num_days * num_travelers,
            "total": total_daily_expenses,
            "formatted": f"₹{total_daily_expenses:,}"
        }
    }
    
    # Budget tips
    tips = []
    if grand_total > 30000:
        tips.append("💡 Consider budget hotels or shorter stay to reduce costs")
    if num_travelers > 2:
        tips.append("💡 Group discounts may be available for activities")
    if total_daily_expenses > total_hotel_cost:
        tips.append("💡 Pre-book activities online for better rates")
    
    # Budget category
    if per_person_total < 10000:
        category = "Budget"
        category_emoji = "💚"
    elif per_person_total < 20000:
        category = "Mid-Range"
        category_emoji = "💛"
    else:
        category = "Premium"
        category_emoji = "💎"
    
    return {
        "success": True,
        "breakdown": breakdown,
        "summary": {
            "total_flight_cost": total_flight_cost,
            "total_hotel_cost": total_hotel_cost,
            "total_daily_expenses": total_daily_expenses,
            "grand_total": grand_total,
            "per_person_total": round(per_person_total),
            "formatted_total": f"₹{grand_total:,}",
            "formatted_per_person": f"₹{round(per_person_total):,}/person"
        },
        "trip_info": {
            "num_travelers": num_travelers,
            "num_nights": num_nights,
            "num_days": num_days,
            "include_return_flight": include_return_flight
        },
        "category": {
            "name": category,
            "emoji": category_emoji,
            "description": f"{category_emoji} {category} Trip"
        },
        "tips": tips,
        "reasoning": f"Total budget of ₹{grand_total:,} for {num_travelers} traveler(s) over {num_days} days. This is a {category.lower()} trip at ₹{round(per_person_total):,} per person."
    }


@tool(args_schema=BudgetEstimationInput)
def BudgetEstimationTool(
    flight_price: int,
    hotel_price_per_night: int,
    num_nights: int,
    num_travelers: int = 1,
    daily_expenses: int = DEFAULT_DAILY_EXPENSES,
    include_return_flight: bool = True
) -> str:
    """
    Calculate total trip budget with detailed breakdown.
    Use this tool to estimate the complete cost of a trip including flights, hotels, and daily expenses.
    """
    result = estimate_budget(
        flight_price, hotel_price_per_night, num_nights,
        num_travelers, daily_expenses, include_return_flight
    )
    return json.dumps(result, indent=2)
