# Product Requirements Document (PRD)
## DBXV2 Build Forge — Roster & Moveset Planner
**Versi Dokumen:** 1.1 (+ Menu Settings: Bahasa & Tema)
**Status Prototipe:** Monolithic `main.py` (~700 LOC fungsional) → Target: Arsitektur Modular Production-Ready
**Target Distribusi:** Windows `.exe` standalone via **Nuitka (onefile mode)**

---

## 0. Ringkasan Eksekutif

Aplikasi ini adalah **planner pra-produksi** untuk modder Dragon Ball Xenoverse 2. Fungsinya menjembatani proses *brainstorming* skillset/moveset karakter mod dengan proses build aktual di tools eksternal (Eternity Tools, LB Mod Installer), dengan mengonsolidasikan data preset ke dalam database lokal ter-cache dan mengekspornya ke spreadsheet.

Prototipe saat ini sudah *functional* namun monolithic (satu file, `QTableWidget` manual, styling inline, tanpa pemisahan lapisan data/UI/logic). PRD ini mendefinisikan refactor menuju arsitektur **modular MVC** berbasis Qt Model/View, penambahan fitur ergonomis, dan kesiapan build ke `.exe`.

### Nama Aplikasi — **FINAL**
Nama resmi aplikasi: **DBXV2 Build Forge**. Nama kerja lama "XV2 Character Skillset & Build Planner" (prototipe) resmi digantikan. Seluruh referensi judul window, judul dialog `About`, `file-version`/`product-name` build Nuitka (§5), dan string i18n (§3.8) harus konsisten memakai nama ini.

---

## 1. Latar Belakang & Tujuan

### 1.1 Masalah pada Prototipe
- Semua logic (dialog, tabel, cache I/O, export) berada dalam satu file `main.py` — sulit di-maintain dan di-test.
- `QTableWidget` diisi ulang manual per `reload_table()` — tidak efisien untuk dataset besar, sorting/filtering dilakukan dengan iterasi manual (`setRowHidden` per baris) alih-alih memakai kapabilitas Qt native.
- Penyimpanan cache (`mod_planner_cache_v4.json`) ditulis langsung dengan `open(..., "w")` — rawan corrupt jika aplikasi crash/kehabisan disk saat proses tulis.
- Styling menggunakan inline `setStyleSheet()` per-widget — tidak konsisten dan sulit diubah temanya secara global.
- Tidak ada validasi/deduplikasi data skill yang konsisten (rawan duplikasi entri mirip di dropdown cache).

### 1.2 Tujuan Refactor
1. Migrasi ke struktur **Modular MVC** yang jelas dan scalable.
2. Migrasi rendering tabel ke **`QAbstractTableModel` + `QSortFilterProxyModel`** untuk live search & sorting native, performant untuk ratusan/ribuan baris.
3. Menjamin **integritas data** (atomic write, validasi input, normalisasi parsing skill).
4. Menambah fitur ergonomis: **Load Preset ke Editor** dari `SheetDetailDialog`.
5. Menyediakan tema **Dark Mode QSS** modern ala tools modding.
6. Siap di-*compile* ke `.exe` **onefile** menggunakan **Nuitka**.

### 1.3 Non-Goals (Eksplisit Di-scope-out)
- **Two-Way Sync Import** (baca kembali `.xlsx`/`.csv` yang sudah diekspor ke tabel roster) — **DITIADAKAN** atas keputusan eksplisit pemilik produk. Alur data bersifat **searah**: Aplikasi → Spreadsheet.
- **Migrasi/kompatibilitas data lama** dari `mod_planner_cache_v4.json` — **DITIADAKAN**. Aplikasi baru mulai dari skema JSON baru (fresh state). Tidak perlu menulis kode migrasi/parser format lama.
- Tidak ada requirement cloud sync/multi-user; aplikasi tetap single-user, local-first.
- Localization **dibutuhkan** (lihat §3.8 — Menu Settings), namun terbatas pada 3 bahasa yang ditentukan (Indonesia, Inggris, Jepang). Tidak perlu menyediakan framework i18n yang generik/pluggable untuk bahasa lain di luar tiga ini.

