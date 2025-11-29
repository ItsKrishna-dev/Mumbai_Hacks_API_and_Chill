from crewai import Task
from typing import Dict, Any
from agents import coordinator_agent
from utils import log

def create_intake_task(
    coordinator_agent,  # Agent object passed from crew
    user_message: str,
    telegram_id: str,
    session_data: Dict[str, Any]
) -> Task:
    """
    Create the intake/coordination task.
    Coordinator ONLY routes - does NOT send messages.
    """
    
    log.info(f"📝 Creating intake task for user {telegram_id}")
    
    return Task(
        description=f"""You are the Coordinator. Analyze the incoming message.

User ID: {telegram_id}
Message: "{user_message}"
Session Data: {session_data}

Your ONLY responsibilities:
1. Determine message type:
   - SYMPTOM: User reporting health symptoms
   - FOLLOWUP: User responding to questions
   - INFO: User asking questions

2. Route to appropriate agent:
   - SYMPTOM or FOLLOWUP → Route to Triage Agent
   - INFO → Provide brief info (but still route to Triage)

3. Provide context for next agent

**CRITICAL RULES:**
- DO NOT send any messages to the user
- DO NOT call send_telegram_message tool
- DO NOT call any tools - just analyze and route
- Your output is ONLY for the next agent

Output format:
Message Type: [SYMPTOM/FOLLOWUP/INFO]
Routing: TRIAGE
Context: [Brief summary for Triage Agent]""",
        
        expected_output="Routing decision with message type and context summary",
        agent=coordinator_agent
    )