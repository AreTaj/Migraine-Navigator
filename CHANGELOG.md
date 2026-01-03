# Changelog

All notable changes to the "Migraine Navigator" project will be documented in this file.


## [v0.2.5] - 2026-01-03
### Added
- **Prediction Mode Control**: Added a clear "Auto (AI) / Manual (Rules)" selector in Settings.
    - Allows users to bypass the ML Model entirely and rely on the explicit Heuristic Engine rules.
    - Useful for testing, low-powered devices, or users who prefer transparent rule-based logic over AI.
- **Settings UI Polish**: 
    - Reorganized Settings into collapsible sections ("Hybrid Engine Calibration", "App Preferences").
    - Moved "Temperature Unit" to a cleaner location.

### Fixed
- **Hourly Graph Flatline**: Restored "Truth Propagation" logic (calibrated scaling) which was lost in v0.2.3.
    - The Hourly Forecast now properly scales its magnitude to align with the Daily ML Risk Prediction.
    - If the Daily Forecast predicts High Risk (e.g., 80%), the Hourly Graph will now peak to reflect that severity, rather than showing a flat "Low Risk" heuristic baseline.

## [v0.2.4] - 2026-01-03
### Added Features
- **Advanced Triggers Registry**:
    - **Categorization**: Triggers are now organized by category (Weather, Food, Lifestyle) with collapsible headers for better readability.
    - **Smart Renaming**: Introduced an inline "Edit Mode" that safely renames triggers and automatically updates all historical log entries to match.
    - **Usage Analysis**: New visualizations grouping "Top Triggers" by category (e.g., total "Weather" impact vs. specific "Rain" impact).
    - **Auto-Migration**: Robust data migration that automatically populates the registry from historical entries for seamless upgrades.
    - **Data Consistency**: Added background synchronization to ensure usage counts always match your full log history.

### Improvements
- **Direct Forecasting**: Switched 7-Day Forecast to "Direct" mode (independent daily predictions) to fix "flatline" graphs and improve responsiveness.
- **Build Optimization**: Optimized build size (~91MB) while ensuring the full scientific stack is bundled.

### Added (Features)
- **Trigger Refinement**:
    - **Categorization**: Groups triggers by category (Weather, Food, etc.) with collapsible headers.
    - **Renaming**: Inline edit mode that also updates historical log entries.
    - **Registry**: Dedicated `/triggers` page with usage analysis and pie charts.

## [v0.2.3] - 2025-12-31
### Performance
- **Critical Fix**: Enforced strict `await` sequencing in Dashboard initialization. Core UI data (Entries, Meds) must now fully complete loading before the heavy AI components are even requested. This guarantees "Instant Load" regardless of backend thread availability.
- **Hourly Optimization**: Refactored `Dashboard.jsx` to ensure the heavy "Truth Propagation" calibration never blocks the initial render.
- **Optimized Critical Path**: `fetchCoreData` now only queries lightweight DB endpoints (Entries, Meds, Priors), ensuring the app opens essentially instantly.

## [v0.2.2] - 2025-12-31
### Added
- **24-Hour Forecast**: New hourly risk graph providing granular "Next 24 Hours" prediction alongside the 7-day view.
- **Risk Calibration**: Implemented "Truth Propagation" logic where the (Daily ML Prediction) acts as the anchor, and the (Hourly Heuristic) curve is scaled to match it. This ensures "Tomorrow's Risk" and "Hourly Peak" are mathematically consistent.
- **Visual Polish**: 
    - **Midnight Boundary**: Visual indicator (Vertical Line) on the hourly graph to separate Today vs Tomorrow.
    - **Terminology**: Renamed "Risk Probability" to "Relative Risk" to accurately reflect the conditional probability.
    - **Console Logging**: Restored real-time terminal output for backend debugging.

### Changed
- **Dashboard Layout**: Compact "Smart Cards" (200px fixed height) with cleaner form interactions to prevent layout shifts.
- **Graph Symmetry**: Standardized styling (Fonts, Colors, Grids) across both Dashboard charts for perfect visual balance.

## [v0.2.1] - 2025-12-30
### Performance (Instant Load)
- **True Instant Load**: Converted CPU-heavy Prediction endpoints to **Synchronous Handlers**. This forces execution in a background ThreadPool, unblocking the Main Event Loop. Dashboard, History, and Meds now load instantly (< 50ms) even while ML warms up on a side thread.
- **Optimized Startup**: Removed background warmup thread that was causing GIL contention.
- **Dependency Removal**: Removed `matplotlib` to eliminate 70s font-cache build on cold start.

