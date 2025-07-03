#!/usr/bin/env uv run
import os
import sys
import json
import asyncio
import logging
import time
import re
from typing import Dict, Any, List, Optional, Union
import urllib.parse
import aiohttp
import ssl

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock mode for testing/task generation
MOCK_MODE = os.environ.get("YOUTUBE_MOCK_MODE", "false").lower() == "true"
if MOCK_MODE:
    logger.info("YouTube server running in MOCK MODE - no real HTTP requests will be made")

# Rate limiting for YouTube API (be respectful)
class RateLimiter:
    def __init__(self, max_requests=10, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """Wait if we're hitting rate limits."""
        if MOCK_MODE:
            return  # Skip rate limiting in mock mode
            
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
rate_limiter = RateLimiter(max_requests=10, time_window=60)

# Initialize the MCP server
mcp_youtube = FastMCP("YouTube Transcript Assistant")
mcp_tool = mcp_youtube.tool

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

# Cache for responses to avoid repeated API calls
_cache = {}

async def get_cached_or_fetch(key, fetch_func, cache_duration=300):  # 5 minutes default
    """Get a cached response or fetch a new one."""
    if key in _cache:
        cached_data, timestamp = _cache[key]
        if time.time() - timestamp < cache_duration:
            return cached_data
    
    result = await fetch_func()
    _cache[key] = (result, time.time())
    return result

def get_api_headers():
    """Get headers for API requests."""
    return {
        'User-Agent': 'YouTube-Transcript-MCP-Server/1.0 (mcp-eval-llm)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

def extract_video_id(url_or_id: str) -> str:
    """
    Extract YouTube video ID from various URL formats or return the ID if already provided.
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - VIDEO_ID (direct ID)
    """
    if not url_or_id:
        raise ValueError("URL or video ID is required")
    
    # If it's already a video ID (11 characters, alphanumeric + underscore + hyphen)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    
    # Extract from various YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    raise ValueError(f"Could not extract video ID from: {url_or_id}")

def get_mock_transcript_data(video_id: str, language: str = "en") -> Dict[str, Any]:
    """Return mock transcript data for testing."""
    return {
        'transcript_url': f'https://mock-transcript-url.com/{video_id}',
        'selected_language': language,
        'available_languages': ['en', 'es', 'fr', 'ko', 'ja'],
        'video_id': video_id
    }

def get_mock_transcript_entries(video_id: str) -> List[Dict[str, Any]]:
    """Return mock transcript entries for testing."""
    return [
        {
            'text': 'Welcome to this sample YouTube video.',
            'start': 0.0,
            'duration': 3.5,
            'end': 3.5
        },
        {
            'text': 'Today we will be discussing artificial intelligence.',
            'start': 3.5,
            'duration': 4.2,
            'end': 7.7
        },
        {
            'text': 'AI has become increasingly important in our daily lives.',
            'start': 7.7,
            'duration': 4.8,
            'end': 12.5
        },
        {
            'text': 'Machine learning algorithms are powering many applications.',
            'start': 12.5,
            'duration': 5.1,
            'end': 17.6
        },
        {
            'text': 'Thank you for watching this educational content.',
            'start': 17.6,
            'duration': 3.9,
            'end': 21.5
        }
    ]

def get_mock_video_metadata(video_id: str) -> Dict[str, Any]:
    """Return mock video metadata for testing."""
    return {
        "title": f"Sample Educational Video {video_id[:8]}",
        "channel": "Educational Channel",
        "description": "This is a sample educational video about technology and artificial intelligence. Learn about the latest developments in AI and machine learning.",
        "view_count": 125000
    }

async def get_youtube_transcript_data(video_id: str, language: str = "en") -> Dict[str, Any]:
    """
    Get transcript data from YouTube's internal API.
    This mimics what youtube-transcript-api does.
    """
    if MOCK_MODE:
        return get_mock_transcript_data(video_id, language)
    
    http_client = await get_http_client()
    headers = get_api_headers()
    
    # Get the video page to extract transcript data
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    async with http_client.get(video_url, headers=headers) as response:
        if response.status != 200:
            raise Exception(f"Failed to fetch video page: {response.status}")
        
        html_content = await response.text()
        
        # Extract ytInitialPlayerResponse JSON from the page
        # This contains the transcript/caption information
        player_response_match = re.search(
            r'var ytInitialPlayerResponse = ({.*?});', html_content
        )
        
        if not player_response_match:
            raise Exception("Could not find player response data")
        
        try:
            player_data = json.loads(player_response_match.group(1))
        except json.JSONDecodeError:
            raise Exception("Could not parse player response data")
        
        # Extract captions data
        captions = player_data.get('captions', {})
        caption_tracks = captions.get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
        
        if not caption_tracks:
            raise Exception("No captions available for this video")
        
        # Find the requested language or fall back to available languages
        selected_track = None
        available_languages = []
        
        for track in caption_tracks:
            lang_code = track.get('languageCode', '')
            available_languages.append(lang_code)
            
            if lang_code == language:
                selected_track = track
                break
        
        # If exact language not found, try to find English or first available
        if not selected_track:
            for track in caption_tracks:
                if track.get('languageCode', '') == 'en':
                    selected_track = track
                    break
            
            if not selected_track and caption_tracks:
                selected_track = caption_tracks[0]
        
        if not selected_track:
            raise Exception(f"No suitable captions found. Available languages: {available_languages}")
        
        # Get the transcript URL
        transcript_url = selected_track.get('baseUrl')
        if not transcript_url:
            raise Exception("Could not find transcript URL")
        
        return {
            'transcript_url': transcript_url,
            'selected_language': selected_track.get('languageCode', 'unknown'),
            'available_languages': available_languages,
            'video_id': video_id
        }

async def fetch_transcript_content(transcript_url: str) -> List[Dict[str, Any]]:
    """Fetch and parse the actual transcript content."""
    if MOCK_MODE:
        # Extract video ID from the mock URL for consistent mock data
        video_id = transcript_url.split('/')[-1] if '/' in transcript_url else 'mock_video'
        return get_mock_transcript_entries(video_id)
    
    http_client = await get_http_client()
    headers = get_api_headers()
    
    async with http_client.get(transcript_url, headers=headers) as response:
        if response.status != 200:
            raise Exception(f"Failed to fetch transcript: {response.status}")
        
        xml_content = await response.text()
        
        # Parse the XML transcript
        # The format is: <text start="0.0" dur="3.5">Transcript text</text>
        transcript_entries = []
        
        # Simple XML parsing for transcript entries
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(xml_content)
            
            for text_elem in root.findall('.//text'):
                start_time = float(text_elem.get('start', 0))
                duration = float(text_elem.get('dur', 0))
                text_content = text_elem.text or ""
                
                # Clean up HTML entities and formatting
                text_content = text_content.replace('&amp;', '&')
                text_content = text_content.replace('&lt;', '<')
                text_content = text_content.replace('&gt;', '>')
                text_content = text_content.replace('&quot;', '"')
                text_content = text_content.replace('&#39;', "'")
                text_content = re.sub(r'<[^>]+>', '', text_content)  # Remove HTML tags
                
                transcript_entries.append({
                    'text': text_content.strip(),
                    'start': start_time,
                    'duration': duration,
                    'end': start_time + duration
                })
            
        except ET.ParseError as e:
            raise Exception(f"Failed to parse transcript XML: {e}")
        
        return transcript_entries

@mcp_tool()
async def get_transcript(
    url: str,
    lang: str = "en",
    include_timestamps: bool = True,
    format_output: str = "detailed"
) -> Dict[str, Any]:
    """
    Extract transcripts from YouTube videos.
    
    Args:
        url: YouTube video URL or video ID
        lang: Language code for transcript (e.g., 'en', 'ko', 'es', 'fr')
        include_timestamps: Whether to include timing information
        format_output: Output format - 'detailed', 'text_only', or 'timed_text'
    """
    try:
        # Extract video ID from URL
        video_id = extract_video_id(url)
        
        cache_key = f"transcript-{video_id}-{lang}-{include_timestamps}-{format_output}"
        
        async def fetch_data():
            await rate_limiter.wait_if_needed()
            
            # Get transcript metadata
            transcript_data = await get_youtube_transcript_data(video_id, lang)
            
            # Fetch actual transcript content
            transcript_entries = await fetch_transcript_content(transcript_data['transcript_url'])
            
            # Format the output based on requested format
            formatted_transcript = format_transcript_output(
                transcript_entries, 
                format_output, 
                include_timestamps
            )
            
            # Get video metadata
            video_metadata = await get_video_metadata(video_id)
            
            return {
                "status": "success",
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "video_metadata": video_metadata,
                "transcript_language": transcript_data['selected_language'],
                "available_languages": transcript_data['available_languages'],
                "transcript_format": format_output,
                "include_timestamps": include_timestamps,
                "transcript_entries_count": len(transcript_entries),
                "transcript": formatted_transcript
            }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in get_transcript: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error getting transcript: {str(e)}",
            "url": url,
            "language": lang
        }

def format_transcript_output(entries: List[Dict[str, Any]], format_type: str, include_timestamps: bool) -> Union[str, List[Dict[str, Any]]]:
    """Format transcript entries based on the requested format."""
    
    if format_type == "text_only":
        # Return just the text content as a single string
        return " ".join(entry['text'] for entry in entries if entry['text'])
    
    elif format_type == "timed_text":
        # Return formatted text with timestamps
        if include_timestamps:
            lines = []
            for entry in entries:
                if entry['text']:
                    timestamp = format_timestamp(entry['start'])
                    lines.append(f"[{timestamp}] {entry['text']}")
            return "\n".join(lines)
        else:
            return " ".join(entry['text'] for entry in entries if entry['text'])
    
    else:  # detailed format
        # Return detailed entries with all metadata
        if include_timestamps:
            return entries
        else:
            return [{"text": entry['text']} for entry in entries if entry['text']]

def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS or HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

async def get_video_metadata(video_id: str) -> Dict[str, Any]:
    """Get basic video metadata from YouTube."""
    if MOCK_MODE:
        return get_mock_video_metadata(video_id)
    
    try:
        http_client = await get_http_client()
        headers = get_api_headers()
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        async with http_client.get(video_url, headers=headers) as response:
            if response.status != 200:
                return {"title": "Unknown", "channel": "Unknown", "error": f"HTTP {response.status}"}
            
            html_content = await response.text()
            
            # Extract title
            title_match = re.search(r'<title>([^<]+)</title>', html_content)
            title = title_match.group(1) if title_match else "Unknown"
            title = title.replace(' - YouTube', '')
            
            # Extract channel name
            channel_match = re.search(r'"ownerChannelName":"([^"]+)"', html_content)
            channel = channel_match.group(1) if channel_match else "Unknown"
            
            # Extract description (first part)
            desc_match = re.search(r'"shortDescription":"([^"]+)"', html_content)
            description = desc_match.group(1) if desc_match else ""
            
            # Extract view count
            views_match = re.search(r'"viewCount":"(\d+)"', html_content)
            view_count = int(views_match.group(1)) if views_match else None
            
            return {
                "title": title,
                "channel": channel,
                "description": description[:200] + "..." if len(description) > 200 else description,
                "view_count": view_count
            }
            
    except Exception as e:
        logger.error(f"Error getting video metadata: {e}")
        return {"title": "Unknown", "channel": "Unknown", "error": str(e)}

@mcp_tool()
async def get_available_languages(
    url: str
) -> Dict[str, Any]:
    """
    Get available transcript languages for a YouTube video.
    
    Args:
        url: YouTube video URL or video ID
    """
    try:
        video_id = extract_video_id(url)
        
        cache_key = f"languages-{video_id}"
        
        async def fetch_data():
            await rate_limiter.wait_if_needed()
            
            # Get transcript metadata to find available languages
            transcript_data = await get_youtube_transcript_data(video_id, "en")  # Language doesn't matter for this call
            
            # Get video metadata
            video_metadata = await get_video_metadata(video_id)
            
            return {
                "status": "success",
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "video_metadata": video_metadata,
                "available_languages": transcript_data['available_languages'],
                "language_count": len(transcript_data['available_languages'])
            }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in get_available_languages: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error getting available languages: {str(e)}",
            "url": url
        }

