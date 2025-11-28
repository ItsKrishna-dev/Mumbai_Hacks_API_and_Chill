from .coordinator_agent import CoordinatorAgentBuilder
from .triage_agent import TriageAgentBuilder
from .surveillance_agent import SurveillanceAgentBuilder
from .alert_agent import AlertAgentBuilder

def build_all_agents():
    """Build and return all agents"""
    return {
        'coordinator': CoordinatorAgentBuilder().build(),
        'triage': TriageAgentBuilder().build(),
        'surveillance': SurveillanceAgentBuilder().build(),
        'alert': AlertAgentBuilder().build()
    }

__all__ = [
    'CoordinatorAgentBuilder',
    'TriageAgentBuilder',
    'SurveillanceAgentBuilder',
    'AlertAgentBuilder',
    'build_all_agents'
]
