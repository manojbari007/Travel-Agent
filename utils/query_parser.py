"""
Query Parser for AI Travel Agent
Parses natural language travel queries with fuzzy matching and proper memory
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import AVAILABLE_CITIES


def fuzzy_match_city(input_str: str) -> Optional[str]:
    """
    Fuzzy match city name to handle misspellings.
    Uses simple edit distance and common misspellings.
    """
    input_lower = input_str.lower().strip()
    
    # Direct match
    for city in AVAILABLE_CITIES:
        if city.lower() == input_lower:
            return city
    
    # Common misspellings and variations
    city_aliases = {
        'hyderabad': ['hyderbad', 'hydrabad', 'hyd', 'hybd', 'hyderbad'],
        'bangalore': ['bengaluru', 'banglore', 'blr', 'blore', 'bangaluru'],
        'mumbai': ['bombay', 'mum', 'mumbay'],
        'delhi': ['new delhi', 'newdelhi', 'del', 'dilli'],
        'kolkata': ['calcutta', 'kolkatta', 'kolkta', 'kol'],
        'chennai': ['madras', 'chenai', 'chennay'],
        'goa': ['gova', 'panaji'],
        'jaipur': ['jpir', 'jaypur', 'jaipr']
    }
    
    for city, aliases in city_aliases.items():
        if input_lower in aliases or input_lower == city:
            return city.title()
    
    # Substring match
    for city in AVAILABLE_CITIES:
        if input_lower in city.lower() or city.lower() in input_lower:
            return city
    
    # Levenshtein-like matching for small errors
    for city in AVAILABLE_CITIES:
        if _similar(input_lower, city.lower()):
            return city
    
    return None


def _similar(a: str, b: str, threshold: float = 0.7) -> bool:
    """Check if two strings are similar (simple similarity check)."""
    if len(a) < 3 or len(b) < 3:
        return False
    
    # Count matching characters
    matches = sum(1 for c in a if c in b)
    ratio = matches / max(len(a), len(b))
    return ratio >= threshold


class QueryParser:
    """
    Parses natural language travel queries with memory support.
    """
    
    def __init__(self):
        self.cities = [c.lower() for c in AVAILABLE_CITIES]
        self.city_map = {c.lower(): c for c in AVAILABLE_CITIES}
        
        self.number_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'a': 1, 'an': 1
        }
        
        self.budget_keywords = {
            'cheap': 'budget', 'budget': 'budget', 'affordable': 'budget', 
            'low cost': 'budget', 'economy': 'budget', 'economical': 'budget',
            'under': 'budget',  # "under 20k" implies budget conscious
            'balanced': 'balanced', 'moderate': 'balanced', 'mid-range': 'balanced',
            'luxury': 'premium', 'premium': 'premium', 'expensive': 'premium',
            'high-end': 'premium', '5 star': 'premium', 'five star': 'premium'
        }
        
        # Memory for conversation context
        self.memory = {}
    
    def parse_query(self, query: str, existing_context: Dict = None) -> Dict[str, Any]:
        """Parse query with context from previous messages."""
        query_lower = query.lower().strip()
        
        # Start with existing context or fresh
        result = {
            'source': None,
            'destination': None,
            'num_days': None,
            'start_date': None,
            'num_travelers': 1,
            'budget_preference': 'balanced',
            'min_hotel_stars': 3,
            'max_budget': None,
            'preferred_activities': None,
            'missing_fields': [],
            'parsed_successfully': False,
            'friendly_message': None
        }
        
        # Merge with existing context
        if existing_context:
            for key in ['source', 'destination', 'num_days', 'start_date', 
                        'num_travelers', 'budget_preference', 'min_hotel_stars', 
                        'max_budget', 'preferred_activities']:
                if existing_context.get(key):
                    result[key] = existing_context[key]
        
        # Extract new information from current query
        new_source, new_dest = self._extract_cities(query_lower)
        if new_source:
            result['source'] = new_source
        if new_dest:
            result['destination'] = new_dest
        
        new_days = self._extract_days(query_lower)
        if new_days:
            result['num_days'] = new_days
        
        new_date = self._extract_date(query_lower)
        if new_date:
            result['start_date'] = new_date
        elif not result['start_date']:
            result['start_date'] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        new_travelers = self._extract_travelers(query_lower)
        if new_travelers:
            result['num_travelers'] = new_travelers
        
        # Extract budget constraint
        new_budget = self._extract_budget_amount(query_lower)
        if new_budget:
            result['max_budget'] = new_budget
            result['budget_preference'] = 'budget'  # If they specify max budget, they're budget conscious
        
        budget_pref = self._extract_budget_preference(query_lower)
        if budget_pref != 'balanced':
            result['budget_preference'] = budget_pref
        
        stars = self._extract_hotel_stars(query_lower)
        if stars != 3:
            result['min_hotel_stars'] = stars
        
        # Determine missing fields
        missing = []
        if not result['source']:
            missing.append('source city')
        if not result['destination']:
            missing.append('destination city')
        if not result['num_days']:
            missing.append('number of days')
        
        result['missing_fields'] = missing
        result['parsed_successfully'] = len(missing) == 0
        
        # Generate response
        if missing:
            result['friendly_message'] = self._generate_missing_info_message(missing, result)
        else:
            result['friendly_message'] = self._generate_confirmation_message(result)
        
        return result
    
    def _extract_cities(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract source and destination with fuzzy matching."""
        source = None
        destination = None
        
        # Pattern: "from X to Y"
        from_to_match = re.search(r'from\s+(\w+)\s+to\s+(\w+)', query)
        if from_to_match:
            source = fuzzy_match_city(from_to_match.group(1))
            destination = fuzzy_match_city(from_to_match.group(2))
            return source, destination
        
        # Pattern: "X to Y" (without 'from')
        to_match = re.search(r'(\w+)\s+to\s+(\w+)', query)
        if to_match:
            src = fuzzy_match_city(to_match.group(1))
            dst = fuzzy_match_city(to_match.group(2))
            if src and dst:
                return src, dst
            elif dst:
                destination = dst
        
        # Pattern: "to X" only
        to_only = re.search(r'\bto\s+(\w+)', query)
        if to_only and not destination:
            destination = fuzzy_match_city(to_only.group(1))
        
        # Pattern: "from X" only (follow-up message)
        from_only = re.search(r'from\s+(\w+)', query)
        if from_only and not source:
            source = fuzzy_match_city(from_only.group(1))
        
        # Pattern: "visiting X" / "trip to X"
        visit_match = re.search(r'(?:visiting|visit|trip to|travel to|going to)\s+(\w+)', query)
        if visit_match and not destination:
            destination = fuzzy_match_city(visit_match.group(1))
        
        # Try to find any city mentioned (for follow-up like "from hyderabad")
        if not source and not destination:
            words = query.split()
            for word in words:
                matched = fuzzy_match_city(word)
                if matched:
                    # If context has destination but no source, this is source
                    source = matched
                    break
        
        return source, destination
    
    def _extract_days(self, query: str) -> Optional[int]:
        """Extract number of days."""
        # Pattern: "X days" or "X day"
        match = re.search(r'(\d+)\s*(?:days?|nights?)', query)
        if match:
            return min(max(int(match.group(1)), 1), 14)
        
        # Word numbers
        for word, num in self.number_words.items():
            if re.search(rf'\b{word}\s*(?:days?|nights?)', query):
                return num
        
        # "a week"
        if 'week' in query and 'weekend' not in query:
            return 7
        if 'weekend' in query:
            return 2
        
        return None
    
    def _extract_date(self, query: str) -> Optional[str]:
        """Extract start date."""
        today = datetime.now()
        
        if 'tomorrow' in query:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        if 'next week' in query:
            return (today + timedelta(days=7)).strftime("%Y-%m-%d")
        if 'next month' in query:
            return (today + timedelta(days=30)).strftime("%Y-%m-%d")
        
        return None
    
    def _extract_travelers(self, query: str) -> Optional[int]:
        """Extract number of travelers."""
        match = re.search(r'(\d+)\s*(?:people|persons?|travelers?|adults?)', query)
        if match:
            return min(max(int(match.group(1)), 1), 10)
        
        if 'couple' in query:
            return 2
        if 'family' in query:
            return 4
        if 'solo' in query:
            return 1
        
        return None
    
    def _extract_budget_amount(self, query: str) -> Optional[int]:
        """Extract budget amount like '20k' or '20000'."""
        # Pattern: "under 20k" or "budget 20000" or "within 15k"
        match = re.search(r'(?:under|within|budget|max|upto|up to)\s*(?:rs\.?|₹|inr)?\s*(\d+)\s*(k|K|thousand)?', query)
        if match:
            amount = int(match.group(1))
            if match.group(2) and match.group(2).lower() == 'k':
                amount *= 1000
            elif amount < 100:  # Likely meant in thousands
                amount *= 1000
            return amount
        
        # Pattern: just "20k" or "₹20000"
        match = re.search(r'(?:rs\.?|₹|inr)?\s*(\d+)\s*(k|K|thousand)?(?:\s*budget)?', query)
        if match:
            amount = int(match.group(1))
            if match.group(2) and match.group(2).lower() == 'k':
                amount *= 1000
            elif amount < 100:
                amount *= 1000
            # Only return if it looks like a budget (reasonable range)
            if 5000 <= amount <= 500000:
                return amount
        
        return None
    
    def _extract_budget_preference(self, query: str) -> str:
        """Extract budget preference."""
        for keyword, preference in self.budget_keywords.items():
            if keyword in query:
                return preference
        return 'balanced'
    
    def _extract_hotel_stars(self, query: str) -> int:
        """Extract hotel star preference."""
        match = re.search(r'(\d+)\s*star', query)
        if match:
            return min(max(int(match.group(1)), 1), 5)
        
        if 'luxury' in query or 'premium' in query:
            return 5
        if 'budget' in query or 'cheap' in query:
            return 2
        
        return 3
    
    def _generate_missing_info_message(self, missing: List[str], result: Dict) -> str:
        """Generate friendly message for missing info."""
        understood = []
        if result['source']:
            understood.append(f"from **{result['source']}**")
        if result['destination']:
            understood.append(f"to **{result['destination']}**")
        if result['num_days']:
            understood.append(f"for **{result['num_days']} days**")
        if result['max_budget']:
            understood.append(f"within **₹{result['max_budget']:,}**")
        
        msg = ""
        if understood:
            msg = f"Got it! Planning a trip {', '.join(understood)}. 👍\n\n"
        
        msg += "I just need:\n"
        
        cities_list = ", ".join(AVAILABLE_CITIES)
        for field in missing:
            if 'source' in field:
                msg += f"📍 **Where from?** ({cities_list})\n"
            elif 'destination' in field:
                msg += f"🎯 **Where to?** ({cities_list})\n"
            elif 'days' in field:
                msg += f"📅 **How many days?**\n"
        
        return msg
    
    def _generate_confirmation_message(self, result: Dict) -> str:
        """Generate confirmation message."""
        budget_info = ""
        if result['max_budget']:
            budget_info = f" within ₹{result['max_budget']:,}"
        
        return (
            f"✅ Planning **{result['num_days']}-day {result['budget_preference']} trip** "
            f"from **{result['source']}** to **{result['destination']}**{budget_info} "
            f"for **{result['num_travelers']}** traveler(s). Finding best options..."
        )


def parse_travel_query(query: str, context: Dict = None) -> Dict[str, Any]:
    """Convenience function."""
    parser = QueryParser()
    return parser.parse_query(query, context)
