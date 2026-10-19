# DBXV2 Build Forge: rencana QoL dan UI/UX

Dokumen ini merangkum semua yang sudah dibahas untuk perbaikan kenyamanan pakai (QoL) dan tampilan (UI/UX) pada DBXV2 Build Forge, termasuk desain halaman Database yang baru.

Batasan dokumen:

- Build Forge diperlakukan sebagai planner murni. Tidak ada integrasi teknis dengan file atau tool modding.

---

## 1. Kondisi aplikasi sekarang

Stack: Python dan PySide6, struktur `models/`, `views/`, `controllers/`, `styles/`, `locales/`, `tests/`, dibuild ke `.exe` dengan Nuitka mode onefile. Tiga halaman lewat sidebar: Editor, Roster (split view sheet dan preset), Database (combo kategori yang menumpuk enam `DatabaseTab`).

Yang sudah ada, jadi tidak perlu diusulkan lagi:

- Command palette (Ctrl+P), find and replace (Ctrl+R), copy/cut/paste preset dengan UUID baru
- Undo/redo bergrup, bulk edit (saat ini hanya di `SheetDetailDialog`)
- Drag-and-drop untuk sheet dan preset, recent sheets, status bar
- Penyimpanan JSON atomik dengan backup rotasi, ekspor xlsx dan csv

Yang belum ada: menu Settings, tema Light, bahasa selain Inggris (hanya `en.json`), dan penyimpanan preferensi tampilan.

Catatan: ringkasan arsitektur otomatis dari GitDiagram menyebut `settings_controller.py`. File itu tidak ada di repo.

---

## 2. Keputusan yang sudah final

| Topik                   | Keputusan                                                                                                                                                        |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Halaman Database        | Tampilan master-detail (daftar kiri, panel detail kanan) untuk Super Skill, Ultimate Skill, Awoken Skill, Evasive Skill, dan Super Soul. Characters tetap tabel. |
| Daftar kiri             | Hanya nama. Kotak centang CaC pindah ke panel kanan.                                                                                                             |
| Entry belum terpakai    | Tidak diredupkan. Statusnya terlihat dari kotak "Skill Used by".                                                                                                 |
| Urutan panel skill      | Skill Type, Ki Used, Deskripsi, Skill Used by (list scroll).                                                                                                     |
| Awoken Skill            | Tanpa Skill Type. Ki Used tetap ada.                                                                                                                             |
| Urutan panel Super Soul | Judul "(owner)'s Super Soul", Effect 1, Effect 2, Limit Burst.                                                                                                   |
| Super Soul              | Ki Blast Type tidak dibuat. Field Note dihapus. Tidak ada kotak "dipakai di".                                                                                    |
| Deskripsi               | Field `note` skill yang labelnya diganti.                                                                                                                        |
| Skill Type              | Daftar tetap, hanya untuk Super, Ultimate, dan Evasive.                                                                                                          |
| Ki Used                 | Angka saja.                                                                                                                                                      |
| Banyak baris terpilih   | Panel menampilkan jumlah dan list nama yang bisa di-scroll.                                                                                                      |
| Edit data               | Lewat dialog, kecuali combo owner di judul panel Super Soul.                                                                                                     |
| Gaya visual             | Mengambil struktur menu in-game, bukan dekorasinya.                                                                                                              |
| Teks antarmuka          | Lewat `en.json` (default Inggris), jadi "Deskripsi" menjadi "Description".                                                                                       |

---

## 3. Dua belas perbaikan QoL dan UI/UX

### 1. Penanda teks baru di editor

Kondisi: semua combo di `EditorTab` bisa diketik bebas (`NoInsert`). `AddPresetWithAutoRegisterCommand._auto_register_master_pool` mendaftarkan nama yang belum ada (dicocokkan persis) sebagai karakter, skill, atau Super Soul baru. Satu typo langsung menjadi entry baru di Database.

Perubahan: field combo yang isinya tidak ada di pool diberi penanda amber dan tooltip ("Belum ada di Database, akan ditambahkan saat disimpan"). Saran entry terdekat memakai `difflib.get_close_matches`.

