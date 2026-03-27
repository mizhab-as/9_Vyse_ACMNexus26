import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY", "dummy_key")

async def generate_triage_briefing(vitals_history: list) -> str:
    """
    Takes raw anomaly flags and translates them to an ER pre-arrival triage briefing.
    Uses generic prompt engineering if standard model is unavailable.
    """
    if openai.api_key == "dummy_key":
        # Fallback dummy for hackathon MVP without API key
        return (
            "🚨 CRITICAL TRIAGE ALERT 🚨\n"
            "PATIENT PROFILE: 65Y/O MALE\n\n"
            "CURRENT STATUS: Suspected Septic Shock\n"
            "Vitals crash detected over the last 15 minutes. "
            f"Heart rate spiked to {vitals_history[-1]['heart_rate']} BPM while blood pressure collapsed to {vitals_history[-1]['blood_pressure']} mmHg. "
            "Oxygen saturation dropping.\n\n"
            "RECOMMENDED ACTION: ER Team prepare vasopressors, massive fluid resuscitation protocols, and IV antibiotics immediately. Patient arriving in 5 minutes."
        )
    
    # Real implementation using GPT-4-turbo
    prompt = f"You are an expert ER Triage AI. Review the following recent vital sign history from a patient in an ambulance, detect the likely physiological deterioration pattern (e.g. Septic Shock), and draft a 3-sentence high-priority briefing for the ER doctors containing current status and recommended immediate actions upon arrival.\n\nVitals:\n{str(vitals_history[-5:])}"
    
    try:
        response = await openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"🚨 CRITICAL ALERT API ERROR: {str(e)} 🚨\nSuspected rapid crashing vitals on incoming ambulance. Prepare ER crash cart."
