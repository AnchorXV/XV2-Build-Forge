from models.skill_parser import (
    extract_bracket_tags,
    normalize_for_dedup,
    parse_skill_display_name,
    parse_skill_input,
    strip_brackets,
)


class TestStripBrackets:

    def test_simple(self):
        assert strip_brackets("[Awoken] Super Saiyan God") == "Super Saiyan God"

    def test_multiple(self):
        assert strip_brackets("[Awoken] [CaC] Potential Unleashed") == "Potential Unleashed"

    def test_no_brackets(self):
        assert strip_brackets("Kamehameha") == "Kamehameha"

    def test_collapses_whitespace(self):
        assert strip_brackets("[Awoken]   Super   Saiyan") == "Super Saiyan"

    def test_empty_brackets(self):
        assert strip_brackets("[] Name") == "Name"


class TestExtractBracketTags:

    def test_multiple(self):
        assert extract_bracket_tags("[Awoken] [CaC] Beast [Custom]") == ["Awoken", "CaC", "Custom"]

    def test_no_tags(self):
        assert extract_bracket_tags("Galick Gun") == []

    def test_whitespace_inside_brackets(self):
        assert extract_bracket_tags("[ Awoken ] Name") == ["Awoken"]

    def test_empty_brackets(self):
        assert extract_bracket_tags("[] Name") == []


class TestNormalizeForDedup:

    def test_variants_match(self):
        s1 = "[Awoken] Super Saiyan God"
        s2 = "super  saiyan god"
        s3 = "Super Saiyan God [CaC]"
        assert normalize_for_dedup(s1) == normalize_for_dedup(s2) == normalize_for_dedup(s3)

    def test_empty(self):
        assert normalize_for_dedup("") == ""

    def test_strips_leading_trailing_punctuation(self):
        assert normalize_for_dedup("!!! Name !!!") == "name"


class TestParseSkillDisplayName:

    def test_full_parse(self):
        raw = "  [Awoken] [CaC]  Super Saiyan  "
        parsed = parse_skill_display_name(raw)
        assert parsed.raw == raw
        assert parsed.clean_name == "Super Saiyan"
        assert parsed.tags == ["Awoken", "CaC"]
        assert parsed.is_cac is True
        assert parsed.category_hint == "Awoken"
        assert parsed.dedup_key == "super saiyan"

    def test_no_tags(self):
        parsed = parse_skill_display_name("Kamehameha")
        assert parsed.clean_name == "Kamehameha"
        assert parsed.tags == []
        assert parsed.is_cac is False
        assert parsed.category_hint is None
        assert parsed.dedup_key == "kamehameha"


class TestParseSkillInput:

    def test_simple_name(self):
        result = parse_skill_input("Kamehameha")
        assert result.name == "Kamehameha"
        assert result.skill_id is None

    def test_name_with_numeric_id(self):
        result = parse_skill_input("Kamehameha : 1024")
        assert result.name == "Kamehameha"
        assert result.skill_id == "1024"

    def test_name_with_multiple_colons(self):
        result = parse_skill_input("A : B : 123")
        assert result.name == "A : B"
        assert result.skill_id == "123"

    def test_empty_input(self):
        result = parse_skill_input("")
        assert result.name == ""
        assert result.skill_id is None

    def test_no_space_around_colon(self):
        result = parse_skill_input("Kamehameha:1024")
        assert result.name == "Kamehameha"
        assert result.skill_id == "1024"

    def test_id_with_alphanumeric(self):
        result = parse_skill_input("Kamehameha : ABC_123")
        assert result.name == "Kamehameha"
        assert result.skill_id == "ABC_123"

    def test_long_description_kept_as_name(self):
        result = parse_skill_input("Kamehameha : This is a long description")
        assert result.name == "Kamehameha : This is a long description"
        assert result.skill_id is None