File: `views/editor_tab.py`, QSS.

### 2. Mode edit terlihat di editor

Kondisi: `_build_save_card` hanya membuat satu tombol Save, padahal README menyebut "Save as New" dan "Update This Entry". `load_entry` mengisi form dan menyimpan `_editing_entry_id` tanpa tanda visual apa pun, lalu `_on_save` memilih jalur baru atau update dari field itu.

Perubahan: banner di atas form saat mengedit ("Mengedit: nama karakter, sheet nama sheet") dengan cara membatalkan mode edit. Tombol dipisah menjadi "Save as New" dan "Update This Entry".

File: `views/editor_tab.py`. Jalur Update juga perlu auto-register, lihat D7.

### 3. Save tanpa modal

Kondisi: `_save_new` dan `_save_update` memunculkan `QMessageBox.information` setiap save. Form tidak dikosongkan setelah Save as New. Ctrl+S di main window hanya menyimpan dan membuat backup data. Status bar sudah dipakai di `_on_save` (3 detik).

Perubahan: pesan sukses pindah ke status bar. Ada dua pilihan, simpan lalu kosongkan form atau simpan lalu pertahankan (berguna untuk varian karakter yang sama). Bentuk kontrol pilihan itu diputuskan saat implementasi. Ctrl+Enter di editor menyimpan.

File: `views/editor_tab.py`.

### 4. Peringatan lunak di editor

Kondisi: `validate_preset_entry` hanya memeriksa Character Name tidak kosong, dan hasilnya tampil lewat dialog peringatan.

Perubahan: tanda di bawah field kalau skill yang sama dipilih dua kali di slot setipe, atau kalau preset identik (karakter, kostum, dan skill sama) sudah ada di sheet target. Peringatan ini tidak menghalangi save.

File: `views/editor_tab.py`, `models/validators.py`.

### 5. Menu konteks preset lengkap

Kondisi: `_on_preset_context_menu` di Roster hanya berisi "Load into editor" dan "Delete". Copy, Cut, dan Paste hanya lewat keyboard (`PresetClipboard`). Bulk Edit hanya muncul di menu konteks `SheetDetailDialog`.

Perubahan: menu berisi Load into editor, Copy, Cut, Paste, Duplicate (Ctrl+D), Bulk Edit (menyebut jumlah terpilih), dan Delete. Duplicate memakai jalur paste sehingga mendapat UUID baru. Setelah menu jadi, cek apakah `SheetDetailDialog` masih punya fungsi yang tidak ada di panel kanan Roster. Kalau tidak, dialog itu bisa dihapus dan Bulk Edit pindah ke panel.

File: `views/roster_tab.py`, `views/dialogs/sheet_detail_dialog.py`.

### 6. Hapus preset tanpa konfirmasi

Kondisi: `_on_delete_preset_clicked` menampilkan dialog konfirmasi, padahal semua hapus bisa di-undo.

Perubahan: dialog diganti pesan status ("3 preset dihapus. Ctrl+Z untuk urungkan"). Hapus sheet tetap memakai dialog karena dampaknya lebih besar.

File: `views/roster_tab.py`, `views/dialogs/sheet_detail_dialog.py`.

### 7. Tooltip dan sel kosong di tabel Roster

Kondisi: `PresetDetailTableModel.data` hanya menangani `DisplayRole` dan alignment. Kolom skill dipatok sekitar 105 px (kolom nama karakter 170 px), sehingga teks terpotong tanpa tooltip.

Perubahan: `ToolTipRole` berisi teks penuh sel. Sel kosong tampil "–" dengan warna diredupkan lewat `ForegroundRole`, jadi preset yang slotnya belum penuh langsung terlihat.

File: `models/table_models.py`.

### 8. Kolom tabel Roster bisa diatur

Kondisi: ada 14 kolom (`TABLE_COLUMNS`), header berjenis `Interactive`, dan lebar awalnya di-hardcode di `roster_tab.py`. Tidak ada yang disimpan.

