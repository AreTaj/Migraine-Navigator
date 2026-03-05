import axios from 'axios';

// Detect if running in Tauri environment
const isTauri =
    !!(window.__TAURI_INTERNALS__ || window.__TAURI__) ||
    window.location.protocol === 'tauri:' ||
    window.location.hostname === 'tauri.localhost';

const apiClient = axios.create({
    baseURL: '',
    timeout: 30000,
});

// --- Dynamic Port Discovery (Tauri Production Only) ---
// Create a gate that holds requests until the backend port is known.
let _portReady = null;
if (isTauri) {
    _portReady = new Promise((resolve) => {
        import('@tauri-apps/api/event').then(({ listen }) => {
            listen('backend-started', (event) => {
                const port = event.payload.port;
                apiClient.defaults.baseURL = `http://127.0.0.1:${port}`;
                console.log(`Backend started on dynamic port: ${port}`);
                resolve();
            });
        }).catch((err) => {
            console.warn('Tauri event API not available:', err);
            resolve(); // Don't block forever if event API fails
        });
    });
}

// Request interceptor: in Tauri mode, wait for port before sending any request
apiClient.interceptors.request.use(async (config) => {
    if (_portReady) {
        await _portReady;
        // CRITICAL: Requests suspended here will have empty config.baseURL from when they started. 
        // We must update them to the newly discovered baseURL.
        config.baseURL = apiClient.defaults.baseURL;
    }

    const isTester = localStorage.getItem('tester_mode') === 'true';
    if (isTester) {
        config.headers['X-Tester-Mode'] = 'true';
    }
    return config;
});

// Retry logic for slow startup (Sidecar takes ~8s to boot)
apiClient.interceptors.response.use(null, async (error) => {
    const config = error.config;

    if (!config || !config.retryCount) {
        config.retryCount = 0;
    }

    const MAX_RETRIES = 15;

    if (config.retryCount < MAX_RETRIES && (!error.response || error.code === 'ERR_NETWORK')) {
        config.retryCount += 1;

        const delay = Math.min(500 * (2 ** (config.retryCount - 1)), 3000);

        console.log(`Backend likely starting... Retrying request (${config.retryCount}/${MAX_RETRIES}) in ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));

        return apiClient(config);
    }

    return Promise.reject(error);
});

export default apiClient;
