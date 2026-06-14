# EPI Vision Mobile - Architecture and Usage

## Architecture

- Uni-app front-end only. Backend remains the existing Python service.
- App uses a tab bar with four core pages: Dashboard, History, Materials, Simulator.
- A lightweight API wrapper lives in `common/api.js` and reads the base URL from `common/config.js` (default: `http://127.0.0.1:5050`).
- Pages call the wrapper and render mobile-friendly cards.
- Dataset list is hard-coded in `common/datasets.js` to avoid inflating app size while keeping data on the backend.

Key files:
- `pages.json`: route definitions and tab bar configuration.
- `manifest.json`: app metadata and Android build settings.
- `common/config.js`: backend base URL.
- `common/api.js`: shared request helpers.

## Usage

### Configure backend

1. Open `common/config.js`.
2. Set `baseUrl` to your backend address, for example `http://192.168.1.10:5050`.

### Run in HBuilderX (recommended for fast start)

1. Open the `mobile-app` folder in HBuilderX.
2. Select Run -> Run to Android emulator or Run to device.

### Run with CLI (optional)

If you prefer the CLI workflow, initialize the dependencies in this folder with the official uni-app Vue CLI template, then copy the source files into it. The HBuilderX workflow is faster for quick validation.

### Connect APIs

- Endpoints are aligned to the Flask routes (`/api/health`, `/api/materials`, `/api/analyze`, etc.).
- Use the page methods to call the APIs and render response data.

### Dataset import note

- The App runtime (Android) does not support `uni.chooseFile` yet. Use the web client to upload datasets, then access them from the app.

### Build Android

1. In HBuilderX, open the project.
2. Choose Build -> Build App (Android).
3. Configure signing and permissions if needed.

## Next Steps

- Replace placeholder cards with real content from your existing API.
- Add loading, empty, and error states for each page.
- Confirm Android network security if your backend is using HTTP.
