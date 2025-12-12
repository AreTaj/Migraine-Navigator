import { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, Trash2, Edit } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './History.css';

function HistoryPage() {
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        fetchEntries();
    }, []);

    const fetchEntries = async () => {
        try {
            const response = await axios.get('/api/v1/entries');
            // Sort by Date Descending
            const sorted = response.data.sort((a, b) => new Date(b.Date) - new Date(a.Date));
            setEntries(sorted);
        } catch (err) {
            console.error(err);
            setError("Failed to load history.");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm("Are you sure you want to delete this entry?")) return;

        try {
            await axios.delete(`/api/v1/entries/${id}`);
            setEntries(entries.filter(e => e.id !== id));
        } catch (err) {
            console.error("Delete failed:", err);
            alert("Failed to delete entry.");
        }
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

    if (loading) return <div className="loading-state"><Loader2 className="animate-spin" size={48} /></div>;
    if (error) return <div className="error-state">{error}</div>;

    return (
        <div className="history-container">
            <h2>Migraine History</h2>

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
                                        {entry.Medication}
                                        {entry.Dosage && <span className="dosage-tag">{entry.Dosage}</span>}
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
                                                onClick={() => handleDelete(entry.id)}
                                                title="Delete Entry"
                                                disabled={!entry.id}
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
        </div>
    );
}

export default HistoryPage;
