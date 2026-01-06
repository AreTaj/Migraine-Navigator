import { useState, useEffect } from 'react';
import { Save, MapPin, Loader2, ChevronDown, ChevronUp, Plus, Armchair, Footprints, Bike, Dumbbell, Utensils } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import medicationService from '../services/medicationService';
import triggerService from '../services/triggerService';
import entryService from '../services/entryService';
import './LogEntry.css';

function LogEntry() {
    const location = useLocation();
    const navigate = useNavigate();
    const editingEntry = location.state?.entry;

    const [availableMeds, setAvailableMeds] = useState([]);
    const [availableTriggers, setAvailableTriggers] = useState([]);

    // UI State for Accordion
    const [detailsOpen, setDetailsOpen] = useState(false);
    const [triggersOpen, setTriggersOpen] = useState(false);

    // Form Data
    const [formData, setFormData] = useState({
        Date: new Date().toISOString().split('T')[0],
        Time: new Date().toTimeString().slice(0, 5),
        Pain_Level: 5,
        Medications: [], // List of {name, dosage} objects
        Sleep: '3',
        Physical_Activity: '1', // Default to Light
        Triggers: '',
        Notes: '',
        Location: '',
        Latitude: null,
        Longitude: null,
        Medication: '',
        Dosage: ''
    });

    const [status, setStatus] = useState({ type: '', message: '' });
    const [locLoading, setLocLoading] = useState(false);

    // Helper: Pain Label Logic
    const getPainLabel = (level) => {
        if (level === 0) return 'No Pain';
        if (level <= 3) return 'Mild';
        if (level <= 6) return 'Moderate';
        return 'Severe';
    };

    // Helper: Auto-Capture Text
    const getAutoCaptureText = () => {
        const d = new Date(formData.Date + 'T' + formData.Time);
        const timeStr = d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
        const locStr = formData.Location ? ` • ${formData.Location}` : '';
        return `${timeStr}${locStr}`;
    };

    useEffect(() => {
        fetchMedications();
        fetchTriggers();
        if (!editingEntry && !formData.Location) {
            handleGetLocation();
        }
    }, [editingEntry]);

    const fetchTriggers = async () => {
        try {
            const data = await triggerService.getTriggers();
            // Store full objects: {id, name, usage_count, category}
            setAvailableTriggers(data);
        } catch (err) {
            console.error("Failed to load triggers", err);
        }
    };

    const fetchMedications = async () => {
        try {
            const data = await medicationService.getMedications();
            setAvailableMeds(data);

            if (!editingEntry) {
                // Auto-select daily meds
                const dailyMeds = data.filter(m => m.frequency === 'daily');
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
            let initialMeds = [];
            if (editingEntry.Medications && editingEntry.Medications.length > 0) {
                initialMeds = editingEntry.Medications;
            } else if (editingEntry.Medication) {
                initialMeds = [{ name: editingEntry.Medication, dosage: editingEntry.Dosage || '' }];
            }

            setFormData({
                ...editingEntry,
                Date: editingEntry.Date || new Date().toISOString().split('T')[0],
                Pain_Level: Number(editingEntry.Pain_Level),
                Sleep: String(editingEntry.Sleep), // Ensure string for comparison
                Physical_Activity: String(editingEntry.Physical_Activity),
                Medications: initialMeds
            });
            // If editing, maybe open details if there are notes?
            if (editingEntry.Notes) setDetailsOpen(true);
        }
    }, [editingEntry]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleGetLocation = async () => {
        setLocLoading(true);
        try {
            const { latitude, longitude, locationName } = await entryService.getLocation();
            setFormData(prev => ({
                ...prev,
                Latitude: latitude, Longitude: longitude, Location: locationName
            }));
        } catch (err) {
            console.error("Location error:", err);
        } finally {
            setLocLoading(false);
        }
    };

    // --- TOGGLE HANDLERS ---
    const toggleMedication = (med) => {
        setFormData(prev => {
            const exists = prev.Medications.some(m => m.name === med.name);
            let newMeds;
            if (exists) {
                newMeds = prev.Medications.filter(m => m.name !== med.name);
            } else {
                newMeds = [...prev.Medications, { name: med.name, dosage: med.default_dosage || '' }];
            }
            return { ...prev, Medications: newMeds };
        });
    };

    const toggleTrigger = (triggerName) => {
        setFormData(prev => {
            const currentList = prev.Triggers ? prev.Triggers.split(',').map(s => s.trim()).filter(Boolean) : [];
            const exists = currentList.includes(triggerName);

            let newList;
            if (exists) {
                newList = currentList.filter(t => t !== triggerName);
            } else {
                newList = [...currentList, triggerName];
            }
            return { ...prev, Triggers: newList.join(', ') };
        });
    };

    const addNewTrigger = async () => {
        const name = prompt("Enter new trigger name:");
        if (name) {
            try {
                await triggerService.addTrigger({ name });
                // Re-fetch to get ID and correct object structure
                fetchTriggers();
                // Auto-select it
                toggleTrigger(name);
            } catch (e) {
                alert("Failed to add trigger: " + e.message);
            }
        }
    };

    const addNewMed = async () => {
        const name = prompt("Enter new medication name:");
        if (name) {
            try {
                await medicationService.addMedication({ name });
                fetchMedications();
                // We can't auto-select easily without the 'default_dosage' logic which might be missing, 
                // but let's assume empty dosage is fine.
                toggleMedication({ name: name, default_dosage: '' });
            } catch (e) {
                alert("Failed to add medication: " + e.message);
            }
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setStatus({ type: 'loading', message: 'Saving...' });

        try {
            const payload = {
                ...formData,
                Pain_Level: parseInt(formData.Pain_Level),
                Medication: "", Dosage: ""
            };

            if (editingEntry && editingEntry.id) {
                await entryService.updateEntry(editingEntry.id, payload);
                setStatus({ type: 'success', message: 'Updated!' });
            } else {
                await entryService.createEntry(payload);
                setStatus({ type: 'success', message: 'Saved!' });
                if (!editingEntry) {
                    // Reset to defaults
                    setFormData(prev => ({
                        ...prev,
                        Pain_Level: 5,
                        Medications: [],
                        Triggers: '',
                        Notes: '',
                        Location: prev.Location // Keep location
                    }));
                }
            }
            // Clear msg
            setTimeout(() => setStatus({ type: '', message: '' }), 2000);
        } catch (err) {
            console.error(err);
            setStatus({ type: 'error', message: 'Failed to save.' });
        }
    };

    // --- RENDER HELPERS ---
    const isMedSelected = (name) => formData.Medications.some(m => m.name === name);
    const isTriggerSelected = (name) => {
        if (!formData.Triggers) return false;
        return formData.Triggers.split(',').map(s => s.trim()).includes(name);
    }

    return (
        <div className="log-entry-container">
            {status.message && (
                <div className={`status-message ${status.type}`}>
                    {status.message}
                </div>
            )}

            <form onSubmit={handleSubmit} className="entry-form">

                {/* 1. PAIN SLIDER */}
                <div className="pain-slider-container">
                    <div className="pain-prompt">How bad is the pain?</div>
                    <div className="pain-display">
                        <div className="pain-value" style={{
                            color: formData.Pain_Level >= 7 ? '#ff6b6b' : (formData.Pain_Level >= 4 ? '#ffd43b' : '#69db7c')
                        }}>
                            {formData.Pain_Level}
                        </div>
                        <div className="pain-label">{getPainLabel(formData.Pain_Level)}</div>
                    </div>
                    <input
                        type="range"
                        name="Pain_Level"
                        min="0" max="10"
                        value={formData.Pain_Level}
                        onChange={handleChange}
                        className="pain-slider"
                    />
                </div>

                {/* 2. MEDICATIONS (Pills) */}
                <div className="form-section">
                    <label>Medications</label>
                    <div className="pill-grid">
                        {availableMeds.map(med => (
                            <button
                                key={med.id}
                                type="button"
                                className={`pill-btn ${isMedSelected(med.name) ? 'active' : ''}`}
                                onClick={() => toggleMedication(med)}
                            >
                                {med.display_name || med.name}
                            </button>
                        ))}
                        <button type="button" className="pill-btn add-pill" onClick={() => navigate('/medications')}>
                            <Plus size={16} /> Manage
                        </button>
                    </div>
                </div>

                {/* 3. SLEEP (Segmented Control) */}
                <div className="form-section">
                    <label>Last Night's Sleep</label>
                    <div className="segmented-control">
                        {[
                            { val: '3', label: 'Good', cls: 'good' },
                            { val: '2', label: 'Fair', cls: 'fair' },
                            { val: '1', label: 'Poor', cls: 'poor' }
                        ].map(opt => (
                            <button
                                key={opt.val}
                                type="button"
                                className={`segment-btn ${opt.cls} ${String(formData.Sleep) === opt.val ? 'active' : ''}`}
                                onClick={() => setFormData(prev => ({ ...prev, Sleep: opt.val }))}
                            >
                                {opt.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* 4. ACTIVITY (Cards) */}
                <div className="form-section">
                    <label>Physical Activity</label>
                    <div className="activity-grid">
                        {[
                            { val: '0', label: 'None', icon: Armchair },
                            { val: '1', label: 'Light', icon: Footprints },
                            { val: '2', label: 'Moderate', icon: Bike },
                            { val: '3', label: 'Heavy', icon: Dumbbell }
                        ].map(opt => (
                            <button
                                key={opt.val}
                                type="button"
                                className={`activity-card ${String(formData.Physical_Activity) === opt.val ? 'active' : ''}`}
                                onClick={() => setFormData(prev => ({ ...prev, Physical_Activity: opt.val }))}
                            >
                                <opt.icon size={24} className="activity-icon" />
                                <span className="activity-label">{opt.label}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* 5. TRIGGERS (Collapsible Grouped) */}
                <div className="details-accordion">
                    <button
                        type="button"
                        className="accordion-header"
                        onClick={() => setTriggersOpen(!triggersOpen)}
                    >
                        <span>TRIGGERS {formData.Triggers ? `• ${formData.Triggers.split(',').length} Selected` : ''}</span>
                        {triggersOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                    </button>

                    {triggersOpen && (
                        <div className="accordion-content">
                            {/* Group Logic */}
                            {Object.entries(availableTriggers.reduce((acc, trig) => {
                                const cat = trig.category || 'Other';
                                if (!acc[cat]) acc[cat] = [];
                                acc[cat].push(trig);
                                return acc;
                            }, {})).sort((a, b) => {
                                // Put "Other" last, others alphabetical
                                if (a[0] === 'Other') return 1;
                                if (b[0] === 'Other') return -1;
                                return a[0].localeCompare(b[0]);
                            }).map(([category, triggers]) => (
                                <div key={category} className="trigger-group">
                                    <h4 className="trigger-category-label">{category}</h4>
                                    <div className="pill-grid">
                                        {triggers.map(trig => (
                                            <button
                                                key={trig.id}
                                                type="button"
                                                className={`pill-btn ${isTriggerSelected(trig.name) ? 'active' : ''}`}
                                                onClick={() => toggleTrigger(trig.name)}
                                            >
                                                {trig.name}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ))}

                            {/* Add New Button */}
                            <div className="trigger-group">
                                <button type="button" className="pill-btn add-pill" onClick={addNewTrigger}>
                                    <Plus size={16} /> Add Custom Trigger
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* 6. SAVE BUTTON (Primary Action) */}
                <div className="save-btn-container">
                    <button type="submit" className="submit-btn" disabled={status.type === 'loading'}>
                        {status.type === 'loading' ? <Loader2 className="animate-spin" /> : <Save size={20} />}
                        {editingEntry ? 'Update Entry' : 'Save Entry'}
                    </button>
                </div>

                {/* 7. FOOTER & DETAILS ACCORDION */}
                {/* 7. CONTEXT CARD (Unified Details) */}
                <div className="context-card">
                    <div className="context-header" onClick={() => setDetailsOpen(!detailsOpen)}>
                        <div className="context-summary">
                            <span className="info-item">
                                {getAutoCaptureText()}
                            </span>
                        </div>
                        <button type="button" className="edit-link">
                            {detailsOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </button>
                    </div>

                    {detailsOpen && (
                        <div className="context-content">
                            <div className="form-group-row">
                                <div className="form-group half">
                                    <label>Date</label>
                                    <input type="date" name="Date" value={formData.Date} onChange={handleChange} />
                                </div>
                                <div className="form-group half">
                                    <label>Time</label>
                                    <input type="time" name="Time" value={formData.Time} onChange={handleChange} />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Notes</label>
                                <textarea name="Notes" value={formData.Notes || ''} onChange={handleChange} rows="3" placeholder="Add specific notes..." />
                            </div>

                            <div className="form-group">
                                <label>Location Override</label>
                                <div className="location-input-wrapper">
                                    <button type="button" onClick={handleGetLocation} className="input-icon-btn" title="Refresh Location">
                                        {locLoading ? <Loader2 className="animate-spin" size={18} /> : <MapPin size={18} />}
                                    </button>
                                    <input type="text" name="Location" value={formData.Location || ''} onChange={handleChange} placeholder="City, State" />
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </form>
        </div>
    );
}

export default LogEntry;
