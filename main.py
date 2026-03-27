import asyncio
import json
import os
import datetime
from collections import deque
from typing import Deque, Dict, Any, List, Optional, Set

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from data_simulator import stream_vitals

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

try:
    from openai import AsyncOpenAI  # type: ignore
except Exception:
    AsyncOpenAI = None  # type: ignore


# --- Application Setup ---
app = FastAPI(
    title="VigilCare Edge Backend",
    description="Streams simulated patient data, performs real-time anomaly detection, and generates triage briefings."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROLLING_WINDOW_SIZE = 60
Z_SCORE_THRESHOLD = -2.0
ANOMALY_STREAK_SECONDS = 10


def is_spo2_anomalous(current_spo2: float, spo2_window: Deque[float]) -> bool:
    if len(spo2_window) < ROLLING_WINDOW_SIZE:
        return False

    window_array = np.array(list(spo2_window), dtype=float)
    mean_spo2 = float(np.mean(window_array))
    std_dev_spo2 = float(np.std(window_array))

    if std_dev_spo2 == 0:
        return False

    z_score = (current_spo2 - mean_spo2) / std_dev_spo2
    return z_score < Z_SCORE_THRESHOLD


async def vitals_async_iter():
    gen = stream_vitals()
    while True:
        try:
            item = await asyncio.to_thread(next, gen)
        except StopIteration:
            return
        yield item


_openai_client: Optional["AsyncOpenAI"] = None


def _get_openai_client() -> "AsyncOpenAI":
    global _openai_client
    if AsyncOpenAI is None:
        raise RuntimeError("openai package is not available but is required for LLM briefings.")
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


def _normalize_briefing(obj: Any) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        return {
            "Clinical_Summary": "",
            "Predicted_Condition": "",
            "Actionable_Prep": [],
        }

    clinical = str(obj.get("Clinical_Summary", "")).strip()
    condition = str(obj.get("Predicted_Condition", "")).strip()
    prep = obj.get("Actionable_Prep", [])
    if not isinstance(prep, list):
        prep = []
    prep = [str(x).strip() for x in prep if str(x).strip()][:3]

    return {
        "Clinical_Summary": clinical,
        "Predicted_Condition": condition,
        "Actionable_Prep": prep,
    }


async def generate_triage_briefing(recent_vitals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Returns STRICT JSON with:
      - Clinical_Summary (1 sentence)
      - Predicted_Condition (short label)
      - Actionable_Prep (array of 3 short items)
    """
    client = _get_openai_client()

    compact = [
        {"t": v.get("timestamp"), "spo2": v.get("SpO2"), "hr": v.get("HR")}
        for v in recent_vitals[-ROLLING_WINDOW_SIZE:]
    ]

    system = (
        "You are an expert emergency physician. "
        "Return output strictly as a JSON object with keys: "
        '"Clinical_Summary" (1 sentence), "Predicted_Condition" (short label), '
        '"Actionable_Prep" (array of 3 short prep actions).'
    )
    user = (
        "Given recent ambulance vitals JSON, infer the likely clinical event and ER preparation. "
        "Constraints:\n"
        "- Output MUST be valid JSON only (no markdown, no extra text).\n"
        '- "Clinical_Summary": exactly 1 sentence.\n'
        '- "Predicted_Condition": short label (e.g., "Acute Hypoxia").\n'
        '- "Actionable_Prep": array of exactly 3 short items.\n\n'
        f"recent_vitals={json.dumps(compact, ensure_ascii=False)}"
    )

    resp = await client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        max_tokens=200,
        response_format={"type": "json_object"},
    )

    raw = (resp.choices[0].message.content or "").strip()
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {
            "Clinical_Summary": raw[:250],
            "Predicted_Condition": "",
            "Actionable_Prep": [],
        }

    return _normalize_briefing(parsed)


class ERAlertsBroadcaster:
    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast_json(self, payload: Dict[str, Any]) -> None:
        message = json.dumps(payload)
        async with self._lock:
            conns = list(self._connections)

        if not conns:
            return

        results = await asyncio.gather(
            *[ws.send_text(message) for ws in conns],
            return_exceptions=True,
        )

        for ws, res in zip(conns, results):
            if isinstance(res, Exception):
                await self.disconnect(ws)


er_alerts = ERAlertsBroadcaster()


class NetworkState:
    def __init__(self) -> None:
        self._online: bool = True
        self._queue: Deque[Dict[str, Any]] = deque()
        self._lock = asyncio.Lock()

    async def get(self) -> Dict[str, Any]:
        async with self._lock:
            return {"online": self._online, "queued": len(self._queue)}

    async def set_online(self, online: bool) -> Dict[str, Any]:
        to_flush: List[Dict[str, Any]] = []
        async with self._lock:
            prev = self._online
            self._online = online
            if (not prev) and online and self._queue:
                to_flush = list(self._queue)
                self._queue.clear()

        for payload in to_flush:
            await er_alerts.broadcast_json(payload)

        return await self.get()

    async def enqueue_or_broadcast(self, payload: Dict[str, Any]) -> None:
        async with self._lock:
            if not self._online:
                self._queue.append(payload)
                return
        await er_alerts.broadcast_json(payload)


network_state = NetworkState()


class NetworkToggle(BaseModel):
    online: bool


@app.get("/api/network")
async def get_network():
    return await network_state.get()


@app.post("/api/network")
async def set_network(toggle: NetworkToggle):
    return await network_state.set_online(toggle.online)


@app.websocket("/ws/er_alerts")
async def ws_er_alerts(websocket: WebSocket):
    await er_alerts.connect(websocket)
    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                continue
    except WebSocketDisconnect:
        await er_alerts.disconnect(websocket)


@app.websocket("/ws/ambulance_stream")
async def ws_ambulance_stream(websocket: WebSocket):
    await websocket.accept()

    spo2_rolling_window: Deque[float] = deque(maxlen=ROLLING_WINDOW_SIZE)
    recent_vitals: Deque[Dict[str, Any]] = deque(maxlen=ROLLING_WINDOW_SIZE)

    anomaly_streak = 0
    briefing_armed = True

    async def _trigger_briefing(snapshot: List[Dict[str, Any]]) -> None:
        try:
            briefing_obj = await generate_triage_briefing(snapshot)
            payload = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "briefing": briefing_obj,
                "window_seconds": len(snapshot),
            }
            await network_state.enqueue_or_broadcast(payload)
        except Exception as e:
            print(f"LLM briefing generation failed: {e}")

    try:
        async for vital_data in vitals_async_iter():
            current_spo2 = float(vital_data["SpO2"])
            anomalous = is_spo2_anomalous(current_spo2, spo2_rolling_window)

            recent_vitals.append(vital_data)
            spo2_rolling_window.append(current_spo2)

            if anomalous:
                anomaly_streak += 1
            else:
                anomaly_streak = 0
                briefing_armed = True

            if briefing_armed and anomaly_streak >= ANOMALY_STREAK_SECONDS:
                briefing_armed = False
                asyncio.create_task(_trigger_briefing(list(recent_vitals)))

            await websocket.send_text(json.dumps({**vital_data, "is_anomalous": anomalous}))

    except WebSocketDisconnect:
        print("Client disconnected from /ws/ambulance_stream.")
    except Exception as e:
        print(f"An error occurred in /ws/ambulance_stream: {e}")