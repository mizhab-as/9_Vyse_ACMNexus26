# Real-Time Dataset Integration Guide

## Architecture Overview

```
Real Data Source(s) → Data Adapter → Anomaly Detector → Backend → Dashboard
    ↓
- Ambulance Telemetry
- Hospital Monitoring Systems (e.g., Philips, GE)
- EHR APIs
- IoT Sensors
```

## Data Source Options

### 1. **Ambulance Telemetry Systems**
- **Zoll MyCare API** - Patient monitoring
- **Phillips HeartStart** - Defibrillator data
- **Stryker PowerLoad** - Ambulance management
- **Custom IoT Devices** - Bluetooth/WiFi vitals sensors

### 2. **Hospital Systems**
- **FHIR (HL7 FHIR)** - Standard healthcare interop
- **DICOM** - Medical imaging
- **Hospital EHR APIs** - Epic, Cerner, etc.

### 3. **Real-Time Monitoring Devices**
- **Pulse Oximeters** - O2 saturation
- **ECG Monitors** - Heart rate/rhythm
- **Blood Pressure Cuffs** - BP data
- **Thermometers** - Temperature sensors

## Implementation Steps

### Step 1: Create Data Adapter (Replace Simulator)

```python
# real_time_adapter.py
import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any

class DataSourceAdapter(ABC):
    """Base class for any real data source"""

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def fetch_vitals(self) -> Dict[str, Any]:
        """Returns standardized vitals in NEXUS format"""
        pass

    @abstractmethod
    async def disconnect(self):
        pass
```

### Step 2: Implement Specific Adapters

#### Option A: REST API Source (Hospital EHR)
```python
# adapters/ehr_adapter.py
import aiohttp
from datetime import datetime

class EHRAdapter(DataSourceAdapter):
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.session = None

    async def connect(self):
        self.session = aiohttp.ClientSession()
        print("[EHR] Connected to EHR system")

    async def fetch_vitals(self) -> dict:
        """Fetch vitals from EHR API"""
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            async with self.session.get(
                f"{self.api_url}/api/vitals/latest",
                headers=headers,
                timeout=5
            ) as resp:
                data = await resp.json()

                # Transform EHR format → NEXUS format
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "patient_id": data["patient_id"],
                    "vitals": {
                        "heart_rate": data["heart_rate"],
                        "systolic_bp": data["systolic_pressure"],
                        "diastolic_bp": data["diastolic_pressure"],
                        "respiratory_rate": data["respiration_rate"],
                        "oxygen_saturation": data["o2_sat"],
                        "temperature": data["temp_celsius"]
                    },
                    "location": {
                        "latitude": data.get("lat", 0.0),
                        "longitude": data.get("lng", 0.0),
                        "eta_minutes": data.get("eta", 0)
                    }
                }
        except Exception as e:
            print(f"[EHR ERROR] {e}")
            return None

    async def disconnect(self):
        if self.session:
            await self.session.close()
```

#### Option B: MQTT/IoT Devices
```python
# adapters/mqtt_adapter.py
import paho.mqtt.client as mqtt
import json
import asyncio
from datetime import datetime

class MQTTAdapter(DataSourceAdapter):
    def __init__(self, broker_url: str, topic: str):
        self.broker_url = broker_url
        self.topic = topic
        self.client = None
        self.latest_vitals = None

    async def connect(self):
        self.client = mqtt.Client()
        self.client.on_message = self._on_message
        self.client.connect(self.broker_url, 1883)
        self.client.subscribe(self.topic)
        self.client.loop_start()
        print("[MQTT] Connected to broker")

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        payload = json.loads(msg.payload.decode())
        self.latest_vitals = {
            "timestamp": datetime.utcnow().isoformat(),
            "patient_id": payload.get("patient_id"),
            "vitals": {
                "heart_rate": payload["hr"],
                "systolic_bp": payload["sbp"],
                "diastolic_bp": payload["dbp"],
                "respiratory_rate": payload["rr"],
                "oxygen_saturation": payload["spo2"],
                "temperature": payload["temp"]
            },
            "location": {
                "latitude": payload.get("lat", 0.0),
                "longitude": payload.get("lng", 0.0),
                "eta_minutes": payload.get("eta", 0)
            }
        }

    async def fetch_vitals(self) -> dict:
        return self.latest_vitals

    async def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
```

