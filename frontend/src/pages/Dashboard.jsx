import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Loader2 } from 'lucide-react';
import './Dashboard.css';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#aaa'];

function Dashboard() {
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [timeRange, setTimeRange] = useState('1y'); // '1m', '1y', '2y'

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get('/api/v1/entries');
                setEntries(response.data);
            } catch (err) {
                console.error("Error fetching entries:", err);
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

        // 1. General Stats (All Time or Current Year?) 
        // Usually "Entries This Year" implies Jan 1 - Dec 31
        const thisYearEntries = entries.filter(e => new Date(e.Date).getFullYear() === currentYear);
        const painfulEntries = entries.filter(e => Number(e.Pain_Level) > 0);

        const yearlyCount = thisYearEntries.length;
        const maxPain = painfulEntries.reduce((max, e) => Math.max(max, Number(e.Pain_Level)), 0);
        const avgPain = painfulEntries.length
            ? (painfulEntries.reduce((sum, e) => sum + Number(e.Pain_Level), 0) / painfulEntries.length).toFixed(1)
            : 0;

        // 2. Medication Data (All Time)
        const medCounts = {};
        painfulEntries.forEach(e => {
            let med = e.Medication ? e.Medication.trim() : "No Medication";
            if (med === "") med = "No Medication";
            medCounts[med] = (medCounts[med] || 0) + 1;
        });
        const medData = Object.entries(medCounts).map(([name, value]) => ({ name, value }));

        // 3. Chart Data (Dynamic based on timeRange)
        let startDate = new Date();
        if (timeRange === '1m') startDate.setMonth(now.getMonth() - 1);
        if (timeRange === '1y') startDate.setFullYear(now.getFullYear() - 1);
        if (timeRange === '2y') startDate.setFullYear(now.getFullYear() - 2);

        const filteredEntries = entries.filter(e => new Date(e.Date) >= startDate);

        let chartData = [];
        if (timeRange === '1m') {
            // Daily Grouping
            const dailyMap = {};
            filteredEntries.forEach(e => {
                dailyMap[e.Date] = (dailyMap[e.Date] || 0) + 1;
            });
            // Sort keys
            Object.keys(dailyMap).sort().forEach(date => {
                chartData.push({ name: new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }), count: dailyMap[date] });
            });
        } else {
            // Monthly Grouping (1y, 2y)
            const monthlyMap = {};
            filteredEntries.forEach(e => {
                const d = new Date(e.Date);
                const key = `${d.getFullYear()}-${d.getMonth()}`; // Unique sortable key
                const label = d.toLocaleDateString(undefined, { month: 'short', year: 'numeric' });

                if (!monthlyMap[key]) monthlyMap[key] = { label, count: 0, sortKey: d.getTime() };
                monthlyMap[key].count += 1;
            });
            // Sort by time
            chartData = Object.values(monthlyMap)
                .sort((a, b) => a.sortKey - b.sortKey)
                .map(item => ({ name: item.label, count: item.count }));
        }

        return { yearlyCount, avgPain, maxPain, medData, chartData };
    }, [entries, timeRange]);

    if (loading) return <div className="loading-state"><Loader2 className="animate-spin" size={48} /></div>;
    if (error) return <div className="error-state">{error}</div>;

    return (
        <div className="dashboard-container">
            <h2>Dashboard</h2>

            <div className="stats-grid">
                <div className="stat-card">
                    <h3>Entries This Year</h3>
                    <p className="stat-value">{stats.yearlyCount}</p>
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
                        </div>
                    </div>
                    <div className="chart-wrapper">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={stats.chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                                <XAxis dataKey="name" stroke="#ccc" fontSize={12} interval={timeRange === '1m' ? 4 : 0} />
                                <YAxis stroke="#ccc" allowDecimals={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#333', border: 'none' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Bar dataKey="count" fill="#4dabf7" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="chart-card">
                    <h3>Medication Usage (All Time)</h3>
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
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                >
                                    {stats.medData.map((entry, index) => (
                                        <Cell
                                            key={`cell-${index}`}
                                            fill={entry.name === 'No Medication' ? '#aaa' : COLORS[index % COLORS.length]}
                                        />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ backgroundColor: '#333', border: 'none' }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
