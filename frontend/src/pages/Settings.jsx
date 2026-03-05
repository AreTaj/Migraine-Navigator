import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Database, Save, Activity, CloudRain } from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from '../services/apiClient';
import '../App.css';

const Settings = () => {
    const [priors, setPriors] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [databases, setDatabases] = useState([]);
    const [activeDb, setActiveDb] = useState(localStorage.getItem('active_db') || 'migraine_log.db');
    const [dbDisplayNames, setDbDisplayNames] = useState(() => JSON.parse(localStorage.getItem('db_display_names')) || {});
    const [showRestartPrompt, setShowRestartPrompt] = useState(false);
    const [isEditingDbName, setIsEditingDbName] = useState(false);
    const [editingDbNameVal, setEditingDbNameVal] = useState('');

    const formatDbName = (db) => {
        if (dbDisplayNames[db]) return `${dbDisplayNames[db]} (${db})`;
        if (db === 'migraine_log.db') return 'migraine_log.db (Primary Data)';
        return db;
    };

    useEffect(() => {
        fetchPriors();
        fetchDatabases();
    }, []);

    // Auto-save logic
    useEffect(() => {
        if (loading || !priors) return;

        const timer = setTimeout(() => {
            savePriors();
        }, 800); // 800ms debounce

        return () => clearTimeout(timer);
    }, [priors, loading]);

    const fetchPriors = async () => {
        try {
            const res = await axios.get('/api/v1/user/priors');
            setPriors(res.data);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setLoading(false);
            alert("Failed to load settings. Is the backend running?");
        }
    };

    const fetchDatabases = async () => {
        try {
            const res = await axios.get('/api/v1/data/databases');
            setDatabases(res.data.databases || []);
        } catch (err) {
            console.error("Failed to fetch databases:", err);
        }
    };

    const savePriors = async () => {
        setSaving(true);
        try {
            await axios.post('/api/v1/user/priors', priors);
            setTimeout(() => setSaving(false), 800);
        } catch (err) {
            console.error("Auto-save failed:", err);
            setSaving(false);
        }
    };

    const [isCalibrationOpen, setIsCalibrationOpen] = useState(true);

    if (loading) return <div className="loading">Loading...</div>;

    return (
        <div style={{ padding: '2rem', paddingBottom: '4rem' }}>
            {showRestartPrompt && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.92)', zIndex: 9999,
                    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                    color: 'white', padding: '2rem', textAlign: 'center'
                }}>
                    <div style={{ background: '#111', padding: '3rem', borderRadius: '12px', border: '1px solid #333', maxWidth: '500px' }}>
                        <Database size={48} style={{ color: '#3b82f6', marginBottom: '1rem' }} />
                        <h2 style={{ marginBottom: '1rem' }}>Database Switched</h2>
                        <p style={{ color: '#cbd5e1', lineHeight: '1.6', marginBottom: '2rem' }}>
                            You have changed the active database. To ensure all data is safely loaded and no background processes are interrupted, you must restart the app.
                        </p>
                        <div style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', padding: '1rem', borderRadius: '8px', border: '1px solid #ef4444' }}>
                            <strong>Action Required:</strong><br />
                            Please completely quit the application (Cmd+Q on Mac) and open it again.
                        </div>
                    </div>
                </div>
            )}

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <SettingsIcon size={32} />
                    <h1>Settings</h1>
                </div>
                {saving && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981', fontSize: '0.9rem', fontWeight: 500 }}>
                        <Activity className="animate-pulse" size={16} /> Saving Changes...
                    </div>
                )}
            </div>

            {/* Section 1: Hybrid Engine Calibration (Collapsible) */}
            <section className="card" style={{ marginBottom: '2rem' }}>
                <div
                    onClick={() => setIsCalibrationOpen(!isCalibrationOpen)}
                    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <h3>Hybrid Engine Calibration</h3>
                        <span className="badge" style={{
                            background: priors.force_heuristic_mode ? '#f59e0b' : '#3b82f6',
                            color: priors.force_heuristic_mode ? '#000' : '#fff'
                        }}>
                            {priors.force_heuristic_mode ? 'Manual Rules' : 'AI Enhanced'}
                        </span>
                    </div>
                    <div style={{ transform: isCalibrationOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
                        ▼
                    </div>
                </div>

                {isCalibrationOpen && (
                    <div style={{ marginTop: '1.5rem', display: 'grid', gap: '1.5rem', animation: 'fadeIn 0.3s ease-in-out' }}>
                        <p className="text-muted" style={{ marginTop: '-0.5rem' }}>
                            Adjust how sensitive the model is to various triggers.
                        </p>

                        {/* Force Heuristic Toggle */}
                        <div className="setting-row">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px' }}>Prediction Mode</label>
                                    <small style={{ color: '#888' }}>Choose between AI-enhanced or strict rule-based forecasting.</small>
                                </div>
                                <div style={{ display: 'flex', background: '#334155', padding: '4px', borderRadius: '8px' }}>
                                    <button
                                        onClick={() => setPriors({ ...priors, force_heuristic_mode: false })}
                                        style={{
                                            padding: '8px 16px',
                                            borderRadius: '6px',
                                            border: 'none',
                                            background: !priors.force_heuristic_mode ? '#3b82f6' : 'transparent',
                                            color: !priors.force_heuristic_mode ? '#fff' : '#94a3b8',
                                            cursor: 'pointer',
                                            fontWeight: 500,
                                            transition: 'all 0.2s'
                                        }}
                                    >Auto (AI)</button>
                                    <button
                                        onClick={() => setPriors({ ...priors, force_heuristic_mode: true })}
                                        style={{
                                            padding: '8px 16px',
                                            borderRadius: '6px',
                                            border: 'none',
                                            background: priors.force_heuristic_mode ? '#f59e0b' : 'transparent',
                                            color: priors.force_heuristic_mode ? '#000' : '#94a3b8',
                                            cursor: 'pointer',
                                            fontWeight: 500,
                                            transition: 'all 0.2s'
                                        }}
                                    >Manual (Rules)</button>
                                </div>
                            </div>
                        </div>

                        <div className="setting-row">
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                <label>Baseline Frequency</label>
                                <span className="badge" style={{
                                    background: priors.force_heuristic_mode ? '#f59e0b' : '#3b82f6',
                                    color: priors.force_heuristic_mode ? '#000' : '#fff'
                                }}>
                                    {priors.baseline_risk < 0.3 ? 'Rare' : priors.baseline_risk < 0.6 ? 'Frequent' : 'Chronic'}
                                </span>
                            </div>
                            <small style={{ color: '#888', display: 'block', marginBottom: '0.5rem' }}>
                                How often do you get migraines regardless of triggers?
                            </small>
                            <input
                                type="range" min="0.05" max="0.95" step="0.05"
                                value={priors.baseline_risk}
                                onChange={(e) => setPriors({ ...priors, baseline_risk: parseFloat(e.target.value) })}
                                style={{ width: '100%' }}
                            />
                        </div>

                        <div className="setting-row">
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                <label>Weather Sensitivity</label>
                                <span className="badge" style={{
                                    background: priors.force_heuristic_mode ? '#f59e0b' : '#3b82f6',
                                    color: priors.force_heuristic_mode ? '#000' : '#fff'
                                }}>{(priors.weather_sensitivity * 10).toFixed(0)}</span>
                            </div>
                            <small style={{ color: '#888', display: 'block', marginBottom: '0.5rem' }}>
                                Impact of pressure drops & temp swings
                            </small>
                            <input
                                type="range" min="0" max="1" step="0.1"
                                value={priors.weather_sensitivity}
                                onChange={(e) => setPriors({ ...priors, weather_sensitivity: parseFloat(e.target.value) })}
                                style={{ width: '100%' }}
                            />
                        </div>

                        <div className="setting-row">
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                <label>Sleep Sensitivity</label>
                                <span className="badge" style={{
                                    background: priors.force_heuristic_mode ? '#f59e0b' : '#3b82f6',
                                    color: priors.force_heuristic_mode ? '#000' : '#fff'
                                }}>{(priors.sleep_sensitivity * 10).toFixed(0)}</span>
                            </div>
                            <small style={{ color: '#888', display: 'block', marginBottom: '0.5rem' }}>
                                Impact of irregular sleep or debt
                            </small>
                            <input
                                type="range" min="0" max="1" step="0.1"
                                value={priors.sleep_sensitivity}
                                onChange={(e) => setPriors({ ...priors, sleep_sensitivity: parseFloat(e.target.value) })}
                                style={{ width: '100%' }}
                            />
                        </div>

                        <div className="setting-row">
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                <label>Physical/Mental Strain</label>
                                <span className="badge" style={{
                                    background: priors.force_heuristic_mode ? '#f59e0b' : '#3b82f6',
                                    color: priors.force_heuristic_mode ? '#000' : '#fff'
                                }}>{(priors.strain_sensitivity * 10).toFixed(0)}</span>
                            </div>
                            <small style={{ color: '#888', display: 'block', marginBottom: '0.5rem' }}>
                                Impact of stress or exhaustion
                            </small>
                            <input
                                type="range" min="0" max="1" step="0.1"
                                value={priors.strain_sensitivity}
                                onChange={(e) => setPriors({ ...priors, strain_sensitivity: parseFloat(e.target.value) })}
                                style={{ width: '100%' }}
                            />
                        </div>
                    </div>
                )}
            </section>

            {/* Section 2: App Preferences */}
            <section className="card" style={{ marginBottom: '2rem' }}>
                <h3>App Preferences</h3>
                <div style={{ marginTop: '1rem' }}>
                    <div className="setting-row">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '4px' }}>Temperature Unit</label>
                                <small style={{ color: '#888' }}>Select your preferred unit for weather display.</small>
                            </div>
                            <div style={{ display: 'flex', background: '#1e293b', padding: '4px', borderRadius: '8px', border: '1px solid #334155' }}>
                                <button
                                    onClick={() => setPriors({ ...priors, temp_unit: 'C' })}
                                    style={{
                                        padding: '6px 16px',
                                        borderRadius: '6px',
                                        border: 'none',
                                        background: priors.temp_unit === 'C' ? '#334155' : 'transparent',
                                        color: priors.temp_unit === 'C' ? '#fff' : '#94a3b8',
                                        cursor: 'pointer',
                                        fontSize: '0.85rem',
                                        fontWeight: '500',
                                        transition: 'all 0.2s'
                                    }}
                                >Celsius</button>
                                <button
                                    onClick={() => setPriors({ ...priors, temp_unit: 'F' })}
                                    style={{
                                        padding: '6px 16px',
                                        borderRadius: '6px',
                                        border: 'none',
                                        background: priors.temp_unit === 'F' ? '#334155' : 'transparent',
                                        color: priors.temp_unit === 'F' ? '#fff' : '#94a3b8',
                                        cursor: 'pointer',
                                        fontSize: '0.85rem',
                                        fontWeight: '500',
                                        transition: 'all 0.2s'
                                    }}
                                >Fahrenheit</button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Section 3: Data Management */}
            <section className="card">
                <h3>Data Management</h3>
                <div style={{ marginTop: '1rem' }}>

                    <div style={{ marginBottom: '1.5rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                            <label style={{ fontWeight: 500, fontSize: '0.95rem' }}>Active Database</label>
                            {activeDb !== 'migraine_log.db' && (
                                <span className="badge" style={{ background: 'var(--accent-color)', color: '#000', padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 'bold' }}>CUSTOM</span>
                            )}
                        </div>
                        <select
                            value={activeDb}
                            onChange={(e) => {
                                const val = e.target.value;
                                localStorage.setItem('active_db', val);
                                setActiveDb(val);
                                setShowRestartPrompt(true);
                            }}
                            style={{
                                width: '100%', padding: '0.8rem', borderRadius: '6px',
                                background: '#111', color: 'white', border: '1px solid #333',
                                fontSize: '1rem'
                            }}
                        >
                            <option value="migraine_log.db">{formatDbName('migraine_log.db')}</option>
                            {databases.filter(db => db !== 'migraine_log.db').map(db => (
                                <option key={db} value={db}>{formatDbName(db)}</option>
                            ))}
                        </select>
                        <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                            {isEditingDbName ? (
                                <>
                                    <input
                                        value={editingDbNameVal}
                                        onChange={(e) => setEditingDbNameVal(e.target.value)}
                                        placeholder="Custom Display Name"
                                        style={{ padding: '0.4rem', borderRadius: '4px', background: '#222', color: 'white', border: '1px solid #444', flex: 1 }}
                                    />
                                    <button
                                        onClick={() => {
                                            const newNames = { ...dbDisplayNames };
                                            if (editingDbNameVal.trim() === '') {
                                                delete newNames[activeDb];
                                            } else {
                                                newNames[activeDb] = editingDbNameVal.trim();
                                            }
                                            setDbDisplayNames(newNames);
                                            localStorage.setItem('db_display_names', JSON.stringify(newNames));
                                            setIsEditingDbName(false);
                                        }}
                                        style={{ background: '#3b82f6', color: 'white', border: 'none', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer' }}
                                    >Save</button>
                                    <button
                                        onClick={() => setIsEditingDbName(false)}
                                        style={{ background: 'transparent', color: '#94a3b8', border: '1px solid #444', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer' }}
                                    >Cancel</button>
                                </>
                            ) : (
                                <button
                                    onClick={() => {
                                        setEditingDbNameVal(dbDisplayNames[activeDb] || '');
                                        setIsEditingDbName(true);
                                    }}
                                    style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: 'none', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}
                                >✎ Edit Display Name</button>
                            )}
                        </div>
                        <p className="text-muted" style={{ fontSize: '0.8rem', marginTop: '10px' }}>
                            Switching databases isolates your data entirely. Your default data is never overwritten or merged.
                        </p>
                    </div>

                    <Link to="/import" className="btn-option" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '1rem', justifyContent: 'center' }}>
                        <Database size={20} /> Import / Restore Data
                    </Link>
                </div>
            </section>
        </div>
    );
};

export default Settings;
