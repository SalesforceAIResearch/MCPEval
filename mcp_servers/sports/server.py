#!/usr/bin/env uv run
import os
import sys
import json
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Literal
import urllib.parse
import aiohttp
import ssl

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Rate limiting for free tier (5 requests per minute)
class RateLimiter:
    def __init__(self, max_requests=5, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """Wait if we're hitting rate limits."""
        async with self.lock:
            now = time.time()
            # Remove requests older than time_window
            self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
            
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = self.time_window - (now - oldest_request) + 1
                if wait_time > 0:
                    logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.time()
                    self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
            
            # Add current request
            self.requests.append(now)

# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=5, time_window=60)

# Initialize the MCP server
mcp_sports = FastMCP("Sports Assistant")
mcp_tool = mcp_sports.tool

# Global HTTP client for reuse
_http_client = None

# SSL verification setting
VERIFY_SSL = os.environ.get("VERIFY_SSL", "true").lower() != "false"
logger.info(f"SSL verification: {'Enabled' if VERIFY_SSL else 'Disabled'}")

async def get_http_client():
    """Get or create a shared HTTP client session."""
    global _http_client
    if _http_client is None or _http_client.closed:
        # Create a connector with SSL verification setting
        ssl_context = ssl.create_default_context()
        if not VERIFY_SSL:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        _http_client = aiohttp.ClientSession(connector=connector)
    return _http_client

async def close_http_client():
    """Close the shared HTTP client session."""
    global _http_client
    if _http_client and not _http_client.closed:
        await _http_client.close()
        _http_client = None
        await asyncio.sleep(0.5)

# Cache for responses
_cache = {}

async def get_cached_or_fetch(key, fetch_func):
    """Get a cached response or fetch a new one."""
    if key in _cache:
        return _cache[key]
    
    result = await fetch_func()
    _cache[key] = result
    return result

def get_api_headers():
    """Get headers for API requests."""
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Sports-MCP-Server/1.0'
    }
    
    api_key = os.getenv("BALLDONTLIE_API_KEY")
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    return headers

def get_base_url(league: str) -> str:
    """Get the correct base URL for each league."""
    base_url = "https://api.balldontlie.io"
    
    if league.upper() == "NBA":
        return f"{base_url}/v1"
    else:
        # For MLB, NFL, NHL, EPL - they use /{sport}/v1/ pattern
        return f"{base_url}/{league.lower()}/v1"

@mcp_tool()
async def get_teams(
    league: Literal["NBA", "MLB", "NFL"]
) -> Dict[str, Any]:
    """
    Get a list of teams for the NBA, NFL or MLB.
    
    Args:
        league: The sports league to get teams for (NBA, MLB, or NFL)
    """
    try:
        http_client = await get_http_client()
        headers = get_api_headers()
        
        # Construct API endpoint based on league
        base_url = get_base_url(league)
        endpoint = f"{base_url}/teams"
        
        cache_key = f"teams-{league.lower()}"
        
        async def fetch_data():
            # Wait if we're hitting rate limits
            await rate_limiter.wait_if_needed()
            
            async with http_client.get(endpoint, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Balldontlie API error: {response.status} - {error_text}")
                    return {
                        "status": "error",
                        "error_message": f"Error fetching teams: {response.status} {response.reason}"
                    }
                
                data = await response.json()
                return {
                    "status": "success",
                    "league": league,
                    "total_teams": len(data.get("data", [])),
                    "teams": _format_teams_data(data.get("data", []), league)
                }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in get_teams: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error fetching teams: {str(e)}"
        }

