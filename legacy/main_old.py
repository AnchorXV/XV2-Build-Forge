import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QComboBox, QSpinBox, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QGroupBox, QDialog, QDialogButtonBox,
    QLineEdit, QFormLayout, QMenu, QAbstractItemView
)
from PySide6.QtCore import Qt, QPoint
import pandas as pd

CACHE_FILE = "mod_planner_cache_v4.json"

TABLE_COLUMNS = [
    "Character Name", "Character ID", "Costume Name", "Costume Index", "Model Preset",
    "Super Skill 1", "Super Skill 2", "Super Skill 3", "Super Skill 4",
    "Ultimate Skill 1", "Ultimate Skill 2",
    "Awoken Skill", "Evasive Skill", "Super Soul"
]

SUMMARY_COLUMNS = [
    "Character Name", "Total Costume", "Total Preset",
    "Total Super Skill", "Total Ultimate Skill",
    "Total Awoken Skill", "Total Evasive Skill", "Total Super Soul"
]

# =========================================================================
# DIALOGS UNTUK DATABASE MANAGER
# =========================================================================

class CharacterDialog(QDialog):
    def __init__(self, title="Character", data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(360, 160)

        layout = QFormLayout(self)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Contoh: GOK")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Contoh: Goku")
        self.playable_combo = QComboBox()
        self.playable_combo.addItems(["Yes", "No"])

        if data:
            self.code_input.setText(data.get("Code", ""))
            self.name_input.setText(data.get("Name", ""))
            self.playable_combo.setCurrentText(data.get("Playable Character", "Yes"))

        layout.addRow("Character Code:", self.code_input)
        layout.addRow("Character Name:", self.name_input)
        layout.addRow("Playable Character:", self.playable_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        return {
            "Code": self.code_input.text().strip().upper(),
            "Name": self.name_input.text().strip(),
            "Playable Character": self.playable_combo.currentText()
        }


class SkillDialog(QDialog):
    def __init__(self, title, data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(380, 160)

        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.cac_combo = QComboBox()
        self.cac_combo.addItems(["No", "Yes"])
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Contoh: Goku (Super Saiyan Blue)")

        if data:
            self.name_input.setText(data.get("Skill Name", ""))
            self.cac_combo.setCurrentText(data.get("Is CaC Skill?", "No"))
            self.note_input.setText(data.get("Note", ""))

        layout.addRow("Skill Name:", self.name_input)
        layout.addRow("Is CaC Skill?:", self.cac_combo)
        layout.addRow("Note:", self.note_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        return {
            "Skill Name": self.name_input.text().strip(),
            "Is CaC Skill?": self.cac_combo.currentText(),
            "Note": self.note_input.text().strip()
        }


class SuperSoulDialog(QDialog):
    def __init__(self, title, data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 200)

        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.effect1_input = QLineEdit()
        self.effect2_input = QLineEdit()
        self.note_input = QLineEdit()

        if data:
            self.name_input.setText(data.get("Super Soul", ""))
            self.effect1_input.setText(data.get("Effect 1", ""))
            self.effect2_input.setText(data.get("Effect 2", ""))
            self.note_input.setText(data.get("Note", ""))

        layout.addRow("Super Soul Name:", self.name_input)
        layout.addRow("Effect 1:", self.effect1_input)
        layout.addRow("Effect 2:", self.effect2_input)
        layout.addRow("Note:", self.note_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        return {
            "Super Soul": self.name_input.text().strip(),
            "Effect 1": self.effect1_input.text().strip(),
            "Effect 2": self.effect2_input.text().strip(),
            "Note": self.note_input.text().strip()
        }


class SheetDetailDialog(QDialog):
    """Dialog popup untuk menampilkan rincian tabel saat baris sheet di-double click."""
    def __init__(self, table_name, rows_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Content Detail Sheet - [{table_name}]")
        self.resize(1000, 480)

        layout = QVBoxLayout(self)
        table = QTableWidget()
        table.setColumnCount(len(TABLE_COLUMNS))
        table.setHorizontalHeaderLabels(TABLE_COLUMNS)
        table.setRowCount(len(rows_data))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        for r_idx, row in enumerate(rows_data):
            for c_idx, col in enumerate(TABLE_COLUMNS):
                item = QTableWidgetItem(str(row.get(col, "")))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(r_idx, c_idx, item)

        layout.addWidget(table)
        close_btn = QPushButton("Tutup")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


# =========================================================================
# REUSABLE DATABASE MANAGER TAB (INLINE EDIT NOTE VIA 2X KLIK KIRI)
# =========================================================================

class DatabaseManagerTab(QWidget):
    def __init__(self, title, cache_key, columns, entry_type, parent_app):
        super().__init__()
        self.title = title
        self.cache_key = cache_key
        self.columns = columns
        self.entry_type = entry_type
        self.app = parent_app
        self.sort_asc = True

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header Tool Bar
        top_bar = QHBoxLayout()
        add_btn = QPushButton("+")
        add_btn.setToolTip(f"Tambah {self.title} Baru")
        add_btn.setFixedSize(34, 30)
        add_btn.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #2b5797; color: white; border-radius: 4px;")
        add_btn.clicked.connect(self.add_entry)
        top_bar.addWidget(add_btn)

        sort_btn = QPushButton("Sort A-Z")
        sort_btn.setStyleSheet("padding: 5px 12px; font-weight: bold;")
        sort_btn.clicked.connect(self.toggle_sort)
        top_bar.addWidget(sort_btn)

        top_bar.addStretch()

        top_bar.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"Cari {self.title}...")
        self.search_input.setFixedWidth(240)
        self.search_input.textChanged.connect(self.filter_table)
        top_bar.addWidget(self.search_input)

        layout.addLayout(top_bar)

        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

        # Klik kiri 2x akan membuka inline editor pada sel yang memiliki flag editable
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

        # Hubungkan perubahan sel langsung ke cache data
        self.table.cellChanged.connect(self.on_cell_changed)

        # Klik Kanan 1x untuk memunculkan context menu (Edit Dialog / Delete)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)

        layout.addWidget(self.table)
        self.reload_table()

    def reload_table(self):
        # Matikan sinyal saat memuat tabel agar tidak memicu on_cell_changed
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        entries = self.app.dropdown_cache.get(self.cache_key, [])

        for row_idx, item in enumerate(entries):
            self.table.insertRow(row_idx)
            for col_idx, col_name in enumerate(self.columns):
                val = item.get(col_name, "")
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignCenter)

                # Khusus kolom Note pada skill dan super soul: izinkan inline edit
                if col_name == "Note" and self.entry_type in ["skill", "supersoul"]:
                    cell.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
                else:
                    cell.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

                self.table.setItem(row_idx, col_idx, cell)

        self.table.blockSignals(False)
        self.filter_table()

    def on_cell_changed(self, row, col):
        """Menyimpan langsung hasil ketikan di kolom Note ke memori dan cache JSON."""
        col_name = self.columns[col]
        if col_name == "Note" and self.entry_type in ["skill", "supersoul"]:
            new_text = self.table.item(row, col).text().strip()
            if row < len(self.app.dropdown_cache[self.cache_key]):
                self.app.dropdown_cache[self.cache_key][row]["Note"] = new_text
                self.app.save_cache()

    def filter_table(self):
        query = self.search_input.text().lower().strip()
        for row in range(self.table.rowCount()):
            match = any(
                query in (self.table.item(row, col).text().lower() if self.table.item(row, col) else "")
                for col in range(self.table.columnCount())
            )
            self.table.setRowHidden(row, not match)

    def toggle_sort(self):
        if self.entry_type == "char":
            sort_key = "Name"
        elif self.entry_type == "skill":
            sort_key = "Skill Name"
        else:
            sort_key = "Super Soul"

        self.app.dropdown_cache[self.cache_key].sort(
            key=lambda x: str(x.get(sort_key, "")).lower(),
            reverse=not self.sort_asc
        )
        self.sort_asc = not self.sort_asc
        self.reload_table()
        self.app.sync_all_combos()
        self.app.save_cache()

    def open_context_menu(self, point: QPoint):
        item = self.table.itemAt(point)
        if not item:
            return
        row = item.row()
        self.table.selectRow(row)

        menu = QMenu(self)
        edit_act = menu.addAction("Edit")
        del_act = menu.addAction("Delete")

        action = menu.exec(self.table.viewport().mapToGlobal(point))
        if action == edit_act:
            self.edit_entry_at(row)
        elif action == del_act:
            self.delete_entry_at(row)

    def add_entry(self):
        if self.entry_type == "char":
            dlg = CharacterDialog(title="Tambah Character", parent=self)
            key_name = "Name"
        elif self.entry_type == "supersoul":
            dlg = SuperSoulDialog(title="Tambah Super Soul", parent=self)
            key_name = "Super Soul"
        else:
            dlg = SkillDialog(title=f"Tambah {self.title}", parent=self)
            key_name = "Skill Name"

        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if not data.get(key_name):
                QMessageBox.warning(self, "Peringatan", "Kolom nama tidak boleh kosong.")
                return

            self.app.dropdown_cache[self.cache_key].append(data)
            self.reload_table()
            self.app.sync_all_combos()
            self.app.save_cache()

    def edit_entry_at(self, row):
        current_data = self.app.dropdown_cache[self.cache_key][row]
        if self.entry_type == "char":
            dlg = CharacterDialog(title="Edit Character", data=current_data, parent=self)
            key_name = "Name"
        elif self.entry_type == "supersoul":
            dlg = SuperSoulDialog(title="Edit Super Soul", data=current_data, parent=self)
            key_name = "Super Soul"
        else:
            dlg = SkillDialog(title=f"Edit {self.title}", data=current_data, parent=self)
            key_name = "Skill Name"

        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if not data.get(key_name):
                QMessageBox.warning(self, "Peringatan", "Kolom nama tidak boleh kosong.")
                return

            self.app.dropdown_cache[self.cache_key][row] = data
            self.reload_table()
            self.app.sync_all_combos()
            self.app.save_cache()

    def delete_entry_at(self, row):
        if self.entry_type == "char":
            display_val = self.app.dropdown_cache[self.cache_key][row].get("Name", "")
        elif self.entry_type == "supersoul":
            display_val = self.app.dropdown_cache[self.cache_key][row].get("Super Soul", "")
        else:
            display_val = self.app.dropdown_cache[self.cache_key][row].get("Skill Name", "")

        confirm = QMessageBox.question(
            self, "Konfirmasi", f"Hapus '{display_val}' dari database?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.app.dropdown_cache[self.cache_key].pop(row)
            self.reload_table()
            self.app.sync_all_combos()
            self.app.save_cache()


# =========================================================================
# ROSTER TABLE PREVIEW TAB (FIXED MOUSE CLICKS)
# =========================================================================

class RosterPreviewTab(QWidget):
    def __init__(self, parent_app):
        super().__init__()
        self.app = parent_app
        self.sort_asc = True

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header Tool Bar
        top_bar = QHBoxLayout()
        add_btn = QPushButton("+")
        add_btn.setToolTip("Buat Sheet / Tabel Roster Baru")
        add_btn.setFixedSize(34, 30)
        add_btn.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #2b5797; color: white; border-radius: 4px;")
        add_btn.clicked.connect(self.create_new_sheet)
        top_bar.addWidget(add_btn)

        sort_btn = QPushButton("Sort A-Z")
        sort_btn.setStyleSheet("padding: 5px 12px; font-weight: bold;")
        sort_btn.clicked.connect(self.toggle_sort)
        top_bar.addWidget(sort_btn)

        top_bar.addStretch()

        top_bar.addWidget(QLabel("Search Sheet:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari nama sheet/karakter...")
        self.search_input.setFixedWidth(240)
        self.search_input.textChanged.connect(self.filter_table)
        top_bar.addWidget(self.search_input)

        layout.addLayout(top_bar)

        # Summary Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(len(SUMMARY_COLUMNS))
        self.table.setHorizontalHeaderLabels(SUMMARY_COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Klik kiri 1x + Ctrl/Shift untuk multi-select
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Mapping interaksi:
        # Klik kiri 2x -> Preview Sheet Detail
        self.table.cellDoubleClicked.connect(self.on_double_clicked)

        # Klik kanan 1x -> Context Menu (Rename Sheet / Delete Sheet)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)

        layout.addWidget(self.table)

        # Bottom Action Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.addWidget(QLabel("<i>Klik kiri 1x untuk memilih baris, klik kiri 2x untuk melihat isi sheet, klik kanan untuk menu.</i>"))
        bottom_bar.addStretch()

        export_btn = QPushButton("Export Selected")
        export_btn.setStyleSheet("padding: 8px 20px; font-weight: bold; background-color: #1e7145; color: white;")
        export_btn.clicked.connect(self.export_selected_tables)
        bottom_bar.addWidget(export_btn)

        layout.addLayout(bottom_bar)

    def calculate_summary(self, table_name, rows):
        costumes = set()
        supers = set()
        ultimates = set()
        awokens = set()
        evasives = set()
        supersouls = set()

        for r in rows:
            costumes.add(r.get("Costume Index", 0))
            for i in range(1, 5):
                s = r.get(f"Super Skill {i}", "").strip()
                if s:
                    supers.add(s)
            for i in range(1, 3):
                u = r.get(f"Ultimate Skill {i}", "").strip()
                if u:
                    ultimates.add(u)
            aw = r.get("Awoken Skill", "").strip()
            if aw:
                awokens.add(aw)
            ev = r.get("Evasive Skill", "").strip()
            if ev:
                evasives.add(ev)
            ss = r.get("Super Soul", "").strip()
            if ss:
                supersouls.add(ss)

        return {
            "Character Name": table_name,
            "Total Costume": len(costumes),
            "Total Preset": len(rows),
            "Total Super Skill": len(supers),
            "Total Ultimate Skill": len(ultimates),
            "Total Awoken Skill": len(awokens),
            "Total Evasive Skill": len(evasives),
            "Total Super Soul": len(supersouls)
        }

    def reload_table(self):
        self.table.setRowCount(0)
        for row_idx, (tbl_name, rows) in enumerate(self.app.rosters.items()):
            summary = self.calculate_summary(tbl_name, rows)
            self.table.insertRow(row_idx)
            for col_idx, col_name in enumerate(SUMMARY_COLUMNS):
                item = QTableWidgetItem(str(summary[col_name]))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)
        self.filter_table()

    def filter_table(self):
        q = self.search_input.text().lower().strip()
        for row in range(self.table.rowCount()):
            match = any(
                q in (self.table.item(row, col).text().lower() if self.table.item(row, col) else "")
                for col in range(self.table.columnCount())
            )
            self.table.setRowHidden(row, not match)

    def toggle_sort(self):
        sorted_keys = sorted(self.app.rosters.keys(), reverse=not self.sort_asc)
        self.app.rosters = {k: self.app.rosters[k] for k in sorted_keys}
        self.sort_asc = not self.sort_asc
        self.reload_table()

    def on_double_clicked(self, row, col):
        tbl_name = self.table.item(row, 0).text()
        rows = self.app.rosters.get(tbl_name, [])
        dlg = SheetDetailDialog(tbl_name, rows, parent=self)
        dlg.exec()

    def open_context_menu(self, point: QPoint):
        item = self.table.itemAt(point)
        if not item:
            return
        row = item.row()
        # Jangan reset multi-seleksi jika baris yang diklik kanan sudah termasuk dalam pilihan
        if not self.table.item(row, 0).isSelected():
            self.table.selectRow(row)

        tbl_name = self.table.item(row, 0).text()
        menu = QMenu(self)
        rename_act = menu.addAction("Rename Sheet")
        del_act = menu.addAction("Delete Sheet")

        action = menu.exec(self.table.viewport().mapToGlobal(point))
        if action == rename_act:
            self.rename_sheet(tbl_name)
        elif action == del_act:
            self.delete_sheet(tbl_name)

    def create_new_sheet(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Buat Sheet / Tabel Roster Baru")
        layout = QFormLayout(dlg)
        name_in = QLineEdit()
        name_in.setPlaceholderText("Contoh: Broly / Vegito")
        layout.addRow("Nama Sheet:", name_in)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)

        if dlg.exec() == QDialog.Accepted and name_in.text().strip():
            name = name_in.text().strip()
            if name not in self.app.rosters:
                self.app.rosters[name] = []
                if name not in self.app.dropdown_cache["table_names"]:
                    self.app.dropdown_cache["table_names"].append(name)
                self.reload_table()
                self.app.sync_all_combos()
                self.app.save_cache()
            else:
                QMessageBox.warning(self, "Peringatan", "Sheet dengan nama tersebut sudah ada.")

    def rename_sheet(self, old_name):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Rename Sheet: {old_name}")
        layout = QFormLayout(dlg)
        name_in = QLineEdit(old_name)
        layout.addRow("Nama Baru:", name_in)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)

        if dlg.exec() == QDialog.Accepted and name_in.text().strip():
            new_name = name_in.text().strip()
            if new_name != old_name:
                self.app.rosters[new_name] = self.app.rosters.pop(old_name)
                idx = self.app.dropdown_cache["table_names"].index(old_name) if old_name in self.app.dropdown_cache["table_names"] else -1
                if idx >= 0:
                    self.app.dropdown_cache["table_names"][idx] = new_name
                self.reload_table()
                self.app.sync_all_combos()
                self.app.save_cache()

    def delete_sheet(self, name):
        if QMessageBox.question(self, "Konfirmasi", f"Hapus seluruh sheet '{name}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.app.rosters.pop(name, None)
            if name in self.app.dropdown_cache["table_names"]:
                self.app.dropdown_cache["table_names"].remove(name)
            self.reload_table()
            self.app.sync_all_combos()
            self.app.save_cache()

    def get_selected_table_names(self):
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        names = []
        for r in selected_rows:
            names.append(self.table.item(r, 0).text())
        return names

    def export_selected_tables(self):
        selected_names = self.get_selected_table_names()
        if not selected_names:
            QMessageBox.warning(self, "Peringatan", "Pilih minimal satu sheet pada tabel untuk diekspor!")
            return

        mode_multi_file = False
        if len(selected_names) > 1:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Opsi Multi-Sheet Export")
            msg_box.setText(f"Kamu memilih {len(selected_names)} sheet. Pilih metode ekspor:")
            single_file_btn = msg_box.addButton("Satu File (Multi-Sheet)", QMessageBox.ActionRole)
            multi_file_btn = msg_box.addButton("File Terpisah Per Sheet", QMessageBox.ActionRole)
            msg_box.addButton("Batal", QMessageBox.RejectRole)
            msg_box.exec()

            if msg_box.clickedButton() == multi_file_btn:
                mode_multi_file = True
            elif msg_box.clickedButton() != single_file_btn:
                return

        if mode_multi_file:
            folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Output")
            if not folder:
                return

            ext_dlg = QDialog(self)
            ext_dlg.setWindowTitle("Format File")
            e_lay = QFormLayout(ext_dlg)
            cb = QComboBox()
            cb.addItems([".xlsx", ".xls", ".csv"])
            e_lay.addRow("Pilih Format:", cb)
            b = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            b.accepted.connect(ext_dlg.accept)
            b.rejected.connect(ext_dlg.reject)
            e_lay.addRow(b)

            if ext_dlg.exec() != QDialog.Accepted:
                return
            chosen_ext = cb.currentText()

            for tbl in selected_names:
                df = pd.DataFrame(self.app.rosters.get(tbl, []))
                clean_name = "".join(c for c in tbl if c not in "[]:*?/\\")
                target_path = os.path.join(folder, f"{clean_name}{chosen_ext}")

                if chosen_ext == ".xlsx":
                    df.to_excel(target_path, index=False, engine="openpyxl")
                elif chosen_ext == ".xls":
                    try:
                        df.to_excel(target_path, index=False, engine="xlwt")
                    except Exception:
                        df.to_excel(target_path, index=False, engine="openpyxl")
                elif chosen_ext == ".csv":
                    df.to_csv(target_path, index=False, encoding="utf-8-sig")

            QMessageBox.information(self, "Sukses", f"Berhasil mengekspor {len(selected_names)} file ke:\n{folder}")
        else:
            filters = "Excel 2007+ (*.xlsx);;Excel 97-2003 (*.xls);;Comma Separated (*.csv)"
            default_name = f"{selected_names[0]}_Export" if len(selected_names) == 1 else "Combined_Roster_Export"
            file_path, selected_filter = QFileDialog.getSaveFileName(self, "Simpan File Export", default_name, filters)

            if not file_path:
                return

            if "*.csv" in selected_filter:
                if len(selected_names) > 1:
                    combined = []
                    for tbl in selected_names:
                        for row in self.app.rosters.get(tbl, []):
                            r = row.copy()
                            r["Roster Sheet"] = tbl
                            combined.append(r)
                    pd.DataFrame(combined).to_csv(file_path, index=False, encoding="utf-8-sig")
                else:
                    df = pd.DataFrame(self.app.rosters.get(selected_names[0], []))
                    df.to_csv(file_path, index=False, encoding="utf-8-sig")

            elif "*.xls" in selected_filter:
                engine_type = "openpyxl" if file_path.endswith(".xlsx") else "xlwt"
                try:
                    with pd.ExcelWriter(file_path, engine=engine_type) as writer:
                        for tbl in selected_names:
                            clean_sheet = "".join(c for c in tbl if c not in "[]:*?/\\")[:31]
                            pd.DataFrame(self.app.rosters.get(tbl, [])).to_excel(writer, sheet_name=clean_sheet or "Sheet1", index=False)
                except Exception:
                    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                        for tbl in selected_names:
                            clean_sheet = "".join(c for c in tbl if c not in "[]:*?/\\")[:31]
                            pd.DataFrame(self.app.rosters.get(tbl, [])).to_excel(writer, sheet_name=clean_sheet or "Sheet1", index=False)
            else:
                with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                    for tbl in selected_names:
                        clean_sheet = "".join(c for c in tbl if c not in "[]:*?/\\")[:31]
                        pd.DataFrame(self.app.rosters.get(tbl, [])).to_excel(writer, sheet_name=clean_sheet or "Sheet1", index=False)

            QMessageBox.information(self, "Sukses", f"Data berhasil diekspor ke:\n{file_path}")


# =========================================================================
# MAIN WINDOW APLIKASI
# =========================================================================

class ModPlannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XV2 Character Skillset & Build Planner")
        self.resize(1200, 800)

        self.rosters = {}
        self.dropdown_cache = {
            "characters": [],
            "character_ids": [],
            "costume_names": [],
            "super_skills": [],
            "ultimate_skills": [],
            "awoken_skills": [],
            "evasive_skills": [],
            "super_souls": [],
            "table_names": []
        }
        self.load_cache()
        self.init_ui()

    def init_ui(self):
        self.main_tabs = QTabWidget(self)
        self.setCentralWidget(self.main_tabs)

        # Tab 1: Form Input & Planning
        tab_editor = QWidget()
        editor_layout = QVBoxLayout(tab_editor)
        editor_layout.setSpacing(10)

        # Character Info
        char_group = QGroupBox("Character & Costume Info")
        char_grid = QGridLayout(char_group)
        char_grid.setSpacing(8)

        char_grid.addWidget(QLabel("<b>Character Name:</b>"), 0, 0)
        self.char_name_cb = QComboBox()
        self.char_name_cb.setEditable(True)
        self.char_name_cb.editTextChanged.connect(self.on_char_name_changed)
        char_grid.addWidget(self.char_name_cb, 0, 1)

        char_grid.addWidget(QLabel("<b>Character ID / Code:</b>"), 0, 2)
        self.char_id_cb = QComboBox()
        self.char_id_cb.setEditable(True)
        char_grid.addWidget(self.char_id_cb, 0, 3)

        char_grid.addWidget(QLabel("Costume Name:"), 1, 0)
        self.costume_name_cb = QComboBox()
        self.costume_name_cb.setEditable(True)
        char_grid.addWidget(self.costume_name_cb, 1, 1)

        char_grid.addWidget(QLabel("Costume Index:"), 1, 2)
        self.costume_idx_spin = QSpinBox()
        self.costume_idx_spin.setRange(0, 9999)
        char_grid.addWidget(self.costume_idx_spin, 1, 3)

        char_grid.addWidget(QLabel("Model Preset:"), 2, 0)
        self.model_preset_spin = QSpinBox()
        self.model_preset_spin.setRange(0, 9999)
        char_grid.addWidget(self.model_preset_spin, 2, 1)

        editor_layout.addWidget(char_group)

        # Skillset Matrix
        skills_group = QGroupBox("Skillset & Super Soul Matrix")
        skills_grid = QGridLayout(skills_group)
        skills_grid.setSpacing(10)

        self.super_combos = []
        for i in range(4):
            skills_grid.addWidget(QLabel(f"<b>Super Skill {i+1}:</b>"), i, 0)
            cb = QComboBox()
            cb.setEditable(True)
            self.super_combos.append(cb)
            skills_grid.addWidget(cb, i, 1)

        self.ultimate_combos = []
        for i in range(2):
            skills_grid.addWidget(QLabel(f"<b>Ultimate Skill {i+1}:</b>"), i, 2)
            cb = QComboBox()
            cb.setEditable(True)
            self.ultimate_combos.append(cb)
            skills_grid.addWidget(cb, i, 3)

        skills_grid.addWidget(QLabel("<b>Awoken Skill:</b>"), 2, 2)
        self.awoken_cb = QComboBox()
        self.awoken_cb.setEditable(True)
        skills_grid.addWidget(self.awoken_cb, 2, 3)

        skills_grid.addWidget(QLabel("<b>Evasive Skill:</b>"), 3, 2)
        self.evasive_cb = QComboBox()
        self.evasive_cb.setEditable(True)
        skills_grid.addWidget(self.evasive_cb, 3, 3)

        skills_grid.addWidget(QLabel("<b>Super Soul:</b>"), 4, 0)
        self.supersoul_cb = QComboBox()
        self.supersoul_cb.setEditable(True)
        skills_grid.addWidget(self.supersoul_cb, 4, 1, 1, 3)

        editor_layout.addWidget(skills_group)
        editor_layout.addStretch()

        # Action & Target Bar
        commit_group = QGroupBox("Save & Target Destination")
        commit_layout = QHBoxLayout(commit_group)

        commit_layout.addWidget(QLabel("<b>Target Sheet:</b>"))
        self.target_table_cb = QComboBox()
        self.target_table_cb.setEditable(True)
        self.target_table_cb.setPlaceholderText("Ketik nama sheet target (misal: Goku)")
        commit_layout.addWidget(self.target_table_cb, stretch=1)

        reset_btn = QPushButton("Reset Form")
        reset_btn.clicked.connect(self.clear_form)
        commit_layout.addWidget(reset_btn)

        save_btn = QPushButton("Simpan ke Target Tabel")
        save_btn.setStyleSheet("padding: 8px 18px; font-weight: bold; background-color: #2b5797; color: white;")
        save_btn.clicked.connect(self.save_entry)
        commit_layout.addWidget(save_btn)

        editor_layout.addWidget(commit_group)

        # Tab 2: Roster Table Preview Baru
        self.roster_preview_tab = RosterPreviewTab(self)

        # Registrasi Main Tabs
        self.main_tabs.addTab(tab_editor, "Skillset Editor")
        self.main_tabs.addTab(self.roster_preview_tab, "Roster Table Preview")

        # Database Manager Tabs
        char_cols = ["Code", "Name", "Playable Character"]
        skill_cols = ["Skill Name", "Is CaC Skill?", "Note"]
        ss_cols = ["Super Soul", "Effect 1", "Effect 2", "Note"]

        self.manager_tabs = {
            "Character": DatabaseManagerTab("Character", "characters", char_cols, "char", self),
            "Super Skill": DatabaseManagerTab("Super Skill", "super_skills", skill_cols, "skill", self),
            "Ultimate Skill": DatabaseManagerTab("Ultimate Skill", "ultimate_skills", skill_cols, "skill", self),
            "Awoken Skill": DatabaseManagerTab("Awoken Skill", "awoken_skills", skill_cols, "skill", self),
            "Evasive Skill": DatabaseManagerTab("Evasive Skill", "evasive_skills", skill_cols, "skill", self),
            "Super Soul": DatabaseManagerTab("Super Soul", "super_souls", ss_cols, "supersoul", self)
        }

        for tab_name, widget in self.manager_tabs.items():
            self.main_tabs.addTab(widget, tab_name)

        self.sync_all_combos()
        self.roster_preview_tab.reload_table()

    def sync_all_combos(self):
        def update_cb(cb, items):
            cur = cb.currentText()
            cb.blockSignals(True)
            cb.clear()
            cb.addItems(items)
            cb.setEditText(cur)
            cb.blockSignals(False)

        char_names = [c.get("Name", "") for c in self.dropdown_cache["characters"] if c.get("Name")]
        char_codes = [c.get("Code", "") for c in self.dropdown_cache["characters"] if c.get("Code")]
        super_names = [s.get("Skill Name", "") for s in self.dropdown_cache["super_skills"] if s.get("Skill Name")]
        ultimate_names = [s.get("Skill Name", "") for s in self.dropdown_cache["ultimate_skills"] if s.get("Skill Name")]
        awoken_names = [s.get("Skill Name", "") for s in self.dropdown_cache["awoken_skills"] if s.get("Skill Name")]
        evasive_names = [s.get("Skill Name", "") for s in self.dropdown_cache["evasive_skills"] if s.get("Skill Name")]
        ss_names = [s.get("Super Soul", "") for s in self.dropdown_cache["super_souls"] if s.get("Super Soul")]

        update_cb(self.char_name_cb, char_names)
        update_cb(self.char_id_cb, char_codes + self.dropdown_cache["character_ids"])
        update_cb(self.costume_name_cb, self.dropdown_cache["costume_names"])
        update_cb(self.target_table_cb, self.dropdown_cache["table_names"])

        for cb in self.super_combos:
            update_cb(cb, super_names)

        for cb in self.ultimate_combos:
            update_cb(cb, ultimate_names)

        update_cb(self.awoken_cb, awoken_names)
        update_cb(self.evasive_cb, evasive_names)
        update_cb(self.supersoul_cb, ss_names)

    def reload_all_views(self):
        for mgr in self.manager_tabs.values():
            mgr.reload_table()
        self.roster_preview_tab.reload_table()

    def on_char_name_changed(self, text):
        base_name = text.split("(")[0].strip()
        if base_name and not self.target_table_cb.currentText():
            self.target_table_cb.setEditText(base_name)

    def _register_character(self, name, code):
        if not name:
            return
        existing = [c.get("Name", "") for c in self.dropdown_cache["characters"]]
        if name not in existing:
            self.dropdown_cache["characters"].append({
                "Code": code or "MOD",
                "Name": name,
                "Playable Character": "Yes"
            })

    def _register_skill(self, name, cache_key):
        if not name:
            return
        existing = [s.get("Skill Name", "") for s in self.dropdown_cache[cache_key]]
        if name not in existing:
            self.dropdown_cache[cache_key].append({
                "Skill Name": name,
                "Is CaC Skill?": "No",
                "Note": ""
            })

    def _register_supersoul(self, name):
        if not name:
            return
        existing = [s.get("Super Soul", "") for s in self.dropdown_cache["super_souls"]]
        if name not in existing:
            self.dropdown_cache["super_souls"].append({
                "Super Soul": name,
                "Effect 1": "",
                "Effect 2": "",
                "Note": ""
            })

    def _register_simple(self, val, cache_key):
        if val and val not in self.dropdown_cache[cache_key]:
            self.dropdown_cache[cache_key].append(val)

    def save_entry(self):
        target_table = self.target_table_cb.currentText().strip()
        if not target_table:
            QMessageBox.warning(self, "Validasi Gagal", "Harap tentukan nama Target Tabel / Sheet!")
            return

        char_name = self.char_name_cb.currentText().strip()
        if not char_name:
            QMessageBox.warning(self, "Validasi Gagal", "Field Character Name tidak boleh kosong!")
            return

        char_id = self.char_id_cb.currentText().strip()
        costume_name = self.costume_name_cb.currentText().strip()
        costume_idx = self.costume_idx_spin.value()
        model_preset = self.model_preset_spin.value()

        supers = [cb.currentText().strip() for cb in self.super_combos]
        ultimates = [cb.currentText().strip() for cb in self.ultimate_combos]
        awoken = self.awoken_cb.currentText().strip()
        evasive = self.evasive_cb.currentText().strip()
        supersoul = self.supersoul_cb.currentText().strip()

        self._register_character(char_name, char_id)
        self._register_simple(char_id, "character_ids")
        self._register_simple(costume_name, "costume_names")
        self._register_simple(target_table, "table_names")

        for s in supers:
            self._register_skill(s, "super_skills")
        for u in ultimates:
            self._register_skill(u, "ultimate_skills")

        self._register_skill(awoken, "awoken_skills")
        self._register_skill(evasive, "evasive_skills")
        self._register_supersoul(supersoul)

        entry = {
            "Character Name": char_name,
            "Character ID": char_id,
            "Costume Name": costume_name,
            "Costume Index": costume_idx,
            "Model Preset": model_preset,
            "Super Skill 1": supers[0],
            "Super Skill 2": supers[1],
            "Super Skill 3": supers[2],
            "Super Skill 4": supers[3],
            "Ultimate Skill 1": ultimates[0],
            "Ultimate Skill 2": ultimates[1],
            "Awoken Skill": awoken,
            "Evasive Skill": evasive,
            "Super Soul": supersoul
        }

        if target_table not in self.rosters:
            self.rosters[target_table] = []

        self.rosters[target_table].append(entry)

        self.sync_all_combos()
        self.reload_all_views()
        self.save_cache()

        QMessageBox.information(self, "Berhasil Disimpan", f"Entri preset berhasil dimasukkan ke tabel: '{target_table}'")
        self.clear_form()

    def clear_form(self):
        for cb in [self.char_name_cb, self.char_id_cb, self.costume_name_cb,
                   self.awoken_cb, self.evasive_cb, self.supersoul_cb]:
            cb.blockSignals(True)
            cb.setEditText("")
            cb.setCurrentIndex(-1)
            cb.blockSignals(False)

        for cb in self.super_combos + self.ultimate_combos:
            cb.blockSignals(True)
            cb.setEditText("")
            cb.setCurrentIndex(-1)
            cb.blockSignals(False)

        self.costume_idx_spin.setValue(0)
        self.model_preset_spin.setValue(0)

    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for k in self.dropdown_cache:
                        if k in loaded:
                            self.dropdown_cache[k] = loaded[k]
                    if "rosters" in loaded:
                        self.rosters = loaded["rosters"]
            except Exception:
                pass

    def save_cache(self):
        try:
            save_payload = dict(self.dropdown_cache)
            save_payload["rosters"] = self.rosters
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(save_payload, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModPlannerApp()
    window.show()
    sys.exit(app.exec())