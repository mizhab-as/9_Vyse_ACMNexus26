import { useMemo, useRef, useState, useEffect } from 'react';
import type { RankedHospital } from './hospitals';

export default function AmbulanceDashboard() {
  const [bloodGroup, setBloodGroup] = useState('O-');
  const [ecgStatus, setEcgStatus] = useState('Normal Sinus Rhythm (80 bpm)');
  const [eta, setEta] = useState('Waiting for GPS…');
  const [statusText, setStatusText] = useState('Live Sync Active');
  const [liveData, setLiveData] = useState<any>({});
  const [currentLoc, setCurrentLoc] = useState<{lat: number, lon: number} | null>(null);

  const [suggested, setSuggested] = useState<RankedHospital | null>(null);
  const [alternate, setAlternate] = useState<RankedHospital | null>(null);
  const [suggestionNote, setSuggestionNote] = useState<string>('Searching nearby hospitals…');

  const lastRouteCalcAtRef = useRef<number>(0);

  const suggestedDisplay = useMemo(() => {
    if (!suggested) return 'No suggested hospital yet';
    const addr = suggested.address ? ` • ${suggested.address}` : '';
    return `${suggested.name}${addr} • ${suggested.etaMinutes} mins (${suggested.distanceKm} km)`;
  }, [suggested]);

  const alternateDisplay = useMemo(() => {
    if (!alternate) return 'No alternate hospital yet';
    const addr = alternate.address ? ` • ${alternate.address}` : '';
    return `${alternate.name}${addr} • ${alternate.etaMinutes} mins (${alternate.distanceKm} km)`;
  }, [alternate]);

  // Live location tracking -> find nearby hospitals -> rank by ETA
  useEffect(() => {
    let watchId: number;

    const recalc = async (lat: number, lon: number) => {
      const now = Date.now();
      if (now - lastRouteCalcAtRef.current < 15000) return; // throttle
      lastRouteCalcAtRef.current = now;

      try {
        setSuggestionNote('Fetching hospital suggestions…');

        const res = await fetch(
          `http://localhost:8002/api/route_suggestions?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`
        );
        if (!res.ok) throw new Error(`route_suggestions ${res.status}`);
        const data = (await res.json()) as {
          suggested: RankedHospital | null;
          alternate: RankedHospital | null;
          note?: string;
        };

        const best = data.suggested ?? null;
        const second = data.alternate ?? null;

        setSuggested(best);
        setAlternate(second);

        if (best) {
          setEta(`${best.etaMinutes} mins (${best.distanceKm} km) → ${best.name}`);
          setSuggestionNote(
            second
              ? `Suggested: ${best.name}. Alternate: ${second.name}.`
              : data.note || `Suggested: ${best.name}. (No alternate hospital found nearby.)`
          );
        } else {
          setEta('Unable to compute ETA');
          setSuggestionNote(data.note || 'No suggestion available.');
        }
      } catch (e) {
        // Fallback: keep old fixed-hospital behavior if routing lookup fails.
        const destLat = 9.9326;
        const destLon = 76.4764;
        try {
          const res = await fetch(
            `https://router.project-osrm.org/route/v1/driving/${lon},${lat};${destLon},${destLat}?overview=false`
          );
          const data = await res.json();
          if (data.routes && data.routes.length > 0) {
            const route = data.routes[0];
            const durationMin = Math.ceil((route.duration * 1.15) / 60);
            const distKm = (route.distance / 1000).toFixed(1);
            setEta(`${durationMin} mins (${distKm} km in Traffic) → Kolencherry Medical Hospital`);
          } else {
            setEta('Unable to route (Check Location)');
          }
        } catch {
          setEta('10 mins (Kolencherry Medical Hospital: 7.7 km via fallback)');
        }

        setSuggested(null);
        setAlternate(null);
        setSuggestionNote('Hospital suggestions failed; using fallback destination.');
      }
    };

    if (navigator.geolocation) {
        watchId = navigator.geolocation.watchPosition(async (pos) => {
            const lat = pos.coords.latitude;
            const lon = pos.coords.longitude;
            setCurrentLoc({lat, lon});
            await recalc(lat, lon);
        }, () => {
            setEta(`Please Allow Location for Live ETA!`);
            setSuggestionNote('Location permission is required for nearby hospital routing.');
        }, { enableHighAccuracy: true });
    }
    return () => { if (watchId) navigator.geolocation.clearWatch(watchId); };
  }, []);

  const openGoogleMapsTo = (h: RankedHospital | null) => {
    if (!h) return;

    const params = new URLSearchParams({
      api: '1',
      destination: `${h.lat},${h.lon}`,
      travelmode: 'driving',
    });
    if (currentLoc) params.set('origin', `${currentLoc.lat},${currentLoc.lon}`);

    const url = `https://www.google.com/maps/dir/?${params.toString()}`;

    // Popups can be blocked; fall back to same-tab navigation.
    const win = window.open(url, '_blank', 'noopener,noreferrer');
    if (!win) window.location.assign(url);
  };

  // Connect to Websocket to show truly live detected data
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8002/ws');
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
        await fetch('http://localhost:8002/api/patient_context', {    
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            blood_group: bloodGroup,
            ecg_status: ecgStatus,
            eta: eta,
            temperature: String(liveData.temperature ?? "98.6"),
            oxygen: String(liveData.oxygen ?? "98"),
            lat: currentLoc ? currentLoc.lat.toString() : "",
            lon: currentLoc ? currentLoc.lon.toString() : "",
            destination_name: suggested?.name ?? "",
            destination_lat: suggested ? String(suggested.lat) : "",
            destination_lon: suggested ? String(suggested.lon) : "",
            alternative_name: alternate?.name ?? "",
            alternative_lat: alternate ? String(alternate.lat) : "",
            alternative_lon: alternate ? String(alternate.lon) : "",
          })
        });
        setStatusText("🔄 Synced to ER");
      } catch (e) {
        setStatusText("❌ Sync Failed");
      }
    };
    
    const timeout = setTimeout(sendUpdate, 500);
    return () => clearTimeout(timeout);
  }, [
    bloodGroup,
    ecgStatus,
    eta,
    liveData.temperature,
    liveData.oxygen,
    currentLoc?.lat,
    currentLoc?.lon,
    suggested?.name,
    suggested?.lat,
    suggested?.lon,
    alternate?.name,
    alternate?.lat,
    alternate?.lon,
  ]);

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
              <label className="block text-sm font-bold text-gray-400 uppercase tracking-wider mb-2">Nearby Hospital Routing (ETA-based)</label>
              <div className="w-full bg-gray-800 border border-gray-700 rounded-xl p-4 shadow-inner space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start space-x-3 min-w-0">
                    <span className="animate-pulse h-3 w-3 bg-green-500 rounded-full inline-block mt-2"></span>
                    <div className="min-w-0">
                      <div className="text-green-400 font-bold truncate">Suggested: {suggestedDisplay}</div>
                      <div className="text-purple-200 font-bold truncate mt-1">Alternate: {alternateDisplay}</div>
                      <div className="text-xs text-gray-400 mt-1">{suggestionNote}</div>
                      <div className="text-xs text-gray-500 mt-1">Current ETA: <span className="text-gray-300 font-bold">{eta}</span></div>
                    </div>
                  </div>

                  <div className="flex gap-2 shrink-0">
                    <button
                      onClick={() => openGoogleMapsTo(suggested)}
                      disabled={!suggested}
                      className="bg-blue-600 disabled:opacity-40 hover:bg-blue-500 text-white px-3 py-2 rounded-lg text-sm font-bold transition-all"
                    >
                      Route (Suggested)
                    </button>
                    <button
                      onClick={() => openGoogleMapsTo(alternate)}
                      disabled={!alternate}
                      className="bg-slate-700 disabled:opacity-40 hover:bg-slate-600 text-white px-3 py-2 rounded-lg text-sm font-bold transition-all"
                    >
                      Route (Alt)
                    </button>
                  </div>
                </div>
                <div className="text-xs text-gray-500 font-bold uppercase">Traffic is approximated (OSRM ETA + small buffer)</div>
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
