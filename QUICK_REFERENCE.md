# 🎯 NEXUS - QUICK REFERENCE CARD

## 📋 30-Second Setup

```bash
# Install dependencies (run once)
python -m pip install --upgrade pip
cd backend && pip install -r requirements.txt && cd ..
cd ml-engine && pip install -r requirements.txt && cd ..
cd data-simulator && pip install -r requirements.txt && cd ..
cd frontend && npm install && cd ..
```

## 🚀 Run (Open 3 Separate Terminals)

```
┌──────────────────────────────────────────────────┐
│ TERMINAL 1: Backend Server (Required)            │
├──────────────────────────────────────────────────┤
│ $ cd backend                                      │
│ $ python -m uvicorn main:app --reload            │
│                                                  │
│ ✅ Ready when: "Application startup complete"   │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ TERMINAL 2: Data Stream (Required)               │
├──────────────────────────────────────────────────┤
│ $ python streaming_simulator.py                  │
│                                                  │
│ ✅ Ready when: "🏥 Starting real-time vitals"   │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ TERMINAL 3: Frontend UI (Optional but recommended│
├──────────────────────────────────────────────────┤
│ $ cd frontend && npm start                       │
│                                                  │
│ ✅ Ready when: "Compiled successfully!"         │
│ 🌐 Visit: http://localhost:3000                 │
└──────────────────────────────────────────────────┘
```

## 🎬 View Results

| View | URL | Purpose |
|------|-----|---------|
| **Paramedic Dashboard** | http://localhost:3000 | Dark mode, live vitals charts |
| **ER Dashboard** | http://localhost:3000/er | Clean alerts, clinical briefing |
| **Backend Health** | http://localhost:8000/health | Check server status |

## 📊 What Happens

```
Timeline: 45 minutes of synthetic patient data
├─ Minutes 0-5:   🟢 NORMAL (baseline vitals)
├─ Minutes 5-15:  🟢 NORMAL (early deterioration, subtle)
├─ Minutes 15-30: 🟡 WARNING (increasingly abnormal)
└─ Minutes 30-45: 🔴 CRITICAL (septic shock crisis)
               ↓
        ML detects anomaly → Backend LLM generates briefing
               ↓
        ER Dashboard pops RED ALERT with recommendations
```

## 🔧 Test Individual Components

```bash
# Test ML Model
cd ml-engine && python anomaly_detector.py

# Test Data Generator
cd data-simulator && python data_generator.py

# View Generated Data
cd data-simulator && python -c "import pandas as pd; print(pd.read_csv('ambulance_vitals_45min.csv').head(30))"
```

## ⚡ Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | `pip install -r requirements.txt` (in that component dir) |
| "Port 8000 already in use" | `python -m uvicorn main:app --port 8001` |
| Frontend shows "disconnected" | Ensure Terminal 1 (backend) is running |
| "npm: command not found" | Install Node.js from nodejs.org |
| Data not updating | Ensure Terminal 2 (streaming) is running |

## 🎯 Success Checklist

- [ ] Terminal 1 shows "Application startup complete"
- [ ] Terminal 2 shows "🟢 NORMAL" samples
- [ ] Terminal 2 shows "🚨 CRISIS DETECTED" after ~30 min
- [ ] Frontend loads at http://localhost:3000
- [ ] Vitals chart updates in real-time
- [ ] ER Dashboard (/er) shows RED alert with briefing

## ⏱️ Expected Timeline

- **0:00-0:20** - Streaming starts, vitals are normal
- **0:20-0:30** - Early deterioration, few warnings
- **0:30-0:40** - Crisis detected, RED alert triggered
- **0:40-0:50** - Stream completes

## 💡 Pro Tips

- **Fast demo**: Edit line 95 in `streaming_simulator.py` → `speed_multiplier=50.0`
- **Reset everything**: `rm -rf node_modules __pycache__ *.csv venv/` then reinstall
- **Debug frontend**: Press F12 in browser → Console tab
- **Backend logs**: Check Terminal 1 for WebSocket messages

---

**Need help?** Read `QUICKSTART.md` for detailed troubleshooting
