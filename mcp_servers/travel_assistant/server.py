import os
import json
import requests
from datetime import datetime
from typing import Optional, Literal, Dict, Any
from zoneinfo import ZoneInfo

import serpapi
from mcp.server.fastmcp import FastMCP

mcp_travel_assistant = FastMCP("Travel Assistant")

mcp_tool = mcp_travel_assistant.tool

serp_api_key = os.getenv("SERP_API_KEY")
yelp_api_key = os.getenv("YELP_API_KEY")


@mcp_tool()
def get_date(timezone: str = "Asia/Singapore"):
    """
    A function to return todays date and time with timezone. Call this before any other functions if you are unaware of the date and time.
    """

    # Get the current date and time in the user's timezone
    user_tz = ZoneInfo(timezone)
    current_datetime = datetime.now(user_tz)

    # Format the datetime string
    formatted_datetime = current_datetime.isoformat()

    return f"Current date and time: {formatted_datetime} ({timezone})"


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
    Search for flights (defaults to Singapore Airlines).
    Args:
        departure_id: Departure airport code
        arrival_id: Arrival airport code
        outbound_date: Departure date (YYYY-MM-DD)
        return_date: Return date for round trips (YYYY-MM-DD). Default: None
        trip_type: 1=Round trip, 2=One way, 3=Multi-city. Default: 2
        travel_class: 1=Economy, 2=Premium, 3=Business, 4=First. Default: 1
        include_airlines: Airline IATA code to include. Default: ""
    """
    params = {
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "type": trip_type,
        "travel_class": travel_class,
        "adults": adults,
        "children": children,
        "infants_in_seat": infants_in_seat,
        "infants_on_lap": infants_on_lap,
        "currency": "USD",
        "hl": "en",
        "include_airlines": include_airlines,
    }

    # Add optional parameters only if they're provided
    if return_date and trip_type == 1:
        params["return_date"] = return_date

    try:
        results = serpapi.search(params).as_dict()
        # Simplify the results
        simplified_results = {"flights": [], "best_flights": []}

        if "best_flights" in results:
            for flight in results["best_flights"]:
                simplified_flight = {
                    "segments": [],
                    "layovers": flight.get("layovers", []),
                    "total_duration": flight.get("total_duration", "N/A"),
                    "type": flight.get("type", "N/A"),
                }
                for segment in flight["flights"]:
                    flight_segment = {
                        "departure_airport": segment.get("departure_airport", "N/A"),
                        "arrival_airport": segment.get("arrival_airport", "N/A"),
                        "duration": segment.get("duration", "N/A"),
                        "travel_class": segment.get("travel_class", "N/A"),
                        "flight_number": segment.get("flight_number", "N/A"),
                        "legroom": segment.get("legroom", "N/A"),
                    }
                    simplified_flight["segments"].append(flight_segment)
                simplified_results["best_flights"].append(simplified_flight)

        if "other_flights" in results:
            for flight in results["other_flights"]:
                simplified_flight = {
                    "segments": [],
                    "layovers": flight.get("layovers", []),
                    "total_duration": flight.get("total_duration", "N/A"),
                    "type": flight.get("type", "N/A"),
                }
                for segment in flight["flights"]:
                    flight_segment = {
                        "departure_airport": segment.get("departure_airport", "N/A"),
                        "arrival_airport": segment.get("arrival_airport", "N/A"),
                        "duration": segment.get("duration", "N/A"),
                        "travel_class": segment.get("travel_class", "N/A"),
                        "flight_number": segment.get("flight_number", "N/A"),
                        "legroom": segment.get("legroom", "N/A"),
                    }
                    simplified_flight["segments"].append(flight_segment)
                simplified_results["flights"].append(simplified_flight)
        return simplified_results

    except Exception as e:
        raise Exception(f"Error searching flights: {str(e)}")


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
) -> Dict[str, Any]:
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
    params = {
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "engine": "google_hotels",
        "q": query,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "adults": adults,
        "children": children,
        "currency": "USD",
        "hl": "en",
    }

    # Add optional parameters
    if children_ages:
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
        # Limit to top 10 properties if there are more
        if "properties" in results:
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
        return results
    except Exception as e:
        raise Exception(f"Error searching hotels: {str(e)}")


@mcp_tool()
def search_restaurants_yelp(query: str) -> Dict[str, Any]:
    """
    Search for restaurants using Yelp AI Chat API.

    This function queries Yelp's AI Chat API to search for restaurants based on natural language queries.
    The results are simplified to include key business information.

    Args:
        query (str): Natural language query describing restaurant preferences (e.g. "Italian restaurants in New York",
                    "Vegetarian friendly cafes in San Francisco", "Best sushi places near me")
    """
    yelp_api_key = os.getenv("YELP_API_KEY")
    url = "https://api.yelp.com/ai/chat/v2"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {yelp_api_key}",
    }
    results = requests.post(
        url, headers=headers, json={"query": query}, timeout=30
    ).json()
    if isinstance(results, str):
        results = json.loads(results)
    if "businesses" in results["entities"][0]:
        simplified_results = []
        for business in results["entities"][0]["businesses"][:5]:
            simplified_results.append(
                {
                    "name": business.get("name", "N/A"),
                    "alias": business.get("alias", "N/A"),
                    "rating": business.get("rating", "N/A"),
                    "categories": business.get("categories", "N/A"),
                    "price": business.get("price", "N/A"),
                    "location": business.get("location", "N/A"),
                    "phone": business.get("phone", "N/A"),
                }
            )
        return simplified_results
    return results


@mcp_tool()
def search_local_business(query: str, location: str) -> Dict[str, Any]:
    """
    Search for local attractions, businesses, and points of interest in a specific location.
    This function search for locations instead of events.

    Args:
        query (str): Search query describing what to look for (e.g. "museums", "parks", "coffee shops")
        location (str): Location to search in (e.g. "New York", "Paris, France")
    """
    params = {
        "engine": "google_local",
        "q": query,
        "location": location,
        "api_key": os.getenv("SERPAPI_API_KEY"),
    }
    results = serpapi.search(params).as_dict()

    # Simplify the results
    simplified_results = []
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


@mcp_tool()
def search_local_events(query: str, location: str, time_filter: str) -> Dict[str, Any]:
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
    params = {
        "engine": "google_events",
        "q": f"{query} in {location}",
        "hl": "en",
        "gl": "us",
        "htichips": f"date:{time_filter}",
        "api_key": os.getenv("SERPAPI_API_KEY"),
    }
    results = serpapi.search(params).as_dict()
    simplified_results = []
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

if __name__ == "__main__":
    # Initialize and run the server
    mcp_travel_assistant.run(transport='stdio')