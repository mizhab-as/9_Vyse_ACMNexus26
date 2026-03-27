# NEXUS Triage System - Complete Deployment Guide

## Quick Start (5 minutes)

### Prerequisites
- Python 3.9+
- Node.js 16+
- pip, npm

### Installation & Running

```bash
# 1. Backend Setup
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# 2. ML Engine Setup (in another terminal)
cd ../ml-engine
pip install -r requirements.txt

# 3. Data Simulator (in another terminal)
cd ../data-simulator
pip install -r requirements.txt
cd ..
python test_integration.py  # Verify ML works

# 4. Frontend Setup (in another terminal)
cd frontend
npm install
npm start
```

Browser opens to http://localhost:3000 (Paramedic view) and http://localhost:3000/er (ER view)

---

## System Architecture

### 1. **Data Simulator** (`data-simulator/`)
- Generates realistic 45-minute ambulance transit dataset
- Models septic shock progression curve
- **Input**: None (self-seeding)
- **Output**: `ambulance_vitals_45min.csv`

### 2. **ML Engine** (`ml-engine/`)
- **Isolation Forest**: Detects unusual feature combinations
- **Z-Score Analysis**: Detects individual metric deviations
- **Trend Analysis**: Detects rapid deterioration
- **Input**: Raw vitals (heart rate, BP, RR, O2, temp)
- **Output**: Anomaly flag + score (0-1)

### 3. **Backend** (`backend/`)
- **FastAPI**: REST + WebSocket server
- **LLM Integration**: Claude/GPT prompts for clinical briefings (or rule-based fallback)
- **Clinical Decision Engine**: Maps ML outputs → specific ER actions
- **Input**: Vitals + anomaly flags
- **Output**: Pre-arrival briefing + recommendations

### 4. **Frontend** (`frontend/`)
- **Paramedic Dashboard**: Dark, data-heavy, real-time waveforms
- **ER Dashboard**: Clean, high-contrast alerts
- **Real-time streaming**: WebSocket connection to backend
- **Dual routing**: Toggle between views seamlessly

---

## Data Flow

```
Ambulance (10s interval vitals)
    ↓
ML Anomaly Detector (edge device)
    ↓ [anomaly flag + raw vitals]
FastAPI Backend
    ↓ [LLM prompt]
Clinical Decision Engine
    ↓ [briefing + actions]
React Dashboards (WebSocket push)
    ↓
Paramedic & ER Visualizations
```

---

## Integration Testing

```bash
# Run full system test (no API keys required)
python test_integration.py

# This will:
# 1. Generate synthetic data
# 2. Run ML detector
# 3. Generate clinical briefings
# 4. Output test_results.json
```

---

## LLM Integration

### Option A: With Claude API (Production)
```bash
export OPENAI_API_KEY="sk-your-key-here"
python -m backend.main
# Will use Claude for real-time briefings
```

### Option B: Rule-Based Fallback (Demo)
```bash
# No API key needed - uses clinical decision rules
python -m backend.main
# Briefings generated from pattern matching
```

---

## Key Features

### ML Anomaly Detection
- **Z-Score**: Flags metrics >2σ from baseline
- **Isolation Forest**: Detects unusual multivariate combinations
- **Trend Analysis**: Detects rates of change
- **Ensemble Decision**: Requires multiple signals to trigger alert

### Clinical Briefings
- **Pattern Matching**: Detects septic shock, cardiogenic shock, respiratory distress
- **Specific Actions**: Each syndrome → specific ER preparation steps
- **Color-Coding**: RED (urgent), YELLOW (warning), GREEN (stable)

### UX Design Principles
- **Paramedic view**: Maximizes data density (ICU-style monitors)
- **ER view**: Maximizes clarity (high-contrast, large text, action-focused)
- **Dual-dashboard**: Split attention requirements

---

## Performance Metrics

- **Anomaly Detection Latency**: <100ms (edge GPU optional)
- **Backend Processing**: <50ms
- **WebSocket Push**: <100ms
- **Total End-to-End**: <300ms (target)

---

## Medical Accuracy Notes

- **Synthet Data**: Follows real septic shock progression curves
- **ML Model**: Calibrated for pre-hospital sensitivity (higher false positive rate acceptable)
- **Clinical Rules**: Based on SIRS criteria, sepsis-3 definitions
- **Not FDA Cleared**: Research/hackathon use only

---

## Troubleshooting

### "Connection refused" on localhost:8000
- [ ] Backend not running: `python -m backend.main`

### "WebSocket connection failed"
- [ ] Check CORS settings in `backend/main.py`
- [ ] Verify frontend uses correct URL (default: `ws://localhost:8000`)

### ML not detecting anomalies
- [ ] Check contamination rate in `ml-engine/anomaly_detector.py`
- [ ] Verify baseline is set (first 1-2 samples initialize baseline)
- [ ] Run `test_integration.py` to verify ML works independently

### Frontend shows no data
- [ ] Check browser console for JS errors
- [ ] Verify streaming simulator is running (`python streaming_simulator.py`)
- [ ] Check network tab for WebSocket connection status

---

## Hackathon Submission Checklist

- [ ] All code in `/backend`, `/ml-engine`, `/frontend`, `/data-simulator`
- [ ] `docs/ARCHITECTURE.md` explains design
- [ ] `docs/JSON_CONTRACTS.json` defines data formats
- [ ] `test_integration.py` passes without API keys
- [ ] Both dashboards deployed and accessible
- [ ] CHANGELOG.md updated hourly
- [ ] Each team member has at least 1 commit
- [ ] `/progress/` folder has screenshots from each hour
- [ ] README.md has clear project description
- [ ] Pitch deck highlights "episodic blind spot" → solution

---

## Pitch Talking Points

1. **Problem**: Current ambulances operate in an "episodic blind spot" - ERs don't know about patient deterioration until arrival
2. **Solution**: Real-time AI-powered pre-arrival briefing system
3. **Tech**: Edge ML + Cloud LLM + Dual-Dashboard UX
4. **Impact**: Reduces triage time by 5-10 minutes, improves clinical outcomes
5. **Demo**: Show paramedic and ER dashboards side-by-side during a simulated deterioration event

---

## Next Steps

- **Polish UI**: Responsive mobile design for tablets in ambulance
- **Real Hardware**: Integrate with actual patient monitors (HL7, FHIR standards)
- **Regulatory**: FDA clearance pathway for clinical deployment
- **Scaling**: Multi-patient tracking, fleet management dashboard

---

**Built for NEXUS Hackathon 2026 - Digital Health Track**
