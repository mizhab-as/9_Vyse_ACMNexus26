@echo off
REM Quick-start script for NEXUS Triage System (Windows)
REM Run this from the project root: run.bat

echo 🏥 NEXUS Real-Time Ambulance-to-Hospital Triage System
echo ========================================================
echo.

REM Check Python version
python --version
echo.

echo 📦 Installing dependencies...
echo.

echo   → Backend dependencies...
cd backend
pip install -q -r requirements.txt
cd ..

echo   → ML Engine dependencies...
cd ml-engine
pip install -q -r requirements.txt
cd ..

echo   → Data Simulator dependencies...
cd data-simulator
pip install -q -r requirements.txt
cd ..

echo ✓ All dependencies installed
echo.
echo 🚀 System is ready to run!
echo.
echo To start the full system, open 3 terminals (Command Prompt or PowerShell) and run:
echo.
echo Terminal 1 (Backend):
echo   cd backend
echo   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo.
echo Terminal 2 (Data Stream):
echo   python streaming_simulator.py
echo.
echo Terminal 3 (Frontend - requires Node.js):
echo   cd frontend
echo   npm install
echo   npm start
echo.
echo Then visit: http://localhost:3000
echo.
pause
