import { useEffect, useMemo, useRef, useState } from 'react';

const WS_URL = 'ws://localhost:8000/ws/er_alerts';

function formatTimestamp(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleString([], { hour12: false });
}

function formatMMSS(totalSeconds) {
  const s = Math.max(0, Number(totalSeconds) || 0);
  const mm = String(Math.floor(s / 60)).padStart(2, '0');
  const ss = String(s % 60).padStart(2, '0');
  return `${mm}:${ss}`;
}

function parseBriefing(raw) {
  if (!raw) return null;

  let obj = raw;
  if (typeof obj === 'string') {
    try {
      obj = JSON.parse(obj);
    } catch {
      return null;
    }
  }

  if (!obj || typeof obj !== 'object') return null;

  const Clinical_Summary = String(obj.Clinical_Summary ?? '').trim();
  const Predicted_Condition = String(obj.Predicted_Condition ?? '').trim();
  const Actionable_Prep = Array.isArray(obj.Actionable_Prep)
    ? obj.Actionable_Prep.map((x) => String(x).trim()).filter(Boolean).slice(0, 3)
    : [];

  if (!Clinical_Summary && !Predicted_Condition && Actionable_Prep.length === 0) return null;

  return { Clinical_Summary, Predicted_Condition, Actionable_Prep };
}

