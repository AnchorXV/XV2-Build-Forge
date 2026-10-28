from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from app_config import get_resource_path

class SeparatedSpinBox(QWidget):
    valueChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._min = 0
        self._max = 99
        self._value = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.line_edit = QLineEdit()
        self.line_edit.setText("0")
        self.line_edit.setAlignment(Qt.AlignCenter)
        self.line_edit.editingFinished.connect(self._on_edit_finished)
        layout.addWidget(self.line_edit, 1)

        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(2)
        
        self.up_btn = QPushButton()
        self.up_btn.setObjectName("spinUpButton")
        self.up_btn.setIcon(QIcon(str(get_resource_path("assets/icons/chevron_up.svg"))))
        self.up_btn.setIconSize(QSize(10, 10))
        self.up_btn.setFixedSize(28, 17)
        self.up_btn.clicked.connect(self._increment)
        btn_layout.addWidget(self.up_btn)
        
        self.down_btn = QPushButton()
        self.down_btn.setObjectName("spinDownButton")
        self.down_btn.setIcon(QIcon(str(get_resource_path("assets/icons/chevron_down.svg"))))
        self.down_btn.setIconSize(QSize(10, 10))
        self.down_btn.setFixedSize(28, 17)
        self.down_btn.clicked.connect(self._decrement)
        btn_layout.addWidget(self.down_btn)
        
        layout.addWidget(btn_container)

    def setRange(self, minimum, maximum):
        self._min = minimum
        self._max = maximum
        self._value = max(minimum, min(self._value, maximum))
        self.line_edit.setText(str(self._value))

    def setValue(self, val):
        try:
            val = int(val)
        except (ValueError, TypeError):
            val = 0
        self._value = max(self._min, min(val, self._max))
        self.line_edit.setText(str(self._value))

    def value(self):
        return self._value

    def _increment(self):
        if self._value < self._max:
            self._value += 1
            self.line_edit.setText(str(self._value))
            self.valueChanged.emit(self._value)

    def _decrement(self):
        if self._value > self._min:
            self._value -= 1
            self.line_edit.setText(str(self._value))
            self.valueChanged.emit(self._value)

    def _on_edit_finished(self):
        try:
            val = int(self.line_edit.text())
        except ValueError:
            val = self._min
        self.setValue(val)
        self.valueChanged.emit(self._value)