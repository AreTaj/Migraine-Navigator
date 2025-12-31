import axios from 'axios';

// Detect if running in Tauri environment
// Check for specific Tauri protocols or internals
const isTauri =
    !!(window.__TAURI_INTERNALS__ || window.__TAURI__) ||
    window.location.protocol === 'tauri:' ||
    window.location.hostname === 'tauri.localhost';

const apiClient = axios.create({
    baseURL: isTauri
        ? 'http://127.0.0.1:8000' // Direct to sidecar in packaged app
        : '',                     // Proxy via Vite in dev
    timeout: 30000, // Higher timeout for slow cold starts
});

// Retry logic for slow startup (Sidecar takes ~8s to boot)
apiClient.interceptors.response.use(null, async (error) => {
    const config = error.config;

    // Check if we should retry (idempotent methods or safe to retry)
    // and if it's a network error (backend not up yet)
    if (!config || !config.retryCount) {
        config.retryCount = 0;
    }

    const MAX_RETRIES = 15; // Try for ~45 seconds total

    if (config.retryCount < MAX_RETRIES && (!error.response || error.code === 'ERR_NETWORK')) {
        config.retryCount += 1;

        // Exponential backoff: 500ms, 1000ms, 2000ms... capped at 3s
        const delay = Math.min(500 * (2 ** (config.retryCount - 1)), 3000);

        console.log(`Backend likely starting... Retrying request (${config.retryCount}/${MAX_RETRIES}) in ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));

        return apiClient(config);
    }

    return Promise.reject(error);
});

export default apiClient;
