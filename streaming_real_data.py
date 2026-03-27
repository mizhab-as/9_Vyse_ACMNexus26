"""
Real Data Streaming Simulator

Replaces synthetic data with actual MIMIC-III patient records.
Streams real vitals through ML anomaly detector → Backend → Dashboard

This is what you should use instead of streaming_simulator.py
"""

import asyncio
import json
import websockets
from datetime import datetime
import sys
import os

# Add current directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import real data loader and ML engine
from real_data_loader import RealDataLoader, MultiPatientRealDataLoader
from ml_engine.anomaly_detector import AnomalyDetector


class RealDataStreamingSimulator:
    def __init__(
        self,
        psv_file: str,
        backend_url: str = "ws://localhost:8000/ws/ambulance/P001",
        patient_id: str = None
    ):
        """
        Args:
            psv_file: Path to real data PSV file (e.g., data_simulator/p000009_sepsis.psv)
            backend_url: Backend WebSocket URL
            patient_id: Optional patient ID override
        """
        self.psv_file = psv_file
        self.backend_url = backend_url
        self.patient_id = patient_id or "REAL_P001"

        # Load real data
        self.real_data_loader = RealDataLoader(psv_file, self.patient_id)
        self.anomaly_detector = AnomalyDetector(window_size=10, contamination=0.1)
        self.crisis_detected_at = None

    async def stream_data(self, speed_multiplier: float = 1.0, interactive: bool = False):
        """
        Stream real patient data to backend

        Args:
            speed_multiplier: 1.0 = real-time (10s per sample), 10.0 = 10x faster
            interactive: Wait for user input between samples
        """
        try:
            async with websockets.connect(self.backend_url) as websocket:
                print(f"[OK] Connected to backend: {self.backend_url}\n")
                print("=" * 80)
                print(f"[REAL DATA] Streaming {os.path.basename(self.psv_file)}")
                print(f"[SCENARIO] {self.real_data_loader.scenario.upper()}")
                print(f"[PATIENTS] Total samples: {self.real_data_loader.total_samples()}")
                print("=" * 80 + "\n")

                sample_idx = 0

                for vitals_payload in self.real_data_loader.get_all_samples():
                    vitals = vitals_payload['vitals']
                    minute = sample_idx * 10 / 60

                    # Run through ML anomaly detector
                    anomaly_detected, anomaly_score, details = self.anomaly_detector.detect_anomaly(vitals)

                    # Enrich payload with ML results
                    enriched_payload = {
                        **vitals_payload,
                        "anomaly_detected": anomaly_detected,
                        "anomaly_score": float(anomaly_score),
                        "alert_level": details.get('alert_level', 'STABLE'),
                        "trend_analysis": details.get('trends', {})
                    }

                    # Send to backend
                    await websocket.send(json.dumps(enriched_payload))

                    # Track when crisis was first detected
                    if anomaly_detected and not self.crisis_detected_at:
                        self.crisis_detected_at = sample_idx
                        print(f"\n🚨 CRISIS DETECTED at sample {sample_idx} ({minute:.1f} min)")
                        print(f"   Anomaly Score: {anomaly_score:.2f}")
                        print("")

                    # Print status
                    if sample_idx % 10 == 0 or anomaly_detected:
                        status = "🚨 CRISIS" if anomaly_detected else "✓  STABLE"
                        print(f"{status} | Sample {sample_idx:3d} ({minute:5.1f} min) | "
                              f"HR: {int(vitals['heart_rate']):3d} | "
                              f"BP: {int(vitals['systolic_bp']):3d}/{int(vitals['diastolic_bp']):3d} | "
                              f"O2: {int(vitals['oxygen_saturation']):3d}% | "
                              f"Score: {anomaly_score:.2f}")

                    # Calculate delay based on speed multiplier
                    # Each sample is 10 seconds apart
                    delay_seconds = 10 / speed_multiplier
                    await asyncio.sleep(delay_seconds)

                    # Interactive mode: wait for user
                    if interactive:
                        input("Press Enter to continue...")

                    sample_idx += 1

                print(f"\n{'=' * 80}")
                print(f"[DONE] Stream complete")
                print(f"Total samples processed: {sample_idx}")
                if self.crisis_detected_at:
                    minutes = self.crisis_detected_at * 10 / 60
                    print(f"Crisis detected at: Sample {self.crisis_detected_at} ({minutes:.1f} minutes)")
                else:
                    print("No crisis events detected")
                print(f"{'=' * 80}\n")

        except Exception as e:
            print(f"[ERROR] Connection error: {e}")
            print("Did you start the backend? Try: cd backend && python -m uvicorn main:app --reload")


async def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("[NEXUS] Real Data Streaming Simulator")
    print("Load actual MIMIC-III patient records instead of synthetic data")
    print("=" * 80 + "\n")

    # Available PSV files
    data_dir = "data_simulator"
    psv_files = []

    if os.path.exists(data_dir):
        for file in sorted(os.listdir(data_dir)):
            if file.endswith(".psv"):
                psv_files.append(os.path.join(data_dir, file))

    if not psv_files:
        print("[ERROR] No PSV files found in data_simulator/")
        print("Make sure p000001_stable.psv or p000009_sepsis.psv exist")
        return

    print(f"Found {len(psv_files)} real data files:\n")
    for idx, file in enumerate(psv_files, 1):
        filename = os.path.basename(file)
        size_kb = os.path.getsize(file) / 1024
        print(f"  {idx}. {filename} ({size_kb:.1f} KB)")

    print("\nDefault: Using p000009_sepsis.psv (recommended - shows crisis progression)")
    print("To use a different file, modify PSV_FILE below\n")

    # Choose which PSV file to stream
    # Default: p000009_sepsis.psv (shows crisis)
    psv_file = "data_simulator/p000009_sepsis.psv"

    if not os.path.exists(psv_file):
        # Fallback to first available
        psv_file = psv_files[0]

    print(f"Using: {os.path.basename(psv_file)}\n")

    # Create simulator with real data
    simulator = RealDataStreamingSimulator(
        psv_file=psv_file,
        backend_url="ws://localhost:8000/ws/ambulance/P001",
        patient_id="REAL_P001"
    )

    print("[INFO] Starting real data stream at 5x speed for demo")
    print("       (use speed_multiplier=1.0 for real-time playback)\n")

    # Stream at 5x speed for demo (real-time would be 1.0)
    await simulator.stream_data(speed_multiplier=5.0, interactive=False)


if __name__ == "__main__":
    print("\n📊 NEXUS Real Data Streaming")
    print("Uses actual MIMIC-III patient records\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[STOP] Simulation stopped by user")
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
