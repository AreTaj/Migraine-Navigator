import React, { useState, useEffect } from 'react';
import axios from '../services/apiClient';
import { Trash2, Plus, Tag, AlertCircle } from 'lucide-react';

const TriggerManager = () => {
    const [triggers, setTriggers] = useState([]);
    const [newTrigger, setNewTrigger] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchTriggers();
    }, []);

    const fetchTriggers = async () => {
        try {
            const res = await axios.get('/api/v1/triggers');
            setTriggers(res.data);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setError("Failed to load triggers.");
            setLoading(false);
        }
    };

    const handleAdd = async (e) => {
        e.preventDefault();
        if (!newTrigger.trim()) return;

        try {
            const res = await axios.post('/api/v1/triggers', { name: newTrigger });
            // Add to local state (optimistic or use response)
            // Re-fetch to simpler ensure id and usage count are aligned or construct manually
            const added = { id: res.data.id, name: res.data.name, usage_count: 0, is_system_default: false };
            setTriggers([...triggers, added].sort((a, b) => b.usage_count - a.usage_count));
            setNewTrigger('');
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to add trigger");
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Delete this trigger? usage history will remain in logs, but it will disappear from autocomplete.")) return;
        try {
            await axios.delete(`/api/v1/triggers/${id}`);
            setTriggers(triggers.filter(t => t.id !== id));
        } catch (err) {
            console.error(err);
            alert("Failed to delete trigger");
        }
    };

    if (loading) return <div style={{ padding: '1rem', color: '#888' }}>Loading triggers...</div>;

    return (
        <section className="card" style={{ marginTop: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Tag size={20} color="#60a5fa" />
                    <h3>Trigger Registry</h3>
                </div>
                <span className="badge" style={{ background: '#3b82f620', color: '#60a5fa' }}>{triggers.length} Active</span>
            </div>

            <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
                Manage the list of known triggers. These will appear in the autocomplete menu when logging a migraine.
                <br /><small style={{ opacity: 0.7 }}>Deleting a trigger here does <strong>not</strong> remove it from past log entries.</small>
            </p>

            <form onSubmit={handleAdd} style={{ display: 'flex', gap: '10px', marginBottom: '1.5rem' }}>
                <input
                    type="text"
                    value={newTrigger}
                    onChange={(e) => setNewTrigger(e.target.value)}
                    placeholder="Add new trigger (e.g. 'Red Wine', 'Stress', 'Bright Light')"
                    style={{
                        flex: 1,
                        padding: '10px',
                        borderRadius: '8px',
                        border: '1px solid #334155',
                        background: '#0f172a',
                        color: 'white',
                        fontSize: '0.95rem'
                    }}
                />
                <button
                    type="submit"
                    className="btn-primary"
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        background: '#3b82f6',
                        border: 'none',
                        color: 'white',
                        padding: '0 20px',
                        borderRadius: '8px',
                        fontWeight: 600,
                        cursor: 'pointer'
                    }}
                >
                    <Plus size={18} /> Add
                </button>
            </form>

            {triggers.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b', border: '1px dashed #334155', borderRadius: '8px' }}>
                    <AlertCircle size={24} style={{ marginBottom: '0.5rem', opacity: 0.5 }} />
                    <p>No triggers defined yet. Add some common ones to get started!</p>
                </div>
            ) : (
                <div className="triggers-list" style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                    {triggers.map(t => (
                        <div key={t.id} style={{
                            background: '#1e293b',
                            border: '1px solid #334155',
                            padding: '6px 12px',
                            borderRadius: '20px',
                            fontSize: '0.9rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            transition: 'all 0.2s'
                        }}>
                            <span style={{ fontWeight: 500 }}>{t.name}</span>
                            <span style={{
                                fontSize: '0.75rem',
                                color: '#94a3b8',
                                background: '#0f172a',
                                padding: '2px 8px',
                                borderRadius: '10px',
                                minWidth: '20px',
                                textAlign: 'center'
                            }} title="Times Used">
                                {t.usage_count}
                            </span>
                            <button
                                onClick={() => handleDelete(t.id)}
                                title="Delete Trigger"
                                style={{
                                    background: 'transparent',
                                    border: 'none',
                                    color: '#94a3b8',
                                    cursor: 'pointer',
                                    padding: '4px',
                                    display: 'flex',
                                    marginLeft: '4px',
                                    borderRadius: '50%'
                                }}
                                onMouseOver={(e) => e.currentTarget.style.color = '#ef4444'}
                                onMouseOut={(e) => e.currentTarget.style.color = '#94a3b8'}
                            >
                                <Trash2 size={14} />
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </section>
    );
};

export default TriggerManager;
