#!/usr/bin/env uv run
import os
import sys
import json
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Literal, Union
import urllib.parse
import aiohttp
import ssl

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Rate limiting for Open Library API
class RateLimiter:
    def __init__(self, max_requests=10, time_window=60):
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
rate_limiter = RateLimiter(max_requests=10, time_window=60)

# Initialize the MCP server
mcp_book = FastMCP("Open Library Book Assistant")
mcp_tool = mcp_book.tool

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
        'Content-Type': 'application/json',
        'User-Agent': 'Book-MCP-Server/1.0 (mcp-eval-llm)'
    }

@mcp_tool()
async def search_books_by_title(
    title: str,
    limit: Optional[int] = 10,
    offset: Optional[int] = 0,
    sort: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for books by title using the Open Library Search API.
    
    Args:
        title: The title of the book to search for
        limit: Maximum number of results to return (default: 10, max: 100)
        offset: Number of results to skip for pagination (default: 0)
        sort: Sort order (new, old, random, etc.)
    """
    try:
        http_client = await get_http_client()
        headers = get_api_headers()
        
        # Construct search parameters
        params = {
            'title': title,
            'limit': min(limit or 10, 100),  # Cap at 100
            'offset': offset or 0
        }
        
        if sort:
            params['sort'] = sort
        
        # Build URL
        base_url = "https://openlibrary.org/search.json"
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        cache_key = f"search-books-{title}-{limit}-{offset}-{sort}"
        
        async def fetch_data():
            await rate_limiter.wait_if_needed()
            
            async with http_client.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Open Library API error: {response.status} - {error_text}")
                    return {
                        "status": "error",
                        "error_message": f"Error searching books: {response.status} {response.reason}"
                    }
                
                data = await response.json()
                books = []
                
                for doc in data.get("docs", []):
                    book = {
                        "title": doc.get("title", "Unknown Title"),
                        "authors": doc.get("author_name", []),
                        "first_publish_year": doc.get("first_publish_year"),
                        "open_library_work_key": doc.get("key"),
                        "edition_count": doc.get("edition_count", 0),
                        "isbn": doc.get("isbn", []),
                        "publisher": doc.get("publisher", []),
                        "language": doc.get("language", []),
                        "subject": doc.get("subject", [])[:10],  # Limit subjects
                        "cover_id": doc.get("cover_i"),
                        "cover_url": f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-M.jpg" if doc.get("cover_i") else None,
                        "has_fulltext": doc.get("has_fulltext", False),
                        "public_scan": doc.get("public_scan_b", False)
                    }
                    books.append(book)
                
                return {
                    "status": "success",
                    "query": title,
                    "total_found": data.get("num_found", 0),
                    "start": data.get("start", 0),
                    "returned_count": len(books),
                    "books": books
                }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in search_books_by_title: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error searching books: {str(e)}"
        }

@mcp_tool()
async def search_authors_by_name(
    name: str,
    limit: Optional[int] = 10,
    offset: Optional[int] = 0
) -> Dict[str, Any]:
    """
    Search for authors by name using the Open Library Authors Search API.
    
    Args:
        name: The name of the author to search for
        limit: Maximum number of results to return (default: 10, max: 100)
        offset: Number of results to skip for pagination (default: 0)
    """
    try:
        http_client = await get_http_client()
        headers = get_api_headers()
        
        # Construct search parameters
        params = {
            'q': name,
            'limit': min(limit or 10, 100),  # Cap at 100
            'offset': offset or 0
        }
        
        # Build URL
        base_url = "https://openlibrary.org/search/authors.json"
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        cache_key = f"search-authors-{name}-{limit}-{offset}"
        
        async def fetch_data():
            await rate_limiter.wait_if_needed()
            
            async with http_client.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Open Library API error: {response.status} - {error_text}")
                    return {
                        "status": "error",
                        "error_message": f"Error searching authors: {response.status} {response.reason}"
                    }
                
                data = await response.json()
                authors = []
                
                for doc in data.get("docs", []):
                    author = {
                        "key": doc.get("key"),
                        "name": doc.get("name", "Unknown Author"),
                        "alternate_names": doc.get("alternate_names", []),
                        "birth_date": doc.get("birth_date"),
                        "death_date": doc.get("death_date"),
                        "top_work": doc.get("top_work"),
                        "work_count": doc.get("work_count", 0),
                        "top_subjects": doc.get("top_subjects", [])[:10],  # Limit subjects
                        "photo_url": f"https://covers.openlibrary.org/a/olid/{doc.get('key')}-M.jpg" if doc.get("key") else None
                    }
                    authors.append(author)
                
                return {
                    "status": "success",
                    "query": name,
                    "total_found": data.get("numFound", 0),
                    "start": data.get("start", 0),
                    "returned_count": len(authors),
                    "authors": authors
                }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in search_authors_by_name: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error searching authors: {str(e)}"
        }

@mcp_tool()
async def get_author_details(
    author_key: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific author using their Open Library key.
    
    Args:
        author_key: The Open Library author key (e.g., "OL26320A")
    """
    try:
        http_client = await get_http_client()
        headers = get_api_headers()
        
        # Clean the author key (remove /authors/ prefix if present)
        clean_key = author_key.replace("/authors/", "").replace("OL", "").replace("A", "")
        formatted_key = f"OL{clean_key}A"
        
        # Build URL
        url = f"https://openlibrary.org/authors/{formatted_key}.json"
        
        cache_key = f"author-details-{formatted_key}"
        
        async def fetch_data():
            await rate_limiter.wait_if_needed()
            
            async with http_client.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Open Library API error: {response.status} - {error_text}")
                    return {
                        "status": "error",
                        "error_message": f"Error fetching author details: {response.status} {response.reason}"
                    }
                
                data = await response.json()
                
                # Extract bio text if it's a complex object
                bio = data.get("bio")
                if isinstance(bio, dict):
                    bio = bio.get("value", str(bio))
                elif isinstance(bio, list) and bio:
                    bio = bio[0].get("value", str(bio[0])) if isinstance(bio[0], dict) else str(bio[0])
                
                author_details = {
                    "name": data.get("name", "Unknown Author"),
                    "personal_name": data.get("personal_name"),
                    "birth_date": data.get("birth_date"),
                    "death_date": data.get("death_date"),
                    "bio": bio,
                    "alternate_names": data.get("alternate_names", []),
                    "photos": data.get("photos", []),
                    "key": data.get("key"),
                    "remote_ids": data.get("remote_ids", {}),
                    "links": data.get("links", []),
                    "photo_url": f"https://covers.openlibrary.org/a/olid/{formatted_key}-L.jpg",
                    "revision": data.get("revision"),
                    "last_modified": data.get("last_modified")
                }
                
                return {
                    "status": "success",
                    "author_key": formatted_key,
                    "author": author_details
                }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in get_author_details: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error fetching author details: {str(e)}"
        }

