#!/usr/bin/env python
"""
Safe wrapper to run the streaming simulator with all path setup
"""
import sys
import os

# Get absolute path to project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Set up Python path FIRST, before any imports
sys.path.insert(0, PROJECT_ROOT)

# Now we can safely import and run
try:
    from data_simulator.data_generator import RealisticAmbulanceDataSimulator
    from ml_engine.anomaly_detector import AnomalyDetector
    import asyncio
    import json
    import websockets
    from datetime import datetime, timedelta

    # Fix Unicode on Windows
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    class StreamingSimulator:
        def __init__(self, backend_url: str = "ws://localhost:8000/ws/ambulance/P001"):
            self.backend_url = backend_url
            self.simulator = RealisticAmbulanceDataSimulator(patient_id="P001", transport_minutes=45)
            self.anomaly_detector = AnomalyDetector(window_size=10, contamination=0.1)
            self.crisis_detected_at = None

        async def stream_data(self, speed_multiplier: float = 1.0, interactive: bool = False):
            try:
                async with websockets.connect(self.backend_url) as websocket:
                    print(f"Connected to backend: {self.backend_url}")

                    for sample_idx in range(self.simulator.total_samples):
                        vitals_payload = self.simulator.get_sample_for_streaming(sample_idx)
                        vitals = vitals_payload['vitals']
                        minute = vitals_payload['timestamp']

                        anomaly_detected, anomaly_score, details = self.anomaly_detector.detect_anomaly(vitals)

                        enriched_payload = {
                            **vitals_payload,
                            "anomaly_detected": anomaly_detected,
                            "anomaly_score": float(anomaly_score),
                            "alert_level": details['alert_level'],
                            "trend_analysis": details['trends']
                        }

                        await websocket.send(json.dumps(enriched_payload))

                        if anomaly_detected and not self.crisis_detected_at:
                            self.crisis_detected_at = sample_idx
                            print(f"CRISIS DETECTED at {vitals_payload['timestamp']}")

                        if sample_idx % 10 == 0 or anomaly_detected:
                            status = "CRISIS" if anomaly_detected else "NORMAL"
                            print(f"{status} | Sample {sample_idx:3d} | "
                                  f"HR: {vitals['heart_rate']:3d} bpm | "
                                  f"BP: {vitals['systolic_bp']:3d}/{vitals['diastolic_bp']:3d} | "
                                  f"O2: {vitals['oxygen_saturation']:3d}% | "
                                  f"Anomaly Score: {anomaly_score:.2f}")

                        delay = (self.simulator.sample_interval_seconds / speed_multiplier)
                        await asyncio.sleep(delay / 1000) if delay < 1 else await asyncio.sleep(0)

                        if interactive:
                            input("Press Enter to continue...")

                    print(f"\nStream complete. Crisis detected at sample {self.crisis_detected_at}")

            except Exception as e:
                print(f"Connection error: {e}")
                print("Did you start the backend? Try: cd backend && python -m uvicorn main:app --reload")

    async def main():
        simulator = StreamingSimulator(backend_url="ws://localhost:8000/ws/ambulance/P001")
        print("Starting real-time vitals stream simulation...\n")
        await simulator.stream_data(speed_multiplier=5.0, interactive=False)

    if __name__ == "__main__":
        print("Ambulance-to-Hospital Real-Time Triage Simulator")
        print("=" * 60)
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n\nSimulation stopped by user")

except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"sys.path[0]: {sys.path[0]}")
    print("\nTrying to debug...")
    print(f"data_simulator exists: {os.path.exists(os.path.join(PROJECT_ROOT, 'data_simulator'))}")
    print(f"ml_engine exists: {os.path.exists(os.path.join(PROJECT_ROOT, 'ml_engine'))}")
    sys.exit(1)
