# Panduan Kompilasi Standalone EXE dengan Nuitka
## DBXV2 Build Forge — Roster & Moveset Planner

Dokumen ini menjelaskan langkah-langkah mem-package aplikasi **DBXV2 Build Forge** menjadi file executable tunggal (`.exe`) mandiri pada Windows menggunakan **Nuitka (onefile mode)** sesuai spesifikasi PRD §5.

---

## 1. Prasyarat Lingkungan Build

1. **Python 3.10+ (64-bit)** telah terpasang dan terdaftar di `PATH`.
2. **C Compiler:** Nuitka membutuhkan C/C++ compiler. Sangat direkomendasikan salah satu dari:
   - **MSVC (Microsoft Visual C++):** Melalui *Visual Studio Community* atau *Build Tools for Visual Studio* (komponen: "Desktop development with C++").
   - **MinGW64 (gcc):** Nuitka dapat mengunduh MinGW64 otomatis saat pertama kali dijalankan jika MSVC tidak terdeteksi.
3. Dependensi Python terinstal:
   ```bash
   pip install -r requirements.txt
   pip install nuitka zstandard ordered-set
   ```

---

## 2. Command Build Resmi (Onefile Mode)

Jalankan perintah berikut dari root folder proyek (`c:\Users\diand\Downloads\Documents\Character Planner`):

```powershell
python -m nuitka `
    --onefile `
    --standalone `
    --enable-plugin=pyside6 `
    --include-data-dir=styles=styles `
    --include-data-dir=locales=locales `
    --windows-console-mode=disable `
    --output-filename="DBXV2_Build_Forge.exe" `
    --company-name="DBXV2Modding" `
    --product-name="DBXV2 Build Forge" `
    --file-version="1.0.0" `
    --product-version="1.0.0" `
    --file-description="DBXV2 Build Forge — Roster & Moveset Planner" `
    main.py
```

### Penjelasan Parameter:
- `--onefile`: Menghasilkan 1 file executable tunggal (`DBXV2_Build_Forge.exe`) tanpa folder dependency terpisah.
- `--enable-plugin=pyside6`: Mengaktifkan plugin resmi Nuitka untuk PySide6 (menangani deteksi otomatis DLL Qt, plugin platform, dan dependensi QtCore/QtGui/QtWidgets).
- `--include-data-dir=styles=styles`: Membundel file stylesheet (`light_theme.qss`, `dark_theme.qss`) ke dalam executable dan dapat diakses via `app_config.get_resource_path()`.
- `--include-data-dir=locales=locales`: Membundel file kamus bahasa (`en.json`, `id.json`, `ja.json`).
- `--windows-console-mode=disable`: Menyembunyikan jendela CMD/terminal hitam di latar belakang saat aplikasi GUI dibuka oleh pengguna.
- `--output-filename="DBXV2_Build_Forge.exe"`: Menentukan nama file keluaran `.exe`.

---

## 3. Opsional: Menambahkan Ikon Aplikasi (`.ico`)

Jika nantinya Anda memiliki file ikon `icon.ico`, tambahkan flag berikut ke perintah di atas:
```powershell
    --windows-icon-from-ico=icon.ico `
```

---

## 4. Struktur Output & Lokasi Data

Setelah proses kompilasi selesai:
1. File binary mandiri akan berada di direktori saat ini: `DBXV2_Build_Forge.exe`.
2. Saat dijalankan oleh pengguna, file data JSON (`build_forge_data.json`) dan file backup (`build_forge_data.json.bak`) akan otomatis dibuat di folder kerja tempat pengguna menjalankan `.exe` tersebut (Current Working Directory).
3. File konfigurasi tema dan bahasa aktif tersimpan otomatis di dalam file data tersebut.

---

## 5. Tips Pemecahan Masalah (Troubleshooting)

- **Antivirus False Positive:** Karena Nuitka melakukan packing onefile mandiri, beberapa Windows Defender terkadang memeriksa hash file baru. Jika proses kompilasi terblokir, tambahkan pengecualian sementara pada folder build.
- **Peringatan Compiler:** Jika muncul pesan `Nuitka: The C compiler is not found`, jawab `yes` ketika Nuitka menawarkan untuk mengunduh gcc/MinGW64 otomatis.
- **Verifikasi Sebelum Rilis:** Uji coba jalankan `DBXV2_Build_Forge.exe` di mesin atau folder bersih lain tanpa Python untuk memastikan seluruh DLL Qt dan resource QSS/JSON terbawa dengan sempurna.
