from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool



# Replace Gemini model with OpenAI GPT-4o
# Note: Requires OPENAI_API_KEY to be set in the environment
GPT4O_MODEL = LiteLlm(model="gpt-4o", parallel_tool_calls=False)

##################################################################################################################################################
############################################################ Define the Tools ###################################################################
##################################################################################################################################################

def get_current_date() -> str:
    """
    Returns the current date in YYYY-MM-DD format.
    
    Returns:
        str: Current date in YYYY-MM-DD format.
    """
    # Best Practice: Log tool execution for easier debugging
    print(f"--- Tool: get_current_date called ---")
    
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


def isin_to_cusip(isin: str) -> str:
    """
    Converts an ISIN (International Securities Identification Number) to a CUSIP.
    This is a fake implementation for testing purposes.
    
    Args:
        isin (str): The ISIN code to convert.
        
    Returns:
        str: A fake CUSIP derived from the ISIN.
    """
    # Best Practice: Log tool execution for easier debugging
    print(f"--- Tool: isin_to_cusip called for ISIN: {isin} ---")
    
    if not isin or len(isin) != 12:
        return "Invalid ISIN format"
    
    # Extract the country code and basic code from ISIN
    country_code = isin[:2]
    basic_code = isin[2:11]
    
    # Create a fake CUSIP (first 8 characters of the basic code + a random check digit)
    import random
    fake_cusip = basic_code[:8] + str(random.randint(0, 9))
    
    return fake_cusip


def get_security_prices(cusip: str, date: str) -> str:
    """
    Returns price information for a security from multiple sources.
    
    Args:
        cusip (str): The CUSIP identifier for the security.
        date (str): The date in YYYY-MM-DD format.
        
    Returns:
        str: JSON string containing price information from multiple sources.
    """
    # Best Practice: Log tool execution for easier debugging
    print(f"--- Tool: get_security_prices called for CUSIP: {cusip}, Date: {date} ---")
    
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


def send_email_to_pricing_team(subject: str, body: str, recipient: str = "pricing-team@example.com") -> str:
    """
    Simulates sending an email to the pricing team.
    
    Args:
        subject (str): Email subject
        body (str): Email body content
        recipient (str): Email recipient, defaults to pricing team address
        
    Returns:
        str: Confirmation message
    """
    # Best Practice: Log tool execution for easier debugging
    print(f"--- Tool: send_email_to_pricing_team called ---")
    print(f"MOCK EMAIL:\nTo: {recipient}\nSubject: {subject}\n\n{body}")
    
    return f"Email has been sent to {recipient} with subject: {subject}"


##################################################################################################################################################
############################################################ Sub-Agents ##########################################################################
##################################################################################################################################################

# Original Pricing Agent (now part of the team)
pricing_agent = Agent(
    model=GPT4O_MODEL,
    name="pricing_agent",
    description="A financial pricing specialist who provides security pricing information.",
    instruction="""You are a financial pricing specialist who provides security pricing information.
    
    Your responsibilities:
    1. Ask the user for a CUSIP (Committee on Uniform Security Identification Procedures) identifier and a date.
    2. Use the get_security_prices tool to retrieve pricing information for the specified security.
    3. Present the pricing information in a well-formatted markdown table.
    4. Flag any anomalies or suspicious pricing patterns (e.g., significant price differences between sources).
    5. If the user provides an ISIN instead of a CUSIP, use the isin_to_cusip tool to convert it first.
    6. Handle dates in natural language format (e.g., "yesterday", "today", "last Friday").
    
    When you detect a pricing anomaly (significant price differences between sources), you should ask:
    "Would you like me to follow up with the team?"
    
    If the user says "yes", inform them that you will hand off to the pricing support agent.
    
    Always respond in a professional, concise manner appropriate for financial services.
    """,
    tools=[get_security_prices, isin_to_cusip, get_current_date],
)

# New Pricing Support Agent (sub-agent)
pricing_support_agent = Agent(
    model=GPT4O_MODEL,
    name="pricing_support_agent",
    description="A financial pricing support specialist who helps users with pricing anomalies.",
    instruction="""You are a financial pricing support specialist who helps users with pricing anomalies.
    
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
    tools=[send_email_to_pricing_team],
)


##################################################################################################################################################
############################################################ Root Agent ##########################################################################
##################################################################################################################################################

# Create AgentTools from the specialized agents
pricing_agent_tool = AgentTool(agent=pricing_agent)
pricing_support_agent_tool = AgentTool(agent=pricing_support_agent)

# Root Agent that uses specialized agents as tools (instead of using sub_agents)
pricing_team_agent = Agent(
    model=GPT4O_MODEL,
    name="pricing_team",
    description="A financial pricing team that coordinates pricing agents to help users with security pricing information and anomalies.",
    instruction="""You are a financial pricing team coordinator that helps users with security pricing information and resolves pricing anomalies.
    
    You have access to two specialized agent tools:
    1. pricing_agent_tool - For handling questions about security pricing and detecting anomalies
    2. pricing_support_agent_tool - For guiding users through follow-up questions when anomalies are detected
    
    Your job is to understand the user's query and use the appropriate agent tool to provide the best possible assistance.
    
    Tool Selection Guidelines:
    - For initial pricing requests or ISIN/CUSIP inquiries, use the pricing_agent_tool.
    - If a pricing anomaly is detected and the user wants to follow up, use the pricing_support_agent_tool.
    - Ensure a coherent conversation flow when switching between tools.
    - Do not try to answer the questions yourself - use the specialized agent tools instead.
    """,
    tools=[pricing_agent_tool, pricing_support_agent_tool]
)
