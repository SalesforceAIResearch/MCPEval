# Healthcare MCP Server

This server provides access to various healthcare APIs including FDA drug information, PubMed literature search, health topics, clinical trials, and medical terminology lookup.

## Setup

1. Copy the configuration template to create your environment file:
   ```bash
   cp config.template .env
   ```

2. Edit the `.env` file with your API keys:
   - **FDA_API_KEY**: Get from https://open.fda.gov/apis/authentication/
   - **PUBMED_API_KEY**: Get from https://ncbi.nlm.nih.gov/account/

3. Install dependencies:
   ```bash
   pip install -r ../../requirements.txt
   ```

4. Test the server with the example client:
   ```bash
   # From the project root directory
   uv run mcp_clients/example_openai_client/client.py mcp_servers/healthcare/server.py
   ```

## Configuration

The server uses the following environment variables:

- `FDA_API_KEY`: API key for FDA drug database access
- `PUBMED_API_KEY`: API key for PubMed literature search
- `VERIFY_SSL`: Set to `false` to disable SSL verification (default: `true`)

## Available Tools

1. **fda_drug_lookup**: Look up drug information from FDA database
2. **pubmed_search**: Search medical literature in PubMed
3. **health_topics_search**: Get evidence-based health information
4. **clinical_trials_search**: Search for clinical trials
5. **medical_terminology_lookup**: Look up ICD-10 medical codes 