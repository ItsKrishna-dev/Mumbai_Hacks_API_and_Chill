from typing import Dict, Any, Optional, List
from crewai import Task, Agent
from utils.logger import log
def create_triage_task(
    triage_agent: Agent,
    user_message: str,
    telegram_id: str,
    session_data: Dict[str, Any],
    conversation_history: Optional[List[str]] = None
) -> Task:
    """Create the triage task"""
    
    log.info(f"Created triage task for user {telegram_id}")
    
    # Extract temperature and symptoms from message for examples
    return Task(
        description="""You are the Triage Agent for user {telegram_id}.

Message: "{message}"
Session: {session_data}
History: {conversation_history}
Routing Action: Use coordinator's decision

**CRITICAL RULES:**
1. Call send_telegram_message ONLY ONCE per execution
2. Check conversation_state before deciding what to do

**IF conversation_state == "INITIAL":**
→ This is the first contact
→ Send ONE message asking for details:
   - Ask for location (city/area)
   - Ask if there are other symptoms
   - Ask about duration
→ Update session: conversation_state = "AWAITING_DETAILS"
→ DO NOT give assessment yet
→ Example message:
   "Thank you for reaching out. To help you better, I need a few details:
   1. What is your location (city/area)?
   2. Are there any other symptoms?
   3. How long have you had these symptoms?
   Please provide these details."

**IF conversation_state == "AWAITING_DETAILS":**
→ User is providing the requested information
→ Collect: location, additional symptoms, duration
→ NOW perform full assessment
→ Send ONE comprehensive message with:
   - Risk level
   - Recommendations
   - When to seek care
→ Update session: conversation_state = "ASSESSMENT_GIVEN"
→ Save health record

**IF conversation_state == "ASSESSMENT_GIVEN":**
→ User is adding NEW symptoms (follow-up)
→ Update the existing assessment
→ Send ONE updated assessment message
→ Update health record

**ENFORCE:** 
- Maximum 1 call to send_telegram_message
- Maximum 1 call to write_health_record
- NO repetitive messages

telegram_id for ALL tool calls: {telegram_id}""",
        expected_output="ONE message sent, health record saved if assessment done",
        agent=self.triage_agent,
        context=[self.intake_task]
    )