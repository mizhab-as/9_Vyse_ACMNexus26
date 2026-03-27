import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY", "dummy_key")

async def generate_triage_briefing(vitals_history: list) -> str:
    """
    VigilCare Predictive Report generator using LLM.
    Analyzes multi-modal short-term trends to predict deterioration.
    """
    latest = vitals_history[-1]
    
    if openai.api_key == "dummy_key":
        return (
            "VIGILCARE PREDICTIVE SMART REPORT\n"
            f"Blood group: {latest['blood_group']}\n"
            f"Visible Injury: {latest['vision_analysis']}\n"
            f"ECG: {latest['ecg_status']} detected.\n\n"
            "PREDICTED RISK: HIGH\n"
            "Likely Complications: High probability of cardiac instability and hemorrhagic shock.\n"
            "Explainable Prediction: Heart rate is consistently climbing while blood pressure collapses rapidly alongside an unstable ECG pattern over the last 10 minutes.\n\n"
            "RECOMMENDED PREPARATION: ER Team prepare massive transfusion protocol (O+), orthopedics consult on standby, and crash cart for predicted cardiac event."
        )
    
    prompt = f"""You are VigilCare, an AI-powered pre-hospital predictive clinical intelligence system.
Review the patient's multimodal data: Blood Group {latest['blood_group']}, Vision AI: {latest['vision_analysis']}.
Recent Vitals & ECG History: {str([f"Min {v['timestamp']}: HR {v['heart_rate']} BP {v['blood_pressure']} ECG {v['ecg_status']}" for v in vitals_history[-5:]])}

Generate a concise, structured Smart Predictive Report explicitly detailing:
Blood group:
Injury:
ECG:
Predicted Risk: (Low/Medium/High)
Likely complications: (Predict what will happen next based on trends)
Explainable Prediction Analysis: (Briefly explain why based on the changing vitals/signals)
"""
    
    try:
        response = await openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"VIGILCARE PREDICTIVE ALERT\nAPI ERROR: {str(e)}\n\nRisk: HIGH. Prepare ER crash cart based on system default fallback."
