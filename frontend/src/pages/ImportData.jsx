import React, { useState } from 'react';
import { Upload, Database, FileSpreadsheet, Check } from 'lucide-react';
import axios from '../services/apiClient';
import '../App.css';

const ImportData = () => {
    const [file, setFile] = useState(null);
    const [type, setType] = useState('csv'); // or 'db'
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
            const endpoint = type === 'csv' ? "/api/v1/data/import/csv" : "/api/v1/data/import/db";
            const res = await axios.post(endpoint, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResult(res.data);
            setStatus("success");
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
                        <p>Processed {result.total_rows} entries.</p>
                        {result.training_triggered && (
                            <p style={{ fontWeight: 'bold' }}>✨ AI Model Trained & Activated! ✨</p>
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
