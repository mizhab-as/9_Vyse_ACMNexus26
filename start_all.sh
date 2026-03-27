#!/bin/bash

# Start all NEXUS components
cd /c/Users/rajit/Downloads/ACM-NEXUS-26

echo "Starting NEXUS Ambulance Triage System..."
echo "==========================================="
echo ""

# Terminal 1: Start Frontend
echo "Starting Frontend (React on port 3000)..."
cd frontend
npm start &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"
cd ..
echo ""

# Terminal 2: Start Streaming Simulator
echo "Starting Streaming Simulator..."
export PYTHONPATH=/c/Users/rajit/Downloads/ACM-NEXUS-26:$PYTHONPATH
python streaming_simulator.py &
SIMULATOR_PID=$!
echo "Simulator started with PID: $SIMULATOR_PID"
echo ""

echo "All services started!"
echo "Backend (8000) - Already running"
echo "Frontend (3000) - PID $FRONTEND_PID"
echo "Simulator - PID $SIMULATOR_PID"
echo ""
echo "Access at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
wait
