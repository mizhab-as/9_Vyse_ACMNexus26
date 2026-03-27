"""
Clinical Prompt Engineering for NEXUS Pre-Arrival Triage Briefings

This module orchestrates Claude/GPT prompts to transform raw ML anomaly flags
into clinically-accurate, actionable pre-arrival briefings for ER teams.

The goal: Sound like an experienced paramedic giving handoff to an ER physician.
"""

import json
from typing import Dict, Optional

class ClinicalTriageBriefing:
    """
    Generates clinical-grade pre-arrival briefings from patient vitals and anomaly data.
    """

    # Medical decision rules
    SEPSIS_INDICATORS = {
        "fever": lambda v: v.get("temperature", 0) > 38.0,
        "tachycardia": lambda v: v.get("heart_rate", 0) > 90,
        "tachypnea": lambda v: v.get("respiratory_rate", 0) > 20,
        "hypotension": lambda v: v.get("systolic_bp", 0) < 100,
        "hypoxia": lambda v: v.get("oxygen_saturation", 0) < 95,
    }

    CARDIAC_INDICATORS = {
        "severe_tachycardia": lambda v: v.get("heart_rate", 0) > 120,
        "severe_hypotension": lambda v: v.get("systolic_bp", 0) < 90,
        "severe_hypoxia": lambda v: v.get("oxygen_saturation", 0) < 90,
    }

    RESP_DISTRESS = {
        "tachypnea": lambda v: v.get("respiratory_rate", 0) > 25,
        "hypoxia_severe": lambda v: v.get("oxygen_saturation", 0) < 90,
    }

    @staticmethod
    def detect_clinical_syndrome(vitals: Dict) -> Optional[str]:
        """
        Pattern matching for common pre-hospital emergency presentations.
        Returns: condition name or None
        """
        sepsis_count = sum(1 for _ , check in ClinicalTriageBriefing.SEPSIS_INDICATORS.items() if check(vitals))
        if sepsis_count >= 3:
            return "septic shock"

        cardiac_count = sum(1 for _, check in ClinicalTriageBriefing.CARDIAC_INDICATORS.items() if check(vitals))
        if cardiac_count >= 2:
            return "cardiogenic shock"

        resp_count = sum(1 for _, check in ClinicalTriageBriefing.RESP_DISTRESS.items() if check(vitals))
        if resp_count >= 2:
            return "respiratory distress"

        return None

    @staticmethod
    def generate_briefing(
        vitals: Dict,
        anomaly_score: float,
        alert_level: str,
        trend_text: str = ""
    ) -> str:
        """
        Generate clinical pre-arrival briefing without requiring LLM API call.
        Fallback when Claude API unavailable (useful for demos).
        """

        hr = vitals.get("heart_rate", 0)
        sbp = vitals.get("systolic_bp", 0)
        dbp = vitals.get("diastolic_bp", 0)
        rr = vitals.get("respiratory_rate", 0)
        o2 = vitals.get("oxygen_saturation", 0)
        temp = vitals.get("temperature", 0)

        syndrome = ClinicalTriageBriefing.detect_clinical_syndrome(vitals)

        # Build briefing from clinical template
        parts = []

        if alert_level == "CRITICAL":
            if syndrome == "septic shock":
                parts.append(f"Patient deteriorating with signs consistent with septic shock. HR {hr} bpm, SBP {sbp} mmHg, RR {rr}, fever {temp:.1f}°C.")
                parts.append("Initiate sepsis protocol on arrival: aggressive fluid resuscitation, blood cultures x2, lactate, CBC/CMP.")
                parts.append("Expedite to ICU. Notify attending immediately.")
            elif syndrome == "cardiogenic shock":
                parts.append(f"Acute hemodynamic deterioration. SBP {sbp}, HR {hr}, O2 {o2}%. Consider acute MI or decompensated HF.")
                parts.append("Prepare for continuous monitoring, establish IV access. Cardiology consult.")
            elif syndrome == "respiratory distress":
                parts.append(f"Acute respiratory compromise. RR {rr}, O2 sat {o2}%. Increased work of breathing.")
                parts.append("Prepare for possible intubation. High-flow O2 on arrival. Respiratory consult.")
            else:
                parts.append(f"Critical vitals: HR {hr}, BP {sbp}/{dbp}, RR {rr}, O2 {o2}%.")
                parts.append("Prepare for immediate assessment and intervention. ICU notification advised.")

        elif alert_level == "WARNING":
            parts.append(f"Early signs of deterioration. HR {hr} bpm, BP {sbp}/{dbp}, RR {rr}, O2 {o2}%.")
            parts.append("Prepare for enhanced monitoring. Have resuscitation equipment ready.")

        else:
            parts.append(f"Stable vitals. HR {hr}, BP {sbp}/{dbp}, RR {rr}, O2 {o2}%. Continue transport.")

        return " ".join(parts)

    @staticmethod
    def format_llm_prompt(vitals: Dict, anomaly_score: float, alert_level: str) -> str:
        """
        Create a well-structured prompt for Claude API (when available).
        """
        return f"""You are an expert emergency medicine physician. Provide a concise pre-arrival briefing (2-3 sentences) based on ambulance vitals.

Current Patient Vitals:
- Heart Rate: {vitals.get('heart_rate')} bpm
- Blood Pressure: {vitals.get('systolic_bp')}/{vitals.get('diastolic_bp')} mmHg
- Respiratory Rate: {vitals.get('respiratory_rate')} breaths/min
- O2 Saturation: {vitals.get('oxygen_saturation')}%
- Temperature: {vitals.get('temperature'):.1f}°C
- Anomaly Score: {anomaly_score:.2f}
- Alert Level: {alert_level}

Provide:
1. Likely clinical syndrome
2. Immediate preparation steps
3. Specific interventions needed

Format: Clinical, direct language. Max 3 sentences."""