def _format_teams_data(teams_data: List[Dict], league: str) -> str:
    """Format teams data for display."""
    if not teams_data:
        return "No teams found."
    
    formatted_teams = []
    
    for team in teams_data:
        if league == "NBA":
            formatted_team = (
                f"Team ID: {team.get('id', 'N/A')}\n"
                f"Full Name: {team.get('full_name', 'N/A')}\n"
                f"Name: {team.get('name', 'N/A')}\n"
                f"Abbreviation: {team.get('abbreviation', 'N/A')}\n"
                f"City: {team.get('city', 'N/A')}\n"
                f"Conference: {team.get('conference', 'N/A')}\n"
                f"Division: {team.get('division', 'N/A')}"
            )
        elif league == "MLB":
            formatted_team = (
                f"Team ID: {team.get('id', 'N/A')}\n"
                f"Display Name: {team.get('display_name', 'N/A')}\n"
                f"Name: {team.get('name', 'N/A')}\n"
                f"Abbreviation: {team.get('abbreviation', 'N/A')}\n"
                f"Location: {team.get('location', 'N/A')}\n"
                f"League: {team.get('league', 'N/A')}\n"
                f"Division: {team.get('division', 'N/A')}\n"
                f"Slug: {team.get('slug', 'N/A')}"
            )
        else:  # NFL
            formatted_team = (
                f"Team ID: {team.get('id', 'N/A')}\n"
                f"Name: {team.get('name', 'N/A')}\n"
                f"Abbreviation: {team.get('abbreviation', 'N/A')}\n"
                f"Full Name: {team.get('full_name', 'N/A')}\n"
                f"Location: {team.get('location', 'N/A')}\n"
                f"Conference: {team.get('conference', 'N/A')}\n"
                f"Division: {team.get('division', 'N/A')}"
            )
        
        formatted_teams.append(formatted_team)
    
    return "\n-----\n".join(formatted_teams)

@mcp_tool()
async def get_players(
    league: Literal["NBA", "MLB", "NFL"],
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    cursor: Optional[int] = None
) -> Dict[str, Any]:
    """
    Gets a list of players for the NBA, NFL or MLB.
    
    Args:
        league: The sports league to get players for (NBA, MLB, or NFL)
        first_name: The first name of the player to search for (optional)
        last_name: The last name of the player to search for (optional)
        cursor: Cursor for pagination (optional)
    """
    try:
        http_client = await get_http_client()
        headers = get_api_headers()
        
        # Construct API endpoint
        base_url = get_base_url(league)
        endpoint = f"{base_url}/players"
        
        # Build query parameters
        params = {}
        if first_name:
            params['first_name'] = first_name
        if last_name:
            params['last_name'] = last_name
        if cursor:
            params['cursor'] = cursor
        
        # Create cache key
        cache_key = f"players-{league.lower()}-{first_name or ''}-{last_name or ''}-{cursor or 0}"
        
        async def fetch_data():
            # Wait if we're hitting rate limits
            await rate_limiter.wait_if_needed()
            
            async with http_client.get(endpoint, headers=headers, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Balldontlie API error: {response.status} - {error_text}")
                    return {
                        "status": "error",
                        "error_message": f"Error fetching players: {response.status} {response.reason}"
                    }
                
                data = await response.json()
                formatted_text = _format_players_data(data.get("data", []), league)
                
                # Add pagination info if available
                meta = data.get("meta", {})
                if meta.get("next_cursor"):
                    formatted_text += f"\n\nPagination Information:\nnext_cursor: {meta['next_cursor']}"
                
                return {
                    "status": "success",
                    "league": league,
                    "total_players": len(data.get("data", [])),
                    "players": formatted_text,
                    "next_cursor": meta.get("next_cursor")
                }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in get_players: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error fetching players: {str(e)}"
        }

