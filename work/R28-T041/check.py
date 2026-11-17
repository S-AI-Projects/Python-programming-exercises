#!/usr/bin/env python3
"""Check script for Question 98 (Task R28-T041)."""

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


def extract_question_98_data() -> tuple[str, str, str]:
    """Extract (solution_code, published_input, published_expected) from Question 98 in markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    start_marker = "### Question 98"
    end_marker = "### Question 99"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        raise ValueError(f"Marker '{start_marker}' not found in {MARKDOWN_PATH}")

    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        raise ValueError(f"Marker '{end_marker}' not found after '{start_marker}' in {MARKDOWN_PATH}")

    section = content[start_idx:end_idx]

    # Extract solution code
    code_match = re.search(r"Solution:\s*```python\s*\n(.*?)\n```", section, re.DOTALL)
    if not code_match:
        raise ValueError("Python code block not found in Question 98 Solution section")
    code = code_match.group(1).strip()

    # Extract published example input and expected output from the Example section
    example_match = re.search(
        r"Example:\s*\nIf the following string is given as input to the program:\s*\n+([^\n]+)\s*\n+Then, the output of the program should be:\s*\n+([^\n]+)",
        section,
    )
    if not example_match:
        raise ValueError(
            "Could not parse published example input and expected output from Question 98 in markdown"
        )

    pub_input = example_match.group(1).strip() + "\n"
    pub_expected = example_match.group(2).strip() + "\n"

    return code, pub_input, pub_expected


def run_solution(code: str, stdin_data: str) -> subprocess.CompletedProcess[str]:
    """Execute the extracted solution code with stdin_data using sys.executable."""
    result = subprocess.run(
        [sys.executable, "-c", code],
        input=stdin_data,
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def record_evidence(
    pub_input: str,
    pub_expected: str,
    pub_actual: str,
    small_input: str,
    small_expected: str,
    small_actual: str,
) -> None:
    """Write the required 4 evidence files into WORK_DIR."""
    # 1. inputs.json
    inputs_data = {
        "published_input": pub_input,
        "smallest_supported_input": small_input,
    }
    (WORK_DIR / "inputs.json").write_text(
        json.dumps(inputs_data, indent=2) + "\n", encoding="utf-8"
    )

    # 2. expected_vs_actual.txt
    comparison_text = (
        "=== Published Example ===\n"
        f"Input:    {repr(pub_input)}\n"
        f"Expected: {repr(pub_expected)}\n"
        f"Actual:   {repr(pub_actual)}\n"
        f"Match:    {pub_actual == pub_expected}\n\n"
        "=== Smallest Supported Input ===\n"
        f"Input:    {repr(small_input)}\n"
        f"Expected: {repr(small_expected)}\n"
        f"Actual:   {repr(small_actual)}\n"
        f"Match:    {small_actual == small_expected}\n"
    )
    (WORK_DIR / "expected_vs_actual.txt").write_text(comparison_text, encoding="utf-8")

    # 3. tool_versions.txt (Python version and OS name only)
    versions_text = (
        f"Python: {platform.python_version()}\n"
        f"OS: {platform.system()}\n"
    )
    (WORK_DIR / "tool_versions.txt").write_text(versions_text, encoding="utf-8")

    # 4. failing_check_output.txt
    # Run self with --wrong in a subprocess to capture the deliberate failing output
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
    parser = argparse.ArgumentParser(description="Check Question 98 solution")
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="Run check with deliberately wrong expected output to test failure",
    )
    args = parser.parse_args()

    code, pub_input, pub_expected = extract_question_98_data()

    if args.wrong:
        pub_expected = "WRONG_OUTPUT\n"

    small_input = "a\n"
    small_expected = "a\n"

    # Test 1: Published example
    pub_result = run_solution(code, pub_input)
    if pub_result.returncode != 0:
        sys.stderr.write(
            f"Process failed with exit code {pub_result.returncode}:\n{pub_result.stderr}\n"
        )
        sys.exit(pub_result.returncode)

    if pub_result.stdout != pub_expected:
        sys.stderr.write(
            f"AssertionError: Published example output mismatch!\n"
            f"  Expected: {repr(pub_expected)}\n"
            f"  Actual:   {repr(pub_result.stdout)}\n"
        )
        sys.exit(1)

    # Test 2: Smallest supported input
    small_result = run_solution(code, small_input)
    if small_result.returncode != 0:
        sys.stderr.write(
            f"Process failed on smallest input with exit code {small_result.returncode}:\n{small_result.stderr}\n"
        )
        sys.exit(small_result.returncode)

    if small_result.stdout != small_expected:
        sys.stderr.write(
            f"AssertionError: Smallest input output mismatch!\n"
            f"  Expected: {repr(small_expected)}\n"
            f"  Actual:   {repr(small_result.stdout)}\n"
        )
        sys.exit(1)

    # If running normally (not --wrong), record all evidence files
    if not args.wrong:
        record_evidence(
            pub_input=pub_input,
            pub_expected=pub_expected,
            pub_actual=pub_result.stdout,
            small_input=small_input,
            small_expected=small_expected,
            small_actual=small_result.stdout,
        )
        print("R28-T041 PASS: Published example and smallest supported input verified successfully.")


if __name__ == "__main__":
    main()
