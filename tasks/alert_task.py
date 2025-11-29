from crewai import Task
from typing import Dict, List, Any
from utils import log
from builtins import str, bool, int, float, dict, list,len

def create_alert_task(
    alert_agent,
    escalation_signal: Dict[str, Any],
    affected_users: List[str] = None,
    broadcast_community: bool = False
) -> Task:
    """
    Task 4: Alert & Communication Task
    
    Generates and dispatches health alerts to users, communities, and authorities.
    """
    
    task_description = f"""
    Generate and dispatch health alerts based on surveillance escalation signal.
    
    **Escalation Details:**
    {escalation_signal}
    
    **Target Audiences:**
    - Affected Users: {len(affected_users) if affected_users else 0} individuals
    - Community Broadcast: {"Yes" if broadcast_community else "No"}
    - Health Authorities: Yes (mock submission)
    
    **Your Crisis Communication Protocol:**
    
    **PHASE 1: Escalation Assessment**
    
    Analyze the surveillance escalation signal:
    - Alert Type: {escalation_signal.get('alert_type', 'unknown')}
    - Severity: {escalation_signal.get('severity', 'moderate')}
    - Location: {escalation_signal.get('affected_location', 'multiple')}
    - Case Count: {escalation_signal.get('case_count', 0)}
    - Symptoms: {escalation_signal.get('affected_symptoms', [])}
    - Anomaly Score: {escalation_signal.get('anomaly_score', 0)}
    
    Determine communication urgency:
    - **CRITICAL**: Immediate threat, life-safety concern
    - **HIGH**: Significant health risk, prompt action needed
    - **MODERATE**: Emerging concern, preventive action advisable
    - **LOW**: Awareness, informational only
    
    **PHASE 2: Audience Segmentation**
    
    Identify three target audiences:
    
    **A. Individual High-Risk Users**
    - Users in affected geographic area
    - Users reporting similar symptoms
    - Users with high/critical risk assessments
    - Users requiring follow-up
    
    **B. Community (Broadcast)**
    - All users subscribed to health alerts
    - Users in affected location + adjacent areas
    - Community health workers
    - Local organizations
    
    **C. Health Authorities (Mock)**
    - Government health department
    - Disease surveillance system
    - Emergency response coordinators
    - Public health officials
    
    **PHASE 3: Message Composition**
    
    Craft appropriate messages for each audience following these templates:
    
    **TEMPLATE A: Individual High-Risk User Alert**
    ```
    🏥 Personal Health Alert
    
    Hello [Name],
    
    We've detected [symptom] reports in your area ([Location]).
    
    📊 Current Situation:
    - [X] similar cases in your vicinity
    - Symptoms: [list symptoms]
    - Time period: Last [X] hours
    
    ⚠️ Your Status: [Risk Level from previous triage]
    
    ✅ What You Should Do:
    1. Monitor your symptoms closely
    2. [Specific actions based on their symptoms]
    3. Avoid crowded areas if possible
    4. Practice good hygiene (masks, handwashing)
    5. Report any worsening symptoms immediately
    
    📞 Seek Immediate Care If:
    - Difficulty breathing develops
    - Symptoms rapidly worsen
    - New severe symptoms appear
    - You feel seriously unwell
    
    We're monitoring the situation and will update you.
    
    Reply /status for health check
    Emergency: Call 108/112
    
    Stay safe! 🙏
    ```
    
    **TEMPLATE B: Community Health Advisory (Severity: HIGH)**
    ```
    ⚠️ COMMUNITY HEALTH ALERT - {{location}}
    
    We've detected an increase in {{primary_symptom}} reports in {{specific_area}}.
    
    📊 Current Situation:
    - {{case_count}} cases reported in last 24 hours
    - Affected area: {{location}}
    - Primary symptoms: {{symptom_list}}
    - Risk level: {{severity}}
    
    🛡️ Protective Actions for Everyone:
    1. Monitor your health for: {{symptom_list}}
    2. Practice respiratory hygiene:
       -  Wear masks in crowded places
       -  Cover coughs and sneezes
       -  Wash hands frequently
    3. Maintain social distance when possible
    4. Avoid large gatherings if symptomatic
    5. Stay home if you feel unwell
    6. Report any symptoms via this bot: /report
    
    📍 If You Live in {{location}}:
    - Be extra vigilant about symptoms
    - Consider avoiding non-essential outings
    - Keep emergency contacts handy
    - Follow local health department guidance
    
    ⚠️ Seek Medical Care If You Have:
    - Fever with difficulty breathing
    - Severe persistent symptoms
    - Rapidly worsening condition
    - Any emergency symptoms
    
    📞 Emergency Contacts:
    - Emergency: 108 / 112
    - Local Health Center: [number]
    - SwasthAI Support: /help
    
    **This is a precautionary alert to help our community stay healthy.**
    
    We're actively monitoring the situation. Updates will follow.
    
    Stay informed -  Stay safe -  Stay connected 🙏
    
    Report symptoms: /start
    Get updates: /alerts on
    ```
    
    **TEMPLATE C: Critical Outbreak Alert (Severity: CRITICAL)**
    ```
    🚨 URGENT HEALTH ALERT - {{location}}
    
    ⚠️ IMMEDIATE ACTION REQUIRED ⚠️
    
    A significant health cluster has been detected in {{location}}.
    
    🚨 SITUATION:
    - Suspected outbreak: {{symptom_type}} illness
    - {{case_count}} confirmed reports
    - Location: {{specific_area}}
    - Status: HIGH TRANSMISSION RISK
    
    🛑 WHAT TO DO RIGHT NOW:
    
    IF YOU HAVE SYMPTOMS:
    1. Stay home immediately
    2. Call health helpline: [number]
    3. Wear a mask
    4. Isolate from household members
    5. DO NOT go to work/school
    
    IF YOU LIVE IN {{location}}:
    1. Minimize outdoor activities
    2. Wear masks in all public spaces
    3. Avoid gatherings of any size
    4. Stock essential supplies
    5. Follow official health guidance
    
    EVERYONE SHOULD:
    1. Monitor health closely
    2. Practice strict hygiene
    3. Maintain physical distance
    4. Report symptoms immediately
    5. Stay informed via official channels
    
    📞 EMERGENCY CONTACTS:
    - Medical Emergency: 108 / 112
    - Health Helpline: [number]
    - SwasthAI: /emergency
    
    🏥 Nearest Healthcare Facilities:
    [List of facilities]
    
    **THIS IS NOT A DRILL**
    Take immediate protective action.
    
    More updates coming. Stay alert and stay safe. 🙏
    
    Report NOW: /start
    ```
    
    **TEMPLATE D: Mock Government Authority Report**
    ```
    {{
        "alert_id": "SWASTHAI-{{timestamp}}",
        "alert_type": "{{alert_type}}",
        "severity": "{{severity}}",
        "detected_at": "{{iso_timestamp}}",
        "reporting_system": "SwasthAI Autonomous Health Intelligence Network",
        
        "location": {{
            "city": "{{city}}",
            "state": "{{state}}",
            "district": "{{district}}",
            "coordinates": "{{lat}}, {{lon}}"
        }},
        
        "epidemiological_data": {{
            "total_cases": {{case_count}},
            "time_window_hours": 24,
            "dominant_symptoms": ["{{symptom1}}", "{{symptom2}}"],
            "symptom_onset_range": "{{onset_range}}",
            "age_distribution": "Mixed ages",
            "gender_distribution": "Mixed",
            "severity_distribution": {{
                "critical": {{critical_count}},
                "high": {{high_count}},
                "moderate": {{moderate_count}},
                "low": {{low_count}}
            }},
            "risk_concentration": "{{percentage}}% in single location"
        }},
        
        "statistical_analysis": {{
            "anomaly_score": {{anomaly_score}},
            "statistical_significance": "p < 0.01",
            "detection_method": "Moving-window statistical analysis",
            "baseline_threshold": "mean + 2.5 × std_dev",
            "geographic_clustering": true,
            "temporal_pattern": "Rapid increase over 24h",
            "symptom_correlation": "High co-occurrence: fever + cough"
        }},
        
        "clinical_assessment": {{
            "suspected_illness_type": "Respiratory illness cluster",
            "transmission_risk": "HIGH",
            "outbreak_potential": "MODERATE-HIGH",
            "public_health_significance": "Requires immediate investigation",
            "recommended_classification": "Suspected Local Outbreak"
        }},
        
        "response_recommendations": [
            "Deploy rapid response team to {{location}}",
            "Conduct active case finding in affected neighborhoods",
            "Implement enhanced surveillance (6-hour monitoring windows)",
            "Consider public health advisory issuance",
            "Arrange laboratory testing for outbreak etiology determination",
            "Establish communication with local healthcare facilities",
            "Activate community health worker network",
            "Prepare for potential cluster investigation"
        ],
        
        "data_source": {{
            "system": "SwasthAI Community Health Surveillance Network",
            "data_collection": "Autonomous AI-driven symptom reporting via Telegram",
            "coverage": "Community-based participatory surveillance",
            "data_quality": "Real-time, geo-tagged, risk-stratified",
            "validation": "AI agent triage with clinical reasoning"
        }},
        
        "contact": {{
            "system": "SwasthAI Coordinator Agent",
            "email": "coordinator@swasthai.health",
            "emergency": "available 24/7",
            "api_endpoint": "api.swasthai.health/alerts"
        }},
        
        "attachments": {{
            "detailed_case_list": "Available upon request",
            "geographic_heatmap": "Available upon request",
            "symptom_timeline": "Available upon request",
            "risk_assessment_matrix": "Available upon request"
        }},
        
        "compliance": {{
            "data_privacy": "DPDP Act 2023 compliant",
            "consent": "User consent obtained for health data sharing",
            "anonymization": "Personal identifiers removed from authority reports",
            "audit_trail": "Complete decision log maintained"
        }}
    }}
    ```
    
    **PHASE 4: Message Formatting & Delivery**
    
    **For Individual Users:**
    - Use send_telegram_message tool
    - Personalize with user's name (if available)
    - Reference their specific symptoms/status
    - Include their risk level
    - Provide specific actionable guidance
    - Send individually to maintain privacy
    
    **For Community Broadcast:**
    - Use broadcast_telegram_message tool
    - Send to all users in affected location
    - Include clear geographic boundaries
    - Provide general preventive guidance
    - Use reassuring but alert tone
    - Include multiple contact options
    
    **For Health Authorities:**
    - Use submit_to_mock_authority tool
    - Format as structured JSON report
    - Include all epidemiological data
    - Provide statistical analysis
    - List specific recommendations
    - Include contact information
    
    **PHASE 5: Alert Logging & Audit Trail**
    
    For every alert dispatched, use write_alert_log tool:
    ```
    write_alert_log(
        alert_type="{{cluster/spike/outbreak}}",
        severity="{{critical/high/moderate/low}}",
        title="Brief descriptive title",
        message="Full message text sent",
        affected_location="{{city, state}}",
        affected_symptoms=[list],
        case_count=X,
        anomaly_score=X.X
    )
    ```
    
    **PHASE 6: Communication Principles**
    
    All messages must follow these guidelines:
    
    **Clarity:**
    - Use simple, direct language (8th-grade reading level)
    - Avoid medical jargon
    - Provide specific actions, not vague advice
    - Use bullet points for scannability
    - Include only essential information
    
    **Accuracy:**
    - State only verified facts
    - Cite data sources
    - Include timestamps
    - Specify geographic boundaries clearly
    - Provide context (not just numbers)
    
    **Empathy:**
    - Acknowledge concern and anxiety
    - Use supportive language
    - Provide reassurance where appropriate
    - Offer multiple support options
    - Maintain respectful tone
    
    **Cultural Sensitivity:**
    - Use inclusive language
    - Avoid stigmatizing language
    - Consider local customs and norms
    - Respect privacy
    - No blame or judgment
    
    **Actionability:**
    - Every alert must have clear next steps
    - Provide specific, achievable actions
    - Include contact information
    - Offer support resources
    - Enable user response/feedback
    
    **Urgency Calibration:**
    - Match tone to severity
    - Use visual indicators (emojis) appropriately
    - Critical alerts: Direct commands ("Do this NOW")
    - High alerts: Strong recommendations ("You should...")
    - Moderate alerts: Advisory ("Consider...")
    - Low alerts: Informational ("Be aware...")
    
    **PHASE 7: Delivery Confirmation & Follow-up**
    
    After dispatching all messages:
    1. Count successful deliveries
    2. Note any failures
    3. Log all dispatches
    4. Confirm to Coordinator
    5. Schedule follow-up if needed
    
    Return summary:
    - Individual alerts sent: X/Y successful
    - Community broadcast sent: Yes/No
    - Authority notification sent: Yes/No
    - Alert log IDs: [list]
    - Any delivery failures: [details]
    
    **Emergency Escalation:**
    If alert is CRITICAL severity:
    - Send immediately, no delays
    - Use all available channels
    - Flag for coordinator attention
    - Consider multiple reminder messages
    - Prioritize delivery over optimization
    
    **Output Required:**
    Provide complete alert dispatch report with:
    1. All messages composed (full text)
    2. Audience targeting decisions
    3. Delivery method per audience
    4. Message customization details
    5. Dispatch confirmations
    6. Alert log references
    7. Authority submission confirmation
    8. Success/failure metrics
    9. Follow-up requirements
    10. Recommendations for Coordinator
    """
    
    task = Task(
        description=task_description,
        agent=alert_agent,
        expected_output="""
        A comprehensive alert dispatch report containing:
        1. Escalation assessment and urgency determination
        2. Audience segmentation strategy
        3. Full message text for each audience type (individual, community, authority)
        4. Delivery confirmations with success metrics
        5. Alert log IDs for audit trail
        6. Mock authority submission ID
        7. Any delivery failures or issues
        8. Follow-up recommendations
        9. Communication effectiveness notes
        10. Next steps for Coordinator
        """,
        async_execution=False  # Sequential to ensure message delivery
    )
    
    log.info(f"Created alert task for {escalation_signal.get('alert_type')} alert")
    return task
