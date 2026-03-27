"""
NEXUS Adapters Package

Real-time data source integrations for the NEXUS Ambulance Triage System.

Available adapters:
  - EHRAdapter: REST API / Hospital EHR systems
  - FHIRAdapter: HL7 FHIR standard (Epic, Cerner, OpenEMR)
  - MQTTAdapter: MQTT IoT devices and sensors
  - AmbulanceDeviceAdapter: WebSocket medical devices
"""

from .ehr_adapter import DataSourceAdapter, EHRAdapter, FHIRAdapter, AmbulanceDeviceAdapter
from .mqtt_adapter import MQTTAdapter, MultiTopicMQTTAdapter

__all__ = [
    "DataSourceAdapter",
    "EHRAdapter",
    "FHIRAdapter",
    "AmbulanceDeviceAdapter",
    "MQTTAdapter",
    "MultiTopicMQTTAdapter",
]

__version__ = "1.0.0"
