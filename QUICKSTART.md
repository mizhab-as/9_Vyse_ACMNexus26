# 🚀 Quick Start Guide - NEXUS Triage System

## Prerequisites

You'll need:
- **Python 3.8+** (check with `python --version`)
- **Node.js 14+** (for frontend) (check with `node --version`)
- **pip** (Python package manager, usually comes with Python)
- **npm** (comes with Node.js)

## 1️⃣ Install All Dependencies

### Option A: Automatic (Windows)
```bash
run.bat
```

### Option B: Automatic (Mac/Linux)
```bash
bash run.sh
```

### Option C: Manual Installation
```bash
# Backend
cd backend
pip install -r requirements.txt
cd ..

# ML Engine
cd ml-engine
pip install -r requirements.txt
cd ..

# Data Simulator
cd data-simulator
pip install -r requirements.txt
cd ..

# Frontend
cd frontend
npm install
cd ..
```

---

## 2️⃣ Run the System (3 Terminals)

### Terminal 1: Start the Backend Server

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

✅ **Backend is ready** when you see: `INFO: Application startup complete`

---

### Terminal 2: Start the Data Stream (in a NEW terminal)

From the project root:
```bash
python streaming_simulator.py
```

**Expected Output:**
```
📊 Ambulance-to-Hospital Real-Time Triage Simulator
============================================================
🏥 Starting real-time vitals stream simulation...

🟢 NORMAL | Sample   0 | HR:  72 bpm | BP: 120/80 | O2:  98% | Anomaly Score: 0.12
🟢 NORMAL | Sample  10 | HR:  73 bpm | BP: 119/79 | O2:  98% | Anomaly Score: 0.11
...
🚨 [Sample 180] CRISIS DETECTED at 2026-03-27T14:45:00.000Z
🔴 CRISIS | Sample 180 | HR: 105 bpm | BP: 105/65 | O2:  91% | Anomaly Score: 0.89
...
✅ Stream complete. Crisis detected at sample 180
```

✅ **Stream is ready** when you see: `🏥 Starting real-time vitals stream simulation...`

---

### Terminal 3: Start the Frontend Dashboard (in ANOTHER NEW terminal)

From the project root:
```bash
cd frontend
npm start
```

**Expected Output:**
```
npm notice
npm notice New minor version of npm available!
Compiled successfully!

Local:            http://localhost:3000
On Your Network:  http://192.168.x.x:3000
```

✅ **Frontend is ready** when you see: `Compiled successfully!`

---

## 3️⃣ View the Dashboards

**Open your browser and visit:**
- 🏥 **Paramedic Dark View**: http://localhost:3000
- 🏥 **ER Clean View**: http://localhost:3000/er

---

## What You'll See

### On the Dashboards:
1. **Live Vitals** update every ~10 seconds
2. **Normal Phase** (minutes 0-30): Green status, stable vitals
3. **Crisis Phase** (minutes 30-45): Red alert pops up with clinical briefing
4. **LLM Triage Briefing**: AI-generated ER recommendations appear automatically

### On the Terminal 2 (Stream):
Watch the anomaly score climb as the patient deteriorates. The ML model will flag the CRISIS when it detects the physiological collapse (typically at minute 30-35).

---

## 🐛 Troubleshooting

### "ModuleNotFoundError" or "No module named..."
**Solution**: Make sure you installed dependencies for that component
```bash
cd backend  # or ml-engine, or data-simulator
pip install -r requirements.txt
```

### "Connection refused" or "Cannot connect to server"
**Solution**: Make sure Terminal 1 (backend) is running
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### "npm: command not found"
**Solution**: Install Node.js from https://nodejs.org/
```bash
# After installing, verify:
node --version
npm --version
```

### Frontend shows "disconnected" status
**Solution**: Backend needs to be running (Terminal 1). Wait 3 seconds, it will auto-reconnect.

### "Port 8000 already in use"
**Solution**: Kill the process on that port or use a different port:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

---

## 📊 Understanding the Data Flow

```
Terminal 2 (Streaming Simulator)
  ↓ (generates 45-min synthetic vitals)
Terminal 1 (Backend + ML Detection)
  ↓ (detects anomaly, generates LLM briefing)
Terminal 3 (Frontend Dashboard)
  ↓ (displays live charts and alerts)
Browser
  ↓ (you see the results!)
```

---

## 🧪 Test Components Individually

### Test ML Model Only
```bash
cd ml-engine
python anomaly_detector.py
```

**Expected Output**: Shows crisis detection with Z-scores and trends

### Test Data Generator Only
```bash
cd data-simulator
python data_generator.py
```

**Expected Output**: Creates `ambulance_vitals_45min.csv` with 270 samples

### View Generated Data
```bash
cd data-simulator
python -c "import pandas as pd; df = pd.read_csv('ambulance_vitals_45min.csv'); print(df.head(30))"
```

---

## 🎬 Demo Mode (No Frontend)

If you just want to see the ML + Backend in action without the React frontend:

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Stream
python streaming_simulator.py
```

Watch Terminal 2 output to see:
- Green samples (normal vitals)
- Red alert when crisis is detected
- Anomaly scores climbing from 0.0 to 0.9+

---

## ✅ Success Criteria

You'll know everything is working when:

1. ✅ Backend server starts without errors
2. ✅ Streaming simulator shows "🟢 NORMAL" samples
3. ✅ Terminal 2 displays "🚨 [Sample XXX] CRISIS DETECTED"
4. ✅ Frontend loads at http://localhost:3000
5. ✅ Vitals chart updates in real-time
6. ✅ ER Dashboard (/er) shows RED alert with clinical briefing

---

## 💡 Pro Tips

- **Speed up the stream**: Edit `streaming_simulator.py` line 95 from `speed_multiplier=5.0` to `speed_multiplier=50.0` for instant demo
- **Change monitor port**: In Terminal 3, use `PORT=3001 npm start` to use a different port
- **Check logs**: Frontend errors appear in browser console (F12 → Console tab)
- **Keep terminals open**: Don't close them during demo; they communicate with each other

---

## 🚀 Ready to Go!

```bash
# One-liner to get started (if running on Mac/Linux):
bash run.sh && echo "Now open 3 terminals and follow the instructions above"

# For Windows:
run.bat
```

**Questions?** Check the Architecture documentation in `docs/ARCHITECTURE.md`
