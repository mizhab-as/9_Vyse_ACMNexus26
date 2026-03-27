"""
EHR/Hospital System Adapter - REST API Integration

Supports:
- Epic EHR API
- Cerner FHIR API
- Generic REST endpoints
"""

import aiohttp
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class DataSourceAdapter(ABC):
    """Base class for any real data source"""

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def fetch_vitals(self) -> Optional[Dict[str, Any]]:
        """Returns vitals in NEXUS standard format"""
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @staticmethod
    def standardize_vitals(raw_data: dict) -> dict:
        """Convert any format to NEXUS standard"""
        return {
            "timestamp": raw_data.get("timestamp", datetime.utcnow().isoformat()),
            "patient_id": raw_data.get("patient_id", "UNKNOWN"),
            "vitals": {
                "heart_rate": int(raw_data.get("heart_rate", 0)),
                "systolic_bp": int(raw_data.get("systolic_bp", 0)),
                "diastolic_bp": int(raw_data.get("diastolic_bp", 0)),
                "respiratory_rate": int(raw_data.get("respiratory_rate", 0)),
                "oxygen_saturation": int(raw_data.get("oxygen_saturation", 0)),
                "temperature": float(raw_data.get("temperature", 0.0))
            },
            "location": {
                "latitude": float(raw_data.get("latitude", 0.0)),
                "longitude": float(raw_data.get("longitude", 0.0)),
                "eta_minutes": int(raw_data.get("eta_minutes", 0))
            }
        }


class EHRAdapter(DataSourceAdapter):
    """Generic REST API adapter for Hospital EHR systems"""

    def __init__(self, api_url: str, api_key: str, poll_endpoint: str = "/api/vitals/latest"):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.poll_endpoint = poll_endpoint
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        print("[EHR] Connected to EHR system at", self.api_url)

    async def fetch_vitals(self) -> Optional[Dict[str, Any]]:
        """Fetch latest vitals from EHR API"""
        if not self.session:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with self.session.get(
                f"{self.api_url}{self.poll_endpoint}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self.standardize_vitals(data)
                else:
                    print(f"[EHR ERROR] API returned status {resp.status}")
                    return None
        except asyncio.TimeoutError:
            print("[EHR ERROR] Request timeout")
            return None
        except Exception as e:
            print(f"[EHR ERROR] {type(e).__name__}: {e}")
            return None

    async def disconnect(self):
        """Close session"""
        if self.session:
            await self.session.close()
        print("[EHR] Disconnected")


class FHIRAdapter(DataSourceAdapter):
    """HL7 FHIR-compliant adapter (works with Epic, Cerner, etc.)"""

    def __init__(self, fhir_base_url: str, patient_id: str, api_key: str):
        self.fhir_base_url = fhir_base_url.rstrip("/")
        self.patient_id = patient_id
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self):
        self.session = aiohttp.ClientSession()
        print(f"[FHIR] Connected to {self.fhir_base_url}")

    async def fetch_vitals(self) -> Optional[Dict[str, Any]]:
        """Fetch from FHIR Observation endpoint"""
        if not self.session:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/fhir+json"
        }

        try:
            # Query for vital signs observations
            url = (f"{self.fhir_base_url}/Observation?"
                   f"patient={self.patient_id}&"
                   f"category=vital-signs&"
                   f"_sort=-date&_count=100")

            async with self.session.get(url, headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    bundle = await resp.json()
                    return self._parse_fhir_observations(bundle)
                return None
        except Exception as e:
            print(f"[FHIR ERROR] {e}")
            return None

    def _parse_fhir_observations(self, bundle: dict) -> Dict[str, Any]:
        """Parse FHIR bundle and extract vitals"""
        vitals = {}

        for entry in bundle.get("entry", []):
            obs = entry["resource"]
            code = obs["code"]["coding"][0]["code"]
            value = obs["value"]["Quantity"]["value"]

            # Map LOINC codes to vitals
            mapping = {
                "8867-4": "heart_rate",      # Heart rate
                "8480-6": "systolic_bp",    # Systolic BP
                "8462-4": "diastolic_bp",   # Diastolic BP
                "9279-1": "respiratory_rate",
                "2708-6": "oxygen_saturation",
                "8310-5": "temperature"
            }

            if code in mapping:
                vitals[mapping[code]] = value

        return self.standardize_vitals({
            "patient_id": self.patient_id,
            "timestamp": datetime.utcnow().isoformat(),
            **vitals
        })

    async def disconnect(self):
        if self.session:
            await self.session.close()


class AmbulanceDeviceAdapter(DataSourceAdapter):
    """Direct streaming from ambulance monitoring devices via WebSocket"""

    def __init__(self, device_ws_url: str, patient_id: str):
        self.device_ws_url = device_ws_url
        self.patient_id = patient_id
        self.websocket = None
        self.latest_vitals = None

    async def connect(self):
        import websockets
        try:
            self.websocket = await websockets.connect(self.device_ws_url)
            # Start listening task
            import asyncio
            asyncio.create_task(self._listen())
            print(f"[DEVICE] Connected to ambulance device at {self.device_ws_url}")
        except Exception as e:
            print(f"[DEVICE ERROR] Connection failed: {e}")

    async def _listen(self):
        """Listen for incoming device data"""
        try:
            async for message in self.websocket:
                payload = json.loads(message)
                self.latest_vitals = self.standardize_vitals({
                    "patient_id": self.patient_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **payload
                })
        except Exception as e:
            print(f"[DEVICE ERROR] {e}")

    async def fetch_vitals(self) -> Optional[Dict[str, Any]]:
        return self.latest_vitals

    async def disconnect(self):
        if self.websocket:
            await self.websocket.close()


async def test_adapter():
    """Test the EHR adapter"""
    import asyncio

    # Mock adapter for testing
    adapter = EHRAdapter(
        api_url="http://mock-ehr.local",
        api_key="test_key"
    )

    await adapter.connect()

    # Simulate fetch
    test_data = {
        "patient_id": "P001",
        "timestamp": datetime.utcnow().isoformat(),
        "heart_rate": 85,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "respiratory_rate": 16,
        "oxygen_saturation": 98,
        "temperature": 37.0,
        "latitude": 40.7128,
        "longitude": -74.0060,
        "eta_minutes": 12
    }

    vitals = adapter.standardize_vitals(test_data)
    print("Standardized vitals:", json.dumps(vitals, indent=2))

    await adapter.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_adapter())
