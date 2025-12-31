import { useMemo } from 'react';

// Helper to parse YYYY-MM-DD as local date
const parseLocalDate = (dateStr) => {
    if (!dateStr) return new Date();
    const parts = dateStr.split('-');
    if (parts.length === 3) {
        return new Date(parts[0], parts[1] - 1, parts[2]);
    }
    return new Date(dateStr);
};

export const useMigraineStats = (entries, timeRange) => {
    return useMemo(() => {
        if (!entries || !entries.length) return { yearlyCount: 0, avgPain: 0, maxPain: 0, chartData: [], avgDaysPerMonth: 0 };

        const now = new Date();

        // 1. Avg Days/Month (Last 12 Months)
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(now.getFullYear() - 1);

        const last12MoEntries = entries.filter(e => {
            const d = new Date(e.Date);
            return d >= oneYearAgo && d <= now && Number(e.Pain_Level) > 0;
        });

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

        // Deduplicate entries by Date (take max pain for the day)
        const dailyEntries = {};
        filteredEntries.forEach(e => {
            const dateStr = e.Date;
            if (!dailyEntries[dateStr]) {
                dailyEntries[dateStr] = e;
            } else {
                if (Number(e.Pain_Level) > Number(dailyEntries[dateStr].Pain_Level)) {
                    dailyEntries[dateStr] = e;
                }
            }
        });
        const uniqueDays = Object.values(dailyEntries);
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
};
