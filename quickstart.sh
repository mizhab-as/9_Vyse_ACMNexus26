#!/bin/bash
# NEXUS Triage System - Quick Start Script

echo "=========================================="
echo "NEXUS Triage System - Quick Start"
echo "=========================================="
echo ""

# Check if running the demo
read -p "Start the full demo? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "[INFO] Launching full E2E demo..."
    python e2e_demo.py --speed 5.0
    exit 0
fi

echo ""
echo "Manual startup Mode"
echo "Open 4 terminal windows and run these commands:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd backend && python -m uvicorn main:app --reload --port 8000"
echo ""
echo "Terminal 2 - Streaming Simulator:"
echo "  python streaming_simulator.py"
echo ""
echo "Terminal 3 - Frontend:"
echo "  cd frontend && npm start"
echo ""
echo "Terminal 4 (Optional) - Monitor ML:"
echo "  cd ml-engine && python anomaly_detector.py"
echo ""
echo "Then open:"
echo "  - Paramedic view: http://localhost:3000"
echo "  - ER view: http://localhost:3000/er"
echo ""
