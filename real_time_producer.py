"""
Real-Time Producer: Unified data ingestion pipeline

Bridges real data sources → NEXUS backend
- Fetches data from configured adapter
- Runs anomaly detection
- Streams to backend via WebSocket
- Handles reconnection and error recovery
"""

import asyncio
import json
import websockets
import sys
import os
from typing import Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_engine.anomaly_detector import AnomalyDetector
from adapters.ehr_adapter import DataSourceAdapter


class RealTimeStreamProducer:
    """Handles real-time data streaming pipeline"""

    def __init__(
        self,
        adapter: DataSourceAdapter,
        backend_url: str = "ws://localhost:8000/ws/ambulance",
        patient_id: str = "REAL_P001"
    ):
        self.adapter = adapter
        self.backend_url = f"{backend_url}/{patient_id}"
        self.patient_id = patient_id
        self.anomaly_detector = AnomalyDetector()
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.stream_active = False
        self.sample_count = 0
        self.crisis_first_detected_at = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

    async def connect_backend(self) -> bool:
        """Connect to NEXUS backend WebSocket"""
        for attempt in range(self.max_reconnect_attempts):
            try:
                self.websocket = await websockets.connect(self.backend_url)
                print(f"[PRODUCER] ✓ Connected to backend: {self.backend_url}")
                self.reconnect_attempts = 0
                return True
            except Exception as e:
                self.reconnect_attempts += 1
                wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60s
                print(f"[PRODUCER] ✗ Connection attempt {attempt + 1}/{self.max_reconnect_attempts} failed")
                print(f"           Retrying in {wait_time}s... ({e})")
                await asyncio.sleep(wait_time)

        print("[ERROR] Failed to connect to backend after max attempts")
        return False

    async def start_streaming(
        self,
        polling_interval_seconds: int = 10,
        demo_mode: bool = False
    ):
        """
        Start streaming real-time vitals

        Args:
            polling_interval_seconds: How often to fetch vitals from adapter
            demo_mode: If True, generates test data patterns
        """
        await self.adapter.connect()

        if not await self.connect_backend():
            await self.adapter.disconnect()
            return

        self.stream_active = True
        print(f"\n[PRODUCER] Starting stream (interval: {polling_interval_seconds}s)")
        print("=" * 70)

        try:
            while self.stream_active:
                try:
                    # Fetch latest vitals
                    vitals_data = await self.adapter.fetch_vitals()

                    if not vitals_data:
                        # No data available yet
                        await asyncio.sleep(polling_interval_seconds)
                        continue

                    # Extract vitals
                    vitals = vitals_data["vitals"]

                    # Run anomaly detection
                    anomaly_detected, anomaly_score, details = self.anomaly_detector.detect_anomaly(vitals)

                    # Build enriched payload
                    enriched_payload = {
                        **vitals_data,
                        "anomaly_detected": anomaly_detected,
                        "anomaly_score": float(anomaly_score),
                        "alert_level": details.get("alert_level", "STABLE"),
                        "trend_analysis": details.get("trends", {})
                    }

                    # Send to backend
                    try:
                        await self.websocket.send(json.dumps(enriched_payload))
                    except websockets.exceptions.ConnectionClosed:
                        print("\n[PRODUCER] Connection lost, attempting reconnect...")
                        if await self.connect_backend():
                            await self.websocket.send(json.dumps(enriched_payload))
                        else:
                            break

                    # Track crisis detection
                    if anomaly_detected and not self.crisis_first_detected_at:
                        self.crisis_first_detected_at = self.sample_count
                        print(f"\n⚠️  CRISIS DETECTED at sample {self.sample_count}")

                    # Print status
                    self.sample_count += 1
                    self._print_sample_status(vitals, anomaly_detected, anomaly_score)

                    await asyncio.sleep(polling_interval_seconds)

                except Exception as e:
                    print(f"[STREAM ERROR] {e}")
                    await asyncio.sleep(polling_interval_seconds)

        except KeyboardInterrupt:
            print("\n\n[PRODUCER] Stream interrupted by user")
        finally:
            await self.stop_streaming()

    def _print_sample_status(self, vitals: dict, anomaly_detected: bool, anomaly_score: float):
        """Pretty print sample status"""
        status = "🚨 CRISIS" if anomaly_detected else "✓ NORMAL"
        hr = vitals.get("heart_rate", 0)
        sbp = vitals.get("systolic_bp", 0)
        dbp = vitals.get("diastolic_bp", 0)
        o2 = vitals.get("oxygen_saturation", 0)

        print(f"{status:12} | Sample {self.sample_count:4d} | "
              f"HR: {hr:3d} | BP: {sbp:3d}/{dbp:3d} | O2: {o2:3d}% | "
              f"Score: {anomaly_score:.2f}")

    async def stop_streaming(self):
        """Gracefully stop streaming"""
        self.stream_active = False

        if self.websocket:
            await self.websocket.close()

        await self.adapter.disconnect()

        print("\n" + "=" * 70)
        print(f"[PRODUCER] Stream ended")
        print(f"Total samples: {self.sample_count}")
        if self.crisis_first_detected_at:
            print(f"Crisis first detected at: Sample {self.crisis_first_detected_at}")
        else:
            print("No crisis events detected")
        print("=" * 70)


