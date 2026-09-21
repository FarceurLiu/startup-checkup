"""Static checker regression tests. These do not execute an AI model."""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("startup_validator", PACKAGE / "scripts/validate.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "startup-checkup"
        shutil.copytree(PACKAGE, self.root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    def error_codes(self) -> set[str]:
        return {item["code"] for item in MODULE.validate(self.root)["errors"]}

    def replace(self, relative: str, before: str, after: str) -> None:
        path = self.root / relative
        path.write_text(path.read_text(encoding="utf-8").replace(before, after, 1), encoding="utf-8")

    def test_valid_package(self) -> None:
        self.assertEqual(MODULE.validate(self.root)["status"], "PASS")

    def test_missing_name(self) -> None:
        self.replace("SKILL.md", "name: startup-checkup\n", "")
        self.assertIn("name", self.error_codes())

    def test_directory_name_mismatch(self) -> None:
        self.replace("SKILL.md", "name: startup-checkup", "name: different-name")
        self.assertIn("directory_name", self.error_codes())

    def test_repeated_hyphen(self) -> None:
        self.replace("SKILL.md", "name: startup-checkup", "name: startup--checkup")
        self.assertIn("name_format", self.error_codes())

    def test_description_length(self) -> None:
        self.replace("SKILL.md", "description: >-\n", "description: >-\n  " + "x" * 1025 + "\n")
        self.assertIn("description", self.error_codes())

    def test_missing_reference(self) -> None:
        (self.root / "references/framework.md").unlink()
        self.assertIn("required_file", self.error_codes())
        self.assertIn("relative_link", self.error_codes())

    def test_escaping_reference(self) -> None:
        self.replace("SKILL.md", "(references/framework.md)", "(../../outside.md)")
        self.assertIn("link_outside", self.error_codes())

    def test_invalid_json(self) -> None:
        (self.root / "tests/cases.json").write_text("{not-json}", encoding="utf-8")
        self.assertIn("case_json", self.error_codes())

    def test_missing_case_assertions(self) -> None:
        path = self.root / "tests/cases.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["cases"][0]["must_include"] = []
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.assertIn("case_assertions", self.error_codes())

    def test_additional_case_is_allowed(self) -> None:
        path = self.root / "tests/cases.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        extra = dict(payload["cases"][0], id="extra")
        payload["cases"].append(extra)
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.assertEqual(self.error_codes(), set())

    def test_missing_boundary_coverage(self) -> None:
        path = self.root / "tests/cases.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["cases"] = [case for case in payload["cases"] if case["category"] != "boundary"]
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.assertIn("case_categories", self.error_codes())

    def test_invocation_policy_type(self) -> None:
        self.replace("agents/openai.yaml", "allow_implicit_invocation: true", "allow_implicit_invocation: maybe")
        self.assertIn("agent_policy", self.error_codes())


if __name__ == "__main__":
    unittest.main()