@mcp_tool()
async def search_transcript(
    url: str,
    search_term: str,
    lang: str = "en",
    context_lines: int = 2
) -> Dict[str, Any]:
    """
    Search for specific terms within a YouTube video transcript.
    
    Args:
        url: YouTube video URL or video ID
        search_term: Term to search for in the transcript
        lang: Language code for transcript (e.g., 'en', 'ko', 'es', 'fr')
        context_lines: Number of lines before and after each match to include
    """
    try:
        video_id = extract_video_id(url)
        
        cache_key = f"search-{video_id}-{lang}-{hash(search_term)}-{context_lines}"
        
        async def fetch_data():
            await rate_limiter.wait_if_needed()
            
            # Get transcript data
            transcript_data = await get_youtube_transcript_data(video_id, lang)
            transcript_entries = await fetch_transcript_content(transcript_data['transcript_url'])
            
            # Search for the term
            matches = []
            search_term_lower = search_term.lower()
            
            for i, entry in enumerate(transcript_entries):
                if search_term_lower in entry['text'].lower():
                    # Get context around the match
                    start_idx = max(0, i - context_lines)
                    end_idx = min(len(transcript_entries), i + context_lines + 1)
                    
                    context_entries = transcript_entries[start_idx:end_idx]
                    
                    match_info = {
                        "match_index": i,
                        "timestamp": format_timestamp(entry['start']),
                        "timestamp_seconds": entry['start'],
                        "matched_text": entry['text'],
                        "context": context_entries,
                        "context_text": " ".join(e['text'] for e in context_entries)
                    }
                    matches.append(match_info)
            
            # Get video metadata
            video_metadata = await get_video_metadata(video_id)
            
            return {
                "status": "success",
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "video_metadata": video_metadata,
                "search_term": search_term,
                "transcript_language": transcript_data['selected_language'],
                "matches_found": len(matches),
                "context_lines": context_lines,
                "matches": matches
            }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in search_transcript: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error searching transcript: {str(e)}",
            "url": url,
            "search_term": search_term,
            "language": lang
        }