def _format_players_data(players_data: List[Dict], league: str) -> str:
    """Format players data for display."""
    if not players_data:
        return "No players found."
    
    formatted_players = []
    
    for player in players_data:
        team = player.get('team', {})
        
        if league == "NBA":
            formatted_player = (
                f"Player ID: {player.get('id', 'N/A')}\n"
                f"First Name: {player.get('first_name', 'N/A')}\n"
                f"Last Name: {player.get('last_name', 'N/A')}\n"
                f"Position: {player.get('position', 'N/A')}\n"
                f"Height: {player.get('height', 'N/A')}\n"
                f"Weight: {player.get('weight', 'N/A')}\n"
                f"Jersey Number: {player.get('jersey_number', 'N/A')}\n"
                f"College: {player.get('college', 'N/A')}\n"
                f"Country: {player.get('country', 'N/A')}\n"
                f"Draft Year: {player.get('draft_year', 'N/A')}\n"
                f"Draft Round: {player.get('draft_round', 'N/A')}\n"
                f"Draft Number: {player.get('draft_number', 'N/A')}\n"
                f"Team ID: {team.get('id', 'N/A')}\n"
                f"Team Name: {team.get('name', 'N/A')}"
            )
        elif league == "MLB":
            formatted_player = (
                f"Player ID: {player.get('id', 'N/A')}\n"
                f"First Name: {player.get('first_name', 'N/A')}\n"
                f"Last Name: {player.get('last_name', 'N/A')}\n"
                f"Full Name: {player.get('full_name', 'N/A')}\n"
                f"Debut Year: {player.get('debut_year', 'N/A')}\n"
                f"Jersey: {player.get('jersey', 'N/A')}\n"
                f"College: {player.get('college', 'N/A')}\n"
                f"Position: {player.get('position', 'N/A')}\n"
                f"Active: {player.get('active', 'N/A')}\n"
                f"Birth Place: {player.get('birth_place', 'N/A')}\n"
                f"Date of Birth: {player.get('dob', 'N/A')}\n"
                f"Age: {player.get('age', 'N/A')}\n"
                f"Height: {player.get('height', 'N/A')}\n"
                f"Weight: {player.get('weight', 'N/A')}\n"
                f"Draft: {player.get('draft', 'N/A')}\n"
                f"Bats/Throws: {player.get('bats_throws', 'N/A')}\n"
                f"Team ID: {team.get('id', 'N/A')}\n"
                f"Team Name: {team.get('name', 'N/A')}"
            )
        else:  # NFL
            formatted_player = (
                f"ID: {player.get('id', 'N/A')}\n"
                f"First Name: {player.get('first_name', 'N/A')}\n"
                f"Last Name: {player.get('last_name', 'N/A')}\n"
                f"Position: {player.get('position', 'N/A')}\n"
                f"Position Abbreviation: {player.get('position_abbreviation', 'N/A')}\n"
                f"Height: {player.get('height', 'N/A')}\n"
                f"Weight: {player.get('weight', 'N/A')}\n"
                f"Jersey Number: {player.get('jersey_number', 'N/A')}\n"
                f"College: {player.get('college', 'N/A')}\n"
                f"Experience: {player.get('experience', 'N/A')}\n"
                f"Age: {player.get('age', 'N/A')}\n"
                f"Team ID: {team.get('id', 'N/A')}\n"
                f"Team Name: {team.get('name', 'N/A')}\n"
                f"Team Location: {team.get('location', 'N/A')}\n"
                f"Team Abbreviation: {team.get('abbreviation', 'N/A')}\n"
                f"Team Conference: {team.get('conference', 'N/A')}\n"
                f"Team Division: {team.get('division', 'N/A')}"
            )
        
        formatted_players.append(formatted_player)
    
    return "\n-----\n".join(formatted_players)

@mcp_tool()
async def get_games(
    league: Literal["NBA", "MLB", "NFL"],
    dates: Optional[List[str]] = None,
    seasons: Optional[List[int]] = None,
    team_ids: Optional[List[int]] = None,
    cursor: Optional[int] = None
) -> Dict[str, Any]:
    """
    Gets the list of games for the NBA, NFL or MLB.
    
    Args:
        league: The sports league to get games for (NBA, MLB, or NFL)
        dates: Get games for specific dates, format: YYYY-MM-DD (optional)
        seasons: Get games for specific seasons, format: YYYY (optional)
        team_ids: Get games for specific team IDs (optional)
        cursor: Cursor for pagination (optional)
    """
    try:
        http_client = await get_http_client()
        headers = get_api_headers()
        
        # Construct API endpoint
        base_url = get_base_url(league)
        endpoint = f"{base_url}/games"
        
        # Build query parameters
        params = {}
        if dates:
            params['dates[]'] = dates
        if seasons:
            params['seasons[]'] = seasons
        if team_ids:
            params['team_ids[]'] = team_ids
        if cursor:
            params['cursor'] = cursor
        
        # Create cache key
        dates_str = ','.join(dates) if dates else ''
        seasons_str = ','.join(map(str, seasons)) if seasons else ''
        team_ids_str = ','.join(map(str, team_ids)) if team_ids else ''
        cache_key = f"games-{league.lower()}-{dates_str}-{seasons_str}-{team_ids_str}-{cursor or 0}"
        
        async def fetch_data():
            # Wait if we're hitting rate limits
            await rate_limiter.wait_if_needed()
            
            async with http_client.get(endpoint, headers=headers, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Balldontlie API error: {response.status} - {error_text}")
                    return {
                        "status": "error",
                        "error_message": f"Error fetching games: {response.status} {response.reason}"
                    }
                
                data = await response.json()
                formatted_text = _format_games_data(data.get("data", []), league)
                
                # Add pagination info if available
                meta = data.get("meta", {})
                if meta.get("next_cursor"):
                    formatted_text += f"\n\nPagination Information:\nnext_cursor: {meta['next_cursor']}"
                
                return {
                    "status": "success",
                    "league": league,
                    "total_games": len(data.get("data", [])),
                    "games": formatted_text,
                    "next_cursor": meta.get("next_cursor")
                }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in get_games: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error fetching games: {str(e)}"
        }

