import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

export default function App() {
  const [data, setData] = useState<any[]>([]);
  const [alert, setAlert] = useState<string | null>(null);
  const [view, setView] = useState<'paramedic' | 'er'>('paramedic');

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onmessage = (event) => {
      const parsed = JSON.parse(event.data);
      setData(prev => {
        const newData = [...prev, parsed];
        if (newData.length > 50) newData.shift(); // keep window small
        return newData;
      });

      if (parsed.triage_alert) {
        setAlert(parsed.triage_alert);
      }
    };

    return () => ws.close();
  }, []);

  const latest = data[data.length - 1];

  if (!latest) return <div className="p-8 text-black">Connecting to ambulance telemetry...</div>;

  return (
    <div className={view === 'paramedic' ? "min-h-screen bg-gray-950 text-white" : "min-h-screen bg-gray-50 text-gray-900"}>
      <header className={`p-4 flex justify-between items-center ${view === 'paramedic' ? 'bg-gray-900' : 'bg-white shadow'}`}>
        <h1 className="text-2xl font-bold">Nexus Health System</h1>
        <div className="space-x-4">
          <button 
            onClick={() => setView('paramedic')}
            className={`px-4 py-2 rounded ${view === 'paramedic' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            Paramedic View
          </button>
          <button 
            onClick={() => setView('er')}
            className={`px-4 py-2 rounded ${view === 'er' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-black'}`}
          >
            ER Dashboard
          </button>
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto">
        {/* Status Indicator */}
        <div className="mb-6 flex justify-between items-center">
            <h2 className="text-xl font-semibold">Live Vitals - Unit 42</h2>
            <div className={`px-4 py-2 rounded-full font-bold uppercase tracking-wider ${latest.status === 'Red' ? 'bg-red-500 text-white' : latest.status === 'Yellow' ? 'bg-yellow-500 text-black' : 'bg-green-500 text-white'}`}>
                Status: {latest.status}
            </div>
        </div>

        {/* Triage Alert in ER View */}
        {view === 'er' && alert && (
            <div className="mb-8 p-6 bg-red-100 border-l-4 border-red-600 text-red-900 rounded shadow-lg animate-pulse">
                <h3 className="text-xl font-bold mb-2">🚨 CRITICAL PRE-ARRIVAL ALERT</h3>
                <p className="whitespace-pre-wrap font-medium">{alert}</p>
            </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className={`p-4 rounded-xl ${view === 'paramedic' ? 'bg-gray-900' : 'bg-white shadow'}`}>
                <h3 className="text-lg font-semibold mb-4">Heart Rate (BPM) - {latest.heart_rate}</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke={view === 'paramedic' ? '#333' : '#eee'} />
                            <XAxis dataKey="timestamp" stroke={view === 'paramedic' ? '#888' : '#333'} />
                            <YAxis domain={[30, 200]} stroke={view === 'paramedic' ? '#888' : '#333'} />
                            <Tooltip contentStyle={{ backgroundColor: view === 'paramedic' ? '#111' : '#fff' }} />
                            <ReferenceLine y={100} stroke="red" strokeDasharray="3 3" />
                            <Line type="monotone" dataKey="heart_rate" stroke="#ff4d4d" strokeWidth={3} isAnimationActive={false} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className={`p-4 rounded-xl ${view === 'paramedic' ? 'bg-gray-900' : 'bg-white shadow'}`}>
                <h3 className="text-lg font-semibold mb-4">Blood Pressure Sys (mmHg) - {latest.blood_pressure}</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke={view === 'paramedic' ? '#333' : '#eee'} />
                            <XAxis dataKey="timestamp" stroke={view === 'paramedic' ? '#888' : '#333'} />
                            <YAxis domain={[40, 180]} stroke={view === 'paramedic' ? '#888' : '#333'} />
                            <Tooltip contentStyle={{ backgroundColor: view === 'paramedic' ? '#111' : '#fff' }} />
                            <ReferenceLine y={90} stroke="red" strokeDasharray="3 3" />
                            <Line type="monotone" dataKey="blood_pressure" stroke="#3b82f6" strokeWidth={3} isAnimationActive={false} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
      </main>
    </div>
  );
}
