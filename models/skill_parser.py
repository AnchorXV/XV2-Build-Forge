from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ParsedSkill:
    name: str
    skill_id: Optional[str] = None


@dataclass(frozen=True)
class SkillDisplayInfo:
    raw: str
    clean_name: str
    tags: list[str] = field(default_factory=list)
    is_cac: bool = False
    category_hint: Optional[str] = None
    dedup_key: str = ""


def strip_brackets(text: str) -> str:
    cleaned = re.sub(r"\[[^\]]*\]", "", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_bracket_tags(text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"\[([^\]]+)\]", text)]


def parse_skill_display_name(raw: str) -> SkillDisplayInfo:
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
    if not token:
        return False
    if token.isdigit():
        return True
    if len(token) <= 10 and re.match(r"^[A-Za-z0-9_]+$", token):
        return True
    return False


def normalize_for_dedup(name: str) -> str:
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
