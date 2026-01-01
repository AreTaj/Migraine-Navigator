import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate } from "react-router-dom";
import { LayoutDashboard, PlusCircle, History, Pill, Settings, Zap } from "lucide-react";
import "./App.css";

import Dashboard from "./pages/Dashboard";
import LogEntry from "./pages/LogEntry";
import HistoryPage from "./pages/History";
import Medications from "./pages/Medications";
import Triggers from "./pages/Triggers";
import SettingsPage from "./pages/Settings";
import ImportData from "./pages/ImportData";
import Onboarding from "./pages/Onboarding";

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

function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();
  const isOnboarding = location.pathname === "/onboarding";

  useEffect(() => {
    const done = localStorage.getItem("onboarding_completed");
    if (!done && !isOnboarding) {
      navigate("/onboarding");
    }
  }, [isOnboarding, navigate]);

  return (
    <div className="app-container">
      {!isOnboarding && (
        <aside className="sidebar">
          <div className="logo-area">
            <h1>Migraine Navigator</h1>
          </div>
          <nav>
            <NavItem to="/" icon={LayoutDashboard} label="Dashboard" />
            <NavItem to="/log" icon={PlusCircle} label="Log Entry" />
            <NavItem to="/medications" icon={Pill} label="Medications" />
            <NavItem to="/triggers" icon={Zap} label="Triggers" />
            <NavItem to="/history" icon={History} label="History" />
            <NavItem to="/settings" icon={Settings} label="Settings" />
          </nav>
        </aside>
      )}
      <main className="content" style={isOnboarding ? { padding: 0, width: "100%", maxWidth: "100%" } : {}}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/log" element={<LogEntry />} />
          <Route path="/medications" element={<Medications />} />
          <Route path="/triggers" element={<Triggers />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/import" element={<ImportData />} />
          <Route path="/onboarding" element={<Onboarding />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
