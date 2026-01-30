# Anki Image Picker

Quickly add images from web search to your Anki flashcards. Select multiple notes, pick images interactively from a grid, and move on - no blind batch downloads.

## Features

- **Interactive selection** - See thumbnails before adding, pick with a click or keyboard (1-8)
- **Batch processing** - Select multiple notes, process them one by one
- **Multiple search providers** - Google, Bing, or DuckDuckGo
- **Smart search** - Auto-strips HTML and cloze markers from search terms
- **Field context** - Use other fields to refine searches on the fly
- **Session control** - Go back, skip, abort, or revert all changes

## Installation

### From AnkiWeb (Recommended)
1. Open Anki → Tools → Add-ons → Get Add-ons...
2. Enter code: `647779979`
3. Restart Anki

### Manual Installation (to be added)
1. Download the latest release from GitHub Releases
2. Extract to your Anki add-ons folder
3. Restart Anki

## Usage

1. In the **Browser**, select one or more notes
2. Right-click → **Quick Image Picker...**
3. Configure:
   - **Source field** - Field containing search terms (e.g., "Word")
   - **Target field** - Where images will be added (e.g., "Picture")
   - **Mode** - Replace, Append, or Skip existing images
4. Click an image or press **1-8** to select and advance
5. Use **Skip** to skip a card, **Back** to revisit previous cards

Settings are remembered per note type, so you only need to configure once.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| 1-8 | Select image |
| Enter | Confirm selection |
| Esc | Skip current card |

## Requirements

- Anki 2.1.54 or later (Qt6)

## See Also

Other image add-ons for Anki:

- [Anki Image Bulk Automatic Downloader](https://ankiweb.net/shared/info/863034630) - Paid, automatic download
- [Quick Images Downloader](https://ankiweb.net/shared/info/8280891) - Bulk download via Google API
- [Batch Image Downloader](https://ankiweb.net/shared/info/1004335882) - Batch download (Qt5)
- [Batch Download Pictures From Google Images](https://ankiweb.net/shared/info/561924305) - Batch download

**How is this different?** The add-ons above download images automatically based on search terms. Anki Image Picker lets you **see and choose** from multiple candidates before inserting - no blind downloads.

## License

MIT
