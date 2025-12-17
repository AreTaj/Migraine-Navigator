# Migraine Navigator

Migraine Navigator is a comprehensive tool designed to help users **track**, **analyze**, and **predict** migraine occurrences. 

> **Alpha v1.0 Update**: The application has been migrated from a legacy Python GUI to a modern **Desktop Application** powered by **Tauri**, **React**, and **FastAPI**.

> **Disclaimer:** This software and its outputs are for informational and educational purposes only and are not intended to diagnose, treat, cure, or prevent any disease. Always consult a qualified healthcare provider for medical advice.

## Features

- **Enhanced Dashboard:** 
    - **Live Prediction**: See your "Tomorrow Risk" based on weather forecasts and recent history.
    - **7-Day Forecast**: Forward-looking probability chart with "Risk" scores to help plan your week ahead.
    - **Offline Resilience**: Automatically falls back to the most recent known weather data if the internet is down, with visual alerts.
    - **Smart Metrics**: Track "Avg Days/Month" and pain severity trends.
    - **Interactive Trends**: Filter by 1M (Severity View), 1Y, or Full History (Frequency View).
    - **Medication Analysis**: Consolidated view with "Donut Style" visualization, extended color palette, and "Pain-Based" usage tracking (ignores pain-free days).
- **Detailed Logging:** 
    - **Smart Geolocation**: IP-based location tagging for accurate weather correlation without intrusive permissions.
    - **Medication Management**: Dedicated registry for tracking doses, frequencies, and stock.
    - **Log Date, Time, Pain Level, Sleep Quality, Physical Activity, Triggers.**
- **History Management:** 
    - **Performance Optimized**: Date-based filtering (Last 7 Days, 30 Days, etc.) for instant loading.
    - **TimeZone Aware**: Intelligent date handling ensuring "Today" means *your* today, regardless of when you log.
    - Full searchable/sortable history table with **Edit** and **Delete** capabilities.
- **Modern Architecture:** 
    - Built on robust SQLite database.
    - **Reactive Caching**: Instant dashboard updates upon data modification, with 1-hour caching for stability.
    - Fast and lightweight Desktop experience.

## Screenshots

![Dashboard View](screenshots/dashboard.png)
*Real-time predictive dashboard with weather integration and trends analysis.*

![Log Entry View](screenshots/log.png)
*Streamlined data entry with standardized inputs.*

![History View](screenshots/history.png)
*Detailed log management and searching.*

![Medications Registry](screenshots/medications.png)
*Centralized registry for managing medication types, dosages, and frequencies (Acute vs. Preventative).*

## Installation

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Rust** (for Tauri)

### Setup

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

## Usage

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
npm run tauri dev
```
*Launches the Desktop Window*

## File Structure

```
Migraine Navigator/
├── api/                     # FastAPI Backend
│   ├── routes/              # API Endpoints (Entries, Analysis)
│   └── main.py              # Server Entry Point
├── frontend/                # React + Tauri Frontend
│   ├── src/                 # UI Source Code
│   │   ├── pages/           # Dashboard, LogEntry, History
│   │   └── App.jsx          # Main Router
│   └── src-tauri/           # Rust Backend (Window Management)
├── services/                # Business Logic Layer
├── data/                    # Database (migraine_log.db)
└── ...
```

## Testing

Backend tests are available to verify API functionality:
```bash
python -m unittest discover tests
```

## Future Roadmap (v1.2)
- **Packaging**: Building standalone installers (`.dmg`, `.exe`).

## License

Copyright © 2025 Aresh Tajvar. All Rights Reserved.

Unauthorized copying of this file, via any medium is strictly prohibited.
The software is proprietary and confidential.

## Acknowledgements

Special thanks to my neurologist, Dr. Jack Schim, for his guidance, wisdom, and moral support to pursue this project. Dr. Schim did not directly participate in development and this does not constitute an endorsement or medical advice.

- [Tauri](https://tauri.app/) - For the lightweight desktop framework.
- [React](https://react.dev/) - For the modern UI library.
- [FastAPI](https://fastapi.tiangolo.com/) - For the high-performance backend.
- [Recharts](https://recharts.org/) - For the beautiful data visualization.
- [Meteostat](https://dev.meteostat.net/) - For historical weather data.
- [Open-Meteo](https://open-meteo.com/) - For live weather forecasts.

## Author

- **Aresh Tajvar**
- **GitHub**: [github.com/AreTaj](https://github.com/AreTaj)
- **LinkedIn**: [linkedin.com/in/aresh-tajvar](https://linkedin.com/in/aresh-tajvar)
