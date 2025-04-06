from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.models.mistral.mistral import MistralChat
from agno.models.openai import OpenAIChat
from agno.team.team import Team

from agents.common import get_model
from agents.experiments.handoff.agno_team.pricing_rating_poc.pricing_team import pricing_team

def isin_to_cusip(isin):
    """
    Converts an ISIN (International Securities Identification Number) to a CUSIP.
    This is a fake implementation for testing purposes.
    
    Args:
        isin (str): The ISIN code to convert.
        
    Returns:
        str: A fake CUSIP derived from the ISIN.
    """
    if not isin or len(isin) != 12:
        return "Invalid ISIN format"
    
    # Extract the country code and basic code from ISIN
    country_code = isin[:2]
    basic_code = isin[2:11]
    
    # Create a fake CUSIP (first 8 characters of the basic code + a random check digit)
    import random
    fake_cusip = basic_code[:8] + str(random.randint(0, 9))
    
    return fake_cusip


def get_security_prices(cusip, date):
    """
    Returns price information for a security from multiple sources.
    
    Args:
        cusip (str): The CUSIP identifier for the security.
        date (str): The date in YYYY-MM-DD format.
        
    Returns:
        str: JSON string containing price information from multiple sources.
    """
    import json
    import random
    
    # Generate fake prices with slight variations
    base_price = random.uniform(50.0, 200.0)
    
    price_data = {
        "cusip": cusip,
        "date": date,
        "sources": {
            "Bloomberg": round(base_price * (1 + random.uniform(-0.02, 0.02)), 2),
            "Yahoo": round(base_price * (1 + random.uniform(-0.03, 0.03)), 2),
            "BobTheBuilder": round(base_price * (1 + random.uniform(-0.05, 0.05)), 2)
        }
    }
    
    return json.dumps(price_data)

def get_security_ratings(cusip, date):
    """
    Returns rating information for a security from multiple rating agencies.
    
    Args:
        cusip (str): The CUSIP identifier for the security.
        date (str): The date in YYYY-MM-DD format.
        
    Returns:
        str: JSON string containing rating information from multiple agencies.
    """
    import json
    import random
    
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




rating_agent = Agent(
    name="Rating Agent",
    role="""You are a financial rating specialist who provides security rating information.
    
    Your responsibilities:
    1. Ask the user for a CUSIP (Committee on Uniform Security Identification Procedures) identifier.
    2. Use the get_security_ratings tool to retrieve rating information for the specified security.
    3. Present the rating information in a well-formatted markdown table.
    4. Flag any anomalies or suspicious rating patterns (e.g., significant rating differences between agencies).
    5. If the user provides an ISIN instead of a CUSIP, use the isin_to_cusip tool to convert it first.
    
    Always respond in a professional, concise manner appropriate for financial services.
    """,
    model=get_model(),
    add_history_to_messages=True,
    num_history_responses=100,
    tools=[get_security_ratings, isin_to_cusip],
    show_tool_calls=True,
    markdown=True,
)




pricing_rating_team = Team(
    name="Pricing and Rating Team",
    mode="route",
    model=get_model(),
    members=[pricing_team, rating_agent],
    # read_team_history=True,
    num_of_interactions_from_history=100,
    enable_team_history=True,
    markdown=True,
    description="""You are a financial information router that directs user queries to the appropriate specialist agent.
    The team consists of two specialized agents:
    1. Pricing Team - Handles questions about security pricing
    2. Rating Agent - Handles questions about security ratings
    
    Your job is to understand the user's query and route it to the correct agent.""",
    instructions=[
        "Identify whether the user is asking about security pricing or security ratings and route to the appropriate agent.",
        "If the query is about pricing or pricing anomalies, route to the Pricing Team.",
        "If the query is about ratings, route to the Rating Agent.",
        "If the user asks a question that is not related to security pricing or ratings, respond in English with:",
        "'I can only answer questions about security pricing and ratings. Please ask a question related to these topics.'",
        "If the user asks about both pricing and ratings, ask the user to specify which they want to know first.",
        "Do not try to answer the questions yourself - delegate to the specialist agents."
    ],
    show_tool_calls=True,
    show_members_responses=True,
)

def human_input_generator():
    while True:
        msg = input("User: ")
        if msg == "exit":
            break
        yield msg


USE_CASES = {
    "human": human_input_generator(),
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

def run_in_cli():
    use_case = "human"
    # use_case = "Pricing then Rating"
    for msg in USE_CASES[use_case]:
        pricing_rating_team.print_response(msg, stream=True)

    # # Ask "How are you?" in all supported languages
    # pricing_rating_team.print_response("Comment allez-vous?", stream=True)  # French
    # pricing_rating_team.print_response("How are you?", stream=True)  # English
    # pricing_rating_team.print_response("你好吗？", stream=True)  # Chinese
    # pricing_rating_team.print_response("Come stai?", stream=True)  # Italian

if __name__ == "__main__":
    run_in_cli()