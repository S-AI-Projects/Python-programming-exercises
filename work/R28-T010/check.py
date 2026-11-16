#!/usr/bin/env python3
"""Mutation-focused regression check for Question 47."""

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
    section = re.search(r"### Question 47(.*?)(?=### Question 48|\Z)", text, re.S)
    if not section:
        raise AssertionError("Question 47 section was not found")
    assert "lazy `map` iterator" in section.group(1)
    code = re.search(r"Solution\s*```python\s*(.*?)```", section.group(1), re.S)
    if not code:
        raise AssertionError("Question 47 solution block was not found")
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
    expected = "[4, 16, 36, 64, 100]"
    published = assert_output(solution, expected)

    smallest_code = solution.replace(
        "li = [1,2,3,4,5,6,7,8,9,10]", "li = [2]", 1
    )
    smallest = assert_output(smallest_code, "[4]")

    # Temporary one-operation mutant: invert the filter predicate.
    mutant = solution.replace("x%2==0", "x%2!=0", 1)
    mutant_result = run(mutant)
    assert mutant_result.returncode == 0, mutant_result.stderr
    mutant_output = mutant_result.stdout.strip()
    assert mutant_output == "[1, 9, 25, 49, 81]"
    assert mutant_output != published, "regression checker failed to distinguish mutant"

    (WORK / "inputs.json").write_text(
        json.dumps(
            {
                "published_input": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "smallest_input": [2],
                "mutant": "x%2==0 -> x%2!=0",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (WORK / "expected_output.txt").write_text(
        "published: [4, 16, 36, 64, 100]\nsmallest: [4]\n"
        "mutant: [1, 9, 25, 49, 81]\n",
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
        "R28-T010 PASS\n"
        "Executed the exact Question 47 solution from Markdown.\n"
        "Verified materialized output, smallest input, and one-operation filter mutant detection.\n",
        encoding="utf-8",
    )
    print("R28-T010 PASS: regression, smallest-input, and mutant checks succeeded")


if __name__ == "__main__":
    main()