# ============== Recommendations Engine ==============

class ActionRecommendations:
    """
    Maps clinical conditions to specific pre-arrival preparation actions.
    """

    ACTIONS_MAP = {
        "septic shock": [
            "Prepare 2L IV catheters and normal saline boluses",
            "Place on continuous cardiac monitoring and pulse oximetry",
            "Draw blood for cultures, CBC, CMP, lactate, blood gas",
            "Notify ICU for admission",
            "Prepare vasopressor ready (if indicated by vitals)"
        ],
        "cardiogenic shock": [
            "Place on continuous cardiac monitoring (12-lead ECG ready)",
            "Establish IV access (large bore catheter)",
            "Prepare for possible ACLS protocol",
            "Notify cardiology and ICU",
            "Prepare for echocardiography"
        ],
        "respiratory distress": [
            "Prepare bag-valve-mask and intubation equipment",
            "Place on high-flow oxygen system",
            "Prepare for possible emergency intubation",
            "Notify respiratory therapy",
            "Have mechanical ventilation ready"
        ],
        "default": [
            "Place on continuous monitoring",
            "Establish IV access",
            "Have resuscitation equipment at bedside",
            "Prepare for rapid assessment"
        ]
    }

    @staticmethod
    def get_actions(syndrome: Optional[str]) -> list:
        """Get recommended actions for detected syndrome."""
        if syndrome and syndrome in ActionRecommendations.ACTIONS_MAP:
            return ActionRecommendations.ACTIONS_MAP[syndrome]
        return ActionRecommendations.ACTIONS_MAP["default"]

# ============== Main Integration ==============

def generate_complete_briefing(vitals: Dict, anomaly_score: float, alert_level: str) -> Dict:
    """
    Complete briefing generation pipeline.
    Returns triage briefing object ready for frontend.
    """

    syndrome = ClinicalTriageBriefing.detect_clinical_syndrome(vitals)
    briefing_text = ClinicalTriageBriefing.generate_briefing(vitals, anomaly_score, alert_level)
    actions = ActionRecommendations.get_actions(syndrome)

    color_map = {
        "STABLE": "GREEN",
        "WARNING": "YELLOW",
        "CRITICAL": "RED"
    }

    return {
        "alert_level": alert_level,
        "color_code": color_map.get(alert_level, "YELLOW"),
        "syndrome": syndrome or "unspecified",
        "triage_briefing": briefing_text,
        "recommended_actions": actions,
        "confidence": 0.95 if syndrome else 0.75,
        "anomaly_score": float(anomaly_score)
    }


# ============== Testing ==============

if __name__ == "__main__":
    print("[TEST] Clinical Prompt Engineering\n")

    # Test 1: Normal vitals
    normal = {
        "heart_rate": 72,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "respiratory_rate": 16,
        "oxygen_saturation": 98,
        "temperature": 37.0
    }
    result = generate_complete_briefing(normal, 0.1, "STABLE")
    print(f"[NORMAL] Alert: {result['alert_level']}")
    print(f"  Briefing: {result['triage_briefing']}\n")

    # Test 2: Warning signs
    warning = {
        "heart_rate": 95,
        "systolic_bp": 105,
        "diastolic_bp": 65,
        "respiratory_rate": 20,
        "oxygen_saturation": 94,
        "temperature": 37.5
    }
    result = generate_complete_briefing(warning, 0.5, "WARNING")
    print(f"[WARNING] Syndrome: {result['syndrome']}")
    print(f"  Briefing: {result['triage_briefing']}\n")

    # Test 3: Critical sepsis
    sepsis = {
        "heart_rate": 110,
        "systolic_bp": 95,
        "diastolic_bp": 55,
        "respiratory_rate": 24,
        "oxygen_saturation": 92,
        "temperature": 39.2
    }
    result = generate_complete_briefing(sepsis, 0.9, "CRITICAL")
    print(f"[CRITICAL] Syndrome: {result['syndrome']}")
    print(f"  Briefing: {result['triage_briefing']}")
    print(f"  Actions: {result['recommended_actions']}")
