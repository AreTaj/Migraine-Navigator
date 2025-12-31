import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Label, ReferenceLine } from 'recharts';

/**
 * Reusable Migraine Trends Chart
 * Props:
 * - data: Array of { name, value, type }
 * - timeRange: '1m', '1y' etc (for axis labeling context)
 * - onTimeRangeChange: callback(newRange)
 */
const MigraineTrends = ({ data, timeRange, onTimeRangeChange }) => {

    // Calculate Average for Reference Line (Only for aggregate views, not daily/1m)
    const averageValue = React.useMemo(() => {
        if (timeRange === '1m' || !data || data.length === 0) return null;
        const total = data.reduce((sum, item) => sum + item.value, 0);
        return total / data.length;
    }, [data, timeRange]);

    return (
        <div className="chart-card">
            <div className="chart-header">
                <h3>Migraine Trends</h3>
                <div className="range-selector">
                    <button className={timeRange === '1m' ? 'active' : ''} onClick={() => onTimeRangeChange('1m')}>1M</button>
                    <button className={timeRange === '1y' ? 'active' : ''} onClick={() => onTimeRangeChange('1y')}>1Y</button>
                    <button className={timeRange === '2y' ? 'active' : ''} onClick={() => onTimeRangeChange('2y')}>2Y</button>
                    <button className={timeRange === '3y' ? 'active' : ''} onClick={() => onTimeRangeChange('3y')}>3Y</button>
                    <button className={timeRange === 'all' ? 'active' : ''} onClick={() => onTimeRangeChange('all')}>All</button>
                </div>
            </div>
            <div className="chart-wrapper" style={{ width: '100%', height: '350px' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
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

                        {/* Average Reference Line */}
                        {averageValue !== null && (
                            <ReferenceLine
                                y={averageValue}
                                stroke="#fcc419"
                                strokeDasharray="3 3"
                                label={{
                                    position: 'right',
                                    value: `Avg: ${averageValue.toFixed(1)}`,
                                    fill: '#fcc419',
                                    fontSize: 12
                                }}
                            />
                        )}
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default MigraineTrends;
