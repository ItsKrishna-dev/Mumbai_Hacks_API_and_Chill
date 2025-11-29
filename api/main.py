from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from config.mongo import db
from utils import log
from api.telegram_webhook import telegram_router, telegram_app
from api.scheduler import start_scheduler, shutdown_scheduler
from database import RiskLevel
import uvicorn
import os
from builtins import Exception, str

users_collection = db["users"]
health_records_collection = db["health_records"]
alerts_collection = db["alerts"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    log.info(f"🚀 Starting {settings.APP_NAME}...")
    
    log.info("📊 MongoDB client ready")
    
    # Create necessary directories
    os.makedirs(settings.BASE_DIR / "logs", exist_ok=True)
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    
    telegram_initialized = False
    log.info("🤖 Initializing Telegram Application...")
    try:
        await telegram_app.initialize()
        await telegram_app.start()
        telegram_initialized = True
        log.info("✅ Telegram Application ready")
    except Exception as telegram_error:
        log.error(
            "❌ Telegram bot startup failed (network block or SSL issue): %s",
            telegram_error,
        )
        log.warning(
            "Network appears to block https://api.telegram.org. "
            "Allow Telegram traffic or log into the captive portal, "
            "then restart the server."
        )
    
    # Start background scheduler
    log.info("⏰ Starting background scheduler...")
    start_scheduler()
    log.info("✅ Scheduler started")
    
    log.info(f"✅ {settings.APP_NAME} is ready!")
    
    yield
    
    # Shutdown
    log.info(f"🛑 Shutting down {settings.APP_NAME}...")
    shutdown_scheduler()
    if telegram_initialized:
        await telegram_app.stop()
        await telegram_app.shutdown()
    else:
        log.info("⏹️ Telegram bot was not running; skipping shutdown")
    log.info("✅ Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="SwasthAI - Autonomous Health Intelligence Network",
    description="Multi-agent health surveillance system using CrewAI",
    version="3.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(telegram_router, prefix="/webhook", tags=["telegram"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SwasthAI",
        "version": "3.0.0 - Multi-Agent System",
        "status": "operational",
        "description": "Autonomous Health Intelligence Agent Network",
        "features": [
            "Multi-Agent System (CrewAI)",
            "Telegram Bot Integration",
            "AI-Powered Triage",
            "Population Surveillance",
            "Automated Alerting",
            "Follow-up Management"
        ],
        "endpoints": {
            "telegram_webhook": "/webhook/telegram",
            "webhook_setup": "/webhook/setup",
            "health": "/health",
            "stats": "/stats",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "agents": "active"
    }

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        total_users = await users_collection.count_documents({})
        total_records = await health_records_collection.count_documents({})
        total_alerts = await alerts_collection.count_documents({})
        
        risk_counts = {}
        for level in RiskLevel:
            risk_counts[level.value] = await health_records_collection.count_documents(
                {"risk_level": level.value}
            )
        
        return {
            "total_users": total_users,
            "total_health_records": total_records,
            "total_alerts": total_alerts,
            "risk_distribution": risk_counts,
            "status": "operational",
            "agents": {
                "coordinator": "active",
                "triage": "active",
                "surveillance": "active",
                "alert": "active"
            }
        }
    except Exception as e:
        log.error(f"Error fetching stats: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
