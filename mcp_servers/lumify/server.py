#!/usr/bin/env uv run
"""Lumify Sports Intelligence MCP server for MCPEval.

Wraps the Lumify REST API (https://lumify.ai) so agent evaluation tasks can
exercise real sports schedules, odds, and explainable bet intelligence.

Requires LUMIFY_API_KEY. Free instant keys (no signup): https://lumify.ai/docs/ai
"""

from __future__ import annotations

import asyncio
import logging
import os
import ssl
import time
from typing import Any, Dict, List, Optional

import aiohttp
from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://lumify.ai"
# Free-tier keys allow ~20 req/min; stay under that with headroom.
RATE_LIMIT_MAX = 15
RATE_LIMIT_WINDOW = 60


class RateLimiter:
    def __init__(self, max_requests: int = RATE_LIMIT_MAX, time_window: int = RATE_LIMIT_WINDOW):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[float] = []
        self.lock = asyncio.Lock()

    async def wait_if_needed(self) -> None:
        async with self.lock:
            now = time.time()
            self.requests = [t for t in self.requests if now - t < self.time_window]
            if len(self.requests) >= self.max_requests:
                wait_time = self.time_window - (now - min(self.requests)) + 1
                if wait_time > 0:
                    logger.info("Rate limit reached. Waiting %.1f seconds...", wait_time)
                    await asyncio.sleep(wait_time)
                    now = time.time()
                    self.requests = [t for t in self.requests if now - t < self.time_window]
            self.requests.append(now)


rate_limiter = RateLimiter()
mcp_lumify = FastMCP("Lumify Sports Intelligence")
mcp_tool = mcp_lumify.tool

_http_client: Optional[aiohttp.ClientSession] = None
_cache: Dict[str, Any] = {}
VERIFY_SSL = os.environ.get("VERIFY_SSL", "true").lower() != "false"
BASE_URL = os.environ.get("LUMIFY_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _api_key() -> Optional[str]:
    key = os.environ.get("LUMIFY_API_KEY", "").strip()
    if key.lower().startswith("bearer "):
        key = key[7:].strip()
    return key or None


async def get_http_client() -> aiohttp.ClientSession:
    global _http_client
    if _http_client is None or _http_client.closed:
        ssl_context = ssl.create_default_context()
        if not VERIFY_SSL:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        _http_client = aiohttp.ClientSession(connector=connector)
    return _http_client


async def close_http_client() -> None:
    global _http_client
    if _http_client and not _http_client.closed:
        await _http_client.close()
        _http_client = None
        await asyncio.sleep(0.25)


def _headers() -> Dict[str, str]:
    key = _api_key()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Lumify-MCPEval-Server/1.0",
    }
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


async def _get_cached_or_fetch(cache_key: str, fetch_func, cache_duration: int = 60):
    cached = _cache.get(cache_key)
    if cached is not None:
        data, ts = cached
        if time.time() - ts < cache_duration:
            return data
    data = await fetch_func()
    _cache[cache_key] = (data, time.time())
    return data


