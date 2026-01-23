# Anki Image Adder Improvements Design

**Date:** 2026-01-23
**Status:** Validated

## 1. Persistence & Configuration

### Architecture
- **Global Config:** Use Anki's `mw.addonManager` to store global settings in `config.json`.
  - `search_suffix`: Default string to append to searches (e.g., "anime").
  - `max_width`: Default maximum width (default: 320).
  - `max_height`: Default maximum height (default: 320).
- **Note Type Mappings:** A persistent map in the config file linking `Note Type Name` to its last-used `source_field`, `target_field`, and `mode`.

### Data Flow
1. Add-on starts -> Load `config.json`.
2. `ConfigDialog` opens -> Pre-populate fields based on the Note Type mapping.
3. User clicks "Start" -> Update mapping for that Note Type in `config.json` and save.

## 2. Enhanced Search & Sizing

### Search Suffix
- **UI:** Add a "Search Suffix" QLineEdit to `ConfigDialog`.
- **Logic:** The effective search term will be `source_field_content + " " + search_suffix`.
- **Flexibility:** Changes in `ConfigDialog` only affect the current session unless the user saves them globally (via Anki Add-on config).

### Dual Constraints
- **Logic:** Support both `max_width` and `max_height` in the image saving process.
- **Implementation:** Generated `<img>` tags will use CSS: `style="max-width: {w}px; max-height: {h}px;"`. This ensures proportional scaling within a bounding box.

## 3. Pagination (Load More)

### Logic
- **Offset Tracking:** `PickerDialog` will track a `current_offset` (starting at 0).
- **Scraper Update:** Modify `fetch_image_urls` to accept a `start` parameter.
- **UI:** Add a "Load More" button at the bottom of the image grid.
- **Interaction:**
  - Clicking "Load More" fetches the next 8-12 results.
  - New images are **appended** to the `QGridLayout`.
  - If no more results are found, the button is disabled.

## 4. Testing & Verification
- Unit tests for `ConfigManager` to ensure Note Type mappings persist correctly.
- Verification of CSS scaling with various image aspect ratios.
- Mock scraper tests to verify offset-based fetching.
