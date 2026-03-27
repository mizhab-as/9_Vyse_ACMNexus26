# Real-Time Dataset Implementation - Complete Guide

## What We Created

You now have a complete framework to integrate **real medical data** into NEXUS without using the simulator.

### Files Created

```
ACM-NEXUS-26/
├── adapters/                          # Data source adapters
│   ├── __init__.py
│   ├── ehr_adapter.py                # EHR, FHIR, REST API, WebSocket
│   └── mqtt_adapter.py               # MQTT IoT devices
│
├── real_time_producer.py             # Central streaming pipeline
├── example_real_time.py              # Mock examples for testing
├── REAL_TIME_INTEGRATION.md          # Detailed technical docs
├── REAL_TIME_QUICKSTART.md           # Quick start guide (THIS FILE)
└── .env.real-time.example            # Configuration template
```

---

## Quick Comparison: Simulator vs. Real-Time

| Feature | Simulator | Real-Time |
|---------|-----------|-----------|
| **Data Source** | Python generator | Real hospital/device systems |
| **Frequency** | Pre-generated 45-minute dataset | Live streaming (configurable) |
| **Configuration** | None (built-in) | Via `.env` file |
| **Use Case** | Demo, testing | Production deployment |
| **Latency** | N/A | As fast as your data source |

---

## 3-Minute Setup

### Option 1: Use Mock Adapter (No Setup)

For testing without real data:

```bash
# Terminal 3 only:
python example_real_time.py
```

Choose either EHR or MQTT mock example. Generates realistic vital progression.

---

### Option 2: EHR/Hospital REST API

```bash
# 1. Copy config
cp .env.real-time.example .env

# 2. Edit .env
# ADAPTER_TYPE=ehr
# EHR_API_URL=http://your-hospital.com
# EHR_API_KEY=your_key

# 3. Run
python real_time_producer.py
```

---

### Option 3: MQTT IoT Devices

```bash
# 1. Copy config
cp .env.real-time.example .env

# 2. Edit .env
# ADAPTER_TYPE=mqtt
# MQTT_BROKER=mqtt.example.com
# MQTT_TOPIC=ambulance/vitals

# 3. Run
python real_time_producer.py
```

---

### Option 4: WebSocket Medical Device

```bash
# 1. Copy config
cp .env.real-time.example .env

# 2. Edit .env
# ADAPTER_TYPE=device
# DEVICE_WS_URL=ws://device-ip:8080/stream

# 3. Run
python real_time_producer.py
```

---

## How It Works

```
┌─────────────────────────────────────┐
│  Your Real Data Source              │
│  (Hospital EHR, MQTT Devices, etc)  │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Adapter (converts format)          │
│  - EHRAdapter                       │
│  - MQTTAdapter                      │
│  - AmbulanceDeviceAdapter           │
└────────────┬────────────────────────┘
             │ standardizes vitals
             ↓
  ┌──────────────────────┐
  │ Vitals JSON          │
  │ {                    │
  │   heart_rate: 85,    │
  │   systolic_bp: 120,  │
  │   ...                │
  │ }                    │
  └──────────┬───────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Real-Time Producer                 │
│  - Anomaly Detection                │
│  - WebSocket Streaming              │
│  - Error Recovery                   │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  NEXUS Backend (port 8000)          │
│  - LLM Triage Briefing              │
│  - WebSocket Hub                    │
└────────────┬────────────────────────┘
             │
      ┌──────┴──────┐
      ↓             ↓
┌──────────┐   ┌──────────┐
│Paramedic │   │ER Team   │
│Dashboard │   │Dashboard │
│(3000)    │   │(3000)    │
└──────────┘   └──────────┘
```

---

## Supported Data Formats

### Input: Hospital EHR API

```json
{
  "patient_id": "P001",
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

### Input: MQTT Device

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

### Output: NEXUS Standard (Auto-Converted)

```json
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
  "alert_level": "STABLE"
}
```

---

## Testing Your Adapter

### Test 1: Mock Data (No Backend Needed)

```python
from adapters.ehr_adapter import EHRAdapter

async def test():
    adapter = EHRAdapter("http://test.local", "test_key")
    await adapter.connect()

    # Test standardization
    raw = {
        "patient_id": "P001",
        "heart_rate": 85,
        # ...
    }

    standardized = adapter.standardize_vitals(raw)
    print(standardized)

    await adapter.disconnect()

