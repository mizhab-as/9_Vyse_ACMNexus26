# 🚀 Welcome to NEXUS

### Conducted by | CLIQUE x ACM MITS |

### 📅 March 27 & 28

### 📍 Muthoot Institute of Technology and Science

<p align="center">
  <img src="template_acm.png" width="500"/>
  <img src="template_clique.png" width="250"/>
</p>

---

### 📖 Description

A **16-hour hackathon** across various domains where innovation meets execution. Build, collaborate, and push your limits.

---

## 🧠 Project Details

```md
### 🏷️ Project Name:
**NEXUS Real-Time Ambulance-to-Hospital Triage System**

### 🎯 Chosen Domain:
**Digital Health & Predictive Care**

### ❗ Problem Statement:
**The "Episodic Blind Spot"**: Emergency Room physicians don't receive crucial patient deterioration data until the ambulance arrives. By then, precious triage and preparation time is lost. A septic shock patient showing early signs during transport may arrive in full crisis condition without pre-arrival warning.

### 💡 Solution:
**Real-Time AI-Powered Pre-Arrival Triage**:
- Deploy lightweight anomaly detection on ambulance edge devices to continuously monitor patient vitals
- Stream raw data to cloud backend via WebSocket with <2s latency
- Use Claude API to generate clinical-grade pre-arrival briefings from anomaly flags
- Display dual-mode dashboards: Paramedic (data-heavy, live charts) and ER Doctor (high-contrast alerts)
- **Result**: ER team receives AI-generated triage briefing BEFORE ambulance arrival
```

---

## 🏗️ Technical Architecture

The system is divided into 4 core components:

| Component | Role | Technology | Status |
|-----------|------|-----------|--------|
| **Backend & Orchestration** | FastAPI server, WebSocket streams, LLM integration | FastAPI, OpenAI API | ✅ Boilerplate ready |
| **ML Edge Engine** | Real-time anomaly detection (Isolation Forest + Z-score) | Scikit-learn, Pandas | ✅ Ready |
| **Data Simulator** | Generate realistic 45-min septic shock deterioration curve | Python, Pandas, NumPy | ✅ Ready |
| **Dual Dashboard** | Paramedic view (dark, data-heavy) + ER view (clean, high-contrast) | React, Tailwind, Recharts | ✅ Components ready |

**Data Flow**:
```
Ambulance (vitals stream)
  → ML Anomaly Detector (edge)
  → FastAPI Backend (LLM briefing)
  → WebSocket to Dashboards
  → Paramedic & ER visualizations
```

---

## 📁 Project Structure

```
.
├── backend/                    # FastAPI WebSocket server
│   ├── main.py                # Core server + LLM prompt engineering
│   └── requirements.txt        # Dependencies
├── ml-engine/                 # Edge anomaly detection
│   ├── anomaly_detector.py    # Isolation Forest + Z-score
│   └── requirements.txt
├── data-simulator/            # Realistic synthetic data generation
│   ├── data_generator.py      # Creates 45-min septic shock curve
│   └── requirements.txt
├── frontend/                  # React dual-dashboard
│   ├── App.jsx               # WebSocket client + routing
│   ├── DualDashboard.jsx     # ParamedicDashboard + ERDashboard
│   └── package.json
├── streaming_simulator.py     # End-to-end integration test
├── docs/
│   ├── ARCHITECTURE.md        # Complete system design
│   └── JSON_CONTRACTS.json    # Data format specifications
└── progress/                  # Hourly progress screenshots
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Backend
cd backend && pip install -r requirements.txt

# ML Engine
cd ../ml-engine && pip install -r requirements.txt

# Data Simulator
cd ../data-simulator && pip install -r requirements.txt

# Frontend
cd ../frontend && npm install
```

### 2. Run the System

**Terminal 1: Start Backend**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Generate Data & Stream**
```bash
cd ..
python streaming_simulator.py
```

**Terminal 3: Start Frontend**
```bash
cd frontend
npm start
```

**Terminal 4 (Optional): Inspect ML directly**
```bash
cd ml-engine
python anomaly_detector.py
```

### 3. View Dashboards

- **Paramedic View** (dark, live charts): http://localhost:3000
- **ER Dashboard** (clean, high-contrast alerts): http://localhost:3000/er

---

## 🧪 Testing Data Flow

1. Streaming simulator generates synthetic patient data (45-minute septic shock progression)
2. ML anomaly detector flags the exact minute deterioration begins (typically ~30 min)
3. Backend receives anomaly, triggers Claude API to generate pre-arrival briefing
4. ER dashboard pops RED alert with clinical recommendations

---

## 🎯 Hackathon Domains

Participants must choose **one** of the following domains:

1️⃣ Digital Asset Protection
2️⃣ Smart Supply Chains
3️⃣ Digital Health & Predictive Care
4️⃣ Climate Intelligence
5️⃣ Cybersecurity & Threat Intelligence

---

## ⚙️ Hackathon Workflow & Rules

To ensure fairness and transparency, we have designed a structured development and tracking system.

---

### 🔗 GitHub Template

👉 **Template Repo:** `{link}`

* All teams must **fork this repository**
* Fork name must follow:

```
<TeamId>_<TeamName>_ACMNexus26
```

* Example:

```
12_CodeWarriors_ACMNexus26
```

* You may rename the repository **after the event ends**

---


---

## 👥 Participation Rules

* Team Size: **2–4 members**
* **Pre-created projects are strictly not allowed**
* All work must be done **during the hackathon timeframe**
* Only registered team members must participate
* Do **not attack or interfere** with college infrastructure/network
* Follow all instructions from the organizing team

---

## 📁 Repository Structure


Repository must not be private. The template Repository includes:

```
AGENTS.md
README.md
CHANGELOG.md
/progress/
```

---

## ⏱️ Hourly Progress Requirements

Every hour, teams must:

* Make **at least one commit**
* Add **at least one progress update** inside `/progress/`

Progress can include:

* Screenshots
* Screen recordings
* Dataset snapshots
* Any meaningful proof of work

### 📂 Progress Format

```
/progress
1.png
2.png
3.png
```

* Files must be **numbered sequentially**
* Each file should reflect **actual development progress**

---

## 📝 Changelog Rules (VERY IMPORTANT)

Every commit must be reflected in `CHANGELOG.md`.

You can:

* Update it per commit, OR
* Update it periodically (but must be complete at the end)

---

### 📌 Changelog Format

```md
## HH:MM

### Features Added
- Added login functionality
- Implemented API integration

### Files Modified
- auth.js
- login.jsx

### Issues Faced
- Firebase auth errors
- API timeout issues
```

---

💡 Tip:
Instructions are already included in `AGENTS.md`.
You can simply prompt it to **"CREATE CHANGELOG"** to follow the format.

---

## 📖 Documentation

We have provided:

* Examples
* Guidelines

Inside:

* `AGENTS.md`
* `README.md`

Please follow them strictly.

---

## 🔍 Monitoring & Verification

* Random checks will be conducted during the hackathon
* Organizers may:

  * Inspect commit history
  * Review changelog consistency
  * Verify progress evidence

---

## 👨‍💻 Team Collaboration Rules

* All members must be added as **collaborators**
* By the end of the hackathon:

  * **Each member must have at least one commit**

---

## ⚠️ Disqualification Criteria

* Use of **pre-built / pre-developed projects**
* Fake or manipulated commit history
* Missing hourly commits or progress updates
* Incomplete or inconsistent changelog

---

## 🏁 Final Note

Focus on building, learning, and enjoying the experience.

---

🔥 **Build. Break. Innovate. See you at NEXUS.**