@mcp_tool()
async def get_author_works(
    author_key: str,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0
) -> Dict[str, Any]:
    """
    Get works by a specific author using their Open Library key.
    
    Args:
        author_key: The Open Library author key (e.g., "OL26320A")
        limit: Maximum number of works to return (default: 50, max: 1000)
        offset: Number of works to skip for pagination (default: 0)
    """
    try:
        http_client = await get_http_client()
        headers = get_api_headers()
        
        # Clean the author key
        clean_key = author_key.replace("/authors/", "").replace("OL", "").replace("A", "")
        formatted_key = f"OL{clean_key}A"
        
        # Construct parameters
        params = {
            'limit': min(limit or 50, 1000),  # Cap at 1000
            'offset': offset or 0
        }
        
        # Build URL
        base_url = f"https://openlibrary.org/authors/{formatted_key}/works.json"
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        cache_key = f"author-works-{formatted_key}-{limit}-{offset}"
        
        async def fetch_data():
            await rate_limiter.wait_if_needed()
            
            async with http_client.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Open Library API error: {response.status} - {error_text}")
                    return {
                        "status": "error",
                        "error_message": f"Error fetching author works: {response.status} {response.reason}"
                    }
                
                data = await response.json()
                works = []
                
                for entry in data.get("entries", []):
                    work = {
                        "title": entry.get("title", "Unknown Title"),
                        "key": entry.get("key"),
                        "authors": [{"key": author.get("author", {}).get("key"), "name": author.get("author", {}).get("name")} 
                                  for author in entry.get("authors", [])],
                        "first_publish_date": entry.get("first_publish_date"),
                        "subjects": entry.get("subjects", [])[:10],  # Limit subjects
                        "covers": entry.get("covers", []),
                        "cover_url": f"https://covers.openlibrary.org/b/id/{entry.get('covers', [None])[0]}-M.jpg" if entry.get("covers") else None
                    }
                    works.append(work)
                
                return {
                    "status": "success",
                    "author_key": formatted_key,
                    "total_works": data.get("size", len(works)),
                    "returned_count": len(works),
                    "works": works
                }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in get_author_works: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error fetching author works: {str(e)}"
        }

