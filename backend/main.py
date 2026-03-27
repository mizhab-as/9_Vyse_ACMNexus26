import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import asyncio
from datetime import datetime
from openai import AsyncOpenAI
import sys

# Import clinical engine
sys.path.insert(0, os.path.dirname(__file__))
from clinical_prompt_engine import generate_complete_briefing

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

# Initialize OpenAI client (optional, will use fallback if key unavailable)
api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key) if api_key else None

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
    anomaly_detected: Optional[bool] = False
    anomaly_score: Optional[float] = 0.0
    alert_level: Optional[str] = "STABLE"
    trend_analysis: Optional[dict] = {}

class TriageBriefing(BaseModel):
    timestamp: str
    patient_id: str
    alert_level: str
    triage_briefing: str
    color_code: str
    recommended_actions: list
    confidence: float
    anomaly_score: float

# ============== Global State ==============

active_patients = {}
connection_manager = {"connections": []}
patient_alerts = {}  # Track alerts per patient

# ============== LLM & Clinical Integration ==============

async def generate_triage_briefing_enhanced(patient_id: str, anomaly_data: dict) -> TriageBriefing:
    """
    Enhanced briefing generation with clinical decision engine.
    Falls back to rule-based if LLM unavailable.
    """

    vitals = anomaly_data.get("raw_vitals", {})
    anomaly_score = anomaly_data.get("anomaly_score", 0.0)
    alert_level = anomaly_data.get("alert_level", "STABLE")

    # Try LLM first if available
    if client and alert_level in ["WARNING", "CRITICAL"]:
        try:
            prompt = f"""You are an expert emergency medicine physician providing a pre-arrival triage briefing to an ER team.

Current Vitals:
- Heart Rate: {vitals.get('heart_rate', 'N/A')} bpm
- Blood Pressure: {vitals.get('systolic_bp', 'N/A')}/{vitals.get('diastolic_bp', 'N/A')} mmHg
- Respiratory Rate: {vitals.get('respiratory_rate', 'N/A')} breaths/min
- O2 Saturation: {vitals.get('oxygen_saturation', 'N/A')}%
- Temperature: {vitals.get('temperature', 'N/A')}°C
- Alert Level: {alert_level}

Provide a concise pre-arrival briefing (1-2 sentences) identifying the likely condition and immediate steps. Clinical tone only."""

            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # More deterministic
                max_tokens=100,
            )
            briefing_text = response.choices[0].message.content
        except Exception as e:
            print(f"[LLM] Error: {e}. Falling back to rule-based.")
            briefing_result = generate_complete_briefing(vitals, anomaly_score, alert_level)
            briefing_text = briefing_result["triage_briefing"]
    else:
        # Use rule-based clinical decision engine
        briefing_result = generate_complete_briefing(vitals, anomaly_score, alert_level)
        briefing_text = briefing_result["triage_briefing"]

    # Get recommended actions
    briefing_result = generate_complete_briefing(vitals, anomaly_score, alert_level)

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
        recommended_actions=briefing_result.get("recommended_actions", ["Prepare for assessment"]),
        confidence=briefing_result.get("confidence", 0.8),
        anomaly_score=float(anomaly_score)
    )

# ============== WebSocket Endpoints ==============

@app.websocket("/ws/ambulance/{patient_id}")
async def websocket_ambulance(websocket: WebSocket, patient_id: str):
    """
    Receives real-time vitals stream from ambulance/ML edge device.
    Broadcasts enriched data (with triage briefing) to all connected ER dashboards.
    """
    await websocket.accept()
    print(f"[WS] Ambulance connected: {patient_id}")

    try:
        while True:
            # Receive vitals data from ambulance
            data = await websocket.receive_text()
            vitals_data = json.loads(data)

            # Store patient data
            active_patients[patient_id] = vitals_data

            # Extract anomaly data from stream
            anomaly_data = {
                "anomaly_detected": vitals_data.get("anomaly_detected", False),
                "anomaly_score": vitals_data.get("anomaly_score", 0.0),
                "alert_level": vitals_data.get("alert_level", "STABLE"),
                "raw_vitals": vitals_data.get("vitals", {}),
                "trend_analysis": vitals_data.get("trend_analysis", {})
            }

            # Generate LLM triage briefing if anomaly detected
            if anomaly_data["anomaly_detected"]:
                triage = await generate_triage_briefing_enhanced(patient_id, anomaly_data)
                patient_alerts[patient_id] = triage
                print(f"[ALERT] {patient_id}: {triage.alert_level}")
            else:
                triage = TriageBriefing(
                    timestamp=vitals_data.get("timestamp"),
                    patient_id=patient_id,
                    alert_level="STABLE",
                    triage_briefing="Patient vitals within normal range. Continue monitoring.",
                    color_code="GREEN",
                    recommended_actions=["Continue standard monitoring"],
                    confidence=0.95,
                    anomaly_score=anomaly_data["anomaly_score"]
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
        print(f"[WS] Ambulance disconnected: {patient_id}")
        if websocket in connection_manager["connections"]:
            connection_manager["connections"].remove(websocket)

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    Receives all real-time triage briefings and vitals.
    Frontend dashboards connect here to render live updates.
    """
    await websocket.accept()
    connection_manager["connections"].append(websocket)
    print(f"[WS] Dashboard connected. Total connections: {len(connection_manager['connections'])}")

    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Keep connection alive
                pass
    except WebSocketDisconnect:
        print(f"[WS] Dashboard disconnected")
        if websocket in connection_manager["connections"]:
            connection_manager["connections"].remove(websocket)

# ============== REST Endpoints ==============

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_patients": len(active_patients),
        "connected_dashboards": len(connection_manager["connections"]),
        "llm_available": client is not None
    }

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: str):
    if patient_id in active_patients:
        return {
            "patient": active_patients[patient_id],
            "alert": patient_alerts.get(patient_id)
        }
    return {"error": "Patient not found"}

@app.get("/alerts")
async def get_all_alerts():
    return {"alerts": patient_alerts}

# ============== Main ==============

if __name__ == "__main__":
    import uvicorn
    print("[NEXUS] Starting backend server...")
    print(f"[INFO] LLM integration: {'ENABLED' if client else 'DISABLED (using fallback)'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