Perubahan: klik kanan pada header untuk menyembunyikan kolom. Kolom tersembunyi, lebar, urutan, dan sorting disimpan lalu dipulihkan saat app dibuka.

Pengecekan: `SETTINGS_FILE` didefinisikan di `app_config.py`, tetapi pemakaiannya tidak ditemukan di `views/` dan `controllers/`. `models/` dan `main.py` belum diperiksa. Item ini dan item 11 membutuhkan mekanisme penyimpanan preferensi yang sama.

### 9. Command palette mencari preset

Kondisi: `_on_palette_action` di `main_window.py` hanya menangani `open_sheet`, `find_character`, `new_sheet`, dan `save`. README menjanjikan pencarian lintas sheet.

Perubahan: hasil pencarian tingkat preset (ketik nama, lompat ke sheet dan barisnya), ditambah perintah pindah halaman dan ekspor.

File: `main_window.py`, `views/widgets/command_palette.py`.

### 10. Copy ke clipboard sistem

Kondisi: `PresetClipboard` adalah singleton di memori, jadi Ctrl+C tidak bisa ditempel ke luar aplikasi.

Perubahan: Ctrl+C juga mengisi `QClipboard` dengan teks tab-delimited, sambil objek aslinya tetap disimpan di singleton untuk paste antar sheet.

File: `views/roster_tab.py`, `views/dialogs/sheet_detail_dialog.py`, `models/preset_clipboard.py`.

### 11. Settings, tema, dan bahasa

Kondisi: menu bar hanya berisi File, Edit, dan Help. `en.json` sudah punya kunci `settings.theme_light`, `theme_dark`, dan `theme_system`, tetapi stylesheet-nya hanya `dark_theme.qss` (600 baris) dan bahasanya hanya Inggris (`DEFAULT_LANGUAGE = "en"`). Default Light yang direncanakan berarti tampilan sekarang kebalikannya.

Rencana: menu Settings dengan pilihan bahasa (Indonesia, Inggris sebagai default, Jepang) dan tema (Light sebagai default, Dark, System).

Perubahan:

- Warna di `dark_theme.qss` dijadikan token lewat `string.Template` di `theme_manager.py`. Hasil render tema Dark harus identik dengan sekarang.
- Palet Light ditulis sebagai kumpulan token baru, tanpa menyalin 600 baris QSS.
- File bahasa `id.json` dan `ja.json` ditambahkan. Pergantian bahasa memakai pola `retranslate_ui` yang sudah ada di halaman Database.
- Pilihan tersimpan lewat mekanisme preferensi yang sama dengan item 8.

### 12. Teks campur bahasa

Kondisi:

- `editor_tab.py` memuat `default=` berbahasa Indonesia untuk `editor.message.target_changed` dan `entry_not_found`.
- `main_window.py` memakai string Inggris langsung di `closeEvent`.
- `database_tab.py` memakai f-string untuk hapus massal dan untuk nama makro undo.
- `sheet_detail_dialog.py` memakai fallback "Bulk Edit Selected (N presets)".

Perubahan: semuanya dipindah ke `en.json` lewat `tr()`. `test_locale_keys.py` yang sudah ada menjaga konsistensi kunci. Semua teks baru dari item lain juga ditulis lewat `tr()`.

---

## 4. Halaman Database baru

### 4.1 Kondisi sekarang

`DatabasePage` memegang combo kategori (characters, super_skills, ultimate_skills, awoken_skills, evasive_skills, super_souls) dan `QStackedWidget` berisi enam `DatabaseTab`. Tiap tab terdiri dari toolbar, `SearchableTableView`, dan `DatabaseTableModel`.

- Kolom skill: Skill Name, Is CaC Skill?, Note.
- Kolom Super Soul: Super Soul, Effect 1, Effect 2, Note.
- Edit lewat double-click yang membuka dialog (semua field `QLineEdit` satu baris).
- Data disimpan sebagai dict di `dropdown_cache`.
- Note bisa diedit langsung di sel. Jalur ini (`setData`) menyimpan tanpa lewat undo stack.