class RealTimeStreamConfig:
    """Configuration management"""

    @staticmethod
    def from_env() -> dict:
        """Load configuration from environment variables"""
        import os

        return {
            "adapter_type": os.getenv("ADAPTER_TYPE", "ehr"),  # ehr, mqtt, device
            "ehr_api_url": os.getenv("EHR_API_URL", "http://localhost:5000"),
            "ehr_api_key": os.getenv("EHR_API_KEY", "test_key"),
            "mqtt_broker": os.getenv("MQTT_BROKER", "localhost"),
            "mqtt_topic": os.getenv("MQTT_TOPIC", "ambulance/vitals"),
            "device_ws_url": os.getenv("DEVICE_WS_URL", "ws://localhost:9000/vitals"),
            "patient_id": os.getenv("PATIENT_ID", "REAL_P001"),
            "backend_url": os.getenv("BACKEND_URL", "ws://localhost:8000/ws/ambulance"),
            "polling_interval": int(os.getenv("POLLING_INTERVAL", "10")),
        }

    @staticmethod
    def create_adapter(config: dict) -> DataSourceAdapter:
        """Factory method to create appropriate adapter"""
        adapter_type = config.get("adapter_type", "ehr").lower()

        if adapter_type == "ehr":
            from adapters.ehr_adapter import EHRAdapter
            return EHRAdapter(
                api_url=config["ehr_api_url"],
                api_key=config["ehr_api_key"]
            )

        elif adapter_type == "mqtt":
            from adapters.mqtt_adapter import MQTTAdapter
            return MQTTAdapter(
                broker_url=config["mqtt_broker"],
                topic=config["mqtt_topic"],
                patient_id=config["patient_id"]
            )

        elif adapter_type == "device":
            from adapters.ehr_adapter import AmbulanceDeviceAdapter
            return AmbulanceDeviceAdapter(
                device_ws_url=config["device_ws_url"],
                patient_id=config["patient_id"]
            )

        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")


async def main():
    """Main entry point"""
    print("[NEXUS] Real-Time Data Stream Producer")
    print("=" * 70)

    # Load configuration
    config = RealTimeStreamConfig.from_env()
    print(f"[CONFIG] Adapter: {config['adapter_type'].upper()}")
    print(f"[CONFIG] Backend: {config['backend_url']}")
    print(f"[CONFIG] Patient ID: {config['patient_id']}")
    print(f"[CONFIG] Polling interval: {config['polling_interval']}s")
    print()

    # Create adapter
    try:
        adapter = RealTimeStreamConfig.create_adapter(config)
    except Exception as e:
        print(f"[ERROR] Failed to create adapter: {e}")
        return

    # Create producer
    producer = RealTimeStreamProducer(
        adapter=adapter,
        backend_url=config["backend_url"],
        patient_id=config["patient_id"]
    )

    # Start streaming
    await producer.start_streaming(
        polling_interval_seconds=config["polling_interval"]
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[STOP] Interrupted")
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
