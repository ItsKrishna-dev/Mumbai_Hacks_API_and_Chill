# crew/health_crew.py
import asyncio
import re
from crewai import Agent, Crew, Task, Process
from crewai import LLM
from config.settings import settings
from tools.database_tools import get_user_session, write_health_record, update_session
from tools.telegram_tools import send_telegram_message
from tools.anomaly_tools import detect_spike
from tools.gov_mock_tools import submit_to_mock_authority
from datetime import datetime
import logging
from utils import log
from config import settings
from tasks import (
    create_intake_task,
    create_triage_task,
    create_surveillance_task,
    create_alert_task,
    create_followup_task
)

logger = logging.getLogger(__name__)


class HealthCrew:
    def __init__(self):
        logger.info("Initializing SwasthAI Health Crew...")
        
        # Initialize LLM with NVIDIA NIM
        self.llm = LLM(
            model="nvidia_nim/mistralai/mistral-medium-3-instruct",
            api_key=settings.NVIDIA_API_KEY,
            base_url="https://integrate.api.nvidia.com/v1",
            temperature=0.7
        )
        
        logger.info("✅ NVIDIA NIM LLM initialized")
        
        # Initialize agents
        self.coordinator_agent = self._create_coordinator_agent()
        self.triage_agent = self._create_triage_agent()
        self.surveillance_agent = self._create_surveillance_agent()
        self.alert_agent = self._create_alert_agent()
        
        # Initialize tasks
        self.intake_task = self._create_intake_task()
        self.triage_task = self._create_triage_task()
        self.surveillance_task = self._create_surveillance_task()
        self.alert_task = self._create_alert_task()
        
        # Create crew
        self.crew = Crew(
            agents=[
                self.coordinator_agent,
                self.triage_agent,
                self.surveillance_agent,
                self.alert_agent
            ],
            tasks=[
                self.intake_task,
                self.triage_task,
                self.surveillance_task,
                self.alert_task
            ],
            process=Process.sequential,
            verbose=True,
            memory=False
        )
        
        logger.info("✅ All agents initialized successfully")

    # ========== AGENT CREATION METHODS (Already correct) ==========
    
    def _create_coordinator_agent(self) -> Agent:
        """Coordinator Agent"""
        return Agent(
            role="Health Surveillance Coordinator",
            goal="Orchestrate workflow and route messages",
            backstory="Central orchestrator of health surveillance system",
            tools=[get_user_session],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=1  # ✅ Only 1 iteration
        )

    def _create_triage_agent(self) -> Agent:
        """Triage Agent"""
        return Agent(
            role="Healthcare Triage Specialist",
            goal="Assess symptoms and provide health recommendations",
            backstory="Experienced healthcare professional in emergency medicine",
            tools=[get_user_session, write_health_record, update_session, send_telegram_message],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=5  # ✅ Only 1 iteration
        )

    def _create_surveillance_agent(self) -> Agent:
        """Surveillance Agent"""
        return Agent(
            role="Public Health Surveillance Analyst",
            goal="Detect disease patterns and emerging health threats",
            backstory="Epidemiologist specializing in disease surveillance",
            tools=[get_user_session, detect_spike, submit_to_mock_authority],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=1  # ✅ Only 1 iteration
        )

    def _create_alert_agent(self) -> Agent:
        """Alert Agent"""
        return Agent(
            role="Health Communication Specialist",
            goal="Deliver timely health alerts to communities",
            backstory="Public health communicator skilled in crisis communication",
            tools=[send_telegram_message, submit_to_mock_authority],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=1  # ✅ Only 1 iteration
        )

    # ========== TASK CREATION METHODS (FIX INDENTATION HERE) ==========
    
    def _create_intake_task(self) -> Task:  # ✅ INDENTED - part of class
        """Coordinator routes without messaging"""
        return Task(
            description="""You are the Coordinator. Analyze user {telegram_id}'s message.

Message: "{message}"
Session: {session_data}
History: {conversation_history}

Your job:
1. Classify message type (SYMPTOM/FOLLOWUP/INFO)
2. Route to TRIAGE agent
3. Provide context

**DO NOT send messages.**
**DO NOT call send_telegram_message.**
**Only analyze and route.**

Output: Message type and context for Triage Agent""",
            expected_output="Routing decision with context",
            agent=self.coordinator_agent
        )

    def _create_triage_task(self) -> Task:
        """Triage must USE send_telegram_message tool"""
        return Task(
            description="""You are the Triage Agent for user {telegram_id}.

    Message: "{message}"
    Session: {session_data}
    History: {conversation_history}

    **YOUR WORKFLOW:**

    Step 1: Get session info
    → CALL TOOL: get_user_session(telegram_id="{telegram_id}")

    Step 2: **CRITICAL - Check if this is FIRST contact or FOLLOW-UP:**

    Look at the session result context field:
    - IF context is EMPTY or context["questions_asked"] is FALSE → This is FIRST CONTACT
    - IF context["questions_asked"] is TRUE → This is USER RESPONDING to your questions

    **IF FIRST CONTACT (no previous questions):**

    1. CALL TOOL: send_telegram_message(
        chat_id="{telegram_id}",
        message="Hello {user_name}, I understand you mentioned: {message}.

    To provide accurate assessment:

    1️⃣ What is your location (city/area)?
    2️⃣ Any other symptoms besides what you mentioned?
    3️⃣ Pre-existing conditions or current medications?

    Please share these details.",
        parse_mode="HTML"
    )

    2. CALL TOOL: update_session(
        telegram_id="{telegram_id}",
        session_state="AWAITING_DETAILS",
        context={{"questions_asked": true, "initial_symptom": "{message}"}}
    )

    3. Your Final Answer: "Initial questions sent, awaiting user response"

    **IF USER IS RESPONDING (questions_asked = true):**

    1. Extract ALL information from BOTH current message AND history:
    - Symptoms: {message} + conversation history
    - Location: Look for city/area names
    - Duration: "for 2 days", "since morning", etc.
    - Severity: fever values, pain levels

    2. Assess risk level:
    - LOW: Mild symptoms
    - MODERATE: Multiple symptoms, >2 days duration
    - HIGH: Fever >102°F (39°C), severe pain, breathing issues
    - CRITICAL: Emergency symptoms

    3. Calculate severity_score (0-10)

    4. CALL TOOL: write_health_record(
        telegram_id="{telegram_id}",
        symptoms=[LIST ALL EXTRACTED SYMPTOMS],
        location="[EXTRACTED LOCATION OR 'Unknown']",
        risk_level="[YOUR ASSESSED LEVEL]",
        severity_score=[YOUR CALCULATED SCORE],
        agent_assessment="Based on your symptoms ([LIST THEM]), you have [RISK LEVEL] risk. [DETAILED EXPLANATION]",
        recommendations=["Rest and hydration", "Monitor temperature", "Seek care if worsens"]
    )

    5. CALL TOOL: send_telegram_message(
        chat_id="{telegram_id}",
        message="🏥 <b>Health Assessment for {user_name}</b>

    <b>Risk Level:</b> [YOUR ASSESSED RISK]
    <b>Severity:</b> [SCORE]/10

    <b>Your Symptoms:</b>
    • [LIST ALL SYMPTOMS]

    <b>Location:</b> [LOCATION]

    <b>Assessment:</b>
    [YOUR DETAILED, CONTEXTUAL ASSESSMENT BASED ON ACTUAL SYMPTOMS]

    <b>Recommendations:</b>
    1. [SPECIFIC RECOMMENDATION 1]
    2. [SPECIFIC RECOMMENDATION 2]
    3. [SPECIFIC RECOMMENDATION 3]

    ⚠️ If symptoms worsen or you develop emergency signs, seek immediate medical care.",
        parse_mode="HTML"
    )

    6. CALL TOOL: update_session(
        telegram_id="{telegram_id}",
        session_state="ASSESSMENT_GIVEN",
        context={{"assessment_complete": true}}
    )

    7. Your Final Answer: "Assessment and recommendations sent to user"

    **CRITICAL RULES:**
    - ALWAYS call send_telegram_message - DO NOT just print text
    - Check questions_asked in context to decide which path
    - Extract ALL symptoms from message + history
    - Provide REAL risk assessment, not placeholders
    - Replace ALL [BRACKETS] with actual values

    telegram_id: {telegram_id}
    user_name: {user_name}""",
            expected_output="Message sent via send_telegram_message tool",
            agent=self.triage_agent,
            context=[self.intake_task]
        )



    def _create_surveillance_task(self) -> Task:  # ✅ INDENTED - part of class
        """Surveillance runs silently"""
        return Task(
            description="""You are the Surveillance Agent.

Current user: {telegram_id}
Health record: From Triage Agent's output

Your job:
1. Analyze population health patterns (silent)
2. Detect disease clustering
3. Check for anomalies using detect_spike if needed
4. Log findings internally

**DO NOT send any messages to users.**
**DO NOT call send_telegram_message.**
**Surveillance runs silently in the background.**

Only flag critical outbreaks for Alert Agent.""",
            expected_output="Surveillance analysis complete (no user message)",
            agent=self.surveillance_agent,
            context=[self.triage_task]
        )

    def _create_alert_task(self) -> Task:  # ✅ INDENTED - part of class
        """Alert only for community-wide issues"""
        return Task(
            description="""You are the Alert Agent.

Surveillance findings: From previous task
Current user: {telegram_id}

Your job:
**ONLY send messages if there's a community-wide outbreak.**

Conditions to send alert:
- Multiple users with similar symptoms in same area
- Disease outbreak threshold exceeded
- Public health emergency

**DO NOT send messages for individual cases.**
**Triage Agent handles all individual user communication.**

If outbreak detected:
- Notify authorities: submit_to_mock_authority(...)
- Send community alert (optional)

Otherwise: Stay silent, do nothing.""",
            expected_output="Alert sent only if outbreak (usually silent)",
            agent=self.alert_agent,
            context=[self.surveillance_task]
        )

    # ========== MESSAGE PROCESSING METHOD ==========
    
    # ✅ ADD 'async' keyword
    async def process_user_message(
        self, 
        telegram_id: int, 
        message: str,
        session_data: dict = None,
        conversation_history: list = None,
        language: str = "en"
    ):
        """Process incoming user message"""
        try:
            logger.info(f"🔄 Processing message from user {telegram_id}")
            
            # Format session data
            session_info = "No previous session"
            if session_data:
                session_info = f"Session ID: {session_data.get('session_id', 'N/A')}, State: {session_data.get('state', 'initial')}"
                logger.info(f"📝 {session_info}")
            
            # Format history
            history_text = "No previous conversation"
            if conversation_history and len(conversation_history) > 0:
                recent_history = conversation_history[-5:]
                history_text = "\n".join(recent_history)
                logger.info(f"💬 Including {len(recent_history)} previous messages")
            
            # ✅ ADD THIS: Extract user name from session or use default
            user_name = "User"
            if session_data and isinstance(session_data, dict):
                # Try to get name from session context
                context = session_data.get('context', {})
                if isinstance(context, dict):
                    user_name = context.get('user_name', 'User')
            
            # Prepare inputs
            crew_inputs = {
                'telegram_id': telegram_id,
                'message': message,
                'user_name': user_name,  # ✅ ADD THIS LINE
                'timestamp': datetime.now().isoformat(),
                'session_data': session_info,
                'conversation_history': history_text,
                'language': language
            }
            
            # Kickoff crew
            result = self.crew.kickoff(inputs=crew_inputs)
            
            logger.info(f"✅ Crew processing complete")
            
            # Return proper dict format
            return {
                "status": "success",
                "result": str(result.raw) if hasattr(result, 'raw') else str(result)
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing user message: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return error dict
            return {
                "status": "error",
                "error": str(e)
            }


# Singleton pattern
_health_crew_instance = None


def get_health_crew() -> HealthCrew:
    """Get or create the HealthCrew singleton"""
    global _health_crew_instance
    if _health_crew_instance is None:
        logger.info("Creating new HealthCrew instance...")
        _health_crew_instance = HealthCrew()
    return _health_crew_instance
