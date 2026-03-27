import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import asyncio
from datetime import datetime
from openai import AsyncOpenAI

# Initialize FastAPI app
app = FastAPI(title="Nexus Triage Backend", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-test"))

# ============== Data Models ==============

class Vitals(BaseModel):
    heart_rate: int
    systolic_bp: int
    diastolic_bp: int
    respiratory_rate: int
    oxygen_saturation: int
    temperature: float

class Location(BaseModel):
    latitude: float
    longitude: float
    eta_minutes: int

class AmbulanceVitalsStream(BaseModel):
    timestamp: str
    patient_id: str
    vitals: Vitals
    location: Location

class AnomalyOutput(BaseModel):
    timestamp: str
    patient_id: str
    anomaly_detected: bool
    anomaly_score: float
    anomaly_type: str
    alert_level: str  # STABLE, WARNING, CRITICAL

class TriageBriefing(BaseModel):
    timestamp: str
    patient_id: str
    alert_level: str
    triage_briefing: str
    color_code: str  # GREEN, YELLOW, RED
    recommended_actions: list
    confidence: float

# ============== Global State ==============

active_patients = {}
connection_manager = {"connections": []}

# ============== LLM Prompt Engineering ==============

async def generate_triage_briefing(patient_id: str, anomaly_data: dict) -> TriageBriefing:
    """
    Takes anomaly output from ML model and generates clinical triage briefing.
    This is the core "magic" that translates numbers into actionable physician guidance.
    """

    vitals = anomaly_data.get("raw_vitals", {})
    trend = anomaly_data.get("trend_analysis", {})
    alert_level = anomaly_data.get("alert_level", "STABLE")

    # Construct the clinical context for LLM
    prompt = f"""
    You are an expert emergency medicine physician providing a pre-arrival triage briefing to an ER team.

    Patient ID: {patient_id}
    Current Vitals:
    - Heart Rate: {vitals.get('heart_rate', 'N/A')} bpm (Trend: {trend.get('heart_rate_trend', 'N/A')})
    - Blood Pressure: {vitals.get('systolic_bp', 'N/A')}/{vitals.get('diastolic_bp', 'N/A')} mmHg (Trend: {trend.get('bp_trend', 'N/A')})
    - Respiratory Rate: {vitals.get('respiratory_rate', 'N/A')} breaths/min
    - O2 Saturation: {vitals.get('oxygen_saturation', 'N/A')}%
    - Temperature: {vitals.get('temperature', 'N/A')}°C

    Alert Level: {alert_level}

    Provide a concise pre-arrival briefing (2-3 sentences max) that:
    1. Identifies likely physiological condition
    2. Specifies immediate preparation steps
    3. Is written in clear, clinical language with specific action items

    Format: Start with "Patient presents with..." and end with recommendations for immediate interventions.
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
        )
        briefing_text = response.choices[0].message.content
    except Exception as e:
        # Fallback briefing if LLM unavailable
        briefing_text = f"Patient showing {alert_level} deterioration pattern. Prepare for immediate assessment. ETA 5 minutes."

    # Determine color code from alert level
    color_map = {
        "STABLE": "GREEN",
        "WARNING": "YELLOW",
        "CRITICAL": "RED"
    }

    return TriageBriefing(
        timestamp=datetime.utcnow().isoformat() + "Z",
        patient_id=patient_id,
        alert_level=alert_level,
        triage_briefing=briefing_text,
        color_code=color_map.get(alert_level, "YELLOW"),
        recommended_actions=[
            "Prepare triage assessment",
            "Alert relevant department",
            "Prepare monitoring equipment"
        ],
        confidence=0.85
    )

# ============== WebSocket Endpoints ==============

@app.websocket("/ws/ambulance/{patient_id}")
async def websocket_ambulance(websocket: WebSocket, patient_id: str):
    """
    Receives real-time vitals stream from ambulance/ML edge device.
    Broadcasts enriched data (with triage briefing) to all connected ER dashboards.
    """
    await websocket.accept()
    connection_manager["connections"].append(websocket)

    try:
        while True:
            # Receive vitals data from ambulance
            data = await websocket.receive_text()
            vitals_data = json.loads(data)

            # Store patient data
            active_patients[patient_id] = vitals_data

            # Simulate receiving anomaly data from ML edge
            # In production: this would come from the actual ML model
            anomaly_data = {
                "anomaly_detected": vitals_data.get("anomaly_detected", False),
                "alert_level": vitals_data.get("alert_level", "STABLE"),
                "raw_vitals": vitals_data.get("vitals", {}),
                "trend_analysis": vitals_data.get("trend_analysis", {})
            }

            # Generate LLM triage briefing if anomaly detected
            if anomaly_data["anomaly_detected"]:
                triage = await generate_triage_briefing(patient_id, anomaly_data)
            else:
                triage = TriageBriefing(
                    timestamp=vitals_data.get("timestamp"),
                    patient_id=patient_id,
                    alert_level="STABLE",
                    triage_briefing="Patient vitals within normal range. Continue monitoring.",
                    color_code="GREEN",
                    recommended_actions=["Continue standard monitoring"],
                    confidence=0.95
                )

            # Broadcast to all connected dashboards
            enriched_data = {
                "vitals": vitals_data,
                "triage": triage.dict()
            }

            for connection in connection_manager["connections"]:
                try:
                    await connection.send_json(enriched_data)
                except:
                    pass

    except WebSocketDisconnect:
        connection_manager["connections"].remove(websocket)

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    Receives all real-time triage briefings and vitals.
    Frontend dashboards connect here to render live updates.
    """
    await websocket.accept()
    connection_manager["connections"].append(websocket)

    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        connection_manager["connections"].remove(websocket)

# ============== REST Endpoints ==============

@app.get("/health")
async def health_check():
    return {"status": "healthy", "active_patients": len(active_patients)}

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: str):
    return active_patients.get(patient_id, {"error": "Patient not found"})

# ============== Main ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