### 4.2 Sketsa layout

Super Skill, Ultimate Skill, dan Evasive Skill:

```
┌ toolbar: [+] [cari...] [Sort A-Z] [Fix cache] ───────────────────┐
├────────────────────────┬──────────────────────────────────────────┤
│ Soaring Rush           │ Kamehameha                               │
│ Heat Wave              │                                          │
│ Supreme Fury           │ Skill Type  [ Ki Blast Skills v ]        │
│ Kamehameha        <--  │ Ki Used     [ 100 ]            [x] CaC   │
│ Bending Kamehameha     │                                          │
│ Spirit Bomb            │ Deskripsi                                │
│ Kaioken Kamehameha     │ ┌──────────────────────────────────┐     │
│ ...  (scroll)          │ │ teks deskripsi, scroll bila      │     │
│                        │ │ panjang                          │     │
│                        │ └──────────────────────────────────┘     │
│                        │ Skill Used by (4)                        │
│                        │ ┌──────────────────────────────────┐     │
│                        │ │ Goku    · Sheet A · Super 1      │  ^  │
│                        │ │ Vegeta  · Sheet B · Super 3      │  v  │
│                        │ └──────────────────────────────────┘     │
│                        │                     [Edit]  [Hapus]      │
└────────────────────────┴──────────────────────────────────────────┘
```

Awoken Skill hanya berbeda di bagian atas. Baris Skill Type tidak ada:

```
│                        │ Ki Used     [ 100 ]            [x] CaC   │
```

Super Soul, owner sudah terisi:

```
├────────────────────────┬──────────────────────────────────────────┤
│ <nama Super Soul>      │ Goku Black's Super Soul                  │
│ <nama Super Soul>      │ (hover: kursor tangan, garis bawah,      │
│ <nama Super Soul> <--  │  tooltip "Click to change character")    │
│ ...  (scroll)          │                                          │
│                        │ Effect 1                                 │
│                        │ ┌──────────────────────────────────┐     │
│                        │ │ ...                              │     │
│                        │ └──────────────────────────────────┘     │
│                        │ Effect 2                                 │
│                        │ ┌──────────────────────────────────┐     │
│                        │ │ ...                              │     │
│                        │ └──────────────────────────────────┘     │
│                        │ Limit Burst                              │
│                        │ ┌──────────────────────────────────┐     │
│                        │ │ ...                              │     │
│                        │ └──────────────────────────────────┘     │
│                        │                     [Edit]  [Hapus]      │
```

Super Soul, owner kosong atau judul sedang diklik:

```
│ <nama Super Soul>      │ [ Select or Fill the Character      v ]   │
```

Beberapa baris terpilih (semua kategori):

```
│                        │ 3 item dipilih                           │
│                        │ ┌──────────────────────────────────┐     │
│                        │ │ Kamehameha                       │  ^  │
│                        │ │ Spirit Bomb                      │  v  │
│                        │ └──────────────────────────────────┘     │
│                        │                             [Hapus]      │
```

Catatan layout:

- Splitter dengan ukuran awal sekitar 300 dan 700, seperti Roster. Toolbar tetap di atas keduanya.
- Panel mengikuti baris aktif (current index), jadi tombol panah atas dan bawah memperbarui panel langsung.
- Double-click pada daftar tetap membuka dialog edit.
- Kotak centang CaC hanya menampilkan status. Mengubahnya lewat Edit.
- Gaya visual: label kecil di atas tiap bagian (gaya `fieldLabel`), kotak teks dengan latar sedikit lebih gelap dari panel, baris terpilih memakai warna aksen yang sama dengan tombol Save. Tanpa kartu di dalam kartu dan tanpa border di tiap bagian.
- Awoken dan Evasive memakai panel skill yang sama. Characters tetap tabel.

### 4.3 Aturan field

