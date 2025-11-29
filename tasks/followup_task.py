from crewai import Task
from typing import Dict, Any
from utils import log


def create_followup_task(
    coordinator_agent,
    triage_agent,
    user_id: str,
    telegram_id: str,
    previous_assessment: Dict[str, Any],
    followup_type: str = "scheduled"
) -> Task:
    """
    Task 5: Follow-up Scheduling and Re-evaluation Task
    
    Manages time-based re-evaluation of high-risk cases.
    """
    
    task_description = f"""
    Conduct follow-up health check for user requiring re-evaluation.
    
    **User Information:**
    - User ID: {user_id}
    - Telegram ID: {telegram_id}
    - Follow-up Type: {followup_type}
    
    **Previous Assessment:**
    {previous_assessment}
    
    **Your Follow-up Care Protocol:**
    
    **PHASE 1: Context Review**
    
    Use get_user_session tool to retrieve:
    - Previous symptom reports
    - Last triage assessment
    - Risk level from previous evaluation
    - Symptoms reported initially
    - Recommendations provided
    - Time since last assessment
    
    Review previous assessment details:
    - Original symptoms: {previous_assessment.get('symptoms', [])}
    - Original risk level: {previous_assessment.get('risk_level', 'unknown')}
    - Original severity score: {previous_assessment.get('severity_score', 0)}
    - Date of last assessment: {previous_assessment.get('reported_at', 'unknown')}
    - Recommendations given: {previous_assessment.get('recommendations', [])}
    
    **PHASE 2: Follow-up Message Initiation**
    
    Send appropriate follow-up message using send_telegram_message tool:
    
    **For High-Risk Follow-up (within 12-24h):**
    ```
    🏥 Health Check-In
    
    Hello! We're following up on your health status.
    
    📋 Last Report: {{hours_ago}} hours ago
    You reported: {{symptom_list}}
    Risk Level: {{risk_level}}
    
    **How are you feeling now?**
    
    Please let us know:
    1. Are your symptoms better, same, or worse?
    2. Any new symptoms?
    3. Have you sought medical care?
    4. Current temperature (if you had fever)?
    
    Your health is important to us. Please respond so we can help. 🙏
    
    Reply here with your update.
    Emergency: Call 108/112
    ```
    
    **For Moderate-Risk Follow-up (24-48h):**
    ```
    👋 Health Check-In
    
    Hi! Time for your scheduled health check.
    
    📋 Last time you reported: {{symptom_list}}
    
    **Quick Update:**
    - How are you feeling now?
    - Are your symptoms improving?
    - Do you have any concerns?
    
    Please share a brief update on your health.
    
    Thanks for keeping us informed! 🌟
    ```
    
    **For Low-Risk Follow-up (48-72h):**
    ```
    ✅ Health Check-In
    
    Hope you're feeling better!
    
    You reported {{symptom_list}} {{days_ago}} days ago.
    
    **Quick question:**
    Are you fully recovered? Please reply:
    - Yes, feeling much better
    - Still have some symptoms
    - Need to report new concerns
    
    Thank you! 🙏
    ```
    
    **PHASE 3: Response Handling**
    
    This task sends the follow-up message and then:
    
    **Option A: User Responds Promptly**
    - Message sent successfully
    - Update session state to "awaiting_followup_response"
    - Set flag for Coordinator to route response to Triage Agent
    - Triage Agent will conduct new assessment when response received
    
    **Option B: No Response After 4 Hours (High-Risk Cases Only)**
    - Send reminder message:
    ```
    ⚠️ Health Check Reminder
    
    We haven't heard back from you regarding your health status.
    
    We're concerned and want to make sure you're okay.
    
    Please send a quick update:
    - How are you feeling?
    - Any changes in symptoms?
    - Do you need help?
    
    Your wellbeing matters. Please respond. 🙏
    
    Emergency: 108/112
    ```
    
    **Option C: No Response After 12 Hours (Critical Cases)**
    - Escalate to Alert Agent for welfare check
    - Consider local health worker notification (if integrated)
    - Flag for coordinator priority attention
    
    **PHASE 4: Re-assessment Preparation**
    
    When user responds:
    1. Update session with new user message
    2. Prepare context for Triage Agent:
       - Previous symptoms for comparison
       - Timeline of symptom evolution
       - Previous risk level
       - Previous recommendations
       - Current follow-up response
    
    3. Delegate to Triage Agent for new assessment
    
    **PHASE 5: Comparative Analysis**
    
    Triage Agent should compare new assessment to previous:
    
    **Symptom Evolution Patterns:**
    
    **IMPROVING (Positive Progression):**
    - Fewer symptoms than before
    - Lower severity scores
    - Symptom resolution reported
    - User feels better
    - No new concerning symptoms
    
    **Action:**
    - Continue monitoring if not fully recovered
    - Extend follow-up interval (48-72h)
    - Provide positive reinforcement
    - Recommend completion of recovery protocol
    - May close case if fully recovered
    
    **STABLE (No Change):**
    - Same symptoms persisting
    - Similar severity levels
    - No improvement, but not worsening
    - Duration now concerning
    
    **Action:**
    - Recommend medical evaluation (if not done)
    - Maintain current follow-up frequency
    - Provide additional guidance
    - Consider escalation if prolonged (>5-7 days)
    - May need investigation for chronic conditions
    
    **WORSENING (Negative Progression):**
    - New symptoms developed
    - Increased severity
    - Spread of symptoms (e.g., cough → breathing difficulty)
    - User reports feeling worse
    - Red flag symptoms emerging
    
    **Action:**
    - IMMEDIATE escalation to higher risk category
    - Recommend urgent medical care
    - Shorten follow-up interval (6-12h)
    - Send specific warning about concerning progression
    - May trigger community surveillance check
    - Flag for Alert Agent if part of cluster
    
    **NEW CONCERNS:**
    - Completely different symptoms
    - May indicate:
      * New illness (not related to original)
      * Complication of original illness
      * Misdiagnosis of original symptoms
    
    **Action:**
    - Conduct fresh triage assessment
    - Treat as new case while maintaining history
    - Compare patterns with community data
    - May indicate disease progression
    
    **PHASE 6: Follow-up Outcome Documentation**
    
    Create new health record with comparative data:
    ```
    {{
        "telegram_id": "{telegram_id}",
        "symptoms": ["updated symptom list"],
        "symptom_details": {{...}},
        "risk_level": "updated_risk_level",
        "severity_score": updated_score,
        "location": "same or updated",
        "agent_assessment": "Comparison to previous assessment. 
                           Previous: [fever, cough] severity 6.5. 
                           Current: [cough only] severity 3.0. 
                           PROGRESSION: Improving. Fever resolved, cough decreasing. 
                           Recommend continued rest and monitoring.",
        "recommendations": ["updated recommendations"],
        "requires_followup": true/false,
        "followup_hours": 24/48/72 or null,
        "previous_record_id": {{previous_record_id}},
        "followup_number": 1/2/3,  # Track how many follow-ups
        "progression_status": "improving/stable/worsening"
    }}
    ```
    
    **PHASE 7: Communication of Follow-up Results**
    
    Send appropriate response based on progression:
    
    **If Improving:**
    ```
    ✅ Great News!
    
    Your symptoms are showing improvement! 
    
    📊 Comparison:
    - Before: {{previous_symptoms}} (Risk: {{prev_risk}})
    - Now: {{current_symptoms}} (Risk: {{current_risk}})
    
    ✅ You're on the right track! Keep:
    {{recommendations}}
    
    {{If fully recovered:}}
    You seem to be recovering well! We'll check once more in {{hours}} hours to confirm full recovery.
    
    {{If partially recovered:}}
    Continue following the recommendations. We'll check again in {{hours}} hours.
    
    Feel free to reach out anytime. Get well soon! 🌟
    ```
    
    **If Stable (No Improvement):**
    ```
    📋 Follow-up Assessment
    
    Your symptoms haven't changed much since last time.
    
    📊 Status:
    - Symptoms: {{symptom_list}}
    - Duration: {{days}} days now
    - Risk: {{risk_level}}
    
    ⚠️ Since your symptoms persist, we recommend:
    - Consult a healthcare provider for evaluation
    - Continue current care practices
    - Monitor for any changes
    
    Persistent symptoms may need professional assessment.
    
    We'll check in again in {{hours}} hours. Stay safe! 🙏
    ```
    
    **If Worsening:**
    ```
    🚨 Important Update
    
    Your symptoms appear to be worsening.
    
    📊 Comparison:
    - Before: {{previous_symptoms}}
    - Now: {{current_symptoms}} + {{new_symptoms}}
    - Risk Level: INCREASED to {{new_risk_level}}
    
    ⚠️ IMMEDIATE ACTIONS NEEDED:
    1. Seek medical care as soon as possible
    2. {{Specific urgent recommendations}}
    3. Call emergency services if symptoms become severe
    
    🏥 Please don't delay getting medical help.
    
    📞 Emergency: 108/112
    
    We'll check on you again in {{short_interval}} hours. 
    Please respond so we know you're okay. 🙏
    ```
    
    **PHASE 8: Follow-up Cycle Management**
    
    Decision logic for continued follow-ups:
    
    **Close Case When:**
    - User reports full recovery
    - All symptoms resolved
    - Risk level returned to "low"
    - User confirms feeling well
    - 2-3 days symptom-free
    
    **Continue Follow-up When:**
    - Symptoms still present (any severity)
    - User still in moderate/high risk
    - Improvement but not complete recovery
    - User requests continued monitoring
    
    **Escalate When:**
    - Symptoms worsening
    - New red flags emerge
    - Part of geographic cluster
    - Duration exceeds expected (>7 days)
    - User non-responsive (high-risk cases)
    
    **PHASE 9: Session and System Updates**
    
    Use update_session tool to:
    - Record follow-up completion
    - Update session state
    - Increment follow-up counter
    - Log progression status
    - Schedule next follow-up (if needed)
    - Close session (if recovery complete)
    
    Notify Coordinator:
    - Follow-up completed
    - New risk assessment
    - Progression status (improving/stable/worsening)
    - Whether continued follow-up needed
    - If escalation required
    - If case can be closed
    
    **PHASE 10: Surveillance Integration**
    
    If symptoms worsening or persisting:
    - Coordinator should trigger Surveillance Agent
    - Check if part of emerging cluster
    - Compare with recent community patterns
    - May indicate outbreak development
    
    **Best Practices:**
    
    **Timing:**
    - Send follow-ups at reasonable hours (9 AM - 9 PM)
    - Adjust for user's timezone
    - Allow 4-6 hours for response before reminders
    - Don't over-message (respect user's time)
    
    **Tone:**
    - Balance concern with encouragement
    - Celebrate improvements
    - Be supportive if no improvement
    - Be urgent but not alarmist if worsening
    - Always maintain empathy
    
    **Data Quality:**
    - Track comparative data for trends
    - Document timeline accurately
    - Note all symptom changes
    - Record adherence to recommendations
    - Maintain complete audit trail
    
    **Output Required:**
    Deliver comprehensive follow-up report with:
    1. Follow-up message sent (full text)
    2. User response (when received)
    3. Comparative analysis (previous vs current)
    4. Progression status (improving/stable/worsening)
    5. New health record created
    6. New risk assessment
    7. Updated recommendations
    8. Next follow-up scheduled (if applicable)
    9. Case closure decision (if recovery complete)
    10. Escalation flags (if needed)
    11. Surveillance trigger (if concerning patterns)
    12. Session update confirmation
    """
    
    task = Task(
        description=task_description,
        agent=coordinator_agent,  # Coordinator manages, delegates to Triage
        expected_output="""
        A complete follow-up care report containing:
        1. Follow-up message text sent to user
        2. Delivery confirmation
        3. Response tracking status
        4. Comparative symptom analysis (when response received)
        5. Progression assessment (improving/stable/worsening)
        6. New health record ID
        7. Updated risk level
        8. New recommendations provided
        9. Follow-up schedule decision (continue/close/escalate)
        10. Session update confirmation
        11. Coordinator action items
        12. Surveillance integration flag (if applicable)
        """,
        async_execution=False
    )
    
    log.info(f"Created follow-up task for user {telegram_id}, type: {followup_type}")
    return task
