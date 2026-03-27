#!/usr/bin/env python3
"""
NEXUS E2E Demo Orchestrator

Runs the complete system:
1. Starts backend server
2. Streams synthetic data
3. Monitors anomaly detection
4. Displays alerts

Usage: python e2e_demo.py [--speed 5.0] [--port 8000]
"""

import asyncio
import subprocess
import sys
import time
import json
from datetime import datetime

async def run_demo(speed_multiplier=5.0, port=8000):
    """Run complete E2E demo."""

    print("=" * 70)
    print("NEXUS E2E DEMO ORCHESTRATOR")
    print("=" * 70)
    print()

    # Step 1: Start backend
    print("[STEP 1] Starting FastAPI backend server...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--reload", f"--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)  # Wait for server startup
    print(f"  Backend running on http://localhost:{port}")
    print()

    # Step 2: Run streaming simulator
    print("[STEP 2] Starting real-time vitals streaming...")
    print(f"  Speed multiplier: {speed_multiplier}x")
    print(f"  Transport duration: ~9 minutes (45 min / {speed_multiplier}x)")
    print()

    simulator_proc = subprocess.Popen(
        [sys.executable, "streaming_simulator.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Step 3: Monitor streaming output
    print("[STEP 3] Processing vitals stream...")
    print()

    start_time = datetime.now()
    alert_detected = False

    for line in simulator_proc.stdout:
        print(line.rstrip())
        if "CRISIS DETECTED" in line:
            alert_detected = True

    # Wait for simulator to complete
    simulator_proc.wait()

    # Step 4: Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    print()
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print(f"Elapsed time: {elapsed:.1f} seconds")
    print(f"Crisis detected: {'YES' if alert_detected else 'NO'}")
    print()
    print("Next steps:")
    print("  1. Open http://localhost:3000 (Paramedic view)")
    print("  2. Open http://localhost:3000/er (ER pre-arrival briefing)")
    print("  3. Run 'npm start' in frontend/ directory")
    print()

    # Cleanup
    backend_proc.terminate()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--speed", type=float, default=5.0, help="Speed multiplier for demo")
    parser.add_argument("--port", type=int, default=8000, help="Backend port")
    args = parser.parse_args()

    try:
        asyncio.run(run_demo(args.speed, args.port))
    except KeyboardInterrupt:
        print("\nDemo stopped by user")