async def _request(method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not _api_key():
        return {
            "status": "error",
            "error_message": (
                "LUMIFY_API_KEY is not set. Get a free instant key (no signup) at "
                "https://lumify.ai/docs/ai and export LUMIFY_API_KEY=lmfy-..."
            ),
        }

    await rate_limiter.wait_if_needed()
    client = await get_http_client()
    url = f"{BASE_URL}{path}"
    clean_params = {k: v for k, v in (params or {}).items() if v is not None and v != ""}

    try:
        async with client.request(method, url, headers=_headers(), params=clean_params) as response:
            text = await response.text()
            if response.status == 401 or response.status == 403:
                return {
                    "status": "error",
                    "error_message": f"Lumify authentication failed ({response.status}). Check LUMIFY_API_KEY.",
                }
            if response.status == 402:
                return {
                    "status": "error",
                    "error_message": "Lumify API credits exhausted (402). Create a new key or top up credits.",
                }
            if response.status == 429:
                return {
                    "status": "error",
                    "error_message": "Lumify rate limit exceeded (429). Retry shortly.",
                }
            if response.status >= 400:
                return {
                    "status": "error",
                    "error_message": f"Lumify API error ({response.status}): {text[:500]}",
                }
            try:
                payload = await response.json(content_type=None)
            except Exception:
                return {
                    "status": "error",
                    "error_message": f"Malformed JSON from Lumify ({response.status}): {text[:300]}",
                }
            if isinstance(payload, dict):
                payload = {"status": "success", **payload}
            else:
                payload = {"status": "success", "data": payload}
            return payload
    except aiohttp.ClientError as exc:
        logger.error("HTTP error calling Lumify %s: %s", path, exc)
        return {"status": "error", "error_message": f"Network error calling Lumify: {exc}"}
    except Exception as exc:
        logger.error("Unexpected error calling Lumify %s: %s", path, exc)
        return {"status": "error", "error_message": f"Unexpected error: {exc}"}


@mcp_tool()
async def list_sports(active_only: bool = True) -> Dict[str, Any]:
    """List sports available in Lumify (NBA, NFL, MLB, NHL, soccer, tennis, golf, MMA, etc.).

    Args:
        active_only: When true, only return currently active sports.
    """
    cache_key = f"sports:{active_only}"

    async def fetch():
        return await _request(
            "GET",
            "/v1/sports",
            {"active_only": str(active_only).lower()},
        )

    return await _get_cached_or_fetch(cache_key, fetch, cache_duration=300)


@mcp_tool()
async def list_teams(
    sport: str,
    league: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 25,
    after_id: Optional[int] = None,
) -> Dict[str, Any]:
    """List teams for a sport, optionally filtered by league or search query.

    Args:
        sport: Sport slug (e.g. nba, nfl, mlb, nhl, soccer).
        league: Optional league slug filter.
        q: Optional free-text search.
        limit: Page size (1-100, default 25).
        after_id: Cursor for the next page from a previous response's next_after_id.
    """
    return await _request(
        "GET",
        "/v1/teams",
        {
            "sport": sport,
            "league": league,
            "q": q,
            "limit": max(1, min(limit, 100)),
            "after_id": after_id,
        },
    )


@mcp_tool()
async def list_players(
    sport: str,
    q: Optional[str] = None,
    limit: int = 25,
    after_id: Optional[int] = None,
) -> Dict[str, Any]:
    """List or search players for a sport.

    Args:
        sport: Sport slug (e.g. nba, nfl, mlb, nhl, tennis).
        q: Optional player name search.
        limit: Page size (1-100, default 25).
        after_id: Cursor for the next page from a previous response's next_after_id.
    """
    return await _request(
        "GET",
        "/v1/players",
        {
            "sport": sport,
            "q": q,
            "limit": max(1, min(limit, 100)),
            "after_id": after_id,
        },
    )


@mcp_tool()
async def list_events(
    sport: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    league: Optional[str] = None,
    status: Optional[str] = None,
    include_scores: bool = True,
    limit: int = 25,
    after_id: Optional[int] = None,
) -> Dict[str, Any]:
    """List sports events (games/matches) for a sport within an optional date window.

    Args:
        sport: Sport slug (e.g. nba, nfl, mlb, nhl, soccer, tennis).
        date_from: Inclusive start datetime (ISO-8601 or YYYY-MM-DD). Max window with date_to is 90 days.
        date_to: Inclusive end datetime (ISO-8601 or YYYY-MM-DD).
        league: Optional league slug filter.
        status: Optional status filter (e.g. scheduled, in_progress, final).
        include_scores: Include participant scores when available (default true).
        limit: Page size (1-100, default 25).
        after_id: Cursor for the next page from a previous response's next_after_id.
    """
    return await _request(
        "GET",
        "/v1/events",
        {
            "sport": sport,
            "from": date_from,
            "to": date_to,
            "league": league,
            "status": status,
            "include_scores": str(include_scores).lower(),
            "limit": max(1, min(limit, 100)),
            "after_id": after_id,
        },
    )


@mcp_tool()
async def get_event(
    event_id: int,
    include_odds: bool = False,
    include_intelligence: bool = False,
    bookmaker: Optional[str] = None,
) -> Dict[str, Any]:
    """Get a single event by ID, optionally embedding current odds and bet intelligence.

    Args:
        event_id: Lumify event ID (from list_events).
        include_odds: When true, include current odds (uses extra API credits when available).
        include_intelligence: When true, include explainable bet intelligence (uses extra credits when available).
        bookmaker: Optional bookmaker filter when including odds/intelligence (default pinnacle).
    """
    params: Dict[str, Any] = {
        "include_odds": str(include_odds).lower(),
        "include_intelligence": str(include_intelligence).lower(),
    }
    if bookmaker:
        params["bookmaker"] = bookmaker
    return await _request("GET", f"/v1/events/{event_id}", params)


@mcp_tool()
async def get_event_odds(event_id: int, bookmaker: Optional[str] = None) -> Dict[str, Any]:
    """Get current betting odds for an event.

    Args:
        event_id: Lumify event ID.
        bookmaker: Bookmaker slug, comma-separated list, or 'all' (default pinnacle).
    """
    return await _request(
        "GET",
        f"/v1/events/{event_id}/odds",
        {"bookmaker": bookmaker},
    )


@mcp_tool()
async def get_event_intelligence(event_id: int, bookmaker: Optional[str] = None) -> Dict[str, Any]:
    """Get explainable bet intelligence / confidence for an event.

    Returns analyst take, match overview, and recommended bets with confidence
    scores and rationales when available for the event.

    Args:
        event_id: Lumify event ID.
        bookmaker: Optional bookmaker context (default pinnacle).
    """
    return await _request(
        "GET",
        f"/v1/events/{event_id}/intelligence",
        {"bookmaker": bookmaker},
    )


if __name__ == "__main__":
    logger.info("Lumify Sports Intelligence MCP Server starting (base_url=%s)", BASE_URL)
    try:
        mcp_lumify.run()
    finally:
        try:
            asyncio.run(close_http_client())
        except RuntimeError:
            pass
