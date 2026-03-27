"""
Advanced Clinical Prompt Engineering for Triage Briefings

This module provides sophisticated LLM prompts that generate
clinically accurate, actionable, tone-perfect pre-arrival briefings.

Key: Briefings must sound like an experienced paramedic handing off to an ER physician,
not like an AI-generated document.
"""

from enum import Enum
from typing import Dict, Tuple

class ClinicalSyndrome(Enum):
    SEPSIS = "sepsis"
    CARDIOGENIC_SHOCK = "cardiogenic_shock"
    RESPIRATORY_DISTRESS = "respiratory_distress"
    HYPOVOLEMIC_SHOCK = "hypovolemic_shock"
    ANAPHYLAXIS = "anaphylaxis"
    STROKE = "acute_stroke"
    MI = "acute_mi"
    TRAUMA = "major_trauma"
    UNKNOWN = "unknown"

class AdvancedClinicalEngine:
    """
    Sophisticated pattern recognition for clinical syndromes.
    Uses multi-point criteria (like SIRS, qSOFA, etc.)
    """

    @staticmethod
    def detect_sepsis(vitals: Dict) -> Tuple[bool, float]:
        """SIRS + qSOFA criteria"""
        score = 0
        max_score = 5

        # SIRS criteria
        if vitals.get("temperature", 37) > 38.0 or vitals.get("temperature", 37) < 36.0:
            score += 1
        if vitals.get("heart_rate", 72) > 90:
            score += 1
        if vitals.get("respiratory_rate", 16) > 20:
            score += 1

        # Perfusion indicators
        if vitals.get("systolic_bp", 120) < 100:
            score += 1

        # Add hypoxia indicator
        if vitals.get("oxygen_saturation", 98) < 94:
            score += 1

        confidence = score / max_score
        return score >= 3, confidence

    @staticmethod
    def detect_cardiogenic_shock(vitals: Dict) -> Tuple[bool, float]:
        """Hypotension + hypoperfusion + pulmonary congestion signs"""
        score = 0
        max_score = 3

        if vitals.get("systolic_bp", 120) < 90:
            score += 1
        if vitals.get("heart_rate", 72) > 100:
            score += 1
        if vitals.get("oxygen_saturation", 98) < 94:
            score += 1

        confidence = score / max_score
        return score >= 2, confidence

    @staticmethod
    def detect_respiratory_distress(vitals: Dict) -> Tuple[bool, float]:
        """Tachypnea + hypoxia"""
        score = 0
        max_score = 2

        if vitals.get("respiratory_rate", 16) > 25:
            score += 1
        if vitals.get("oxygen_saturation", 98) < 94:
            score += 1

        confidence = score / max_score
        return score >= 1, confidence

    @staticmethod
    def classify_syndrome(vitals: Dict) -> Tuple[ClinicalSyndrome, float]:
        """
        Multi-level classification returning most likely syndrome with confidence.
        """

        sepsis, sep_conf = AdvancedClinicalEngine.detect_sepsis(vitals)
        cardiac, card_conf = AdvancedClinicalEngine.detect_cardiogenic_shock(vitals)
        respiratory, resp_conf = AdvancedClinicalEngine.detect_respiratory_distress(vitals)

        confidence_scores = {
            ClinicalSyndrome.SEPSIS: sep_conf if sepsis else 0,
            ClinicalSyndrome.CARDIOGENIC_SHOCK: card_conf if cardiac else 0,
            ClinicalSyndrome.RESPIRATORY_DISTRESS: resp_conf if respiratory else 0,
        }

        if all(v == 0 for v in confidence_scores.values()):
            return ClinicalSyndrome.UNKNOWN, 0

        best_syndrome = max(confidence_scores, key=confidence_scores.get)
        return best_syndrome, confidence_scores[best_syndrome]