---

## 2. Arsitektur Target (Modular MVC)

### 2.1 Struktur Folder

```
dbxv2_build_forge/
├── main.py                          # Entry point — inisialisasi QApplication, load stylesheet, tampilkan MainWindow
├── app_config.py                    # Konstanta global: nama app, versi, path cache, kolom tabel
│
├── models/
│   ├── __init__.py
│   ├── schemas.py                   # Dataclasses: CharacterEntry, SkillEntry, SuperSoulEntry, PresetEntry, RosterSheet
│   ├── data_store.py                # AppDataStore — single source of truth in-memory (rosters + dropdown_cache)
│   ├── persistence.py                # AtomicJsonPersistence — write-to-temp + os.replace, backup rotasi
│   ├── validators.py                 # Validasi input (nama tidak boleh kosong, deteksi duplikasi mirip via normalisasi string)
│   ├── table_models.py               # QAbstractTableModel: DatabaseTableModel, RosterSummaryTableModel, PresetDetailTableModel
│   └── skill_parser.py               # Normalisasi pola "[Skill Name] : [ID]" vs teks murni
│
├── views/
│   ├── __init__.py
│   ├── main_window.py                 # QMainWindow — hanya assembling tab & menu, tanpa business logic
│   ├── editor_tab.py                  # Tab "Skillset Editor" (form input + target sheet)
│   ├── roster_preview_tab.py           # Tab "Roster Table Preview" (QTableView + proxy model)
│   ├── database_manager_tab.py         # Reusable tab utk Character/Skill/SuperSoul manager (QTableView + proxy model)
│   ├── dialogs/
│   │   ├── character_dialog.py
│   │   ├── skill_dialog.py
│   │   ├── super_soul_dialog.py
│   │   ├── sheet_detail_dialog.py        # + tombol/menu "Load into Editor"
│   │   └── export_options_dialog.py      # Dialog pilihan format & mode export (extract dari inline logic lama)
│   ├── widgets/
│   │   ├── searchable_table_view.py      # QTableView + built-in search bar terhubung ke QSortFilterProxyModel
│   │   └── toolbar_widget.py             # Reusable toolbar: tombol "+", "Sort A-Z", search box
│   └── tab_manager.py                    # Wrapper QTabWidget registrasi semua tab
│
├── controllers/
│   ├── __init__.py
│   ├── app_controller.py               # Orkestrator utama — menghubungkan model & view, lifecycle app
│   ├── editor_controller.py            # Logic save_entry, clear_form, register ke dropdown cache
│   ├── roster_controller.py            # Logic create/rename/delete sheet, load preset ke editor
│   ├── database_controller.py          # Logic add/edit/delete entry Character/Skill/SuperSoul
│   ├── export_controller.py             # Builder ekspor Excel/CSV (single-file, multi-sheet, per-file)
│   ├── settings_controller.py           # Logic apply bahasa & tema, load/save settings.json — BARU
│   └── signal_bus.py                    # EventBus terpusat (Qt Signals) — dropdown_cache_changed, roster_changed, language_changed, theme_changed, dsb.
│
├── styles/
│   ├── dark_theme.qss                   # Tema Dark (ala Eternity Tools / CUS)
│   ├── light_theme.qss                  # Tema Light — **DEFAULT** aplikasi
│   └── theme_manager.py                 # Loader QSS + deteksi tema sistem + switch tema runtime
│
├── locales/
│   ├── en.json                          # Bahasa Inggris — **DEFAULT** aplikasi
│   ├── id.json                          # Bahasa Indonesia
│   ├── ja.json                          # Bahasa Jepang
│   └── i18n_manager.py                  # Loader locale + fungsi translate `tr(key: str) -> str`
│
├── views/
│   ├── ... (seperti sebelumnya)
│   └── dialogs/
│       └── settings_dialog.py           # Dialog Menu Settings (Bahasa & Tema) — BARU
│
├── resources/
│   └── icons/                           # Ikon toolbar (add, edit, delete, export, load, settings, dsb)
│
└── build/
    └── nuitka_build.md                  # Instruksi & flag command Nuitka onefile
```