- Skill Type: Strike Skills, Ki Blast Skills, Power Ups / Buffs, Other/Utility. Hanya untuk Super, Ultimate, dan Evasive. Nilai disimpan sebagai kode internal (usulan: `strike`, `ki_blast`, `buff`, `other`) dan labelnya tampil lewat `tr()`, supaya data tidak rusak saat bahasa diganti.
- Ki Used: bilangan bulat opsional. Kosong tampil "–", bukan 0, supaya skill yang belum diisi bisa dibedakan dari yang memang berbiaya nol.
- Deskripsi: isi field `note` yang sudah ada, ditampilkan sebagai kotak teks yang bisa di-scroll.
- Limit Burst dan Effect: teks multibaris.

### 4.4 Item pengerjaan Database

**D1. Skema**

- `SkillEntry` mendapat `skill_type` dan `ki_used`.
- `SuperSoulEntry` mendapat `owner` dan `limit_burst`, dan kehilangan `note`. Note Super Soul yang sudah terisi tidak ikut tersimpan lagi setelah save berikutnya. Kalau ada yang ingin dipertahankan, salin dulu atau ambil dari file backup.
- Data lama dimuat dengan nilai kosong, jadi tidak perlu reset.
- Dict entry baru dibuat di tiga file, dan ketiganya diubah bersamaan: `controllers/undo_commands.py` (auto-register), `views/dialogs/bulk_edit_dialog.py`, dan `_canonicalize_cache_item` di `models/data_store.py`.
- Ikut diperbarui: `schemas.py` (termasuk cabang legacy Title Case), konstanta kolom di `app_config.py`, `_map_col_to_key` di `DatabaseTableModel`.
- Tes baru: serialisasi field baru dan pemuatan data lama (`tests/test_models.py`).

**D2. Dialog edit**

- Dialog skill: Skill Type berupa dropdown tetap yang hanya muncul untuk Super, Ultimate, dan Evasive. `SkillDialog` sekarang hanya menerima label tampilan, jadi dialog perlu diberi tahu kategorinya. Ki Used berupa kolom angka. Label Note menjadi Deskripsi, dan kolomnya multibaris.
- Dialog Super Soul: Owner berupa combo yang bisa diketik dengan pilihan dari nama di Characters. Effect 1, Effect 2, dan Limit Burst berupa kotak teks multibaris. Field Note dihapus.
- Combo yang bisa diketik dengan pencocokan "mengandung" dan tanpa membedakan huruf besar kecil sekarang hanya ada sebagai `_setup_searchable_combo` di `EditorTab`. Fungsinya diangkat menjadi helper di `views/widgets/` dan dipakai tiga tempat: editor, dialog Super Soul, dan judul panel.

**D3. Fungsi "Skill Used by"**

Fungsi murni di `models/`: menerima nama entry dan kategorinya, mengembalikan daftar (karakter, sheet, slot) dari seluruh roster.

- Pemetaan slot: `super_skills` ke Super Skill 1 sampai 4, `ultimate_skills` ke Ultimate Skill 1 dan 2, `awoken_skills` ke Awoken Skill, `evasive_skills` ke Evasive Skill.
- Pencocokan memakai nama persis.
- Baris tampil sebagai "Karakter · Sheet · Slot".
- Double-click pada baris pindah ke sheet itu di Roster (tambahan kecil yang boleh dicoret).
- Mudah dites karena tidak bergantung pada UI.

**D4. Layout master-detail**

- `DatabaseTab._build_ui` memakai `QSplitter` dengan toolbar di atas. Daftar kiri satu kolom berisi nama.
- Panel dibuat satu widget yang isinya mengikuti kategori. Banyak baris terpilih punya tampilannya sendiri.
- Judul panel Super Soul berupa `QStackedWidget` dua halaman (lihat 4.5).
- Seleksi diambil dari current index. Mode seleksi tetap `ExtendedSelection` agar hapus massal tetap jalan.
- Pengecekan sebelum mulai: pastikan filter pencarian di `SearchableTableView` mencakup semua kolom. Dengan begitu Deskripsi dan Effect tetap bisa dicari walau kolomnya tidak tampil di daftar.

