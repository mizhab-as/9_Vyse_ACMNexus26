import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ParamedicDashboard, ERDashboard } from './DualDashboard';

/**
 * App: Main component handling WebSocket connection and view routing.
 */
export default function App() {
  const [vitalsData, setVitalsData] = useState(null);
  const [triageData, setTriageData] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

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
        if (data.vitals) setVitalsData(data.vitals);
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
      // Attempt reconnect after 3 seconds
      setTimeout(() => {
        // Reconnection logic would go here
      }, 3000);
    };

    return () => ws.close();
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        {/* Navigation Bar */}
        <nav className="bg-blue-600 text-white p-4 shadow-lg">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="flex space-x-6">
              <Link to="/" className="font-bold text-lg hover:text-blue-100">
                🏥 NEXUS Triage
              </Link>
              <Link to="/" className="hover:text-blue-100">
                Paramedic View
              </Link>
              <Link to="/er" className="hover:text-blue-100">
                ER Dashboard
              </Link>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-400' :
                connectionStatus === 'error' ? 'bg-red-400' :
                'bg-gray-400'
              }`}></div>
              <span className="text-sm">{connectionStatus}</span>
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
