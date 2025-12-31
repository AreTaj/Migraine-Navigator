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

    if (loading) return <div className="loading">Loading...</div>;

    return (
        <div style={{ padding: '2rem' }}>
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

            {/* Medical Profile */}
            <section className="card" style={{ marginBottom: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3>Hybrid Engine Calibration</h3>
                </div>
                <p className="text-muted">Adjust how sensitive you are to various triggers. Changes are saved automatically.</p>

                <div style={{ display: 'grid', gap: '1.5rem', marginTop: '1.5rem' }}>

                    <div className="setting-row">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                            <label>Baseline Frequency</label>
                            <span className="badge">
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
                        <div style={{ display: 'flex', justifyContent: 'space-between', color: '#666', fontSize: '0.8rem' }}>
                            <span>Rarely</span>
                            <span>Chronic</span>
                        </div>
                    </div>

                    <div className="setting-row">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                            <label>Weather Sensitivity</label>
                            <span className="badge">{(priors.weather_sensitivity * 10).toFixed(0)}</span>
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
                        <div style={{ display: 'flex', justifyContent: 'space-between', color: '#666', fontSize: '0.8rem' }}>
                            <span>Low Impact</span>
                            <span>High Impact</span>
                        </div>
                    </div>

                    <div className="setting-row">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                            <label>Sleep Sensitivity</label>
                            <span className="badge">{(priors.sleep_sensitivity * 10).toFixed(0)}</span>
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
                        <div style={{ display: 'flex', justifyContent: 'space-between', color: '#666', fontSize: '0.8rem' }}>
                            <span>Low Impact</span>
                            <span>High Impact</span>
                        </div>
                    </div>

                    <div className="setting-row">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                            <label>Physical/Mental Strain</label>
                            <span className="badge">{(priors.strain_sensitivity * 10).toFixed(0)}</span>
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
                        <div style={{ display: 'flex', justifyContent: 'space-between', color: '#666', fontSize: '0.8rem' }}>
                            <span>Low Impact</span>
                            <span>High Impact</span>
                        </div>
                    </div>
                </div>
            </section>

            {/* Data Management */}
            <section className="card">
                <h3>Data Management</h3>
                <div style={{ marginTop: '1rem' }}>
                    <Link to="/import" className="btn-option" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '1rem', justifyContent: 'center' }}>
                        <Database size={20} /> Import / Restore Data
                    </Link>
                </div>
            </section>
        </div>
    );
};

export default Settings;
