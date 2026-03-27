"""
Example: Real-Time Integration with Mock Data

This script demonstrates how to use the real-time adapters without
needing actual medical devices or hospital systems.

Run this to test the full pipeline locally:
  python example_real_time.py
"""

import asyncio
import json
from typing import Dict, Any, Optional
import sys
import os
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adapters.ehr_adapter import DataSourceAdapter
from real_time_producer import RealTimeStreamProducer


class MockEHRAdapter(DataSourceAdapter):
    """
    Mock EHR adapter that simulates a hospital EHR system.
    Generates realistic vital trends (normal → crisis progression).
    """

    def __init__(self, simulation_minutes: int = 5):
        self.sample_count = 0
        self.start_time = datetime.utcnow()
        self.simulation_minutes = simulation_minutes
        self.total_samples = (simulation_minutes * 60) // 10  # 10s intervals
        self.crisis_progression = False

    async def connect(self):
        print("[MOCK-EHR] Connected to mock hospital system")

    def _get_sample(self, idx: int) -> Dict[str, Any]:
        """Generate vitals for sample index"""
        elapsed_minutes = (idx * 10) / 60.0  # Each sample is 10 seconds

        # Normal vitals (first 3 minutes)
        base_hr = 80
        base_sbp = 120
        base_dbp = 80
        base_rr = 16
        base_spo2 = 98
        base_temp = 37.0

        # Crisis detection at 50% of timeline (simulating deterioration)
        if elapsed_minutes > self.simulation_minutes * 0.5:
            # Tachycardia
            base_hr += int((elapsed_minutes - self.simulation_minutes * 0.5) * 2)

            # Hypotension
            base_sbp -= int((elapsed_minutes - self.simulation_minutes * 0.5) * 1.5)

            # Tachypnea
            base_rr += int((elapsed_minutes - self.simulation_minutes * 0.5) * 0.5)

            # Desaturation
            base_spo2 -= int((elapsed_minutes - self.simulation_minutes * 0.5) * 0.3)

            self.crisis_progression = True

        # Add small random fluctuations (realistic sensor noise)
        vitals = {
            "heart_rate": max(40, min(200, base_hr + random.randint(-3, 3))),
            "systolic_bp": max(60, min(250, base_sbp + random.randint(-2, 2))),
            "diastolic_bp": max(30, min(150, base_dbp + random.randint(-2, 2))),
            "respiratory_rate": max(5, min(60, base_rr + random.randint(-1, 1))),
            "oxygen_saturation": max(50, min(100, base_spo2 + random.randint(-1, 1))),
            "temperature": base_temp + random.uniform(-0.2, 0.2),
        }

        # Simulate GPS location (ambulance moving)
        lat = 40.7128 + (elapsed_minutes / 100) * 0.01  # Moving north
        lng = -74.0060 + (elapsed_minutes / 100) * 0.01  # Moving east
        eta = max(2, 15 - int(elapsed_minutes))

        return {
            "patient_id": "DEMO_P001",
            "timestamp": (self.start_time + timedelta(seconds=idx * 10)).isoformat(),
            **vitals,
            "latitude": lat,
            "longitude": lng,
            "eta_minutes": eta,
        }

    async def fetch_vitals(self) -> Optional[Dict[str, Any]]:
        """Return next sample in sequence"""
        if self.sample_count >= self.total_samples:
            return None  # Simulation complete

        sample = self._get_sample(self.sample_count)
        self.sample_count += 1
        return self.standardize_vitals(sample)

    async def disconnect(self):
        print(f"[MOCK-EHR] Disconnected (simulated {self.sample_count} samples)")


class MockMQTTAdapter(DataSourceAdapter):
    """Mock MQTT adapter for testing IoT device integration"""

    def __init__(self):
        self.sample_count = 0
        self.crisis_at_sample = 30  # Trigger crisis after 30 samples (5 mins)

    async def connect(self):
        print("[MOCK-MQTT] Connected to simulated MQTT broker")

    async def fetch_vitals(self) -> Optional[Dict[str, Any]]:
        """Simulate sensor readings"""
        if self.sample_count > 100:
            return None

        # Simulate crisis onset
        if self.sample_count < self.crisis_at_sample:
            # Stable period
            vitals = {
                "patient_id": "MQTT_P001",
                "heart_rate": 75 + random.randint(-5, 5),
                "systolic_bp": 118 + random.randint(-3, 3),
                "diastolic_bp": 78 + random.randint(-3, 3),
                "respiratory_rate": 15 + random.randint(-2, 2),
                "oxygen_saturation": 98 + random.randint(-1, 0),
                "temperature": 37.0 + random.uniform(-0.1, 0.1),
            }
        else:
            # Crisis period - septic shock
            crisis_progress = self.sample_count - self.crisis_at_sample
            vitals = {
                "patient_id": "MQTT_P001",
                "heart_rate": 95 + crisis_progress * 1.5,
                "systolic_bp": 110 - crisis_progress * 1.0,
                "diastolic_bp": 72 - crisis_progress * 0.8,
                "respiratory_rate": 18 + crisis_progress * 0.5,
                "oxygen_saturation": 97 - crisis_progress * 0.2,
                "temperature": 37.8 + crisis_progress * 0.05,
            }

        self.sample_count += 1

        return self.standardize_vitals(vitals)

    async def disconnect(self):
        print(f"[MOCK-MQTT] Disconnected (simulated {self.sample_count} samples)")


async def example_ehr_integration():
    """Example: Mock EHR system integration"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Hospital EHR REST API Integration")
    print("=" * 70)

    # Create mock adapter simulating an EHR system
    adapter = MockEHRAdapter(simulation_minutes=5)

    # Create producer
    producer = RealTimeStreamProducer(
        adapter=adapter,
        backend_url="ws://localhost:8000/ws/ambulance",
        patient_id="DEMO_P001"
    )

    # Stream data
    await producer.start_streaming(polling_interval_seconds=10)


async def example_mqtt_integration():
    """Example: MQTT IoT device integration"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: MQTT IoT Device Integration")
    print("=" * 70)

    # Create mock MQTT adapter
    adapter = MockMQTTAdapter()

    # Create producer
    producer = RealTimeStreamProducer(
        adapter=adapter,
        backend_url="ws://localhost:8000/ws/ambulance",
        patient_id="MQTT_P001"
    )

    # Stream data
    await producer.start_streaming(polling_interval_seconds=5)


async def main():
    """Run examples"""
    print("\n" + "=" * 70)
    print("NEXUS Real-Time Integration Examples")
    print("=" * 70)
    print("\nThese examples demonstrate how to integrate REAL data sources:")
    print("  1. EHR/Hospital API systems")
    print("  2. MQTT IoT devices")
    print("  3. WebSocket medical devices")
    print("\nMake sure backend is running:")
    print("  cd backend && python -m uvicorn main:app --reload")
    print("\nThen run this example. Dashboard at: http://localhost:3000")
    print()

    # Choose which example to run
    print("Available examples:")
    print("  1. EHR System Integration (mock)")
    print("  2. MQTT Device Integration (mock)")
    print()

    choice = input("Run example (1 or 2, or 'q' to quit): ").strip().lower()

    if choice == "1":
        await example_ehr_integration()
    elif choice == "2":
        await example_mqtt_integration()
    else:
        print("Exiting")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