#### Option C: WebSocket Stream (Live Devices)
```python
# adapters/websocket_adapter.py
import websockets
import json
from datetime import datetime

class WebSocketDeviceAdapter(DataSourceAdapter):
    def __init__(self, device_url: str, patient_id: str):
        self.device_url = device_url
        self.patient_id = patient_id
        self.websocket = None
        self.latest_vitals = None

    async def connect(self):
        self.websocket = await websockets.connect(self.device_url)
        asyncio.create_task(self._listen())
        print("[WS] Connected to device stream")

    async def _listen(self):
        """Listen for device updates"""
        try:
            async for message in self.websocket:
                payload = json.loads(message)
                self.latest_vitals = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "patient_id": self.patient_id,
                    "vitals": {
                        "heart_rate": payload["heart_rate"],
                        "systolic_bp": payload["sbp"],
                        "diastolic_bp": payload["dbp"],
                        "respiratory_rate": payload["rr"],
                        "oxygen_saturation": payload["spo2"],
                        "temperature": payload["temp"]
                    },
                    "location": payload.get("location", {})
                }
        except Exception as e:
            print(f"[WS ERROR] {e}")

    async def fetch_vitals(self) -> dict:
        return self.latest_vitals

    async def disconnect(self):
        if self.websocket:
            await self.websocket.close()
```

### Step 3: Real-Time Stream Producer

```python
# real_time_producer.py
import asyncio
import json
import websockets
from typing import Optional
from ml_engine.anomaly_detector import AnomalyDetector

class RealTimeStreamProducer:
    def __init__(self, adapter: DataSourceAdapter, backend_url: str = "ws://localhost:8000/ws/ambulance"):
        self.adapter = adapter
        self.backend_url = backend_url
        self.anomaly_detector = AnomalyDetector()
        self.websocket = None
        self.stream_active = False

    async def connect_backend(self):
        """Connect to NEXUS backend"""
        patient_id = "REAL_P001"  # Replace with actual patient ID
        try:
            self.websocket = await websockets.connect(
                f"{self.backend_url}/{patient_id}"
            )
            print(f"[PRODUCER] Connected to backend")
            return True
        except Exception as e:
            print(f"[ERROR] Backend connection failed: {e}")
            return False

    async def start_streaming(self, polling_interval_seconds: int = 10):
        """Poll real data and stream to backend"""
        await self.adapter.connect()

        if not await self.connect_backend():
            return

        self.stream_active = True
        sample_count = 0

        try:
            while self.stream_active:
                # Fetch latest vitals
                vitals_data = await self.adapter.fetch_vitals()

                if not vitals_data:
                    await asyncio.sleep(polling_interval_seconds)
                    continue

                # Run through anomaly detector
                vitals = vitals_data["vitals"]
                anomaly_detected, anomaly_score, details = self.anomaly_detector.detect_anomaly(vitals)

                # Enrich payload
                enriched_payload = {
                    **vitals_data,
                    "anomaly_detected": anomaly_detected,
                    "anomaly_score": float(anomaly_score),
                    "alert_level": details.get("alert_level", "STABLE"),
                    "trend_analysis": details.get("trends", {})
                }

                # Send to backend
                await self.websocket.send(json.dumps(enriched_payload))

                sample_count += 1
                status = "[CRISIS]" if anomaly_detected else "[NORMAL]"
                print(f"{status} | Sample {sample_count} | HR: {vitals['heart_rate']} | "
                      f"Score: {anomaly_score:.2f}")

                # Poll interval
                await asyncio.sleep(polling_interval_seconds)

        except Exception as e:
            print(f"[STREAM ERROR] {e}")
        finally:
            await self.adapter.disconnect()
            if self.websocket:
                await self.websocket.close()

    async def stop_streaming(self):
        self.stream_active = False
```

### Step 4: Launch Real-Time Producer

```bash
# real_time_runner.py (Terminal 3 replacement)
import asyncio
import sys
import os
from adapters.ehr_adapter import EHRAdapter
from real_time_producer import RealTimeStreamProducer

async def main():
    # Choose adapter based on data source

    # Option 1: EHR System
    adapter = EHRAdapter(
        api_url="https://hospital-ehr.example.com",
        api_key="YOUR_API_KEY"
    )

    # Option 2: MQTT Devices
    # adapter = MQTTAdapter("mqtt.example.com", "ambulance/vitals")

    # Option 3: WebSocket Device
    # adapter = WebSocketDeviceAdapter("ws://device.local:8080/stream", "patient_001")

    producer = RealTimeStreamProducer(adapter)
    await producer.start_streaming(polling_interval_seconds=10)

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration (Environment Variables)

Create `.env.real-time`:

```env
# EHR Configuration
EHR_API_URL=https://hospital-ehr.example.com
EHR_API_KEY=your_api_key_here
EHR_PATIENT_ID=P001

# MQTT Configuration
MQTT_BROKER=mqtt.example.com
MQTT_TOPIC=ambulance/vitals
MQTT_PORT=1883

# WebSocket Device
DEVICE_WS_URL=ws://device.local:8080/stream

# Backend
BACKEND_WS_URL=ws://localhost:8000/ws/ambulance

# Polling
DATA_POLLING_INTERVAL=10  # seconds
```

## Security Considerations

### 1. HIPAA Compliance (US Healthcare)
```python
# hipaa_middleware.py
from functools import wraps
import hashlib
from datetime import datetime, timedelta

