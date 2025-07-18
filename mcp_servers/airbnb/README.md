# Airbnb MCP Server

MCP Server for searching Airbnb listings and getting detailed property information.

## Installation

Install the server using npm:

```bash
# Install and run directly with npx (recommended)
npx -y @openbnb/mcp-server-airbnb

# Or install globally
npm install -g @openbnb/mcp-server-airbnb
```

## Usage with OpenAI Client

From the project root:

```bash
# Basic usage
uv run mcp_clients/example_openai_client/client.py --servers @openbnb/mcp-server-airbnb

# With multiple servers
uv run mcp_clients/example_openai_client/client.py --servers @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb

# With explicit arguments
uv run mcp_clients/example_openai_client/client.py --servers @openbnb/mcp-server-airbnb:--ignore-robots-txt
```

## Tools

### `airbnb_search`
Search for Airbnb listings.

**Required:**
- `location` (string) - Location to search

**Optional:**
- `checkin` (string, YYYY-MM-DD) - Check-in date
- `checkout` (string, YYYY-MM-DD) - Check-out date
- `adults` (number) - Number of adults
- `children` (number) - Number of children
- `pets` (number) - Number of pets
- `minPrice` (number) - Minimum price
- `maxPrice` (number) - Maximum price

### `airbnb_listing_details`
Get detailed information about a specific listing.

**Required:**
- `id` (string) - Airbnb listing ID

**Optional:**
- `checkin` (string, YYYY-MM-DD) - Check-in date
- `checkout` (string, YYYY-MM-DD) - Check-out date
- `adults` (number) - Number of adults
- `children` (number) - Number of children
- `pets` (number) - Number of pets

## Reference

This server is from the [@openbnb/mcp-server-airbnb](https://github.com/openbnb-org/mcp-server-airbnb) repository. 