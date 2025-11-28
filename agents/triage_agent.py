from crewai import Agent
from config.settings import settings
from utils.logger import log

class TriageAgentBuilder:
    """Triage Agent - Uses Llama for medical analysis"""
    
    def __init__(self):
        # Keep Ollama
        self.llm = f"ollama/{settings.OLLAMA_MODEL}"
        
        from tools import write_health_record, send_telegram_message
        
        self.tools = [
            write_health_record,
            send_telegram_message
        ]
    
    def build(self) -> Agent:
        """Build and return the Triage Agent"""
        
        return Agent(
            role="Medical Symptom Triage Specialist",
            
            goal="""You MUST use your tools. Do NOT just write what you would do.
            
            STEP 1: Call write_health_record tool
            STEP 2: Call send_telegram_message tool
            
            These are ACTIONS you must take, not descriptions.""",
            
            backstory="""You are an emergency physician who ALWAYS:
            1. Saves patient records using write_health_record
            2. Sends assessments using send_telegram_message
            
            You do this by CALLING TOOLS, not describing them.""",
            
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=self.tools,
            max_iter=1,  # Give plenty of attempts
            max_rpm=None
        )
