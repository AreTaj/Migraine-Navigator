import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Database, Save, Activity, CloudRain } from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import '../App.css';

const API_BASE = "http://127.0.0.1:8000/api/v1";

const Settings = () => {
    const [priors, setPriors] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        fetchPriors();
    }, []);

    const fetchPriors = async () => {
        try {
            const res = await axios.get(`${API_BASE}/user/priors`);
            setPriors(res.data);
            setLoading(false);
        } catch (err) {
            console.error(err);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            await axios.post(`${API_BASE}/user/priors`, priors);
            setTimeout(() => setSaving(false), 500);
        } catch (err) {
            alert("Failed");
            setSaving(false);
        }
    };

    if (loading) return <div className="loading">Loading...</div>;

    return (
        <div style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                <SettingsIcon size={32} />
                <h1>Settings</h1>
            </div>

            {/* Medical Profile */}
            <section className="card" style={{ marginBottom: '2rem' }}>
                <h3>Hybrid Engine Calibration</h3>
                <p className="text-muted">Adjust how sensitive you are to various triggers.</p>

                <div style={{ display: 'grid', gap: '1.5rem', marginTop: '1.5rem' }}>

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

                <button className="primary-btn" onClick={handleSave} disabled={saving} style={{ marginTop: '1.5rem', width: 'auto' }}>
                    {saving ? "Saved!" : "Update Calibration"}
                </button>
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
