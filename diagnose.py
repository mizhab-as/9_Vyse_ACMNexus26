#!/usr/bin/env python
"""
Diagnostic script to verify NEXUS system setup
"""
import sys
import os

print("=" * 60)
print("NEXUS System Diagnostic")
print("=" * 60)

# Check Python version
print(f"\n✓ Python: {sys.version.split()[0]}")

# Check directory structure
print("\n✓ Directory Structure:")
project_root = '/c/Users/rajit/Downloads/ACM-NEXUS-26'
os.chdir(project_root)

required_dirs = [
    'backend',
    'frontend',
    'ml_engine',
    'data_simulator',
]

for d in required_dirs:
    path = os.path.join(project_root, d)
    exists = "✓" if os.path.isdir(path) else "✗"
    print(f"  {exists} {d}/")

# Check key files
print("\n✓ Key Files:")
key_files = [
    'streaming_simulator.py',
    'backend/main.py',
    'frontend/package.json',
    'ml_engine/anomaly_detector.py',
    'data_simulator/data_generator.py',
]

for f in key_files:
    path = os.path.join(project_root, f)
    exists = "✓" if os.path.isfile(path) else "✗"
    print(f"  {exists} {f}")

# Check Python modules
print("\n✓ Python Imports:")
sys.path.insert(0, project_root)

try:
    from data_simulator.data_generator import RealisticAmbulanceDataSimulator
    print("  ✓ data_simulator.data_generator.RealisticAmbulanceDataSimulator")
except Exception as e:
    print(f"  ✗ data_simulator.data_generator - Error: {e}")

try:
    from ml_engine.anomaly_detector import AnomalyDetector
    print("  ✓ ml_engine.anomaly_detector.AnomalyDetector")
except Exception as e:
    print(f"  ✗ ml_engine.anomaly_detector - Error: {e}")

# Check npm
print("\n✓ Frontend Dependencies:")
frontend_dir = os.path.join(project_root, 'frontend')
npm_installed = os.path.isdir(os.path.join(frontend_dir, 'node_modules'))
print(f"  {'✓' if npm_installed else '✗'} npm packages installed" +
      (f" ({os.path.getsize(os.path.join(frontend_dir, 'node_modules'))} bytes)" if npm_installed else ""))

# Check services
print("\n✓ Service Status:")
try:
    import socket
    def is_port_open(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0

    print(f"  {'✓' if is_port_open(8000) else '✗'} Backend (port 8000)")
    print(f"  {'✓' if is_port_open(3000) else '✗'} Frontend (port 3000)")
except Exception as e:
    print(f"  ! Could not check ports: {e}")

print("\n" + "=" * 60)
print("Setup verification complete!")
print("=" * 60)
