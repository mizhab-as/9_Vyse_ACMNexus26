#!/bin/bash
# Quick-start script for NEXUS Triage System
# Run this from the project root: bash run.sh

set -e

echo "🏥 NEXUS Real-Time Ambulance-to-Hospital Triage System"
echo "========================================================"
echo ""

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."

echo "  → Backend dependencies..."
cd backend && pip install -q -r requirements.txt && cd ..

echo "  → ML Engine dependencies..."
cd ml-engine && pip install -q -r requirements.txt && cd ..

echo "  → Data Simulator dependencies..."
cd data-simulator && pip install -q -r requirements.txt && cd ..

echo "✓ All dependencies installed"

echo ""
echo "🚀 System is ready to run!"
echo ""
echo "To start the full system, open 3 terminals and run:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Terminal 2 (Data Stream):"
echo "  python streaming_simulator.py"
echo ""
echo "Terminal 3 (Frontend - requires Node.js):"
echo "  cd frontend && npm install && npm start"
echo ""
echo "Then visit: http://localhost:3000"
echo ""
