import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Database, Save, Activity, CloudRain } from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from '../services/apiClient';
import '../App.css';

const Settings = () => {
    const [priors, setPriors] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        fetchPriors();
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
                    <Link to="/import" className="btn-option" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '1rem', justifyContent: 'center' }}>
                        <Database size={20} /> Import / Restore Data
                    </Link>

                    {localStorage.getItem('tester_mode') === 'true' ? (
                        <button
                            className="btn-option"
                            style={{ width: '100%', marginTop: '1rem', background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', border: '1px solid #ef4444' }}
                            onClick={() => {
                                localStorage.removeItem('tester_mode');
                                window.location.reload();
                            }}
                        >
                            Exit Tester Mode
                        </button>
                    ) : (
                        <button
                            className="btn-option"
                            style={{ width: '100%', marginTop: '1rem', background: 'rgba(59, 130, 246, 0.2)', color: '#93c5fd', border: '1px solid #3b82f6' }}
                            onClick={() => {
                                localStorage.setItem('tester_mode', 'true');
                                localStorage.setItem('onboarding_completed', 'true');
                                window.location.href = '/';
                            }}
                        >
                            Explore as Tester (Demo Data)
                        </button>
                    )}
                </div>
            </section>
        </div>
    );
};

export default Settings;
