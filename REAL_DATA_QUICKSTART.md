# NEXUS Real Data Streaming - Quick Start

## What Changed ✨

**Before:** `streaming_simulator.py` generated synthetic 45-min ambulance data
**Now:** `real_data_streaming.py` uses real sepsis patient data from MIMIC-III

## Launch (3 Terminals)

### Terminal 1: Backend
```bash
cd backend
python -m uvicorn main:app --reload
```

### Terminal 2: Real Data Stream (NEW!)
```bash
python real_data_streaming.py
```

### Terminal 3: Frontend
```bash
cd frontend
npm start
```

Then visit: **http://localhost:3000**

---

## The Data 📊

**Dataset:** `data_simulator/p000009_sepsis.psv`
**Patient:** Real ICU sepsis case (confirmed sepsis = SepsisLabel: 1)
**Duration:** 258 samples (~43 hours of ICU monitoring)
**Crisis Pattern:**
- Start: HR 117, SBP 116, O2 99% (early deterioration)
- Progression: BP drops, HR varies, O2 fluctuates
- Sepsis confirmed in ground truth labels

---

## What You'll See 👀

```
[REAL DATA STREAM] Starting...
[OK] Connected to backend: ws://localhost:8000/ws/ambulance/P009

[ALERT] CRISIS DETECTED at sample 6!
[CRISIS] | Sample   6 | HR: 120 | BP: 118/64 | O2: 100% | Score: 1.00
[CRISIS] | Sample   7 | HR: 109 | BP: 106/59 | O2:  98% | Score: 1.00
...
```

**Dashboard:** Real-time graphs update with actual patient trajectory → Crisis alert with triage briefing

---

## Compare Files

| File | Type | Use Case |
|------|------|----------|
| `streaming_simulator.py` | Synthetic | Testing, demo (45 min) |
| `real_data_streaming.py` | **Real Patient Data** | **HACKATHON DEMO** ✅ |

---

## To Use Different Patients

Edit line in `real_data_streaming.py`:

```python
loader = RealDataStreamLoader(
    psv_file='data_simulator/p000001_stable.psv',  # <- Change to different patient
    backend_url='ws://localhost:8000/ws/ambulance/P001'
)
```

Available patients:
- `p000001_stable.psv` - Stable case (good baseline)
- `p000009_sepsis.psv` - **SEPSIS (recommended)** 🎯

---

## Speed Control

Change playback speed in your command:

```python
# Inside real_data_streaming.py
await loader.stream_real_data(speed_multiplier=5.0)  # 5x = 5 hours → ~60 sec demo
```

---

## Judges Will See 💡

> "Our system processes **real patient data** from clinical records and detects abnormal patterns in realtime. Here's a confirmed sepsis case where our ML caught the deterioration..."

**Much stronger than:** synthetic randomly-generated data 💪
