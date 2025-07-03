# server.py
from mcp.server.fastmcp import FastMCP

# Create a basic MCP server
mcp = FastMCP("Demo")

# Adding MCP tools
@mcp.tool()
def IdentifyRecordByName(recordName: str, objectApiName: str):
    """Searches for Salesforce CRM records by name and returns a list of matching Salesforce CRM record IDs."""
    return f"IdentifyRecordByName({recordName}, {objectApiName})"

@mcp.tool()
def AnswerQuestionsWithKnowledge(query: str):
    """Answers questions about company policies and procedures, troubleshooting steps, or product information. For example: “What is your return policy?” “How do I fix an issue?” or “What features does a product have?"""
    return f"AnswerQuestionsWithKnowledge({query})"

@mcp.tool()
def QueryRecordsWithAggregate(query: str):
    """Answers aggregation questions (such as count, sum, max, min, or average) about Salesforce CRM data based on the user input and specific conditions, such as field values. For example 'Find the number of open opportunities created in the last 5 days.'"""
    return f"QueryRecordsWithAggregate({query})"

@mcp.tool()
def SummarizeRecord(recordId: str):
    """Summarizes a single Salesforce CRM record. You must call the action /EmployeeCopilot__SummarizeRecord only if the user explicitly asks for a summary (e.g: 'Summary', 'Recap', 'Highlights'). This action should be called only when there isn't a more specific summarization action."""
    return f"SummarizeRecord({recordId})"

@mcp.tool()
def DraftOrReviseEmail(recordId: str, userInput: str, latestEmailDraft: str):
    """Creates an email draft or revises the latest generated email based on user input."""
    return f"DraftOrReviseEmail({recordId}, {userInput}, {latestEmailDraft})"

@mcp.tool()
def IdentifyObjectByName(objectName: str):
    """Finds the Salesforce object API name by extracting an object name from the user input."""
    return f"IdentifyObjectByName({objectName})"

@mcp.tool()
def QueryRecords(query: str):
    """Finds and retrieves Salesforce CRM records based on user input and specific conditions, such as field values. This action automatically identifies the correct records and object type. e.g. 'Find all open opportunities created in the last 5 days sorted by created date.'"""
    return f"QueryRecords({query})"

@mcp.tool()
def show(caption: str, refs: str):
    """Displays the function results assigned to each of the `refs` to the user. Always use this to show function results, never summarize them."""
    return f"show({caption}, {refs})"

@mcp.tool()
def GetActivitiesTimeline(recordId: str, activityTypes: list):
    """Retrieve a timeline of all CRM activities associated with one record, including past and future activities."""
    return f"GetActivitiesTimeline({recordId}, {activityTypes})"

@mcp.tool()
def GetRecordDetails(recordId: str):
    """Generates a text blob containing record details, including object fields and values and records from related lists."""
    return f"GetRecordDetails({recordId})"

@mcp.tool()
def userSelect(caption: str, optionRef: int):
    """Generates a text blob containing record details, including object fields and values and records from related lists."""
    return f"userSelect({caption}, {optionRef})"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')