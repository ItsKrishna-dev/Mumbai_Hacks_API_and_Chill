from crewai import Agent
from config.settings import settings
from utils.logger import log


class CoordinatorAgentBuilder:
    """Coordinator Agent - Uses NVIDIA NIM Mistral for fast routing decisions"""
    
    def __init__(self):
        # ✅ Changed from Gemini to NVIDIA NIM
        self.llm = f"nvidia_nim/{settings.NVIDIA_MODEL}"
        self.tools = []
    
    def build(self) -> Agent:
        """Build and return the Coordinator Agent"""
        
        return Agent(
            role="Health Surveillance Coordinator & System Orchestrator",
            
            goal="""Route health messages to the Medical Symptom Triage Specialist.
            
            When you see symptoms, delegate to "Medical Symptom Triage Specialist".
            
            Pass task as a STRING, context as a STRING, coworker as a STRING.
            Example:
            - task: "Assess symptoms"
            - context: "User has fever 103F and cough"
            - coworker: "Medical Symptom Triage Specialist"
            """,
            
            backstory="""You route patient cases to the right specialist.""",
            
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            tools=self.tools,
            max_iter=1,
            allow_code_execution=False
        )
