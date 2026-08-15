#!/usr/bin/env python3
"""Validate the structural contract for completed cheat sheets."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SHEETS = ROOT / "cheat-sheets" / "correctness"
REQUIRED_FIELDS = (
    "title",
    "bug_classes",
    "authority",
    "mechanizable",
    "maturity",
    "last_reviewed",
)
HEADINGS = (
    "Why review misses it",
    "The default",
    "Rules",
    "Anti-patterns",
    "What it costs",
    "Review questions",
    "How to mechanize",
    "References",
)
ENUMS = {
    "authority": {"individual", "design", "organizational"},
    "mechanizable": {
        "type",
        "lint",
        "property-test",
        "assertion",
        "observation",
        "none",
    },
    "maturity": {"draft", "reviewed"},
}


def section(text: str, name: str) -> str:
    match = re.search(
        rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    return match.group(1) if match else ""


def local_link_errors(path: Path, text: str) -> list[str]:
    errors = []
    for target in re.findall(r"\[[^]]*\]\(([^)]+)\)", text):
        if "://" in target or target.startswith(("#", "mailto:")):
            continue
        destination = target.split("#", 1)[0]
        if destination and not (path.parent / destination).resolve().exists():
            errors.append(f"local link does not resolve: {target}")
    return errors


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    front_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not front_match:
        return ["missing YAML front matter"]

    fields = {}
    for line in front_match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()

    for field in REQUIRED_FIELDS:
        if not fields.get(field):
            errors.append(f"missing front-matter field: {field}")
    for field, choices in ENUMS.items():
        if fields.get(field) and fields[field] not in choices:
            errors.append(f"invalid {field}: {fields[field]}")
    if fields.get("last_reviewed") and not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", fields["last_reviewed"]
    ):
        errors.append("last_reviewed must be YYYY-MM-DD")
    if fields.get("bug_classes") and not re.fullmatch(
        r"\[[a-z0-9-]+(?:, [a-z0-9-]+)*\]", fields["bug_classes"]
    ):
        errors.append("bug_classes must be a comma-separated list of kebab-case slugs")

    body = text[front_match.end() :]
    h1 = re.search(r"^# (.+)$", body, re.MULTILINE)
    if not h1 or h1.group(1) != fields.get("title"):
        errors.append("title must match the H1 exactly")
    actual_headings = tuple(re.findall(r"^## (.+)$", body, re.MULTILINE))
    if actual_headings != HEADINGS:
        errors.append(f"H2 headings must be exactly, in order: {', '.join(HEADINGS)}")
    if "<!--" in text or "-->" in text:
        errors.append("template comments remain")

    word_count = len(body.split())
    if word_count >= 1500:
        errors.append(f"word count is {word_count}; must be under 1,500")
    rules = re.findall(r"^\d+\. ", section(body, "Rules"), re.MULTILINE)
    if not 6 <= len(rules) <= 10:
        errors.append(f"Rules has {len(rules)} items; expected 6–10")
    questions = re.findall(r"^- ", section(body, "Review questions"), re.MULTILINE)
    if not 5 <= len(questions) <= 8:
        errors.append(f"Review questions has {len(questions)} items; expected 5–8")

    errors.extend(local_link_errors(path, text))
    index = path.parent / "README.md"
    if not index.exists() or f"]({path.name})" not in index.read_text(encoding="utf-8"):
        errors.append(f"section index does not link {path.name}")
    return errors


def paths_from_args() -> list[Path]:
    if len(sys.argv) > 1:
        return [(ROOT / arg).resolve() for arg in sys.argv[1:]]
    return sorted(
        path for path in SHEETS.glob("*/*.md") if path.name != "README.md"
    )


def main() -> int:
    failed = False
    for path in paths_from_args():
        if not path.is_file():
            print(f"FAIL {path.relative_to(ROOT)}: file does not exist")
            failed = True
            continue
        errors = validate(path)
        label = path.relative_to(ROOT)
        if errors:
            failed = True
            print(f"FAIL {label}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {label}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
