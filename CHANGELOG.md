# Changelog

All notable changes to the "Migraine Navigator" project will be documented in this file.

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
