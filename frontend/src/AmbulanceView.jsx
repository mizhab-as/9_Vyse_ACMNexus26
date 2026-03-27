import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';

const WS_URL = 'ws://localhost:8000/ws/ambulance_stream';
const API_BASE = 'http://localhost:8000';

function formatTime(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleTimeString([], { hour12: false });
}

function clamp(n, lo, hi) {
  return Math.min(hi, Math.max(lo, n));
}

export default function AmbulanceView({ embedded = false } = {}) {
  const [status, setStatus] = useState('disconnected'); // connecting | connected | disconnected
  const [error, setError] = useState('');
  const [data, setData] = useState([]); // [{ t, spo2, hr, is_anomalous }]
  const [networkOnline, setNetworkOnline] = useState(true);
  const [netBusy, setNetBusy] = useState(false);

  const wsRef = useRef(null);
  const retryRef = useRef({ attempt: 0, timer: null, closedByUser: false });

  const latest = data.length ? data[data.length - 1] : null;

  const chartData = useMemo(() => {
    return data.map((d) => ({
      t: d.t,
      SpO2: d.spo2,
      HR: d.hr,
      is_anomalous: d.is_anomalous,
    }));
  }, [data]);

  const patientCritical = Boolean(latest?.is_anomalous);

  const spo2Stroke = useMemo(() => {
    const spo2 = latest?.spo2;
    if (!Number.isFinite(spo2)) return 'rgb(var(--chart-spo2))';
    if (spo2 < 92) return 'rgb(239 68 68)'; // red-500
    if (spo2 >= 95) return 'rgb(var(--chart-spo2))'; // green
    return 'rgb(245 158 11)'; // amber-500
  }, [latest?.spo2]);

  useEffect(() => {
    // Load initial network toggle state for demo.
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/network`);
        const j = await res.json();
        setNetworkOnline(Boolean(j.online));
      } catch {
        // If API is unreachable, keep default (online) and avoid blocking the view.
      }
    })();
  }, []);

  async function toggleNetwork() {
    setNetBusy(true);
    try {
      const next = !networkOnline;
      const res = await fetch(`${API_BASE}/api/network`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ online: next }),
      });
      const j = await res.json();
      setNetworkOnline(Boolean(j.online));
    } catch (e) {
      setError('Network toggle failed');
    } finally {
      setNetBusy(false);
    }
  }

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
          const t = msg.timestamp ? formatTime(msg.timestamp) : '';
          const spo2 = Number(msg.SpO2);
          const hr = Number(msg.HR);
          const is_anomalous = Boolean(msg.is_anomalous);

          if (!Number.isFinite(spo2) || !Number.isFinite(hr)) return;

          setData((prev) => {
            const next = prev.concat([
              {
                t,
                spo2: clamp(spo2, 0, 100),
                hr: Math.max(0, hr),
                is_anomalous,
              },
            ]);
            const MAX_POINTS = 300;
            return next.length > MAX_POINTS ? next.slice(next.length - MAX_POINTS) : next;
          });
        } catch (e) {
          console.error('Failed to parse websocket message', e);
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
        {/* Patient Status Banner */}
        <div
          className={[
            'mb-4 rounded-2xl border px-4 py-3 ring-1 backdrop-blur',
            patientCritical
              ? 'border-rose-500/40 bg-rose-500/10 ring-rose-500/30 animate-pulse'
              : 'border-emerald-500/30 bg-emerald-500/10 ring-emerald-500/20',
          ].join(' ')}
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div
                className={[
                  'h-2.5 w-2.5 rounded-full',
                  patientCritical ? 'bg-rose-400' : 'bg-emerald-400',
                ].join(' ')}
              />
              <div
                className={[
                  'text-sm font-semibold tracking-wide',
                  patientCritical ? 'text-rose-100' : 'text-emerald-100',
                ].join(' ')}
              >
                {patientCritical ? 'CRITICAL: ANOMALY DETECTED' : 'STABLE'}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={toggleNetwork}
                disabled={netBusy}
                className={[
                  'rounded-full px-3 py-1 text-xs font-semibold ring-1 transition',
                  networkOnline
                    ? 'bg-emerald-500/10 text-emerald-200 ring-emerald-500/30 hover:bg-emerald-500/15'
                    : 'bg-slate-500/10 text-slate-200 ring-slate-500/30 hover:bg-slate-500/15',
                  netBusy ? 'opacity-70 cursor-not-allowed' : '',
                ].join(' ')}
                title="Demo: toggle ER network online/offline"
              >
                Network: {networkOnline ? 'Online' : 'Offline'}
              </button>

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
                Stream: {WS_URL}
              </span>
            </div>
          </div>
        </div>

        <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight sm:text-2xl">
              Ambulance Monitor
            </h1>
            <p className="mt-1 text-sm text-slate-300">
              Bedside-style waveform display (SpO2 + HR), updating every second.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {latest ? (
              <>
                <span className="rounded-full bg-slate-500/10 px-3 py-1 text-xs font-medium text-slate-200 ring-1 ring-slate-500/30">
                  SpO2: <span className="font-semibold">{latest.spo2.toFixed(1)}%</span>
                </span>
                <span className="rounded-full bg-slate-500/10 px-3 py-1 text-xs font-medium text-slate-200 ring-1 ring-slate-500/30">
                  HR: <span className="font-semibold">{latest.hr.toFixed(0)} bpm</span>
                </span>
              </>
            ) : (
              <span className="rounded-full bg-slate-500/10 px-3 py-1 text-xs font-medium text-slate-200 ring-1 ring-slate-500/30">
                Awaiting vitals…
              </span>
            )}
          </div>
        </header>

        <section className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4 lg:col-span-1 flex flex-col justify-center">
            <h2 className="text-sm font-semibold text-slate-200">Latest Vitals</h2>

            <div className="mt-3 grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-slate-950/40 p-3 ring-1 ring-slate-800 flex flex-col items-center justify-center">
                <div className="text-xs text-slate-400">SpO2</div>
                <div
                  className={[
                    'mt-1 text-4xl font-semibold tabular-nums',
                    latest?.spo2 < 92 ? 'text-rose-400' : 'text-emerald-400',
                  ].join(' ')}
                >
                  {latest ? `${latest.spo2.toFixed(1)}%` : '—'}
                </div>
              </div>

              <div className="rounded-xl bg-slate-950/40 p-3 ring-1 ring-slate-800 flex flex-col items-center justify-center">
                <div className="text-xs text-slate-400">Heart Rate</div>
                <div className="mt-1 text-4xl font-semibold tabular-nums text-blue-400">
                  {latest ? `${latest.hr.toFixed(0)}` : '—'}
                </div>
              </div>
            </div>

            <div className="mt-4 text-xs text-slate-400 text-center">
              Showing last <span className="font-medium text-slate-200">{data.length}</span> seconds
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4 lg:col-span-2">
            <div className="mb-3 flex items-baseline justify-between gap-3">
              <h2 className="text-sm font-semibold text-slate-200">Real-time Trend</h2>
              <div className="text-xs text-slate-400 hidden sm:block">
                SpO2 color: green ≥95, amber 92–95, red &lt;92
              </div>
            </div>

            <div className="h-[360px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 8, right: 12, left: -20, bottom: 8 }}>
                  <CartesianGrid stroke="rgba(148,163,184,0.12)" strokeDasharray="3 3" />
                  <XAxis
                    dataKey="t"
                    tick={{ fill: 'rgba(226,232,240,0.8)', fontSize: 12 }}
                    axisLine={{ stroke: 'rgba(148,163,184,0.25)' }}
                    tickLine={{ stroke: 'rgba(148,163,184,0.25)' }}
                    interval="preserveEnd"
                    minTickGap={30}
                  />
                  <YAxis
                    yAxisId="spo2"
                    domain={[60, 100]}
                    tick={{ fill: 'rgba(226,232,240,0.8)', fontSize: 12 }}
                    axisLine={{ stroke: 'rgba(148,163,184,0.25)' }}
                    tickLine={{ stroke: 'rgba(148,163,184,0.25)' }}
                  />
                  <YAxis
                    yAxisId="hr"
                    orientation="right"
                    domain={[40, 180]}
                    tick={{ fill: 'rgba(226,232,240,0.8)', fontSize: 12 }}
                    axisLine={{ stroke: 'rgba(148,163,184,0.25)' }}
                    tickLine={{ stroke: 'rgba(148,163,184,0.25)' }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: 'rgba(2,6,23,0.92)',
                      border: '1px solid rgba(148,163,184,0.25)',
                      borderRadius: 8,
                      color: 'rgba(226,232,240,0.95)',
                      fontSize: 12,
                    }}
                    labelStyle={{ color: 'rgba(226,232,240,0.8)', marginBottom: '4px' }}
                  />
                  <Legend wrapperStyle={{ color: 'rgba(226,232,240,0.8)', fontSize: 12, paddingTop: '10px' }} />

                  <Line
                    yAxisId="spo2"
                    type="monotone"
                    dataKey="SpO2"
                    name="SpO2 (%)"
                    stroke={spo2Stroke}
                    strokeWidth={2.25}
                    dot={false}
                    isAnimationActive={false}
                    style={{ transition: 'stroke 300ms ease' }}
                  />
                  <Line
                    yAxisId="hr"
                    type="monotone"
                    dataKey="HR"
                    name="HR (bpm)"
                    stroke="rgb(var(--chart-hr))"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {!data.length && status === 'connected' ? (
              <div className="mt-3 text-sm text-slate-300 flex justify-center">
                Waiting for first vitals packet...
              </div>
            ) : null}
          </div>
        </section>
      </div>
    </div>
  );
}