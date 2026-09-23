# DBXV2 Build Forge — Roster & Moveset Planner

**DBXV2 Build Forge** adalah aplikasi desktop modern berbasis **Python** dan **PySide6 (Qt 6)** yang dirancang khusus untuk modder Dragon Ball Xenoverse 2. Aplikasi ini berfungsi sebagai perencana pra-produksi untuk merancang skillset, preset model, kostum, dan super soul karakter mod sebelum di-build ke dalam tool eksternal seperti Eternity Tools atau LB Mod Installer.

---

## 🌟 Fitur Utama

- **Arsitektur Modular MVC**: Pemisahan lapisan data model (`models/`), antarmuka pengguna (`views/`), pengendali logika (`controllers/`), dan event bus terpusat (`SignalBus`).
- **Qt Model/View Native**: Menggunakan `QAbstractTableModel` dan `QSortFilterProxyModel` untuk performa tinggi, pencarian instan (debounced live search), dan sorting multi-kolom yang mulus.
- **Integritas Data Crash-Safe**: Sistem penyimpanan JSON atomik (`write-to-temp` + `os.replace`) dilengkapi dengan rotasi backup otomatis (`.bak`) dan pemulihan transparan jika terjadi crash atau korupsi file.
- **Load Preset ke Editor**: Muat kembali data preset dari pratinjau roster langsung ke form editor untuk pembaruan instan (*Update This Entry*) menggunakan pelacakan UUID unik.
- **Internasionalisasi (i18n)**: Dukungan penuh 3 bahasa dengan pergantian langsung saat aplikasi berjalan tanpa perlu restart:
  - 🇺🇸 English
  - 🇮🇩 Bahasa Indonesia
  - 🇯🇵 日本語 (Japanese)
- **Tema Modern (QSS)**:
  - **Light Theme**: Tampilan bersih dengan aksen biru/hijau.
  - **Dark Theme**: Estetika modding tool gelap ala Eternity Tools / CUS editor.
  - **Follow System**: Otomatis mendeteksi preferensi tema OS pengguna.
- **Ekspor Fleksibel**: Ekspor multi-sheet ke format **Excel (.xlsx)** via `openpyxl` atau **CSV** dengan pemisah section terstruktur tanpa dependensi berat seperti pandas.
- **Siap Kompilasi Standalone EXE**: Dirancang khusus agar 100% kompatibel dengan kompilasi **Nuitka (onefile mode)** di Windows.

---

## 📂 Struktur Proyek

```
Character Planner/
├── main.py                          # Entry point aplikasi
├── app_config.py                    # Konfigurasi & path resolver
├── requirements.txt                 # Daftar dependensi Python
├── README.md                        # Dokumentasi proyek
│
├── models/                          # Lapisan Data & Bisnis
│   ├── schemas.py                   # Dataclass domain (PresetEntry, CharacterEntry, dll.)
│   ├── data_store.py                # AppDataStore (Single source of truth in-memory)
│   ├── persistence.py               # AtomicJsonPersistence & rotasi .bak
│   ├── validators.py                # Validasi input form & nama sheet
│   ├── skill_parser.py              # Parser tag [Awoken], [CaC], dedup normaliser
│   └── table_models.py              # QAbstractTableModel untuk tabel
│
├── views/                           # Lapisan Antarmuka Pengguna (GUI)
│   ├── main_window.py               # Top-level QMainWindow
│   ├── tab_manager.py               # QTabWidget orchestrator
│   ├── editor_tab.py                # Tab Editor Skillset
│   ├── roster_tab.py                # Tab Roster Preview
│   ├── database_tab.py              # Tab Database Manager generik
│   ├── widgets/
│   │   ├── searchable_table_view.py # QTableView + proxy model search
│   │   └── toolbar_widget.py        # Toolbar (+, Sort A-Z, Search)
│   └── dialogs/
│       ├── db_entry_dialog.py       # Dialog tambah/edit Karakter, Skill, Super Soul
│       ├── sheet_detail_dialog.py   # Dialog isi sheet & tombol Load into Editor
│       ├── export_dialog.py         # Dialog & engine ekspor XLSX / CSV
│       └── settings_dialog.py       # Dialog pengaturan bahasa & tema
│
├── controllers/                     # Lapisan Pengendali & Event Bus
│   ├── signal_bus.py                # Event bus Qt terpusat
│   ├── app_controller.py            # Master coordinator aplikasi
│   ├── editor_controller.py         # Logika form editor
│   ├── roster_controller.py         # Logika manajemen sheet roster
│   ├── database_controller.py       # Logika cache database
│   ├── export_controller.py         # Logika ekspor file
│   └── settings_controller.py       # Logika konfigurasi & tema
│
├── styles/                          # Stylesheet QSS & Tema
│   ├── light_theme.qss              # Tema terang
│   ├── dark_theme.qss               # Tema gelap
│   └── theme_manager.py             # Loader & deteksi tema OS
│
├── locales/                         # File Kamus Bahasa (JSON)
│   ├── en.json                      # Bahasa Inggris
│   ├── id.json                      # Bahasa Indonesia
│   ├── ja.json                      # Bahasa Jepang
│   └── i18n_manager.py              # Lookup engine & fallback
│
├── tests/                           # Unit Test Otomatis
│   ├── test_models.py               # Test serialisasi, persistence & CRUD
│   ├── test_skill_parser.py         # Test parsing & normalisasi nama skill
│   └── test_locale_keys.py          # Test kelengkapan key antar bahasa
│
├── build/
│   └── nuitka_build.md              # Panduan kompilasi ke EXE
│
└── legacy/
    └── main_old.py                  # Cadangan prototipe monolithic lama
```

---

## 🚀 Menjalankan Aplikasi dari Source Code

### 1. Instalasi Dependensi
Pastikan Python 3.10+ sudah terinstal:
```bash
pip install -r requirements.txt
```

### 2. Jalankan Aplikasi
```bash
python main.py
```

---

## 🧪 Menjalankan Automated Tests

Seluruh modul inti diverifikasi dengan unit test otomatis:
```bash
pytest -v
```

Hasil test mencakup:
- Integritas serialisasi UUID `PresetEntry` dan pemulihan file corrupt via `.bak`.
- Normalisasi deduplikasi skill input (`models.skill_parser`).
- Konsistensi 100% key kamus bahasa antara `en.json`, `id.json`, dan `ja.json`.

---

## 📦 Membangun Standalone Windows EXE

Untuk mem-package aplikasi menjadi file executable tunggal (`DBXV2_Build_Forge.exe`) tanpa ketergantungan Python:

Lihat panduan lengkap di: [`build/nuitka_build.md`](file:///c:/Users/diand/Downloads/Documents/Character%20Planner/build/nuitka_build.md).

Perintah cepat (PowerShell):
```powershell
python -m nuitka --onefile --standalone --enable-plugin=pyside6 --include-data-dir=styles=styles --include-data-dir=locales=locales --windows-console-mode=disable --output-filename="DBXV2_Build_Forge.exe" main.py
```

---

## 📄 Lisensi & Kredit

- **DBXV2 Build Forge** dikembangkan untuk komunitas modding Dragon Ball Xenoverse 2.
- Menggunakan teknologi: [PySide6 (Qt for Python)](https://wiki.qt.io/Qt_for_Python), [openpyxl](https://openpyxl.readthedocs.io/), dan [Nuitka](https://nuitka.net/).