### Fixed
- **Zero-Forecast Crash**: Removed `mmap_mode='r'` from `joblib` loading, which caused silent crashes in the packaged application.
- **Heuristic Fallback**: Implemented robust fallback logic. If ML fails or is loading, the 7-day forecast now populates using the heuristics engine instead of showing zeroes.
- **UI Polish**: Fixed excessive whitespace in Dashboard header.
- **Logs**: Moved logs from Desktop to `~/Library/Application Support/AreTaj/MigraineNavigator/`.

### Added
- **Safety Nets**: Added exponential backoff retry logic to all key API consumers (Onboarding, Settings).
- **Baseline Calibration**: Exposed "Baseline Frequency" in Settings.

## [v0.2.0] - 2025-12-29
### Added
- **Hybrid Prediction Engine**:
    - **Bayesian Heuristic Engine**: Hand-tuned expert system for "Cold Start" (New Users).
    - **Gradient Boosting ML**: Automatically takes over when N > 30 days of data is available.
- **Recursive Forecasting**: 7-Day forecasts now simulate the future day-by-day (using predicted pain as input for subsequent days) to capture "Migraine Clusters".
- **Enhanced Triggers**:
    - Rain (>0.5mm).
    - High Humidity (>70%).
    - Rapid Pressure Changes (Stability Index).
- **Onboarding Flow**: Guided setup for Baseline Risk and Sensitivity calibration.
- **Settings Tab**: UI to adjust sensitivity priors (Weather, Sleep, Strain) and manage data.
- **Data Import**: Bulk import for `.csv` and `.db` files with validation and auto-ML triggering.

### Fixed
- **7-Day Forecast Bug**: Fixed flat-line predictions by implementing recursive history appending.
- **Input Validation**: API now strictly validates `Date` and `Pain Level` on import.

### Changed
- **Testing**: Overhauled test suite to 18 robust integration tests (100% pass rate).
- **Architecture**: Separated `forecasting.heuristic_predictor` into its own module for easier maintenance.
- **License**: Adopted GNU GPLv3 to protect open-source nature while allowing for portfolio showcase.

## [v0.1.3] - 2025-12-25
### Added
- **Snooze Feature**: Added "Snooze" button to the Dashboard, allowing users to defer "Check-In" alerts for Today, 1 Week, or 2 Weeks.
- **Persistence**: Snooze preferences are saved locally and survive app restarts.
### Fixed
- **Medication Display**: Corrected bug where reminders showed "Scientific ID" (e.g. `onabotulinumtoxinA`) instead of Brand Name (e.g. `Botox`).
- **Dependency Management**: Updated `Cargo.lock` to ensure consistent Rust builds across environments.

## [v0.1.2] - 2025-12-23
### Performance
- **Sequential Loading**: Dashboard now loads instantly. The app no longer blocks on AI model initialization (2-3s delay), instead loading the UI first and showing a spinner only on the "Risk Forecast" card.
### Fixed
- **Data Integrity**: Fixed critical issue where migrating from dev -> prod caused column misalignment in the database.
- **Recovery Script**: Added tools to rescue previously corrupted history entries.
- **Sidecar Management**: Fixed conditional spawning logic that conflicted with manual dev workflows.

## [v0.1.1] - 2025-12-20
### Fixed
- **Zombie Processes**: Implemented "Stdin Monitor" (Dead Man's Switch) to guarantee Python backend termination when the main window closes.
- **Build Size**: Reduced DMG size (357MB -> 180MB) by optimizing PyInstaller exclusions (TensorFlow/Keras).
- **Startup Crash**: Fixed PID 1 crash on macOS systems.

## [v0.1.0] - 2025-12-20
### Added
- **Desktop Application**: First release of the Tauri + React + FastAPI architecture.
- **Dashboard**: Real-time "Tomorrow Risk" gauge and recent history charts.
- **Medication Registry**: Registry for Acute and Preventative medications with inventory tracking.
- **Sidecar Management**: Robust process management using `Stdin Monitor` (Dead Man's Switch) to prevent zombie Python processes.
- **Geolocation**: IP-based location tagging for Open-Meteo weather correlation.
