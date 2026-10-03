# DBXV2 Build Forge

A desktop application for planning Dragon Ball Xenoverse 2 character presets before
they are built into external modding tools such as Eternity Tools or LB Mod Installer.

Built with Python and PySide6 (Qt 6).

---

## Overview

DBXV2 Build Forge is a pre-production planning tool for DBXV2 modders. It provides a
structured workspace to design character skillsets, costume configurations, model
presets, and Super Souls, then export the results in a portable format for use in
external build tools.

The application is optimized for personal workflow: fast startup, keyboard-driven
navigation, and automatic data persistence.

---

## Features

### Workspace
- Sidebar navigation with three main workspaces: Editor, Roster, Database
- Keyboard-first interface with global shortcuts
- Persistent window state across sessions

### Skillset Editor
- Card-based form layout with clear visual hierarchy
- Searchable dropdowns for all skill fields (type-to-filter, case-insensitive)
- Automatic character ID lookup based on character name
- Automatic master pool registration: new characters, skills, and Super Souls are
  added to the reference database on first save
- Two-button save flow: "Save as New" and "Update This Entry" (via UUID tracking)

### Roster Management
- Split-view layout: sheet list on the left, preset detail on the right
- Multi-sheet management with drag-and-drop reordering
- Per-sheet metadata: notes and tags
- Duplicate sheet, rename sheet, delete sheet (all undoable)
- Bulk operations via Ctrl+Click, Ctrl+Shift+Click, and Ctrl+A

### Command Palette (Ctrl+P)
- Quick navigation to any sheet or character by name
- Keyboard-driven: type to filter, arrow keys to navigate, Enter to select
- Search across all sheets in the current project

### Find and Replace (Ctrl+R)
- Field-scoped or all-field search
- Scope selection: current sheet or all sheets
- Case-sensitive toggle
- Live preview showing the number of matches before applying
- Replace All operation is fully undoable in a single step

### Clipboard Operations (Ctrl+C, Ctrl+X, Ctrl+V)
- Copy or cut presets from one sheet and paste into another
- Cloned presets receive new UUIDs to preserve data integrity
- Works across the roster panel and the sheet detail dialog

### Data Persistence
- Crash-safe JSON persistence using atomic write-to-temp with os.replace
- Automatic backup rotation (.bak file)
- Transparent recovery from corrupted primary file via backup
- Timestamped backups stored in `backups/` directory every 10 minutes
- Real-time auto-save on every data mutation

### Export
- Multi-sheet export to Excel (.xlsx) via openpyxl
- CSV export with section-separated structure
- Single-file or per-sheet export modes
- No dependency on pandas or other heavy libraries

### Undo/Redo
- Complete undo stack for all CRUD operations
- Grouped operations (bulk delete, paste multiple, cut multiple) undo in a single step
- Keyboard shortcuts: Ctrl+Z (undo), Ctrl+Y (redo)

---

## Requirements

- Windows 10 or Windows 11 (64-bit)
- Python 3.10 or later (for source execution)
- No Python installation required for the compiled executable

---

## Running from Source

Install dependencies:

    pip install -r requirements.txt

Launch the application:

    python main.py

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+P` | Command Palette |
| `Ctrl+R` | Find and Replace |
| `Ctrl+C` | Copy selected preset(s) |
| `Ctrl+X` | Cut selected preset(s) |
| `Ctrl+V` | Paste preset(s) into current sheet |
| `Ctrl+A` | Select all in current table |
| `Ctrl+Shift+Click` | Extend selection to clicked row |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+N` | New sheet |
| `Ctrl+S` | Save and backup |
| `Delete` | Delete selected item |
| `Esc` | Close dialog |

---