### 2.2 Prinsip Desain Kunci
- **Single Source of Truth:** `AppDataStore` di `models/data_store.py` menyimpan seluruh state (`rosters`, `dropdown_cache`) — tidak ada widget yang menyimpan data sendiri di luar model Qt-nya.
- **Signal Bus terpusat:** Perubahan data (`entry_added`, `entry_deleted`, `sheet_renamed`, dst.) dipancarkan lewat `signal_bus.py`, didengarkan oleh semua tab yang relevan — menggantikan pola `self.app.reload_all_views()` manual yang tersebar di prototipe.
- **View bersih dari logic:** Views hanya menangani rendering & delegasi event ke Controller. Tidak ada `pd.DataFrame(...)` atau `json.dump(...)` langsung di dalam file `views/`.
- **Testability:** Karena `models/` dan `controllers/` tidak bergantung pada instance `QApplication` yang aktif untuk logikanya (hanya pakai Qt Signals sebagai mekanisme observer), unit test bisa ditulis dengan `pytest` tanpa membutuhkan display/headless Qt environment untuk sebagian besar logic non-UI.

---

## 3. Spesifikasi Fungsional Detail

### 3.1 Model/View Migration (Qt Native Sort & Filter)

**Masalah di prototipe:** `filter_table()` melakukan iterasi manual `for row in range(self.table.rowCount())` dan `setRowHidden()`. `toggle_sort()` men-sort data source lalu memanggil `reload_table()` (rebuild seluruh QTableWidgetItem).

**Solusi target:**
- Setiap tabel (Character/Skill/SuperSoul manager, Roster Summary, Sheet Detail) memiliki `QAbstractTableModel` khusus yang membaca langsung dari `AppDataStore` (list of dict/dataclass), meng-emit `dataChanged`/`layoutChanged`/`beginInsertRows` sesuai operasi CRUD — bukan rebuild total.
- Setiap `QTableView` dibungkus `QSortFilterProxyModel`:
  - **Live search** → `proxy.setFilterKeyColumn(-1)` (semua kolom) + `setFilterCaseSensitivity(Qt.CaseInsensitive)`, terhubung ke `textChanged` pada search box dengan **debounce ringan** (opsional, `QTimer` single-shot 150ms) agar tidak filter tiap keystroke pada dataset besar.
  - **Sort A-Z / Z-A** → `proxy.sort(column, order)` dipicu tombol "Sort A-Z" yang kini toggle `Qt.AscendingOrder`/`Qt.DescendingOrder`, atau *diperkaya* jadi **sort-by-click-header** (`view.setSortingEnabled(True)`) sebagai *quality-of-life* tambahan yang gratis didapat dari native Qt.
- **Inline edit kolom "Note"** dipertahankan lewat `flags()` override di model (`Qt.ItemIsEditable` hanya utk kolom Note pada entry_type skill/supersoul) dan `setData()` yang langsung menulis ke `AppDataStore` + memicu `signal_bus.dropdown_cache_changed`.

### 3.2 Interaksi Mouse — Kontrak Perilaku (WAJIB dipertahankan identik)

| Tab | Klik Kiri 1x | Klik Kiri 2x (Double) | Klik Kanan |
|---|---|---|---|
| Database Manager (Character/Skill/Super Soul) | Select row | Inline-edit khusus kolom "Note" (skill & supersoul saja) | Context menu: Edit / Delete |
| Roster Table Preview | Single/multi-select (Ctrl/Shift, `ExtendedSelection`) | Buka `SheetDetailDialog` | Context menu: Rename Sheet / Delete Sheet |
| **Sheet Detail Dialog (baru)** | Select row preset | — *(reserved, tidak dipakai)* | Context menu baru: **"Load into Editor"** |

> Catatan implementasi: dengan migrasi ke `QTableView`, pastikan `setEditTriggers()` di-set eksplisit ke `QAbstractItemView.DoubleClicked` **hanya** untuk model kolom Note, karena secara default `QTableView` bisa memicu edit mode pada klik yang tidak diinginkan jika `flags()` model tidak dikontrol ketat.

