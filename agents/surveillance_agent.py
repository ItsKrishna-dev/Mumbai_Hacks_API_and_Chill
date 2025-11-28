from crewai import Agent
from config import settings
from utils import log

class SurveillanceAgentBuilder:
    """
    Surveillance Agent - Uses Llama 3.2 3B for epidemiological analysis
    """
    
    def __init__(self):
        # Use Llama 3.2 3B via Ollama for medical pattern detection
        self.llm = f"ollama/{settings.LLM_MODEL}"
        
        # Import tools
        from tools import get_recent_symptoms, detect_spike, write_alert_log
        
        self.tools = [
            get_recent_symptoms,
            detect_spike,
            write_alert_log
        ]
    
    def build(self) -> Agent:
        """Build and return the Surveillance Agent"""
        
        return Agent(
            role="Epidemiological Surveillance Analyst",
            
            goal="""Monitor population health data for disease outbreak patterns.
            
            ANALYSIS PROTOCOL:
            1. Retrieve recent symptom reports
            2. Identify symptom clusters
            3. Detect statistical spikes
            4. Calculate outbreak probability
            5. Create alerts for concerning patterns
            
            Use epidemiological methods and statistical analysis.""",
            
            backstory="""You are a CDC-trained epidemiologist specializing in 
            infectious disease surveillance and outbreak detection. You use 
            statistical methods to identify emerging health threats.""",
            
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=self.tools,
            max_iter=1,
            max_rpm=None
        )
