import { useState, useEffect } from 'react';
import axios from '../services/apiClient';
import { Trash2, Plus, Zap, AlertCircle, Pencil, X, Check, ChevronDown, ChevronRight } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './Medications.css'; // Reusing Medications CSS for consistent styling

import CreatableSelect from 'react-select/creatable';

const COLORS = [
    '#EF4444', '#F59E0B', '#3B82F6', '#10B981', '#8B5CF6',
    '#EC4899', '#6366F1', '#14B8A6', '#F97316', '#64748B'
];



function Triggers() {
    const [triggers, setTriggers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [newTrigger, setNewTrigger] = useState('');
    const [deleteConfirmId, setDeleteConfirmId] = useState(null);
    const [editingId, setEditingId] = useState(null);
    const [editName, setEditName] = useState('');
    const [collapsedCategories, setCollapsedCategories] = useState({});

    // Usage Stats State
    const [entries, setEntries] = useState([]);
    const [timeRange, setTimeRange] = useState('1m');
    const [groupByCategory, setGroupByCategory] = useState(false);
    const [usageStats, setUsageStats] = useState([]);

    useEffect(() => {
        fetchTriggers();
        fetchEntries();
    }, []);

    // Calculate Usage Stats
    useEffect(() => {
        if (!entries.length) return;

        let startDate = new Date();
        if (timeRange === '1m') startDate.setMonth(startDate.getMonth() - 1);
        if (timeRange === '1y') startDate.setFullYear(startDate.getFullYear() - 1);
        if (timeRange === 'all') startDate = new Date(0);

        const filteredEntries = entries.filter(e => new Date(e.Date) >= startDate);

        // Count usage
        const counts = {};
        let total = 0;

        filteredEntries.forEach(e => {
            if (!e.Triggers) return;

            // Handle comma separated string
            const list = e.Triggers.split(',').map(s => s.trim()).filter(Boolean);
            list.forEach(tName => {
                let key = tName;
                if (groupByCategory) {
                    // Case-insensitive lookup
                    const triggerObj = triggers.find(tr => tr.name.toLowerCase() === tName.toLowerCase());

                    if (triggerObj) {
                        key = triggerObj.category || 'Uncategorized';
                    } else {
                        // Trigger found in history but not in registry (deleted or renamed)
                        // We treat these as 'Uncategorized' (or could be 'Archived')
                        key = 'Uncategorized';
                    }
                }
                counts[key] = (counts[key] || 0) + 1;
                total++;
            });
        });

        // Calculate data
        const totalTriggers = total;
        // 1. Map to array with explicit number casting
        const mappedData = Object.keys(counts).map(key => {
            const count = Number(counts[key]);
            const percentage = totalTriggers > 0 ? ((count / totalTriggers) * 100).toFixed(0) : '0';
            return {
                name: `${key} (${percentage}%)`,
                value: count,
                rawValue: count
            };
        });

        // 2. Sort Descending (Highest Value First)
        // Explicit comparator to avoid any ambiguity
        mappedData.sort((a, b) => {
            if (b.value > a.value) return 1;
            if (b.value < a.value) return -1;
            // Secondary sort by name if values equal (stable sort)
            return a.name.localeCompare(b.name);
        });

        // 3. Slice Top 10
        const finalData = mappedData.slice(0, 10);

        console.log("UsageStats Sorted:", finalData);
        setUsageStats(finalData);
    }, [entries, timeRange, triggers, groupByCategory]);

    const fetchTriggers = async () => {
        try {
            const res = await axios.get('/api/v1/triggers');
            setTriggers(res.data);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setError("Failed to fetch triggers.");
            setLoading(false);
        }
    };

    const fetchEntries = async () => {
        try {
            const res = await axios.get('/api/v1/entries');
            setEntries(res.data);
        } catch (err) {
            console.error("Failed to fetch entries");
        }
    };

    const handleAdd = async (e) => {
        e.preventDefault();
        if (!newTrigger.trim()) return;

        try {
            const res = await axios.post('/api/v1/triggers', { name: newTrigger });
            // Optimistic add or fetch
            const added = { id: res.data.id, name: res.data.name, usage_count: 0, category: null };
            setTriggers([...triggers, added].sort((a, b) => b.usage_count - a.usage_count));
            setNewTrigger('');
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to add trigger");
        }
    };

    const handleDeleteClick = (id) => {
        if (deleteConfirmId === id) {
            deleteTrigger(id);
        } else {
            setDeleteConfirmId(id);
            setTimeout(() => setDeleteConfirmId(null), 3000); // Auto cancel
        }
    };

    const handleCategoryUpdate = async (id, newCategory) => {
        const catValue = newCategory ? newCategory.value : null;

        // Optimistic update
        const updatedTriggers = triggers.map(t =>
            t.id === id ? { ...t, category: catValue } : t
        );
        setTriggers(updatedTriggers);

        try {
            await axios.put(`/api/v1/triggers/${id}`, { category: catValue || '' });
        } catch (err) {
            console.error("Failed to update category", err);
            // Revert? For now, we just rely on next fetch or ignore.
        }
    };

    const deleteTrigger = async (id) => {
        try {
            await axios.delete(`/api/v1/triggers/${id}`);
            setTriggers(triggers.filter(t => t.id !== id));
            setDeleteConfirmId(null);
        } catch (err) {
            alert("Failed to delete trigger");
        }
    };

    const handleEditClick = (trigger) => {
        setEditingId(trigger.id);
        setEditName(trigger.name);
    };

    const handleEditSave = async (id) => {
        if (!editName.trim()) return;

        // Optimistic
        const originalName = triggers.find(t => t.id === id)?.name;
        const updatedTriggers = triggers.map(t =>
            t.id === id ? { ...t, name: editName } : t
        );
        setTriggers(updatedTriggers);
        setEditingId(null);

        try {
            await axios.put(`/api/v1/triggers/${id}`, { name: editName });
            // Re-fetch entries because the backend updated the historical logs,
            // but our local 'entries' state still has the old trigger names.
            fetchEntries();
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to rename trigger");
            // Revert
            setTriggers(triggers.map(t => t.id === id ? { ...t, name: originalName } : t));
        }
    };

    const handleEditCancel = () => {
        setEditingId(null);
        setEditName('');
    };

    const toggleCategory = (category) => {
        setCollapsedCategories(prev => ({
            ...prev,
            [category]: !prev[category]
        }));
    };

    return (
        <div className="medications-container"> {/* Reusing class for layout */}
            <h2>Triggers Registry</h2>
            <p className="subtitle">Manage the factors that influence your migraines.</p>

            {/* --- Usage Chart --- */}
            <div className="medication-stats-card" style={{ marginTop: '1rem', padding: '1.5rem', background: '#1e1e1e', borderRadius: '12px', border: '1px solid #333' }}>
                <div className="chart-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Zap size={20} color="#F59E0B" />
                        <h3>Top Triggers</h3>
                    </div>
                    <div className="range-selector" style={{ background: '#333', padding: '4px', borderRadius: '6px', display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <label style={{ fontSize: '0.8rem', color: '#888', marginRight: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                            <input
                                type="checkbox"
                                checked={groupByCategory}
                                onChange={(e) => setGroupByCategory(e.target.checked)}
                                style={{ marginRight: '4px' }}
                            />
                            Group
                        </label>
                        <div style={{ width: '1px', height: '16px', background: '#444' }}></div>
                        <button onClick={() => setTimeRange('1m')} style={{ background: timeRange === '1m' ? '#4dabf7' : 'transparent', color: timeRange === '1m' ? 'white' : '#888', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer' }}>1M</button>
                        <button onClick={() => setTimeRange('1y')} style={{ background: timeRange === '1y' ? '#4dabf7' : 'transparent', color: timeRange === '1y' ? 'white' : '#888', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer' }}>1Y</button>
                        <button onClick={() => setTimeRange('all')} style={{ background: timeRange === 'all' ? '#4dabf7' : 'transparent', color: timeRange === 'all' ? 'white' : '#888', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer' }}>All</button>
                    </div>
                </div>

                <div style={{ width: '100%', height: 300, display: 'flex', alignItems: 'center' }}>
                    {usageStats.length > 0 ? (
                        <>
                            {/* Chart Side */}
                            <div style={{ flex: 1, height: '100%' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={usageStats}
                                            cx="50%"
                                            cy="50%"
                                            outerRadius={100}
                                            fill="#8884d8"
                                            dataKey="value"
                                            stroke="#fff"
                                            strokeWidth={1}
                                            paddingAngle={1}
                                        >
                                            {usageStats.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }}
                                            formatter={(value, name) => [`${value} times`, name.split(' (')[0]]}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>

                            {/* Custom Legend Side */}
                            <div style={{ width: '220px', paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px', justifyContent: 'center', height: '100%', overflowY: 'auto' }}>
                                {usageStats.map((item, index) => (
                                    <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: '#cbd5e1' }}>
                                        <div style={{
                                            width: '10px',
                                            height: '10px',
                                            backgroundColor: COLORS[index % COLORS.length],
                                            borderRadius: '2px',
                                            flexShrink: 0
                                        }}></div>
                                        <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={item.name}>
                                            {item.name}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </>
                    ) : (
                        <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#888' }}>
                            <p>No trigger data found for this period.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* --- Add Trigger --- */}
            <div className="add-medication-card" style={{ marginTop: '2rem' }}>
                <h3>Add New Trigger</h3>
                <form onSubmit={handleAdd} className="add-form">
                    <div className="form-group full">
                        <label>Trigger Name</label>
                        <input
                            type="text"
                            value={newTrigger}
                            onChange={(e) => setNewTrigger(e.target.value)}
                            placeholder="e.g. Red Wine, Stress, Storms..."
                            required
                        />
                    </div>
                    <div className="form-group full">
                        <button type="submit" className="add-btn">
                            <Plus size={18} /> Add Trigger
                        </button>
                    </div>
                </form>
            </div>

            {/* --- List Grouped by Category --- */}
            <div className="medications-list" style={{ marginTop: '2rem' }}>
                <h3>Your Triggers</h3>
                {loading ? <p>Loading...</p> : (
                    <div>
                        {(() => {
                            // Group triggers
                            const grouped = triggers.reduce((acc, t) => {
                                const cat = t.category || 'Uncategorized';
                                if (!acc[cat]) acc[cat] = [];
                                acc[cat].push(t);
                                return acc;
                            }, {});

                            // Sort categories (Uncategorized first)
                            const cats = Object.keys(grouped).sort((a, b) => {
                                if (a === 'Uncategorized') return -1;
                                if (b === 'Uncategorized') return 1;
                                return a.localeCompare(b);
                            });

                            // Derived options from existing data
                            const existingOptions = Array.from(new Set(triggers.map(t => t.category).filter(Boolean)))
                                .sort()
                                .map(c => ({ value: c, label: c }));

                            return cats.map(category => (
                                <div key={category} style={{ marginBottom: '1rem', background: '#0f172a', borderRadius: '8px', overflow: 'hidden', border: '1px solid #1e293b' }}>
                                    <h4
                                        onClick={() => toggleCategory(category)}
                                        style={{
                                            padding: '1rem',
                                            margin: 0,
                                            color: '#e2e8f0',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '10px',
                                            cursor: 'pointer',
                                            background: '#1e293b',
                                            userSelect: 'none'
                                        }}
                                    >
                                        {collapsedCategories[category] ? <ChevronRight size={18} /> : <ChevronDown size={18} />}
                                        {category === 'Uncategorized' ? 'Unsorted' : category}
                                        <span style={{ fontSize: '0.75rem', background: '#334155', padding: '2px 8px', borderRadius: '12px', color: '#fff', marginLeft: 'auto' }}>
                                            {grouped[category].length}
                                        </span>
                                    </h4>

                                    {!collapsedCategories[category] && (
                                        <div style={{ padding: '1rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem', borderTop: '1px solid #1e293b' }}>
                                            {grouped[category].map(t => (
                                                <div key={t.id} style={{
                                                    background: '#1e293b',
                                                    border: '1px solid #334155',
                                                    padding: '1rem',
                                                    borderRadius: '8px',
                                                    display: 'flex',
                                                    justifyContent: 'space-between',
                                                    alignItems: 'center',
                                                    gap: '1rem'
                                                }}>
                                                    <div style={{ flex: 1, overflow: 'hidden' }}>
                                                        {editingId === t.id ? (
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                                <input
                                                                    type="text"
                                                                    value={editName}
                                                                    onChange={(e) => setEditName(e.target.value)}
                                                                    autoFocus
                                                                    style={{
                                                                        background: '#334155',
                                                                        border: '1px solid #475569',
                                                                        color: 'white',
                                                                        padding: '4px 8px',
                                                                        borderRadius: '4px',
                                                                        fontSize: '0.9rem',
                                                                        width: '100%'
                                                                    }}
                                                                    onKeyDown={(e) => {
                                                                        if (e.key === 'Enter') handleEditSave(t.id);
                                                                        if (e.key === 'Escape') handleEditCancel();
                                                                    }}
                                                                />
                                                                <button onClick={() => handleEditSave(t.id)} className="icon-btn" style={{ color: '#10B981', padding: '4px' }}><Check size={16} /></button>
                                                                <button onClick={handleEditCancel} className="icon-btn" style={{ color: '#EF4444', padding: '4px' }}><X size={16} /></button>
                                                            </div>
                                                        ) : (
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                                <div style={{ fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '140px' }} title={t.name}>{t.name}</div>
                                                                <button onClick={() => handleEditClick(t)} className="icon-btn edit-btn" style={{ opacity: 0.5, padding: '2px' }} title="Rename">
                                                                    <Pencil size={12} />
                                                                </button>
                                                            </div>
                                                        )}
                                                        <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Used {t.usage_count} times</div>
                                                    </div>

                                                    <div style={{ width: '140px' }}>
                                                        <CreatableSelect
                                                            isClearable
                                                            placeholder="Category"
                                                            options={existingOptions}
                                                            value={t.category ? { label: t.category, value: t.category } : null}
                                                            onChange={(val) => handleCategoryUpdate(t.id, val)}
                                                            formatCreateLabel={(inputValue) => `Create "${inputValue}"`}
                                                            styles={{
                                                                control: (base) => ({
                                                                    ...base,
                                                                    background: 'transparent',
                                                                    borderColor: '#334155',
                                                                    minHeight: '28px',
                                                                    height: '28px',
                                                                    fontSize: '0.75rem'
                                                                }),
                                                                valueContainer: (base) => ({ ...base, height: '28px', padding: '0 8px' }),
                                                                indicatorsContainer: (base) => ({ ...base, height: '28px' }),
                                                                input: (base) => ({ ...base, color: 'white' }),
                                                                singleValue: (base) => ({ ...base, color: '#94a3b8' }),
                                                                menu: (base) => ({ ...base, background: '#1e293b', border: '1px solid #334155', zIndex: 999 }),
                                                                option: (base, state) => ({
                                                                    ...base,
                                                                    background: state.isFocused ? '#334155' : '#1e293b',
                                                                    color: 'white',
                                                                    cursor: 'pointer',
                                                                    fontSize: '0.8rem'
                                                                }),
                                                                placeholder: (base) => ({ ...base, color: '#555' })
                                                            }}
                                                        />
                                                    </div>

                                                    {deleteConfirmId === t.id ? (
                                                        <button
                                                            onClick={() => handleDeleteClick(t.id)}
                                                            className="icon-btn delete-confirm"
                                                            style={{ background: '#EF4444', color: 'white', width: 'auto', padding: '4px 8px', fontSize: '0.75rem', borderRadius: '4px', flexShrink: 0 }}
                                                        >
                                                            Confirm?
                                                        </button>
                                                    ) : (
                                                        <button onClick={() => handleDeleteClick(t.id)} className="icon-btn delete" style={{ flexShrink: 0 }}>
                                                            <Trash2 size={16} />
                                                        </button>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ));
                        })()}
                    </div>
                )}
            </div>
        </div>
    );
}

export default Triggers;