### 3.3 Fitur Baru: "Load Preset ke Editor" dari Sheet Detail

**User flow:**
1. User double-click baris sheet di Roster Table Preview → `SheetDetailDialog` terbuka menampilkan seluruh preset dalam sheet tersebut.
2. User klik kanan pada salah satu baris preset → context menu muncul dengan opsi **"Load into Editor"** (selain opsi baca-saja yang sudah ada).
3. Controller (`roster_controller.load_preset_into_editor`) mem-broadcast data baris tersebut via `signal_bus.preset_load_requested.emit(preset_data)`.
4. `EditorTab` mendengarkan sinyal ini, mengisi seluruh field form (`char_name_cb`, `char_id_cb`, kombinasi skill, dst.) dengan data preset, **dan otomatis men-switch `main_tabs` ke tab "Skillset Editor"**.
5. Field "Target Sheet" (`target_table_cb`) di-*prefill* dengan nama sheet asal — sehingga jika user klik "Simpan", perilaku default adalah **update ke sheet yang sama** (bukan duplikasi otomatis).
6. **Duplikasi vs Edit-in-place:** karena `save_entry()` di prototipe selalu melakukan `append()` baru, perlu keputusan desain baru:
   - Tambahkan tombol alternatif di Editor: **"Simpan sebagai Baris Baru"** (duplicate, perilaku lama — default) vs **"Update Baris Ini"** (replace in-place, muncul hanya ketika preset sedang dalam mode "loaded for edit", butuh index/ID unik sebagai referensi baris asal).
   - Ini membutuhkan setiap `PresetEntry` memiliki **UUID unik** (`entry_id: str`) yang digenerate saat `save_entry()` pertama kali — perubahan skema data dari prototipe (yang murni `dict` tanpa ID).

### 3.4 Standarisasi Parsing Skill (Data Integrity)

**Masalah di prototipe:** `_register_skill()` hanya mengecek exact string match (`if name not in existing`) — variasi penulisan seperti `"Kamehameha"` vs `"Kamehameha : 123"` vs `" kamehameha "` dianggap entri berbeda, menyebabkan dropdown "kotor" dengan duplikat semu.

**Solusi (`models/skill_parser.py`):**
- Fungsi `parse_skill_input(raw: str) -> ParsedSkill` yang mengenali pola:
  - `"[Skill Name] : [ID]"` (contoh: `"Kamehameha : 1024"`) → dipecah jadi `name="Kamehameha"`, `skill_id="1024"`.
  - Teks murni tanpa delimiter `:` → `name=raw.strip()`, `skill_id=None`.
- Fungsi `normalize_for_dedup(name: str) -> str` — lowercase, strip whitespace berlebih, hilangkan karakter non-alfanumerik di pinggir — dipakai sebagai **key pembanding** saat registrasi ke dropdown cache (bukan dipakai untuk mengubah data asli yang ditampilkan/disimpan).
- Saat `_register_skill()` dipanggil: bandingkan `normalize_for_dedup(new_name)` terhadap `normalize_for_dedup(existing_name)` untuk semua entri — jika cocok, **jangan tambahkan entri baru**, namun jika `skill_id` baru ada dan entri lama belum punya `skill_id`, **update field ID** entri lama (best-effort enrichment, bukan overwrite nama).
- Tambahkan unit test (`tests/test_skill_parser.py`) mencakup kasus: delimiter ganda (`"A : B : 123"`), whitespace tidak konsisten, case-insensitive duplicate.

### 3.5 Atomic Persistence

**Masalah di prototipe:** `save_cache()` menulis langsung ke `CACHE_FILE` — jika proses terhenti di tengah `json.dump()` (crash, power loss), file menjadi corrupt/truncated dan **seluruh data hilang**.

