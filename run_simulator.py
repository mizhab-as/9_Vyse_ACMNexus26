#!/usr/bin/env python
"""
Wrapper to start streaming simulator with proper path setup
"""
import sys
import os

# Set working directory
os.chdir('/c/Users/rajit/Downloads/ACM-NEXUS-26')

# Add project root to path BEFORE any imports
sys.path.insert(0, '/c/Users/rajit/Downloads/ACM-NEXUS-26')

# Now run the simulator
if __name__ == '__main__':
    from streaming_simulator import StreamingSimulator
    import asyncio

    simulator = StreamingSimulator(backend_url="ws://localhost:8000/ws/ambulance/P001")
    print("🏥 Starting real-time vitals stream simulation...\n")

    # Stream at 5x speed for demo
    asyncio.run(simulator.stream_data(speed_multiplier=5.0, interactive=False))
