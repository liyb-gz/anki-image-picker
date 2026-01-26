# Multi-Provider Image Support Design

**Goal:** Reduce reliance on Google Images by adding Bing and DuckDuckGo as alternative providers, selectable via both configuration and the active picker UI.

## Architecture

We will implement a **Strategy Pattern** for image fetching to keep the codebase modular and extensible.

### 1. Scraper Dispatcher (`src/scraper.py`)
- The `fetch_image_urls` function will be refactored to accept a `provider` argument.
- It will route requests to specific internal functions: `_fetch_google`, `_fetch_bing`, and `_fetch_duckduckgo`.
- **Bing Logic**: Extract JSON metadata from `m` attributes in `<a>` tags.
- **DuckDuckGo Logic**: 
    1. Fetch the main search page to extract the `vqd` token.
    2. Call the `/i.js` endpoint with the token to get a JSON list of image URLs.

### 2. Configuration Persistence
- **Global Config**: Add `default_provider` (string, default: "google").
- **Note-Type Config**: Add `preferred_provider` to the model-specific configuration.
- `ConfigManager` in `src/anki_utils.py` will be updated to handle these new keys.

## UI Components

### 1. Enhanced Config Dialog (`src/gui/config_dialog.py`)
- Add a `QComboBox` labeled "Preferred Provider".
- Options: "Google", "Bing", "DuckDuckGo".
- Pre-populate based on saved note-type config or global defaults.

### 2. Interactive Picker Update (`src/gui/picker_dialog.py`)
- **Provider Selector**: Add a `QComboBox` to the top layout next to the search input.
- **Dynamic Search**: Changing the provider in the dropdown will automatically trigger a new search (`start_fetching`).
- **Session Stickiness**: The chosen provider will persist for the remainder of the current picking session.

## Data Flow
1. User starts the addon.
2. `main.py` fetches the `preferred_provider` from config and passes it to `ConfigDialog`.
3. User confirms or changes the provider.
4. `PickerDialog` receives the initial provider.
5. Every search request passes the current provider string to `scraper.fetch_image_urls`.
6. If the user changes the provider in the Picker UI, `note_data["config"]["preferred_provider"]` is updated for the session.

## Error Handling
- Each provider implementation will be wrapped in a `try...except` block.
- Specific error messages will be returned (e.g., "Bing: Rate limited") to help the user decide when to switch providers.
- The UI will display these specific errors in the status label.
