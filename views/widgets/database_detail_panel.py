from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from controllers.undo_commands import EditCacheItemCommand
from locales.i18n_manager import tr
from models.character_usage import find_skill_usage
from views.widgets.searchable_combo import populate_combo, setup_searchable_combo

SKILL_CATEGORIES = {"super_skills", "ultimate_skills", "awoken_skills", "evasive_skills"}
SUPER_SOUL_CATEGORY = "super_souls"

class DatabaseDetailPanel(QFrame):

    navigate_requested = Signal(str, str)
    edit_requested = Signal()
    delete_requested = Signal()

    def __init__(
        self,
        store,
        undo_stack: QUndoStack,
        category_key: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("databaseDetailPanel")
        self._store = store
        self._undo_stack = undo_stack
        self._category = category_key
        self._current_row = -1
        self._current_entry: Optional[dict] = None
        self._is_skill = category_key in SKILL_CATEGORIES
        self._is_soul = category_key == SUPER_SOUL_CATEGORY

        self._build_ui()
        self.clear()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._stack = QStackedWidget()
        outer.addWidget(self._stack)

        self._multi_page = self._build_multi_page()
        self._stack.addWidget(self._multi_page)

        self._single_page = self._build_single_page()
        self._stack.addWidget(self._single_page)

    def _build_multi_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        self._multi_label = QLabel("")
        self._multi_label.setObjectName("panelTitle")
        layout.addWidget(self._multi_label)

        self._multi_list = QListWidget()
        self._multi_list.setObjectName("panelList")
        layout.addWidget(self._multi_list, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._multi_delete_btn = QPushButton(tr("database.character_panel.delete"))
        self._multi_delete_btn.setObjectName("dangerButton")
        self._multi_delete_btn.clicked.connect(self.delete_requested.emit)
        btn_row.addWidget(self._multi_delete_btn)
        layout.addLayout(btn_row)

        return page

    def _build_single_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("characterDetailScroll")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        if self._is_soul:
            self._title_stack = QStackedWidget()
            self._title_label = QLabel("")
            self._title_label.setObjectName("panelTitle")
            self._title_label.setCursor(Qt.PointingHandCursor)
            self._title_label.mousePressEvent = self._on_title_clicked
            self._title_stack.addWidget(self._title_label)

            self._title_combo = QComboBox()
            setup_searchable_combo(self._title_combo)
            self._populate_owners()
            self._title_combo.lineEdit().returnPressed.connect(self._on_owner_committed)
            self._title_combo.lineEdit().editingFinished.connect(self._on_owner_editing_finished)
            self._title_stack.addWidget(self._title_combo)

            self._title_stack.setCurrentIndex(0)
            layout.addWidget(self._title_stack)
        else:
            self._title_label = QLabel("")
            self._title_label.setObjectName("panelTitle")
            layout.addWidget(self._title_label)

        if self._is_skill:
            self._skill_type_label = self._make_field_label(tr("dialog.skill.label_skill_type"))
            self._skill_type_value = QLabel("")
            self._skill_type_value.setObjectName("panelValue")
            layout.addWidget(self._skill_type_label)
            layout.addWidget(self._skill_type_value)

            self._ki_label = self._make_field_label(tr("dialog.skill.label_ki_used"))
            self._ki_value = QLabel("")
            self._ki_value.setObjectName("panelValue")
            layout.addWidget(self._ki_label)
            layout.addWidget(self._ki_value)

            self._cac_cb = QCheckBox(tr("dialog.skill.label_cac"))
            self._cac_cb.setEnabled(False)
            layout.addWidget(self._cac_cb)

            self._desc_label = self._make_field_label(tr("dialog.skill.label_description"))
            layout.addWidget(self._desc_label)

            self._desc_value = QPlainTextEdit()
            self._desc_value.setReadOnly(True)
            self._desc_value.setMinimumHeight(80)
            self._desc_value.setMaximumHeight(140)
            layout.addWidget(self._desc_value)

            self._usage_label = self._make_field_label("")
            layout.addWidget(self._usage_label)

            self._usage_list = QListWidget()
            self._usage_list.setObjectName("panelList")
            self._usage_list.setMinimumHeight(100)
            self._usage_list.setMaximumHeight(180)
            self._usage_list.itemDoubleClicked.connect(self._on_usage_double_clicked)
            layout.addWidget(self._usage_list)

        if self._is_soul:
            self._effect1_label = self._make_field_label(tr("dialog.super_soul.label_effect1"))
            layout.addWidget(self._effect1_label)
            self._effect1_value = QPlainTextEdit()
            self._effect1_value.setReadOnly(True)
            self._effect1_value.setMinimumHeight(60)
            layout.addWidget(self._effect1_value)

            self._effect2_label = self._make_field_label(tr("dialog.super_soul.label_effect2"))
            layout.addWidget(self._effect2_label)
            self._effect2_value = QPlainTextEdit()
            self._effect2_value.setReadOnly(True)
            self._effect2_value.setMinimumHeight(60)
            layout.addWidget(self._effect2_value)

            self._limit_label = self._make_field_label(tr("dialog.super_soul.label_limit_burst"))
            layout.addWidget(self._limit_label)
            self._limit_value = QPlainTextEdit()
            self._limit_value.setReadOnly(True)
            self._limit_value.setMinimumHeight(60)
            layout.addWidget(self._limit_value)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        self._edit_btn = QPushButton(tr("database.character_panel.edit"))
        self._edit_btn.setObjectName("secondaryButton")
        self._edit_btn.clicked.connect(self.edit_requested.emit)
        btn_row.addWidget(self._edit_btn)

        self._delete_btn = QPushButton(tr("database.character_panel.delete"))
        self._delete_btn.setObjectName("dangerButton")
        self._delete_btn.clicked.connect(self.delete_requested.emit)
        btn_row.addWidget(self._delete_btn)

        layout.addLayout(btn_row)

        scroll.setWidget(container)
        outer.addWidget(scroll)

        return page

    @staticmethod
    def _make_field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("panelFieldLabel")
        return label

    def _populate_owners(self) -> None:
        try:
            chars = self._store.get_cache("characters")
        except Exception:
            chars = []
        names = sorted([c.get("name", "") for c in chars if c.get("name")])
        populate_combo(self._title_combo, names)

    def clear(self) -> None:
        self._current_row = -1
        self._current_entry = None
        self._stack.setCurrentIndex(1)
        self._title_label.setText(tr("database.character_panel.no_selection"))
        if self._is_soul:
            self._title_stack.setCurrentIndex(0)
        if self._is_skill:
            self._skill_type_value.setText("")
            self._ki_value.setText("")
            self._cac_cb.setChecked(False)
            self._desc_value.setPlainText("")
            self._usage_label.setText("")
            self._usage_list.clear()
        if self._is_soul:
            self._effect1_value.setPlainText("")
            self._effect2_value.setPlainText("")
            self._limit_value.setPlainText("")
        self._set_buttons_enabled(False)

    def set_single(self, row: int, entry: dict) -> None:
        self._current_row = row
        self._current_entry = entry
        self._stack.setCurrentIndex(1)
        name = entry.get("name", "") or "—"

        if self._is_soul:
            owner = entry.get("owner", "").strip()
            self._update_soul_title(owner)
            self._title_stack.setCurrentIndex(0)
            self._effect1_value.setPlainText(entry.get("effect_1", ""))
            self._effect2_value.setPlainText(entry.get("effect_2", ""))
            self._limit_value.setPlainText(entry.get("limit_burst", ""))
        else:
            self._title_label.setText(name)

        if self._is_skill:
            self._skill_type_label.show()
            self._skill_type_value.show()
            skill_type = entry.get("skill_type", "")
            self._skill_type_value.setText(
                tr(f"dialog.skill.type.{skill_type}") if skill_type else "—"
            )

            ki = entry.get("ki_used")
            self._ki_value.setText(str(ki) if ki is not None else "—")
            self._cac_cb.setChecked(bool(entry.get("is_cac", False)))
            self._desc_value.setPlainText(entry.get("note", ""))
            self._populate_usage(name)

        self._set_buttons_enabled(True)

    def set_multi(self, selected_entries: list[dict]) -> None:
        self._stack.setCurrentIndex(0)
        count = len(selected_entries)
        self._multi_label.setText(
            tr("database.character_panel.multi_selected", count=count)
        )
        self._multi_list.clear()
        for e in selected_entries:
            self._multi_list.addItem(e.get("name", "") or "—")
        self._set_buttons_enabled(True)
        self._edit_btn.hide()

    def _populate_usage(self, skill_name: str) -> None:
        if not skill_name:
            self._usage_label.setText("")
            self._usage_list.clear()
            return

        usage = find_skill_usage(self._store, skill_name, self._category)
        self._usage_label.setText(
            tr("database.character_panel.skill_used_by", name=skill_name)
        )
        self._usage_list.clear()
        for u in usage:
            item = QListWidgetItem(u.display_label())
            item.setData(Qt.UserRole, {"sheet": u.sheet_name, "entry_id": u.entry_id})
            self._usage_list.addItem(item)

    def _on_usage_double_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.UserRole)
        if data:
            self.navigate_requested.emit(data["sheet"], data["entry_id"])

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self._edit_btn.setEnabled(enabled)
        self._delete_btn.setEnabled(enabled)
        self._multi_delete_btn.setEnabled(enabled)

    def current_row(self) -> int:
        return self._current_row

    def _update_soul_title(self, owner: str) -> None:
        if owner:
            self._title_label.setText(
                tr("database.character_panel.soul_title_with_owner", owner=owner)
            )
        else:
            self._title_label.setText(tr("database.character_panel.soul_title_empty"))

    def _on_title_clicked(self, event) -> None:
        if self._current_entry is None:
            return
        owner = self._current_entry.get("owner", "").strip()
        self._title_combo.blockSignals(True)
        self._title_combo.setCurrentText(owner)
        self._title_combo.blockSignals(False)
        self._title_stack.setCurrentIndex(1)
        self._title_combo.setFocus()
        self._title_combo.lineEdit().selectAll()

    def _on_owner_committed(self) -> None:
        new_owner = self._title_combo.currentText().strip()
        if not new_owner:
            self._title_stack.setCurrentIndex(0)
            return
        self._commit_owner(new_owner)

    def _on_owner_editing_finished(self) -> None:
        if self._title_stack.currentIndex() == 1:
            self._title_stack.setCurrentIndex(0)

    def _commit_owner(self, new_owner: str) -> None:
        items = self._store.get_cache(self._category)
        row = self._current_row
        if row < 0 or row >= len(items):
            return
        old_entry = items[row]
        if old_entry.get("owner", "") == new_owner:
            self._title_stack.setCurrentIndex(0)
            return
        new_entry = dict(old_entry)
        new_entry["owner"] = new_owner
        cmd = EditCacheItemCommand(self._store, self._category, row, old_entry, new_entry)
        self._undo_stack.push(cmd)
        self._current_entry = new_entry
        self._update_soul_title(new_owner)
        self._title_stack.setCurrentIndex(0)