import os
import json
import requests
from datetime import datetime
from typing import Optional, Literal, Dict, Any, List, Union
from datetime import datetime, timedelta
from typing import Optional, Literal, Dict, Any
from zoneinfo import ZoneInfo
import time
import random
from dotenv import load_dotenv

import serpapi
from mcp.server.fastmcp import FastMCP
from mcp import McpError
from mcp.server import Server
from mcp.types import Tool, TextContent

# Load environment variables from .env file
load_dotenv()

mcp_travel_assistant = FastMCP("Travel Assistant")

mcp_tool = mcp_travel_assistant.tool

# API keys configuration - support both variations
serp_api_key = os.getenv("SERPAPI_API_KEY") or os.getenv("SERP_API_KEY")
yelp_api_key = os.getenv("YELP_API_KEY")

# Constants for API keys (uppercase for use in functions)
SERPAPI_API_KEY = serp_api_key
YELP_API_KEY = yelp_api_key

# Configuration constants
FLIGHT_LIMITS = {
    "MAX_ADULTS": 6,
    "MAX_TOTAL_PASSENGERS": 6,
    "MAX_STRATEGIES": 4
}

HOTEL_LIMITS = {
    "MAX_ADULTS": 4,
    "MAX_TOTAL_GUESTS": 6,
    "MAX_STRATEGIES": 4
}

# Rate limiting configuration for Yelp API
YELP_RATE_LIMIT_DELAY = 5  # seconds between requests (increased from 2)
YELP_MAX_RETRIES = 2  # reduced retries to avoid hitting limits
YELP_BACKOFF_FACTOR = 3  # increased backoff factor
last_yelp_request_time = 0

# Airport code mappings for common issues
AIRPORT_CODE_MAPPINGS = {
    "PAR": "CDG",  # Paris - use Charles de Gaulle as primary
    "LON": "LHR",  # London - use Heathrow as primary
    "NYC": "JFK",  # New York - use JFK as primary
    "WAS": "DCA",  # Washington - use Reagan as primary
    "CHI": "ORD",  # Chicago - use O'Hare as primary
    "MIL": "MXP",  # Milan - use Malpensa as primary
    "MOW": "SVO",  # Moscow - use Sheremetyevo as primary
    "BUE": "EZE",  # Buenos Aires - use Ezeiza as primary
    "RIO": "GIG",  # Rio de Janeiro - use Galeão as primary
    "SAO": "GRU",  # São Paulo - use Guarulhos as primary
}

# Helper functions
def get_airport_code(code: str) -> str:
    """Get the best airport code, mapping problematic codes to specific airports"""
    return AIRPORT_CODE_MAPPINGS.get(code.upper(), code.upper())

