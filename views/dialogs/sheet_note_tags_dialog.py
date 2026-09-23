"""
DBXV2 Build Forge — Sheet Note & Tags Dialog.

Provides a UI to edit a sheet's note and tags.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QLineEdit,
    QPushButton,
)
from PySide6.QtCore import Qt

from locales.i18n_manager import tr


class SheetNoteTagsDialog(QDialog):
    """Dialog to edit Note and Tags for a given RosterSheet."""

    def __init__(self, sheet_name: str, meta: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("roster.dialog.note_tags_title", name=sheet_name))
        self.resize(400, 300)
        
        self.sheet_name = sheet_name
        self.note = meta.get("note", "")
        self.tags = meta.get("tags", [])
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Note
        note_label = QLabel(tr("roster.dialog.note_tags_note_label"))
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText(tr("roster.dialog.note_tags_note_placeholder"))
        self.note_edit.setPlainText(self.note)
        
        # Tags
        tags_label = QLabel(tr("roster.dialog.note_tags_tags_label"))
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText(tr("roster.dialog.note_tags_tags_placeholder"))
        self.tags_edit.setText(", ".join(self.tags))
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton(tr("dialog.common.cancel"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok = QPushButton(tr("dialog.common.ok"))
        self.btn_ok.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)

        layout.addWidget(note_label)
        layout.addWidget(self.note_edit)
        layout.addWidget(tags_label)
        layout.addWidget(self.tags_edit)
        layout.addLayout(btn_layout)

    def get_meta(self) -> dict:
        """Return the updated meta dict."""
        note = self.note_edit.toPlainText().strip()
        tags_raw = self.tags_edit.text()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        return {"note": note, "tags": tags}
