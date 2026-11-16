#!/usr/bin/env python3
"""Verify the published Question 28 example and its clarified conversion step."""

from __future__ import annotations

import json
import platform
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MARKDOWN = ROOT / "100+ Python challenging programming exercises for Python 3.md"
WORK = Path(__file__).resolve().parent


def extract_solution() -> str:
    text = MARKDOWN.read_text(encoding="utf-8")
    section = re.search(r"### Question 28(.*?)(?=### Question 29|\Z)", text, re.S)
    if not section:
        raise AssertionError("Question 28 section was not found")
    code = re.search(r"Solution\s*```python\s*(.*?)```", section.group(1), re.S)
    if not code:
        raise AssertionError("Question 28 solution block was not found")
    return code.group(1).strip()


def run(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )


def assert_output(code: str, expected: str) -> str:
    result = run(code)
    assert result.returncode == 0, result.stderr
    actual = result.stdout.strip()
    assert actual == expected, f"expected {expected!r}, got {actual!r}"
    return actual


def main() -> None:
    solution = extract_solution()
    assert "value_as_string = str(n)" in solution

    published = assert_output(solution, "3")

    smallest_code = solution.replace("printValue(3)", "printValue(0)", 1)
    smallest = assert_output(smallest_code, "0")

    # The checker must distinguish the correct conversion from a one-operation mutant.
    mutant = solution.replace("str(n)", "str(n + 1)", 1)
    mutant_result = run(mutant)
    assert mutant_result.returncode == 0
    assert mutant_result.stdout.strip() != "3", "mutant was not detected"

    evidence = {
        "solution": solution,
        "published_output": published,
        "smallest_input": 0,
        "smallest_output": smallest,
        "mutant_detected": True,
        "python": sys.version,
        "platform": platform.platform(),
    }
    (WORK / "inputs.json").write_text(
        json.dumps({"published_input": 3, "smallest_input": 0}, indent=2) + "\n",
        encoding="utf-8",
    )
    (WORK / "expected_output.txt").write_text("published: 3\nsmallest: 0\n", encoding="utf-8")
    (WORK / "actual_output.txt").write_text(
        f"published: {published}\nsmallest: {smallest}\n", encoding="utf-8"
    )
    (WORK / "python_version.txt").write_text(sys.version + "\n", encoding="utf-8")
    (WORK / "tool_versions.txt").write_text(
        f"Python: {sys.version.split()[0]}\nPlatform: {platform.platform()}\n",
        encoding="utf-8",
    )
    (WORK / "test_results.txt").write_text(
        json.dumps({"status": "PASS", **evidence}, indent=2) + "\n", encoding="utf-8"
    )
    print("R28-T006 PASS: published, smallest-input, and mutant checks succeeded")


if __name__ == "__main__":
    main()
