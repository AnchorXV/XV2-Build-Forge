"""
DBXV2 Build Forge — Skill Input Parser & Normaliser.

Handles the ``"Skill Name : ID"`` pattern and bracket tags (``[Awoken]``, ``[CaC]``)
common in DBXV2 modding data, providing normalisation for deduplication (PRD §3.4, §3.5).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ParsedSkill:
    """Result of parsing a raw skill input string.

    Attributes:
        name: The cleaned skill display name.
        skill_id: Optional numeric/string ID extracted from the input.
    """
    name: str
    skill_id: Optional[str] = None


@dataclass(frozen=True)
class SkillDisplayInfo:
    """Detailed breakdown of a skill's display text with extracted tags.

    Attributes:
        raw: The original unparsed string.
        clean_name: The name with bracket tags stripped.
        tags: List of extracted tag strings (e.g. ``["Awoken", "CaC"]``).
        is_cac: True if ``"CaC"`` is among the bracket tags.
        category_hint: First recognised category tag (``Awoken``, ``Super``, etc.) if any.
        dedup_key: Normalised key suitable for deduplication.
    """
    raw: str
    clean_name: str
    tags: list[str] = field(default_factory=list)
    is_cac: bool = False
    category_hint: Optional[str] = None
    dedup_key: str = ""


def strip_brackets(text: str) -> str:
    """Remove all bracketed tags like ``[Awoken]`` or ``[CaC]`` and collapse whitespace.

    Examples:
        >>> strip_brackets("[Awoken] Super Saiyan God")
        'Super Saiyan God'
        >>> strip_brackets("Kamehameha [CaC]")
        'Kamehameha'
    """
    cleaned = re.sub(r"\[[^\]]*\]", "", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_bracket_tags(text: str) -> list[str]:
    """Extract all text inside square brackets.

    Examples:
        >>> extract_bracket_tags("[Awoken] [CaC] Potential Unleashed")
        ['Awoken', 'CaC']
    """
    return [match.group(1).strip() for match in re.finditer(r"\[([^\]]+)\]", text)]


def parse_skill_display_name(raw: str) -> SkillDisplayInfo:
    """Parse a skill display string, extracting bracket tags and normalising.

    Args:
        raw: The raw skill display name string.

    Returns:
        A ``SkillDisplayInfo`` containing cleaned name, tags, and dedup key.
    """
    clean_name = strip_brackets(raw)
    tags = extract_bracket_tags(raw)
    is_cac = any(t.lower() == "cac" for t in tags)

    known_categories = {"super", "ultimate", "awoken", "evasive"}
    category_hint = None
    for t in tags:
        if t.lower() in known_categories:
            category_hint = t
            break

    dedup = normalize_for_dedup(clean_name)
    return SkillDisplayInfo(
        raw=raw,
        clean_name=clean_name,
        tags=tags,
        is_cac=is_cac,
        category_hint=category_hint,
        dedup_key=dedup,
    )


def parse_skill_input(raw: str) -> ParsedSkill:
    """Parse a raw skill input string into name and optional ID.

    Recognised patterns:
        - ``"Kamehameha : 1024"`` → name ``"Kamehameha"``, skill_id ``"1024"``
        - ``"A : B : 123"`` → name ``"A : B"``, skill_id ``"123"``
        - ``"Kamehameha"`` → name ``"Kamehameha"``, skill_id ``None``

    Args:
        raw: The raw user input string.

    Returns:
        A ``ParsedSkill`` with cleaned name and optional ID.
    """
    raw = raw.strip()
    if not raw:
        return ParsedSkill(name="", skill_id=None)

    if " : " in raw:
        parts = raw.split(" : ")
    elif ":" in raw:
        parts = raw.split(":")
    else:
        return ParsedSkill(name=raw.strip(), skill_id=None)

    candidate_id = parts[-1].strip()
    if _looks_like_id(candidate_id):
        name = " : ".join(p.strip() for p in parts[:-1]).strip()
        return ParsedSkill(name=name or raw.strip(), skill_id=candidate_id)

    return ParsedSkill(name=raw.strip(), skill_id=None)


def _looks_like_id(token: str) -> bool:
    """Heuristic: a token is treated as an ID if it is numeric or short code."""
    if not token:
        return False
    if token.isdigit():
        return True
    if len(token) <= 10 and re.match(r"^[A-Za-z0-9_]+$", token):
        return True
    return False


def normalize_for_dedup(name: str) -> str:
    """Normalise a skill/item name for duplicate detection.

    Transformations applied:
        1. Strip bracketed tags (e.g. ``[Awoken]``).
        2. Strip leading/trailing whitespace and collapse internal spaces.
        3. Lowercase.
        4. Strip non-alphanumeric characters at edges.
    """
    if not name:
        return ""
    # Strip brackets first
    name = strip_brackets(name)
    # Collapse whitespace
    result = re.sub(r"\s+", " ", name.strip())
    # Lowercase
    result = result.lower()
    # Strip non-alnum at edges
    result = re.sub(r"^[^a-z0-9]+", "", result)
    result = re.sub(r"[^a-z0-9]+$", "", result)
    return result
