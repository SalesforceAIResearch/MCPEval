# Sports MCP Server

A Model Control Protocol (MCP) server that provides access to sports data from multiple leagues including NBA, MLB, and NFL through the [balldontlie.io](https://www.balldontlie.io/) API.

## Features

- Get teams for NBA, MLB, and NFL
- Search and retrieve player information
- Access game data and schedules
- Get detailed game information by ID
- Built-in rate limiting for free tier usage
- Caching for improved performance

## Getting Your API Key

To use this server, you'll need to obtain an API key from balldontlie.io:

### Step 1: Visit the balldontlie.io Website
1. Go to [https://www.balldontlie.io/](https://www.balldontlie.io/)
2. Click on "Pricing" or "Sign Up" in the navigation menu

### Step 2: Choose Your Plan
- **Free Tier**: 5 requests per minute, perfect for testing and light usage
- **Paid Plans**: Higher rate limits available for production use

### Step 3: Sign Up for an Account
1. Click "Sign Up for Free" or select your preferred plan
2. Fill out the registration form with your email and other required information
3. Verify your email address if required

### Step 4: Access Your API Key
1. Log into your balldontlie.io dashboard
2. Navigate to your account settings or API section
3. Copy your API key - it will look something like: `your-api-key-here`

### Step 5: Set Up Environment Variable
Set the `BALLDONTLIE_API_KEY` environment variable:

```bash
# For Linux/Mac (add to ~/.bashrc or ~/.zshrc for persistence)
export BALLDONTLIE_API_KEY="your-api-key-here"

# For Windows Command Prompt
set BALLDONTLIE_API_KEY=your-api-key-here

# For Windows PowerShell
$env:BALLDONTLIE_API_KEY="your-api-key-here"
```

**Note**: The server will work with limited functionality without an API key, but having one provides:
- Higher rate limits
- Access to premium features
- Better reliability

## Available Functions

### 1. get_teams(league)
Get a list of teams for a specific league.

**Parameters:**
- `league`: "NBA", "MLB", or "NFL"

**Example:** Get all NBA teams

### 2. get_players(league, first_name?, last_name?, cursor?)
Search for players in a specific league.

**Parameters:**
- `league`: "NBA", "MLB", or "NFL"
- `first_name`: (Optional) Player's first name
- `last_name`: (Optional) Player's last name
- `cursor`: (Optional) Pagination cursor

**Example:** Search for players named "LeBron"

### 3. get_games(league, dates?, seasons?, team_ids?, cursor?)
Get games for a specific league with optional filters.

**Parameters:**
- `league`: "NBA", "MLB", or "NFL"
- `dates`: (Optional) List of dates in YYYY-MM-DD format
- `seasons`: (Optional) List of seasons (YYYY format)
- `team_ids`: (Optional) List of team IDs
- `cursor`: (Optional) Pagination cursor

**Example:** Get games for a specific date

### 4. get_game(league, game_id)
Get detailed information about a specific game.

**Parameters:**
- `league`: "NBA", "MLB", or "NFL"
- `game_id`: The ID of the game (from get_games results)

## Rate Limiting

The server includes built-in rate limiting to comply with the balldontlie.io API limits:

- **Free Tier**: 5 requests per minute
- The server automatically waits when rate limits are reached
- Responses are cached to reduce API calls

## Usage with OpenAI Client

From the project root:

```bash
uv run mcp_clients/example_openai_client/client.py --servers mcp_servers/sports/server.py

# With multiple servers
uv run mcp_clients/example_openai_client/client.py --servers @modelcontextprotocol/server-sequential-thinking mcp_servers/sports/server.py^BALLDONTLIE_API_KEY=your-api-key-here

```

## Usage Examples

Once connected, you can ask the client questions like:

- "Show me all NBA teams"
- "Find players named LeBron in the NBA"
- "Get today's NBA games"
- "Show me details for game ID 12345"
- "What MLB teams are there?"
- "Find NFL games from last week"

## Error Handling

The server provides comprehensive error handling:
- Network connectivity issues
- API rate limit exceeded
- Invalid parameters
- Missing game/player/team data

All functions return a structured response with:
- `status`: "success" or "error"
- `error_message`: Description of any errors
- Data fields specific to each function

## SSL Configuration

By default, SSL verification is enabled. You can disable it by setting:
```bash
export VERIFY_SSL=false
```

## Supported Leagues

- **NBA**: National Basketball Association
- **MLB**: Major League Baseball  
- **NFL**: National Football League

Each league has its own specific data format and available information fields.
