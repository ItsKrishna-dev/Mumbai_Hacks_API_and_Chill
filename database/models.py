from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId

class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class SessionState(str, Enum):
    INITIAL = "initial"
    IN_TRIAGE = "in_triage"
    AWAITING_RESPONSE = "awaiting_response"
    COMPLETED = "completed"
    FOLLOW_UP = "follow_up"


class ConversationState(str, Enum):
    INITIAL = "initial"
    AWAITING_DETAILS = "awaiting_details"
    DETAILS_COLLECTED = "details_collected"
    ASSESSMENT_GIVEN = "assessment_given"

class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    telegram_id: str
    session_state: str = "initial"
    conversation_state: str = ConversationState.INITIAL  # ✅ Add this
    context: dict = {}
    current_question: int = 0
    symptoms_collected: list = []
    location: str = None  # ✅ Add location
    additional_details: dict = {}  # ✅ Add extra details
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

class MongoModel(BaseModel):
    """Base model that maps MongoDB `_id` to `id` for convenience."""

    id: Optional[str] = Field(default=None, alias="_id")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )


class User(MongoModel):
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    preferred_language: str = Field(default="en")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Session(MongoModel):
    telegram_id: str
    session_state: SessionState = SessionState.INITIAL
    context: Dict[str, Any] = Field(default_factory=dict)
    current_question: int = 0
    symptoms_collected: List[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class HealthRecord(MongoModel):
    telegram_id: str
    session_id: Optional[str] = None
    symptoms: List[str]
    symptom_details: Dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel
    severity_score: float = 0.0
    location: Optional[str] = None
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    symptom_onset: Optional[datetime] = None
    temperature: Optional[float] = None
    has_fever: bool = False
    has_cough: bool = False
    has_breathing_difficulty: bool = False
    requires_followup: bool = False
    followup_date: Optional[datetime] = None
    followup_completed: bool = False
    agent_assessment: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    severity_notes: Optional[str] = None


class Alert(MongoModel):
    alert_type: str
    severity: RiskLevel
    title: str
    message: str
    affected_location: Optional[str] = None
    affected_symptoms: List[str] = Field(default_factory=list)
    case_count: int = 0
    anomaly_score: float = 0.0
    sent_to_users: List[str] = Field(default_factory=list)
    sent_to_authorities: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None


class SurveillanceLog(MongoModel):
    run_at: datetime = Field(default_factory=datetime.utcnow)
    window_start: datetime
    window_end: datetime
    total_reports: int = 0
    symptom_counts: Dict[str, int] = Field(default_factory=dict)
    location_counts: Dict[str, int] = Field(default_factory=dict)
    anomalies_detected: List[Dict[str, Any]] = Field(default_factory=list)
    alert_triggered: bool = False
    alert_id: Optional[str] = None
    analysis_details: Dict[str, Any] = Field(default_factory=dict)
