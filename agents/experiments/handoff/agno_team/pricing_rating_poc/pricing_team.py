from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.models.mistral.mistral import MistralChat
from agno.models.openai import OpenAIChat
from agno.team.team import Team

from agents.common import get_model

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
            "CharlesRiver": round(base_price * (1 + random.uniform(-0.05, 0.05)), 2)
        }
    }
    
    return json.dumps(price_data)

def send_email_to_pricing_team(subject, body, recipient="pricing-team@example.com"):
    """
    Simulates sending an email to the pricing team.
    
    Args:
        subject (str): Email subject
        body (str): Email body content
        recipient (str): Email recipient, defaults to pricing team address
        
    Returns:
        str: Confirmation message
    """
    print(f"MOCK EMAIL:\nTo: {recipient}\nSubject: {subject}\n\n{body}")
    
    return f"Email has been sent to {recipient} with subject: {subject}"



# Original Pricing Agent (now part of the team)
pricing_agent = Agent(
    name="Pricing Agent",
    role="""You are a financial pricing specialist who provides security pricing information.
    
    Your responsibilities:
    1. Ask the user for a CUSIP (Committee on Uniform Security Identification Procedures) identifier and a date.
    2. Use the get_security_prices tool to retrieve pricing information for the specified security.
    3. Present the pricing information in a well-formatted markdown table.
    4. Flag any anomalies or suspicious pricing patterns (e.g., significant price differences between sources).
    5. If the user provides an ISIN instead of a CUSIP, use the isin_to_cusip tool to convert it first.
    6. Handle dates in natural language format (e.g., "yesterday", "today", "last Friday").


    
    When you detect a pricing anomaly (significant price differences between sources), you should ask:
    "Would you like me to follow up with the team?"
    
    If the user says "yes", inform the pricing team that you need to hand off to the pricing support agent.
    
    Always respond in a professional, concise manner appropriate for financial services.
    """,
    model=get_model(),
    add_history_to_messages=True,
    num_history_responses=100,
    tools=[get_security_prices, isin_to_cusip],
    show_tool_calls=True,
    markdown=True,
    add_datetime_to_instructions=True,
)

# New Pricing Support Agent (sub-agent)
pricing_support_agent = Agent(
    name="Pricing Support Agent",
    role="""You are a financial pricing support specialist who helps users with pricing anomalies.
    
    Your responsibilities:
    1. Guide the user through a series of follow-up questions to gather information about the pricing anomaly.
    2. Ask the following questions in sequence:
       - When did the issue start?
       - Are colleagues affected?
       - What environment are they using (e.g., Windows, Mac)?
    3. If not sure ask for clarification.
    4. After you have all the required info, provide a summary of the information collected and assure the user is happy with the email to be sent.
    5. Only THEN (all info & summary validated by user), send the email to the pricing team.

    Always respond in a professional, concise manner appropriate for financial services.
    """,
    model=get_model(),
    add_history_to_messages=True,
    num_history_responses=100,
    tools=[send_email_to_pricing_team],
    show_tool_calls=True,
    markdown=True,
    add_datetime_to_instructions=True,
)

# Pricing Team (includes all members)
pricing_team = Team(
    name="Pricing Team",
    mode="route",
    model=get_model(),
    members=[pricing_agent, pricing_support_agent],
    description="""You are a financial pricing team that helps users with security pricing information and resolves pricing anomalies.
    
    The team consists of two specialized agents:
    1. Pricing Agent - Handles questions about security pricing and detects anomalies
    2. Pricing Support Agent - Guides users through follow-up questions when anomalies are detected
    
    Your job is to understand the user's query and coordinate the team members to provide the best possible assistance.""",
    instructions=[
        "Start by routing all initial requests to the Pricing Agent.",
        "If the Pricing Agent detects an anomaly and the user wants to follow up, route to the Pricing Support Agent.",
        "Ensure smooth handoffs between team members and maintain a coherent conversation flow.",
        # "If the user asks a question that is not related to security pricing, respond with:",
        # "'I can only answer questions about security pricing. Please ask a question related to this topic.'",
        "Do not try to answer the questions yourself - delegate to the specialist agents."
    ],
    num_of_interactions_from_history=100,
    enable_team_history=True,
    markdown=True,
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
    "Pricing Query": [
        "What is the current price for CUSIP 037833100?",
    ],
    "ISIN Conversion": [
        "What is the price for ISIN US0378331005?",
    ],
    "Anomaly Follow-up": [
        "What is the current price for CUSIP 037833100?",
        "yes",  # Response to "Would you like me to follow up with the team?"
        "It started yesterday",  # Response to "When did the issue start?"
        "Yes, my entire team is affected",  # Response to "Are colleagues affected?"
        "We're using Windows 10",  # Response to "What environment are they using?"
    ],
}

def run_in_cli():
    use_case = "human"
    messages = USE_CASES[use_case]
    
    if use_case == "human":
        for message in messages:
            response = pricing_team(message)
            print(f"Team: {response}")
    else:
        for message in messages:
            print(f"User: {message}")
            response = pricing_team(message)
            print(f"Team: {response}")


if __name__ == "__main__":
    run_in_cli()