class ClinicalPromptTemplates:
    """
    High-quality prompt templates for Claude/GPT.
    These are tuned to produce clinical-sounding briefings.
    """

    SYSTEM_PROMPT = """You are an expert emergency medicine physician with 15 years of experience.
You are providing a rapid pre-arrival briefing to your ER team about an incoming ambulance patient.

Your briefing should:
1. Sound like you're talking to colleagues, not writing documentation
2. Lead with the key finding that needs immediate action
3. Be specific - use exact numbers from vitals
4. Include ONE specific preparation or intervention per area
5. Be 2-3 sentences maximum
6. Use clinical terminology appropriately
7. End with the ETA or highest priority action

Example of GOOD briefing:
"24F, peritoneal signs and tachycardic at 115 with SBP 92. Likely hemorrhagic shock from ruptured ectopic. Get type & cross, activate massive transfusion protocol, have OR standing by. ETA 4 minutes."

Example of POOR briefing:
"Patient with possible emergency. Alert all teams. Prepare for intervention." (too vague)

Now provide the briefing for this patient:"""

    SEPSIS_PROMPT = """Patient vitals suggest severe infection:
- Fever: {temperature}°C
- Heart Rate: {heart_rate} bpm (tachycardic)
- Blood Pressure: {systolic_bp}/{diastolic_bp} mmHg (hypotensive)
- Respiratory Rate: {respiratory_rate} (elevated)
- O2 Sat: {oxygen_saturation}%

This patient needs sepsis protocol activation on arrival.
Generate a 2-3 sentence pre-arrival briefing."""

    CARDIAC_PROMPT = """Patient showing signs of cardiovascular compromise:
- Blood Pressure: {systolic_bp}/{diastolic_bp} mmHg (HYPOTENSIVE)
- Heart Rate: {heart_rate} bpm
- O2 Saturation: {oxygen_saturation}%
- Respiratory Rate: {respiratory_rate}

Risk: Cardiogenic shock or acute MI.
Generate a 2-3 sentence pre-arrival briefing that includes specific prep steps."""

    RESPIRATORY_PROMPT = """Patient in respiratory distress:
- O2 Saturation: {oxygen_saturation}% (CRITICAL if <90)
- Respiratory Rate: {respiratory_rate} breaths/min (elevated)
- Heart Rate: {heart_rate} bpm
- Blood Pressure: {systolic_bp}/{diastolic_bp}

Generate a 2-3 sentence pre-arrival briefing focused on airway management."""

    @staticmethod
    def get_detailed_prompt(syndrome: ClinicalSyndrome, vitals: Dict, anomaly_score: float) -> str:
        """
        Generate specialized prompt based on detected syndrome.
        """

        formatted_vitals = {
            "temperature": f"{vitals.get('temperature', 37):.1f}",
            "heart_rate": vitals.get("heart_rate", 72),
            "systolic_bp": vitals.get("systolic_bp", 120),
            "diastolic_bp": vitals.get("diastolic_bp", 80),
            "respiratory_rate": vitals.get("respiratory_rate", 16),
            "oxygen_saturation": vitals.get("oxygen_saturation", 98),
        }

        if syndrome == ClinicalSyndrome.SEPSIS:
            specific_prompt = ClinicalPromptTemplates.SEPSIS_PROMPT.format(**formatted_vitals)
        elif syndrome == ClinicalSyndrome.CARDIOGENIC_SHOCK:
            specific_prompt = ClinicalPromptTemplates.CARDIAC_PROMPT.format(**formatted_vitals)
        elif syndrome == ClinicalSyndrome.RESPIRATORY_DISTRESS:
            specific_prompt = ClinicalPromptTemplates.RESPIRATORY_PROMPT.format(**formatted_vitals)
        else:
            specific_prompt = f"""Generic vital signs: HR {vitals.get('heart_rate')}, BP {vitals.get('systolic_bp')}/{vitals.get('diastolic_bp')}, O2 {vitals.get('oxygen_saturation')}%, RR {vitals.get('respiratory_rate')}, Temp {vitals.get('temperature'):.1f}°C.
Anomaly score: {anomaly_score:.2f} (higher = more concerning).

Generate a brief pre-arrival briefing."""

        return ClinicalPromptTemplates.SYSTEM_PROMPT + "\n\n" + specific_prompt

    @staticmethod
    def format_for_gpt(syndrome: ClinicalSyndrome, vitals: Dict, anomaly_score: float, alert_level: str) -> Dict:
        """
        Format as complete API call for Claude/OpenAI.
        """

        prompt = ClinicalPromptTemplates.get_detailed_prompt(syndrome, vitals, anomaly_score)

        return {
            "messages": [
                {"role": "system", "content": ClinicalPromptTemplates.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "model": "gpt-4-turbo",
            "temperature": 0.4,  # Lower = more consistent clinical tone
            "max_tokens": 120,
            "top_p": 0.9
        }


class RefinedClinicalEngine:
    """
    Enhanced clinical decision engine with better syndrome classification
    and more sophisticated briefing generation.
    """

    @staticmethod
    def generate_briefing_advanced(vitals: Dict, anomaly_score: float, alert_level: str) -> Dict:
        """
        Generate refined briefing using advanced syndrome classification.
        """

        # Classify syndrome
        syndrome, syndrome_conf = AdvancedClinicalEngine.classify_syndrome(vitals)

        # Get recommended actions based on syndrome
        actions = RefinedClinicalEngine._get_syndrome_actions(syndrome)

        # Determine color code
        color_code = "GREEN"
        if alert_level == "CRITICAL" or anomaly_score > 0.8:
            color_code = "RED"
        elif alert_level == "WARNING" or anomaly_score > 0.5:
            color_code = "YELLOW"

        # Generate briefing text
        if syndrome != ClinicalSyndrome.UNKNOWN:
            briefing_text = RefinedClinicalEngine._generate_syndrome_briefing(syndrome, vitals)
        else:
            briefing_text = RefinedClinicalEngine._generate_generic_briefing(vitals, anomaly_score)

        return {
            "syndrome": syndrome.value,
            "syndrome_confidence": syndrome_conf,
            "triage_briefing": briefing_text,
            "color_code": color_code,
            "recommended_actions": actions,
            "alert_level": alert_level,
            "anomaly_score": anomaly_score
        }

    @staticmethod
    def _get_syndrome_actions(syndrome: ClinicalSyndrome) -> list:
        """Get specific actions for syndrome."""

        actions = {
            ClinicalSyndrome.SEPSIS: [
                "Activate sepsis protocol on arrival",
                "Prepare IV lines for aggressive fluid resuscitation",
                "Draw blood cultures x2 before antibiotics",
                "Prepare vasopressor support if SBP remains <90",
                "Notify ICU for admission"
            ],
            ClinicalSyndrome.CARDIOGENIC_SHOCK: [
                "Place on continuous cardiac monitoring",
                "Prepare for possible ACLS intervention",
                "Have crash cart at bedside",
                "Notify cardiology immediately",
                "Prepare for emergency catheterization"
            ],
            ClinicalSyndrome.RESPIRATORY_DISTRESS: [
                "Prepare bag-valve-mask and intubation equipment",
                "Place on high-flow oxygen",
                "Notify respiratory therapy stat",
                "Have mechanical ventilation standing by",
                "Prepare for possible emergency intubation"
            ],
        }

        return actions.get(syndrome, [
            "Place on continuous monitoring",
            "Prepare for rapid assessment",
            "Have resuscitation equipment available"
        ])

    @staticmethod
    def _generate_syndrome_briefing(syndrome: ClinicalSyndrome, vitals: Dict) -> str:
        """Generate syndrome-specific briefing."""

        hr = vitals.get("heart_rate", 72)
        sbp = vitals.get("systolic_bp", 120)
        dbp = vitals.get("diastolic_bp", 80)
        temp = vitals.get("temperature", 37)
        o2 = vitals.get("oxygen_saturation", 98)
        rr = vitals.get("respiratory_rate", 16)

        templates = {
            ClinicalSyndrome.SEPSIS: f"Septic patient: fever {temp:.1f}°C, HR {hr}, SBP {sbp}. Activate sepsis protocol, prepare for ICU admission. ETA 5 minutes.",
            ClinicalSyndrome.CARDIOGENIC_SHOCK: f"Cardiogenic shock: SBP {sbp}, HR {hr}, RR {rr}, O2 {o2}%. Have ACLS ready, notify cardiology. ETA 4 minutes.",
            ClinicalSyndrome.RESPIRATORY_DISTRESS: f"Respiratory distress: RR {rr}, O2 {o2}%. Prepare intubation, high-flow O2 on arrival. ETA 3 minutes.",
        }

        return templates.get(syndrome, f"Patient with HR {hr}, BP {sbp}/{dbp}, O2 {o2}%. Prepare for immediate assessment.")

    @staticmethod
    def _generate_generic_briefing(vitals: Dict, anomaly_score: float) -> str:
        """Generate generic briefing when syndrome unclear."""

        if anomaly_score > 0.8:
            return "Critical vitals detected. Prepare for rapid assessment and intervention. Have resuscitation equipment ready."
        elif anomaly_score > 0.5:
            return "Patient showing concerning vitals trends. Prepare for enhanced monitoring and possible intervention."
        else:
            return "Patient stable in transport. Continue standard monitoring."


if __name__ == "__main__":
    print("[TEST] Advanced Clinical Engine\n")

    # Test case 1: Clear sepsis
    vitals = {
        "heart_rate": 110,
        "systolic_bp": 88,
        "diastolic_bp": 52,
        "respiratory_rate": 24,
        "oxygen_saturation": 91,
        "temperature": 39.5
    }

    result = RefinedClinicalEngine.generate_briefing_advanced(vitals, 0.9, "CRITICAL")
    print(f"Test 1 - Sepsis:")
    print(f"  Syndrome: {result['syndrome']} (confidence: {result['syndrome_confidence']:.2f})")
    print(f"  Briefing: {result['triage_briefing']}")
    print(f"  Color: {result['color_code']}")
    print()

    # Test case 2: Cardiac shock
    vitals2 = {
        "heart_rate": 120,
        "systolic_bp": 75,
        "diastolic_bp": 45,
        "respiratory_rate": 22,
        "oxygen_saturation": 90,
        "temperature": 37.0
    }

    result2 = RefinedClinicalEngine.generate_briefing_advanced(vitals2, 0.85, "CRITICAL")
    print(f"Test 2 - Cardiogenic Shock:")
    print(f"  Syndrome: {result2['syndrome']}")
    print(f"  Briefing: {result2['triage_briefing']}")
    print()

    # Test case 3: Stable
    vitals3 = {
        "heart_rate": 72,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "respiratory_rate": 16,
        "oxygen_saturation": 98,
        "temperature": 37.0
    }

    result3 = RefinedClinicalEngine.generate_briefing_advanced(vitals3, 0.2, "STABLE")
    print(f"Test 3 - Stable Patient:")
    print(f"  Syndrome: {result3['syndrome']}")
    print(f"  Briefing: {result3['triage_briefing']}")
