# Real-Time Dataset Integration - Quick Start

## Overview

This guide shows how to replace the simulator with real-time data from your actual data sources:
- Hospital EHR systems (Epic, Cerner)
- MQTT IoT devices (ambulance sensors)
- WebSocket medical devices
- Custom APIs

## Files Created

```
adapters/
├── ehr_adapter.py         # REST API / EHR / FHIR integration
├── mqtt_adapter.py        # MQTT IoT device integration
└── __init__.py

real_time_producer.py      # Unified streaming pipeline
.env.real-time.example     # Configuration template
REAL_TIME_INTEGRATION.md   # Detailed technical docs
```

## Quick Start (3 Steps)

### Step 1: Choose Your Data Source

**Option A: EHR/REST API (Hospital Systems)**
```bash
cp .env.real-time.example .env
# Edit .env
# ADAPTER_TYPE=ehr
# EHR_API_URL=http://your-hospital-ehr.com
# EHR_API_KEY=your_key
```

**Option B: MQTT Devices**
```bash
# Edit .env
# ADAPTER_TYPE=mqtt
# MQTT_BROKER=mqtt.example.com
# MQTT_TOPIC=ambulance/vitals
```

**Option C: WebSocket Device**
```bash
# Edit .env
# ADAPTER_TYPE=device
# DEVICE_WS_URL=ws://device.local:8080/vitals
```

### Step 2: Launch System (3 terminals)

**Terminal 1 - Backend**
```bash
cd backend && python -m uvicorn main:app --reload
```

**Terminal 2 - Frontend**
```bash
cd frontend && npm start
```

**Terminal 3 - Real-Time Producer (NEW!)**
```bash
python real_time_producer.py
```

### Step 3: Monitor Dashboard

Open http://localhost:3000

You'll see:
- Live vitals from your real data source
- Anomalies detected in real-time
- AI-powered triage briefings
- Crisis alerts

---

## Data Source Examples

### Example 1: Hospital EHR REST API

**Your EHR API returns:**
```json
{
  "patient_id": "P001",
  "timestamp": "2026-03-27T12:30:00Z",
  "heart_rate": 85,
  "systolic_pressure": 120,
  "diastolic_pressure": 80,
  "respiration_rate": 16,
  "o2_sat": 98,
  "temp_celsius": 37.0,
  "lat": 40.7128,
  "lng": -74.0060,
  "eta": 12
}
```

**Configuration:**
```bash
ADAPTER_TYPE=ehr
EHR_API_URL=http://your-hospital-ehr.com
EHR_API_KEY=your_authentication_key
```

**Code:**
```python
from adapters.ehr_adapter import EHRAdapter
from real_time_producer import RealTimeStreamProducer

adapter = EHRAdapter(
    api_url="http://hospital-ehr.com",
    api_key="your_key"
)

producer = RealTimeStreamProducer(adapter)
await producer.start_streaming(polling_interval_seconds=10)
```

---

### Example 2: MQTT IoT Devices

**Your device publishes to MQTT:**
```json
{
  "patient_id": "P001",
  "hr": 85,
  "sbp": 120,
  "dbp": 80,
  "rr": 16,
  "spo2": 98,
  "temp": 37.0,
  "lat": 40.7128,
  "lng": -74.0060,
  "eta": 12
}
```

**Configuration:**
```bash
ADAPTER_TYPE=mqtt
MQTT_BROKER=mqtt.company.local
MQTT_TOPIC=ambulance/vitals
```

**Code:**
```python
from adapters.mqtt_adapter import MQTTAdapter

adapter = MQTTAdapter(
    broker_url="mqtt.example.com",
    topic="ambulance/vitals",
    patient_id="P001"
)

producer = RealTimeStreamProducer(adapter)
await producer.start_streaming(polling_interval_seconds=60)
```

---

### Example 3: WebSocket Medical Device

