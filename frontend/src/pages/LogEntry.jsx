import { useState, useEffect } from 'react';
import axios from '../services/apiClient';
import { Save, MapPin, Trash2, Plus, Loader2 } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { getCurrentLocation, getCityName } from '../utils/geolocation';
import './LogEntry.css';

function LogEntry() {
    const location = useLocation();
    const navigate = useNavigate();
    const editingEntry = location.state?.entry;

    const [availableMeds, setAvailableMeds] = useState([]);

    // Form Data
    const [formData, setFormData] = useState({
        Date: new Date().toISOString().split('T')[0],
        Time: new Date().toTimeString().slice(0, 5),
        Pain_Level: 5,
        Medications: [], // List of {name, dosage} objects
        Sleep: '3',
        Physical_Activity: '2',
        Triggers: '',
        Notes: '',
        Location: '',
        Latitude: null,
        Longitude: null,
        Medication: '', // Legacy support (hidden)
        Dosage: ''      // Legacy support (hidden)
    });

    const [status, setStatus] = useState({ type: '', message: '' });
    const [selectedMedId, setSelectedMedId] = useState(""); // For the dropdown
    const [locLoading, setLocLoading] = useState(false);

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
        fetchMedications();
        // Auto-fetch location if new entry and no location set
        if (!editingEntry && !formData.Location) {
            handleGetLocation();
        }
    }, []);

    const fetchMedications = async () => {
        try {
            const res = await axios.get('/api/v1/medications');
            setAvailableMeds(res.data);

            // Only auto-populate if NOT editing
            if (!editingEntry) {
                const dailyMeds = res.data.filter(m => m.frequency === 'daily');
                if (dailyMeds.length > 0) {
                    setFormData(prev => ({
                        ...prev,
                        Medications: dailyMeds.map(m => ({
                            name: m.name,
                            dosage: m.default_dosage
                        }))
                    }));
                }
            }
        } catch (err) {
            console.error("Failed to load medications", err);
        }
    };

    useEffect(() => {
        if (editingEntry) {
            // Handle Medication Migration/Legacy logic for the UI form
            let initialMeds = [];
            if (editingEntry.Medications && editingEntry.Medications.length > 0) {
                // New format
                initialMeds = editingEntry.Medications;
            } else if (editingEntry.Medication) {
                // Old format fallback
                initialMeds = [{ name: editingEntry.Medication, dosage: editingEntry.Dosage || '' }];
            }

            setFormData({
                ...editingEntry,
                Date: editingEntry.Date || new Date().toISOString().split('T')[0],
                Pain_Level: Number(editingEntry.Pain_Level),
                Sleep: normalizeSleep(editingEntry.Sleep),
                Physical_Activity: normalizeActivity(editingEntry.Physical_Activity),
                Medications: initialMeds
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

    const handleGetLocation = async () => {
        // Debugging via Status Message (since alert() is broken)
        setStatus({ type: 'loading', message: 'Getting location... (Please wait)' });
        setLocLoading(true);
        try {
            const { latitude, longitude } = await getCurrentLocation();
            let locationName = await getCityName(latitude, longitude);

            const fallbackLoc = latitude.toFixed(2) + ", " + longitude.toFixed(2);
            setFormData(prev => ({
                ...prev,
                Latitude: latitude,
                Longitude: longitude,
                Location: locationName || fallbackLoc
            }));
            setStatus({ type: 'success', message: 'Location found: ' + (locationName || fallbackLoc) });
        } catch (err) {
            console.error("Location error:", err);
            setStatus({ type: 'error', message: 'Location Error: ' + err.message });
        } finally {
            setLocLoading(false);
            // Clear success message after 3 seconds
            setTimeout(() => {
                setStatus(prev => prev.type === 'success' ? { type: '', message: '' } : prev);
            }, 3000);
        }
    };

    // --- Medication Logic ---
    const handleAddMedication = () => {
        if (!selectedMedId) return;
        const med = availableMeds.find(m => m.id === Number(selectedMedId));
        if (!med) return;

        // Check if already added
        if (formData.Medications.some(m => m.name === med.name)) {
            setStatus({ type: 'error', message: `${med.name} is already in the list.` });
            setTimeout(() => setStatus({ type: '', message: '' }), 3000);
            return;
        }

        const newItem = {
            name: med.name,
            dosage: med.default_dosage || ''
        };

        setFormData(prev => ({
            ...prev,
            Medications: [...prev.Medications, newItem]
        }));
        setSelectedMedId(""); // Reset dropdown
        setStatus({ type: '', message: '' }); // Clear any errors
    };

    // ... inside return ...
    <button
        type="button"
        onClick={handleAddMedication}
        className="icon-btn add-med-btn"
        title="Add Selected Medication"
        disabled={!selectedMedId}
    >
        <Plus size={20} />
    </button>

    const handleRemoveMedication = (index) => {
        setFormData(prev => ({
            ...prev,
            Medications: prev.Medications.filter((_, i) => i !== index)
        }));
    };

    const handleUpdateDosage = (index, newDosage) => {
        setFormData(prev => {
            const updated = [...prev.Medications];
            updated[index] = { ...updated[index], dosage: newDosage };
            return { ...prev, Medications: updated };
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setStatus({ type: 'loading', message: 'Saving...' });

        try {
            const payload = {
                ...formData,
                Pain_Level: parseInt(formData.Pain_Level),
                // Ensure legacy columns are treated as deprecated (empty for new, or unchanged for edit if we wanted, but let's just ignore them)
                Medication: "",
                Dosage: ""
            };

            if (editingEntry && editingEntry.id) {
                // UPDATE
                await axios.put(`/api/v1/entries/${editingEntry.id}`, payload);
                setStatus({ type: 'success', message: 'Entry updated successfully!' });
            } else {
                // CREATE
                await axios.post('/api/v1/entries', payload);
                setStatus({ type: 'success', message: 'Entry saved successfully!' });

                // Reset form slightly for next entry if creating
                if (!editingEntry) {
                    setFormData(prev => ({
                        ...prev,
                        Pain_Level: 5,
                        Medications: [],
                        Triggers: '',
                        Notes: '',
                        Location: '',
                        Latitude: null,
                        Longitude: null
                    }));
                }
            }
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

                {/* Medication Selector */}
                <div className="form-group full meds-section">
                    <label>Medications</label>
                    <div className="meds-selector-row">
                        <select
                            value={selectedMedId}
                            onChange={(e) => setSelectedMedId(e.target.value)}
                            className="med-select"
                        >
                            <option value="">Select a medication...</option>
                            {availableMeds.map(med => (
                                <option key={med.id} value={med.id}>
                                    {med.name} {med.display_name ? `(${med.display_name})` : ''}
                                </option>
                            ))}
                        </select>
                        <button
                            type="button"
                            onClick={handleAddMedication}
                            className="icon-btn add-med-btn"
                            title="Add Selected Medication"
                            disabled={!selectedMedId}
                        >
                            <Plus size={20} />
                        </button>
                    </div>

                    {/* Selected Meds List */}
                    <div className="selected-meds-list">
                        {formData.Medications.map((item, index) => (
                            <div key={index} className="med-item-row">
                                <span className="med-name">{item.name}</span>
                                <input
                                    type="text"
                                    placeholder="Dosage"
                                    value={item.dosage}
                                    onChange={(e) => handleUpdateDosage(index, e.target.value)}
                                    className="med-dosage-input"
                                />
                                <button type="button" onClick={() => handleRemoveMedication(index)} className="icon-btn remove-med-btn">
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        ))}
                        {formData.Medications.length === 0 && (
                            <div className="no-meds-text">No medications selected</div>
                        )}
                    </div>
                    <div className="meds-hint">
                        <small>Manage your medication list in the <a href="/medications">Medications Tab</a></small>
                    </div>
                </div>

                <div className="form-group half">
                    <label>Last Night's Sleep</label>
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
                        <button
                            type="button"
                            onClick={handleGetLocation}
                            className="input-icon-btn"
                            title="Get Current Location"
                        >
                            {locLoading ? <Loader2 size={18} className="animate-spin" /> : <MapPin size={18} />}
                        </button>
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