def validate_date(date_str: str) -> bool:
    """Validate date format"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def adjust_date_if_past(date_str: str) -> tuple[str, bool]:
    """
    Adjust a date string if it's in the past to a future date.
    Returns (adjusted_date, was_adjusted)
    """
    try:
        if not validate_date(date_str):
            # If date format is invalid, return a week from now
            future_date = datetime.now().date() + timedelta(days=7)
            return future_date.strftime("%Y-%m-%d"), True
            
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        
        if date_obj <= today:
            # If date is in the past or today, move it to next week
            adjusted_date = today + timedelta(days=7)
            return adjusted_date.strftime("%Y-%m-%d"), True
        else:
            return date_str, False
    except ValueError:
        # If date format is invalid, return a week from now
        future_date = datetime.now().date() + timedelta(days=7)
        return future_date.strftime("%Y-%m-%d"), True

def cap_passengers(adults: int, children: int = 0, infants_in_seat: int = 0, infants_on_lap: int = 0) -> tuple[int, int, int, int, List[str]]:
    """
    Cap passenger counts to API limits and return adjustment notes
    Returns (adults, children, infants_in_seat, infants_on_lap, adjustment_notes)
    """
    original_adults = adults
    original_children = children
    original_infants_in_seat = infants_in_seat
    original_infants_on_lap = infants_on_lap
    notes = []
    
    # Auto-cap adults at limit
    if adults > FLIGHT_LIMITS["MAX_ADULTS"]:
        adults = FLIGHT_LIMITS["MAX_ADULTS"]
        notes.append(f"Adults reduced from {original_adults} to {adults} (API limit: {FLIGHT_LIMITS['MAX_ADULTS']} max)")
    
    # Auto-cap total passengers at limit
    total_passengers = adults + children + infants_in_seat + infants_on_lap
    if total_passengers > FLIGHT_LIMITS["MAX_TOTAL_PASSENGERS"]:
        # Reduce children first, then infants to fit within limit
        excess = total_passengers - FLIGHT_LIMITS["MAX_TOTAL_PASSENGERS"]
        if children >= excess:
            children = children - excess
        else:
            children = 0
            excess = excess - children
            if infants_in_seat >= excess:
                infants_in_seat = infants_in_seat - excess
            else:
                infants_in_seat = 0
                excess = excess - infants_in_seat
                infants_on_lap = max(0, infants_on_lap - excess)
        
        notes.append(f"Total passengers reduced from {original_adults + original_children + original_infants_in_seat + original_infants_on_lap} to {adults + children + infants_in_seat + infants_on_lap} (API limit: {FLIGHT_LIMITS['MAX_TOTAL_PASSENGERS']} max)")
    
    return adults, children, infants_in_seat, infants_on_lap, notes

def cap_hotel_guests(adults: int, children: int = 0) -> tuple[int, int, List[str]]:
    """
    Cap hotel guest counts to API limits and return adjustment notes
    Returns (adults, children, adjustment_notes)
    """
    original_adults = adults
    original_children = children
    notes = []
    
    # Auto-cap adults at hotel limit
    if adults > HOTEL_LIMITS["MAX_ADULTS"]:
        adults = HOTEL_LIMITS["MAX_ADULTS"]
        notes.append(f"Adults reduced from {original_adults} to {adults} (API limit: {HOTEL_LIMITS['MAX_ADULTS']} adults max)")
    
    # Auto-cap total guests at limit
    total_guests = adults + children
    if total_guests > HOTEL_LIMITS["MAX_TOTAL_GUESTS"]:
        # Reduce children to fit within limit
        excess = total_guests - HOTEL_LIMITS["MAX_TOTAL_GUESTS"]
        children = max(0, children - excess)
        notes.append(f"Children reduced from {original_children} to {children} (guest limit: {HOTEL_LIMITS['MAX_TOTAL_GUESTS']} total)")
    
    return adults, children, notes

def generate_children_ages(children_count: int) -> str:
    """Generate default ages for children"""
    if children_count <= 0:
        return ""
    # Generate ages between 5-12 years old
    ages = [str(5 + (i % 8)) for i in range(children_count)]
    return ",".join(ages)

def clean_location_query(query: str) -> tuple[str, bool]:
    """Clean up location queries for better API compatibility"""
    original_query = query
    
    # Handle known problematic locations
    location_mappings = {
        "Edinburgh Old Town": "Edinburgh, Scotland",
        "Jeju Island": "Jeju, South Korea",
        "Old Town Edinburgh": "Edinburgh, Scotland",
        "Edinburgh Old Town, Scotland": "Edinburgh, Scotland",
        "Jeju Island, South Korea": "Jeju, South Korea",
        "Santorini Old Town": "Santorini, Greece",
        "Venice Old Town": "Venice, Italy",
        "Prague Old Town": "Prague, Czech Republic",
        "Dubrovnik Old Town": "Dubrovnik, Croatia",
    }
    
    # Check if query matches any problematic location
    for problematic, replacement in location_mappings.items():
        if problematic.lower() in query.lower():
            query = query.lower().replace(problematic.lower(), replacement)
            return query, True
    
    # Additional query cleanup - remove potentially problematic terms
    problematic_terms = ["old town", "old city", "historic district", "historic center"]
    for term in problematic_terms:
        if term in query.lower():
            query = query.replace(term, "").strip()
            if query.endswith(","):
                query = query[:-1].strip()
            return query, True
    
    return query, False

def create_flight_error_response(error_msg: str, departure_id: str, arrival_id: str, suggestions: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a standardized flight error response"""
    default_suggestions = [
        f"Try alternative airports near {departure_id} or {arrival_id}",
        "Consider different travel dates",
        "Check if the route is served by airlines",
        "Try booking directly with airlines"
    ]
    
    return {
        "error": error_msg,
        "message": "Unable to search flights at this time. Please try alternative approaches.",
        "suggestions": suggestions or default_suggestions,
        "alternative_airports": {
            "departure": f"Consider airports near {departure_id}",
            "arrival": f"Consider airports near {arrival_id}"
        }
    }

