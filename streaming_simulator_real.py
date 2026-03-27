"""
Streaming Simulator (Real Data Integration)

This script:
1. Loads a real clinical patient record from the PhysioNet Sepsis dataset (.psv).
2. Cleans and interpolates the medical data (HR, Temp, SBP, DBP, Resp, O2).
3. Streams the actual patient telemetry through our edge ML detector.
4. Pushes the anomaly-enriched telemetry to our FastAPI cloud backend via WebSockets.
"""

import asyncio
import json
import websockets
from datetime import datetime, timedelta
import sys
import os
import pandas as pd
import numpy as np
import io

# Fix Unicode encoding on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add current directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from ml_engine.anomaly_detector import AnomalyDetector

class RealDataSimulator:
    def __init__(self, psv_filepath: str, patient_id: str = "REAL-P002"):
        self.psv_filepath = psv_filepath
        self.patient_id = patient_id
        self.df = self._load_and_clean_data()
        self.total_samples = len(self.df)
    
    def _load_and_clean_data(self):
        print(f"[DATA] Loading real patient telemetry from {self.psv_filepath}...")
        df = pd.read_csv(self.psv_filepath, sep='|')
        
        # We only care about core vitals for this demo
        core_cols = ['HR', 'SBP', 'DBP', 'Resp', 'O2Sat', 'Temp', 'SepsisLabel']
        df = df[core_cols].copy()
        
        # Real ICU data has lots of missing (NaN) values because they don't take blood pressure every second.
        # We forward-fill the data to simulate a continuous monitor holding its last value.
        df.ffill(inplace=True)
        df.bfill(inplace=True) # Backfill if the very first few rows are NaN

        # If backfill failed (entire column is NaN), fill with standard medians
        df['HR'] = df['HR'].fillna(80)
        df['SBP'] = df['SBP'].fillna(120)
        df['DBP'] = df['DBP'].fillna(80)
        df['Resp'] = df['Resp'].fillna(16)
        df['O2Sat'] = df['O2Sat'].fillna(98)
        df['Temp'] = df['Temp'].fillna(37.0)
        
        return df

    def get_sample_for_streaming(self, sample_idx: int) -> dict:
        row = self.df.iloc[sample_idx]
        
        vitals = {
            "heart_rate": int(row['HR']),
            "systolic_bp": int(row['SBP']),
            "diastolic_bp": int(row['DBP']),
            "respiratory_rate": int(row['Resp']),
            "oxygen_saturation": int(row['O2Sat']),
            "temperature": float(row['Temp'])
        }
        
        timestamp = datetime(2026, 3, 27, 22, 0, 0) + timedelta(minutes=sample_idx)
        
        return {
            "timestamp": timestamp.isoformat() + "Z",
            "patient_id": self.patient_id,
            "vitals": vitals,
            "is_actual_sepsis": bool(row['SepsisLabel']),
            "location": {
                "latitude": 12.9352 + (np.random.random() * 0.001),
                "longitude": 77.6245 + (np.random.random() * 0.001),
                "eta_minutes": max(1, self.total_samples - sample_idx)
            }
        }

class StreamingSimulatorReal:
    def __init__(self, backend_url: str, psv_filepath: str, patient_id: str):
        self.backend_url = backend_url
        self.simulator = RealDataSimulator(psv_filepath, patient_id)
        self.anomaly_detector = AnomalyDetector(window_size=10, contamination=0.1)
        self.crisis_detected_at = None

    async def stream_data(self, speed_multiplier: float = 1.0):
        try:
            async with websockets.connect(self.backend_url) as websocket:
                print(f"[OK] Connected to backend: {self.backend_url}")
                print(f"[INFO] Streaming {self.simulator.total_samples} hours of real ICU data...\n")

                for sample_idx in range(self.simulator.total_samples):
                    vitals_payload = self.simulator.get_sample_for_streaming(sample_idx)
                    vitals = vitals_payload['vitals']

                    # 1. Edge ML Anomaly Detection!
                    anomaly_detected, anomaly_score, details = self.anomaly_detector.detect_anomaly(vitals)

                    enriched_payload = {
                        **vitals_payload,
                        "anomaly_detected": anomaly_detected,
                        "anomaly_score": float(anomaly_score),
                        "alert_level": details.get('alert_level', 'STABLE'),
                        "trend_analysis": details.get('trends', {})
                    }

                    # 2. Transmit to Cloud
                    await websocket.send(json.dumps(enriched_payload))

                    if anomaly_detected and not self.crisis_detected_at:
                        self.crisis_detected_at = sample_idx
                        print(f"\n[ALERT] Sample {sample_idx} - ML CRISIS DETECTED! (Is clinical sepsis: {vitals_payload['is_actual_sepsis']})")

                    status_color = "[CRISIS]" if anomaly_detected else "[NORMAL]"
                    print(f"{status_color} | Data {sample_idx:3d} | "
                          f"HR: {vitals['heart_rate']:3d} | "
                          f"BP: {vitals['systolic_bp']:3d}/{vitals['diastolic_bp']:3d} | "
                          f"ML Score: {anomaly_score:.2f} | "
                          f"Real Sepsis: {vitals_payload['is_actual_sepsis']}")

                    await asyncio.sleep(0.5 / speed_multiplier) 

                print("\n[DONE] PhysioNet Stream complete.")

        except Exception as e:
            print(f"[ERROR] Connection error: {e}")

async def main():
    # We will run the septic patient for the demo!
    psv_target = "data_simulator/p000009_sepsis.psv"
    patient_tag = "REAL-SEPSIS"
    
    if not os.path.exists(psv_target):
        print(f"[FATAL] Could not find {psv_target}. Did you download it?")
        sys.exit(1)

    sim = StreamingSimulatorReal(
        backend_url=f"ws://localhost:8000/ws/ambulance/{patient_tag}",
        psv_filepath=psv_target,
        patient_id=patient_tag
    )
    
    # Run at 2x speed
    await sim.stream_data(speed_multiplier=2.0)

if __name__ == "__main__":
    print("[NEXUS] PhysioNet Real-Data Triage Stream")
    print("=" * 60)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[STOP] Real data simulation stopped.")
