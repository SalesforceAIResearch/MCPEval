# National Parks MCP Server

MCP Server for the National Park Service (NPS) API, providing real-time information about U.S. National Parks.

## Installation

Install the server using npm:

```bash
# Install and run directly with npx (recommended)
npx -y mcp-server-nationalparks

# Or install globally
npm install -g mcp-server-nationalparks
```

## Usage with OpenAI Client

From the project root:

```bash
# With NPS API key (required)
uv run mcp_clients/example_openai_client/client.py --servers mcp-server-nationalparks^NPS_API_KEY=your-api-key-here

# With multiple servers
uv run mcp_clients/example_openai_client/client.py --servers @modelcontextprotocol/server-sequential-thinking mcp-server-nationalparks^NPS_API_KEY=your-api-key-here

# Combined example
uv run mcp_clients/example_openai_client/client.py --servers @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb mcp-server-nationalparks^NPS_API_KEY=your-api-key-here
```

## API Key Required

Get a free API key from the [National Park Service Developer Portal](https://www.nps.gov/subjects/developer/api-documentation.htm).

## Tools

### `findParks`
Search for national parks based on various criteria.

**Optional:**
- `stateCode` (string) - Filter by state code (e.g., "CA", "CA,OR,WA")
- `q` (string) - Search term for park name or description
- `limit` (number) - Maximum results (default: 10, max: 50)
- `start` (number) - Start position for pagination
- `activities` (string) - Filter by activities (e.g., "hiking,camping")

### `getParkDetails`
Get comprehensive information about a specific national park.

**Required:**
- `parkCode` (string) - Park code (e.g., "yose" for Yosemite)

### `getAlerts`
Get current alerts for national parks including closures and hazards.

**Optional:**
- `parkCode` (string) - Filter by park code (e.g., "yose,grca")
- `limit` (number) - Maximum results (default: 10, max: 50)
- `start` (number) - Start position for pagination
- `q` (string) - Search term for alerts

### `getVisitorCenters`
Get information about visitor centers and operating hours.

**Optional:**
- `parkCode` (string) - Filter by park code
- `limit` (number) - Maximum results (default: 10, max: 50)
- `start` (number) - Start position for pagination
- `q` (string) - Search term for visitor centers

### `getCampgrounds`
Get information about available campgrounds and amenities.

**Optional:**
- `parkCode` (string) - Filter by park code
- `limit` (number) - Maximum results (default: 10, max: 50)
- `start` (number) - Start position for pagination
- `q` (string) - Search term for campgrounds

### `getEvents`
Find upcoming events at parks.

**Optional:**
- `parkCode` (string) - Filter by park code
- `limit` (number) - Maximum results (default: 10, max: 50)
- `start` (number) - Start position for pagination
- `dateStart` (string) - Start date (YYYY-MM-DD)
- `dateEnd` (string) - End date (YYYY-MM-DD)
- `q` (string) - Search term for events

## Common Park Codes

| Park | Code |
|------|------|
| Yosemite | yose |
| Grand Canyon | grca |
| Yellowstone | yell |
| Zion | zion |
| Great Smoky Mountains | grsm |
| Acadia | acad |
| Olympic | olym |
| Rocky Mountain | romo |

## Reference

This server is from the [mcp-server-nationalparks](https://github.com/kyrietangsheng/mcp-server-nationalparks) repository. 