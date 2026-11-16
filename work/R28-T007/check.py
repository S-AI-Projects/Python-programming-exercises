#!/usr/bin/env python3
"""Verify the Question 16 derivation against the actual Markdown solution."""

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
    section = re.search(r"### Question 16(.*?)(?=### Question 17|\Z)", text, re.S)
    if not section:
        raise AssertionError("Question 16 section was not found")
    code = re.search(r"Solution\s*:?\s*```python\s*(.*?)```", section.group(1), re.S)
    if not code:
        raise AssertionError("Question 16 solution block was not found")
    return code.group(1).strip()


def run(code: str, value: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        input=value + "\n",
        capture_output=True,
        text=True,
        check=False,
    )


def assert_case(code: str, value: str, expected: str) -> str:
    result = run(code, value)
    assert result.returncode == 0, result.stderr
    actual = result.stdout.strip()
    assert actual == expected, f"input {value!r}: expected {expected!r}, got {actual!r}"
    return actual


def main() -> None:
    section = re.search(
        r"### Question 16(.*?)(?=### Question 17|\Z)",
        MARKDOWN.read_text(encoding="utf-8"),
        re.S,
    )
    assert section and "Derivation for the published input" in section.group(1)
    solution = extract_solution()
    assert "split" in solution and "int(x)%2!=0" in solution and "join" in solution

    published_input = "1,2,3,4,5,6,7,8,9"
    published = assert_case(solution, published_input, "1,3,5,7,9")
    smallest = assert_case(solution, "1", "1")

    # Deliberately invert the oddness predicate; the published fixture must catch it.
    mutant = solution.replace("int(x)%2!=0", "int(x)%2==0", 1)
    mutant_output = assert_case(mutant, published_input, "2,4,6,8")
    assert mutant_output != published

    (WORK / "inputs.json").write_text(
        json.dumps(
            {"published_input": published_input, "smallest_input": "1"}, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    (WORK / "expected_output.txt").write_text(
        "published: 1,3,5,7,9\nsmallest: 1\nmutant: 2,4,6,8\n",
        encoding="utf-8",
    )
    (WORK / "actual_output.txt").write_text(
        f"published: {published}\nsmallest: {smallest}\nmutant: {mutant_output}\n",
        encoding="utf-8",
    )
    (WORK / "python_version.txt").write_text(sys.version + "\n", encoding="utf-8")
    (WORK / "tool_versions.txt").write_text(
        f"Python: {sys.version.split()[0]}\nPlatform: {platform.platform()}\n",
        encoding="utf-8",
    )
    (WORK / "test_results.txt").write_text(
        "R28-T007 PASS\n"
        "Executed the exact Question 16 solution from Markdown.\n"
        "Verified the published derivation, smallest input, and oddness mutant.\n",
        encoding="utf-8",
    )
    print("R28-T007 PASS: derivation, published output, and mutant checks succeeded")


if __name__ == "__main__":
    main()
