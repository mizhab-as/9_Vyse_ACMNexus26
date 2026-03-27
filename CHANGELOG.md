# Changelog

## 22:32

### Features Added
- FastAPI edge backend WebSockets for ambulance vitals (`/ws/ambulance_stream`) and ER alerts broadcast (`/ws/er_alerts`).
- Rolling 60s Z-score SpO2 anomaly detection with a 10s consecutive-anomaly trigger to generate an LLM triage briefing.
- “Spotty Network” demo toggle (`GET/POST /api/network`) that pauses ER broadcasts while continuing local detection; queues LLM briefings offline and flushes immediately when back online.
- LLM prompt updated to return **strict JSON**: `Clinical_Summary` (1 sentence), `Predicted_Condition`, `Actionable_Prep` (3 items).
- React dashboards: AmbulanceView (Recharts live chart + dynamic SpO2 color + STABLE/CRITICAL banner + Network toggle) and ERDashboard (parses JSON briefing, renders high-contrast checklist, shows 10-minute ETA countdown).

### Files Modified
- main.py
- data_simulator.py
- frontend/src/AmbulanceView.jsx
- frontend/src/ERDashboard.jsx
- project_brain.md

### Issues Faced
- CHANGELOG timestamp not captured from the session context; replace `00:00` with the actual commit time if needed.

## 09:00

### Features Added
- Initialized project structure
- Added `AGENTS.md` with hackathon workflow rules
- Created `CHANGELOG.md` with predefined format

### Files Modified
- AGENTS.md
- CHANGELOG.md
- README.md

### Issues Faced
- None

## 12:47

### Features Added
- Added local template image assets (template_acm.png, template_clique.png)
- Refactored AGENTS.md, README.md, and CHANGELOG.md to use 24-hour time format (HH:MM) instead of "Hour X"

### Files Modified
- AGENTS.md
- CHANGELOG.md
- README.md
- template_acm.png
- template_clique.png

### Issues Faced
- Initial remote image download attempt failed, resolved by using provided local files