**Device broadcasts data on WebSocket:**
```json
{
  "heart_rate": 85,
  "sbp": 120,
  "dbp": 80,
  "rr": 16,
  "spo2": 98,
  "temp": 37.0
}
```

**Configuration:**
```bash
ADAPTER_TYPE=device
DEVICE_WS_URL=ws://ambulance-monitor.local:8080/vitals
```

**Code:**
```python
from adapters.ehr_adapter import AmbulanceDeviceAdapter

adapter = AmbulanceDeviceAdapter(
    device_ws_url="ws://device.local:8080",
    patient_id="P001"
)

producer = RealTimeStreamProducer(adapter)
await producer.start_streaming()
```

---

## Data Format Standardization

All adapters automatically convert to NEXUS standard format:

```python
{
    "timestamp": "2026-03-27T12:30:00Z",
    "patient_id": "P001",
    "vitals": {
        "heart_rate": 85,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "respiratory_rate": 16,
        "oxygen_saturation": 98,
        "temperature": 37.0
    },
    "location": {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "eta_minutes": 12
    },
    "anomaly_detected": false,
    "anomaly_score": 0.15,
    "alert_level": "STABLE",
    "trend_analysis": {
        "hr_trend": "stable",
        "bp_trend": "stable"
    }
}
```

---

## Testing Without Real Data

Use mock data to test your implementation:

```python
from adapters.ehr_adapter import EHRAdapter, DataSourceAdapter
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

class MockEHRAdapter(DataSourceAdapter):
    """Mock adapter for testing"""

    async def connect(self):
        print("[MOCK] Connected")

    async def fetch_vitals(self) -> Optional[Dict[str, Any]]:
        """Return simulated vitals"""
        return self.standardize_vitals({
            "patient_id": "TEST_P001",
            "timestamp": datetime.utcnow().isoformat(),
            "heart_rate": 85,
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "respiratory_rate": 16,
            "oxygen_saturation": 98,
            "temperature": 37.0
        })

    async def disconnect(self):
        print("[MOCK] Disconnected")

# Test
async def test():
    adapter = MockEHRAdapter()
    from real_time_producer import RealTimeStreamProducer

    producer = RealTimeStreamProducer(adapter)
    await producer.start_streaming(polling_interval_seconds=5)

asyncio.run(test())
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found" | `pip install websockets aiohttp paho-mqtt` |
| Backend connection fails | Ensure backend is running on port 8000 |
| No data arriving | Check adapter configuration in .env |
| Anomaly not detected | May require ML model tuning in `ml_engine/anomaly_detector.py` |
| MQTT connection fails | Check broker address, port, and firewall |

---

## Advanced: Custom Adapter

Create your own adapter for unique data sources:

```python
from adapters.ehr_adapter import DataSourceAdapter
from typing import Dict, Any, Optional

class CustomAdapter(DataSourceAdapter):
    def __init__(self, config: dict):
        self.config = config

    async def connect(self):
        # Initialize your connection
        pass

    async def fetch_vitals(self) -> Optional[Dict[str, Any]]:
        # Fetch from your source
        raw_data = await self.your_fetch_method()

        # Convert to NEXUS format
        return self.standardize_vitals({
            "patient_id": raw_data["pid"],
            "heart_rate": raw_data["hr"],
            # ... map all fields
        })

    async def disconnect(self):
        # Clean up
        pass
```

---

## Performance Tuning

| Parameter | Value | Impact |
|-----------|-------|--------|
| `polling_interval_seconds` | 10 | Balance latency vs. API load |
| `anomaly_detector.window_size` | 10 | More samples = better trend detection |
| `anomaly_detector.contamination` | 0.1 | % of data expected to be anomalies |

---

## Next Steps

1. **Choose data source** → Implement adapter
2. **Test with mock data** → Verify pipeline
3. **Connect real source** → Deploy to production
4. **Monitor alerts** → Fine-tune ML model
5. **Scale deployment** → Add load balancing if needed

For detailed architecture and security info, see `REAL_TIME_INTEGRATION.md`
