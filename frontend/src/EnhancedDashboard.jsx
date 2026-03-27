import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

/**
 * Enhanced Paramedic Dashboard with real-time vitals streaming
 */
export const ParamedicDashboard = ({ vitalsData, triageData }) => {
  const [vitalsHistory, setVitalsHistory] = useState([]);
  const [scrollIndex, setScrollIndex] = useState(0);

  useEffect(() => {
    if (vitalsData?.vitals) {
      setVitalsHistory(prev => {
        const updated = [...prev, {
          time: vitalsHistory.length,
          ...vitalsData.vitals
        }];
        return updated.slice(-200); // Keep last 200 samples
      });
    }
  }, [vitalsData]);

  const getColorClass = (value, normal_min, normal_max) => {
    if (value < normal_min || value > normal_max) return 'text-red-600 font-bold';
    return 'text-green-600';
  };

  return (
    <div className="bg-slate-950 text-white p-6 min-h-screen font-mono">
      <div className="max-w-7xl mx-auto">
        {/* Header with status indicator */}
        <div className="mb-8 border-b-2 border-cyan-500 pb-4">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-4xl font-bold text-cyan-400 mb-2">
                {triageData?.alert_level === 'CRITICAL' ? '[CRITICAL] ' : ''}AMBULANCE MONITOR
              </h1>
              <p className="text-cyan-600 text-sm">Patient ID: {vitalsData?.patient_id || 'AWAITING...'}</p>
              {vitalsData?.location && (
                <p className="text-cyan-600 text-sm">
                  ETA: {vitalsData.location.eta_minutes} min | Location: {vitalsData.location.latitude.toFixed(4)}, {vitalsData.location.longitude.toFixed(4)}
                </p>
              )}
            </div>
            <div className={`w-4 h-4 rounded-full animate-pulse ${
              triageData?.alert_level === 'CRITICAL' ? 'bg-red-600' :
              triageData?.alert_level === 'WARNING' ? 'bg-yellow-600' :
              'bg-green-600'
            }`}></div>
          </div>
        </div>

        {/* Main vitals grid - medical ICU style */}
        <div className="grid grid-cols-3 gap-3 mb-8">
          <VitalMonitor
            label="HR"
            value={vitalsData?.vitals?.heart_rate || '--'}
            unit="bpm"
            min={60}
            max={100}
            critical_low={50}
            critical_high={130}
          />
          <VitalMonitor
            label="SBP"
            value={vitalsData?.vitals?.systolic_bp || '--'}
            unit="mmHg"
            min={90}
            max={130}
            critical_low={70}
            critical_high={180}
          />
          <VitalMonitor
            label="DBP"
            value={vitalsData?.vitals?.diastolic_bp || '--'}
            unit="mmHg"
            min={60}
            max={90}
            critical_low={40}
            critical_high={110}
          />
          <VitalMonitor
            label="RR"
            value={vitalsData?.vitals?.respiratory_rate || '--'}
            unit="br/min"
            min={12}
            max={20}
            critical_low={8}
            critical_high={30}
          />
          <VitalMonitor
            label="SpO2"
            value={vitalsData?.vitals?.oxygen_saturation || '--'}
            unit="%"
            min={95}
            max={100}
            critical_low={85}
            critical_high={101}
          />
          <VitalMonitor
            label="TEMP"
            value={(vitalsData?.vitals?.temperature || 0).toFixed(1)}
            unit="°C"
            min={36.5}
            max={37.5}
            critical_low={35}
            critical_high={40}
          />
        </div>

        {/* Real-time waveform chart */}
        <div className="bg-slate-900 border border-cyan-700 rounded-lg p-4 mb-8">
          <h2 className="text-cyan-400 font-bold mb-4 text-lg">HEART RATE WAVEFORM</h2>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={vitalsHistory}>
              <defs>
                <linearGradient id="colorHR" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
              <XAxis stroke="#64748b" />
              <YAxis stroke="#64748b" domain={[40, 160]} />
              <Tooltip
                contentStyle={{ backgroundColor: '#000', border: '1px solid #06b6d4', borderRadius: '4px' }}
                labelStyle={{ color: '#06b6d4' }}
              />
              <Area
                type="monotone"
                dataKey="heart_rate"
                stroke="#06b6d4"
                fillOpacity={1}
                fill="url(#colorHR)"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Alert section */}
        {triageData?.alert_level && (
          <div className={`border-2 rounded-lg p-4 mb-8 ${
            triageData.alert_level === 'CRITICAL' ? 'border-red-600 bg-red-950' :
            triageData.alert_level === 'WARNING' ? 'border-yellow-600 bg-yellow-950' :
            'border-green-600 bg-green-950'
          }`}>
            <p className={`font-bold text-lg mb-2 ${
              triageData.alert_level === 'CRITICAL' ? 'text-red-300' :
              triageData.alert_level === 'WARNING' ? 'text-yellow-300' :
              'text-green-300'
            }`}>
              [{triageData.alert_level}] {triageData.triage_briefing}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Enhanced ER Dashboard - High contrast, clinical focus
 */
export const ERDashboard = ({ vitalsData, triageData }) => {
  const getColorTheme = (colorCode) => {
    switch (colorCode) {
      case 'RED':
        return { wrapper: 'border-red-600 bg-red-50', title: 'text-red-900', accent: 'bg-red-600' };
      case 'YELLOW':
        return { wrapper: 'border-yellow-600 bg-yellow-50', title: 'text-yellow-900', accent: 'bg-yellow-600' };
      default:
        return { wrapper: 'border-green-600 bg-green-50', title: 'text-green-900', accent: 'bg-green-600' };
    }
  };

  const theme = getColorTheme(triageData?.color_code);

  return (
    <div className="bg-white p-8 min-h-screen">
      <div className="max-w-5xl mx-auto">
        {/* Emergency Header */}
        <div className={`border-4 rounded-lg p-8 mb-8 ${theme.wrapper}`}>
          <div className="flex justify-between items-center mb-4">
            <h1 className={`text-4xl font-black ${theme.title}`}>
              PRE-ARRIVAL PATIENT BRIEFING
            </h1>
            <div className={`${theme.accent} text-white px-6 py-3 rounded-lg font-bold text-lg`}>
              {triageData?.alert_level || 'STABLE'}
            </div>
          </div>

          <div className={`text-lg font-semibold mb-4 ${theme.title} leading-relaxed`}>
            {triageData?.triage_briefing || 'Awaiting patient data...'}
          </div>

          {triageData?.alert_level === 'CRITICAL' && (
            <div className="bg-red-600 text-white p-2 rounded font-bold text-center text-sm">
              URGENT - IMMEDIATE PREPARATION REQUIRED
            </div>
          )}
        </div>

        {/* Vitals Snapshot Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
          <div className="bg-gray-900 text-white p-4 rounded-lg text-center">
            <p className="text-gray-400 text-xs font-bold mb-1">HEART RATE</p>
            <p className="text-3xl font-bold">{vitalsData?.vitals?.heart_rate ?? '--'}</p>
            <p className="text-gray-500 text-xs">bpm</p>
          </div>
          <div className="bg-gray-900 text-white p-4 rounded-lg text-center">
            <p className="text-gray-400 text-xs font-bold mb-1">BLOOD PRESSURE</p>
            <p className="text-3xl font-bold">{vitalsData?.vitals?.systolic_bp ?? '--'}/{vitalsData?.vitals?.diastolic_bp ?? '--'}</p>
            <p className="text-gray-500 text-xs">mmHg</p>
          </div>
          <div className="bg-gray-900 text-white p-4 rounded-lg text-center">
            <p className="text-gray-400 text-xs font-bold mb-1">O2 SAT</p>
            <p className="text-3xl font-bold">{vitalsData?.vitals?.oxygen_saturation ?? '--'}</p>
            <p className="text-gray-500 text-xs">%</p>
          </div>
          <div className="bg-gray-900 text-white p-4 rounded-lg text-center">
            <p className="text-gray-400 text-xs font-bold mb-1">RESP RATE</p>
            <p className="text-3xl font-bold">{vitalsData?.vitals?.respiratory_rate ?? '--'}</p>
            <p className="text-gray-500 text-xs">br/min</p>
          </div>
        </div>

        {/* Actions */}
        {triageData?.recommended_actions && (
          <div className="bg-blue-50 border-l-4 border-blue-600 p-6 rounded-lg">
            <h3 className="text-xl font-bold text-blue-900 mb-4">IMMEDIATE ACTIONS</h3>
            <ul className="space-y-3">
              {triageData.recommended_actions.map((action, idx) => (
                <li key={idx} className="flex items-start text-blue-900">
                  <span className="bg-blue-600 text-white font-bold px-3 py-1 rounded-full mr-3 min-w-fit">
                    {idx + 1}
                  </span>
                  <span className="font-semibold pt-1">{action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Vital Monitor Component (ICU-style)
 */
const VitalMonitor = ({ label, value, unit, min, max, critical_low, critical_high }) => {
  let borderColor = 'border-green-500';
  let textColor = 'text-green-300';

  if (typeof value === 'number') {
    if (value < critical_low || value > critical_high) {
      borderColor = 'border-red-600';
      textColor = 'text-red-400';
    } else if (value < min || value > max) {
      borderColor = 'border-yellow-600';
      textColor = 'text-yellow-300';
    }
  }

  return (
    <div className={`border-2 ${borderColor} rounded-lg p-4 bg-slate-900 text-center`}>
      <p className="text-slate-400 text-xs font-bold mb-2">{label}</p>
      <p className={`text-3xl font-bold ${textColor} mb-1`}>{value}</p>
      <p className="text-slate-500 text-xs">{unit}</p>
    </div>
  );
};

export default { ParamedicDashboard, ERDashboard };
