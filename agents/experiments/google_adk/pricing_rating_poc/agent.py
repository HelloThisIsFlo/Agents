from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext

from .pricing_team import pricing_team_agent, isin_to_cusip, get_current_date, GPT4O_MODEL


##################################################################################################################################################
############################################################ Rating Agent Tools #################################################################
##################################################################################################################################################

def get_security_ratings(cusip: str, date: str, tool_context: ToolContext) -> str:
    """
    Returns rating information for a security from multiple rating agencies.
    Also updates the state with the requested rating date.
    
    Args:
        cusip (str): The CUSIP identifier for the security.
        date (str): The date in YYYY-MM-DD format.
        
    Returns:
        str: JSON string containing rating information from multiple agencies.
    """
    # Best Practice: Log tool execution for easier debugging
    print(f"--- Tool: get_security_ratings called for CUSIP: {cusip}, Date: {date} ---")
    
    import json
    import random
    
    # Update the state with the new rating date
    if cusip not in tool_context.state:
        print(f"Initializing state for CUSIP: {cusip}")
        tool_context.state[cusip] = {"price_dates": set(), "rating_dates": set()}
    
    print(f"Adding rating date: {date}")
    tool_context.state[cusip]["rating_dates"].add(date)
    
    # Define possible ratings from each agency
    ratings = {
        "Fitch": ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-"],
        "Moody's": ["Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3", "Baa1", "Baa2", "Baa3", "Ba1", "Ba2", "Ba3"],
        "S&P": ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-"]
    }
    
    # Generate random ratings from each agency
    rating_data = {
        "cusip": cusip,
        "date": date,
        "agencies": {
            "Fitch": random.choice(ratings["Fitch"]),
            "Moody's": random.choice(ratings["Moody's"]),
            "S&P": random.choice(ratings["S&P"])
        }
    }
    
    return json.dumps(rating_data)

##################################################################################################################################################
############################################################ Rating Agent #######################################################################
##################################################################################################################################################

rating_agent = Agent(
    model=GPT4O_MODEL,
    name="rating_agent",
    description="A financial rating specialist who provides security rating information.",
    instruction="""You are a financial rating specialist who provides security rating information.
    
    Your responsibilities:
    1. Ask the user for a CUSIP (Committee on Uniform Security Identification Procedures) identifier.
    2. Use the get_security_ratings tool to retrieve rating information for the specified security.
    3. Present the rating information in a well-formatted markdown table.
    4. Flag any anomalies or suspicious rating patterns (e.g., significant rating differences between agencies).
    5. If the user provides an ISIN instead of a CUSIP, use the isin_to_cusip tool to convert it first.
    Always respond in a professional, concise manner appropriate for financial services.
    """,
    tools=[get_security_ratings, isin_to_cusip, get_current_date],
)

##################################################################################################################################################
############################################################ Pricing Rating Team ###############################################################
##################################################################################################################################################

root_agent = Agent(
    model=GPT4O_MODEL,
    name="pricing_rating_team",
    description="A financial information router that directs user queries to the appropriate specialist agent.",
    instruction="""You are a financial information router that directs user queries to the appropriate specialist agent.
    
    The team consists of two specialized agents:
    1. pricing_team - Handles questions about security pricing
    2. rating_agent - Handles questions about security ratings
    
    Your job is to understand the user's query and route it to the correct agent.
    
    Routing Rules:
    - Identify whether the user is asking about security pricing or security ratings and route to the appropriate agent.
    - If the query is about pricing or pricing anomalies, route to the pricing_team.
    - If the query is about ratings, route to the rating_agent.
    - If the user asks a question that is not related to security pricing or ratings, respond with:
      'I can only answer questions about security pricing and ratings. Please ask a question related to these topics.'
    - If the user asks about both pricing and ratings, ask the user to specify which they want to know first.
    - Do not try to answer the questions yourself - delegate to the specialist agents.
    """,
    sub_agents=[pricing_team_agent, rating_agent]
)

# Sample use cases for testing
USE_CASES = {
    "Pricing then Rating": [
        "What is the current price for CUSIP 037833100?",
        "Can you tell me the rating for CUSIP 037833100?",
    ],
    "ISIN Conversion": [
        "What is the price for ISIN US0378331005?",
        "What are the ratings for ISIN US0378331005?",
    ],
    "Combined Query": [
        "I need both pricing and rating information for CUSIP 037833100",
    ],
    "Date Specific": [
        "What was the price of CUSIP 037833100 on 2025-03-15?",
    ],
}