#!/usr/bin/env python3
"""Verify Question 8 output and document its text-sorting limitation."""

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
    section = re.search(r"### Question 8(.*?)(?=### Question 9|\Z)", text, re.S)
    if not section:
        raise AssertionError("Question 8 section was not found")
    code = re.search(r"Solution:\s*```python\s*(.*?)```", section.group(1), re.S)
    if not code:
        raise AssertionError("Question 8 solution block was not found")
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
    text = MARKDOWN.read_text(encoding="utf-8")
    section = re.search(r"### Question 8(.*?)(?=### Question 9|\Z)", text, re.S)
    assert section and "lexicographically" in section.group(1)
    solution = extract_solution()

    published_input = "without,hello,bag,world"
    published = assert_case(solution, published_input, "bag,hello,without,world")
    smallest = assert_case(solution, "a", "a")
    limitation = assert_case(solution, "10,2,1", "1,10,2")

    # Deliberately reverse the sort; the published fixture must detect the regression.
    mutant = solution.replace("items.sort()", "items.sort(reverse=True)", 1)
    mutant_result = run(mutant, published_input)
    assert mutant_result.returncode == 0
    assert mutant_result.stdout.strip() != published

    (WORK / "inputs.json").write_text(
        json.dumps(
            {
                "published_input": published_input,
                "smallest_input": "a",
                "limitation_input": "10,2,1",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (WORK / "expected_output.txt").write_text(
        "published: bag,hello,without,world\n"
        "smallest: a\n"
        "limitation: 1,10,2\n",
        encoding="utf-8",
    )
    (WORK / "actual_output.txt").write_text(
        f"published: {published}\nsmallest: {smallest}\nlimitation: {limitation}\n",
        encoding="utf-8",
    )
    (WORK / "python_version.txt").write_text(sys.version + "\n", encoding="utf-8")
    (WORK / "tool_versions.txt").write_text(
        f"Python: {sys.version.split()[0]}\nPlatform: {platform.platform()}\n",
        encoding="utf-8",
    )
    (WORK / "test_results.txt").write_text(
        "R28-T008 PASS\n"
        "Executed the exact Question 8 solution from Markdown.\n"
        "Verified the published output, smallest input, lexical-order limitation, and mutant detection.\n",
        encoding="utf-8",
    )
    print("R28-T008 PASS: output, limitation, and mutant checks succeeded")


if __name__ == "__main__":
    main()
