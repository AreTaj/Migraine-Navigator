import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, Label } from 'recharts';


import { Loader2 } from 'lucide-react';
import './Dashboard.css';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#aaa'];

function Dashboard() {
    const [entries, setEntries] = useState([]);
    const [prediction, setPrediction] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [timeRange, setTimeRange] = useState('1y'); // '1m', '1y', '2y'
    const [medTimeRange, setMedTimeRange] = useState('all'); // Separate filter for meds

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [entriesRes, predRes] = await Promise.all([
                    axios.get('/api/v1/entries'),
                    axios.get('/api/v1/prediction/future')
                ]);
                setEntries(entriesRes.data);
                setPrediction(predRes.data);
            } catch (err) {
                console.error("Error fetching dashboard data:", err);
                // Don't block whole dashboard if prediction fails
                // But generally error state handles both
                setError("Failed to load dashboard data.");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    // --- Aggregation Logic ---
    const stats = useMemo(() => {
        if (!entries.length) return { yearlyCount: 0, avgPain: 0, maxPain: 0, medData: [], chartData: [] };

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
        const uniqueDays12Mo = new Set(last12MoEntries.map(e => e.Date)).size;
        const avgDaysPerMonth = (uniqueDays12Mo / 12).toFixed(1);

        const painfulEntries = entries.filter(e => Number(e.Pain_Level) > 0);
        const maxPain = painfulEntries.reduce((max, e) => Math.max(max, Number(e.Pain_Level)), 0);
        const avgPain = painfulEntries.length
            ? (painfulEntries.reduce((sum, e) => sum + Number(e.Pain_Level), 0) / painfulEntries.length).toFixed(1)
            : 0;

        // 2. Medication Data (Filtered by medTimeRange)
        let medStartDate = new Date();
        // 'now' is already defined at the beginning of the useMemo hook
        if (medTimeRange === '1m') medStartDate.setMonth(now.getMonth() - 1);
        if (medTimeRange === '1y') medStartDate.setFullYear(now.getFullYear() - 1);
        if (medTimeRange === '2y') medStartDate.setFullYear(now.getFullYear() - 2);
        if (medTimeRange === '3y') medStartDate.setFullYear(now.getFullYear() - 3);
        if (medTimeRange === 'all') medStartDate = new Date(0);

        const medFilteredEntries = entries.filter(e => new Date(e.Date) >= medStartDate && Number(e.Pain_Level) > 0);

        const medCounts = {};
        const normalizeMed = (name) => {
            const lower = name.toLowerCase();
            if (lower.includes('ibuprofen') || lower.includes('advil')) return 'Ibuprofen';
            if (lower.includes('nurtec')) return 'Nurtec';
            if (lower.includes('tylenol') || lower.includes('acetaminophen')) return 'Tylenol';
            if (lower.includes('excedrin')) return 'Excedrin';
            if (lower.includes('ubrelvy')) return 'Ubrelvy';
            if (lower.includes('sumatriptan') || lower.includes('imitrex')) return 'Sumatriptan';
            if (lower.includes('rizatriptan') || lower.includes('maxalt')) return 'Rizatriptan';
            return name; // Return original if no match
        };

        medFilteredEntries.forEach(e => {
            let med = e.Medication ? e.Medication.trim() : "No Medication";
            if (med === "") med = "No Medication";

            // Normalize
            if (med !== "No Medication") {
                med = normalizeMed(med);
            }

            medCounts[med] = (medCounts[med] || 0) + 1;
        });
        const medData = Object.entries(medCounts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => {
                if (b.value === a.value) {
                    return a.name.localeCompare(b.name);
                }
                return b.value - a.value;
            });

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
                .sort((a, b) => new Date(a.Date) - new Date(b.Date))
                .map(e => ({
                    name: new Date(e.Date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
                    value: Number(e.Pain_Level),
                    type: 'pain'
                }));
        } else {
            // Monthly Grouping (1y, 2y, all) -> Show Frequency
            const monthlyMap = {};
            migraineDays.forEach(e => {
                const d = new Date(e.Date);
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

        return { avgDaysPerMonth, avgPain, maxPain, medData, chartData };
    }, [entries, timeRange, medTimeRange]);

    if (loading) return <div className="loading-state"><Loader2 className="animate-spin" size={48} /></div>;
    if (error) return <div className="error-state">{error}</div>;

    // Helper for risk color
    const getRiskColor = (level) => {
        if (level === 'High') return '#ff6b6b';
        if (level === 'Moderate') return '#fcc419';
        return '#51cf66';
    };

    return (
        <div className="dashboard-container">
            <h2>Dashboard</h2>

            <div className="stats-grid">
                {/* Forecast Card */}
                {prediction && (
                    <div className="stat-card forecast-card" style={{ borderLeft: `5px solid ${getRiskColor(prediction.risk_level)}` }}>
                        <h3>Tomorrow's Risk</h3>
                        <p className="stat-value" style={{ color: getRiskColor(prediction.risk_level) }}>
                            {prediction.probability}%
                        </p>
                        <p className="stat-subtext" style={{ fontSize: '0.9rem', color: '#ccc' }}>
                            {prediction.risk_level} Risk
                        </p>
                    </div>
                )}

                <div className="stat-card">
                    <h3>Avg Days/Mo (12mo)</h3>
                    <p className="stat-value">{stats.avgDaysPerMonth}</p>
                </div>
                <div className="stat-card">
                    <h3>Average Pain</h3>
                    <p className="stat-value">{stats.avg_pain || stats.avgPain}</p>
                </div>
                <div className="stat-card">
                    <h3>Highest Pain</h3>
                    <p className="stat-value">{stats.maxPain}</p>
                </div>
            </div>

            <div className="charts-grid">
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

                <div className="chart-card">
                    <div className="chart-header">
                        <h3>Medication Usage</h3>
                        <div className="range-selector">
                            <button className={medTimeRange === '1m' ? 'active' : ''} onClick={() => setMedTimeRange('1m')}>1M</button>
                            <button className={medTimeRange === '1y' ? 'active' : ''} onClick={() => setMedTimeRange('1y')}>1Y</button>
                            <button className={medTimeRange === 'all' ? 'active' : ''} onClick={() => setMedTimeRange('all')}>All</button>
                        </div>
                    </div>
                    <div className="chart-wrapper">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={stats.medData}
                                    cx="50%"
                                    cy="50%"
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {stats.medData.map((entry, index) => (
                                        <Cell
                                            key={`cell-${index}`}
                                            fill={entry.name === 'No Medication' ? '#aaa' : COLORS[index % COLORS.length]}
                                        />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ backgroundColor: '#333', border: 'none' }} />
                                <Legend
                                    layout="vertical"
                                    align="right"
                                    verticalAlign="middle"
                                    wrapperStyle={{ fontSize: '0.8rem', paddingLeft: '10px' }}
                                    formatter={(value, entry) => {
                                        const { payload } = entry;
                                        const total = stats.medData.reduce((sum, item) => sum + item.value, 0);
                                        const percent = ((payload.value / total) * 100).toFixed(0);
                                        return `${value} (${percent}%)`;
                                    }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
