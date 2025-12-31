import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Pill, CalendarCheck, CheckCircle2, Clock, XCircle, AlertTriangle, Sparkles } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Label, LineChart, Line } from 'recharts';
import axios from '../services/apiClient';
import HourlyForecastGraph from '../components/HourlyForecastGraph';
import AllCaughtUpCard from '../components/AllCaughtUpCard';
import { useMigraineStats } from '../utils/useMigraineStats';
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
    // New State for Hourly Forecast (Lifted Up)
    const [hourlyData, setHourlyData] = useState([]);
    const [hourlyLoading, setHourlyLoading] = useState(true);
    const [priors, setPriors] = useState(null);

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
                const [entriesRes, medsRes, hourlyRes, priorsRes] = await Promise.all([
                    axios.get('/api/v1/entries'),
                    axios.get('/api/v1/medications'),
                    axios.get('/api/v1/prediction/hourly').catch(err => ({ data: [] })), // Fail gracefully
                    axios.get('/api/v1/user/priors').catch(err => ({ data: { temp_unit: 'C' } }))
                ]);

                const entriesData = entriesRes.data;
                setEntries(entriesData);
                const allMeds = medsRes.data;
                setMeds(allMeds);
                setHourlyData(hourlyRes.data);
                setHourlyLoading(false);
                setPriors(priorsRes.data);


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

    // Add missing handler
    const handleDismissRetro = () => {
        setShowRetroCard(false);
    };



    // --- Aggregation Logic (Hooks) ---
    const stats = useMigraineStats(entries, timeRange);

    // Calculate Streak
    const currentStreak = useMemo(() => {
        if (!entries || entries.length === 0) return 0;
        const sorted = [...entries].sort((a, b) => new Date(b.Date) - new Date(a.Date));
        let streak = 0;
        let checkDate = new Date();
        // Allow streak to continue if today is not logged yet
        const todayStr = checkDate.toISOString().split('T')[0];
        if (!sorted.find(e => e.Date === todayStr)) {
            checkDate.setDate(checkDate.getDate() - 1);
        }

        while (true) {
            const dateStr = checkDate.toISOString().split('T')[0];
            if (sorted.find(e => e.Date === dateStr)) {
                streak++;
                checkDate.setDate(checkDate.getDate() - 1);
            } else {
                break;
            }
        }
        return streak;
    }, [entries]);


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
            {/* Header Removed */}

            {/* --- DASHBOARD OVERVIEW ROW (Status Center + Quick Stats) --- */}
            <div className="dashboard-overview">

                {/* 1. STATUS CENTER (Smart Cards OR "All Caught Up") */}
                {hasSmartCards ? (
                    <div className="smart-cards-section">
                        {(() => {
                            const cards = [];
                            const hour = new Date().getHours();
                            const isEvening = hour >= 18;

                            // 1. Retroactive Checks
                            if (showRetroCheckin) {
                                cards.push({
                                    priority: 10,
                                    id: 'retro',
                                    content: (
                                        <div className="smart-card" style={{ borderLeft: '4px solid #f59e0b' }}>
                                            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                                                <div>
                                                    <h3><AlertTriangle color="#f59e0b" /> Missing {missingDays.length} {missingDays.length === 1 ? 'Day' : 'Days'}</h3>
                                                    {!retroConfirming && <p>We missed logs for <b>{missingDays[0]}</b> to <b>{missingDays[missingDays.length - 1]}</b>. Were they pain-free?</p>}
                                                </div>
                                                <button onClick={handleDismissRetro} style={{ background: 'none', border: 'none', color: '#666', cursor: 'pointer' }}><XCircle size={18} /></button>
                                            </div>

                                            {!retroConfirming ? (
                                                <div className="card-actions">
                                                    <button className="action-btn" onClick={() => {
                                                        const initialData = {};
                                                        missingDays.forEach(d => { initialData[d] = { sleep: '3', activity: '2' }; });
                                                        setRetroData(initialData);
                                                        setRetroConfirming(true);
                                                    }}>
                                                        Yes, Log All
                                                    </button>
                                                </div>
                                            ) : (
                                                <div className="checkin-form" style={{ marginTop: '0.2rem', width: '100%' }}>
                                                    <p style={{ fontSize: '0.9rem', color: '#bfdbfe', marginBottom: '0.5rem' }}>Confirm details per day:</p>
                                                    <div className="retro-days-list" style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', maxHeight: '120px', overflowY: 'auto', marginBottom: '0.5rem' }}>
                                                        {missingDays.map(dateStr => (
                                                            <div key={dateStr} style={{ display: 'flex', gap: '1rem', alignItems: 'center', background: 'rgba(255,255,255,0.05)', padding: '4px 8px', borderRadius: '4px' }}>
                                                                <span style={{ fontSize: '0.8rem', width: '80px' }}>{parseLocalDate(dateStr).toLocaleDateString(undefined, { month: 'numeric', day: 'numeric' })}</span>
                                                                <select
                                                                    value={retroData[dateStr]?.sleep || '3'}
                                                                    onChange={(e) => setRetroData(prev => ({ ...prev, [dateStr]: { ...prev[dateStr], sleep: e.target.value } }))}
                                                                    style={{ padding: '2px', borderRadius: '4px', border: 'none', background: 'rgba(0,0,0,0.3)', color: 'white', fontSize: '0.8rem' }}
                                                                >
                                                                    <option value="1">Sleep: Poor</option><option value="2">Sleep: Fair</option><option value="3">Sleep: Good</option>
                                                                </select>
                                                                <select
                                                                    value={retroData[dateStr]?.activity || '2'}
                                                                    onChange={(e) => setRetroData(prev => ({ ...prev, [dateStr]: { ...prev[dateStr], activity: e.target.value } }))}
                                                                    style={{ padding: '2px', borderRadius: '4px', border: 'none', background: 'rgba(0,0,0,0.3)', color: 'white', fontSize: '0.8rem' }}
                                                                >
                                                                    <option value="0">Act: None</option><option value="1">Act: Light</option><option value="2">Act: Mod</option><option value="3">Act: Heavy</option>
                                                                </select>
                                                            </div>
                                                        ))}
                                                    </div>
                                                    <div className="card-actions">
                                                        <button className="action-btn" onClick={handleConfirmRetroLog}>Confirm</button>
                                                        <button className="action-btn secondary" onClick={() => setRetroConfirming(false)}>Cancel</button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )
                                });
                            }

                            // 2. Daily Check-in
                            if (showDailyCheckin) {
                                cards.push({
                                    priority: isEvening ? 15 : 30,
                                    id: 'daily',
                                    content: (
                                        <div className="smart-card">
                                            <div className="card-header">
                                                <h3><CheckCircle2 color="#4ade80" /> Daily Check-in</h3>
                                                {checkinStep === 'initial' && <p>You haven't logged an entry for today yet.</p>}
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
                                                <div className="checkin-form" style={{ marginTop: '0.2rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                                                        <div>
                                                            <label style={{ fontSize: '0.8rem', color: '#bfdbfe', display: 'block', marginBottom: '2px' }}>Last Night's Sleep</label>
                                                            <select name="sleep" value={checkinData.sleep} onChange={handleCheckinChange} style={{ width: '100%', padding: '4px', borderRadius: '6px', border: 'none', background: 'rgba(255,255,255,0.1)', color: 'white', fontSize: '0.9rem' }}>
                                                                <option value="1">Poor</option><option value="2">Fair</option><option value="3">Good</option>
                                                            </select>
                                                        </div>
                                                        <div>
                                                            <label style={{ fontSize: '0.8rem', color: '#bfdbfe', display: 'block', marginBottom: '2px' }}>Activity Level</label>
                                                            <select name="activity" value={checkinData.activity} onChange={handleCheckinChange} style={{ width: '100%', padding: '4px', borderRadius: '6px', border: 'none', background: 'rgba(255,255,255,0.1)', color: 'white', fontSize: '0.9rem' }}>
                                                                <option value="0">None</option><option value="1">Light</option><option value="2">Moderate</option><option value="3">Heavy</option>
                                                            </select>
                                                        </div>
                                                    </div>
                                                    <div className="card-actions" style={{ marginTop: '0.2rem' }}>
                                                        <button className="action-btn" onClick={handleConfirmDailyCheckin}>Confirm Log</button>
                                                        <button className="action-btn secondary" onClick={() => setCheckinStep('initial')}>Cancel</button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )
                                });
                            }

                            // 3. Reminders
                            if (showReminders && dueMeds.length > 0) {
                                const validMeds = dueMeds.filter(med => {
                                    const snoozeDate = localStorage.getItem(`snooze_${med.name}`);
                                    if (!snoozeDate) return true;
                                    return new Date() > new Date(snoozeDate);
                                });

                                validMeds.forEach((med, i) => {
                                    cards.push({
                                        priority: 20,
                                        id: `med-${i}`,
                                        content: (
                                            <div className="smart-card reminder">
                                                <div className="card-header">
                                                    <h3><Clock color="#c4b5fd" /> {med.display_name || med.name} Reminder</h3>
                                                    <p>Due today! ({med.dueDays <= 0 ? `Overdue` : 'Due now'})</p>
                                                </div>
                                                <div className="card-actions">
                                                    <button className="action-btn" onClick={() => navigate('/log')}>Log Injection</button>
                                                    <div className="snooze-actions" style={{ position: 'relative', display: 'inline-block' }}>
                                                        <button className="action-btn secondary" onClick={(e) => {
                                                            const menu = e.currentTarget.nextElementSibling;
                                                            menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
                                                        }}>Snooze</button>
                                                        <div className="snooze-menu" style={{ display: 'none', position: 'absolute', bottom: '100%', left: '0', background: '#333', border: '1px solid #555', borderRadius: '6px', padding: '8px', zIndex: 100, minWidth: '120px' }}>
                                                            {[{ l: 'Tomorrow', d: 1 }, { l: 'Next Week', d: 7 }].map(opt => (
                                                                <button key={opt.d} style={{ display: 'block', width: '100%', textAlign: 'left', background: 'none', border: 'none', color: '#fff', padding: '6px', cursor: 'pointer' }}
                                                                    onClick={() => {
                                                                        const d = new Date(); d.setDate(d.getDate() + opt.d);
                                                                        localStorage.setItem(`snooze_${med.name}`, d.toISOString());
                                                                        setDueMeds(prev => prev.filter(m => m.name !== med.name));
                                                                    }}>
                                                                    {opt.l}
                                                                </button>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        )
                                    });
                                });
                            }

                            // Sort cards by priority (Lowest number first)
                            cards.sort((a, b) => a.priority - b.priority);

                            if (cards.length === 0) {
                                const now = new Date();
                                const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
                                const todayEntry = entries.find(e => e.Date === todayStr);
                                return <AllCaughtUpCard weather={hourlyData[0]} todayEntry={todayEntry} tempUnit={priors?.temp_unit} />;
                            }

                            return cards.map((card, index) => (
                                <div key={card.id} style={{
                                    position: index === 0 ? 'relative' : 'absolute',
                                    top: 0, left: 0, width: '100%',
                                    height: '100%', /* Force full height of container */
                                    zIndex: 50 - index,
                                    transform: `translateY(${index * 8}px) scale(${1 - index * 0.05})`,
                                    transformOrigin: 'top center',
                                    opacity: index === 0 ? 1 : 1 - (index * 0.3),
                                    transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
                                    pointerEvents: index === 0 ? 'auto' : 'none',
                                    borderRadius: '12px', /* Fix rounding clipping */
                                    overflow: 'hidden' // Clip background cards content
                                }}>
                                    {card.content}
                                </div>
                            ));
                        })()}
                    </div>
                ) : (
                    // --- ALL CAUGHT UP STATE ---
                    <div className="status-center-card">
                        <Sparkles color="#4ade80" size={32} />
                        <h3 style={{ margin: '0.5rem 0 0', color: '#f8fafc' }}>You're all caught up!</h3>
                        <p style={{ margin: 0, fontSize: '0.9rem' }}>Enjoy your day.</p>

                        {currentStreak > 0 && (
                            <div className="status-streak">
                                <span style={{ fontSize: '1.2rem' }}>🔥</span>
                                <b>{currentStreak} Day Streak</b>
                            </div>
                        )}
                    </div>
                )}


                {/* 2. RISK CARD */}
                <div className="stat-card forecast-card" style={{ borderLeft: prediction ? `5px solid ${getRiskColor(prediction.risk_level)}` : '5px solid #444', height: '200px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <h3>Tomorrow's Risk</h3>
                    {predLoading ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#888', marginTop: '1rem' }}>
                            <Loader2 className="animate-spin" size={20} />
                            <span style={{ fontSize: '0.9rem' }}>Analyzing...</span>
                        </div>
                    ) : prediction ? (
                        <>
                            <p className="stat-value" style={{ color: getRiskColor(prediction.risk_level) }}>
                                {prediction.probability}%
                            </p>
                            <p className="stat-subtext" style={{ fontSize: '0.9rem', color: '#ccc' }}>
                                {prediction.risk_level} Risk
                            </p>
                        </>
                    ) : (
                        <p style={{ fontSize: '0.9rem', color: '#888', marginTop: '1rem' }}>Data Unavailable</p>
                    )}
                </div>

            </div>

            {/* --- CHARTS GRID --- */}
            <div className="charts-grid">
                {/* 1. 24-Hour Hourly Risk (Left) */}
                <HourlyForecastGraph data={hourlyData} loading={hourlyLoading} />

                {/* 2. 7-Day Forecast (Right) */}
                <div className="chart-card">
                    <div className="chart-header">
                        <h3>7-Day Forecast</h3>
                    </div>
                    <div className="chart-wrapper">
                        {forecast.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={forecast}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                                    <XAxis
                                        dataKey="date"
                                        height={50}
                                        tick={{ fill: '#aaa', fontSize: 11 }}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={(dateStr) => parseLocalDate(dateStr).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' })}
                                    />
                                    <YAxis
                                        domain={[0, 100]}
                                        tick={{ fill: '#aaa', fontSize: 11 }}
                                        tickLine={false}
                                        axisLine={false}
                                        label={{ value: 'Risk Probability', angle: -90, position: 'insideLeft', fill: '#666', fontSize: 13 }}
                                    />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                                        itemStyle={{ color: '#e2e8f0' }}
                                        formatter={(value) => [`${value.toFixed(1)}%`, 'Risk']}
                                        labelFormatter={(label) => parseLocalDate(label).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
                                    />
                                    <Line type="monotone" dataKey="risk_probability" stroke="#8884d8" strokeWidth={3} dot={{ r: 4, fill: '#8884d8', strokeWidth: 0 }} activeDot={{ r: 6 }} />
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
            </div>
        </div >
    );
};

export default Dashboard;
