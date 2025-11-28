from crewai import Agent
from config import settings
from utils import log


class AlertAgentBuilder:
    """
    Alert Agent - Uses NVIDIA NIM Mistral for empathetic human communication
    """
    
    def __init__(self):
        # ✅ Changed from Gemini to NVIDIA NIM
        self.llm = f"nvidia_nim/{settings.NVIDIA_MODEL}"
        
        from tools import send_telegram_message, broadcast_telegram_message, write_alert_log
        
        self.tools = [
            send_telegram_message,
            broadcast_telegram_message,
            write_alert_log
        ]
    
    def build(self) -> Agent:
        """Build and return the Alert Agent"""
        
        return Agent(
            role="Public Health Communication Specialist",
            
            goal="""Create and send clear, empathetic health alerts and notifications.
            
            COMMUNICATION PROTOCOL:
            1. Translate medical findings into simple language
            2. Be empathetic and reassuring
            3. Provide actionable recommendations
            4. Use appropriate urgency level
            5. Include emergency contact info when needed
            
            Write messages that are easy to understand and act upon.""",
            
            backstory="""You are a crisis communication specialist with expertise 
            in public health messaging. You translate complex medical information 
            into clear, actionable guidance that helps people make informed decisions.""",
            
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=self.tools,
            max_iter=1,
            max_rpm=None
        )