def create_hotel_error_response(error_msg: str, location: str, suggestions: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a standardized hotel error response"""
    default_suggestions = [
        f"Try searching for a broader location (e.g., city instead of specific area)",
        "Consider different dates",
        "Check if the location name is spelled correctly",
        "Try removing specific area names from your search"
    ]
    
    return {
        "error": error_msg,
        "message": "Unable to find hotels for the specified criteria. Please try alternative approaches.",
        "suggestions": suggestions or default_suggestions,
        "location_tried": location
    }


@mcp_tool()
def get_date(timezone: str = "Asia/Singapore"):
    """
    A function to return todays date and time with timezone. Call this before any other functions if you are unaware of the date and time.
    """
    try:
        # Get the current date and time in the user's timezone
        user_tz = ZoneInfo(timezone)
        current_datetime = datetime.now(user_tz)

        # Format the datetime string
        formatted_datetime = current_datetime.isoformat()

        return f"Current date and time: {formatted_datetime} ({timezone})"
    except Exception as e:
        # Fallback to UTC if timezone is invalid
        current_datetime = datetime.now(ZoneInfo("UTC"))
        formatted_datetime = current_datetime.isoformat()
        return f"Current date and time: {formatted_datetime} (UTC - invalid timezone '{timezone}' provided)"


@mcp_tool()
def search_flights(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: Optional[str] = None,
    trip_type: Literal[1, 2, 3] = 2,
    travel_class: Literal[1, 2, 3, 4] = 1,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    include_airlines: Optional[str] = "",
) -> Dict[str, Any]:
    """
    Search for flights with enhanced error handling and smart fallbacks.
    
    Args:
        departure_id: Departure airport code
        arrival_id: Arrival airport code
        outbound_date: Departure date (YYYY-MM-DD)
        return_date: Return date for round trips (YYYY-MM-DD). Default: None
        trip_type: 1=Round trip, 2=One way, 3=Multi-city. Default: 2
        travel_class: 1=Economy, 2=Premium, 3=Business, 4=First. Default: 1
        include_airlines: Airline IATA code to include. Default: ""
    """
    # Map problematic airport codes to specific airports
    original_departure = departure_id
    original_arrival = arrival_id
    departure_id = get_airport_code(departure_id)
    arrival_id = get_airport_code(arrival_id)
    
    # Cap passengers to API limits
    adults, children, infants_in_seat, infants_on_lap, passenger_notes = cap_passengers(
        adults, children, infants_in_seat, infants_on_lap
    )

    # Adjust dates if they're in the past
    original_outbound_date = outbound_date
    outbound_date, outbound_adjusted = adjust_date_if_past(outbound_date)
    
    original_return_date = return_date
    return_adjusted = False
    if return_date:
        return_date, return_adjusted = adjust_date_if_past(return_date)
        # Ensure return date is after outbound date
        outbound_obj = datetime.strptime(outbound_date, "%Y-%m-%d").date()
        return_obj = datetime.strptime(return_date, "%Y-%m-%d").date()
        if return_obj <= outbound_obj:
            return_date = (outbound_obj + timedelta(days=1)).strftime("%Y-%m-%d")
            return_adjusted = True

    # Enhanced search strategies with airport code fallbacks
    search_strategies = [
        # Strategy 1: Original parameters (with mapped codes)
        {},
        # Strategy 2: Try different date (add 1 day)
        {
            "outbound_date": (datetime.strptime(outbound_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
            "return_date": (datetime.strptime(return_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d") if return_date else None
        },
        # Strategy 3: Try one-way if round trip fails
        {"trip_type": 2, "return_date": None},
        # Strategy 4: Try with fewer passengers
        {"adults": min(adults, 2), "children": 0, "infants_in_seat": 0, "infants_on_lap": 0}
    ]
    
    results = None
    strategy_used = 0
    
    for i, strategy in enumerate(search_strategies):
        params = {
            "api_key": SERPAPI_API_KEY,
            "engine": "google_flights",
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "outbound_date": strategy.get("outbound_date", outbound_date),
            "type": strategy.get("trip_type", trip_type),
            "travel_class": travel_class,
            "adults": strategy.get("adults", adults),
            "children": strategy.get("children", children),
            "infants_in_seat": strategy.get("infants_in_seat", infants_in_seat),
            "infants_on_lap": strategy.get("infants_on_lap", infants_on_lap),
            "currency": "USD",
            "hl": "en",
            "include_airlines": include_airlines,
        }

        if strategy.get("return_date") is not None or (not strategy.get("return_date") and return_date and i == 0):
            if strategy.get("return_date"):
                params["return_date"] = strategy["return_date"]
            elif return_date and i == 0:
                params["return_date"] = return_date

        try:
            results = serpapi.search(params).as_dict()
            
            # Check if we got meaningful results
            has_results = False
            if results:
                # Check for actual flight results
                if "best_flights" in results and len(results["best_flights"]) > 0:
                    has_results = True
                elif "other_flights" in results and len(results["other_flights"]) > 0:
                    has_results = True
                elif results.get("search_information", {}).get("flights_results_state") != "Fully empty":
                    has_results = True
            
            if has_results:
                strategy_used = i + 1
                break
            elif i < len(search_strategies) - 1:
                # Wait a bit before trying next strategy
                time.sleep(1)
                continue
                
        except Exception as e:
            if i == len(search_strategies) - 1:
                # Last strategy failed - provide enhanced error response
                return create_flight_error_response(
                    f"Flight search failed: {str(e)}", 
                    departure_id, 
                    arrival_id,
                    [
                        "Check if airport codes are correct",
                        "Try different dates",
                        "Consider alternative airports nearby",
                        f"Original codes: {original_departure} → {original_arrival}",
                        f"Mapped codes: {departure_id} → {arrival_id}"
                    ]
                )
            continue
    
    # Handle case where no flights found
    if not results or results.get("search_information", {}).get("flights_results_state") == "Fully empty":
        return create_flight_error_response(
            "No flights found",
            departure_id,
            arrival_id,
            [
                f"No flights available for {departure_id} → {arrival_id}",
                "Try alternative airports nearby",
                "Consider different travel dates",
                "Check if the route is served by airlines",
                f"Strategies attempted: {len(search_strategies)}"
            ]
        )
    
    # Add comprehensive metadata about adjustments
    if "search_metadata" not in results:
        results["search_metadata"] = {}
    
    all_notes = []
    
    # Add airport code mapping notes
    if original_departure != departure_id:
        all_notes.append(f"Departure airport mapped from {original_departure} to {departure_id}")
    if original_arrival != arrival_id:
        all_notes.append(f"Arrival airport mapped from {original_arrival} to {arrival_id}")
    
    # Add passenger adjustment notes
    all_notes.extend(passenger_notes)
    
    # Add date adjustment notes
    if outbound_adjusted:
        all_notes.append(f"Outbound date adjusted from {original_outbound_date} to {outbound_date} (past date)")
    if return_adjusted:
        all_notes.append(f"Return date adjusted from {original_return_date} to {return_date} (past date or before outbound)")
    
    # Add strategy notes
    if strategy_used > 1:
        all_notes.append(f"Used search strategy {strategy_used} to find results (original search yielded no results)")
    
    if all_notes:
        results["search_metadata"]["adjustment_notes"] = all_notes
    
    return results


@mcp_tool()
def search_hotels(
    query: str,
    check_in_date: str,
    check_out_date: str,
    adults: int = 2,
    children: int = 0,
    children_ages: Optional[str] = None,
    sort_by: Optional[
        Literal[3, 8, 13]
    ] = None,  # 3=Lowest price, 8=Highest rating, 13=Most reviewed
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    hotel_class: Optional[
        str
    ] = None,  # "2,3,4,5" for multiple classes    # Vacation rental specific parameters
    limit: Optional[int] = 5,
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Search for hotels and accommodations using the Google Hotels API via SerpAPI.

    Args:
        query (str): Search query for location/hotel name
        check_in_date (str): Check-in date in YYYY-MM-DD format
        check_out_date (str): Check-out date in YYYY-MM-DD format
        adults (int, optional): Number of adults. Defaults to 2.
        children (int, optional): Number of children. Defaults to 0.
        children_ages (str, optional): Comma-separated ages of children
        sort_by (int, optional): Sort results by - 3=Lowest price, 8=Highest rating, 13=Most reviewed
        min_price (float, optional): Minimum price filter
        max_price (float, optional): Maximum price filter
        hotel_class (str, optional): Filter by hotel class (e.g. "2,3,4,5")
        limit (int, optional): Maximum number of results to return. Defaults to 5.
    """
    # Cap guest counts to API limits
    adults, children, guest_notes = cap_hotel_guests(adults, children)

    # Fix children_ages mismatch - generate default ages if children > 0 but no ages provided
    original_children_ages = children_ages
    children_ages_adjusted = False
    if children > 0 and not children_ages:
        children_ages = generate_children_ages(children)
        children_ages_adjusted = True
    elif children > 0 and children_ages:
        # Validate that number of ages matches number of children
        ages_list = children_ages.split(",")
        if len(ages_list) != children:
            # Adjust ages to match children count
            if len(ages_list) < children:
                # Add default ages for missing children
                for i in range(children - len(ages_list)):
                    ages_list.append(str(6 + i))
            else:
                # Trim excess ages
                ages_list = ages_list[:children]
            children_ages = ",".join(ages_list)
            children_ages_adjusted = True
    elif children == 0:
        # No children, so no ages needed
        children_ages = None

    # Clean up and standardize location query for better API compatibility
    original_query = query
    query, query_adjusted = clean_location_query(query)

    # Adjust dates if they're in the past
    original_check_in_date = check_in_date
    check_in_date, checkin_adjusted = adjust_date_if_past(check_in_date)
    
    original_check_out_date = check_out_date
    check_out_date, checkout_adjusted = adjust_date_if_past(check_out_date)
    
    # Ensure check-out is after check-in
    checkin_obj = datetime.strptime(check_in_date, "%Y-%m-%d").date()
    checkout_obj = datetime.strptime(check_out_date, "%Y-%m-%d").date()
    if checkout_obj <= checkin_obj:
        check_out_date = (checkin_obj + timedelta(days=1)).strftime("%Y-%m-%d")
        checkout_adjusted = True

    # Try multiple search strategies if no results
    search_strategies = [
        # Strategy 1: Original query
        {"q": query},
        # Strategy 2: Broader location search (remove specific area names)
        {"q": query.split(",")[0].strip() if "," in query else query},
        # Strategy 3: Add "hotels" to query
        {"q": f"hotels {query}"},
        # Strategy 4: Try with different date range (add a day)
        {"q": query, "check_in_date": (datetime.strptime(check_in_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
         "check_out_date": (datetime.strptime(check_out_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")},
    ]
    
    results = None
    strategy_used = 0
    
    for i, strategy in enumerate(search_strategies):
        params = {
            "api_key": SERPAPI_API_KEY,
            "engine": "google_hotels",
            "check_in_date": strategy.get("check_in_date", check_in_date),
            "check_out_date": strategy.get("check_out_date", check_out_date),
            "adults": adults,
            "children": children,
            "currency": "USD",
            "hl": "en",
        }
        
        # Update query for this strategy
        params["q"] = strategy["q"]

        # Add optional parameters
        if children_ages and children > 0:
            params["children_ages"] = children_ages
        if sort_by:
            params["sort_by"] = sort_by
        if min_price:
            params["min_price"] = min_price
        if max_price:
            params["max_price"] = max_price
        if hotel_class:
            params["hotel_class"] = hotel_class

        try:
            results = serpapi.search(params).as_dict()
            
            # Check if we got meaningful results
            if "properties" in results and len(results["properties"]) > 0:
                strategy_used = i + 1
                break
            elif i < len(search_strategies) - 1:
                # Wait a bit before trying next strategy
                time.sleep(0.5)
                continue
                
        except Exception as e:
            if i == len(search_strategies) - 1:
                # Last strategy failed - provide enhanced error response
                return create_hotel_error_response(
                    f"Hotel search failed: {str(e)}",
                    query,
                    [
                        f"API error occurred for location: {query}",
                        "Try a different location name",
                        "Consider broader search terms",
                        "Check if dates are valid"
                    ]
                )
            continue
    
    if not results:
        return create_hotel_error_response(
            "No hotel search results available",
            query,
            [
                "Try searching for a broader location (e.g., city instead of specific area)",
                "Consider different dates",
                "Check if the location name is spelled correctly",
                f"Strategies attempted: {len(search_strategies)}"
            ]
        )
    
    # Add notes about any adjustments made
    if "search_metadata" not in results:
        results["search_metadata"] = {}
    
    all_notes = []
    
    # Add guest count adjustment notes
    all_notes.extend(guest_notes)
    
    # Add children ages adjustment notes
    if children_ages_adjusted:
        if original_children_ages:
            all_notes.append(f"Children ages adjusted from '{original_children_ages}' to '{children_ages}' (count mismatch)")
        else:
            all_notes.append(f"Children ages generated: '{children_ages}' (missing ages for {children} children)")
    
    # Add location query adjustment notes
    if query_adjusted:
        all_notes.append(f"Location query adjusted from '{original_query}' to '{query}' (API compatibility)")
    
    # Add date adjustment notes
    if checkin_adjusted:
        all_notes.append(f"Check-in date adjusted from {original_check_in_date} to {check_in_date} (past date)")
    
    if checkout_adjusted:
        all_notes.append(f"Check-out date adjusted from {original_check_out_date} to {check_out_date} (past date or before check-in)")
    
    # Add strategy notes
    if strategy_used > 1:
        all_notes.append(f"Used search strategy {strategy_used} to find results (original query yielded no results)")
    
    if all_notes:
        results["search_metadata"]["adjustment_notes"] = all_notes
    
    # Handle case where no properties found
    if "properties" not in results or len(results["properties"]) == 0:
        return {
            "message": "No hotels found for this search",
            "search_metadata": results.get("search_metadata", {}),
            "suggestions": [
                "Try a different location or broader search area",
                "Consider different dates",
                "Check spelling of location name"
            ],
            "original_response": results
        }
    
    # Limit to top results if there are more
    results["properties"] = results["properties"][:limit]
    
    # Simplify the results
    simplified_results = []
    for hotel in results["properties"]:
        if isinstance(hotel, str):
            hotel = json.loads(hotel)
        simplified_hotel = {
            "name": hotel.get("name", "N/A"),
            "description": hotel.get("description", "N/A"),
            "link": hotel.get("link", "N/A"),
            "gps_coordinates": hotel.get("gps_coordinates", "N/A"),
            "check_in_time": hotel.get("check_in_time", "N/A"),
            "check_out_time": hotel.get("check_out_time", "N/A"),
            "rate_per_night": hotel.get("rate_per_night", {}).get(
                "lowest", "N/A"
            ),
            "total_rate": hotel.get("total_rate", {}).get("lowest", "N/A"),
            "overall_rating": hotel.get("overall_rating", "N/A"),
            "nearby_places": hotel.get("nearby_places", "N/A"),
            "hotel_class": hotel.get("hotel_class", "N/A"),
            "amenities": hotel.get("amenities", "N/A"),
        }
        simplified_results.append(simplified_hotel)
    return simplified_results


@mcp_tool()
def search_restaurants_yelp(query: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Search for restaurants using Yelp AI Chat API with conservative rate limiting and retry logic.

    This function queries Yelp's AI Chat API to search for restaurants based on natural language queries.
    The results are simplified to include key business information.

    Args:
        query (str): Natural language query describing restaurant preferences (e.g. "Italian restaurants in New York",
                    "Vegetarian friendly cafes in San Francisco", "Best sushi places near me")
    """
    global last_yelp_request_time
    
    # Conservative rate limiting: ensure we don't make requests too frequently
    current_time = time.time()
    time_since_last_request = current_time - last_yelp_request_time
    if time_since_last_request < YELP_RATE_LIMIT_DELAY:
        sleep_time = YELP_RATE_LIMIT_DELAY - time_since_last_request
        time.sleep(sleep_time)
    
    url = "https://api.yelp.com/ai/chat/v2"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {YELP_API_KEY}",
    }
    
    # Conservative retry logic with longer delays
    for attempt in range(YELP_MAX_RETRIES):
        try:
            last_yelp_request_time = time.time()
            
            response = requests.post(
                url, headers=headers, json={"query": query}, timeout=30
            )
            
            # Handle rate limiting (429) specifically with longer backoff
            if response.status_code == 429:
                if attempt < YELP_MAX_RETRIES - 1:
                    # Much longer exponential backoff
                    backoff_time = (YELP_BACKOFF_FACTOR ** attempt) * YELP_RATE_LIMIT_DELAY
                    jitter = random.uniform(1, 3)  # Longer jitter
                    total_wait = backoff_time + jitter
                    
                    time.sleep(total_wait)
                    continue
                else:
                    # Final attempt failed with 429 - provide comprehensive fallback
                    return {
                        "error": "Restaurant search temporarily unavailable",
                        "message": "Unable to access restaurant database due to high demand. Please try alternative methods.",
                        "fallback_options": [
                            "Use Google Maps or Google Search for restaurant recommendations",
                            "Check TripAdvisor or local tourism websites",
                            "Ask locals or hotel concierge for recommendations",
                            "Use general travel guides for the destination"
                        ],
                        "manual_suggestions": {
                            "query": query,
                            "note": "Search for this query manually using web search engines"
                        },
                        "retry_after": "Please wait 10-15 minutes before trying restaurant search again"
                    }
            
            # Check if request was successful
            if response.status_code != 200:
                if attempt < YELP_MAX_RETRIES - 1:
                    # Retry for other non-200 status codes with longer delay
                    backoff_time = (YELP_BACKOFF_FACTOR ** attempt) * YELP_RATE_LIMIT_DELAY
                    time.sleep(backoff_time)
                    continue
                else:
                    return {
                        "error": f"Restaurant search service returned error {response.status_code}",
                        "message": "Restaurant search service is currently unavailable.",
                        "fallback_options": [
                            "Use Google Maps for restaurant search",
                            "Check local food blogs and review sites",
                            "Consult travel guidebooks for restaurant recommendations"
                        ]
                    }
            
            # Success! Process the response
            results = response.json()
            
            # Handle string response (if API returns stringified JSON)
            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except json.JSONDecodeError:
                    return {
                        "error": "Invalid response from restaurant search service",
                        "message": "Unable to parse restaurant search results.",
                        "fallback_options": [
                            "Try a different search query",
                            "Use Google Maps or other restaurant search services"
                        ]
                    }
            
            # Check for different response formats
            businesses = []
            
            # Format 1: Standard entities format
            if "entities" in results and isinstance(results["entities"], list) and len(results["entities"]) > 0:
                if "businesses" in results["entities"][0]:
                    businesses = results["entities"][0]["businesses"]
            
            # Format 2: Direct businesses array
            elif "businesses" in results:
                businesses = results["businesses"]
            
            # Format 3: Results array
            elif "results" in results:
                businesses = results["results"]
            
            # Format 4: Data wrapper
            elif "data" in results and "businesses" in results["data"]:
                businesses = results["data"]["businesses"]
            
            # If we found businesses, process them
            if businesses and len(businesses) > 0:
                simplified_results = []
                for business in businesses[:5]:  # Limit to 5 results
                    simplified_business = {
                        "name": business.get("name", "N/A"),
                        "alias": business.get("alias", "N/A"),
                        "rating": business.get("rating", "N/A"),
                        "categories": business.get("categories", "N/A"),
                        "price": business.get("price", "N/A"),
                        "location": business.get("location", "N/A"),
                        "phone": business.get("phone", "N/A"),
                        "url": business.get("url", "N/A"),
                        "review_count": business.get("review_count", "N/A"),
                    }
                    simplified_results.append(simplified_business)
                return {
                    "restaurants": simplified_results,
                    "source": "Yelp AI Chat API",
                    "note": f"Successfully retrieved after {attempt + 1} attempt(s)"
                }
            
            # If no businesses found, return helpful message
            else:
                return {
                    "message": "No restaurants found for this specific query",
                    "suggestions": [
                        "Try a broader search (e.g., just the city name)",
                        "Search for a different cuisine type",
                        "Use general web search for restaurant recommendations"
                    ],
                    "fallback_options": [
                        "Google Maps restaurant search",
                        "TripAdvisor restaurant listings",
                        "Local tourism websites"
                    ]
                }
                
        except requests.exceptions.Timeout:
            if attempt < YELP_MAX_RETRIES - 1:
                time.sleep(YELP_BACKOFF_FACTOR ** attempt * 2)
                continue
            return {
                "error": "Restaurant search timeout",
                "message": "Restaurant search service is taking too long to respond.",
                "fallback_options": [
                    "Try again in a few minutes",
                    "Use Google Maps for restaurant search",
                    "Check local restaurant review websites"
                ]
            }
        except requests.exceptions.RequestException as e:
            if attempt < YELP_MAX_RETRIES - 1:
                time.sleep(YELP_BACKOFF_FACTOR ** attempt * 2)
                continue
            return {
                "error": f"Network error: {str(e)}",
                "message": "Unable to connect to restaurant search service.",
                "fallback_options": [
                    "Check your internet connection",
                    "Try again later",
                    "Use alternative restaurant search methods"
                ]
            }
        except Exception as e:
            if attempt < YELP_MAX_RETRIES - 1:
                time.sleep(YELP_BACKOFF_FACTOR ** attempt * 2)
                continue
            return {
                "error": f"Unexpected error: {str(e)}",
                "message": "An unexpected error occurred while searching restaurants.",
                "fallback_options": [
                    "Try a different search approach",
                    "Use manual restaurant search methods",
                    "Consult travel guides or local recommendations"
                ]
            }
    
    # This should never be reached, but just in case
    return {
        "error": "Maximum retries exceeded",
        "message": "Unable to complete restaurant search after multiple attempts",
        "fallback_options": [
            "Please try again in 15-20 minutes",
            "Use alternative restaurant search services",
            "Consult local tourism resources"
        ]
    }


@mcp_tool()
def search_local_business(query: str, location: str) -> List[Dict[str, Any]]:
    """
    Search for local attractions, businesses, and points of interest in a specific location.
    This function search for locations instead of events.

    Args:
        query (str): Search query describing what to look for (e.g. "museums", "parks", "coffee shops")
        location (str): Location to search in (e.g. "New York", "Paris, France")
    """
    # Clean up location parameter for better API compatibility
    original_location = location
    location, location_adjusted = clean_location_query(location)

    params = {
        "engine": "google_local",
        "q": query,
        "location": location,
        "api_key": SERPAPI_API_KEY,
    }
    
    try:
        results = serpapi.search(params).as_dict()

        # Add note about location adjustment if made
        if location_adjusted:
            if "search_metadata" not in results:
                results["search_metadata"] = {}
            results["search_metadata"]["location_adjustment_note"] = (
                f"Location adjusted from '{original_location}' to '{location}' for API compatibility"
            )

        # Simplify the results
        simplified_results = []
        if "local_results" in results:
            for result in results["local_results"][:5]:
                simplified_result = {
                    "name": result.get("title", "N/A"),
                    "type": result.get("type", "N/A"),
                    "address": result.get("address", "N/A"),
                    "description": result.get("description", "N/A"),
                    "gps_coordinates": result.get("gps_coordinates", "N/A"),
                }
                simplified_results.append(simplified_result)
        return simplified_results
    except Exception as e:
        raise Exception(f"Error searching local business: {str(e)}")


@mcp_tool()
def search_local_events(query: str, location: str, time_filter: str) -> List[Dict[str, Any]]:
    """
    Search for local events like concerts, exhibitions, etc. using Google Events via SerpAPI.
    This function search for events instead of locations.

    This function searches for events based on a query and time filter, returning simplified
    event details like name, date, address, link and description.

    Args:
        query (str): Search query for events (e.g. "concerts", "art exhibitions")
        location (str): Location to search in (e.g. Singapore)
        time_filter (str): Filter events by time period. One of:
            - "today": Today's events
            - "tomorrow": Tomorrow's events
            - "week": This week's events
            - "today_weekend": Events this weekend
            - "next_week": Next week's events
            - "month": This month's events
            - "next_month": Next month's events
    """
    # Clean up location parameter for better API compatibility (events work better with simpler names)
    original_location = location
    location, location_adjusted = clean_location_query(location)
    
    # For events, simplify even further by using just the city name
    if "," in location:
        location = location.split(",")[0].strip()
        location_adjusted = True

    params = {
        "engine": "google_events",
        "q": f"{query} in {location}",
        "hl": "en",
        "gl": "us",
        "htichips": f"date:{time_filter}",
        "api_key": SERPAPI_API_KEY,
    }
    
    try:
        results = serpapi.search(params).as_dict()
        
        # Add note about location adjustment if made
        if location_adjusted:
            if "search_metadata" not in results:
                results["search_metadata"] = {}
            results["search_metadata"]["location_adjustment_note"] = (
                f"Location adjusted from '{original_location}' to '{location}' for API compatibility"
            )
        
        simplified_results = []
        if "events_results" in results:
            for event in results["events_results"][:5]:
                simplified_event = {
                    "name": event.get("title", "N/A"),
                    "date": event.get("date", "N/A"),
                    "address": event.get("address", "N/A"),
                    "link": event.get("link", "N/A"),
                    "description": event.get("description", "N/A"),
                    "ticket_info": (
                        ticket_info[0]
                        if (ticket_info := event.get("ticket_info", None))
                        else "N/A"
                    ),
                    "venue": event.get("venue", "N/A"),
                }
                simplified_results.append(simplified_event)
        return simplified_results
    except Exception as e:
        raise Exception(f"Error searching local events: {str(e)}")

if __name__ == "__main__":
    # Initialize and run the server
    mcp_travel_assistant.run(transport='stdio')