asyncio.run(test())
```

### Test 2: Full Integration

```bash
# Terminal 1
cd backend && python -m uvicorn main:app --reload

# Terminal 2
cd frontend && npm start

# Terminal 3
python example_real_time.py  # Choose mock example
```

Then visit http://localhost:3000

---

## Adapters Available

### 1. EHRAdapter (Generic REST API)

```python
from adapters.ehr_adapter import EHRAdapter

adapter = EHRAdapter(
    api_url="https://hospital-ehr.com",
    api_key="your_key"
)
```

**Supports:** Any REST API returning vital signs

---

### 2. FHIRAdapter (HL7 FHIR Standard)

```python
from adapters.ehr_adapter import FHIRAdapter

adapter = FHIRAdapter(
    fhir_base_url="https://fhir.example.com",
    patient_id="patient-123",
    api_key="your_key"
)
```

**Supports:** Epic, Cerner, OpenEMR, any FHIR-compliant system

---

### 3. MQTTAdapter (IoT Devices)

```python
from adapters.mqtt_adapter import MQTTAdapter

adapter = MQTTAdapter(
    broker_url="mqtt.example.com",
    topic="ambulance/vitals"
)
```

**Supports:** Any MQTT device (pulse oximeter, BP cuff, etc.)

---

### 4. AmbulanceDeviceAdapter (WebSocket)

```python
from adapters.ehr_adapter import AmbulanceDeviceAdapter

adapter = AmbulanceDeviceAdapter(
    device_ws_url="ws://device.local:8080/vitals",
    patient_id="P001"
)
```

**Supports:** Direct WebSocket medical devices

---

## Configuration Reference

### .env File (Complete)

```bash
# ===== ADAPTER SELECTION =====
ADAPTER_TYPE=ehr  # Options: ehr, mqtt, device

# ===== EHR API =====
EHR_API_URL=http://hospital.example.com
EHR_API_KEY=your_api_key

# ===== MQTT =====
MQTT_BROKER=mqtt.example.com
MQTT_TOPIC=ambulance/vitals

# ===== WEBSOCKET DEVICE =====
DEVICE_WS_URL=ws://device.local:8080/vitals

# ===== NEXUS BACKEND =====
BACKEND_URL=ws://localhost:8000/ws/ambulance

# ===== PATIENT INFO =====
PATIENT_ID=REAL_P001

# ===== TIMING =====
POLLING_INTERVAL=10  # seconds between polls
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: websockets` | `pip install websockets aiohttp paho-mqtt` |
| Backend connection fails | Check backend is running on port 8000 |
| No data appears | Check adapter config in `.env` |
| MQTT connection refused | Verify broker URL and firewall |
| API returns 401/403 | Check API key in `.env` |

---

## Next Steps

1. **Start with testing** → Run `example_real_time.py` with mock data
2. **Choose adapter** → EHR, MQTT, or WebSocket?
3. **Configure** → Edit `.env` with your data source
4. **Deploy** → Replace simulator with `real_time_producer.py`
5. **Monitor** → Watch for anomalies on the dashboard at http://localhost:3000

---

## For Production Deployment

See `REAL_TIME_INTEGRATION.md` for:
- Security & HIPAA compliance
- Data validation
- Error handling
- Scaling considerations
- Monitoring & observability

---

## Key Classes

### DataSourceAdapter (Base Class)

```python
from adapters.ehr_adapter import DataSourceAdapter

class MyCustomAdapter(DataSourceAdapter):
    async def connect(self):
        # Initialize your connection
        pass

    async def fetch_vitals(self):
        # Return standardized vitals or None
        pass

    async def disconnect(self):
        # Clean up
        pass
```

### RealTimeStreamProducer

```python
from real_time_producer import RealTimeStreamProducer

producer = RealTimeStreamProducer(adapter)
await producer.start_streaming(polling_interval_seconds=10)
```

---

## Support

**Issues?** Check `REAL_TIME_INTEGRATION.md` for detailed technical docs.

**Questions?** The `example_real_time.py` script demonstrates all adapters with mock data.

---

Good luck! 🚀