@mcp_tool()
async def get_book_by_isbn(
    isbn: str
) -> Dict[str, Any]:
    """
    Get detailed book information using ISBN.
    
    Args:
        isbn: The ISBN of the book (can be ISBN-10 or ISBN-13)
    """
    try:
        http_client = await get_http_client()
        headers = get_api_headers()
        
        # Clean ISBN (remove hyphens and spaces)
        clean_isbn = isbn.replace("-", "").replace(" ", "")
        
        # Build URL
        url = f"https://openlibrary.org/isbn/{clean_isbn}.json"
        
        cache_key = f"book-isbn-{clean_isbn}"
        
        async def fetch_data():
            await rate_limiter.wait_if_needed()
            
            async with http_client.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Open Library API error: {response.status} - {error_text}")
                    return {
                        "status": "error",
                        "error_message": f"Error fetching book by ISBN: {response.status} {response.reason}"
                    }
                
                data = await response.json()
                
                # Extract description if it's a complex object
                description = data.get("description")
                if isinstance(description, dict):
                    description = description.get("value", str(description))
                elif isinstance(description, list) and description:
                    description = description[0].get("value", str(description[0])) if isinstance(description[0], dict) else str(description[0])
                
                book_details = {
                    "title": data.get("title", "Unknown Title"),
                    "authors": [{"key": author.get("key"), "name": author.get("name")} 
                              for author in data.get("authors", [])],
                    "publishers": data.get("publishers", []),
                    "publish_date": data.get("publish_date"),
                    "number_of_pages": data.get("number_of_pages"),
                    "isbn_13": data.get("isbn_13", []),
                    "isbn_10": data.get("isbn_10", []),
                    "oclc": data.get("oclc", []),
                    "lccn": data.get("lccn", []),
                    "key": data.get("key"),
                    "works": [{"key": work.get("key")} for work in data.get("works", [])],
                    "covers": data.get("covers", []),
                    "cover_url": f"https://covers.openlibrary.org/b/id/{data.get('covers', [None])[0]}-M.jpg" if data.get("covers") else None,
                    "subjects": data.get("subjects", []),
                    "description": description,
                    "physical_format": data.get("physical_format"),
                    "weight": data.get("weight"),
                    "revision": data.get("revision"),
                    "last_modified": data.get("last_modified")
                }
                
                return {
                    "status": "success",
                    "isbn": clean_isbn,
                    "book": book_details
                }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in get_book_by_isbn: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error fetching book by ISBN: {str(e)}"
        }

@mcp_tool()
async def get_book_cover_url(
    identifier_type: Literal["isbn", "oclc", "lccn", "olid", "id"],
    identifier_value: str,
    size: Literal["S", "M", "L"] = "L"
) -> Dict[str, Any]:
    """
    Get the cover image URL for a book using various identifiers.
    
    Args:
        identifier_type: Type of identifier (isbn, oclc, lccn, olid, id)
        identifier_value: The identifier value
        size: Cover size - S (small), M (medium), L (large)
    """
    try:
        # Clean identifier value
        clean_value = identifier_value.replace("-", "").replace(" ", "")
        
        # Map identifier types to URL format
        type_mapping = {
            "isbn": "isbn",
            "oclc": "oclc", 
            "lccn": "lccn",
            "olid": "olid",
            "id": "id"
        }
        
        if identifier_type not in type_mapping:
            return {
                "status": "error",
                "error_message": f"Invalid identifier type: {identifier_type}. Must be one of: {', '.join(type_mapping.keys())}"
            }
        
        # Build cover URL
        url_type = type_mapping[identifier_type]
        cover_url = f"https://covers.openlibrary.org/b/{url_type}/{clean_value}-{size}.jpg"
        
        return {
            "status": "success",
            "identifier_type": identifier_type,
            "identifier_value": clean_value,
            "size": size,
            "cover_url": cover_url
        }
        
    except Exception as e:
        logger.error(f"Error in get_book_cover_url: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error generating cover URL: {str(e)}"
        }

