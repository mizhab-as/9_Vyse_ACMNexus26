"""
Real Data Streaming: Uses actual patient data from PhysioNet (MIMIC-III style)

This script:
1. Loads real sepsis patient data from p000009_sepsis.psv
2. Maps ICU columns → ambulance vitals
3. Streams through ML anomaly detector
4. Sends enriched data to backend via WebSocket

Data source: MIMIC-III-like ICU dataset with confirmed sepsis cases
Patient: p000009 (sepsis progression over ~48 hours in ICU)
"""

import asyncio
import json
import websockets
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Fix Unicode encoding on Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add current directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
os.chdir(script_dir)

from ml_engine.anomaly_detector import AnomalyDetector


class RealDataStreamLoader:
    def __init__(self, psv_file: str, backend_url: str = "ws://localhost:8000/ws/ambulance/P009"):
        """
        Load real patient data and set up streaming.

        Args:
            psv_file: Path to PSV file (e.g., 'data_simulator/p000009_sepsis.psv')
            backend_url: WebSocket endpoint for backend
        """
        self.psv_file = psv_file
        self.backend_url = backend_url
        self.patient_id = "P009_SEPSIS_REAL"
        self.anomaly_detector = AnomalyDetector(window_size=10, contamination=0.1)
        self.crisis_detected_at = None

        print(f"[DATA] Loading real patient data from: {psv_file}")
        try:
            self.df = pd.read_csv(psv_file, sep='|')
            print(f"[OK] Loaded {len(self.df)} samples from real patient record")
            print(f"[INFO] Columns: {list(self.df.columns[:10])}...")
        except Exception as e:
            print(f"[ERROR] Failed to load PSV: {e}")
            raise

    def map_icu_to_ambulance_vitals(self, row: pd.Series) -> dict:
        """
        Map ICU measurement columns to ambulance vitals format.
        Handles missing data gracefully with reasonable defaults.
        """
        # Handle NaN values - use defaults or interpolate
        def safe_int(val, default=0):
            return int(val) if pd.notna(val) and not np.isnan(val) else default

        def safe_float(val, default=0.0):
            return float(val) if pd.notna(val) and not np.isnan(val) else default

        vitals = {
            'heart_rate': safe_int(row.get('HR', 0), 75),
            'systolic_bp': safe_int(row.get('SBP', 0), 120),
            'diastolic_bp': safe_int(row.get('DBP', 0), 80),
            'respiratory_rate': safe_int(row.get('Resp', 0), 16),
            'oxygen_saturation': safe_int(row.get('O2Sat', 0), 98),
            'temperature': safe_float(row.get('Temp', 0), 37.0),
        }

        # Ensure reasonable bounds
        vitals['heart_rate'] = max(40, min(200, vitals['heart_rate']))
        vitals['systolic_bp'] = max(50, min(250, vitals['systolic_bp']))
        vitals['diastolic_bp'] = max(30, min(150, vitals['diastolic_bp']))
        vitals['respiratory_rate'] = max(8, min(50, vitals['respiratory_rate']))
        vitals['oxygen_saturation'] = max(50, min(100, vitals['oxygen_saturation']))
        vitals['temperature'] = max(35.0, min(42.0, vitals['temperature']))

        return vitals

    async def stream_real_data(self, speed_multiplier: float = 5.0):
        """
        Stream real patient data to backend.

        Args:
            speed_multiplier: 1.0 = real-time, 5.0 = 5x speed for demo
        """
        try:
            async with websockets.connect(self.backend_url) as websocket:
                print(f"[OK] Connected to backend: {self.backend_url}\n")
                print("[REAL DATA STREAM] Starting...")
                print("=" * 70)

                start_time = datetime.now()
                loop_count = 0

                while True:  # CONTINUOUS LOOP
                    loop_count += 1
                    print(f"\n[STREAM] Loop {loop_count} starting...")

                    for idx, row in self.df.iterrows():
                        # Skip completely empty rows
                        if pd.isna(row.get('HR')) and pd.isna(row.get('SBP')):
                            continue

                        # Map ICU data to ambulance vitals
                        vitals = self.map_icu_to_ambulance_vitals(row)

                        # Run through ML anomaly detector
                        anomaly_detected, anomaly_score, details = self.anomaly_detector.detect_anomaly(vitals)

                        # Create enriched payload
                        enriched_payload = {
                            'timestamp': f"Loop-{loop_count}-Sample-{idx}",
                            'patient_id': self.patient_id,
                            'vitals': vitals,
                            'location': {
                                'latitude': 0.0,
                                'longitude': 0.0,
                                'eta_minutes': 45  # Simulated ambulance ETA
                            },
                            'anomaly_detected': anomaly_detected,
                            'anomaly_score': float(anomaly_score),
                            'alert_level': details.get('alert_level', 'STABLE'),
                            'trend_analysis': details.get('trends', {}),
                            'sepsis_label': int(row.get('SepsisLabel', 0))  # Ground truth
                        }

                        # Send to backend
                        await websocket.send(json.dumps(enriched_payload))

                        # Track crisis detection
                        if anomaly_detected and not self.crisis_detected_at:
                            self.crisis_detected_at = idx
                            print(f"\n🚨 [ALERT] CRISIS DETECTED at sample {idx}!")

                        # Status every 5 samples
                        if idx % 10 == 0 or anomaly_detected:
                            status = "🚨 [CRISIS]" if anomaly_detected else "✓ [NORMAL]"
                            elapsed = (datetime.now() - start_time).total_seconds()
                            print(f"{status} | Loop {loop_count} Sample {idx:3d} ({elapsed:6.1f}s) | "
                                  f"HR: {vitals['heart_rate']:3d} | "
                                  f"BP: {vitals['systolic_bp']:3d}/{vitals['diastolic_bp']:3d} | "
                                  f"O2: {vitals['oxygen_saturation']:3d}% | "
                                  f"Temp: {vitals['temperature']:.1f}°C | "
                                  f"Score: {anomaly_score:.2f}")

                        # Delay based on speed multiplier
                        delay = 10 / speed_multiplier  # 10 seconds between ICU measurements @ 1x
                        await asyncio.sleep(delay)  # Sleep for calculated seconds

        except Exception as e:
            print(f"[ERROR] Connection error: {e}")
            print("Make sure backend is running: python -m uvicorn backend.main:app --reload")


async def main():
    # Use the real sepsis patient data
    loader = RealDataStreamLoader(
        psv_file='data_simulator/p000009_sepsis.psv',
        backend_url='ws://localhost:8000/ws/ambulance/P009'
    )

    print("\n")
    print("=" * 70)
    print("NEXUS: REAL PATIENT DATA STREAMING")
    print("Dataset: p000009_sepsis.psv (Confirmed sepsis case from MIMIC-III)")
    print("Patient: Septic shock progression over ICU stay")
    print("=" * 70)
    print()

    # Stream at 5x speed for demo (1.0 = real-time)
    await loader.stream_real_data(speed_multiplier=5.0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[STOP] Stream stopped by user")
    except Exception as e:
        print(f"\n[FATAL] {e}")
        sys.exit(1)
