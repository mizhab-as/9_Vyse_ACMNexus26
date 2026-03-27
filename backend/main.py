import asyncio
import json
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from pydantic import BaseModel
import time
import httpx
import math

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


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    la1 = math.radians(lat1)
    la2 = math.radians(lat2)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin(d_lon / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


async def _overpass_hospitals(lat: float, lon: float, radius_m: int) -> list[dict]:
    query = f"""
[out:json];
(
  node[\"amenity\"=\"hospital\"](around:{radius_m},{lat},{lon});
  way[\"amenity\"=\"hospital\"](around:{radius_m},{lat},{lon});
  relation[\"amenity\"=\"hospital\"](around:{radius_m},{lat},{lon});
);
out center 50;
"""

    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.post(
            "https://overpass-api.de/api/interpreter",
            headers={
                "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            },
            data={"data": query},
        )
        res.raise_for_status()
        data = res.json()

    elements = data.get("elements") if isinstance(data, dict) else None
    if not isinstance(elements, list):
        return []

    hospitals: list[dict] = []
    for el in elements:
        if not isinstance(el, dict):
            continue
        el_lat = el.get("lat")
        el_lon = el.get("lon")
        if not isinstance(el_lat, (int, float)) or not isinstance(el_lon, (int, float)):
            center = el.get("center")
            if isinstance(center, dict):
                el_lat = center.get("lat")
                el_lon = center.get("lon")
        if not isinstance(el_lat, (int, float)) or not isinstance(el_lon, (int, float)):
            continue

        tags = el.get("tags") if isinstance(el.get("tags"), dict) else {}
        name = tags.get("name") if isinstance(tags.get("name"), str) else "Unnamed Hospital"
        name = name.strip() or "Unnamed Hospital"

        addr_parts = [
            tags.get("addr:street"),
            tags.get("addr:city"),
            tags.get("addr:district"),
            tags.get("addr:state"),
        ]
        addr_parts = [p for p in addr_parts if isinstance(p, str) and p.strip()]
        address = ", ".join(addr_parts) if addr_parts else ""

        hospitals.append(
            {
                "id": f"{el.get('type')}/{el.get('id')}",
                "name": name,
                "lat": float(el_lat),
                "lon": float(el_lon),
                "address": address,
            }
        )

    # De-dupe
    seen: set[str] = set()
    deduped: list[dict] = []
    for h in hospitals:
        key = f"{h['name']}|{h['lat']:.5f}|{h['lon']:.5f}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(h)

    # Sort by straight-line distance first
    deduped.sort(key=lambda h: _haversine_km(lat, lon, h["lat"], h["lon"]))
    return deduped[:8]


async def _osrm_eta(lat: float, lon: float, dest_lat: float, dest_lon: float) -> tuple[int, float]:
    url = f"https://router.project-osrm.org/route/v1/driving/{lon},{lat};{dest_lon},{dest_lat}?overview=false"
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url)
        res.raise_for_status()
        data = res.json()

    routes = data.get("routes") if isinstance(data, dict) else None
    if not isinstance(routes, list) or not routes:
        raise ValueError("No route")
    route0 = routes[0]
    duration = route0.get("duration")
    distance = route0.get("distance")
    if not isinstance(duration, (int, float)) or not isinstance(distance, (int, float)):
        raise ValueError("Invalid route")

    eta_minutes = max(1, math.ceil((float(duration) * 1.15) / 60.0))
    distance_km = max(0.1, round((float(distance) / 1000.0) * 10) / 10)
    return eta_minutes, distance_km


@app.get("/api/route_suggestions")
async def route_suggestions(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
):
    # Try 8km then 15km (cap as requested)
    radii = [8000, 15000]
    hospitals: list[dict] = []
    for r in radii:
        hospitals = await _overpass_hospitals(lat, lon, r)
        if len(hospitals) >= 2:
            break

    if not hospitals:
        return {"suggested": None, "alternate": None, "note": "No nearby hospitals found."}

    ranked: list[dict] = []
    for h in hospitals:
        try:
            eta_minutes, distance_km = await _osrm_eta(lat, lon, h["lat"], h["lon"])
            ranked.append({**h, "etaMinutes": eta_minutes, "distanceKm": distance_km})
        except Exception:
            continue

    ranked.sort(key=lambda h: h.get("etaMinutes", 10**9))
    suggested = ranked[0] if ranked else None
    alternate = None
    if suggested:
        suggested_id = suggested.get("id")
        suggested_name = (suggested.get("name") or "").strip().lower()
        s_lat = float(suggested.get("lat"))
        s_lon = float(suggested.get("lon"))

        # Avoid returning the same hospital under a different OSM element.
        # Use id, name, and minimum geo separation.
        min_sep_km = 0.5
        for h in ranked[1:]:
            if h.get("id") == suggested_id:
                continue
            cand_name = (h.get("name") or "").strip().lower()
            if cand_name and cand_name == suggested_name:
                continue
            sep = _haversine_km(s_lat, s_lon, float(h.get("lat")), float(h.get("lon")))
            if sep < min_sep_km:
                continue
            alternate = h
            break

    note = "OK" if suggested else "Could not rank by ETA."
    if suggested and not alternate:
        note = "Suggested found; no alternate within 15km."

    return {"suggested": suggested, "alternate": alternate, "note": note}

patient_context = {
    "blood_group": "O-",
    "temperature": "98.6",
    "ecg_status": "Normal Sinus Rhythm (80 bpm)",
    "oxygen": "98",
    "eta": "Calculating...",
    "lat": "",
    "lon": "",
    "destination_name": "",
    "destination_lat": "",
    "destination_lon": "",
    "alternative_name": "",
    "alternative_lat": "",
    "alternative_lon": "",
}

class PatientContextModel(BaseModel):
    blood_group: str
    temperature: str
    ecg_status: str
    oxygen: str
    eta: str
    lat: str = ""
    lon: str = ""
    destination_name: str = ""
    destination_lat: str = ""
    destination_lon: str = ""
    alternative_name: str = ""
    alternative_lat: str = ""
    alternative_lon: str = ""

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
    patient_context["destination_name"] = context.destination_name
    patient_context["destination_lat"] = context.destination_lat
    patient_context["destination_lon"] = context.destination_lon
    patient_context["alternative_name"] = context.alternative_name
    patient_context["alternative_lat"] = context.alternative_lat
    patient_context["alternative_lon"] = context.alternative_lon
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

        hospital_name = patient_context.get("destination_name") or "Kolencherry Medical Hospital"
        alt_hospital_name = patient_context.get("alternative_name") or ""
        alt_suffix = f" (Alt: {alt_hospital_name})" if alt_hospital_name else ""
        
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
            vitals["triage_alert"] = f"CRITICAL AI DETECTED: High risk of Myocardial Infarction / Cardiac Arrest predicted from real-time ECG ({hr_val} BPM). {hospital_name}{alt_suffix}: Prepare Code Team.\n*** BLOOD GROUP {blood_group} REQUIRED ***"
            vitals["status"] = "High Risk"
        elif is_dangerous_o2:
            vitals["triage_alert"] = f"DANGEROUS CONDITION (AI ALERT): Patient SpO2 is dangerously low ({spo2_val}% - Hypoxia). BP Spiking ({sys_bp}/{dia_bp}). {hospital_name}{alt_suffix}: Prepare ICU.\n*** BLOOD GROUP {blood_group} REQUIRED ***"
            vitals["status"] = "Critical"
        elif is_serious_o2:
            vitals["triage_alert"] = f"SERIOUS CONDITION: Patient oxygen level dropping ({spo2_val}%). Route to {hospital_name}{alt_suffix}.\nBlood Group {blood_group} units on standby."
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
