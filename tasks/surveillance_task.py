from crewai import Task
from typing import Optional
from utils import log
from config import settings
def create_surveillance_task(
    surveillance_agent,
    time_window_hours: int = 24,
    location_filter: Optional[str] = None,
    triggered_by: str = "scheduled"
) -> Task:
    """
    Task 3: Surveillance & Anomaly Detection Task
    
    Analyzes population-level symptom data to detect clusters and outbreaks.
    """
    
    task_description = f"""
    Conduct population-level epidemiological surveillance and anomaly detection.
    
    **Analysis Parameters:**
    - Time Window: Last {time_window_hours} hours
    - Location Filter: {location_filter if location_filter else "All locations"}
    - Triggered By: {triggered_by}
    - Anomaly Threshold: {settings.ANOMALY_THRESHOLD} cases
    - Analysis Timestamp: Current time
    
    **Your Epidemiological Analysis Protocol:**
    
    **PHASE 1: Data Collection**
    
    Use get_recent_symptoms tool to retrieve:
    - All symptom reports from last {time_window_hours} hours
    - Filter by location: {location_filter if location_filter else "No filter"}
    - Limit: 100 most recent records
    
    Expected data structure:
    ```
    {{
        "total_records": 45,
        "symptom_counts": {{"fever": 25, "cough": 18, "fatigue": 15}},
        "location_counts": {{"Mumbai": 18, "Pune": 12, "Thane": 8}},
        "risk_distribution": {{"critical": 1, "high": 4, "moderate": 13, "low": 27}}
    }}
    ```
    
    **PHASE 2: Baseline Statistical Analysis**
    
    Calculate population-level metrics:
    1. Total symptom reports in window
    2. Symptom frequency distribution
    3. Geographic distribution (cases per location)
    4. Risk level distribution
    5. Temporal patterns (if data available)
    
    Document baseline statistics:
    - Mean symptom count per type
    - Standard deviation across locations
    - Historical baseline (if available from previous runs)
    - Day-of-week and time-of-day patterns
    
    **PHASE 3: Anomaly Detection**
    
    **Method 1: Statistical Spike Detection (Symptom-Level)**
    
    For each symptom type, use detect_spike tool:
    ```
    detect_spike(
        symptom_data={{"fever": 25, "cough": 18, "fatigue": 15}},
        location_data={{"Mumbai": 18, "Pune": 12}},
        baseline_multiplier=2.5  # Threshold: mean + 2.5 × std_dev
    )
    ```
    
    Interpretation:
    - If count > (mean + 2.5 × std_dev) → FLAG as anomaly
    - Calculate anomaly_score = (observed - mean) / std_dev
    - Anomaly score > 3.0 → HIGH concern
    - Anomaly score 2.0-3.0 → MODERATE concern
    - Anomaly score < 2.0 → LOW concern or normal variation
    
    **Method 2: Geographic Clustering Detection**
    
    For each location with reports:
    - Compare to mean case count across all locations
    - Flag locations with count > (mean + 2.5 × std_dev)
    - Identify geographic hotspots
    - Calculate concentration ratio: cases_in_location / total_cases
    - If >40% of cases in single location → Geographic cluster alert
    
    **Method 3: Symptom Correlation Analysis**
    
    Use compute_symptom_correlation tool:
    - Detect unusual symptom combinations
    - Calculate co-occurrence rates
    - Compare observed vs expected correlation
    - Flag correlation_score > 1.5× expected
    
    Example concerning combinations:
    - Fever + Cough + Breathing Difficulty (respiratory cluster)
    - Vomiting + Diarrhea + Fever (gastro outbreak)
    - Fever + Rash + Joint Pain (vector-borne disease)
    
    **PHASE 4: Clinical Relevance Assessment**
    
    Evaluate detected anomalies for public health significance:
    
    **HIGH CLINICAL CONCERN (Escalation Required):**
    - Respiratory symptom cluster: fever + cough + breathing difficulty
    - Geographic concentration: >5 cases in single area within 24h
    - Rapid spike: >50% increase from previous window
    - Critical/high risk cases clustering
    - Novel or unusual symptom combinations
    - Multiple moderate concerns occurring simultaneously
    
    **MODERATE CLINICAL CONCERN (Monitor Closely):**
    - Single symptom spike without clustering
    - Gradual increase over multiple days
    - Seasonal pattern deviation
    - 3-5 cases in single location
    - Known endemic disease patterns
    
    **LOW CLINICAL CONCERN (Document Only):**
    - Minor fluctuations within normal range
    - Isolated cases without pattern
    - Expected seasonal variations
    - Non-infectious symptom reports
    
    **PHASE 5: Escalation Decision Logic**
    
    Generate escalation signal when ANY of these conditions met:
    
    ✅ **Escalate if:**
    - Anomaly score > 3.0 for any symptom
    - Geographic cluster with ≥{settings.ANOMALY_THRESHOLD} cases in single location
    - High-concern symptom combination detected
    - Critical/high risk distribution >20% of total cases
    - Rapid increase: >50% growth compared to previous window
    - Multiple moderate concerns (≥3) occurring together
    
    ❌ **Do NOT escalate if:**
    - Total reports < 10 (insufficient sample size)
    - Only low-risk cases
    - Known reporting artifact (campaign, awareness event)
    - Single isolated case
    - Normal seasonal pattern
    
    **PHASE 6: Generate Surveillance Report**
    
    Create comprehensive analysis report:
    ```
    {{
        "analysis_timestamp": "2025-11-18T14:00:00Z",
        "time_window_hours": {time_window_hours},
        "total_reports": 45,
        "sample_size_adequate": true,  # ≥10 reports
        
        "descriptive_statistics": {{
            "symptom_counts": {{"fever": 25, "cough": 18, "fatigue": 15}},
            "location_counts": {{"Mumbai": 18, "Thane": 7, "Pune": 5}},
            "risk_distribution": {{"critical": 1, "high": 4, "moderate": 13, "low": 27}},
            "mean_symptom_count": 12.7,
            "std_dev_symptom_count": 8.3
        }},
        
        "anomalies_detected": [
            {{
                "type": "symptom_spike",
                "symptom": "fever",
                "observed_count": 25,
                "expected_count": 12,
                "anomaly_score": 3.8,
                "severity": "high",
                "geographic_distribution": {{"Mumbai": 18, "Thane": 7}},
                "clinical_concern": "HIGH - Respiratory illness cluster"
            }},
            {{
                "type": "location_cluster",
                "location": "Mumbai",
                "case_count": 18,
                "percentage_of_total": 40.0,
                "dominant_symptoms": ["fever", "cough", "fatigue"],
                "risk_concentration": {{"high": 3, "moderate": 10, "low": 5}},
                "clinical_concern": "HIGH - Geographic clustering"
            }}
        ],
        
        "symptom_correlations": [
            {{
                "symptoms": ["fever", "cough"],
                "co_occurrence_count": 15,
                "correlation_score": 2.1,
                "interpretation": "Respiratory illness pattern"
            }}
        ],
        
        "escalation_required": true,
        "escalation_reason": "Fever spike (score: 3.8) with geographic clustering in Mumbai (18 cases, 40% of total). Respiratory symptom correlation detected.",
        "escalation_severity": "high",  # critical/high/moderate
        
        "recommendations": [
            "Issue community health alert for Mumbai area",
            "Notify mock health authorities of potential outbreak",
            "Increase surveillance frequency to 6-hour windows",
            "Request enhanced reporting from Mumbai healthcare facilities",
            "Monitor for additional respiratory symptom reports",
            "Consider geographic expansion of monitoring to adjacent areas"
        ],
        
        "confidence_level": "high",  # high/medium/low
        "data_quality_notes": "Adequate sample size. Geographic data complete. Risk stratification complete.",
        
        "follow_up_actions": [
            "Alert Agent: Dispatch community alert for Mumbai",
            "Alert Agent: Submit report to mock authority",
            "Coordinator: Schedule next surveillance in 6 hours",
            "Coordinator: Flag Mumbai users for proactive follow-up"
        ]
    }}
    ```
    
    **PHASE 7: Alert Generation (If Escalation Required)**
    
    If escalation_required == true:
    - Use write_alert_log tool to record the alert
    - Return escalation signal to Coordinator
    - Coordinator will delegate to Alert Agent
    
    Alert log structure:
    ```
    write_alert_log(
        alert_type="symptom_cluster",  # cluster/spike/outbreak
        severity="high",  # critical/high/moderate/low
        title="Fever Cluster Detected - Mumbai",
        message="18 fever cases detected in Mumbai in last 24h. Respiratory symptoms present.",
        affected_location="Mumbai, Maharashtra",
        affected_symptoms=["fever", "cough"],
        case_count=18,
        anomaly_score=3.8
    )
    ```
    
    **PHASE 8: Continuous Monitoring Recommendations**
    
    Provide guidance for next surveillance cycle:
    - If anomaly detected: Increase frequency (6-12h windows)
    - If normal patterns: Maintain current frequency (24h windows)
    - If outbreak confirmed: Continuous monitoring (1-3h windows)
    
    **Statistical Best Practices:**
    
    ⚠️ **Important Considerations:**
    - Require minimum 10 reports before anomaly detection
    - Account for day-of-week patterns (weekends may have fewer reports)
    - Consider time-of-day reporting patterns
    - Watch for data quality issues (batch uploads, system tests)
    - Cross-validate anomalies across multiple detection methods
    - Prioritize recent data over older reports
    - Document all assumptions and limitations
    
    **False Positive Mitigation:**
    - Confirm spikes persist across multiple windows
    - Verify geographic clustering isn't population density artifact
    - Check for reporting campaigns or awareness events
    - Look for alternative explanations
    - Require multiple indicators before escalation
    
    **Output Required:**
    Deliver comprehensive surveillance report with:
    1. Complete statistical analysis
    2. All detected anomalies with scores
    3. Clinical significance assessment
    4. Escalation decision with reasoning
    5. Specific recommendations
    6. Alert log reference (if escalated)
    7. Next surveillance schedule
    8. Confidence and data quality metrics
    """
    
    task = Task(
        description=task_description,
        agent=surveillance_agent,
        expected_output="""
        A comprehensive epidemiological surveillance report containing:
        1. Time window and parameters used
        2. Total records analyzed with quality metrics
        3. Descriptive statistics (symptom counts, location distribution, risk levels)
        4. Detected anomalies with anomaly scores
        5. Geographic clustering analysis
        6. Symptom correlation analysis
        7. Clinical significance assessment for each finding
        8. Escalation decision (true/false) with detailed reasoning
        9. Specific, actionable recommendations
        10. Alert log ID (if escalation triggered)
        11. Follow-up actions for Coordinator and Alert Agent
        12. Next surveillance schedule recommendation
        13. Confidence level and data quality notes
        """,
        async_execution=False  # Sequential to ensure data consistency
    )
    
    log.info(f"Created surveillance task for {time_window_hours}h window, location: {location_filter}")
    return task
