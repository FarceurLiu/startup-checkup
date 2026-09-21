#!/usr/bin/env python3
"""Read-only static checks for this package, not a general YAML/behavior validator.

Uses Python 3.9+ standard library only. It never installs, writes, or calls a network.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REQUIRED = (
    "SKILL.md", "README.md", "agents/openai.yaml",
    "references/framework.md", "references/evidence-and-experiments.md",
    "references/source-map.md", "templates/assessment.md",
    "templates/experiment.md", "scripts/validate.py",
    "tests/cases.json", "tests/test_validator.py", "tests/README.md",
    "tests/VALIDATION.md", "examples/service-delivery.md", "CHANGELOG.md", "LICENSE",
)
STATUSES = ("已支持", "部分支持", "待驗證", "本輪反證", "不適用")


def validate(root: Path) -> dict[str, Any]:
    """Validate the fixed package contract without changing the package."""
    root = root.expanduser().resolve()
    errors: list[dict[str, str]] = []
    checks = 0

    def check(condition: bool, code: str, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            errors.append({"code": code, "message": message})

    def read(relative: str) -> str:
        path = root / relative
        try:
            path.resolve().relative_to(root)
            if path.is_symlink():
                raise ValueError("Symbolic links are not supported by this package checker.")
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError) as exc:
            check(False, "read", f"{relative}: {exc}")
            return ""

    check(root.is_dir(), "root", "Package directory does not exist.")
    for relative in REQUIRED:
        check((root / relative).is_file(), "required_file", f"Missing file: {relative}")

    text = read("SKILL.md")
    sections = text.split("---\n", 2)
    has_frontmatter = text.startswith("---\n") and len(sections) == 3
    check(has_frontmatter, "frontmatter", "SKILL.md must start with YAML frontmatter.")
    frontmatter, body = (sections[1], sections[2]) if has_frontmatter else ("", text)
    names = re.findall(r"^name:\s*([^\n]+)$", frontmatter, flags=re.M)
    check(len(names) == 1, "name", "Exactly one name field is required.")
    name = names[0].strip() if names else ""
    check(bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)) and len(name) <= 64,
          "name_format", "Name must be lowercase, 1–64 characters, without repeated hyphens.")
    check(name == root.name, "directory_name", "Skill name must match the package directory.")

    # This package intentionally uses a folded >- description, not arbitrary YAML.
    descriptions = re.findall(r"^description: >-\n((?:[ \t]+[^\n]*\n)+)", frontmatter, flags=re.M)
    description = " ".join(line.strip() for line in descriptions[0].splitlines()) if descriptions else ""
    check(len(descriptions) == 1 and 1 <= len(description) <= 1024,
          "description", "Expected one nonempty folded description of at most 1024 characters.")
    check(len(text.splitlines()) < 500, "length", "Keep the entry file under 500 lines.")
    for status in STATUSES:
        check(status in body, "status", f"Missing hypothesis status: {status}")
    for module in (f"M{n:02d}" for n in range(1, 10)):
        check(module in body, "module", f"Missing module reference: {module}")
    for stage in ("G1", "G2", "G3", "G4"):
        check(stage in body, "stage", f"Missing stage reference: {stage}")

    for md in sorted(root.rglob("*.md")):
        relative = str(md.relative_to(root))
        if md.is_symlink():
            check(False, "symlink", f"Do not distribute symlink: {relative}")
            continue
        data = read(relative)
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", data):
            target = target.split("#", 1)[0]
            if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                continue
            destination = (md.parent / target).resolve()
            try:
                destination.relative_to(root)
                inside = True
            except ValueError:
                inside = False
            check(inside, "link_outside", f"Reference escapes package: {relative} -> {target}")
            if inside:
                check(destination.is_file(), "relative_link", f"Broken reference: {relative} -> {target}")

    agent = read("agents/openai.yaml")
    for field in ("display_name:", "short_description:", "default_prompt:"):
        check(field in agent, "agent_metadata", f"Missing UI field: {field}")
    check(f"${name}" in agent, "agent_prompt", "Default prompt must mention the skill name.")
    check(bool(re.search(r"allow_implicit_invocation:\s*(true|false)\b", agent)),
          "agent_policy", "Invocation policy must be true or false.")

    try:
        payload = json.loads(read("tests/cases.json"))
        cases = payload.get("cases", []) if isinstance(payload, dict) else []
        check(isinstance(cases, list) and len(cases) >= 5, "case_count", "Expected at least five behavioral scenarios.")
        if not isinstance(cases, list):
            cases = []
        case_objects = [case for case in cases if isinstance(case, dict)]
        check(len(case_objects) == len(cases), "case_object", "Each scenario must be an object.")
        ids = [case.get("id") for case in case_objects]
        check(all(isinstance(item, str) for item in ids) and len(set(map(str, ids))) == len(ids),
              "case_id", "Case IDs must be unique strings.")
        counts = Counter(str(case.get("category")) for case in case_objects)
        check(set(counts) <= {"typical", "confusing", "boundary"}
              and counts["typical"] >= 2 and counts["confusing"] >= 2 and counts["boundary"] >= 1,
              "case_categories", "Expected at least two typical, two confusing, and one boundary scenario; no unknown categories.")
        for case in case_objects:
            ident = str(case.get("id", "?"))
            check(isinstance(case.get("prompt"), str) and bool(case["prompt"].strip()),
                  "case_prompt", f"{ident}: missing prompt.")
            check(isinstance(case.get("should_trigger"), bool),
                  "case_trigger", f"{ident}: should_trigger must be boolean.")
            for field in ("must_include", "must_not_include"):
                value = case.get(field)
                check(isinstance(value, list) and bool(value)
                      and all(isinstance(item, str) and bool(item.strip()) for item in value),
                      "case_assertions", f"{ident}: {field} must contain nonempty strings.")
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        check(False, "case_json", f"Cannot read scenario JSON: {exc}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "scope": "fixed-package static contract; not model behavior or full YAML certification",
        "root": str(root), "checks": checks, "errors": errors,
        "model_behavior_evaluation": "not_run_by_this_validator",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    result = validate(Path(args.root))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
