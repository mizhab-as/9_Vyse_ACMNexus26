import { useState, useEffect } from 'react';

export default function AmbulanceDashboard() {
  const [bloodGroup, setBloodGroup] = useState('O-');
  const [ecgStatus, setEcgStatus] = useState('Normal Sinus Rhythm (80 bpm)');
  const [eta, setEta] = useState('Calculating live driving route via OSRM...');
  const [statusText, setStatusText] = useState('Live Sync Active');
  const [liveData, setLiveData] = useState<any>({});
  const [currentLoc, setCurrentLoc] = useState<{lat: number, lon: number} | null>(null);

  // Simulated live location tracking & real open-source routing API!
  useEffect(() => {
    let watchId: number;
    if (navigator.geolocation) {
        watchId = navigator.geolocation.watchPosition(async (pos) => {
            const lat = pos.coords.latitude;
            const lon = pos.coords.longitude;
            setCurrentLoc({lat, lon});
            // Kolencherry medical hospital specific coords
            const destLat = 9.9326;
            const destLon = 76.4764;
            
            try {
                // Public open-source routing API (OSRM) driving route
                const res = await fetch(`https://router.project-osrm.org/route/v1/driving/${lon},${lat};${destLon},${destLat}?overview=false`);
                const data = await res.json();
                
                if (data.routes && data.routes.length > 0) {
                     const route = data.routes[0];
                     // Convert seconds to minutes and add 15% arbitrary buffer for "traffic" simulation on top of baseline
                     const durationMin = Math.ceil((route.duration * 1.15) / 60);
                     const distKm = (route.distance / 1000).toFixed(1);
                     setEta(`${durationMin} mins (${distKm} km in Traffic)`);
                } else {
                     setEta(`Unable to route to Kolencherry (Check Location)`);
                }
            } catch (e) {
                setEta(`10 mins (Kolencherry Medical Hospital: 7.7 km via fallback)`);
            }
        }, (err) => {
            setEta(`Please Allow Location for Live ETA!`);
        }, { enableHighAccuracy: true });
    }
    return () => { if (watchId) navigator.geolocation.clearWatch(watchId); };
  }, []);

  const openGoogleMaps = () => {
      // Opens live navigation using Google Maps
      if (currentLoc) {
          window.open(`https://www.google.com/maps/dir/?api=1&origin=${currentLoc.lat},${currentLoc.lon}&destination=Kolencherry+Medical+Hospital&travelmode=driving`, '_blank');
      } else {
          window.open(`https://www.google.com/maps/dir/?api=1&destination=Kolencherry+Medical+Hospital&travelmode=driving`, '_blank');
      }
  };

  // Connect to Websocket to show truly live detected data
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onmessage = (event) => {
      try {
        setLiveData(JSON.parse(event.data));
      } catch (e) {}
    };
    return () => ws.close();
  }, []);

  // Auto-sync vitals on any change making it truly live & interactive
  useEffect(() => {
    const sendUpdate = async () => {
      try {
        await fetch('http://localhost:8000/api/patient_context', {    
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            blood_group: bloodGroup,
            ecg_status: ecgStatus,
            eta: eta,
            temperature: liveData.temperature || "98.6",
            oxygen: liveData.oxygen || "98",
            lat: currentLoc ? currentLoc.lat.toString() : "",
            lon: currentLoc ? currentLoc.lon.toString() : ""
          })
        });
        setStatusText("🔄 Synced to ER");
      } catch (e) {
        setStatusText("❌ Sync Failed");
      }
    };
    
    const timeout = setTimeout(sendUpdate, 500);
    return () => clearTimeout(timeout);
  }, [bloodGroup, ecgStatus, eta]);

  return (
    <div className="min-h-screen bg-gray-950 text-white pb-10">
      <header className="p-6 bg-gray-900 shadow-xl border-b border-gray-800 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-blue-500">Paramedic Control Panel</h1>
          <p className="text-sm font-medium text-gray-400 mt-1">Provide Live Updates to the Hospital</p>
        </div>
      </header>

      <main className="p-6 max-w-3xl mx-auto mt-6">
        <div className="bg-gray-900 p-8 rounded-2xl shadow-xl space-y-6 border border-gray-800">

            <div>
                <label className="block text-sm font-bold text-gray-400 uppercase tracking-wider mb-2">Live GPS Route calculation</label>
                <div className="w-full bg-gray-800 border border-gray-700 rounded-xl p-4 text-green-400 font-bold flex items-center justify-between shadow-inner">
                    <div className="flex items-center space-x-3">
                        <span className="animate-pulse h-3 w-3 bg-green-500 rounded-full inline-block"></span>
                        <span>{eta}</span>
                    </div>
                    <button 
                        onClick={openGoogleMaps}
                        className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all shadow-[0_0_10px_rgba(37,99,235,0.5)] flex items-center space-x-2"
                    >
                        <span>Open Google Maps</span>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                    </button>
                </div>
            </div>

            <div>
                <label className="block text-sm font-bold text-gray-400 uppercase tracking-wider mb-2">Blood Type</label>
                <select
                    value={bloodGroup}
                    onChange={e => setBloodGroup(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl p-4 text-white font-bold focus:ring-2 focus:ring-red-500 outline-none"     
                >
                    <option value="Unknown">Select Blood Group</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                </select>
            </div>
            
            <div>
                <label className="block text-sm font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                    Live ECG Status (Derives Heart Rate)
                </label>
                <select
                    value={ecgStatus}
                    onChange={e => setEcgStatus(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl p-4 text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none"     
                >
                    <option value="Normal Sinus Rhythm (80 bpm)">Normal Sinus Rhythm (80 bpm) - Stable</option>
                    <option value="Ventricular Tachycardia (145 bpm)">Ventricular Tachycardia (145 bpm) - Risk of Heart Attack</option>
                    <option value="Bradycardia (45 bpm)">Bradycardia (45 bpm) - Risk of Heart Attack</option>
                    <option value="Ischemia (110 bpm)">Ischemia (110 bpm) - Elevated</option>
                    <option value="Dynamic Auto-Simulation (AI Controlled)">Dynamic Auto-Simulation (AI Evolves Patient Crash organically)</option>
                </select>
            </div>

            <div className="grid grid-cols-2 gap-6">
                <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 shadow-inner">
                    <label className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center">
                       <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
                       Live Temp Sensor
                    </label>
                    <p className="text-4xl font-black text-emerald-400 mt-2">
                        {liveData.temperature || '--'} <span className="text-lg font-bold text-gray-500">°F</span>
                    </p>
                </div>
                <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 shadow-inner">
                    <label className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center">
                       <span className="w-2 h-2 rounded-full bg-teal-500 mr-2 animate-pulse"></span>
                       Live SpO2 Sensor
                    </label>
                    <p className="text-4xl font-black text-teal-400 mt-2">
                        {liveData.oxygen || '--'} <span className="text-lg font-bold text-gray-500">%</span>
                    </p>
                </div>
            </div>

            <div className="pt-4 border-t border-gray-800 flex items-center justify-between">
                <p className="text-sm font-bold text-green-400 animate-pulse">{statusText}</p>
                <div className="space-x-2 flex">
                    <button 
                         onClick={() => setEcgStatus('Dynamic Auto-Simulation (AI Controlled)')}
                         className="px-3 py-1 bg-purple-900 hover:bg-purple-700 text-purple-100 rounded text-xs font-bold transition-colors border border-purple-800"
                    >
                        Random AI Scenario
                    </button>
                    <button 
                         onClick={() => setEcgStatus('Ventricular Tachycardia (145 bpm)')}
                         className="px-3 py-1 bg-red-900 hover:bg-red-700 text-red-100 rounded text-xs font-bold transition-colors border border-red-800"
                    >
                        Heart Emergency
                    </button>
                    <button 
                         onClick={() => setEcgStatus('Normal Sinus Rhythm (80 bpm)')}
                         className="px-3 py-1 bg-teal-900 hover:bg-teal-700 text-teal-100 rounded text-xs font-bold transition-colors border border-teal-800"
                    >
                        Normals
                    </button>
                </div>
            </div>
        </div>
      </main>
    </div>
  );
}
