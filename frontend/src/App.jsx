import { useMemo, useState } from 'react';
import AmbulanceView from './AmbulanceView.jsx';
import ERDashboard from './ERDashboard.jsx';

export default function App() {
  const [view, setView] = useState('ambulance');

  const isAmbulance = view === 'ambulance';
  const title = useMemo(
    () => (isAmbulance ? 'Paramedic View' : 'ER Doctor View'),
    [isAmbulance],
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div>
            <div className="text-xs font-semibold tracking-wider text-slate-400">VIGILCARE AI</div>
            <div className="text-sm font-semibold text-slate-100">{title}</div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setView('ambulance')}
              className={
                "rounded-lg px-3 py-1.5 text-xs font-semibold ring-1 transition " +
                (isAmbulance
                  ? 'bg-slate-100/10 text-slate-100 ring-slate-100/20'
                  : 'bg-transparent text-slate-300 ring-slate-700 hover:bg-slate-100/5')
              }
            >
              Paramedic
            </button>
            <button
              type="button"
              onClick={() => setView('er')}
              className={
                "rounded-lg px-3 py-1.5 text-xs font-semibold ring-1 transition " +
                (!isAmbulance
                  ? 'bg-slate-100/10 text-slate-100 ring-slate-100/20'
                  : 'bg-transparent text-slate-300 ring-slate-700 hover:bg-slate-100/5')
              }
            >
              ER Dashboard
            </button>
          </div>
        </div>
      </div>

      {isAmbulance ? <AmbulanceView embedded /> : <ERDashboard embedded />}
    </div>
  );
}
