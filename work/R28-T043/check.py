#!/usr/bin/env python3
"""Check script for Question 1 (Task R28-T043)."""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

# Paths relative to this script
WORK_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_PATH = REPO_ROOT / "100+ Python challenging programming exercises for Python 3.md"


def extract_question_1_solutions() -> tuple[str, str]:
    """Extract (source_code, alternative_code) from Question 1 in markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    match = re.search(
        r"^### Question 1\s*\n(.*?)(?=^### Question 2\s*\n)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise ValueError("Could not find Question 1 section in markdown")

    section = match.group(1)

    # Extract source solution
    src_match = re.search(r"Solution:\s*\n+```python\s*\n(.*?)\n```", section, re.DOTALL)
    if not src_match:
        raise ValueError("Could not find source solution in Question 1")
    src_code = src_match.group(1).strip()

    # Extract alternative solution
    alt_match = re.search(r"Alternative solution:\s*\n+```python\s*\n(.*?)\n```", section, re.DOTALL)
    if not alt_match:
        raise ValueError("Could not find alternative solution in Question 1")
    alt_code = alt_match.group(1).strip()

    return src_code, alt_code


def run_solution(code: str) -> subprocess.CompletedProcess[str]:
    """Execute code in a subprocess without stdin using sys.executable."""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def verify_mathematical_counts() -> tuple[int, int, int]:
    """Independently compute and assert 172, 34, and 138 counts."""
    multiples_of_7 = list(range(2002, 3200, 7))
    count_7 = len(multiples_of_7)
    assert count_7 == 172, f"Expected 172 multiples of 7, got {count_7}"

    multiples_of_35 = [i for i in multiples_of_7 if i % 5 == 0]
    count_35 = len(multiples_of_35)
    assert count_35 == 34, f"Expected 34 multiples of 35, got {count_35}"

    retained = [i for i in multiples_of_7 if i % 5 != 0]
    count_retained = len(retained)
    assert count_retained == 138, f"Expected 138 retained numbers, got {count_retained}"

    return count_7, count_35, count_retained


def record_evidence(
    expected_output: str,
    source_actual: str,
    alternative_actual: str,
    count_7: int,
    count_35: int,
    count_retained: int,
) -> None:
    """Write the required 4 evidence files into WORK_DIR."""
    # 1. inputs.json
    inputs_data = {
        "input": None,
        "description": "Question 1 takes no console input; evaluates the fixed integer range [2000, 3200] inclusive.",
    }
    (WORK_DIR / "inputs.json").write_text(
        json.dumps(inputs_data, indent=2) + "\n", encoding="utf-8"
    )

    # 2. expected_vs_actual.txt
    tokens = source_actual.strip().split(",")
    int_tokens = [int(t) for t in tokens]
    comparison_text = (
        "=== Mathematical Fixture Verification ===\n"
        f"Multiples of 7 in [2002, 3199] (step 7): {count_7}\n"
        f"Multiples of 35 dropped (divisible by 5): {count_35}\n"
        f"Retained matching numbers:                {count_retained}\n"
        f"First matching number:                    {int_tokens[0]}\n"
        f"Last matching number:                     {int_tokens[-1]}\n\n"
        "=== Source Solution Output ===\n"
        f"Expected (first 50 chars): {repr(expected_output[:50])}...\n"
        f"Actual   (first 50 chars): {repr(source_actual[:50])}...\n"
        f"Exact Length:             {len(source_actual)}\n"
        f"Matches Expected:         {source_actual == expected_output}\n\n"
        "=== Alternative Solution Output ===\n"
        f"Actual   (first 50 chars): {repr(alternative_actual[:50])}...\n"
        f"Exact Length:             {len(alternative_actual)}\n"
        f"Matches Expected:         {alternative_actual == expected_output}\n\n"
        "=== Source vs Alternative Equivalence ===\n"
        f"Identical Output:         {source_actual == alternative_actual}\n"
    )
    (WORK_DIR / "expected_vs_actual.txt").write_text(comparison_text, encoding="utf-8")

    # 3. tool_versions.txt (Python version and OS name only)
    versions_text = (
        f"Python: {platform.python_version()}\n"
        f"OS: {platform.system()}\n"
    )
    (WORK_DIR / "tool_versions.txt").write_text(versions_text, encoding="utf-8")

    # 4. failing_check_output.txt
    failing_proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--wrong"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert failing_proc.returncode != 0, (
        "Expected check.py --wrong to exit with non-zero code, but got 0"
    )
    (WORK_DIR / "failing_check_output.txt").write_text(
        f"Return code: {failing_proc.returncode}\n"
        f"Stdout:\n{failing_proc.stdout}\n"
        f"Stderr:\n{failing_proc.stderr}\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Question 1 solution and alternative")
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="Run check with deliberately wrong expected output to test failure",
    )
    args = parser.parse_args()

    # 1. Independently assert mathematical counts
    count_7, count_35, count_retained = verify_mathematical_counts()

    # Ground truth expected output
    matching_numbers = [i for i in range(2002, 3200, 7) if i % 5 != 0]
    expected_output = ",".join(str(i) for i in matching_numbers) + "\n"

    if args.wrong:
        expected_output = "WRONG_OUTPUT\n"

    # 2. Extract solutions from markdown
    src_code, alt_code = extract_question_1_solutions()

    # 3. Run source solution
    src_res = run_solution(src_code)
    if src_res.returncode != 0:
        sys.stderr.write(
            f"Source process failed with exit code {src_res.returncode}:\n{src_res.stderr}\n"
        )
        sys.exit(src_res.returncode)

    if src_res.stdout != expected_output:
        sys.stderr.write(
            f"AssertionError: Source solution output mismatch!\n"
            f"  Expected: {repr(expected_output[:50])}...\n"
            f"  Actual:   {repr(src_res.stdout[:50])}...\n"
        )
        sys.exit(1)

    # 4. Run alternative solution
    alt_res = run_solution(alt_code)
    if alt_res.returncode != 0:
        sys.stderr.write(
            f"Alternative process failed with exit code {alt_res.returncode}:\n{alt_res.stderr}\n"
        )
        sys.exit(alt_res.returncode)

    if alt_res.stdout != expected_output:
        sys.stderr.write(
            f"AssertionError: Alternative solution output mismatch!\n"
            f"  Expected: {repr(expected_output[:50])}...\n"
            f"  Actual:   {repr(alt_res.stdout[:50])}...\n"
        )
        sys.exit(1)

    # 5. Assert source == alternative
    assert src_res.stdout == alt_res.stdout, "Source and Alternative outputs do not match!"

    # 6. Verify output properties
    tokens = src_res.stdout.strip().split(",")
    assert len(tokens) == 138, f"Expected 138 numbers, got {len(tokens)}"
    int_tokens = [int(t) for t in tokens]
    assert int_tokens[0] == 2002, f"First number must be 2002, got {int_tokens[0]}"
    assert int_tokens[-1] == 3199, f"Last number must be 3199, got {int_tokens[-1]}"
    for x in int_tokens:
        assert 2000 <= x <= 3200, f"Number {x} outside range [2000, 3200]"
        assert x % 7 == 0, f"Number {x} not divisible by 7"
        assert x % 5 != 0, f"Number {x} is divisible by 5"
    assert int_tokens == sorted(int_tokens), "Numbers must be in ascending order"

    # If running normally (not --wrong), record all evidence files
    if not args.wrong:
        record_evidence(
            expected_output=expected_output,
            source_actual=src_res.stdout,
            alternative_actual=alt_res.stdout,
            count_7=count_7,
            count_35=count_35,
            count_retained=count_retained,
        )
        print("R28-T043 PASS: Source and alternative solutions verified successfully.")


if __name__ == "__main__":
    main()
