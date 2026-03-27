import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import time

from simulator import simulate_ambulance_ride
from ml_engine import AnomalyDetector
from llm_triage import generate_triage_briefing

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

# Background task to send data
async def data_streamer():
    hr_detector = AnomalyDetector(window_size=10, threshold=2.5) # Sensitive
    bp_detector = AnomalyDetector(window_size=10, threshold=2.5)
    
    vitals_history = []
    alert_triggered = False

    async for vitals in simulate_ambulance_ride():
        vitals_history.append(vitals)
        
        # Check anomalies
        hr_anomaly = hr_detector.process_new_metric(vitals["heart_rate"])
        bp_anomaly = bp_detector.process_new_metric(vitals["blood_pressure"])
        
        vitals["anomaly"] = hr_anomaly or bp_anomaly
        
        # Determine if we should trigger triage alert
        # If red zone and anomaly detected for the first time
        if vitals["status"] == "Red" and (hr_anomaly or bp_anomaly) and not alert_triggered:
            alert_triggered = True
            vitals["triage_alert"] = await generate_triage_briefing(vitals_history)
        else:
            vitals["triage_alert"] = None
            
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
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
