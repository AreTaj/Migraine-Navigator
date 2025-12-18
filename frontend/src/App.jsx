import { BrowserRouter as Router, Routes, Route, Link, useLocation } from "react-router-dom";
import { LayoutDashboard, PlusCircle, History, Pill } from "lucide-react";
import "./App.css";

import Dashboard from "./pages/Dashboard";
import LogEntry from "./pages/LogEntry";
import HistoryPage from "./pages/History";
import Medications from "./pages/Medications";

function NavItem({ to, icon: Icon, label }) {
  const location = useLocation();
  const isActive = location.pathname === to;
  return (
    <Link to={to} className={`nav-item ${isActive ? "active" : ""}`}>
      <Icon size={20} />
      <span>{label}</span>
    </Link>
  );
}

function App() {
  return (
    <Router>
      <div className="app-container">
        <aside className="sidebar">
          <div className="logo-area">
            <h1>Migraine Navigator</h1>
          </div>
          <nav>
            <NavItem to="/" icon={LayoutDashboard} label="Dashboard" />
            <NavItem to="/log" icon={PlusCircle} label="Log Entry" />
            <NavItem to="/medications" icon={Pill} label="Medications" />
            <NavItem to="/history" icon={History} label="History" />
          </nav>
        </aside>
        <main className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/log" element={<LogEntry />} />
            <Route path="/medications" element={<Medications />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
