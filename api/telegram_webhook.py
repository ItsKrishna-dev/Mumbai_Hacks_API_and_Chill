from typing import Optional
from fastapi import APIRouter, Header, Request
from telegram import InlineKeyboardMarkup, Update,InlineKeyboardButton
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from utils.translation import translate_text_sync
from telegram.request import HTTPXRequest
import httpx
from config import settings
from config.mongo import db
from utils import log
from crew import get_health_crew
from database import User, Session, SessionState, RiskLevel
from datetime import datetime
from pymongo import DESCENDING
import json
from api.image_analyzer import analyze_medical_image
from api.voice_to_text import transcribe_audio
import uuid
import tempfile
import os
# Create router
telegram_router = APIRouter()


class CustomHTTPXRequest(HTTPXRequest):
    """Extend PTB HTTPX client to allow toggling SSL verification."""

    def __init__(self, *args, verify: bool = True, **kwargs):
        self._verify_override = verify
        super().__init__(*args, **kwargs)

    def _build_client(self) -> httpx.AsyncClient:  # type: ignore[override]
        client_kwargs = {**self._client_kwargs, "verify": self._verify_override}
        return httpx.AsyncClient(**client_kwargs)


# Initialize Telegram application (TLS verify disabled for local proxy)
telegram_request = CustomHTTPXRequest(verify=False)
telegram_app = (
    ApplicationBuilder()
    .token(settings.TELEGRAM_BOT_TOKEN)
    .request(telegram_request)
    .build()
)


users_collection = db["users"]
sessions_collection = db["sessions"]
health_records_collection = db["health_records"]

LANGUAGE_OPTIONS = {
    "en": {
        "label": "English 🇬🇧",
        "ack": "Great! I'll continue helping you in English.",
    },
    "hi": {
        "label": "हिन्दी 🇮🇳",
        "ack": "बहुत बढ़िया! अब मैं हिंदी में आपकी मदद करूंगा।",
    },
    "mr": {
        "label": "मराठी 🇮🇳",
        "ack": "छान! आता मी मराठीत तुमची मदत करेन.",
    },
}

LANGUAGE_PROMPT = (
    "Please choose your preferred language / कृपया भाषा चुनें / कृपया भाषा निवडा."
)

WELCOME_MESSAGE_EN = """
👋 Welcome to SwasthAI!

I'm your **Autonomous AI Health Intelligence Network** powered by multi-agent coordination.

**🤖 Our AI Agents:**
• **Coordinator Agent** - Orchestrates your health journey
• **Triage Agent** - Expert symptom assessment
• **Surveillance Agent** - Community health monitoring
• **Alert Agent** - Timely health notifications

**✨ What Makes Us Special:**
✅ Advanced AI-powered symptom analysis
✅ Real-time risk assessment
✅ Population-level disease surveillance
✅ Automated follow-up care
✅ Community health alerts
✅ Privacy-first design

**📝 How to Use:**
Just describe your symptoms naturally:
"I have fever and cough for 2 days"

Our agents will:
1. Assess your symptoms
2. Determine risk level
3. Provide recommendations
4. Schedule follow-ups
5. Monitor community patterns

**Commands:**
/help - Detailed help
/status - Your health records
/test - Test the system

Ready to start? Type your symptoms! 🏥
""".strip()

def _model_dump(model):
    return model.model_dump(by_alias=True, exclude_none=True)


async def fetch_user(telegram_id: str):
    return await users_collection.find_one({"telegram_id": telegram_id})


async def ensure_user_profile(tg_user):
    telegram_id = str(tg_user.id)
    existing = await fetch_user(telegram_id)
    now = datetime.utcnow()
    update_fields = {
        "username": tg_user.username,
        "first_name": tg_user.first_name,
        "last_name": tg_user.last_name,
        "updated_at": now,
    }
    
    if existing:
        # backfill default language if missing
        if "preferred_language" not in existing:
            update_fields["preferred_language"] = "en"
        if update_fields:
            await users_collection.update_one(
                {"telegram_id": telegram_id},
                {"$set": update_fields},
            )
        return await fetch_user(telegram_id), False
    
    user_model = User(
        telegram_id=telegram_id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
    )
    payload = _model_dump(user_model)
    result = await users_collection.insert_one(payload)
    payload["_id"] = result.inserted_id
    return payload, True


