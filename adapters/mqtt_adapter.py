"""
MQTT adapter for IoT devices (ambulance sensors, pulse oximeters, etc.)

Supports any MQTT-compatible device:
- Bluetooth vitals sensors
- Ambulance telemetry systems
- Hospital monitoring networks
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters.ehr_adapter import DataSourceAdapter


class MQTTAdapter(DataSourceAdapter):
    """MQTT-based adapter for real-time sensor data"""

    def __init__(self, broker_url: str, topic: str, patient_id: str = "MQTT_P001"):
        self.broker_url = broker_url
        self.topic = topic
        self.patient_id = patient_id
        self.client = None
        self.latest_vitals: Optional[Dict[str, Any]] = None
        self.connected = False

    async def connect(self):
        """Connect to MQTT broker"""
        try:
            import paho.mqtt.client as mqtt

            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect

            # Non-blocking connect
            self.client.connect(self.broker_url, 1883, keepalive=60)
            self.client.loop_start()

            # Wait for connection
            await asyncio.sleep(2)
            print(f"[MQTT] Connected to broker at {self.broker_url}")
            print(f"[MQTT] Listening on topic: {self.topic}")

        except ImportError:
            print("[ERROR] paho-mqtt not installed. Install with: pip install paho-mqtt")
        except Exception as e:
            print(f"[MQTT ERROR] Connection failed: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when MQTT connects"""
        if rc == 0:
            self.connected = True
            client.subscribe(self.topic)
            print("[MQTT] Connected and subscribed")
        else:
            print(f"[MQTT] Failed to connect, return code {rc}")

    def _on_message(self, client, userdata, msg):
        """Callback when MQTT message arrives"""
        try:
            payload = json.loads(msg.payload.decode())

            # Map common MQTT sensor names to NEXUS format
            self.latest_vitals = self.standardize_vitals({
                "patient_id": payload.get("patient_id", self.patient_id),
                "timestamp": datetime.utcnow().isoformat(),
                "heart_rate": payload.get("hr") or payload.get("heart_rate"),
                "systolic_bp": payload.get("sbp") or payload.get("systolic_bp"),
                "diastolic_bp": payload.get("dbp") or payload.get("diastolic_bp"),
                "respiratory_rate": payload.get("rr") or payload.get("respiratory_rate"),
                "oxygen_saturation": payload.get("spo2") or payload.get("oxygen_saturation"),
                "temperature": payload.get("temp") or payload.get("temperature"),
                "latitude": payload.get("lat"),
                "longitude": payload.get("lng"),
                "eta_minutes": payload.get("eta")
            })

        except json.JSONDecodeError:
            print(f"[MQTT ERROR] Invalid JSON: {msg.payload}")
        except Exception as e:
            print(f"[MQTT ERROR] {e}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback when MQTT disconnects"""
        self.connected = False
        if rc != 0:
            print(f"[MQTT] Unexpected disconnection: {rc}")

    async def fetch_vitals(self) -> Optional[Dict[str, Any]]:
        """Get latest vitals received from MQTT"""
        return self.latest_vitals

    async def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        print("[MQTT] Disconnected")


class MultiTopicMQTTAdapter(DataSourceAdapter):
    """Advanced MQTT adapter for multiple topics (one per vital sign)"""

    def __init__(self, broker_url: str, patient_id: str = "MQTT_P002"):
        self.broker_url = broker_url
        self.patient_id = patient_id
        self.client = None
        self.vitals_cache: Dict[str, Any] = {}

        # Topic to vitals mapping
        self.topic_mapping = {
            "vitals/heart_rate": "heart_rate",
            "vitals/blood_pressure/systolic": "systolic_bp",
            "vitals/blood_pressure/diastolic": "diastolic_bp",
            "vitals/respiratory_rate": "respiratory_rate",
            "vitals/oxygen_saturation": "oxygen_saturation",
            "vitals/temperature": "temperature",
            "location/gps": None  # Special handling
        }

    async def connect(self):
        """Connect and subscribe to all vital topics"""
        try:
            import paho.mqtt.client as mqtt

            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message

            self.client.connect(self.broker_url, 1883, keepalive=60)
            self.client.loop_start()

            await asyncio.sleep(2)
            print("[MQTT Multi] Connected to broker")

        except Exception as e:
            print(f"[MQTT Multi ERROR] {e}")

    def _on_connect(self, client, userdata, flags, rc):
        """Subscribe to all vital topics on connect"""
        if rc == 0:
            for topic in self.topic_mapping.keys():
                client.subscribe(topic)
            print(f"[MQTT Multi] Subscribed to {len(self.topic_mapping)} topics")

    def _on_message(self, client, userdata, msg):
        """Update vitals cache as messages arrive"""
        try:
            value = float(msg.payload.decode())

            if msg.topic == "location/gps":
                # Parse GPS data
                gps = json.loads(msg.payload.decode())
                self.vitals_cache["latitude"] = gps.get("lat")
                self.vitals_cache["longitude"] = gps.get("lng")
            else:
                # Map topic to vital name
                vital_name = self.topic_mapping.get(msg.topic)
                if vital_name:
                    self.vitals_cache[vital_name] = int(value) if vital_name != "temperature" else value

        except Exception as e:
            print(f"[MQTT Multi ERROR] {e}")

    async def fetch_vitals(self) -> Optional[Dict[str, Any]]:
        """Return standardized vitals when all required fields present"""
        required = ["heart_rate", "systolic_bp", "diastolic_bp", "oxygen_saturation"]

        if all(k in self.vitals_cache for k in required):
            return self.standardize_vitals({
                "patient_id": self.patient_id,
                "timestamp": datetime.utcnow().isoformat(),
                **self.vitals_cache
            })
        return None

    async def disconnect(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        print("[MQTT Multi] Disconnected")


# Test MQTT adapter
if __name__ == "__main__":
    import asyncio

    async def test():
        adapter = MQTTAdapter(
            broker_url="localhost",
            topic="ambulance/vitals",
            patient_id="P001"
        )

        await adapter.connect()

        # Simulate receiving data
        print("Waiting for MQTT messages (30 seconds)...")
        for i in range(30):
            vitals = await adapter.fetch_vitals()
            if vitals:
                print(f"[SAMPLE {i}] HR: {vitals['vitals']['heart_rate']}")
            await asyncio.sleep(1)

        await adapter.disconnect()

    asyncio.run(test())