def _format_games_data(games_data: List[Dict], league: str) -> str:
    """Format games data for display."""
    if not games_data:
        return "No games found."
    
    formatted_games = []
    
    for game in games_data:
        if league == "NBA":
            formatted_game = _format_nba_game(game)
        elif league == "MLB":
            formatted_game = _format_mlb_game(game)
        else:  # NFL
            formatted_game = _format_nfl_game(game)
        
        formatted_games.append(formatted_game)
    
    return "\n\n-----\n\n".join(formatted_games)

def _format_nba_game(game: Dict) -> str:
    """Format NBA game data."""
    home_team = game.get('home_team', {})
    visitor_team = game.get('visitor_team', {})
    
    return (
        f"Game ID: {game.get('id', 'N/A')}\n"
        f"Date: {game.get('date', 'N/A')}\n"
        f"Season: {game.get('season', 'N/A')}\n"
        f"Status: {game.get('status', 'N/A')}\n"
        f"Period: {game.get('period', 'N/A')}\n"
        f"Time: {game.get('time', 'N/A')}\n"
        f"Postseason: {game.get('postseason', 'N/A')}\n"
        f"Score: {home_team.get('full_name', 'N/A')} {game.get('home_team_score', 'N/A')} - {game.get('visitor_team_score', 'N/A')} {visitor_team.get('full_name', 'N/A')}\n"
        f"Home Team: {home_team.get('full_name', 'N/A')} ({home_team.get('abbreviation', 'N/A')})\n"
        f"Visitor Team: {visitor_team.get('full_name', 'N/A')} ({visitor_team.get('abbreviation', 'N/A')})"
    )

def _format_mlb_game(game: Dict) -> str:
    """Format MLB game data."""
    home_team = game.get('home_team', {})
    away_team = game.get('away_team', {})
    home_team_data = game.get('home_team_data', {})
    away_team_data = game.get('away_team_data', {})
    
    # Format inning scores
    home_innings = home_team_data.get('inning_scores', [])
    away_innings = away_team_data.get('inning_scores', [])
    home_innings_str = ', '.join(f"Inning {i+1}: {score}" for i, score in enumerate(home_innings))
    away_innings_str = ', '.join(f"Inning {i+1}: {score}" for i, score in enumerate(away_innings))
    
    return (
        f"Game ID: {game.get('id', 'N/A')}\n"
        f"Date: {game.get('date', 'N/A')}\n"
        f"Season: {game.get('season', 'N/A')}\n"
        f"Postseason: {game.get('postseason', 'N/A')}\n"
        f"Status: {game.get('status', 'N/A')}\n"
        f"Venue: {game.get('venue', 'N/A')}\n"
        f"Attendance: {game.get('attendance', 'N/A')}\n"
        f"\nMatchup: {game.get('home_team_name', 'N/A')} vs {game.get('away_team_name', 'N/A')}\n"
        f"\nHome Team: {home_team.get('display_name', 'N/A')} ({home_team.get('abbreviation', 'N/A')})\n"
        f"  League: {home_team.get('league', 'N/A')}\n"
        f"  Division: {home_team.get('division', 'N/A')}\n"
        f"  Runs: {home_team_data.get('runs', 'N/A')}\n"
        f"  Hits: {home_team_data.get('hits', 'N/A')}\n"
        f"  Errors: {home_team_data.get('errors', 'N/A')}\n"
        f"  Inning Scores: {home_innings_str}\n"
        f"\nAway Team: {away_team.get('display_name', 'N/A')} ({away_team.get('abbreviation', 'N/A')})\n"
        f"  League: {away_team.get('league', 'N/A')}\n"
        f"  Division: {away_team.get('division', 'N/A')}\n"
        f"  Runs: {away_team_data.get('runs', 'N/A')}\n"
        f"  Hits: {away_team_data.get('hits', 'N/A')}\n"
        f"  Errors: {away_team_data.get('errors', 'N/A')}\n"
        f"  Inning Scores: {away_innings_str}\n"
        f"\nFinal Score: {game.get('home_team_name', 'N/A')} {home_team_data.get('runs', 'N/A')} - {away_team_data.get('runs', 'N/A')} {game.get('away_team_name', 'N/A')}"
    )

