import React, { useState } from 'react';
import { Upload, Database, FileSpreadsheet, Check } from 'lucide-react';
import axios from '../services/apiClient';
import '../App.css';

const ImportData = () => {
    const [file, setFile] = useState(null);
    const [type, setType] = useState('csv'); // or 'db'
    const [importMode, setImportMode] = useState('merge'); // 'merge' or 'separate'
    const [status, setStatus] = useState("idle"); // idle, uploading, success, error
    const [result, setResult] = useState(null);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
        setStatus("idle");
    };

    const handleUpload = async () => {
        if (!file) return;
        setStatus("uploading");

        const formData = new FormData();
        formData.append("file", file);

        try {
            let endpoint = "/api/v1/data/import/csv";
            if (type === 'db') {
                endpoint = importMode === 'separate' ? "/api/v1/data/import/db-separate" : "/api/v1/data/import/db";
            }

            const res = await axios.post(endpoint, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResult(res.data);
            setStatus("success");

            // If importing a separate DB, automatically switch to it
            if (type === 'db' && importMode === 'separate' && res.data.database_name) {
                localStorage.setItem('active_db', res.data.database_name);
            }
        } catch (error) {
            console.error(error);
            setStatus("error");
        }
    };

    return (
        <div style={{ padding: '2rem' }}>
            <h2>Import Data</h2>
            <p className="text-muted">Restore a backup (.db) or import from Excel/CSV.</p>

            <div className="card" style={{ marginTop: '1rem' }}>
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
                    <button
                        className={`btn-option ${type === 'csv' ? 'selected' : ''}`}
                        onClick={() => setType('csv')}
                        style={{ flex: 1, padding: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                    >
                        <FileSpreadsheet /> CSV Import
                    </button>
                    <button
                        className={`btn-option ${type === 'db' ? 'selected' : ''}`}
                        onClick={() => setType('db')}
                        style={{ flex: 1, padding: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                    >
                        <Database /> SQLite Backup
                    </button>
                </div>

                {type === 'db' && (
                    <div style={{
                        marginBottom: '2rem',
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                        gap: '1rem',
                        background: '#222',
                        padding: '1.25rem',
                        borderRadius: '8px',
                        border: '1px solid #333'
                    }}>
                        <label style={{
                            display: 'grid',
                            gridTemplateColumns: '24px 1fr',
                            gap: '12px',
                            alignItems: 'start',
                            cursor: 'pointer',
                            padding: '0.75rem',
                            borderRadius: '6px',
                            background: importMode === 'merge' ? 'rgba(255,255,255,0.03)' : 'transparent',
                            border: importMode === 'merge' ? '1px solid #444' : '1px solid transparent',
                            transition: 'all 0.2s'
                        }}>
                            <input
                                type="radio"
                                name="importMode"
                                value="merge"
                                checked={importMode === 'merge'}
                                onChange={() => setImportMode('merge')}
                                style={{ marginTop: '5px', flexShrink: 0 }}
                            />
                            <div style={{ minWidth: 0 }}>
                                <strong style={{ display: 'block', marginBottom: '4px', color: '#fff' }}>Merge data</strong>
                                <div className="text-muted" style={{ fontSize: '0.85rem', lineHeight: '1.5' }}>
                                    Combine with current active database, skipping duplicates.
                                </div>
                            </div>
                        </label>
                        <label style={{
                            display: 'grid',
                            gridTemplateColumns: '24px 1fr',
                            gap: '12px',
                            alignItems: 'start',
                            cursor: 'pointer',
                            padding: '0.75rem',
                            borderRadius: '6px',
                            background: importMode === 'separate' ? 'rgba(255,255,255,0.03)' : 'transparent',
                            border: importMode === 'separate' ? '1px solid #444' : '1px solid transparent',
                            transition: 'all 0.2s'
                        }}>
                            <input
                                type="radio"
                                name="importMode"
                                value="separate"
                                checked={importMode === 'separate'}
                                onChange={() => setImportMode('separate')}
                                style={{ marginTop: '5px', flexShrink: 0 }}
                            />
                            <div style={{ minWidth: 0 }}>
                                <strong style={{ display: 'block', marginBottom: '4px', color: '#fff' }}>Load as separate Database</strong>
                                <div className="text-muted" style={{ fontSize: '0.85rem', lineHeight: '1.5' }}>
                                    Keep data isolated. You can switch to it in Settings.
                                </div>
                            </div>
                        </label>
                    </div>
                )}

                <div
                    style={{
                        border: '2px dashed #444',
                        padding: '3rem',
                        textAlign: 'center',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        background: '#222'
                    }}
                    onClick={() => document.getElementById('fileInput').click()}
                >
                    <input
                        id="fileInput"
                        type="file"
                        accept={type === 'csv' ? ".csv" : ".db,.sqlite"}
                        onChange={handleFileChange}
                        style={{ display: 'none' }}
                    />

                    {file ? (
                        <div>
                            <Check size={48} color="var(--success-color)" style={{ display: 'block', margin: '0 auto 1rem' }} />
                            <p>{file.name}</p>
                            <small>{Math.round(file.size / 1024)} KB</small>
                        </div>
                    ) : (
                        <div>
                            <Upload size={48} style={{ display: 'block', margin: '0 auto 1rem', opacity: 0.5 }} />
                            <p>Click to Select File</p>
                        </div>
                    )}
                </div>

                {file && status !== "success" && (
                    <button
                        className="primary-btn"
                        onClick={handleUpload}
                        disabled={status === "uploading"}
                        style={{ width: '100%', marginTop: '2rem' }}
                    >
                        {status === "uploading" ? "Importing..." : "Start Import"}
                    </button>
                )}

                {status === "success" && result && (
                    <div className="alert success" style={{ marginTop: '2rem' }}>
                        <h4>Import Successful!</h4>
                        {result.message ? (
                            <p>{result.message}</p>
                        ) : (
                            <>
                                <p>✅ Imported <strong>{result.imported_rows}</strong> new entries.</p>
                                {result.skipped_rows > 0 && (
                                    <p style={{ color: '#94a3b8' }}>⏭ Skipped <strong>{result.skipped_rows}</strong> duplicate entries.</p>
                                )}
                                {result.training_triggered && (
                                    <p style={{ fontWeight: 'bold' }}>✨ AI Model Trained & Activated! ✨</p>
                                )}
                            </>
                        )}
                        {type === 'db' && importMode === 'separate' && (
                            <button
                                className="primary-btn"
                                style={{ marginTop: '1rem' }}
                                onClick={() => window.location.href = '/'}
                            >
                                Go to Dashboard
                            </button>
                        )}
                    </div>
                )}

                {status === "error" && (
                    <div className="alert error" style={{ marginTop: '2rem' }}>
                        Import Failed. Please check the file format.
                    </div>
                )}

            </div>
        </div>
    );
};

export default ImportData;
