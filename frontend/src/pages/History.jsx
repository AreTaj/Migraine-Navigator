import { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, Trash2, Edit } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './History.css';

function HistoryPage() {
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [deleteId, setDeleteId] = useState(null);
    const [medDisplayMap, setMedDisplayMap] = useState({}); // New state for mapping
    const [timeRange, setTimeRange] = useState('30d');

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

    // ... (skip unchanged helper functions like formatDate, getSleepLabel, etc.) ...

    const getMedDisplayName = (genericName) => {
        return medDisplayMap[genericName] || genericName;
    };

    // ... (inside the table render) ...

    {
        entry.Medications && entry.Medications.length > 0 ? (
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
    )
    }
                                    </td >
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
                                </tr >
                            ))
                        )
}
                    </tbody >
                </table >
            </div >

    {/* Confirmation Modal */ }
{
    deleteId && (
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
    )
}
        </div >
    );
}

export default HistoryPage;
