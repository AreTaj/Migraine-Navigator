import axios from 'axios';

// Detect if running in Tauri environment
// In v2, window.__TAURI_INTERNALS__ is often used, but we can also check for the specific plugin keys if needed.
const isTauri = !!(window.__TAURI_INTERNALS__ || window.__TAURI__);

const apiClient = axios.create({
    baseURL: isTauri
        ? 'http://localhost:8000' // Direct to sidecar in packaged app
        : '',                     // Proxy via Vite in dev
});

export default apiClient;
