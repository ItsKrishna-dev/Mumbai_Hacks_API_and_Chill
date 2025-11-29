from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import asyncio
from config import settings
from config.mongo import db
from utils import log
from crew import get_health_crew
import atexit

# Global scheduler instance
scheduler = None
health_records_collection = db["health_records"]


async def _find_followups_due(limit: int = 50):
    now = datetime.utcnow()
    cursor = health_records_collection.find(
        {
            "requires_followup": True,
            "followup_completed": False,
            "followup_date": {"$lte": now},
        }
    ).limit(limit)
    return await cursor.to_list(length=limit)

def run_scheduled_surveillance():
    """
    Run surveillance analysis on schedule.
    
    This function is called periodically to check for disease patterns.
    """
    log.info("⏰ Running scheduled surveillance analysis...")
    
    try:
        health_crew = get_health_crew()
        
        result = health_crew.run_surveillance_analysis(
            time_window_hours=settings.SPIKE_WINDOW_HOURS
        )
        
        if result.get("escalation"):
            log.warning(f"🚨 Escalation detected in scheduled surveillance!")
        else:
            log.info("✅ Scheduled surveillance complete - No anomalies")
            
    except Exception as e:
        log.error(f"❌ Error in scheduled surveillance: {str(e)}")

def run_scheduled_followups():
    """
    Check for users requiring follow-up and send messages.
    """
    log.info("⏰ Checking for scheduled follow-ups...")
    
    try:
        records = asyncio.run(_find_followups_due())
        
        if not records:
            log.info("No follow-ups due at this time")
            return
        
        log.info(f"Found {len(records)} follow-ups due")
        
        health_crew = get_health_crew()
        
        for record in records:
            try:
                telegram_id = record.get("telegram_id")
                if not telegram_id:
                    log.warning("Skipping follow-up without telegram_id")
                    continue
                
                health_crew.execute_followup_check(
                    user_id=telegram_id,
                    telegram_id=telegram_id,
                    previous_assessment={
                        "symptoms": record.get("symptoms", []),
                        "risk_level": record.get("risk_level", "moderate"),
                        "severity_score": record.get("severity_score", 0),
                        "reported_at": record.get("reported_at", datetime.utcnow()).isoformat(),
                        "recommendations": record.get("recommendations", []),
                    },
                    followup_type="scheduled",
                )
                
                log.info(f"✅ Follow-up sent to {telegram_id}")
            
            except Exception as e:
                log.error(f"Error sending follow-up to user {record.get('telegram_id')}: {str(e)}")
                continue
                    
    except Exception as e:
        log.error(f"❌ Error in scheduled follow-ups: {str(e)}")

def start_scheduler():
    """
    Start the background scheduler for periodic tasks.
    """
    global scheduler
    
    if scheduler is not None:
        log.warning("Scheduler already running")
        return
    
    scheduler = BackgroundScheduler()
    
    # Schedule surveillance every X minutes
    scheduler.add_job(
        func=run_scheduled_surveillance,
        trigger=IntervalTrigger(minutes=settings.SURVEILLANCE_INTERVAL_MINUTES),
        id='surveillance_job',
        name='Run surveillance analysis',
        replace_existing=True
    )
    
    # Schedule follow-up checks every 15 minutes
    scheduler.add_job(
        func=run_scheduled_followups,
        trigger=IntervalTrigger(minutes=15),
        id='followup_job',
        name='Check scheduled follow-ups',
        replace_existing=True
    )
    
    scheduler.start()
    
    log.info(f"✅ Scheduler started:")
    log.info(f"   - Surveillance: Every {settings.SURVEILLANCE_INTERVAL_MINUTES} minutes")
    log.info(f"   - Follow-ups: Every 15 minutes")
    
    # Shut down scheduler on exit
    atexit.register(lambda: shutdown_scheduler())

def shutdown_scheduler():
    """
    Shut down the scheduler gracefully.
    """
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        log.info("✅ Scheduler shut down")