**D5. Konfirmasi hapus**

Pesan hapus menyebut berapa preset yang memakai entry itu, memakai fungsi D3 (berlaku untuk skill dan Super Soul).

**D6. Edit Note lewat sel dimatikan**

`setData` di `DatabaseTableModel` menyimpan perubahan Note langsung dengan `store.save()`, tanpa undo. Jalur itu dihapus, termasuk flag `ItemIsEditable` untuk kolom Note, sehingga semua edit Database lewat dialog dan `EditCacheItemCommand`.

**D7. Owner Super Soul terisi otomatis dari Editor**

Lihat aturan lengkap di 4.5.

### 4.5 Aturan owner Super Soul

Pengisian:

- Dari Editor, Super Soul baru mendapat `owner` sama dengan Character Name pada preset yang sedang disimpan. Pengisian hanya terjadi saat entry pertama kali dibuat dan tidak menimpa owner yang sudah ada.
- Jalur "Update This Entry" (`EditPresetEntryCommand`) saat ini tidak memanggil auto-register sama sekali. Jalur itu ikut diperbaiki supaya skill atau Super Soul baru yang dipilih lewat Update juga terdaftar, dengan owner terisi.
- Undo tetap utuh karena command auto-register sudah menyimpan snapshot cache.
- Dari dialog Database, Owner dipilih dari dropdown Characters atau diketik bebas. Yang diketik hanya tersimpan sebagai teks dan tidak menambah karakter baru ke Characters.
- Super Soul lama yang owner-nya kosong tetap kosong sampai diisi dari Database atau dari judul panel.
- Bulk Edit yang mendaftarkan Super Soul baru meninggalkan owner kosong, karena preset yang dipilih bisa milik karakter berbeda.

Judul panel:

- Owner terisi: judul "(owner)'s Super Soul" (contoh: Goku Black's Super Soul). Judul bisa diklik, dan setelah diklik berubah menjadi combo yang bisa dipilih atau diisi.
- Owner kosong: judul langsung berupa combo dengan placeholder "Select or Fill the Character".
- Memilih dari dropdown atau menekan Enter menyimpan owner. Satu pengisian adalah satu langkah undo lewat `EditCacheItemCommand`.
- Esc atau klik di luar membatalkan tanpa mengubah apa pun.
- Enter dengan kolom kosong diabaikan, supaya owner yang sudah terisi tidak hilang tanpa sengaja. Mengosongkan owner dilakukan lewat tombol Edit.
- Owner yang diketik di sini juga hanya tersimpan sebagai teks.
- Saat banyak baris terpilih, judul diganti keterangan jumlah dan combo tidak muncul.
- Combo ini satu-satunya bagian panel yang mengubah data langsung. Bagian lain hanya menampilkan.

---

## 5. Dependensi

- D1 harus lebih dulu dari D2 dan D7.
- D3 harus lebih dulu dari D4 dan D5.
- D6 dikerjakan setelah D4.
- Helper combo yang bisa diketik (D2) dibutuhkan juga oleh D4 dan D7.
- Gaya panel baru di D4 ditulis ke QSS. Kalau D4 selesai sebelum tokenisasi di item 11, gayanya perlu dipindah ke token kemudian.
- Item 8 dan 11 sama-sama butuh tempat menyimpan preferensi.
- Item 12 tidak bergantung pada apa pun. Semua teks baru dari item lain ditulis lewat `tr()`.
- Item 1 sampai 7, 9, dan 10 berdiri sendiri.

---

## 6. Yang sengaja tidak dikerjakan

- Panel detail untuk Characters karena belum di rencanakan.

---

## 7. Batas dokumen

Semua isi berasal dari pembacaan kode dan diskusi. Aplikasi belum dijalankan, jadi hal berikut masih perlu diuji langsung setelah implementasi: kontras tema Light dan Dark, keterbacaan baris terpilih, lebar daftar kiri pada jendela kecil, dan skala tampilan di layar HiDPI (Windows dengan skala 125 atau 150 persen) sebelum build Nuitka.
