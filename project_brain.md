# Project: VigilCare AI (Ambulance-to-ER Predictive Pipeline)

## 1. Core Objective
A continuous predictive health monitoring system that shifts healthcare from episodic observation to proactive intervention. The system operates in an ambulance transit scenario, processing edge data to give ER doctors a "Pre-Arrival Triage Briefing" before the patient arrives.

## 2. The Architecture
* **Edge Data Simulator:** Generates continuous synthetic patient vitals (SpO2, HR, Temp) simulating a 45-minute ambulance ride with a gradual deterioration (e.g., dropping SpO2, rising HR).
* **Edge ML Engine (Ambulance):** A lightweight Python script using Z-scores/Isolation Forests to detect anomalies in the continuous stream locally.
* **Cloud Backend:** FastAPI server that receives the anomaly flags and aggregated trends from the edge.
* **Agentic LLM Layer:** Ingests the raw anomaly data and outputs a natural-language clinical triage briefing.
* **Frontend Dashboards:** React/Tailwind application with two views: "Paramedic View" (raw streaming charts) and "ER Doctor View" (high-contrast alerts and LLM briefing).

## 3. Tech Stack
* Backend: Python, FastAPI, WebSockets
* Frontend: React, Tailwind CSS, Recharts
* Data/ML: Pandas, Scikit-learn, tsfresh (optional)

## 4. Current State & Next Steps
[Update this section manually every few hours so Copilot knows where you are in the sprint.]

## 5. The Demo Flow (Phase 2)
1. Start data_simulator.py (Normal vitals).
2. AmbulanceView shows green charts, "STABLE" status.
3. Toggle "Network" to "Offline" to simulate a dead zone.
4. data_simulator.py introduces the SpO2 drop (Minute 30 deterioration).
5. Edge AI detects the anomaly locally (no cloud connection needed).
6. Toggle "Network" to "Online".
7. System immediately flushes the queued LLM alert to the ERDashboard.
8. ERDashboard flashes red, displaying the parsed actionable checklist and clinical summary.