export default function ERDashboard({ embedded = false } = {}) {
  const [status, setStatus] = useState('disconnected'); // connecting | connected | disconnected
  const [error, setError] = useState('');
  const [alerts, setAlerts] = useState([]); // [{ timestamp, briefingObj, window_seconds }]

  const [etaTargetMs, setEtaTargetMs] = useState(null);
  const [nowMs, setNowMs] = useState(Date.now());

  const wsRef = useRef(null);
  const retryRef = useRef({ attempt: 0, timer: null, closedByUser: false });

  const latest = alerts.length ? alerts[0] : null;

  useEffect(() => {
    const id = window.setInterval(() => setNowMs(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const etaSeconds = useMemo(() => {
    if (!etaTargetMs) return 600; // default 10:00 for the "waiting" state
    return Math.max(0, Math.floor((etaTargetMs - nowMs) / 1000));
  }, [etaTargetMs, nowMs]);

  const meta = useMemo(() => {
    return {
      wsUrl: WS_URL,
      lastUpdated: latest?.timestamp ? formatTimestamp(latest.timestamp) : null,
    };
  }, [latest]);

  useEffect(() => {
    const retryState = retryRef.current;
    retryState.closedByUser = false;

    const connect = () => {
      setError('');
      setStatus('connecting');

      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        retryState.attempt = 0;
        setStatus('connected');
      };

      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);

          const briefingObj = parseBriefing(msg.briefing);
          if (!briefingObj) return;

          const payload = {
            timestamp: msg.timestamp ?? new Date().toISOString(),
            briefingObj,
            window_seconds: Number(msg.window_seconds ?? 0),
          };

          setAlerts((prev) => [payload, ...prev].slice(0, 10));
          setEtaTargetMs(Date.now() + 10 * 60 * 1000); // reset countdown on each incoming alert
        } catch (e) {
          console.error('Failed to parse ER alert payload:', e);
        }
      };

      ws.onerror = () => {
        setError('WebSocket error');
      };

      ws.onclose = () => {
        wsRef.current = null;
        setStatus('disconnected');

        if (retryState.closedByUser) return;

        retryState.attempt += 1;
        const delayMs = Math.min(8000, 500 * 2 ** (retryState.attempt - 1));
        retryState.timer = window.setTimeout(connect, delayMs);
      };
    };

    connect();

    return () => {
      retryState.closedByUser = true;
      if (retryState.timer) window.clearTimeout(retryState.timer);
      retryState.timer = null;
      if (wsRef.current) wsRef.current.close();
      wsRef.current = null;
    };
  }, []);

  return (
    <div className={embedded ? '' : 'min-h-screen bg-slate-950 text-slate-100'}>
      <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6">
        {/* Top urgency bar */}
        <div className="mb-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-4 ring-1 ring-slate-800">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="text-xs font-semibold tracking-wider text-slate-400">
                HOSPITAL DASHBOARD
              </div>
              <div className="mt-1 text-sm font-semibold text-slate-100">
                ER Doctor View — Pre‑Arrival Alerts
              </div>
              <div className="mt-1 text-xs text-slate-300">
                ETA COUNTDOWN (demo): <span className="font-semibold text-slate-50">{formatMMSS(etaSeconds)}</span>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span
                className={[
                  'rounded-full px-3 py-1 text-xs font-medium ring-1',
                  status === 'connected'
                    ? 'bg-emerald-500/10 text-emerald-200 ring-emerald-500/30'
                    : status === 'connecting'
                      ? 'bg-amber-500/10 text-amber-200 ring-amber-500/30'
                      : 'bg-slate-500/10 text-slate-200 ring-slate-500/30',
                ].join(' ')}
              >
                {status.toUpperCase()}
              </span>

              {error ? (
                <span className="rounded-full bg-rose-500/10 px-3 py-1 text-xs font-medium text-rose-200 ring-1 ring-rose-500/30">
                  {error}
                </span>
              ) : null}

              <span className="hidden sm:inline-flex rounded-full bg-slate-500/10 px-3 py-1 text-xs font-medium text-slate-200 ring-1 ring-slate-500/30">
                Source: {meta.wsUrl}
              </span>
            </div>
          </div>
        </div>

        <main className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <section className="lg:col-span-2">
            {!latest ? (
              <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-slate-200">
                    Waiting for incoming transit...
                  </div>
                  <div className="text-xs text-slate-400">
                    {status === 'connected' ? 'Listening for alerts' : 'Connecting'}
                  </div>
                </div>

                <div className="mt-4 rounded-xl bg-slate-950/40 p-4 ring-1 ring-slate-800">
                  <div className="text-xs font-semibold tracking-wider text-slate-400">
                    STATUS
                  </div>
                  <div className="mt-2 text-sm text-slate-200">
                    No Pre‑Arrival Triage Briefing received yet.
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 p-5 ring-1 ring-rose-500/30 animate-pulse">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-rose-500/15 px-3 py-1 text-xs font-semibold tracking-wider text-rose-200 ring-1 ring-rose-500/30">
                      HIGH PRIORITY ALERT
                    </div>
                    <h2 className="mt-3 text-lg font-semibold text-slate-50">
                      Pre‑Arrival Triage Briefing
                    </h2>
                    <div className="mt-1 text-xs text-slate-200/80">
                      Received: <span className="font-medium">{formatTimestamp(latest.timestamp)}</span>
                      {latest.window_seconds ? (
                        <span className="ml-2 text-slate-200/70">
                          (window: {latest.window_seconds}s)
                        </span>
                      ) : null}
                    </div>
                  </div>

                  <div className="rounded-xl bg-slate-950/40 px-3 py-2 ring-1 ring-rose-500/20">
                    <div className="text-[11px] font-semibold tracking-wider text-slate-300">
                      PREDICTED
                    </div>
                    <div className="mt-1 text-xs font-semibold text-slate-50">
                      {latest.briefingObj.Predicted_Condition || '—'}
                    </div>
                  </div>
                </div>

                <div className="mt-4 rounded-xl bg-slate-950/50 p-4 ring-1 ring-rose-500/25">
                  <div className="text-xs font-semibold tracking-wider text-rose-200/90">
                    CLINICAL SUMMARY
                  </div>
                  <p className="mt-3 text-base leading-relaxed text-slate-50">
                    {latest.briefingObj.Clinical_Summary}
                  </p>
                </div>

                <div className="mt-4 rounded-xl bg-slate-950/50 p-4 ring-1 ring-rose-500/25">
                  <div className="text-xs font-semibold tracking-wider text-rose-200/90">
                    ACTIONABLE PREP (CHECKLIST)
                  </div>
                  <div className="mt-3 space-y-2">
                    {(latest.briefingObj.Actionable_Prep || []).map((item, i) => (
                      <label
                        key={`${item}-${i}`}
                        className="flex items-start gap-3 rounded-lg bg-slate-950/40 p-2 ring-1 ring-slate-800"
                      >
                        <input
                          type="checkbox"
                          className="mt-0.5 h-4 w-4 accent-rose-500"
                        />
                        <span className="text-sm font-medium text-slate-50">{item}</span>
                      </label>
                    ))}
                    {(!latest.briefingObj.Actionable_Prep || latest.briefingObj.Actionable_Prep.length === 0) ? (
                      <div className="text-xs text-slate-300">No prep checklist provided.</div>
                    ) : null}
                  </div>
                </div>

                {meta.lastUpdated ? (
                  <div className="mt-3 text-xs text-slate-200/70">
                    Last updated: {meta.lastUpdated}
                  </div>
                ) : null}
              </div>
            )}
          </section>

          <aside className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-200">Alert Feed</h3>
              <span className="rounded-full bg-slate-500/10 px-2.5 py-1 text-xs font-medium text-slate-200 ring-1 ring-slate-500/30">
                {alerts.length} recent
              </span>
            </div>

            <div className="mt-3 space-y-2">
              {alerts.length === 0 ? (
                <div className="rounded-xl bg-slate-950/40 p-3 ring-1 ring-slate-800">
                  <div className="text-xs text-slate-400">
                    No alerts yet. Keep this view open for incoming briefings.
                  </div>
                </div>
              ) : (
                alerts.map((a, idx) => (
                  <div
                    key={`${a.timestamp}-${idx}`}
                    className={[
                      'rounded-xl p-3 ring-1',
                      idx === 0
                        ? 'bg-rose-500/10 ring-rose-500/25'
                        : 'bg-slate-950/40 ring-slate-800',
                    ].join(' ')}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-xs font-semibold text-slate-200">
                        {idx === 0 ? 'LATEST' : 'PRIOR'}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {formatTimestamp(a.timestamp)}
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-slate-200/90">
                      {a.briefingObj?.Predicted_Condition
                        ? `${a.briefingObj.Predicted_Condition}: `
                        : ''}
                      {a.briefingObj?.Clinical_Summary || ''}
                    </div>
                  </div>
                ))
              )}
            </div>
          </aside>
        </main>
      </div>
    </div>
  );
}