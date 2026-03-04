# Contributing to Migraine Navigator

## Developer Setup

1.  **Clone the Repository**
2.  **Backend Setup**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```
3.  **Frontend Setup**:
    ```bash
    cd frontend
    npm install
    ```

## Development Workflow

To run the application in development mode, you need two terminals:

**Terminal 1: Backend API**
```bash
source .venv/bin/activate
uvicorn api.main:app --reload
```
*Runs on http://127.0.0.1:8000*

**Terminal 2: Frontend App**
```bash
cd frontend
npm run dev
```
*Launches the Desktop Window*

### Automated Sidecar Management
The application features **environment-aware** backend logic:
*   **Development Mode (`npm run dev`)**: The bundled sidecar is **DISABLED**. The app connects to your manually running `uvicorn` instance (Terminal 1) and uses the local Project Database (`data/migraine_log.db`).
*   **Release Mode (Packaged App)**: The sidecar is **ENABLED**. The app automatically spawns the managed backend process and uses the System Database (`~/Library/Application Support/...`).

## Testing

To run the automated tests:

```bash
source .venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```
*Note: Agents can also run the automated `/verify` workflow for a standardized integrity check.*

## File Structure

```
Migraine Navigator/
├── api/                     # FastAPI Backend
│   ├── routes/              # API Endpoints (Entries, Analysis, Data Import, Training)
│   └── main.py              # Server Entry Point
├── frontend/                # React + Tauri Frontend
│   ├── src/                 # UI Source Code
│   │   ├── pages/           # Dashboard, LogEntry, History
│   │   └── App.jsx          # Main Router
│   └── src-tauri/           # Rust Backend (Window Management)
├── services/                # Business Logic Layer (Pure Python/SQLite)
├── forecasting/             # ML Pipeline (Training, Inference, Feature Engineering)
├── scripts/                 # Utility Scripts (api_entry.py, Packaging)
├── documentation/           # Technical Reports & Architecture
├── website/                 # Docusaurus Public Website
├── data/                    # Database (migraine_log.db)
└── ...
```

## Release Process

1.  **Build**: Run `./scripts/package_app.sh` to generate the DMG.
2.  **Verify**: Check `releases/` for the new artifact.
3.  **Upload**: Use the robust upload script to handle network instability:
    ```bash
    ./scripts/robust_upload.sh v0.3.0 releases/Migraine_Navigator_0.3.0_aarch64.dmg
    ```