## Project Structure

    DBXV2_Build_Forge/
    |
    |-- main.py                     Application entry point
    |-- app_config.py               Constants and resource path resolver
    |-- requirements.txt            Python dependencies
    |
    |-- assets/
    |   |-- fonts/                  Bundled fonts (Plus Jakarta Sans)
    |   `-- icons/                  SVG icons and application icon
    |
    |-- models/                     Data and business logic layer
    |   |-- schemas.py              Domain dataclasses (PresetEntry, CharacterEntry, etc.)
    |   |-- data_store.py           AppDataStore (single source of truth)
    |   |-- persistence.py          AtomicJsonPersistence with backup rotation
    |   |-- validators.py           Input validation
    |   |-- skill_parser.py         Skill tag parser and deduplication normalizer
    |   |-- table_models.py         QAbstractTableModel implementations
    |   |-- find_replace.py         Find and Replace core logic
    |   |-- exporters.py            XLSX and CSV writers
    |   `-- preset_clipboard.py     In-memory clipboard singleton
    |
    |-- views/                      User interface layer
    |   |-- main_window.py          Top-level QMainWindow
    |   |-- page_manager.py         Sidebar and page stack orchestrator
    |   |-- editor_tab.py           Skillset Editor
    |   |-- roster_tab.py           Roster Split View
    |   |-- database_page.py        Consolidated database manager
    |   |-- database_tab.py         Single category database tab
    |   |-- widgets/
    |   |   |-- sidebar_widget.py       Sidebar navigation
    |   |   |-- section_header.py       Section header component
    |   |   |-- searchable_table_view.py  Table with proxy model search
    |   |   |-- toolbar_widget.py       Reusable toolbar
    |   |   `-- command_palette.py      Command Palette overlay
    |   `-- dialogs/
    |       |-- db_entry_dialog.py      Character/Skill/Super Soul editor
    |       |-- sheet_detail_dialog.py  Sheet contents viewer
    |       |-- sheet_note_tags_dialog.py  Sheet notes and tags editor
    |       |-- bulk_edit_dialog.py     Multi-preset field editor
    |       |-- find_replace_dialog.py  Find and Replace dialog
    |       |-- export_dialog.py        Export flow
    |       `-- about_dialog.py         About dialog
    |
    |-- controllers/                Controller and event bus layer
    |   |-- signal_bus.py           Centralized Qt signal bus
    |   |-- app_controller.py       Application coordinator
    |   `-- undo_commands.py        QUndoCommand implementations
    |
    |-- styles/                     QSS stylesheets
    |   |-- dark_theme.qss          Dark theme stylesheet
    |   `-- theme_manager.py        Stylesheet loader with asset URL resolver
    |
    |-- locales/                    Localization
    |   |-- en.json                 English strings
    |   `-- i18n_manager.py         Translation lookup engine
    |
    `-- tests/                      Unit tests
        |-- test_models.py          Serialization, persistence, CRUD
        |-- test_skill_parser.py    Skill parsing and normalization
        |-- test_find_replace.py    Find and Replace logic
        |-- test_undo_commands.py   Undo/redo command behavior
        `-- test_locale_keys.py     Locale key consistency

---

## Running Tests

    pytest -v

Test coverage includes:
- UUID serialization integrity of PresetEntry and recovery from corrupted files via .bak
- Skill input deduplication and normalization
- Undo/redo command behavior across all CRUD operations
- Find and Replace matching logic with case sensitivity
- Locale key resolution and translation fallback

---

## Building a Standalone Executable

To package the application as a single Windows executable without Python dependencies,
use Nuitka:

    python -m nuitka ^
        --onefile ^
        --enable-plugin=pyside6 ^
        --include-data-dir=assets=assets ^
        --include-data-dir=locales=locales ^
        --include-data-dir=styles=styles ^
        --windows-console-mode=disable ^
        --windows-icon-from-ico=assets/icons/DBXV2_Build_Forge.ico ^
        --output-dir=build_nuitka ^
        --output-filename="DBXV2_Build_Forge.exe" ^
        --company-name="AnchorXV" ^
        --product-name="DBXV2 Build Forge" ^
        --file-version=1.0.0.0 ^
        --product-version=1.0.0.0 ^
        --assume-yes-for-downloads ^
        main.py

Output: `build_nuitka/DBXV2_Build_Forge.exe` (~23 MB, compressed).

The first build takes approximately 6 to 10 minutes. Subsequent builds with compiler
caching complete in 2 to 3 minutes.

### Data File Location

In compiled mode, the data file (`build_forge_data.json`) is created next to the
executable, not in the temporary extraction directory. This ensures data persists
across application restarts.

---

## Technology Stack

- PySide6 (Qt for Python) - GUI framework
- openpyxl - Excel file writing
- Nuitka - Python to C compilation for distribution
- pytest - Test framework

---

## License

This project is developed for the Dragon Ball Xenoverse 2 modding community.
See the LICENSE file for details.