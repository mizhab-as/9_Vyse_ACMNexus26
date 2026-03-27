import asyncio
import json
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

from simulator import simulate_ambulance_ride
from ml_engine import AnomalyDetector

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(connection)

manager = ConnectionManager()

patient_context = {
    "blood_group": "O-",
    "temperature": "98.6",
    "ecg_status": "Normal Sinus Rhythm (80 bpm)",
    "oxygen": "98",
    "eta": "Calculating...",
    "lat": "",
    "lon": ""
}

class PatientContextModel(BaseModel):
    blood_group: str
    temperature: str
    ecg_status: str
    oxygen: str
    eta: str
    lat: str = ""
    lon: str = ""

@app.post("/api/patient_context")
async def update_patient_context(context: PatientContextModel):
    global patient_context
    patient_context["blood_group"] = context.blood_group
    patient_context["temperature"] = context.temperature
    patient_context["ecg_status"] = context.ecg_status
    patient_context["oxygen"] = context.oxygen
    patient_context["eta"] = context.eta
    patient_context["lat"] = context.lat
    patient_context["lon"] = context.lon
    return {"status": "success", "data": patient_context}

@app.get("/api/patient_context")
async def get_patient_context():
    return patient_context

async def data_streamer():
    hr_detector = AnomalyDetector(window_size=10, threshold=2.5)
    
    vitals_history = []
    
    # AI state trackers for dynamic mode
    dynamic_start_time = 0
    in_dynamic_mode = False

    async for vitals in simulate_ambulance_ride():
        vitals.update(patient_context)
        vitals_history.append(vitals)
        
        # Derive HR implicitly from ECG stream selection
        ecg = patient_context.get("ecg_status", "Normal Sinus Rhythm (80 bpm)")
        target_spo2_mode = "normal"
        
        if "Dynamic" in ecg:
            if not in_dynamic_mode:
                in_dynamic_mode = True
                dynamic_start_time = time.time()
                
            elapsed = time.time() - dynamic_start_time
            if elapsed < 15:
                # First 15 seconds: Normal
                base_hr = 80
                target_spo2_mode = "normal"
            elif elapsed < 35:
                # 15s to 35s: Start deteriorating (Ischemia / Hypoxia begins)
                base_hr = 110 + int((elapsed - 15) * 1.5)
                target_spo2_mode = "warning"
            else:
                # 35s+: Full critical crash
                base_hr = 145 + random.randint(0, 10)
                target_spo2_mode = "critical"
        else:
            in_dynamic_mode = False
            # Static mapped inputs
            if "145" in ecg:
                base_hr = 145
                target_spo2_mode = "critical"
            elif "45" in ecg:
                base_hr = 45
                target_spo2_mode = "critical"
            elif "110" in ecg:
                base_hr = 110
                target_spo2_mode = "warning"
            else:
                base_hr = 80
                target_spo2_mode = "normal"
            
        # Add live fluctuation to HR
        hr_val = base_hr + random.randint(-4, 4)
        vitals["heart_rate"] = hr_val
        
        # Live automatic fluctuating SpO2 and Temp (random walk governed by condition)
        base_spo2 = float(patient_context.get("oxygen", 98))
        if target_spo2_mode == "critical":
            # Emergency: Oxygen drops
            if base_spo2 > 82:
                spo2_val = base_spo2 - random.uniform(0.5, 1.5)
            else:
                spo2_val = base_spo2 + random.uniform(-0.5, 0.5)
        elif target_spo2_mode == "warning":
            if base_spo2 > 90:
                spo2_val = base_spo2 - random.uniform(0.2, 0.8)
            else:
                spo2_val = base_spo2 + random.uniform(-0.5, 0.5)
        else:
            # Normal: Oxygen recovers to 98-99
            if base_spo2 < 98:
                spo2_val = base_spo2 + random.uniform(0.5, 1.5)
            else:
                spo2_val = base_spo2 + random.uniform(-0.2, 0.2)
                
        spo2_val = max(50.0, min(100.0, spo2_val))
        patient_context["oxygen"] = str(round(spo2_val, 1))
        
        base_temp = float(patient_context.get("temperature", 98.6))
        # Temp gravitates based on condition
        if hr_val > 100 and base_temp < 101.5:
             temp_val = base_temp + random.uniform(0.0, 0.2)
        elif hr_val <= 100 and base_temp > 98.6:
             temp_val = base_temp - random.uniform(0.0, 0.2)
        else:
             temp_val = base_temp + random.uniform(-0.1, 0.1)
             
        temp_val = round(max(97.0, min(105.0, temp_val)), 1)
        patient_context["temperature"] = str(temp_val)

        blood_group = patient_context.get("blood_group", "Unknown")

        # Live calculate Blood Pressure inversely related to SpO2 drop
        drop_factor = max(0, 98 - spo2_val)
        sys_bp = int(120 + (drop_factor * 2.5) + random.randint(-4, 4))
        dia_bp = int(80 + (drop_factor * 1.5) + random.randint(-3, 3))
        vitals["blood_pressure"] = f"{sys_bp}/{dia_bp}"
        
        # Calculate Heart Attack Prediction binary outcome
        risk_score = 5 # base risk
        if hr_val > 100:
            risk_score += (hr_val - 100) * 0.8
        elif hr_val < 60:
            risk_score += (60 - hr_val) * 1.5
        if spo2_val < 95:
            risk_score += (95 - spo2_val) * 2.5
        if sys_bp > 140:
            risk_score += (sys_bp - 140) * 0.5
            
        is_heart_attack = (risk_score >= 40) or (hr_val > 120) or (hr_val < 50)
        vitals["heart_attack_prediction"] = "YES" if is_heart_attack else "NO"
        
        vitals["oxygen"] = str(round(spo2_val, 1))
        vitals["temperature"] = str(temp_val)
        
        # Fixed Time for moving graph
        from datetime import datetime
        vitals["time"] = datetime.now().strftime("%H:%M:%S")

        hr_anomaly = hr_detector.process_new_metric(hr_val)
        
        is_dangerous_o2 = spo2_val < 85
        is_serious_o2 = spo2_val < 92 and spo2_val >= 85
        
        vitals["anomaly"] = bool(hr_anomaly or is_heart_attack or is_dangerous_o2 or is_serious_o2)
        
        # Priority rules for triaging
        if is_heart_attack:
            vitals["triage_alert"] = f"CRITICAL AI DETECTED: High risk of Myocardial Infarction / Cardiac Arrest predicted from real-time ECG ({hr_val} BPM). Kolencherry Medical Hospital: Prepare Code Team.\n*** BLOOD GROUP {blood_group} REQUIRED ***"
            vitals["status"] = "High Risk"
        elif is_dangerous_o2:
            vitals["triage_alert"] = f"DANGEROUS CONDITION (AI ALERT): Patient SpO2 is dangerously low ({spo2_val}% - Hypoxia). BP Spiking ({sys_bp}/{dia_bp}). Kolencherry Medical Hospital: Prepare ICU.\n*** BLOOD GROUP {blood_group} REQUIRED ***"
            vitals["status"] = "Critical"
        elif is_serious_o2:
            vitals["triage_alert"] = f"SERIOUS CONDITION: Patient oxygen level dropping ({spo2_val}%). Route to Kolencherry Medical Hospital.\nBlood Group {blood_group} units on standby."
            vitals["status"] = "Warning"
        else:
            vitals["triage_alert"] = None
            vitals["status"] = "Stable"

        await manager.broadcast(json.dumps(vitals))
        
        if len(vitals_history) > 60:
            vitals_history.pop(0)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(data_streamer())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
