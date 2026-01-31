# txt-snippets

A lightweight, cross-platform text expansion tool written in Python.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-lightgrey.svg)

## Features

- 🚀 **Fast text expansion** - Type a trigger, get instant replacement
- 🎯 **Cursor positioning** - Use `$CURSOR$` to place cursor after expansion
- 📅 **Dynamic variables** - Insert current date/time automatically
- 🌐 **Unicode support** - Full emoji and international character support
- 💾 **Cloud sync ready** - Store snippets on Dropbox, iCloud, or Google Drive
- 🖥️ **System tray** - Runs quietly in the background

## Quick Start

### macOS

1. Download or clone this repository
2. Double-click **`start_mac.command`**
3. Grant Accessibility permission:
   - System Settings → Privacy & Security → Accessibility
   - Add and enable **Terminal.app**

> Terminal window opens briefly and closes automatically.

### Windows

1. Download or clone this repository
2. Double-click **`start_windows_silent.vbs`** (no console window)
   - Or use `start_windows.bat` for first setup / debugging

> First launch will automatically set up the virtual environment and install dependencies.

## Usage

The app runs in the menu bar (macOS) / system tray (Windows). Click the icon to:

| Menu Item | Action |
|-----------|--------|
| **Set Library Path** | Select your snippets file |
| **Open Library** | Edit snippets in your text editor |
| **Reload** | Refresh snippets after editing |
| **Launch at Login** | Toggle auto-start |
| **Exit** | Quit the application |

## Snippet Format

Snippets are stored in a plain text file with `trigger::replacement` format:

```text
# Basic replacement
]hello::Hello, World! 👋

# Multi-line (use \n for newline, \t for tab)
]sig::Best regards,\nJohn Doe

# Cursor positioning - cursor lands between tags
]tag::<div>$CURSOR$</div>

# Dynamic date/time
]da::$DATE_YYYYMMDD$           # → 20260131
]dda::$DATE_YYYY/MM/DD$        # → 2026/01/31
]ddda::$DATE_YYYY年M月D日$     # → 2026年1月31日
]time::$TIME_HH:MM:SS$         # → 21:30:00
]now::$DATETIME$               # → 2026-01-31 21:30:00
```

## Dynamic Variables

| Variable | Example Output |
|----------|----------------|
| `$DATE_YYYYMMDD$` | `20260131` |
| `$DATE_YYYY/MM/DD$` | `2026/01/31` |
| `$DATE_YYYY年M月D日$` | `2026年1月31日` |
| `$TIME_HH:MM:SS$` | `21:30:00` |
| `$DATETIME$` | `2026-01-31 21:30:00` |

## Cloud Sync

Store your `snippets.txt` in a cloud-synced folder (Dropbox, iCloud, Google Drive), then set the library path via the tray menu for cross-device sync.

## Requirements

- Python 3.9+
- macOS: Terminal needs Accessibility permission
- Windows: Python must be installed and in PATH

## License

MIT License
