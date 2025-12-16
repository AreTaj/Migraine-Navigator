import { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, Trash2, Edit } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './History.css';

function HistoryPage() {
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [deleteId, setDeleteId] = useState(null); // ID of entry to delete
    const [medDisplayMap, setMedDisplayMap] = useState({}); // New state for mapping
    // Filters
    const [timeRange, setTimeRange] = useState('30d'); // 7d, 30d, 90d, 180d, 1y

    const navigate = useNavigate();

    useEffect(() => {
        // Fetch Metadata (Generic->Display Map)
        const fetchMeds = async () => {
            try {
                const res = await axios.get('/api/v1/medications');
                const map = {};
                res.data.forEach(m => {
                    map[m.name] = m.display_name || m.name;
                });
                setMedDisplayMap(map);
            } catch (e) {
                console.warn("Failed to load generic->display map", e);
            }
        };
        fetchMeds();
    }, []);

    useEffect(() => {
        fetchEntries();
    }, [timeRange]);

    const getDateRange = () => {
        const end = new Date();
        let start = new Date();

        switch (timeRange) {
            case '7d': start.setDate(end.getDate() - 7); break;
            case '30d': start.setDate(end.getDate() - 30); break;
            case '90d': start.setDate(end.getDate() - 90); break;
            case '180d': start.setDate(end.getDate() - 180); break;
            case '1y': start.setFullYear(end.getFullYear() - 1); break;
            default: start.setDate(end.getDate() - 30);
        }

        return {
            startStr: start.toISOString().split('T')[0],
            endStr: end.toISOString().split('T')[0]
        };
    };

    const fetchEntries = async () => {
        setLoading(true);
        try {
            const { startStr, endStr } = getDateRange();
            let url = '/api/v1/entries';
            const params = new URLSearchParams();
            if (startStr) params.append('start_date', startStr);
            if (endStr) params.append('end_date', endStr);

            const response = await axios.get(url, { params });
            // API now returns sorted data, but double check
            setEntries(response.data);
        } catch (err) {
            console.error(err);
            setError("Failed to load history.");
        } finally {
            setLoading(false);
        }
    };

    const confirmDelete = (e, id) => {
        e.stopPropagation();
        setDeleteId(id);
    };

    const performDelete = async () => {
        if (!deleteId) return;

        try {
            await axios.delete(`/api/v1/entries/${deleteId}`);
            setEntries(prev => prev.filter(e => e.id !== deleteId));
            setDeleteId(null); // Close modal
        } catch (err) {
            console.error("Delete failed:", err);
            // Fallback to console since alert is broken
        }
    };

    const cancelDelete = () => {
        setDeleteId(null);
    };

    const handleEdit = (entry) => {
        navigate('/log', { state: { entry } });
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return '';
        return new Date(dateStr).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    const getSleepLabel = (val) => {
        const v = String(val).toLowerCase();
        if (v === '1' || v === 'poor') return 'Poor';
        if (v === '2' || v === 'fair') return 'Fair';
        if (v === '3' || v === 'good') return 'Good';
        return val; // Fallback
    };

    const getActivityLabel = (val) => {
        const v = String(val).toLowerCase();
        if (v === '0' || v === 'none') return 'None';
        if (v === '1' || v === 'light') return 'Light';
        if (v === '2' || v === 'moderate') return 'Mod';
        if (v === '3' || v === 'heavy') return 'Heavy';
        return val;
    };

    const getMedDisplayName = (genericName) => {
        return medDisplayMap[genericName] || genericName;
    };

    if (loading) return <div className="loading-state"><Loader2 className="animate-spin" size={48} /></div>;
    if (error) return <div className="error-state">{error}</div>;

    return (
        <div className="history-container">
            <div className="history-header">
                <h2>Migraine History</h2>
                <div className="filter-controls">
                    <label>Period:</label>
                    <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
                        <option value="7d">Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                        <option value="90d">Last 3 Months</option>
                        <option value="180d">Last 6 Months</option>
                        <option value="1y">Last Year</option>
                    </select>
                </div>
            </div>

            <div className="table-wrapper">
                <table className="history-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Pain</th>
                            <th>Medication</th>
                            <th>Sleep</th>
                            <th>Activity</th>
                            <th>Triggers</th>
                            <th>Location</th>
                            <th>Notes</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {entries.length === 0 ? (
                            <tr><td colSpan="10" className="no-data">No entries found</td></tr>
                        ) : (
                            entries.map((entry, index) => (
                                <tr key={entry.id || index}>
                                    <td>{formatDate(entry.Date)}</td>
                                    <td>{entry.Time}</td>
                                    <td>
                                        <span className={`pain-badge pain-${entry.Pain_Level}`}>
                                            {entry.Pain_Level}
                                        </span>
                                    </td>
                                    <td>
                                        {/* New Format */}
                                        {entry.Medications && entry.Medications.length > 0 ? (
                                            <div className="meds-tags">
                                                {entry.Medications.map((m, i) => (
                                                    <span key={i} className="med-tag">
                                                        {getMedDisplayName(m.name)} {m.dosage ? `(${m.dosage})` : ''}
                                                    </span>
                                                ))}
                                            </div>
                                        ) : (
                                            /* Legacy Fallback */
                                            <>
                                                {entry.Medication}
                                                {entry.Dosage && <span className="dosage-tag">{entry.Dosage}</span>}
                                            </>
                                        )}
                                    </td>
                                    <td>{getSleepLabel(entry.Sleep)}</td>
                                    <td>{getActivityLabel(entry['Physical Activity'] || entry.Physical_Activity)}</td>
                                    <td className="truncate-cell" title={entry.Triggers}>{entry.Triggers}</td>
                                    <td className="truncate-cell" title={entry.Location}>{entry.Location}</td>
                                    <td className="notes-cell" title={entry.Notes}>{entry.Notes}</td>
                                    <td>
                                        <div className="action-buttons">
                                            <button
                                                className="action-btn edit-btn"
                                                onClick={() => handleEdit(entry)}
                                                title="Edit Entry"
                                            >
                                                <Edit size={16} />
                                            </button>
                                            <button
                                                className="action-btn delete-btn"
                                                onClick={(e) => confirmDelete(e, entry.id)}
                                                title={`Delete Entry ${entry.id}`}
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Confirmation Modal */}
            {deleteId && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    backgroundColor: 'rgba(0,0,0,0.7)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    zIndex: 1000
                }}>
                    <div style={{
                        backgroundColor: '#1e293b', padding: '2rem', borderRadius: '12px',
                        border: '1px solid #334155', maxWidth: '400px', width: '90%'
                    }}>
                        <h3 style={{ marginTop: 0 }}>Confirm Deletion</h3>
                        <p style={{ color: '#94a3b8' }}>Are you sure you want to delete this entry? This action cannot be undone.</p>
                        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                            <button
                                onClick={cancelDelete}
                                style={{
                                    padding: '8px 16px', background: 'transparent', color: '#cbd5e1',
                                    border: '1px solid #475569', borderRadius: '6px', cursor: 'pointer'
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={performDelete}
                                style={{
                                    padding: '8px 16px', background: '#ef4444', color: 'white',
                                    border: 'none', borderRadius: '6px', cursor: 'pointer'
                                }}
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default HistoryPage;
