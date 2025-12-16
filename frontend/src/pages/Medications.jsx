import { useState, useEffect } from 'react';
import axios from 'axios';
import { Trash2, Plus, Save, Edit2, X, Loader2 } from 'lucide-react';
import './Medications.css'; // We'll create this next

function Medications() {
    const [medications, setMedications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [editingId, setEditingId] = useState(null);
    const [deleteConfirmId, setDeleteConfirmId] = useState(null);
    const [editData, setEditData] = useState({});

    // UI States
    const [saveLoading, setSaveLoading] = useState(false);

    // Scan State
    const [scanConfirming, setScanConfirming] = useState(false);
    const [scanMsg, setScanMsg] = useState(null);

    // Form State
    const [newMed, setNewMed] = useState({
        name: '',
        default_dosage: '',
        display_name: '',
        frequency: 'as_needed', // 'as_needed', 'daily', 'periodic'
        period_days: ''
    });

    useEffect(() => {
        fetchMedications();
    }, []);

    const fetchMedications = async () => {
        try {
            const res = await axios.get('/api/v1/medications');
            setMedications(res.data);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setError("Failed to fetch medications.");
            setLoading(false);
        }
    };

    const handleScanImport = async () => {
        setScanMsg("Scanning...");
        try {
            const res = await axios.post('/api/v1/medications/import');
            setScanMsg(res.data.message);
            setScanConfirming(false);
            fetchMedications();
            setTimeout(() => setScanMsg(null), 3000);
        } catch (err) {
            setScanMsg("Import failed.");
            setTimeout(() => setScanMsg(null), 3000);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setNewMed(prev => ({ ...prev, [name]: value }));
    };

    const handleAdd = async (e) => {
        e.preventDefault();
        if (!newMed.name) return;

        try {
            await axios.post('/api/v1/medications', newMed);
            setNewMed({
                name: '',
                default_dosage: '',
                display_name: '',
                frequency: 'as_needed',
                period_days: ''
            });
            fetchMedications();
        } catch (err) {
            console.error(err);
        }
    };

    const handleDeleteClick = (id) => {
        if (deleteConfirmId === id) {
            // Confirmed
            deleteMedication(id);
        } else {
            // First click
            setDeleteConfirmId(id);
            // Auto-cancel after 3s
            setTimeout(() => setDeleteConfirmId(null), 3000);
        }
    };

    const deleteMedication = async (id) => {
        try {
            await axios.delete(`/api/v1/medications/${id}`);
            setMedications(medications.filter(m => m.id !== id));
            setDeleteConfirmId(null);
        } catch (err) {
            console.error(err);
        }
    };

    // Edit Handlers
    const startEdit = (med) => {
        setEditingId(med.id);
        setEditData({ ...med });
    };

    const cancelEdit = () => {
        setEditingId(null);
        setEditData({});
    };

    const saveEdit = async () => {
        setSaveLoading(true);
        try {
            // Prepare payload - fix types and nulls
            const payload = { ...editData };

            // Sanitize strings
            if (!payload.name) payload.name = ""; // Should be blocked by HTML required, but safe to spec
            if (payload.display_name === null || payload.display_name === undefined) payload.display_name = "";
            if (payload.default_dosage === null || payload.default_dosage === undefined) payload.default_dosage = "";

            // Sanitize integers
            if (payload.period_days === "") payload.period_days = null;
            if (payload.period_days) payload.period_days = parseInt(payload.period_days);

            console.log("Saving payload:", payload); // Debug log

            await axios.put(`/api/v1/medications/${editingId}`, payload);

            // Update local state with the corrected payload
            setMedications(medications.map(m => m.id === editingId ? payload : m));
            setEditingId(null);
            setEditData({});
            setScanMsg("Saved!");
            setTimeout(() => setScanMsg(null), 2000);
        } catch (err) {
            console.error("Save Error:", err);
            const errMsg = err.response?.data?.detail
                ? (typeof err.response.data.detail === 'object' ? JSON.stringify(err.response.data.detail) : err.response.data.detail)
                : err.message;
            setScanMsg(`Error: ${errMsg}`);
            // Don't clear error immediately so user can read it
            setTimeout(() => setScanMsg(null), 5000);
        } finally {
            setSaveLoading(false);
        }
    };

    const handleEditChange = (e) => {
        const { name, value } = e.target;
        setEditData(prev => ({ ...prev, [name]: value }));
    };

    return (
        <div className="medications-container">
            <h2>Medications Registry</h2>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <p className="subtitle" style={{ margin: 0 }}>Manage usage and defaults for your medications.</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {scanMsg && (
                        <span style={{
                            fontSize: '0.85rem',
                            color: (scanMsg.startsWith("Error") || scanMsg.includes("fail")) ? '#ef4444' : '#10b981',
                            fontWeight: 500
                        }}>
                            {scanMsg}
                        </span>
                    )}
                    <button
                        onClick={scanConfirming ? handleScanImport : () => setScanConfirming(true)}
                        onMouseLeave={() => !scanMsg && setScanConfirming(false)}
                        style={{
                            background: scanConfirming ? '#f59e0b' : '#3b82f6',
                            border: 'none',
                            padding: '8px 12px',
                            borderRadius: '6px',
                            color: 'white',
                            cursor: 'pointer',
                            fontSize: '0.85rem',
                            transition: 'background 0.2s'
                        }}
                    >
                        {scanConfirming ? "Confirm Import?" : "Scan & Import History"}
                    </button>
                </div>
            </div>

            <div className="add-medication-card">
                <h3>Add New Medication</h3>
                <form onSubmit={handleAdd} className="add-form">
                    <div className="form-row">
                        <div className="form-group">
                            <label>Name (Generic)</label>
                            <input
                                type="text"
                                name="name"
                                value={newMed.name}
                                onChange={handleInputChange}
                                placeholder="e.g. Ibuprofen"
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Display Name (Optional)</label>
                            <input
                                type="text"
                                name="display_name"
                                value={newMed.display_name}
                                onChange={handleInputChange}
                                placeholder="e.g. Advil"
                            />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label>Default Dosage</label>
                            <input
                                type="text"
                                name="default_dosage"
                                value={newMed.default_dosage}
                                onChange={handleInputChange}
                                placeholder="e.g. 200mg"
                            />
                        </div>
                        <div className="form-group">
                            <label>Frequency</label>
                            <select name="frequency" value={newMed.frequency} onChange={handleInputChange}>
                                <option value="as_needed">As Needed (Acute)</option>
                                <option value="daily">Daily (Preventative)</option>
                                <option value="periodic">Periodic (Injection)</option>
                            </select>
                        </div>
                    </div>

                    {newMed.frequency === 'periodic' && (
                        <div className="form-group">
                            <label>Period (Days)</label>
                            <input
                                type="number"
                                name="period_days"
                                value={newMed.period_days}
                                onChange={handleInputChange}
                                placeholder="e.g. 90"
                            />
                        </div>
                    )}

                    <div className="form-group full">
                        <button type="submit" className="add-btn">
                            <Plus size={18} /> Add Medication
                        </button>
                    </div>
                </form>
            </div>

            <div className="medications-list">
                <h3>Your Medications</h3>
                {loading ? <p>Loading...</p> : (
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Display As</th>
                                <th>Default Dosage</th>
                                <th>Frequency</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {medications.map(med => (
                                <tr key={med.id}>
                                    {editingId === med.id ? (
                                        // Edit Mode Rows
                                        <>
                                            <td><input name="name" value={editData.name} onChange={handleEditChange} className="edit-input" /></td>
                                            <td><input name="display_name" value={editData.display_name || ''} onChange={handleEditChange} className="edit-input" /></td>
                                            <td><input name="default_dosage" value={editData.default_dosage || ''} onChange={handleEditChange} className="edit-input" /></td>
                                            <td>
                                                <select name="frequency" value={editData.frequency} onChange={handleEditChange} className="edit-input">
                                                    <option value="as_needed">Acute</option>
                                                    <option value="daily">Daily</option>
                                                    <option value="periodic">Periodic</option>
                                                </select>
                                                {editData.frequency === 'periodic' && (
                                                    <input
                                                        type="number"
                                                        name="period_days"
                                                        value={editData.period_days || ''}
                                                        onChange={handleEditChange}
                                                        placeholder="Days"
                                                        style={{ width: '60px', marginTop: '4px' }}
                                                    />
                                                )}
                                            </td>
                                            <td>
                                                <div style={{ display: 'flex', gap: '8px' }}>
                                                    <button className="icon-btn save" onClick={saveEdit} title="Save" disabled={saveLoading}>
                                                        {saveLoading ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                                                    </button>
                                                    <button className="icon-btn cancel" onClick={cancelEdit} title="Cancel" disabled={saveLoading}>
                                                        <X size={16} />
                                                    </button>
                                                </div>
                                            </td>
                                        </>
                                    ) : (
                                        // View Mode Rows
                                        <>
                                            <td>{med.name}</td>
                                            <td>{med.display_name || '-'}</td>
                                            <td>{med.default_dosage || '-'}</td>
                                            <td>
                                                <span className={`freq-tag ${med.frequency}`}>
                                                    {med.frequency === 'as_needed' && 'Acute'}
                                                    {med.frequency === 'daily' && 'Daily'}
                                                    {med.frequency === 'periodic' && `Every ${med.period_days} days`}
                                                </span>
                                            </td>
                                            <td>
                                                <div style={{ display: 'flex', gap: '8px' }}>
                                                    <button className="icon-btn edit" onClick={() => startEdit(med)} title="Edit">
                                                        <Edit2 size={16} />
                                                    </button>

                                                    {deleteConfirmId === med.id ? (
                                                        <button
                                                            className="icon-btn delete-confirm"
                                                            onClick={() => handleDeleteClick(med.id)}
                                                            style={{ background: '#ef4444', color: 'white', width: 'auto', padding: '4px 8px', fontSize: '0.75rem' }}
                                                        >
                                                            Confirm?
                                                        </button>
                                                    ) : (
                                                        <button className="icon-btn delete" onClick={() => handleDeleteClick(med.id)} title="Delete">
                                                            <Trash2 size={16} />
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                        </>
                                    )}
                                </tr>
                            ))}
                            {medications.length === 0 && (
                                <tr>
                                    <td colSpan="5" className="empty-state">No medications added yet.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                )}
            </div>
        </div >
    );
}

export default Medications;
