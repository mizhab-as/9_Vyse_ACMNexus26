import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

/**
 * ParamedicDashboard: Dark mode, data-heavy view for ambulance crew.
 * Shows raw vitals streams with minimal interpretation.
 */
export const ParamedicDashboard = ({ vitalsData, triageData }) => {
  const [vitalsHistory, setVitalsHistory] = useState([]);

  useEffect(() => {
    if (vitalsData) {
      setVitalsHistory(prev => [...prev.slice(-100), vitalsData]);
    }
  }, [vitalsData]);

  return (
    <div className="bg-gray-900 text-white p-6 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold">🚑 Ambulance - Real-Time Monitoring</h1>
          <p className="text-gray-400 mt-2">Patient ID: {vitalsData?.patient_id || 'N/A'}</p>
        </div>

        {/* Vitals Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
          <VitalCard
            label="Heart Rate"
            value={vitalsData?.vitals?.heart_rate || '--'}
            unit="bpm"
            normal_range="60-100"
          />
          <VitalCard
            label="Systolic BP"
            value={vitalsData?.vitals?.systolic_bp || '--'}
            unit="mmHg"
            normal_range="90-130"
          />
          <VitalCard
            label="Diastolic BP"
            value={vitalsData?.vitals?.diastolic_bp || '--'}
            unit="mmHg"
            normal_range="60-90"
          />
          <VitalCard
            label="O2 Saturation"
            value={vitalsData?.vitals?.oxygen_saturation || '--'}
            unit="%"
            normal_range="95-100"
          />
          <VitalCard
            label="Respiratory Rate"
            value={vitalsData?.vitals?.respiratory_rate || '--'}
            unit="br/min"
            normal_range="12-20"
          />
          <VitalCard
            label="Temperature"
            value={(vitalsData?.vitals?.temperature || 0).toFixed(1)}
            unit="°C"
            normal_range="36.5-37.5"
          />
        </div>

        {/* Trends Chart */}
        <div className="bg-gray-800 rounded-lg p-4 mb-8">
          <h2 className="text-xl font-bold mb-4">Heart Rate Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={vitalsHistory}>
              <CartesianGrid stroke="#444" />
              <XAxis stroke="#999" label={{ value: 'Time (samples)', position: 'insideBottom', offset: -5 }} />
              <YAxis stroke="#999" domain={[40, 160]} />
              <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #fff' }} />
              <Line
                type="monotone"
                dataKey={(d) => d?.vitals?.heart_rate}
                stroke="#00ff00"
                isAnimationActive={false}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Alert Banner */}
        {triageData?.alert_level === 'CRITICAL' && (
          <div className="bg-red-900 border-l-4 border-red-500 p-4 rounded">
            <p className="font-bold text-red-100">⚠️ CRITICAL ALERT</p>
            <p className="text-red-100 text-sm mt-2">{triageData?.triage_briefing}</p>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * ERDashboard: Clean, professional view for emergency room physicians.
 * Highlights critical alerts with high-contrast design.
 */
export const ERDashboard = ({ vitalsData, triageData }) => {
  const getColorCode = (colorCode) => {
    switch (colorCode) {
      case 'RED':
        return { bg: 'bg-red-100', border: 'border-red-500', text: 'text-red-900' };
      case 'YELLOW':
        return { bg: 'bg-yellow-100', border: 'border-yellow-500', text: 'text-yellow-900' };
      default:
        return { bg: 'bg-green-100', border: 'border-green-500', text: 'text-green-900' };
    }
  };

  const colors = getColorCode(triageData?.color_code);

  return (
    <div className="bg-white p-8 min-h-screen">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">🏥 ER Pre-Arrival Briefing</h1>
        </div>

        {/* Main Alert Card */}
        <div className={`${colors.bg} ${colors.border} border-2 rounded-lg p-8 mb-8 shadow-lg`}>
          <div className="flex justify-between items-start mb-4">
            <h2 className={`${colors.text} text-3xl font-bold`}>
              {triageData?.alert_level === 'CRITICAL' ? '🚨 URGENT' : 'Status'}
            </h2>
            <span className={`${colors.text} text-sm font-semibold px-3 py-1 rounded-full bg-opacity-30`}>
              {triageData?.alert_level || 'STABLE'}
            </span>
          </div>

          <p className={`${colors.text} text-lg leading-relaxed`}>
            {triageData?.triage_briefing || 'Awaiting patient data...'}
          </p>
        </div>

        {/* Quick Vitals Snapshot */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <QuickVital
            label="HR"
            value={vitalsData?.vitals?.heart_rate}
            unit="bpm"
          />
          <QuickVital
            label="BP"
            value={`${vitalsData?.vitals?.systolic_bp}/${vitalsData?.vitals?.diastolic_bp}`}
            unit="mmHg"
          />
          <QuickVital
            label="O2"
            value={vitalsData?.vitals?.oxygen_saturation}
            unit="%"
          />
          <QuickVital
            label="RR"
            value={vitalsData?.vitals?.respiratory_rate}
            unit="br/min"
          />
        </div>

        {/* Recommended Actions */}
        {triageData?.recommended_actions && triageData.recommended_actions.length > 0 && (
          <div className="bg-gray-50 border-l-4 border-blue-500 p-6 rounded">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Recommended Actions</h3>
            <ul className="space-y-2">
              {triageData.recommended_actions.map((action, idx) => (
                <li key={idx} className="text-gray-700 flex items-start">
                  <span className="text-blue-500 font-bold mr-3">→</span>
                  {action}
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
 * Helper component: Vital sign card (paramedic view)
 */
const VitalCard = ({ label, value, unit, normal_range }) => {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <p className="text-gray-400 text-sm">{label}</p>
      <p className="text-3xl font-bold text-white mt-2">{value} {unit}</p>
      <p className="text-gray-500 text-xs mt-1">Normal: {normal_range}</p>
    </div>
  );
};

/**
 * Helper component: Quick vital display (ER view)
 */
const QuickVital = ({ label, value, unit }) => {
  return (
    <div className="bg-gray-100 rounded-lg p-4 text-center">
      <p className="text-gray-600 text-sm font-semibold">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-2">{value} {unit}</p>
    </div>
  );
};

export default { ParamedicDashboard, ERDashboard };
