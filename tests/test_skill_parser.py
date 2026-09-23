"""
Unit tests for models.skill_parser (PRD §3.5).
"""

import pytest

from models.skill_parser import (
    extract_bracket_tags,
    normalize_for_dedup,
    parse_skill_display_name,
    strip_brackets,
)


class TestSkillParser:
    def test_strip_brackets_simple(self):
        raw = "[Awoken] Super Saiyan God"
        assert strip_brackets(raw) == "Super Saiyan God"

    def test_strip_brackets_multiple(self):
        raw = "[Awoken] [CaC] Potential Unleashed"
        assert strip_brackets(raw) == "Potential Unleashed"

    def test_strip_brackets_no_brackets(self):
        raw = "Kamehameha"
        assert strip_brackets(raw) == "Kamehameha"

    def test_extract_bracket_tags(self):
        raw = "[Awoken] [CaC] Beast [Custom]"
        tags = extract_bracket_tags(raw)
        assert tags == ["Awoken", "CaC", "Custom"]

    def test_extract_bracket_tags_empty(self):
        assert extract_bracket_tags("Galick Gun") == []

    def test_normalize_for_dedup(self):
        s1 = "[Awoken] Super Saiyan God"
        s2 = "super  saiyan god"
        s3 = "Super Saiyan God [CaC]"
        assert normalize_for_dedup(s1) == normalize_for_dedup(s2) == normalize_for_dedup(s3)

    def test_parse_skill_display_name(self):
        raw = "  [Awoken] [CaC]  Super Saiyan  "
        parsed = parse_skill_display_name(raw)
        assert parsed.raw == raw
        assert parsed.clean_name == "Super Saiyan"
        assert parsed.tags == ["Awoken", "CaC"]
        assert parsed.is_cac is True
        assert parsed.category_hint == "Awoken"
        assert parsed.dedup_key == "super saiyan"
