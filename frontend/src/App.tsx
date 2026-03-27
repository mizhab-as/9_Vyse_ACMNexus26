import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import HospitalDashboard from './HospitalDashboard';
import AmbulanceDashboard from './AmbulanceDashboard';

function Navigation() {
  const location = useLocation();
  const isAmbulance = location.pathname === '/ambulance';

  return (
    <nav className="p-4 bg-gray-900 text-white flex justify-between items-center shadow-lg">
      <div className="text-xl font-bold tracking-widest text-blue-400">VigilCare Nexus</div>
      <div className="space-x-4 flex">
        <Link
            to="/ambulance"
            className={`px-4 py-2 rounded-lg font-semibold transition-all ${isAmbulance ? 'bg-blue-600 text-white shadow-inner' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>
            [+] Ambulance Control
        </Link>
        <Link
            to="/"
            className={`px-4 py-2 rounded-lg font-semibold transition-all ${!isAmbulance ? 'bg-red-600 text-white shadow-inner' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>
            [H] ER / Hospital View
        </Link>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Navigation />
      <Routes>
        <Route path="/" element={<HospitalDashboard />} />
        <Route path="/ambulance" element={<AmbulanceDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
