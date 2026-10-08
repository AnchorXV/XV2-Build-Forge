# DBXV2 Build Forge

A desktop application for planning Dragon Ball Xenoverse 2 character presets before
they are built into external modding tools such as Eternity Tools or LB Mod Installer.

Built with Python and PySide6 (Qt 6).

---

## Overview

DBXV2 Build Forge is a pre-production planning tool for DBXV2 modders. It provides a
workspace to design character skillsets, costume configurations, model presets, and
Super Souls, then export the results in a portable format for use in external build
tools.

It was built around a specific daily workflow: open it, make a few edits, close it,
without waiting on load times or hunting through menus for a shortcut.

---

## Features

### Workspace
- Sidebar navigation across three workspaces: Editor, Roster, Database
- Global keyboard shortcuts for navigation
- Window state (size, position, last active tab) persists across sessions

### Skillset editor
- Card-based form layout
- Searchable dropdowns for all skill fields (type-to-filter, case-insensitive)
- Character ID lookup based on the name entered
- New characters, skills, and Super Souls are registered to the reference database
  automatically on first save
- Two save actions, "Save as New" and "Update This Entry," tracked by UUID so the two
  never get confused

### Roster management
- Split view: sheet list on the left, preset detail on the right
- Multi-sheet management with drag-and-drop reordering
- Per-sheet notes and tags
- Duplicate, rename, or delete a sheet, all undoable
- Bulk selection via Ctrl+Click, Ctrl+Shift+Click, and Ctrl+A

### Command palette (Ctrl+P)
- Jump to any sheet or character by name
- Type to filter, arrow keys to move through results, Enter to select
- Searches across every sheet in the current project

### Find and replace (Ctrl+R)
- Scope a search to one field or all fields, one sheet or all sheets
- Case-sensitive toggle
- Shows the match count before you apply anything
- Replace All undoes in a single step

### Clipboard operations (Ctrl+C, Ctrl+X, Ctrl+V)
- Copy or cut presets from one sheet and paste into another
- Pasted or cloned presets get new UUIDs so they never collide with the originals
- Works from both the roster panel and the sheet detail dialog

### Data persistence
- Writes are atomic: data is written to a temp file, then swapped in with os.replace,
  so a crash mid-write cannot corrupt the main file
- Rotating .bak backup, with a full timestamped backup written to `backups/` every
  10 minutes
- If the primary file turns out corrupted, the app falls back to the backup on load
  without asking
- Every mutation triggers a save, so there is nothing to lose between saves

### Export
- Multi-sheet export to Excel (.xlsx) via openpyxl
- CSV export with sections separated
- Single-file or per-sheet export
- openpyxl is the only export dependency; no pandas

### Undo/redo
- Every CRUD operation is undoable
- Bulk actions (deleting several presets, pasting several, cutting several) undo as
  one step rather than one per item
- Ctrl+Z to undo, Ctrl+Y to redo

---

## Requirements

- Windows 10 or Windows 11 (64-bit)
- Python 3.10 or later, if running from source
- No Python installation needed for the compiled executable

---

## Running from source

Install dependencies:

    pip install -r requirements.txt

Launch the application:

    python main.py

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+P` | Command palette |
| `Ctrl+R` | Find and replace |
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

## Project structure

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

## Running tests

    pytest -v

The test suite covers UUID serialization and recovery from a corrupted file via
.bak, skill input deduplication and normalization, undo/redo across all CRUD
operations, Find and Replace matching with case sensitivity on and off, and locale
key resolution with translation fallback.

---

## Building a standalone executable

To package the application as a single Windows executable with no Python
dependency, use Nuitka:

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

Output: `build_nuitka/DBXV2_Build_Forge.exe` (about 23 MB, compressed).

The first build takes 6 to 10 minutes. Later builds reuse the compiler cache and
finish in 2 to 3 minutes.

### Data file location

In compiled mode, `build_forge_data.json` is written next to the executable, not
into the temporary extraction directory, so data survives a restart.

---

## Technology stack

- PySide6 (Qt for Python) for the GUI
- openpyxl for writing Excel files
- Nuitka to compile to a standalone executable
- pytest for the test suite

---

## License

This project is developed for the Dragon Ball Xenoverse 2 modding community. See
the LICENSE file for details.