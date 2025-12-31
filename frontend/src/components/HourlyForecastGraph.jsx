import React, { useState, useEffect } from 'react';
import axios from '../services/apiClient';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Label } from 'recharts';
import { Loader2, AlertTriangle, ShieldCheck } from 'lucide-react';

const HourlyForecastGraph = () => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchHourly = async () => {
            try {
                const res = await axios.get('/api/v1/prediction/hourly');
                setData(res.data);
                setLoading(false);
            } catch (err) {
                console.error("Hourly forecast failed", err);
                setError("Failed to load hourly forecast");
                setLoading(false);
            }
        };
        fetchHourly();
    }, []);

    if (loading) return (
        <div className="chart-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Loader2 className="animate-spin" size={32} />
        </div>
    );

    if (error) return (
        <div className="chart-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444' }}>
            <AlertTriangle className="mr-2" /> {error}
        </div>
    );

    // Custom Tooltip
    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            const point = payload[0].payload;
            const details = point.details || {};

            return (
                <div style={{ backgroundColor: '#1e293b', padding: '10px', borderRadius: '8px', border: '1px solid #334155' }}>
                    <p style={{ fontWeight: 'bold', marginBottom: '5px', color: '#e2e8f0' }}>
                        {new Date(point.time).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                    </p>
                    <p style={{ color: '#fbbf24', fontSize: '0.9rem' }}>Relative Risk: {point.risk_score.toFixed(1)}%</p>
                    <p style={{ color: '#94a3b8', fontSize: '0.8rem', marginBottom: '8px' }}>Level: {point.risk_level}</p>

                    <div style={{ marginTop: '8px', fontSize: '0.75rem', color: '#cbd5e1', borderTop: '1px solid #334155', paddingTop: '4px' }}>
                        {details.heuristic_weather !== undefined && (
                            <div>Weather Factor: {(details.heuristic_weather * 100).toFixed(0)}%</div>
                        )}
                        {details.circadian_risk !== undefined && (
                            <div>Circadian Factor: {(details.circadian_risk * 100).toFixed(0)}%</div>
                        )}
                        {details.mitigation_factor < 0.9 && (
                            <div style={{ color: '#4ade80', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                                <ShieldCheck size={12} /> Med Protection Active
                            </div>
                        )}
                    </div>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="chart-card">
            <div className="chart-header">
                <h3>24-Hour Hourly Risk</h3>
            </div>
            <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#fcc419" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#fcc419" stopOpacity={0.05} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                        <XAxis
                            dataKey="time"
                            height={50}
                            tick={{ fill: '#aaa', fontSize: 11 }}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(t) => {
                                const d = new Date(t);
                                const h = d.getHours();
                                const ampm = h >= 12 ? 'PM' : 'AM';
                                const h12 = h % 12 || 12;
                                return `${h12} ${ampm}`;
                            }}
                            interval={3}
                            tickMargin={12}
                        />
                        <YAxis
                            domain={[0, 100]}
                            tick={{ fill: '#aaa', fontSize: 11 }}
                            tickLine={false}
                            axisLine={false}
                            label={{ value: 'Relative Risk', angle: -90, position: 'insideLeft', fill: '#666', fontSize: 13 }}
                        />
                        <Tooltip content={<CustomTooltip />} />

                        {(() => {
                            // Find midnight index for visual separator
                            const midnightPoint = data.find(d => {
                                const date = new Date(d.time);
                                return date.getHours() === 0;
                            });

                            if (midnightPoint) {
                                return (
                                    <ReferenceLine
                                        x={midnightPoint.time}
                                        stroke="#555"
                                        strokeDasharray="3 3"
                                    >
                                        <Label
                                            value={new Date(midnightPoint.time).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                            position="insideTopLeft"
                                            offset={10}
                                            fill="#eee"
                                            fontSize={12}
                                        />
                                        <Label
                                            value={new Date(new Date(midnightPoint.time).getTime() - 86400000).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                            position="insideTopRight"
                                            offset={10}
                                            fill="#eee"
                                            fontSize={12}
                                        />
                                    </ReferenceLine>
                                );
                            }
                            return null;
                        })()}

                        <Area
                            type="monotone"
                            dataKey="risk_score"
                            stroke="#fbbf24"
                            strokeWidth={3}
                            fillOpacity={1}
                            fill="url(#riskGradient)"
                            dot={{ r: 3, fill: '#fbbf24', strokeWidth: 0 }}
                            activeDot={{ r: 6, fill: '#fbbf24' }}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default HourlyForecastGraph;
