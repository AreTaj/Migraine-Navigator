import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CloudRain, Moon, Activity, Check, ArrowRight, ArrowLeft } from 'lucide-react';
import axios from '../services/apiClient';
import '../App.css';

const Onboarding = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);

    // State for Priors
    const [formData, setFormData] = useState({
        baseline_risk: 0.1, // Default: Rare
        weather_sensitivity: 0.5,
        sleep_sensitivity: 0.5,
        strain_sensitivity: 0.5
    });

    const handleNext = () => setStep(step + 1);
    const handleBack = () => setStep(step - 1);

    const handleSubmit = async () => {
        setLoading(true);
        try {
            await axios.post('/api/v1/user/priors', formData);
            // Mark as completed in local storage for now to avoid re-check lag
            localStorage.setItem('onboarding_completed', 'true');
            navigate('/');
        } catch (error) {
            console.error("Failed to save priors:", error);
            alert("Failed to save setup. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container" style={{ maxWidth: '600px', margin: '0 auto', padding: '2rem', textAlign: 'center' }}>

            {/* Step 1: Welcome & Baseline */}
            {step === 1 && (
                <div className="fade-in">
                    <h1>Welcome to Migraine Navigator</h1>
                    <p style={{ color: '#888', marginBottom: '2rem' }}>
                        Let's calibrate the prediction engine to your unique patterns.
                    </p>

                    <div className="card">
                        <h3>How often do you experience migraines?</h3>
                        <div className="grid-options">
                            {[
                                { label: "Rare (0-2 days/mo)", val: 0.1 },
                                { label: "Periodic (3-7 days/mo)", val: 0.3 },
                                { label: "Frequent (8-14 days/mo)", val: 0.6 },
                                { label: "Chronic (15+ days/mo)", val: 0.9 }
                            ].map((opt) => (
                                <button
                                    key={opt.val}
                                    className={`btn-option ${formData.baseline_risk === opt.val ? 'selected' : ''}`}
                                    onClick={() => setFormData({ ...formData, baseline_risk: opt.val })}
                                    style={{
                                        display: 'block',
                                        width: '100%',
                                        margin: '0.5rem 0',
                                        padding: '1rem',
                                        border: formData.baseline_risk === opt.val ? '2px solid var(--primary)' : '1px solid #333',
                                        background: formData.baseline_risk === opt.val ? '#1a1a1a' : 'transparent',
                                        color: 'var(--text-main, #fff)'
                                    }}
                                >
                                    {opt.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <button className="primary-btn" onClick={handleNext} style={{ marginTop: '2rem' }}>
                        Next <ArrowRight size={16} style={{ display: 'inline', verticalAlign: 'middle' }} />
                    </button>

                    <button
                        className="text-btn"
                        onClick={() => {
                            if (window.confirm("Use synthetic demo data? Your own data will not be saved.")) {
                                localStorage.setItem('tester_mode', 'true');
                                localStorage.setItem('onboarding_completed', 'true');
                                navigate('/');
                                window.location.reload(); // Ensure apiClient picks up the new header
                            }
                        }}
                        style={{ display: 'block', margin: '1.5rem auto 0', padding: '0.5rem', opacity: 0.6, fontSize: '0.9rem' }}
                    >
                        Explore as Tester (Demo Data)
                    </button>
                </div>
            )}

            {/* Step 2: Sensitivities */}
            {step === 2 && (
                <div className="fade-in">
                    <h2>Sensitivity Profile</h2>
                    <p style={{ color: '#888', marginBottom: '2rem' }}>
                        Adjust how much these factors typically affect you.
                    </p>

                    <div className="card" style={{ textAlign: 'left', padding: '1.5rem' }}>

                        {/* Weather */}
                        <div style={{ marginBottom: '2rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <CloudRain size={18} /> Weather Changes
                                </label>
                                <span className="badge">{Math.round(formData.weather_sensitivity * 10)}</span>
                            </div>
                            <small style={{ color: '#888', display: 'block', marginBottom: '0.5rem' }}>
                                Impact of pressure drops & temp swings
                            </small>
                            <input
                                type="range" min="0" max="1" step="0.1"
                                value={formData.weather_sensitivity}
                                onChange={(e) => setFormData({ ...formData, weather_sensitivity: parseFloat(e.target.value) })}
                                style={{ width: '100%' }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#666', fontSize: '0.8rem' }}>
                                <span>Low Impact</span>
                                <span>High Impact</span>
                            </div>
                        </div>

                        {/* Sleep */}
                        <div style={{ marginBottom: '2rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <Moon size={18} /> Sleep Quality
                                </label>
                                <span className="badge">{Math.round(formData.sleep_sensitivity * 10)}</span>
                            </div>
                            <small style={{ color: '#888', display: 'block', marginBottom: '0.5rem' }}>
                                Impact of irregular sleep or debt
                            </small>
                            <input
                                type="range" min="0" max="1" step="0.1"
                                value={formData.sleep_sensitivity}
                                onChange={(e) => setFormData({ ...formData, sleep_sensitivity: parseFloat(e.target.value) })}
                                style={{ width: '100%' }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#666', fontSize: '0.8rem' }}>
                                <span>Low Impact</span>
                                <span>High Impact</span>
                            </div>
                        </div>

                        {/* Strain */}
                        <div style={{ marginBottom: '1rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <Activity size={18} /> Physical/Mental Strain
                                </label>
                                <span className="badge">{Math.round(formData.strain_sensitivity * 10)}</span>
                            </div>
                            <small style={{ color: '#888', display: 'block', marginBottom: '0.5rem' }}>
                                Impact of stress or exhaustion
                            </small>
                            <input
                                type="range" min="0" max="1" step="0.1"
                                value={formData.strain_sensitivity}
                                onChange={(e) => setFormData({ ...formData, strain_sensitivity: parseFloat(e.target.value) })}
                                style={{ width: '100%' }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#666', fontSize: '0.8rem' }}>
                                <span>Low Impact</span>
                                <span>High Impact</span>
                            </div>
                        </div>

                    </div>

                    <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                        <button className="secondary-btn" onClick={handleBack}>
                            <ArrowLeft size={16} /> Back
                        </button>
                        <button className="primary-btn" onClick={handleSubmit} disabled={loading}>
                            {loading ? 'Optimizing Engine...' : 'Finish Setup'} <Check size={16} />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Onboarding;
