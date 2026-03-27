import { useEffect, useState } from 'react';

export default function HospitalDashboard() {
  const [data, setData] = useState<any[]>([]);
  const [alertText, setAlertText] = useState<string | null>(null);
  const [isAcknowledged, setIsAcknowledged] = useState<boolean>(false);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8002/ws');

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        setData(prev => {
          const newData = [...prev, parsed];
          if (newData.length > 50) newData.shift();
          return newData;
        });
        if (parsed.triage_alert) {
            if (alertText !== parsed.triage_alert) {
                setIsAcknowledged(false); // Reset acknowledgement on new alert
            }
            setAlertText(parsed.triage_alert);
        } else {
            setAlertText(null);
            setIsAcknowledged(false);
        }
      } catch (e) {
        console.error("Invalid JSON from WS", e);
      }
    };
    return () => ws.close();
  }, [alertText]);

  const latest = data[data.length - 1];

  if (!latest) return <div className="p-12 text-center text-gray-500 font-bold text-xl animate-pulse">Waiting for Ambulance Connection...</div>;

  const spo2 = parseFloat(latest.oxygen) || 100;
  const sysBP = latest.blood_pressure ? parseInt(latest.blood_pressure.split('/')[0]) : 120;
  
  const isDangerousO2 = spo2 < 85;
  const isSeriousO2 = spo2 >= 85 && spo2 < 92;
  const isHeartAttackRisk = latest.heart_attack_prediction === 'YES';
  const isHighBP = sysBP >= 140;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-10">
      <header className="p-6 bg-slate-900 shadow-2xl flex justify-between items-center border-b-[6px] border-red-600">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Kolencherry Medical Hospital - ER Live Monitor</h1>
          <p className="text-sm font-semibold text-sky-400 uppercase tracking-widest mt-1">Live Ambulance Feed (#Unit-42)</p>
          <p className="text-xs font-bold text-slate-400 mt-2 uppercase tracking-widest">
            Destination (Suggested): {latest.destination_name || '—'}
          </p>
        </div>
        <div className="flex space-x-4">
            <div className="px-6 py-3 rounded-xl font-bold uppercase tracking-widest bg-slate-800 text-sky-300 border border-slate-700 shadow-inner text-sm flex items-center">
                <span className="w-2 h-2 rounded-full bg-sky-400 mr-3 animate-pulse"></span>
                ETA: {latest.eta || 'Calculating...'}
            </div>
            <div className={`px-6 py-3 rounded-xl font-bold uppercase tracking-widest shadow-inner text-sm flex items-center ${
                isHeartAttackRisk ? 'bg-red-500 text-white animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.7)]' :
                isDangerousO2 ? 'bg-purple-600 text-white animate-pulse shadow-[0_0_15px_rgba(147,51,234,0.7)]' :
                isHighBP ? 'bg-orange-500 text-white animate-pulse shadow-[0_0_15px_rgba(249,115,22,0.7)]' :
                isSeriousO2 ? 'bg-yellow-500 text-white animate-pulse shadow-[0_0_15px_rgba(234,179,8,0.7)]' :
                'bg-green-500 text-white'
            }`}>
                {isHeartAttackRisk ? 'HEART ATTACK RISK DETECTED' : isDangerousO2 ? 'BLOOD NEEDED (DANGEROUS O2)' : isHighBP ? 'HYPERTENSION ALERT (BP SPIKE)' : isSeriousO2 ? 'SERIOUS O2 LEVEL' : 'PATIENT STABLE'}
            </div>
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        {alertText && (
            <div className={`p-6 border-l-8 rounded shadow-xl flex justify-between items-center transition-all ${isAcknowledged ? 'bg-slate-800 border-slate-600 opacity-60' : isHeartAttackRisk ? 'bg-red-100 border-red-600 animate-pulse' : isDangerousO2 ? 'bg-purple-100 border-purple-600 animate-pulse' : isHighBP ? 'bg-orange-100 border-orange-600 animate-pulse' : isSeriousO2 ? 'bg-yellow-100 border-yellow-600 animate-pulse' : 'bg-blue-100 border-blue-600'}`}>
                <div>
                    <h3 className={`text-2xl font-black mb-2 tracking-tight ${isAcknowledged ? 'text-slate-400' : isHeartAttackRisk ? 'text-red-900' : isDangerousO2 ? 'text-purple-900' : isHighBP ? 'text-orange-900' : isSeriousO2 ? 'text-yellow-900' : 'text-blue-900'}`}>
                        {isAcknowledged ? 'ALERT ACKNOWLEDGED & TEAM DISPATCHED' : isHeartAttackRisk ? 'VIGILCARE PREDICTIVE ALERT (CARDIAC EMERGENCY)' : isDangerousO2 ? 'URGENT: DANGEROUS CONDITION' : isHighBP ? 'HYPERTENSIVE CRISIS' : isSeriousO2 ? 'SERIOUS CONDITION' : 'GENERAL ALERT'}
                    </h3>
                    <p className={`whitespace-pre-wrap font-semibold font-mono text-lg leading-relaxed ${isAcknowledged ? 'text-slate-500 line-through' : isHeartAttackRisk ? 'text-red-800' : isDangerousO2 ? 'text-purple-800' : isHighBP ? 'text-orange-800' : isSeriousO2 ? 'text-yellow-800' : 'text-blue-800'}`}>
                        {alertText}
                    </p>
                </div>
                {!isAcknowledged && (
                    <button 
                         onClick={() => setIsAcknowledged(true)}
                         className={`px-8 py-4 rounded-xl font-black text-xl uppercase tracking-widest text-white shadow-2xl transition-transform hover:scale-105 active:scale-95 ${isHeartAttackRisk ? 'bg-red-600 hover:bg-red-500' : isDangerousO2 ? 'bg-purple-600 hover:bg-purple-500' : isHighBP ? 'bg-orange-600 hover:bg-orange-500' : isSeriousO2 ? 'bg-yellow-600 hover:bg-yellow-500' : 'bg-blue-600 hover:bg-blue-500'}`}
                    >
                        Acknowledge & Prepare
                    </button>
                )}
            </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
            <div className={`bg-slate-900 p-5 rounded-xl shadow-2xl border-l-[6px] ${isDangerousO2 ? 'border-purple-500 animate-pulse' : 'border-sky-500'} ring-1 ring-slate-800`}>
                <p className={`text-xs font-bold uppercase tracking-wider mb-2 ${isDangerousO2 ? 'text-purple-400' : 'text-sky-400'}`}>Blood Group</p>
                <div className="flex items-center space-x-3">
                  <p className="text-3xl font-black text-white">{latest.blood_group || 'Unknown'}</p>
                </div>
            </div>
            <div className="bg-slate-900 p-5 rounded-xl shadow-2xl border-l-[6px] border-emerald-500 ring-1 ring-slate-800">
                <p className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">Temperature</p>
                <div className="flex items-start space-x-3">
                  <p className="text-3xl font-black text-white">{latest.temperature || '--'} <span className="text-sm font-bold text-slate-500">°F</span></p>
                </div>
            </div>
            <div className={`bg-slate-900 p-5 rounded-xl shadow-2xl border-l-[6px] ${isHeartAttackRisk ? 'border-red-500 animate-pulse' : 'border-rose-400'} ring-1 ring-slate-800`}>
                <p className={`text-xs font-bold uppercase tracking-wider mb-1 ${isHeartAttackRisk ? 'text-red-500' : 'text-rose-400'}`}>Live Heart Rate</p>
                <span className="text-[10px] font-bold text-slate-400 block mb-2 uppercase tracking-wide truncate">{latest.ecg_status}</span>
                <div className="flex items-start space-x-3">
                  <p className="text-4xl font-black text-rose-500 animate-pulse">{latest.heart_rate || '--'} <span className="text-sm font-bold text-slate-500">BPM</span></p>
                </div>
            </div>
            <div className={`bg-slate-900 p-5 rounded-xl shadow-2xl border-l-[6px] ${isDangerousO2 ? 'border-purple-500' : isSeriousO2 ? 'border-yellow-500' : 'border-teal-400'} ring-1 ring-slate-800`}>
                <p className={`text-xs font-bold uppercase tracking-wider mb-2 ${isDangerousO2 ? 'text-purple-400' : isSeriousO2 ? 'text-yellow-400' : 'text-teal-400'}`}>Oxygen (SpO2)</p>
                <div className="flex items-start space-x-3">
                  <p className="text-3xl font-black text-white">{latest.oxygen || '--'} <span className="text-sm font-bold text-slate-500">%</span></p>
                </div>
            </div>
             <div className={`bg-slate-900 p-5 rounded-xl shadow-2xl border-l-[6px] ${isHighBP ? 'border-orange-500 animate-pulse' : 'border-indigo-500'} ring-1 ring-slate-800`}>
                <p className={`text-xs font-bold uppercase tracking-wider mb-2 ${isHighBP ? 'text-orange-400' : 'text-indigo-400'}`}>Blood Pressure</p>
                <div className="flex items-start space-x-3">
                  <p className={`text-3xl font-black ${isHighBP ? 'text-orange-400' : 'text-white'}`}>
                     {latest.blood_pressure || '--/--'} 
                     <span className="text-sm text-slate-500 font-bold ml-1">mmHg</span>
                  </p>
                </div>
                {isHighBP && <span className="text-[10px] font-bold text-orange-400 uppercase tracking-widest mt-2 block">Triggered by Hypoxia</span>}
            </div>
        </div>

        <div className="bg-slate-800 p-8 shadow-2xl rounded-xl mt-6 border border-slate-700 flex flex-col md:flex-row items-center gap-6 justify-between">
             <div className="flex-1 w-full text-center md:text-left">
                 <h3 className="text-lg font-bold text-gray-400 uppercase tracking-widest mb-4">AI Predictive Analysis (ECG + SpO2)</h3>
                 <div className={`w-full py-8 px-6 flex flex-col justify-center rounded-2xl bg-slate-900 border-4 transition-all duration-300 ${latest.heart_attack_prediction === 'YES' ? 'border-red-600 shadow-[0_0_50px_rgba(239,68,68,0.5)]' : 'border-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.15)]'}`}>
                      <p className={`text-5xl md:text-6xl font-black tracking-tight mb-2 ${latest.heart_attack_prediction === 'YES' ? 'text-red-500 animate-pulse drop-shadow-[0_0_15px_rgba(239,68,68,0.8)]' : 'text-emerald-500'}`}>
                          {latest.heart_attack_prediction === 'YES' ? 'HEART ATTACK DETECTED' : 'NO HEART ATTACK RISK'}
                      </p>
                      
                      <div className={`mt-6 p-4 rounded-xl border-2 shadow-inner ${isDangerousO2 || isSeriousO2 ? 'bg-purple-900/30 border-purple-600/50' : 'bg-teal-900/30 border-teal-500/50'}`}>
                          <p className={`text-lg md:text-2xl font-black uppercase tracking-widest ${isDangerousO2 || isSeriousO2 ? 'text-purple-400 animate-pulse' : 'text-teal-400'}`}>
                              AI OXYGEN PREDICTION: {(isDangerousO2 || isSeriousO2) ? 'PATIENT IS CRITICAL' : 'PATIENT STABLE'}
                          </p>
                      </div>
                 </div>
             </div>
             <div className="flex-1 w-full md:w-1/3 bg-slate-900 border border-slate-700 p-6 rounded-2xl shadow-inner text-center">
                  <h3 className="text-sm font-bold text-sky-400 uppercase tracking-widest mb-3">Live ETA Tracker</h3>
                  <div className="text-3xl font-black text-white flex items-center justify-center space-x-3">
                      <span className="w-4 h-4 rounded-full bg-blue-500 animate-pulse"></span>
                      <span>{latest.eta || 'Calculating...'}</span>
                  </div>
                 <p className="text-xs text-slate-500 font-bold mt-4 uppercase">Destination: {latest.destination_name || '—'}</p>
             </div>
        </div>
      </main>
    </div>
  );
}
