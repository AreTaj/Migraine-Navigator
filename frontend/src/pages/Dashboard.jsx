import { useState, useEffect, useMemo } from 'react';
import axios from '../services/apiClient';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Label, LineChart, Line } from 'recharts';


import { useNavigate } from 'react-router-dom';
import { Loader2, Pill, CalendarCheck, CheckCircle2, Clock, XCircle, AlertTriangle } from 'lucide-react';
import './Dashboard.css';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#aaa'];

// Helper to parse YYYY-MM-DD as local date (avoiding UTC offset issues)
const parseLocalDate = (dateStr) => {
    if (!dateStr) return new Date();
    const parts = dateStr.split('-');
    if (parts.length === 3) {
        return new Date(parts[0], parts[1] - 1, parts[2]);
    }
    return new Date(dateStr);
};

function Dashboard() {
    const [entries, setEntries] = useState([]);
    const [prediction, setPrediction] = useState(null);
    const [loading, setLoading] = useState(true);
    const [predLoading, setPredLoading] = useState(true); // New state for lazy load
    const [forecast, setForecast] = useState([]); // 7-day forecast
    const [error, setError] = useState(null);
    const [timeRange, setTimeRange] = useState('1y'); // '1m', '1y', '2y'

    const navigate = useNavigate();
    const [meds, setMeds] = useState([]);

    // --- Smart Dashboard State ---
    const [todayStatus, setTodayStatus] = useState('unknown'); // 'unknown', 'logged', 'missing'
    const [missingDays, setMissingDays] = useState([]);
    const [dailyMeds, setDailyMeds] = useState([]);
    const [dueMeds, setDueMeds] = useState([]);
    const [showRetroCard, setShowRetroCard] = useState(true);
    const [retroConfirming, setRetroConfirming] = useState(false);
    const [retroData, setRetroData] = useState({}); // Map of date -> {sleep, activity}

    // Check-in Form State
    const [checkinStep, setCheckinStep] = useState('initial'); // 'initial', 'details'
    const [checkinData, setCheckinData] = useState({
        sleep: '3', // Default Good
        activity: '2', // Default Moderate
        notes: ''
    });

    useEffect(() => {

        const fetchCoreData = async () => {
            try {
                // 1. Critical Data (Fast) - Loads immediately
                const [entriesRes, medsRes] = await Promise.all([
                    axios.get('/api/v1/entries'),
                    axios.get('/api/v1/medications')
                ]);

                const entriesData = entriesRes.data;
                setEntries(entriesData);
                const allMeds = medsRes.data;
                setMeds(allMeds);

                // --- SMART LOGIC (Synchronous) ---
                const now = new Date();
                const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
                const dailyMedList = allMeds.filter(m => m.frequency === 'daily');
                setDailyMeds(dailyMedList);

                // 1. Check Today
                const hasEntryToday = entriesData.some(e => e.Date === todayStr);
                setTodayStatus(hasEntryToday ? 'logged' : 'missing');

                // 2. Check Retroactive Gap (Last 7 days)
                if (entriesData.length > 0) {
                    const sorted = [...entriesData].sort((a, b) => new Date(b.Date) - new Date(a.Date));
                    const lastDateStr = sorted[0].Date;

                    const missing = [];
                    let curr = new Date();
                    curr.setDate(curr.getDate() - 1);
                    const lastDate = new Date(lastDateStr);

                    while (curr > lastDate && missing.length < 5) {
                        const dStr = curr.toISOString().split('T')[0];
                        if (!entriesData.some(e => e.Date === dStr)) {
                            missing.push(dStr);
                        }
                        curr.setDate(curr.getDate() - 1);
                    }
                    setMissingDays(missing.reverse());
                }

                // 3. Periodic Reminders
                const periodicMeds = allMeds.filter(m => m.frequency === 'periodic' && m.period_days);
                const dueList = [];
                periodicMeds.forEach(med => {
                    const entriesWithMed = entriesData.filter(e =>
                        e.Medications && e.Medications.some(m => m.name === med.name)
                        || (e.Medication && e.Medication.includes(med.name))
                    );

                    if (entriesWithMed.length > 0) {
                        entriesWithMed.sort((a, b) => new Date(b.Date) - new Date(a.Date));
                        const lastUsage = new Date(entriesWithMed[0].Date);
                        const nextDue = new Date(lastUsage);
                        nextDue.setDate(nextDue.getDate() + Number(med.period_days));

                        const warningWindow = new Date();
                        warningWindow.setDate(warningWindow.getDate() + 7);
                        if (nextDue <= warningWindow) {
                            const diffTime = nextDue - new Date();
                            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                            dueList.push({ ...med, dueDays: diffDays, nextDate: nextDue.toDateString() });
                        }
                    }
                });
                setDueMeds(dueList);
                setLoading(false); // Critical UI Ready

            } catch (err) {
                console.error("Error fetching dashboard data:", err);
                setError(`Failed to load dashboard data: ${err.message}`);
                setLoading(false);
            }
        };

        const fetchPredictions = async () => {
            // 2. Lazy Load Prediction (Slow)
            setPredLoading(true);
            try {
                // Run in parallel
                const [predRes, forecastRes] = await Promise.allSettled([
                    axios.get('/api/v1/prediction/future'),
                    axios.get('/api/v1/prediction/forecast')
                ]);

                if (predRes.status === 'fulfilled') {
                    setPrediction(predRes.value.data);
                } else {
                    console.warn("Prediction fetch failed:", predRes.reason);
                }

                if (forecastRes.status === 'fulfilled') {
                    setForecast(forecastRes.value.data);
                } else {
                    console.error("Forecast fetch failed", forecastRes.reason);
                }
            } finally {
                setPredLoading(false);
            }
        };

        // Independent executions
        fetchCoreData();
        fetchPredictions();
    }, []);

    // --- Actions ---
    // --- Actions ---
    const handleStartDailyCheckin = () => {
        setCheckinStep('details');
    };

    const handleCheckinChange = (e) => {
        const { name, value } = e.target;
        setCheckinData(prev => ({ ...prev, [name]: value }));
    };

    const handleConfirmDailyCheckin = async () => {
        try {
            // Use local date for "today"
            const now = new Date();
            const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
            const payload = {
                Date: todayStr,
                Time: "12:00",
                Pain_Level: 0,
                Medications: dailyMeds.map(m => ({ name: m.name, dosage: m.default_dosage })),
                Sleep: parseInt(checkinData.sleep),
                Physical_Activity: parseInt(checkinData.activity),
                Notes: checkinData.notes || "Auto-logged via Daily Check-in"
            };
            await axios.post('/api/v1/entries', payload);
            setTodayStatus('logged');
            alert("Logged healthy day successfully!");
            setCheckinStep('initial'); // Reset
        } catch (err) {
            alert("Failed to log. " + (err.response?.data?.detail || err.message));
        }
    };

    const handleConfirmRetroLog = async () => {
        try {
            await Promise.all(missingDays.map(dateStr => {
                const dayData = retroData[dateStr] || { sleep: '3', activity: '2' };
                return axios.post('/api/v1/entries', {
                    Date: dateStr,
                    Time: "12:00",
                    Pain_Level: 0,
                    Medications: dailyMeds.map(m => ({ name: m.name, dosage: m.default_dosage })),
                    Sleep: parseInt(dayData.sleep),
                    Physical_Activity: parseInt(dayData.activity),
                    Notes: "Retroactive Bulk Log"
                });
            }));
            setMissingDays([]); // Clear card
            setShowRetroCard(false);
            setRetroConfirming(false);
            alert("All days logged successfully!");
        } catch (err) {
            console.error("Bulk log failed", err);
            alert("Failed to bulk log.");
        }
    };

    const handleAddMissingEntries = async () => {
        setMissingEntryStatus('Locating...');

        try {
            // Attempt location fetch
            let locData = { Latitude: null, Longitude: null, Location: '' };
            try {
                const { latitude, longitude } = await getCurrentLocation();
                const city = await getCityName(latitude, longitude);
                locData = {
                    Latitude: latitude,
                    Longitude: longitude,
                    Location: city || `${latitude.toFixed(2)}, ${longitude.toFixed(2)}`
                };
            } catch (e) {
                console.warn("Retroactive location fetch failed", e);
            }

            setMissingEntryStatus('Saving...');

            const requests = missingDates.map(dateStr => {
                // Get the feedback for this specific date
                const feedback = missingEntriesData[dateStr] || { sleep: '3', activity: '2' };

                return axios.post('/api/v1/entries', {
                    Date: dateStr,
                    Time: "12:00",
                    Pain_Level: 0,
                    Sleep: feedback.sleep,
                    Physical_Activity: feedback.activity,
                    Notes: "Retroactive Bulk Log",
                    ...locData
                });
            });

            await Promise.all(requests);

            setMissingEntryStatus('Success!');
            setTimeout(() => {
                setShowMissingModal(false);
                setMissingEntryStatus('');
                // Refresh dashboard
                window.location.reload();
            }, 1000);

        } catch (err) {
            console.error(err);
            setMissingEntryStatus('Error saving entries.');
        }
    };


    // --- Aggregation Logic ---
    const stats = useMemo(() => {
        if (!entries.length) return { yearlyCount: 0, avgPain: 0, maxPain: 0, chartData: [] };

        const now = new Date();
        const currentYear = now.getFullYear();

        // 1. Avg Days/Month (Last 12 Months)
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(now.getFullYear() - 1);

        const last12MoEntries = entries.filter(e => {
            const d = new Date(e.Date);
            return d >= oneYearAgo && d <= now && Number(e.Pain_Level) > 0;
        });

        // Unique days count
        // 1. Avg Days/Month (Last 12 Months)
        // Calculate dynamic denominator based on data range
        let denominator = 12;
        if (entries.length > 0) {
            const firstEntry = new Date(Math.min(...entries.map(e => new Date(e.Date))));
            const dataSpanMonths = (now.getFullYear() - firstEntry.getFullYear()) * 12 + (now.getMonth() - firstEntry.getMonth()) + 1;
            denominator = Math.min(12, Math.max(1, dataSpanMonths));
        }

        const uniqueDays12Mo = new Set(last12MoEntries.map(e => e.Date)).size;
        const avgDaysPerMonth = (uniqueDays12Mo / denominator).toFixed(1);

        const painfulEntries = entries.filter(e => Number(e.Pain_Level) > 0);
        const maxPain = painfulEntries.reduce((max, e) => Math.max(max, Number(e.Pain_Level)), 0);
        const avgPain = painfulEntries.length
            ? (painfulEntries.reduce((sum, e) => sum + Number(e.Pain_Level), 0) / painfulEntries.length).toFixed(1)
            : 0;

        // 3. Chart Data (Dynamic based on timeRange)
        let startDate = new Date();
        if (timeRange === '1m') startDate.setMonth(now.getMonth() - 1);
        if (timeRange === '1y') startDate.setFullYear(now.getFullYear() - 1);
        if (timeRange === '2y') startDate.setFullYear(now.getFullYear() - 2);
        if (timeRange === '3y') startDate.setFullYear(now.getFullYear() - 3);
        if (timeRange === 'all') startDate = new Date(0); // Epoch

        const filteredEntries = entries.filter(e => new Date(e.Date) >= startDate);

        // ... (skipping unchanged aggregation logic)

        // (In JSX)
        <div className="range-selector">
            <button className={timeRange === '1m' ? 'active' : ''} onClick={() => setTimeRange('1m')}>1M</button>
            <button className={timeRange === '1y' ? 'active' : ''} onClick={() => setTimeRange('1y')}>1Y</button>
            <button className={timeRange === '2y' ? 'active' : ''} onClick={() => setTimeRange('2y')}>2Y</button>
            <button className={timeRange === '3y' ? 'active' : ''} onClick={() => setTimeRange('3y')}>3Y</button>
            <button className={timeRange === '5y' ? 'active' : ''} onClick={() => setTimeRange('5y')}>5Y</button>
        </div>

        // Deduplicate entries by Date (take max pain for the day)
        // This fixes the issue of >31 entries per month
        const dailyEntries = {};
        filteredEntries.forEach(e => {
            const dateStr = e.Date;
            if (!dailyEntries[dateStr]) {
                dailyEntries[dateStr] = e;
            } else {
                // If we have multiple entries, keep the one with higher pain, or just track existence
                // For counting "migraine days", just existence of >0 pain is enough?
                // But the user might want "How many entries" vs "How many days".
                // User said: "should only be the single worst counted for each day".
                if (Number(e.Pain_Level) > Number(dailyEntries[dateStr].Pain_Level)) {
                    dailyEntries[dateStr] = e;
                }
            }
        });
        const uniqueDays = Object.values(dailyEntries);

        // Filter out days with 0 pain (User said "0 is no migraine")
        // Counting Pain Level >= 1 as a "Migraine Day"
        const migraineDays = uniqueDays.filter(e => Number(e.Pain_Level) > 0);

        let chartData = [];
        if (timeRange === '1m') {
            // Daily Grouping -> Show Pain Level
            chartData = migraineDays
                .sort((a, b) => parseLocalDate(a.Date) - parseLocalDate(b.Date))
                .map(e => ({
                    name: parseLocalDate(e.Date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
                    value: Number(e.Pain_Level),
                    type: 'pain'
                }));
        } else {
            // Monthly Grouping (1y, 2y, all) -> Show Frequency
            const monthlyMap = {};
            migraineDays.forEach(e => {
                const d = parseLocalDate(e.Date);
                const key = `${d.getFullYear()}-${d.getMonth()}`; // Unique sortable key
                const label = d.toLocaleDateString(undefined, { month: 'short', year: 'numeric' });

                if (!monthlyMap[key]) monthlyMap[key] = { label, count: 0, sortKey: d.getTime() };
                monthlyMap[key].count += 1;
            });
            // Sort by time
            chartData = Object.values(monthlyMap)
                .sort((a, b) => a.sortKey - b.sortKey)
                .map(item => ({ name: item.label, value: item.count, type: 'count' }));
        }

        return { avgDaysPerMonth, avgPain, maxPain, chartData };
    }, [entries, timeRange]);

    if (loading) return <div className="loading-state"><Loader2 className="animate-spin" size={48} /></div>;
    if (error) return <div className="error-state">{error}</div>;

    // Helper for risk color
    const getRiskColor = (level) => {
        if (level === 'High') return '#ff6b6b';
        if (level === 'Moderate') return '#fcc419';
        return '#51cf66';
    };

    // --- Render Logic ---
    const showDailyCheckin = todayStatus === 'missing';
    const showRetroCheckin = showRetroCard && missingDays.length > 0;
    const showReminders = dueMeds.length > 0;
    const hasSmartCards = showDailyCheckin || showRetroCheckin || showReminders;

    return (
        <div className="dashboard-container">
            <h2>Dashboard</h2>

            {/* --- SMART CARDS SECTION --- */}
            {hasSmartCards && (
                <div className="smart-cards-section">

                    {/* 1. Daily Check-in (Only if not logged) */}
                    {showDailyCheckin && (
                        <div className="smart-card">
                            <div className="card-header">
                                <h3><CheckCircle2 color="#4ade80" /> Daily Check-in</h3>
                                <p>
                                    {checkinStep === 'initial'
                                        ? "You haven't logged an entry for today yet."
                                        : "Great! Just a few quick details:"}
                                </p>
                            </div>

                            {checkinStep === 'initial' ? (
                                <div className="card-actions">
                                    <button className="action-btn" onClick={handleStartDailyCheckin}>
                                        {dailyMeds.length > 0 ? "Healthy & Medicated" : "Pain Free Day"}
                                    </button>
                                    <button className="action-btn secondary" onClick={() => navigate('/log')}>
                                        Migraine Attack
                                    </button>
                                </div>
                            ) : (
                                <div className="checkin-form" style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                        <div>
                                            <label style={{ fontSize: '0.85rem', color: '#bfdbfe', display: 'block', marginBottom: '4px' }}>Last Night's Sleep</label>
                                            <select
                                                name="sleep"
                                                value={checkinData.sleep}
                                                onChange={handleCheckinChange}
                                                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: 'none', background: 'rgba(255,255,255,0.1)', color: 'white' }}
                                            >
                                                <option value="1">Poor</option>
                                                <option value="2">Fair</option>
                                                <option value="3">Good</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label style={{ fontSize: '0.85rem', color: '#bfdbfe', display: 'block', marginBottom: '4px' }}>Activity Level</label>
                                            <select
                                                name="activity"
                                                value={checkinData.activity}
                                                onChange={handleCheckinChange}
                                                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: 'none', background: 'rgba(255,255,255,0.1)', color: 'white' }}
                                            >
                                                <option value="0">None</option>
                                                <option value="1">Light</option>
                                                <option value="2">Moderate</option>
                                                <option value="3">Heavy</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div>
                                        <label style={{ fontSize: '0.85rem', color: '#bfdbfe', display: 'block', marginBottom: '4px' }}>Notes (Optional)</label>
                                        <input
                                            type="text"
                                            name="notes"
                                            value={checkinData.notes}
                                            onChange={handleCheckinChange}
                                            placeholder="Any notes..."
                                            style={{ width: '100%', padding: '8px', borderRadius: '6px', border: 'none', background: 'rgba(255,255,255,0.1)', color: 'white' }}
                                        />
                                    </div>
                                    <div className="card-actions">
                                        <button className="action-btn" onClick={handleConfirmDailyCheckin}>
                                            Confirm Log
                                        </button>
                                        <button className="action-btn secondary" onClick={() => setCheckinStep('initial')}>
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* 2. Retroactive Check-in */}
                    {showRetroCheckin && (
                        <div className="smart-card">
                            <div className="card-header">
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <h3><CalendarCheck color="#fbbf24" /> Missing {missingDays.length} Days</h3>
                                    <div onClick={() => setShowRetroCard(false)} style={{ cursor: 'pointer' }}><XCircle size={18} /></div>
                                </div>
                                <p>We missed logs for <b>{missingDays[0]}</b> to <b>{missingDays[missingDays.length - 1]}</b>. Were they pain-free?</p>
                            </div>

                            {!retroConfirming ? (
                                <div className="card-actions">
                                    <button className="action-btn" onClick={() => {
                                        // Initialize per-day data
                                        const initialData = {};
                                        missingDays.forEach(d => {
                                            initialData[d] = { sleep: '3', activity: '2' };
                                        });
                                        setRetroData(initialData);
                                        setRetroConfirming(true);
                                    }}>
                                        Yes, Log All
                                    </button>
                                </div>
                            ) : (
                                <div className="checkin-form" style={{ marginTop: '1rem' }}>
                                    <p style={{ fontSize: '0.9rem', color: '#bfdbfe', marginBottom: '1rem' }}>
                                        Confirm details for each day:
                                    </p>
                                    <div className="retro-days-list" style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', maxHeight: '300px', overflowY: 'auto', marginBottom: '1rem' }}>
                                        {missingDays.map(dateStr => (
                                            <div key={dateStr} style={{ background: 'rgba(255,255,255,0.05)', padding: '0.8rem', borderRadius: '8px' }}>
                                                <div style={{ fontWeight: '600', marginBottom: '0.5rem', fontSize: '0.9rem' }}>{parseLocalDate(dateStr).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}</div>
                                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                                                    <div>
                                                        <label style={{ fontSize: '0.75rem', color: '#bfdbfe', display: 'block', marginBottom: '2px' }}>Sleep (Night Before)</label>
                                                        <select
                                                            value={retroData[dateStr]?.sleep || '3'}
                                                            onChange={(e) => setRetroData(prev => ({
                                                                ...prev,
                                                                [dateStr]: { ...prev[dateStr], sleep: e.target.value }
                                                            }))}
                                                            style={{ width: '100%', padding: '6px', borderRadius: '4px', border: 'none', background: 'rgba(0,0,0,0.2)', color: 'white', fontSize: '0.85rem' }}
                                                        >
                                                            <option value="1">Poor</option>
                                                            <option value="2">Fair</option>
                                                            <option value="3">Good</option>
                                                        </select>
                                                    </div>
                                                    <div>
                                                        <label style={{ fontSize: '0.75rem', color: '#bfdbfe', display: 'block', marginBottom: '2px' }}>Activity</label>
                                                        <select
                                                            value={retroData[dateStr]?.activity || '2'}
                                                            onChange={(e) => setRetroData(prev => ({
                                                                ...prev,
                                                                [dateStr]: { ...prev[dateStr], activity: e.target.value }
                                                            }))}
                                                            style={{ width: '100%', padding: '6px', borderRadius: '4px', border: 'none', background: 'rgba(0,0,0,0.2)', color: 'white', fontSize: '0.85rem' }}
                                                        >
                                                            <option value="0">None</option>
                                                            <option value="1">Light</option>
                                                            <option value="2">Moderate</option>
                                                            <option value="3">Heavy</option>
                                                        </select>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="card-actions">
                                        <button className="action-btn" onClick={handleConfirmRetroLog}>
                                            Confirm All
                                        </button>
                                        <button className="action-btn secondary" onClick={() => setRetroConfirming(false)}>
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* 3. Periodic Reminders */}
                    {showReminders && dueMeds
                        .filter(med => {
                            const snoozeDate = localStorage.getItem(`snooze_${med.name}`);
                            if (!snoozeDate) return true;
                            return new Date() > new Date(snoozeDate);
                        })
                        .map((med, i) => (
                            <div className="smart-card reminder" key={i}>
                                <div className="card-header">
                                    <h3><Clock color="#c4b5fd" /> {med.display_name || med.name} Reminder</h3>
                                    <p>
                                        {med.dueDays <= 0 ?
                                            `Overdue by ${Math.abs(med.dueDays)} days!` :
                                            `Due in ${med.dueDays} days (${med.nextDate})`}
                                    </p>
                                </div>
                                <div className="card-actions">
                                    <button className="action-btn" onClick={() => navigate('/log')}>
                                        Log Injection
                                    </button>
                                    <div className="snooze-actions" style={{ position: 'relative', display: 'inline-block' }}>
                                        <button
                                            className="action-btn secondary"
                                            onClick={(e) => {
                                                const menu = e.currentTarget.nextElementSibling;
                                                menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
                                            }}
                                        >
                                            Snooze...
                                        </button>
                                        <div className="snooze-menu" style={{
                                            display: 'none',
                                            position: 'absolute',
                                            bottom: '100%',
                                            left: '0',
                                            background: '#333',
                                            border: '1px solid #555',
                                            borderRadius: '6px',
                                            padding: '8px',
                                            zIndex: 100,
                                            minWidth: '120px',
                                            boxShadow: '0 4px 6px rgba(0,0,0,0.3)'
                                        }}>
                                            <div style={{ fontSize: '0.8rem', color: '#ccc', marginBottom: '6px', paddingBottom: '4px', borderBottom: '1px solid #444' }}>Snooze until:</div>
                                            {[
                                                { label: 'Tomorrow', days: 1 },
                                                { label: 'Next Week', days: 7 },
                                                { label: '2 Weeks', days: 14 }
                                            ].map(opt => (
                                                <button
                                                    key={opt.days}
                                                    style={{
                                                        display: 'block',
                                                        width: '100%',
                                                        textAlign: 'left',
                                                        background: 'none',
                                                        border: 'none',
                                                        color: '#fff',
                                                        padding: '6px 4px',
                                                        cursor: 'pointer',
                                                        fontSize: '0.85rem'
                                                    }}
                                                    onClick={() => {
                                                        const d = new Date();
                                                        d.setDate(d.getDate() + opt.days);
                                                        localStorage.setItem(`snooze_${med.name}`, d.toISOString());
                                                        // Force re-render by updating dummy state or reloading window logic? 
                                                        // Simplest for hotfix: reload or update 'dueMeds' local state.
                                                        setDueMeds(prev => prev.filter(m => m.name !== med.name));
                                                    }}
                                                >
                                                    {opt.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}

                </div>
            )}

            <div className="stats-grid">
                {/* Forecast Card */}
                <div className="stat-card forecast-card" style={{ borderLeft: prediction ? `5px solid ${getRiskColor(prediction.risk_level)}` : '5px solid #444', minHeight: '120px' }}>
                    <h3>Tomorrow's Risk</h3>
                    {predLoading ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#888', marginTop: '1rem' }}>
                            <Loader2 className="animate-spin" size={20} />
                            <span style={{ fontSize: '0.9rem' }}>Analyzing weather...</span>
                        </div>
                    ) : prediction ? (
                        <>
                            <p className="stat-value" style={{ color: getRiskColor(prediction.risk_level) }}>
                                {prediction.probability}%
                            </p>
                            <p className="stat-subtext" style={{ fontSize: '0.9rem', color: '#ccc' }}>
                                {prediction.risk_level} Risk
                            </p>

                            {prediction.source === 'historical_fallback' && (
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '6px',
                                    marginTop: '8px',
                                    paddingTop: '8px',
                                    borderTop: '1px solid #333',
                                    fontSize: '0.8rem',
                                    color: '#fcb900' // Careful orange
                                }}>
                                    <AlertTriangle size={14} />
                                    <span>Using past weather ({prediction.source_date})</span>
                                </div>
                            )}
                        </>
                    ) : (
                        <p style={{ fontSize: '0.9rem', color: '#888', marginTop: '1rem' }}>Data Unavailable</p>
                    )}
                </div>

                <div className="stat-card">
                    <h3>Avg Days/Mo (12mo)</h3>
                    <p className="stat-value">{stats.avgDaysPerMonth}</p>
                </div>

            </div>

            <div className="charts-grid">
                <div className="chart-card">
                    <div className="chart-header">
                        <h3>7-Day Forecast</h3>
                    </div>
                    <div className="chart-wrapper">
                        {forecast.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={forecast}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                                    <XAxis
                                        dataKey="date"
                                        stroke="#ccc"
                                        fontSize={12}
                                        tickFormatter={(dateStr) => parseLocalDate(dateStr).toLocaleDateString(undefined, { weekday: 'short', month: 'numeric', day: 'numeric' })}
                                    />
                                    <YAxis stroke="#ccc" domain={[0, 100]}>
                                        <Label
                                            value="Risk Probability"
                                            angle={-90}
                                            position="insideLeft"
                                            style={{ textAnchor: 'middle', fill: '#ccc', fontSize: '0.8rem' }}
                                        />
                                    </YAxis>
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#333', border: 'none' }}
                                        formatter={(value) => [`${value.toFixed(1)}%`, 'Risk']}
                                        labelFormatter={(label) => parseLocalDate(label).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
                                    />
                                    <Line type="monotone" dataKey="risk_probability" stroke="#8884d8" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : error ? (
                            <div className="error-state" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444' }}>
                                <AlertTriangle className="mr-2" size={20} />
                                <p>Unable to load forecast</p>
                            </div>
                        ) : (
                            <div className="loading-state" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <Loader2 className="animate-spin" size={24} />
                            </div>
                        )}
                    </div>
                </div>

                <div className="chart-card">
                    <div className="chart-header">
                        <h3>Migraine Trends</h3>
                        <div className="range-selector">
                            <button className={timeRange === '1m' ? 'active' : ''} onClick={() => setTimeRange('1m')}>1M</button>
                            <button className={timeRange === '1y' ? 'active' : ''} onClick={() => setTimeRange('1y')}>1Y</button>
                            <button className={timeRange === '2y' ? 'active' : ''} onClick={() => setTimeRange('2y')}>2Y</button>
                            <button className={timeRange === '3y' ? 'active' : ''} onClick={() => setTimeRange('3y')}>3Y</button>
                            <button className={timeRange === 'all' ? 'active' : ''} onClick={() => setTimeRange('all')}>All</button>
                        </div>
                    </div>
                    <div className="chart-wrapper">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={stats.chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                                <XAxis
                                    dataKey="name"
                                    stroke="#ccc"
                                    fontSize={12}
                                    minTickGap={20}
                                    interval="preserveStartEnd"
                                />
                                <YAxis stroke="#ccc" allowDecimals={false}>
                                    <Label
                                        value={timeRange === '1m' ? "Pain Level" : "Days"}
                                        angle={-90}
                                        position="insideLeft"
                                        style={{ textAnchor: 'middle', fill: '#ccc', fontSize: '0.8rem' }}
                                    />
                                </YAxis>
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#333', border: 'none' }}
                                    itemStyle={{ color: '#fff' }}
                                    formatter={(value, name, props) => [value, props.payload.type === 'pain' ? 'Pain Level' : 'Days']}
                                />
                                <Bar dataKey="value" fill="#4dabf7" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
