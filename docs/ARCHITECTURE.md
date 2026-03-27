# 🏥 Ambulance-to-Hospital Real-Time Triage System
## Architecture & Data Flow

### 🎯 Project Overview
**Domain:** Digital Health & Predictive Care
**Problem:** Ambulances exist in an "episodic blind spot" — doctors don't know patient deterioration until the ambulance arrives. By then, precious triage time is lost.
**Solution:** Real-time anomaly detection + AI-powered triage briefing delivered **before ambulance arrival**.

---

## 🔄 Data Flow Architecture

```
┌─────────────────┐
│   AMBULANCE     │ (Source: wearables/monitors)
│   (ML Edge)     │
└────────┬────────┘
         │ JSON payload: vitals every 10s
         ▼
┌─────────────────────────────┐
│  Anomaly Detection Engine   │ (ML Edge Engineer role)
│  - Z-score, Isolation Forest│ Runs locally → detects crash
└────────┬────────────────────┘
         │ Flags + raw vitals
         ▼
┌─────────────────────────────┐
│   FastAPI Backend Server    │ (Systems Architect role)
│   - WebSocket streams       │ Aggregates data → LLM
│   - LLM Prompt Engineering  │
└────────┬────────────────────┘
         │ Enhanced JSON: alert + triage briefing
         ▼
┌─────────────────────────────┐
│     React Dual-Dashboard    │ (Frontend UX Engineer role)
│   View A: Paramedic (dark)  │
│   View B: ER Doctor (clean) │
└─────────────────────────────┘
```

---

## 📊 JSON Contracts (Locked for Parallel Development)

### 1. **Ambulance Vitals Stream** → ML Engine
```json
{
  "timestamp": "2026-03-27T14:30:25.123Z",
  "patient_id": "P001",
  "vitals": {
    "heart_rate": 72,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "respiratory_rate": 16,
    "oxygen_saturation": 98,
    "temperature": 37.0
  },
  "location": {
    "latitude": 12.9352,
    "longitude": 77.6245,
    "eta_minutes": 8
  }
}
```

### 2. **Anomaly Detection Output** → Backend
```json
{
  "timestamp": "2026-03-27T14:32:15.123Z",
  "patient_id": "P001",
  "anomaly_detected": true,
  "anomaly_score": 0.87,
  "anomaly_type": "physiological_deterioration",
  "raw_vitals": { /* vitals snapshot */ },
  "trend_analysis": {
    "heart_rate_trend": "↑ +18 bpm",
    "bp_trend": "↓ -15 systolic",
    "alert_level": "CRITICAL"
  }
}
```

### 3. **LLM Triage Briefing** → Frontend
```json
{
  "timestamp": "2026-03-27T14:32:20.123Z",
  "patient_id": "P001",
  "alert_level": "CRITICAL",
  "triage_briefing": "Patient presents with rapid deterioration consistent with septic shock. HR elevated to 90 bpm, SBP dropped 15 points to 105. RR rising. Likely infectious etiology. Recommend: expedite to ICU, initiate fluid resuscitation protocol, blood cultures x2, sepsis panel.",
  "color_code": "RED",
  "recommended_actions": [
    "Notify ICU team immediately",
    "Prepare sepsis protocol",
    "Expedite patient intake"
  ]
}
```

---

## 👥 Role Breakdown

| Role | Responsibility | Tech Stack | Deliverables |
|------|---|---|---|
| **1. Agentic Systems Architect** | FastAPI backend, WebSockets, LLM orchestration | FastAPI, WebSocket, OpenAI API | Backend server, prompt engineering |
| **2. Medical Domain/Data Engineer** | Realistic vitals simulation (Synthea or custom Python) | Python, Pandas, Synthea | 45-min synthetic patient dataset |
| **3. ML Edge Engineer** | Anomaly detection (Z-score, Isolation Forest) | Scikit-learn, Pandas | ML model, inference script |
| **4. Frontend UX Engineer** | Dual-dashboard (paramedic + ER), real-time charts | React, Tailwind, Recharts | Deployed frontend + styling |

---

## ⏰ 24-Hour Sprint Timeline

**Hours 1-2:** Architecture lockdown (THIS PHASE)
**Hours 3-10:** Deep work in parallel
**Hours 11-16:** Integration
**Hours 17-20:** Refinement
**Hours 21-24:** Pitch prep

---

## 🔗 Key Implementation Notes

- **No randomness:** Realistic medical deterioration curve
- **Fast inference:** ML model runs on edge (no rounds-trip delays)
- **Commercial UX:** Judges expect polished, medical-grade interface
- **Pitch story:** "Episodic blind spot" → solve with real-time AI
