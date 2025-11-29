# database/__init__.py

from pymongo import MongoClient
from config.settings import settings
from utils.logger import log
from builtins import Exception
# Import your existing models
from .models import (
    User,
    Session,
    HealthRecord,
    Alert,
    SurveillanceLog,
    RiskLevel,
    SessionState,
)

# ADD THIS: MongoDB Client Setup
mongo_client = MongoClient(settings.MONGODB_URL)
db = mongo_client[settings.MONGODB_DB_NAME]

# ADD THIS: Collection References
users_collection = db['users']
sessions_collection = db['sessions']
health_records_collection = db['health_records']
alerts_collection = db['alerts']
surveillance_logs_collection = db['surveillance_logs']


# ADD THIS: Initialize Database Function
def init_db():
    """Initialize MongoDB indexes for performance"""
    try:
        # Create indexes for fast queries
        users_collection.create_index("telegram_id", unique=True)
        health_records_collection.create_index("user_id")
        health_records_collection.create_index("reported_at")
        sessions_collection.create_index([("user_id", 1), ("last_activity", -1)])
        alerts_collection.create_index("created_at")
        surveillance_logs_collection.create_index("timestamp")
        
        log.info("✅ MongoDB initialized with indexes")
    except Exception as e:
        log.error(f"❌ MongoDB init error: {e}")


# Update exports
__all__ = [
    # Models (keep existing)
    "User",
    "Session",
    "HealthRecord",
    "Alert",
    "SurveillanceLog",
    "RiskLevel",
    "SessionState",
    
    # ADD THIS: MongoDB client and collections
    "db",
    "mongo_client",
    "users_collection",
    "sessions_collection",
    "health_records_collection",
    "alerts_collection",
    "surveillance_logs_collection",
    "init_db",
]
