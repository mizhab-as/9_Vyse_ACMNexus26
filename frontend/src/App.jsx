import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ParamedicDashboard, ERDashboard } from './EnhancedDashboard';

/**
 * App: Main component handling WebSocket connection and view routing.
 */
export default function App() {
  const [vitalsData, setVitalsData] = useState(null);
  const [triageData, setTriageData] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    // Connect to WebSocket backend
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/dashboard';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('✓ Connected to backend');
      setConnectionStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.vitals) {
          setVitalsData(data.vitals);
          setLastUpdate(new Date().toLocaleTimeString());
        }
        if (data.triage) setTriageData(data.triage);
      } catch (e) {
        console.error('Failed to parse message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('error');
    };

    ws.onclose = () => {
      console.log('✗ Disconnected from backend');
      setConnectionStatus('disconnected');
    };

    return () => ws.close();
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-gray-900">
        {/* Professional Navigation Bar */}
        <nav className="bg-gradient-to-r from-blue-900 to-blue-800 text-white p-4 shadow-2xl border-b-2 border-blue-600">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="flex space-x-8 items-center">
              <div className="font-bold text-2xl flex items-center space-x-2">
                <span className="text-cyan-400 text-3xl">H</span>
                <span>NEXUS Triage System</span>
              </div>
              <Link to="/" className="hover:text-cyan-300 font-semibold transition">
                Paramedic Dashboard
              </Link>
              <Link to="/er" className="hover:text-cyan-300 font-semibold transition">
                ER Pre-Arrival
              </Link>
            </div>
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-400 animate-pulse' :
                connectionStatus === 'error' ? 'bg-red-400' :
                'bg-gray-400'
              }`}></div>
              <span className="text-sm font-mono">
                {connectionStatus === 'connected' ? 'Live' : connectionStatus.toUpperCase()}
              </span>
              {lastUpdate && (
                <span className="text-xs text-gray-300 font-mono ml-4">
                  Last update: {lastUpdate}
                </span>
              )}
            </div>
          </div>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<ParamedicDashboard vitalsData={vitalsData} triageData={triageData} />} />
          <Route path="/er" element={<ERDashboard vitalsData={vitalsData} triageData={triageData} />} />
        </Routes>
      </div>
    </Router>
  );
}