**Solusi (`models/persistence.py`):**
```python
class AtomicJsonPersistence:
    def save(self, path: Path, payload: dict) -> None:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)  # Atomic pada POSIX & Windows (NTFS)
```
- Tambahkan **rotating backup**: sebelum `os.replace`, salin file lama ke `{path}.bak` (maks 1 generasi, opsional bisa dikembangkan ke 3 generasi `.bak1/.bak2/.bak3` jika dibutuhkan robustness lebih tinggi).
- Load-time: jika file utama gagal di-parse (`json.JSONDecodeError`), otomatis fallback ke `.bak` dengan notifikasi non-blocking ke user (bukan crash langsung).
- Karena keputusan produk adalah **fresh schema** (tanpa migrasi data lama), file cache baru sebaiknya diberi nama berbeda dari prototipe, misal `build_forge_data.json`, untuk menghindari ambiguitas dengan file lama `mod_planner_cache_v4.json` yang mungkin masih ada di direktori kerja user.

### 3.6 Export Builder (Excel/CSV)

Logic export dari `RosterPreviewTab.export_selected_tables()` (single file besar berisi UI dialog + pandas logic tercampur) dipecah ke `controllers/export_controller.py`:
- `ExportController.export_single_file(table_names, file_path, file_format)`
- `ExportController.export_multi_file(table_names, folder_path, file_format)`
- `ExportController.export_combined_csv(table_names, file_path)` — menambahkan kolom `"Roster Sheet"` seperti perilaku lama.
- Tetap pertahankan fallback `xlwt → openpyxl` untuk `.xls` seperti prototipe (karena `xlwt` sudah unmaintained dan mungkin gagal di lingkungan tertentu).
- Sanitasi nama sheet (`[]:*?/\` dan batas 31 karakter Excel) dipindah ke fungsi utilitas reusable `utils/excel_utils.py` (dipakai baik oleh single & multi-file export, menghindari duplikasi logic seperti di prototipe).

### 3.7 Sistem Tema — Light (Default) / Dark / Same as System

- Palet Dark: latar gelap (`#1e1e1e` / `#252526`), aksen biru modding-tools (`#2b5797` dipertahankan dari prototipe sebagai *brand accent*), hijau sukses (`#1e7145` dipertahankan utk tombol Export).
- Palet Light: **tema default aplikasi** saat pertama kali dijalankan (`first_run`) — latar terang (`#f5f5f5` / `#ffffff`), teks gelap (`#1a1a1a`), aksen biru & hijau tetap sama dengan Dark demi konsistensi *brand* modding-tools.
- Styling dipindah **100% ke QSS eksternal** (`styles/dark_theme.qss` & `styles/light_theme.qss`) — hapus semua `widget.setStyleSheet("...")` inline dari prototipe. Gunakan **object name** (`setObjectName("addButton")`) sebagai selector QSS, bukan inline style, agar tema bisa diubah tanpa menyentuh kode Python.
- `theme_manager.py` menyediakan:
  - `apply_theme(app: QApplication, theme_mode: ThemeMode) -> None` — dipanggil saat startup & saat user mengganti tema lewat Settings.
  - `ThemeMode` enum: `LIGHT` (default) / `DARK` / `SYSTEM`.
  - Untuk mode **`SYSTEM`** — deteksi preferensi OS via `QGuiApplication.styleHints().colorScheme()` (Qt 6.5+, tersedia di PySide6 versi yang mendukung `Qt.ColorScheme`). Jika API ini tidak tersedia di versi PySide6 yang dipakai project, fallback ke deteksi registry Windows (`HKEY_CURRENT_USER\...\Personalize\AppsUseLightTheme`) sebagai alternatif khusus Windows (karena target build adalah `.exe` Windows).
  - Perubahan tema berlaku **langsung tanpa perlu restart aplikasi** (reload stylesheet on QApplication instance).

### 3.8 Menu Settings — Bahasa & Tema (BARU)

**Lokasi akses:** Menu bar (`QMenuBar`) di `MainWindow` — menu **"Settings"** (atau ikon gear di toolbar utama), membuka `SettingsDialog` (modal, non-blocking terhadap data — perubahan bisa langsung di-*preview* tanpa perlu tombol "Apply" terpisah, cukup "OK"/"Cancel" standar).

**Opsi yang tersedia:**

| Pengaturan | Pilihan | Default |
|---|---|---|
| **Bahasa (Language)** | Bahasa Indonesia / **English** / 日本語 (Japanese) | **English** |
| **Tema (Theme)** | **Light** / Dark / Same as System | **Light** |

**Persistensi:** Disimpan terpisah dari data roster/cache, di file `settings.json` (bukan bagian dari `build_forge_data.json`) — memakai mekanisme `AtomicJsonPersistence` yang sama (§3.5) demi konsistensi. Contoh skema:
```json
{
  "language": "en",
  "theme": "light"
}
```
Dimuat di awal `main.py` sebelum `QApplication` dibuat sepenuhnya (khusus untuk tema — agar tidak ada "flash" tema salah saat startup), lalu diteruskan ke `theme_manager.apply_theme()` dan `i18n_manager.set_language()`.

**Internationalization (i18n):**
- `i18n_manager.py` menyediakan fungsi global `tr(key: str, **kwargs) -> str` yang membaca dari dictionary JSON locale aktif (`locales/en.json`, `locales/id.json`, `locales/ja.json`), dengan **fallback ke English** jika key tidak ditemukan di locale yang dipilih (mencegah UI menampilkan string kosong/crash jika terjemahan Jepang belum lengkap).
- Seluruh string UI yang saat ini di-*hardcode* Bahasa Indonesia di prototipe (label field, tombol, judul dialog, pesan `QMessageBox`) **wajib direfactor** memakai `tr("key.path")` — bukan f-string/string literal langsung — agar bisa diterjemahkan.
- Struktur key locale disarankan bertingkat namespace, misal: `editor.label.character_name`, `dialog.confirm.delete_entry`, `menu.settings.title`, dst.
- **Penting — dampak arsitektur:** karena §3.2 (interaksi mouse) dan §3.3 (Load into Editor) semula ditulis dengan label Bahasa Indonesia sebagai acuan implisit ("Load into Editor", "Simpan sebagai Baris Baru", dll.), semua label tersebut kini harus melalui key i18n yang sama — pastikan ketiga file locale (`en`/`id`/`ja`) memuat key yang identik satu sama lain (validasi lewat unit test sederhana yang membandingkan `set(en.keys()) == set(id.keys()) == set(ja.keys())`, agar tidak ada key yang tertinggal saat penambahan fitur baru di kemudian hari).
- **Perubahan bahasa berlaku langsung tanpa restart** — sama seperti tema, seluruh widget teks statis (label, tooltip, judul tab) perlu di-*retranslate* saat sinyal `signal_bus.language_changed` terpancar. Untuk widget yang sulit di-retranslate secara dinamis (misal judul `QMainWindow`), boleh menampilkan dialog kecil "Restart aplikasi untuk menerapkan bahasa sepenuhnya pada beberapa elemen" sebagai *acceptable fallback*, asalkan sebagian besar UI utama (form, tabel, tombol) tetap live-update.

---

## 4. Requirement Non-Fungsional

| Aspek | Requirement |
|---|---|
| **Performa** | Live search pada tabel ≥1000 baris tidak boleh menyebabkan UI freeze/lag terasa (>100ms per keystroke) — dicapai lewat `QSortFilterProxyModel` native, bukan iterasi Python manual. |
| **Type Hinting** | Seluruh fungsi publik di `models/` dan `controllers/` wajib memakai type hints (PEP 484), divalidasi dengan `mypy` (opsional tapi direkomendasikan sebagai CI check). |
| **Code Style** | PEP8, `black` untuk formatting, `ruff`/`flake8` untuk linting. |
| **Error Handling** | Tidak ada `except Exception: pass` senyap seperti di prototipe (`load_cache`, `save_cache`) — minimal log ke file `app.log` dan/atau notifikasi non-blocking ke user. |
| **Build Target** | Kompatibel Nuitka **onefile**: hindari resource loading berbasis path relatif yang rapuh — gunakan pola deteksi `sys.frozen` / `__compiled__` untuk resolve path resource (ikon, QSS) baik saat dijalankan dari source maupun dari `.exe` hasil kompilasi. |
| **Dependency Footprint** | Minimalkan dependency non-esensial untuk memperkecil ukuran `.exe` onefile (pandas + openpyxl sudah cukup berat; evaluasi apakah `xlwt` benar-benar perlu dipertahankan mengingat format `.xls` sudah usang). |

---

## 5. Rencana Build Nuitka (Onefile)

Dicatat sebagai referensi awal untuk tahap build (detail final menyesuaikan hasil refactor):

```bash
python -m nuitka main.py ^
  --onefile ^
  --standalone ^
  --enable-plugin=pyside6 ^
  --windows-console-mode=disable ^
  --include-data-dir=styles=styles ^
  --include-data-dir=resources=resources ^
  --output-dir=dist ^
  --windows-icon-from-ico=resources/icons/app_icon.ico ^
  --company-name="Andra" ^
  --product-name="DBXV2 Build Forge" ^
  --file-version=1.0.0.0 ^
  --product-version=1.0.0.0
```
Catatan:
- `--onefile` dipilih sesuai preferensi (single `.exe`, trade-off startup time sedikit lebih lambat karena ekstraksi ke temp dir tiap run).
- `--include-data-dir` wajib untuk QSS & ikon karena tidak otomatis ter-bundle seperti modul Python.
- `--windows-console-mode=disable` agar tidak muncul jendela terminal di belakang GUI (aplikasi desktop murni).

---

## 6. Deliverables yang Diharapkan dari Google Antigravity

1. **Struktur folder lengkap** sesuai Bagian 2.1, seluruh file `.py` terisi (tidak ada stub kosong tanpa implementasi).
2. **Migrasi 1:1 seluruh fungsionalitas prototipe** ke arsitektur baru — tidak boleh ada regresi fitur (semua interaksi mouse di Bagian 3.2 harus identik).
3. Implementasi lengkap **Qt Model/View** (Bagian 3.1) menggantikan seluruh `QTableWidget` manual.
4. Implementasi **atomic persistence** (Bagian 3.5).
5. Implementasi **fitur "Load into Editor"** (Bagian 3.3) lengkap dengan mekanisme Update vs Duplicate.
6. Implementasi **skill parser & dedup** (Bagian 3.4).
7. **Sistem Tema** Light (default) / Dark / Same as System, QSS modern siap pakai (Bagian 3.7).
8. **Menu Settings** lengkap dengan pilihan Bahasa (ID/EN-default/JP) dan Tema, termasuk 3 file locale JSON terisi penuh dan konsisten key-nya (Bagian 3.8).
9. Dokumentasi singkat per modul (docstring format Google/NumPy style) — cukup untuk on-boarding developer lain.
10. **Tidak perlu** mengimplementasikan Two-Way Sync Import maupun migrasi data lama — eksplisit di luar scope (Bagian 1.3).

---

## 7. Lampiran — Skema Data Baru (Referensi Model)

```python
# models/schemas.py (ringkasan konseptual, bukan kode final)

@dataclass
class CharacterEntry:
    code: str
    name: str
    is_playable: bool

@dataclass
class SkillEntry:
    skill_name: str
    skill_id: str | None
    is_cac_skill: bool
    note: str

@dataclass
class SuperSoulEntry:
    name: str
    effect_1: str
    effect_2: str
    note: str

@dataclass
class PresetEntry:
    entry_id: str              # UUID baru — tidak ada di prototipe
    character_name: str
    character_id: str
    costume_name: str
    costume_index: int
    model_preset: int
    super_skills: list[str]     # len == 4
    ultimate_skills: list[str]  # len == 2
    awoken_skill: str
    evasive_skill: str
    super_soul: str

@dataclass
class RosterSheet:
    name: str
    presets: list[PresetEntry]
```

---

*Dokumen ini disusun berdasarkan analisis kode prototipe `main.py` (1033 baris) dan keputusan scope yang telah dikonfirmasi langsung oleh pemilik produk (Andra).*