class HIPAAMiddleware:
    """Ensure HIPAA compliance for patient data"""

    @staticmethod
    def encrypt_patient_id(patient_id: str) -> str:
        """Hash patient IDs in logs"""
        return hashlib.sha256(patient_id.encode()).hexdigest()[:16]

    @staticmethod
    def audit_log(action: str, patient_id: str, timestamp: str):
        """Log all data access"""
        hashed_id = HIPAAMiddleware.encrypt_patient_id(patient_id)
        with open("hipaa_audit.log", "a") as f:
            f.write(f"{timestamp} | {action} | {hashed_id}\n")

    @staticmethod
    def validate_data_retention(age_hours: int = 24) -> bool:
        """Delete data older than retention period"""
        return True
```

### 2. API Authentication
```python
# Use OAuth2 / JWT tokens
from fastapi_jwt_auth import AuthJWT

@app.websocket("/ws/ambulance/{patient_id}")
async def websocket_ambulance(websocket: WebSocket, patient_id: str, token: str):
    # Validate token
    # Allow only authenticated sources
    pass
```

### 3. Data Validation
```python
class VitalsValidator:
    """Validate incoming vitals are within physiological ranges"""

    SAFE_RANGES = {
        "heart_rate": (40, 200),
        "systolic_bp": (60, 250),
        "diastolic_bp": (30, 150),
        "oxygen_saturation": (50, 100),
        "temperature": (32, 42),
        "respiratory_rate": (5, 60)
    }

    @staticmethod
    def is_valid(vitals: dict) -> bool:
        for key, (min_val, max_val) in VitalsValidator.SAFE_RANGES.items():
            if key in vitals and not (min_val <= vitals[key] <= max_val):
                return False
        return True
```

## Deployment Architecture

```
┌─────────────────────────────────────┐
│   Real Data Sources                 │
│  (EHR, Devices, Ambulance Systems)  │
└────────────┬────────────────────────┘
             │ HTTP/MQTT/WS
             ↓
┌─────────────────────────────────────┐
│   Kafka/RabbitMQ (Message Queue)    │ ← Optional for scale
└────────────┬────────────────────────┘
             │
     ┌───────┴────────┐
     ↓                ↓
┌─────────────┐  ┌──────────────────────┐
│ Validator   │  │ Real-Time Producer   │
│ & Enricher  │  │ (Anomaly Detection)  │
└────┬────────┘  └──────────┬───────────┘
     │                      │
     └──────────┬───────────┘
                ↓
        ┌───────────────────┐
        │  FastAPI Backend  │
        │  WebSocket Hub    │
        └────────┬──────────┘
                 │
        ┌────────┴────────┐
        ↓                 ↓
     ┌──────────┐    ┌──────────┐
     │ Paramedic│    │ER Team   │
     │Dashboard │    │Dashboard │
     └──────────┘    └──────────┘
```

## Testing Real-Time Integration

```python
# test_real_time.py
import pytest
from adapters.ehr_adapter import EHRAdapter
from real_time_producer import RealTimeStreamProducer

@pytest.mark.asyncio
async def test_ehr_adapter_connection():
    adapter = EHRAdapter("http://test.local", "test_key")
    await adapter.connect()
    vitals = await adapter.fetch_vitals()
    assert vitals is not None
    assert "vitals" in vitals
    await adapter.disconnect()

@pytest.mark.asyncio
async def test_data_validation():
    from hipaa_middleware import VitalsValidator

    valid_vitals = {
        "heart_rate": 80,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "respiratory_rate": 16,
        "oxygen_saturation": 98,
        "temperature": 37.0
    }

    assert VitalsValidator.is_valid(valid_vitals)

    invalid_vitals = {
        "heart_rate": 400,  # Out of range
        "systolic_bp": 120,
        "diastolic_bp": 80
    }

    assert not VitalsValidator.is_valid(invalid_vitals)
```

## Launching Real-Time System

```bash
# Terminal 1: Backend (unchanged)
cd backend && python -m uvicorn main:app --reload

# Terminal 2: Frontend (unchanged)
cd frontend && npm start

# Terminal 3: Real-Time Producer (new)
python real_time_runner.py
```

## Monitoring & Observability

```python
# monitoring.py
import prometheus_client
from prometheus_client import Counter, Histogram

data_points_received = Counter('data_points_received', 'Total vitals received')
anomalies_detected = Counter('anomalies_detected', 'Total anomalies')
processing_time = Histogram('vitals_processing_seconds', 'Processing time')
connection_errors = Counter('connection_errors', 'Connection failures')
```

## Next Steps

1. **Choose Data Source** - Select which real system to integrate with
2. **Implement Adapter** - Create adapter for your specific data format
3. **Test Locally** - Use mock data before connecting to production
4. **HIPAA Audit** - Ensure compliance before going live
5. **Monitor** - Set up dashboards for data pipeline health
6. **Deploy** - Launch in hospital environment with proper security

