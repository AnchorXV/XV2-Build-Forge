import os
import pytest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from models.data_store import AppDataStore
from models.table_models import DatabaseTableModel
from views.widgets.multi_field_filter_proxy import MultiFieldFilterProxy


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def store(tmp_path):
    return AppDataStore(data_file=tmp_path / "test.json")


@pytest.fixture
def skill_model(qapp, store):
    store.dropdown_cache["super_skills"] = [
        {"name": "Kamehameha", "skill_type": "ki_blast", "ki_used": 100, "note": "classic", "is_cac": False},
        {"name": "Spirit Bomb", "skill_type": "ki_blast", "ki_used": 300, "note": "big ball", "is_cac": False},
        {"name": "Afterimage", "skill_type": "other", "ki_used": None, "note": "", "is_cac": False},
    ]
    return DatabaseTableModel(
        store, "super_skills", columns=["Skill Name"], entry_type="skill"
    )


class TestMultiFieldFilter:

    def test_empty_filter_accepts_all(self, qapp, skill_model):
        proxy = MultiFieldFilterProxy(
            ["name", "skill_type", "ki_used", "note"]
        )
        proxy.setSourceModel(skill_model)
        proxy.set_filter_text("")
        assert proxy.rowCount() == 3

    def test_filter_by_name(self, qapp, skill_model):
        proxy = MultiFieldFilterProxy(
            ["name", "skill_type", "ki_used", "note"]
        )
        proxy.setSourceModel(skill_model)
        proxy.set_filter_text("kame")
        assert proxy.rowCount() == 1

    def test_filter_by_skill_type(self, qapp, skill_model):
        proxy = MultiFieldFilterProxy(
            ["name", "skill_type", "ki_used", "note"]
        )
        proxy.setSourceModel(skill_model)
        proxy.set_filter_text("ki_blast")
        assert proxy.rowCount() == 2

    def test_filter_by_note(self, qapp, skill_model):
        proxy = MultiFieldFilterProxy(
            ["name", "skill_type", "ki_used", "note"]
        )
        proxy.setSourceModel(skill_model)
        proxy.set_filter_text("classic")
        assert proxy.rowCount() == 1

    def test_case_insensitive(self, qapp, skill_model):
        proxy = MultiFieldFilterProxy(["name", "note"])
        proxy.setSourceModel(skill_model)
        proxy.set_filter_text("KAMEHAMEHA")
        assert proxy.rowCount() == 1

    def test_no_match(self, qapp, skill_model):
        proxy = MultiFieldFilterProxy(["name", "note"])
        proxy.setSourceModel(skill_model)
        proxy.set_filter_text("zzzz")
        assert proxy.rowCount() == 0