import { useState, useEffect } from 'react';
import axios from 'axios';
import { Trash2, Plus, Save, Edit2, X, Loader2 } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './Medications.css'; // We'll create this next

const COLORS = [
    '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8',
    '#82ca9d', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
    '#FFEEAD', '#D4A5A5', '#9B59B6', '#3498DB', '#E67E22',
    '#2ECC71', '#F1C40F', '#E74C3C', '#34495E', '#1ABC9C'
];

function Medications() {
    const [medications, setMedications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [editingId, setEditingId] = useState(null);
    const [deleteConfirmId, setDeleteConfirmId] = useState(null);
    const [editData, setEditData] = useState({});

    // Usage Stats State
    const [entries, setEntries] = useState([]);
    const [medTimeRange, setMedTimeRange] = useState('1y');
    const [usageStats, setUsageStats] = useState([]);

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
        fetchEntries();
    }, []);

    // Calculate Usage Stats when entries or range changes
    useEffect(() => {
        if (!entries.length || !medications.length) return;

        let startDate = new Date();
        if (medTimeRange === '1m') startDate.setMonth(startDate.getMonth() - 1);
        if (medTimeRange === '1y') startDate.setFullYear(startDate.getFullYear() - 1);
        if (medTimeRange === 'all') startDate = new Date(0);

        const filteredEntries = entries.filter(e => new Date(e.Date) >= startDate && Number(e.Pain_Level) > 0);

        // Count usage
        const counts = {};
        let total = 0;

        filteredEntries.forEach(e => {
            let meds = [];

            // Handle different data formats for Medications
            if (Array.isArray(e.Medications)) {
                // New Format: List of objects [{name: "Advil", dosage: "200mg"}, ...]
                meds = e.Medications.map(m => m.name).filter(Boolean);
            } else if (typeof e.Medications === 'string' && e.Medications.trim().length > 0) {
                // Legacy Format: "Advil, Tylenol"
                meds = e.Medications.split(',').map(s => s.trim()).filter(Boolean);
            }

            if (meds.length === 0) {
                counts['No Medication'] = (counts['No Medication'] || 0) + 1;
                total++;
            } else {
                meds.forEach(m => {
                    counts[m] = (counts[m] || 0) + 1;
                    total++;
                });
            }
        });

        const data = Object.keys(counts).map(key => ({
            name: `${key} (${total > 0 ? ((counts[key] / total) * 100).toFixed(0) + '%' : '0%'})`,
            value: counts[key]
        })).sort((a, b) => b.value - a.value);

        setUsageStats(data);
    }, [entries, medications, medTimeRange]);

    const fetchEntries = async () => {
        try {
            const res = await axios.get('/api/v1/entries');
            setEntries(res.data);
        } catch (err) {
            console.error("Failed to fetch entries for stats");
        }
    };

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
                            <label>Scientific Name (Generic)</label>
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
                            <label>Brand / Display Name (Optional)</label>
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
                                <th>Scientific Name</th>
                                <th>Brand / Display Name</th>
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

            {/* --- Usage Chart Section --- */}
            <div className="medication-stats-card" style={{ marginTop: '2rem', padding: '1.5rem', background: '#1e1e1e', borderRadius: '12px', border: '1px solid #333' }}>
                <div className="chart-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <h3>Usage Analysis</h3>
                    <div className="range-selector" style={{ background: '#333', padding: '4px', borderRadius: '6px' }}>
                        <button
                            onClick={() => setMedTimeRange('1m')}
                            style={{ background: medTimeRange === '1m' ? '#4dabf7' : 'transparent', color: medTimeRange === '1m' ? 'white' : '#888', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer' }}
                        >1M</button>
                        <button
                            onClick={() => setMedTimeRange('1y')}
                            style={{ background: medTimeRange === '1y' ? '#4dabf7' : 'transparent', color: medTimeRange === '1y' ? 'white' : '#888', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer' }}
                        >1Y</button>
                        <button
                            onClick={() => setMedTimeRange('all')}
                            style={{ background: medTimeRange === 'all' ? '#4dabf7' : 'transparent', color: medTimeRange === 'all' ? 'white' : '#888', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer' }}
                        >All</button>
                    </div>
                </div>
                <div style={{ width: '100%', height: 300 }}>
                    {usageStats.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={usageStats}
                                    cx="40%"
                                    cy="50%"
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {usageStats.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.name.startsWith('No Medication') ? '#aaa' : COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#333', border: 'none', color: '#fff' }}
                                    formatter={(value, name, props) => [`${value} (${(props.payload.percent * 100).toFixed(0)}%)`, name]}
                                />
                                <Legend layout="vertical" verticalAlign="middle" align="right" wrapperStyle={{ paddingLeft: "10px" }} />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : (
                        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#888' }}>
                            <p>No usage data for this period.</p>
                        </div>
                    )}
                </div>
            </div>
        </div >
    );
}

export default Medications;