@mcp_tool()
async def get_author_photo_url(
    author_key: str,
    size: Literal["S", "M", "L"] = "L"
) -> Dict[str, Any]:
    """
    Get the photo URL for an author using their Open Library ID.
    
    Args:
        author_key: The Open Library author key (e.g., "OL26320A")
        size: Photo size - S (small), M (medium), L (large)
    """
    try:
        # Clean the author key
        clean_key = author_key.replace("/authors/", "").replace("OL", "").replace("A", "")
        formatted_key = f"OL{clean_key}A"
        
        # Build photo URL
        photo_url = f"https://covers.openlibrary.org/a/olid/{formatted_key}-{size}.jpg"
        
        return {
            "status": "success",
            "author_key": formatted_key,
            "size": size,
            "photo_url": photo_url
        }
        
    except Exception as e:
        logger.error(f"Error in get_author_photo_url: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error generating author photo URL: {str(e)}"
        }

@mcp_tool()
async def search_books_advanced(
    query: Optional[str] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    subject: Optional[str] = None,
    publisher: Optional[str] = None,
    language: Optional[str] = None,
    first_publish_year: Optional[int] = None,
    limit: Optional[int] = 10,
    offset: Optional[int] = 0,
    sort: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform advanced book search with multiple criteria.
    
    Args:
        query: General search query
        title: Search by title
        author: Search by author name
        subject: Search by subject
        publisher: Search by publisher
        language: Search by language (e.g., 'eng', 'fre')
        first_publish_year: Search by first publication year
        limit: Maximum number of results to return (default: 10, max: 100)
        offset: Number of results to skip for pagination (default: 0)
        sort: Sort order (new, old, random, etc.)
    """
    try:
        http_client = await get_http_client()
        headers = get_api_headers()
        
        # Build search parameters
        params = {
            'limit': min(limit or 10, 100),
            'offset': offset or 0
        }
        
        # Add search criteria
        if query:
            params['q'] = query
        if title:
            params['title'] = title
        if author:
            params['author'] = author
        if subject:
            params['subject'] = subject
        if publisher:
            params['publisher'] = publisher
        if language:
            params['language'] = language
        if first_publish_year:
            params['first_publish_year'] = first_publish_year
        if sort:
            params['sort'] = sort
        
        # If no specific search criteria provided, use general query
        if not any([query, title, author, subject, publisher, language, first_publish_year]):
            return {
                "status": "error",
                "error_message": "At least one search criterion must be provided"
            }
        
        # Build URL
        base_url = "https://openlibrary.org/search.json"
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        # Create cache key from parameters
        cache_key = f"search-advanced-{hash(str(sorted(params.items())))}"
        
        async def fetch_data():
            await rate_limiter.wait_if_needed()
            
            async with http_client.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Open Library API error: {response.status} - {error_text}")
                    return {
                        "status": "error",
                        "error_message": f"Error performing advanced search: {response.status} {response.reason}"
                    }
                
                data = await response.json()
                books = []
                
                for doc in data.get("docs", []):
                    book = {
                        "title": doc.get("title", "Unknown Title"),
                        "authors": doc.get("author_name", []),
                        "first_publish_year": doc.get("first_publish_year"),
                        "open_library_work_key": doc.get("key"),
                        "edition_count": doc.get("edition_count", 0),
                        "isbn": doc.get("isbn", [])[:5],  # Limit ISBNs
                        "publisher": doc.get("publisher", [])[:5],  # Limit publishers
                        "language": doc.get("language", []),
                        "subject": doc.get("subject", [])[:10],  # Limit subjects
                        "cover_id": doc.get("cover_i"),
                        "cover_url": f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-M.jpg" if doc.get("cover_i") else None,
                        "has_fulltext": doc.get("has_fulltext", False),
                        "public_scan": doc.get("public_scan_b", False),
                        "ratings_average": doc.get("ratings_average"),
                        "ratings_count": doc.get("ratings_count")
                    }
                    books.append(book)
                
                return {
                    "status": "success",
                    "search_criteria": {k: v for k, v in params.items() if k not in ['limit', 'offset']},
                    "total_found": data.get("num_found", 0),
                    "start": data.get("start", 0),
                    "returned_count": len(books),
                    "books": books
                }
        
        return await get_cached_or_fetch(cache_key, fetch_data)
        
    except Exception as e:
        logger.error(f"Error in search_books_advanced: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error performing advanced search: {str(e)}"
        }

# Startup and cleanup functions
async def startup():
    """Initialize the server."""
    logger.info("Book MCP Server starting up...")

async def shutdown():
    """Clean up resources."""
    logger.info("Book MCP Server shutting down...")
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
    mcp_book.run()