@mcp_tool()
async def get_transcript_summary(
    url: str,
    lang: str = "en",
    max_length: int = 500
) -> Dict[str, Any]:
    """
    Get a summary of the YouTube video transcript.
    
    Args:
        url: YouTube video URL or video ID
        lang: Language code for transcript (e.g., 'en', 'ko', 'es', 'fr')
        max_length: Maximum length of the summary in characters
    """
    try:
        video_id = extract_video_id(url)
        
        cache_key = f"summary-{video_id}-{lang}-{max_length}"
        
        async def fetch_data():
            await rate_limiter.wait_if_needed()
            
            # Get transcript data
            transcript_data = await get_youtube_transcript_data(video_id, lang)
            transcript_entries = await fetch_transcript_content(transcript_data['transcript_url'])
            
            # Create full text
            full_text = " ".join(entry['text'] for entry in transcript_entries if entry['text'])
            
            # Simple summarization: take first part, middle part, and end part
            text_length = len(full_text)
            if text_length <= max_length:
                summary = full_text
            else:
                # Take portions from beginning, middle, and end
                part_length = max_length // 3
                
                beginning = full_text[:part_length]
                middle_start = text_length // 2 - part_length // 2
                middle = full_text[middle_start:middle_start + part_length]
                end = full_text[-part_length:]
                
                summary = f"{beginning}... {middle}... {end}"
            
            # Get video metadata
            video_metadata = await get_video_metadata(video_id)
            
            # Calculate transcript statistics
            total_duration = transcript_entries[-1]['end'] if transcript_entries else 0
            word_count = len(full_text.split())
            
            return {
                "status": "success",
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "video_metadata": video_metadata,
                "transcript_language": transcript_data['selected_language'],
                "summary": summary,
                "summary_length": len(summary),
                "original_length": text_length,
                "total_duration_seconds": total_duration,
                "total_duration_formatted": format_timestamp(total_duration),
                "word_count": word_count,
                "transcript_entries_count": len(transcript_entries)
            }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in get_transcript_summary: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error getting transcript summary: {str(e)}",
            "url": url,
            "language": lang
        }

# Startup and cleanup functions
async def startup():
    """Initialize the server."""
    logger.info("YouTube Transcript MCP Server starting up...")

async def shutdown():
    """Clean up resources."""
    logger.info("YouTube Transcript MCP Server shutting down...")
    await close_http_client()

if __name__ == "__main__":
    import uvloop
    import sys
    
    # Use uvloop for better performance if available
    try:
        uvloop.install()
    except ImportError:
        pass
    
    # Run the server
    mcp_youtube.run()