def _format_nfl_game(game: Dict) -> str:
    """Format NFL game data."""
    home_team = game.get('home_team', {})
    visitor_team = game.get('visitor_team', {})
    home_score = game.get('home_team_score', 0)
    visitor_score = game.get('visitor_team_score', 0)
    
    # Determine winner
    if home_score > visitor_score:
        winner = home_team.get('full_name', 'N/A')
    elif visitor_score > home_score:
        winner = visitor_team.get('full_name', 'N/A')
    else:
        winner = 'Tie'
    
    return (
        f"Game ID: {game.get('id', 'N/A')}\n"
        f"Date: {game.get('date', 'N/A')}\n"
        f"Season: {game.get('season', 'N/A')}\n"
        f"Week: {game.get('week', 'N/A')}\n"
        f"Status: {game.get('status', 'N/A')}\n"
        f"Postseason: {game.get('postseason', 'N/A')}\n"
        f"Venue: {game.get('venue', 'N/A')}\n"
        f"Summary: {game.get('summary', 'N/A')}\n"
        f"\nMatchup: {home_team.get('full_name', 'N/A')} vs {visitor_team.get('full_name', 'N/A')}\n"
        f"\nHome Team: {home_team.get('full_name', 'N/A')} ({home_team.get('abbreviation', 'N/A')})\n"
        f"  Location: {home_team.get('location', 'N/A')}\n"
        f"  Conference: {home_team.get('conference', 'N/A')}\n"
        f"  Division: {home_team.get('division', 'N/A')}\n"
        f"  Score: {home_score}\n"
        f"\nVisitor Team: {visitor_team.get('full_name', 'N/A')} ({visitor_team.get('abbreviation', 'N/A')})\n"
        f"  Location: {visitor_team.get('location', 'N/A')}\n"
        f"  Conference: {visitor_team.get('conference', 'N/A')}\n"
        f"  Division: {visitor_team.get('division', 'N/A')}\n"
        f"  Score: {visitor_score}\n"
        f"\nFinal Score: {home_team.get('full_name', 'N/A')} {home_score} - {visitor_score} {visitor_team.get('full_name', 'N/A')}\n"
        f"Winner: {winner}"
    )

@mcp_tool()
async def get_game(
    league: Literal["NBA", "MLB", "NFL"],
    game_id: int
) -> Dict[str, Any]:
    """
    Get a specific game from one of the following leagues NBA, MLB, NFL.
    
    Args:
        league: The sports league to get the game for (NBA, MLB, or NFL)
        game_id: The id of the game from the get_games tool
    """
    try:
        http_client = await get_http_client()
        headers = get_api_headers()
        
        # Construct API endpoint
        base_url = get_base_url(league)
        endpoint = f"{base_url}/games/{game_id}"
        
        cache_key = f"game-{league.lower()}-{game_id}"
        
        async def fetch_data():
            # Wait if we're hitting rate limits
            await rate_limiter.wait_if_needed()
            
            async with http_client.get(endpoint, headers=headers) as response:
                if response.status == 404:
                    return {
                        "status": "error",
                        "error_message": f"Game ID {game_id} not found"
                    }
                elif response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Balldontlie API error: {response.status} - {error_text}")
                    return {
                        "status": "error",
                        "error_message": f"Error fetching game: {response.status} {response.reason}"
                    }
                
                data = await response.json()
                game_data = data.get("data")
                
                if not game_data:
                    return {
                        "status": "error",
                        "error_message": f"Game ID {game_id} not found"
                    }
                
                if league == "NBA":
                    formatted_text = _format_nba_game(game_data)
                elif league == "MLB":
                    formatted_text = _format_mlb_game(game_data)
                else:  # NFL
                    formatted_text = _format_nfl_game(game_data)
                
                return {
                    "status": "success",
                    "league": league,
                    "game_id": game_id,
                    "game": formatted_text
                }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in get_game: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error fetching game: {str(e)}"
        }

# Server startup and shutdown handlers
async def startup():
    """Initialize the server."""
    logger.info("Sports MCP Server starting up...")

async def shutdown():
    """Clean up resources."""
    logger.info("Sports MCP Server shutting down...")
    await close_http_client()

if __name__ == "__main__":
    import mcp
    mcp_sports.run()