async def fetch_active_session(telegram_id: str):
    return await sessions_collection.find_one(
        {
            "telegram_id": telegram_id,
            "session_state": {"$ne": SessionState.COMPLETED.value},
        },
        sort=[("started_at", DESCENDING)],
    )


async def ensure_active_session(telegram_id: str) -> Session:
    """Ensure user has an active session"""
    
    # Get or create user (ASYNC)
    user = await users_collection.find_one({"telegram_id": telegram_id})
    
    if not user:
        # Create new user
        user_data = {
            "telegram_id": telegram_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await users_collection.insert_one(user_data)
        user = await users_collection.find_one({"_id": result.inserted_id})
    
    # Find active session (ASYNC)
    session = await sessions_collection.find_one(
        {
            "user_id": user["_id"],
            "session_state": {"$ne": "COMPLETED"}
        },
        sort=[("started_at", -1)]
    )
    
    if not session:
        # Create new session
        session_data = {
            "user_id": user["_id"],
            "telegram_id": telegram_id,
            "session_state": "initial",
            "context": {},
            "current_question": 0,
            "symptoms_collected": [],
            "started_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        result = await sessions_collection.insert_one(session_data)
        session = await sessions_collection.find_one({"_id": result.inserted_id})
    
    # Convert ObjectId to string for Pydantic
    session_dict = dict(session)
    session_dict["_id"] = str(session_dict["_id"])  # Convert ObjectId to string
    session_dict["user_id"] = str(session_dict["user_id"])  # Convert user_id too
    
    # Convert to Pydantic model
    return Session(**session_dict)


# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    log.info(f"📱 /start command from user {telegram_id}")
    
    profile, created = await ensure_user_profile(user)
    
    if created:
        log.info(f"✅ New user created: {telegram_id}")
    current_language = profile.get("preferred_language")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(LANGUAGE_OPTIONS["en"]["label"], callback_data="lang_en"),
                InlineKeyboardButton(LANGUAGE_OPTIONS["hi"]["label"], callback_data="lang_hi"),
                InlineKeyboardButton(LANGUAGE_OPTIONS["mr"]["label"], callback_data="lang_mr"),
            ]
        ]
    )
    prompt = LANGUAGE_PROMPT
    if current_language and current_language in LANGUAGE_OPTIONS:
        prompt += f"\n\nCurrent: {LANGUAGE_OPTIONS[current_language]['label']}"
    await update.message.reply_text(prompt, reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
❓ **SwasthAI Help**

**🤖 Multi-Agent System:**
Our 4 specialized AI agents work together:

1️⃣ **Coordinator Agent**
   • Routes your queries
   • Manages workflow
   • Schedules follow-ups

2️⃣ **Triage Agent**
   • Symptom assessment
   • Risk stratification
   • Health recommendations

3️⃣ **Surveillance Agent**
   • Pattern detection
   • Outbreak identification
   • Community monitoring

4️⃣ **Alert Agent**
   • Health notifications
   • Community alerts
   • Emergency warnings

**📝 Symptom Reporting:**
Just type naturally:
• "Fever and cough for 2 days"
• "Headache and nausea"
• "Difficulty breathing"

**🎯 Risk Levels:**
🚨 CRITICAL - Emergency care needed
⚠️ HIGH - See doctor soon
🟡 MODERATE - Monitor closely
✅ LOW - Self-care

**Commands:**
/start - Start conversation
/help - This message
/status - Health history
/test - Test agents

**🚨 Emergency:**
Severe symptoms? Call: 108 / 112

**🔐 Privacy:**
Your data is secure and used only for:
• Your personal health monitoring
• Anonymous community surveillance
• Early disease detection

Questions? Just ask! 💬
"""
    await update.message.reply_text(help_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    telegram_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    user = await fetch_user(telegram_id)
    if not user:
        await update.message.reply_text("No health records found. Use /start to begin.")
        return
    
    cursor = (
        health_records_collection.find({"telegram_id": telegram_id})
        .sort("reported_at", DESCENDING)
        .limit(5)
    )
    records = await cursor.to_list(length=5)
    
    if not records:
        status_text = f"""
📊 **Health Status - {user_name}**

No symptoms reported yet.

Type your symptoms to start AI-powered health monitoring! 🏥
"""
    else:
        latest = records[0]
        reported_at = latest.get("reported_at", datetime.utcnow())
        time_ago = datetime.utcnow() - reported_at
        hours_ago = int(time_ago.total_seconds() / 3600)
        
        risk_emoji = {
            "critical": "🚨",
            "high": "⚠️",
            "moderate": "🟡",
            "low": "✅"
        }
        
        status_text = f"""
📊 **Your Health Status**

**Latest Assessment:** {hours_ago}h ago
{risk_emoji.get(latest.get('risk_level'), '🟡')} **Risk:** {latest.get('risk_level', 'moderate').upper()}
**Severity:** {latest.get('severity_score', 0)}/10

**Symptoms:** {', '.join(latest.get('symptoms', []))}

**Assessment:**
{(latest.get('agent_assessment') or '')[:200]}...

**History:** {len(records)} reports
"""
        
        if latest.get("requires_followup"):
            status_text += f"\n📅 **Follow-up:** Scheduled"
        
        status_text += "\n\n Type new symptoms to update your status."
    
    await update.message.reply_text(status_text)

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /test command"""
    user = update.effective_user
    
    test_msg = f"""
🧪 **SwasthAI System Test**

**Bot Status:** ✅ Operational
**AI Agents:** ✅ All Active
**Database:** ✅ Connected
**Surveillance:** ✅ Monitoring

**Your Account:**
• ID: {user.id}
• Username: @{user.username or 'Not set'}
• Name: {user.first_name}

**Active Agents:**
🤖 Coordinator: Ready
🏥 Triage: Ready
📊 Surveillance: Running
📢 Alert: Standby

**Test AI Assessment:**
Type: "I have fever and headache"

The agents will coordinate to provide comprehensive assessment! 🚀
"""
    await update.message.reply_text(test_msg)

async def language_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline language selection callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data or ""
    language_code = data.split("_", 1)[-1]
    
    if language_code not in LANGUAGE_OPTIONS:
        await query.edit_message_text("Unsupported language choice. Please try again.")
        return
    
    telegram_id = str(query.from_user.id)
    
    await users_collection.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"preferred_language": language_code}},
    )
    
    log.info("🌍 User %s selected language %s", telegram_id, language_code)
    
    ack_text = LANGUAGE_OPTIONS[language_code]["ack"]
    await query.edit_message_text(ack_text)
    
    welcome_text = WELCOME_MESSAGE_EN
    if language_code != "en":
        # ✅ FIX 2: REMOVE AWAIT HERE (translate_text_sync is NOT async)
        translated = translate_text_sync(WELCOME_MESSAGE_EN, language_code)
        if translated:
            welcome_text = translated
    
    await query.message.reply_text(welcome_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages with CrewAI multi-agent system"""
    user = update.effective_user
    telegram_id = str(update.effective_user.id)
    profile, _ = await ensure_user_profile(user)
    preferred_language = profile.get("preferred_language", "en")
    message_text = update.message.text
    
    log.info(f"💬 Message from {telegram_id}: {message_text}")
    
    try:
        # Send typing indicator
        await update.message.chat.send_action("typing")
        await ensure_user_profile(user)
        
        # Normalize user input
        if preferred_language != "en" and message_text:
            try:
                normalized = translate_text_sync(message_text, preferred_language)
                if normalized and normalized != message_text:
                    log.info(f"🔤 Normalized: '{message_text}' → '{normalized}'")
                    message_text = normalized
            except Exception as t_e:
                log.warning(f"Translation normalization failed: {t_e}")
        
        # Get or create user session
        session = await ensure_active_session(telegram_id)
        
        session_data = {
            "session_id": session.id,
            "state": session.session_state,
            "context": session.context or {},
            "current_question": session.current_question,
            "symptoms_collected": session.symptoms_collected or [],
        }
        
        # Get conversation history
        if 'history' not in context.user_data:
            context.user_data['history'] = []
        
        # Get health crew and process message
        log.info(f"🚀 Invoking CrewAI agents for {telegram_id}")
        health_crew = get_health_crew()
        
        # ✅ FIXED: Removed user_name parameter
        result = await health_crew.process_user_message(
            message=message_text,
            telegram_id=telegram_id,
            session_data=session_data,
            conversation_history=context.user_data.get('history', []),
            language=preferred_language
        )
        
        # Store in history
        context.user_data['history'].append(f"User: {message_text}")
        if len(context.user_data['history']) > 10:
            context.user_data['history'] = context.user_data['history'][-10:]
        
        log.info(f"✅ CrewAI processing complete for {telegram_id}")
        
        # Handle response
        if result and result.get("status") == "error":
            error_msg = result.get("error", "Unknown error")
            log.error(f"❌ Processing failed: {error_msg}")
            
            if "rate" in error_msg.lower() or "quota" in error_msg.lower():
                await update.message.reply_text(
                    "⏳ Service is busy right now. Please wait a moment and try again."
                )
            else:
                await update.message.reply_text(
                    "Sorry, I encountered an error. Please try again or use /help."
                )
        
        elif result and result.get("status") == "success" and result.get("result"):
            reply_text = result.get("result")
            
            # Translate outgoing response to user's language
            if preferred_language != "en" and reply_text:
                try:
                    translated_reply = translate_text_sync(reply_text, preferred_language)
                    if translated_reply and translated_reply != reply_text:
                        reply_text = translated_reply
                        log.info(f"🔁 Translated reply to {preferred_language}")
                except Exception as t_e:
                    log.warning(f"Final translation failed: {t_e}")
            
            # Send reply
            await update.message.reply_text(reply_text)
        
    except Exception as e:
        log.error(f"❌ Error handling message: {str(e)}")
        import traceback
        traceback.print_exc()
        
        await update.message.reply_text(
            "Sorry, I encountered an error processing your message. "
            "Our technical team has been notified. Please try again or use /help."
        )




# Add this new handler for photos BEFORE the message handler
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages with medical image analysis"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    profile, _ = await ensure_user_profile(user)
    preferred_language = profile.get("preferred_language", "en")
    
    log.info(f"📷 Photo received from {telegram_id}")
    
    try:
        # Send typing indicator
        await update.message.chat.send_action("typing")
        
        # Get the photo file
        photo = update.message.photo[-1]  # Get highest resolution
        file = await context.bot.get_file(photo.file_id)
        
        # Download to temporary file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        # Download file to disk
        await file.download_to_drive(tmp_path)
        
        log.info(f"🖼️ Downloaded image to: {tmp_path}")
        log.info(f"🖼️ Analyzing medical image from {telegram_id}...")
        
        # Analyze image
        analysis = await analyze_medical_image(tmp_path, preferred_language)
        
        log.info(f"✅ Analysis result: {analysis[:100]}...")
        
        # Translate if needed
        if preferred_language != "en" and analysis:
            try:
                from utils.translation import translate_text_sync
                translated = await translate_text_sync(analysis, preferred_language)
                if translated:
                    analysis = translated
                    log.info(f"✅ Translated analysis to {preferred_language}")
                else:
                    log.warning("Translation failed or empty — using original reply")
            except Exception as t_e:
                log.warning(f"Translation of image analysis failed: {t_e}")
        
        # Send response
        response_msg = f"SwasthAI: 🖼️ Medical Image Analysis\n\n{analysis}\n\n⚠️ Disclaimer: This is assistive analysis only, not a medical diagnosis. Always consult a healthcare professional."
        
        await update.message.reply_text(response_msg)
        log.info(f"✅ Image analysis sent to {telegram_id}")
        
    except Exception as e:
        log.error(f"❌ Error handling photo: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            "Sorry, I couldn't analyze the image. Please try again or describe your symptoms."
        )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages with speech-to-text and health response"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    profile, _ = await ensure_user_profile(user)
    preferred_language = profile.get("preferred_language", "en")
    
    log.info(f"🎤 Voice message received from {telegram_id}")
    
    ogg_path = None
    try:
        # Send typing indicator
        await update.message.chat.send_action("typing")
        
        # Get the voice file
        voice_file = update.message.voice
        file = await context.bot.get_file(voice_file.file_id)
        
        # Create unique temporary file path to avoid caching
        unique_id = str(uuid.uuid4())[:8]
        temp_dir = tempfile.gettempdir()
        ogg_path = os.path.join(temp_dir, f"voice_{telegram_id}_{unique_id}.ogg")
        
        log.info(f"🎤 Downloading voice to: {ogg_path}")
        
        # Save voice file
        await file.download_to_drive(ogg_path)
        
        if not os.path.exists(ogg_path):
            log.error(f"❌ Voice file download failed: {ogg_path}")
            await update.message.reply_text(
                "Sorry, I couldn't download the voice file. Please try again."
            )
            return
        
        log.info(f"✅ Voice file downloaded ({os.path.getsize(ogg_path)} bytes)")
        log.info(f"🎤 Transcribing voice from {telegram_id}...")
        
        # Transcribe audio
        transcription = await transcribe_audio(ogg_path)
        
        if not transcription or "failed" in transcription.lower() or "error" in transcription.lower():
            await update.message.reply_text(
                "Sorry, I couldn't transcribe the voice message. Please try again or type your symptoms."
            )
            return
        
        log.info(f"✅ Transcription: {transcription}")
        
        # Send transcription acknowledgment
        await update.message.reply_text(f"🎤 Transcribed: {transcription}")
        
        # Now process the transcribed text like a normal message
        # Ensure active session
        session = await ensure_active_session(telegram_id)
        
        session_data = {
            "session_id": session.id,
            "state": session.session_state,
            "context": session.context,
            "current_question": session.current_question,
            "symptoms_collected": session.symptoms_collected
        }
        
        if "history" not in context.user_data:
            context.user_data["history"] = []
        
        # Get health crew and process transcribed message
        health_crew = get_health_crew()
        
        log.info(f"🚀 Processing transcribed voice as message for {telegram_id}")
        
        result = await health_crew.process_user_message(
            message=transcription,
            telegram_id=telegram_id,
            session_data=session_data,
            conversation_history=context.user_data.get("history", []),
            language=preferred_language,
        )
        
        context.user_data["history"].append(f"User (voice): {transcription}")
        if len(context.user_data["history"]) > 10:
            context.user_data["history"] = context.user_data["history"][-10:]
        
        log.info(f"✅ Voice health assessment complete for {telegram_id}")
        
        # Handle result
        if result and result.get("status") == "success" and result.get("result"):
            reply_text = result.get("result")
            
            # Final translation
            if preferred_language != "en" and reply_text:
                try:
                    # ✅ NO AWAIT - translate_text_sync is synchronous
                    translated_reply = translate_text_sync(reply_text, preferred_language)
                    if translated_reply:
                        reply_text = translated_reply
                        log.info(f"✅ Translated reply to {preferred_language}")
                except Exception as t_e:
                    log.warning(f"Translation failed: {t_e}")
            
            await update.message.reply_text(reply_text)
        else:
            error_msg = result.get("error", "Unknown error") if result else "No response"
            log.error(f"❌ Health assessment failed: {error_msg}")
            await update.message.reply_text(
                "Sorry, I encountered an error processing your health assessment. Please try again."
            )
        
    except Exception as e:
        log.error(f"❌ Error handling voice: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            "Sorry, I couldn't process the voice message. Please try again."
        )
    finally:
        # Clean up OGG file
        if ogg_path and os.path.exists(ogg_path):
            try:
                os.remove(ogg_path)
                log.debug(f"🗑️ Cleaned up voice file: {ogg_path}")
            except Exception as cleanup_err:
                log.warning(f"Could not delete voice file: {cleanup_err}")


# Register handlers
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(CommandHandler("status", status_command))
telegram_app.add_handler(CommandHandler("test", test_command))
telegram_app.add_handler(CallbackQueryHandler(language_selection_handler, pattern="^lang_"))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
telegram_app.add_handler(MessageHandler(filters.VOICE, handle_voice))

@telegram_router.post("/telegram")
async def telegram_webhook(request: Request):
    """Telegram webhook endpoint"""
    try:
        data = await request.json()
        log.info(f"📥 Webhook received")
        
        # Create Update object
        update = Update.de_json(data, telegram_app.bot)
        
        # Process update
        await telegram_app.process_update(update)
        
        return {"status": "ok"}
        
    except Exception as e:
        log.error(f"❌ Webhook error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@telegram_router.get("/setup")
async def setup_webhook():
    """Setup Telegram webhook"""
    try:
        if not settings.WEBHOOK_URL:
            return {
                "status": "error",
                "message": "WEBHOOK_URL not configured in settings"
            }
        
        webhook_url = f"{settings.WEBHOOK_URL}/webhook/telegram"
        
        # Set webhook
        await telegram_app.bot.set_webhook(webhook_url)
        
        # Get webhook info
        webhook_info = await telegram_app.bot.get_webhook_info()
        
        log.info(f"✅ Webhook set to: {webhook_url}")
        
        return {
            "status": "success",
            "webhook_url": webhook_url,
            "webhook_info": {
                "url": webhook_info.url,
                "has_custom_certificate": webhook_info.has_custom_certificate,
                "pending_update_count": webhook_info.pending_update_count
            }
        }
        
    except Exception as e:
        log.error(f"❌ Error setting webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
