import { useState, useEffect } from 'react';
import axios from 'axios';
import { Save, MapPin } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import './LogEntry.css';

function LogEntry() {
    const location = useLocation();
    const navigate = useNavigate();
    const editingEntry = location.state?.entry;

    const [formData, setFormData] = useState({
        Date: new Date().toISOString().split('T')[0],
        Time: new Date().toTimeString().slice(0, 5),
        Pain_Level: 5,
        Medication: '',
        Dosage: '',
        Sleep: '3', // Default Good
        Physical_Activity: '2', // Default Moderate
        Triggers: '',
        Notes: '',
        Location: '',
    });

    const [status, setStatus] = useState({ type: '', message: '' });

    // Helper to normalize legacy strings to numbers
    const normalizeSleep = (val) => {
        val = String(val).toLowerCase();
        if (val === 'good') return '3';
        if (val === 'fair') return '2';
        if (val === 'poor') return '1';
        return val;
    };

    const normalizeActivity = (val) => {
        val = String(val).toLowerCase();
        if (val === 'none') return '0';
        if (val === 'light') return '1';
        if (val === 'moderate') return '2';
        if (val === 'heavy') return '3';
        return val;
    };

    useEffect(() => {
        if (editingEntry) {
            setFormData({
                ...editingEntry,
                Date: editingEntry.Date || new Date().toISOString().split('T')[0],
                Pain_Level: Number(editingEntry.Pain_Level),
                Sleep: normalizeSleep(editingEntry.Sleep),
                Physical_Activity: normalizeActivity(editingEntry.Physical_Activity)
            });
        }
    }, [editingEntry]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setStatus({ type: 'loading', message: 'Saving...' });

        try {
            const payload = {
                ...formData,
                Pain_Level: parseInt(formData.Pain_Level),
            };

            if (editingEntry && editingEntry.id) {
                // UPDATE
                await axios.put(`/api/v1/entries/${editingEntry.id}`, payload);
                setStatus({ type: 'success', message: 'Entry updated successfully!' });
            } else {
                // CREATE
                await axios.post('/api/v1/entries', payload);
                setStatus({ type: 'success', message: 'Entry saved successfully!' });
            }

            // If needed, redirect back after short delay (optional)
            // setTimeout(() => navigate('/history'), 1000); 
        } catch (err) {
            console.error(err);
            setStatus({ type: 'error', message: 'Failed to save entry. Check console.' });
        }
    };

    return (
        <div className="log-entry-container">
            <h2>{editingEntry ? 'Edit Migraine Entry' : 'Log New Migraine'}</h2>

            {status.message && (
                <div className={`status-message ${status.type}`}>
                    {status.message}
                </div>
            )}

            <form onSubmit={handleSubmit} className="entry-form">
                <div className="form-group half">
                    <label>Date</label>
                    <input type="date" name="Date" value={formData.Date} onChange={handleChange} required />
                </div>
                <div className="form-group half">
                    <label>Time</label>
                    <input type="time" name="Time" value={formData.Time} onChange={handleChange} required />
                </div>

                <div className="form-group full">
                    <label>Pain Level: {formData.Pain_Level}</label>
                    <input
                        type="range"
                        name="Pain_Level"
                        min="0" max="10"
                        value={formData.Pain_Level}
                        onChange={handleChange}
                        className="range-input"
                    />
                    <div className="range-labels">
                        <span>Low</span>
                        <span>Severe</span>
                    </div>
                </div>

                <div className="form-group half">
                    <label>Medication</label>
                    <input type="text" name="Medication" value={formData.Medication} onChange={handleChange} placeholder="e.g. Ibuprofen" />
                </div>
                <div className="form-group half">
                    <label>Dosage</label>
                    <input type="text" name="Dosage" value={formData.Dosage} onChange={handleChange} placeholder="e.g. 200mg" />
                </div>

                <div className="form-group half">
                    <label>Sleep Quality</label>
                    <select name="Sleep" value={formData.Sleep} onChange={handleChange}>
                        <option value="3">Good</option>
                        <option value="2">Fair</option>
                        <option value="1">Poor</option>
                    </select>
                </div>
                <div className="form-group half">
                    <label>Physical Activity</label>
                    <select name="Physical_Activity" value={formData.Physical_Activity} onChange={handleChange}>
                        <option value="0">None</option>
                        <option value="1">Light</option>
                        <option value="2">Moderate</option>
                        <option value="3">Heavy</option>
                    </select>
                </div>

                <div className="form-group full">
                    <label>Location</label>
                    <div className="input-icon-wrapper">
                        <MapPin size={18} className="input-icon" />
                        <input type="text" name="Location" value={formData.Location || ''} onChange={handleChange} placeholder="Current location" />
                    </div>
                </div>

                <div className="form-group full">
                    <label>Triggers</label>
                    <textarea name="Triggers" value={formData.Triggers || ''} onChange={handleChange} rows="2" placeholder="Potential triggers..." />
                </div>

                <div className="form-group full">
                    <label>Notes</label>
                    <textarea name="Notes" value={formData.Notes || ''} onChange={handleChange} rows="3" placeholder="Additional details..." />
                </div>

                <button type="submit" className="submit-btn" disabled={status.type === 'loading'}>
                    <Save size={18} />
                    {status.type === 'loading' ? 'Saving...' : (editingEntry ? 'Update Entry' : 'Save Entry')}
                </button>
            </form>
        </div>
    );
}

export default LogEntry;
