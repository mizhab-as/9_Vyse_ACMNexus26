"""
Streaming Simulator: End-to-end integration test.

This script:
1. Generates synthetic 45-minute ambulance data
2. Streams each vitals sample through the ML anomaly detector
3. Sends enriched data (with triage briefing) to backend via WebSocket

Use this for demo/testing without real ambulance hardware.
"""

import asyncio
import json
import websockets
from datetime import datetime, timedelta
import sys
import os

# Fix Unicode encoding on Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add current directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Change to script directory to ensure relative imports work
os.chdir(script_dir)

from data_simulator.data_generator import RealisticAmbulanceDataSimulator
from ml_engine.anomaly_detector import AnomalyDetector

class StreamingSimulator:
    def __init__(self, backend_url: str = "ws://localhost:8000/ws/ambulance/P001"):
        self.backend_url = backend_url
        self.simulator = RealisticAmbulanceDataSimulator(patient_id="P001", transport_minutes=45)
        self.anomaly_detector = AnomalyDetector(window_size=10, contamination=0.1)
        self.crisis_detected_at = None

    async def stream_data(self, speed_multiplier: float = 1.0, interactive: bool = False):
        """
        Streams synthetic data to backend.

        Args:
            speed_multiplier: 1.0 = real-time, 10.0 = 10x faster for demo
            interactive: If True, waits for user input between samples
        """
        try:
            async with websockets.connect(self.backend_url) as websocket:
                print(f"[OK] Connected to backend: {self.backend_url}")

                for sample_idx in range(self.simulator.total_samples):
                    # Generate vitals for this sample
                    vitals_payload = self.simulator.get_sample_for_streaming(sample_idx)
                    vitals = vitals_payload['vitals']
                    minute = vitals_payload['timestamp']

                    # Run through ML anomaly detector
                    anomaly_detected, anomaly_score, details = self.anomaly_detector.detect_anomaly(vitals)

                    # Enrich payload with ML results
                    enriched_payload = {
                        **vitals_payload,
                        "anomaly_detected": anomaly_detected,
                        "anomaly_score": float(anomaly_score),
                        "alert_level": details['alert_level'],
                        "trend_analysis": details['trends']
                    }

                    # Send to backend
                    await websocket.send(json.dumps(enriched_payload))

                    # Track when crisis was first detected
                    if anomaly_detected and not self.crisis_detected_at:
                        self.crisis_detected_at = sample_idx
                        print(f"[ALERT] Sample {sample_idx} - CRISIS DETECTED at {vitals_payload['timestamp']}")

                    # Print status
                    if sample_idx % 10 == 0 or anomaly_detected:
                        status = "[CRISIS]" if anomaly_detected else "[NORMAL]"
                        print(f"{status} | Sample {sample_idx:3d} | "
                              f"HR: {vitals['heart_rate']:3d} bpm | "
                              f"BP: {vitals['systolic_bp']:3d}/{vitals['diastolic_bp']:3d} | "
                              f"O2: {vitals['oxygen_saturation']:3d}% | "
                              f"Anomaly Score: {anomaly_score:.2f}")

                    # Sleep based on speed multiplier
                    delay = (self.simulator.sample_interval_seconds / speed_multiplier)
                    await asyncio.sleep(delay / 1000) if delay < 1 else await asyncio.sleep(0)

                    # Interactive mode: wait for user
                    if interactive:
                        input("Press Enter to continue...")

                print(f"\n[DONE] Stream complete. Crisis detected at sample {self.crisis_detected_at}")

        except Exception as e:
            print(f"[ERROR] Connection error: {e}")
            print("Did you start the backend? Try: python -m backend.main")

async def main():
    simulator = StreamingSimulator(backend_url="ws://localhost:8000/ws/ambulance/P001")
    print("[INFO] Starting real-time vitals stream simulation...\n")

    # Stream at 5x speed for demo (real-time would be 1.0)
    await simulator.stream_data(speed_multiplier=5.0, interactive=False)

if __name__ == "__main__":
    print("[NEXUS] Ambulance-to-Hospital Real-Time Triage Simulator")
    print("=" * 60)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[STOP] Simulation stopped by user")
