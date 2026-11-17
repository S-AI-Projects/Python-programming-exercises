#!/usr/bin/env python3
"""Check script for Question 58 (Task R28-T046)."""

from __future__ import annotations

import argparse
import ast
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


def extract_question_58_data() -> tuple[str, str, str, str, str, str, tuple[str, ...]]:
    """Extract code, inputs, outputs, pattern, and expected groups from markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    match = re.search(
        r"^### Question 58\s*\n(.*?)(?=^### Question 59\s*\n)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise ValueError("Could not find Question 58 section in markdown")

    section = match.group(1)

    code_match = re.search(r"Solution:\s*\n+```(?:python)?\s*\n(.*?)\n```", section, re.DOTALL)
    if not code_match:
        raise ValueError("Could not find solution code block in Question 58")
    code = code_match.group(1).strip()

    example_match = re.search(
        r"Example:\s*\nIf the following email address is given as input to the program:\s*\n+([^\n]+)\s*\n+Then, the output of the program should be:\s*\n+([^\n]+)",
        section,
    )
    if not example_match:
        raise ValueError("Could not parse published example from Question 58")

    pub_input = example_match.group(1).strip() + "\n"
    pub_expected = example_match.group(2).strip() + "\n"

    small_match = re.search(
        r"Smallest supported input:\s*\nIf the following email address is given as input to the program:\s*\n+([^\n]+)\s*\n+Then, the output of the program should be:\s*\n+([^\n]+)",
        section,
    )
    if not small_match:
        raise ValueError("Could not parse smallest supported input from Question 58")

    small_input = small_match.group(1).strip() + "\n"
    small_expected = small_match.group(2).strip() + "\n"

    # Extract pattern from solution code without retyping
    pat_match = re.search(r'pat2\s*=\s*r?["\'](.*?)["\']\n', code)
    if not pat_match:
        raise ValueError("Could not extract regex pattern from solution code")
    pattern = pat_match.group(1)

    # Extract expected groups tuple from explanation
    groups_match = re.search(r"evaluates to\s*`?(\([^\)`]+?\))`?", section)
    if not groups_match:
        raise ValueError("Could not extract expected groups tuple from explanation")
    expected_groups = ast.literal_eval(groups_match.group(1))

    return code, pub_input, pub_expected, small_input, small_expected, pattern, expected_groups


def run_solution(code: str, stdin_data: str) -> subprocess.CompletedProcess[str]:
    """Execute code in a subprocess with stdin using sys.executable."""
    return subprocess.run(
        [sys.executable, "-c", code],
        input=stdin_data,
        capture_output=True,
        text=True,
        check=False,
    )


def record_evidence(
    pub_input: str,
    pub_expected: str,
    pub_actual: str,
    small_input: str,
    small_expected: str,
    small_actual: str,
    pub_groups: tuple[str, ...],
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
        "=== Published Example Verification ===\n"
        f"Input:                    {repr(pub_input)}\n"
        f"Expected Output:          {repr(pub_expected)}\n"
        f"Actual Output:            {repr(pub_actual)}\n"
        f"Matches Expected:         {pub_actual == pub_expected}\n"
        f"Intermediate match groups: {pub_groups}\n"
        f"Group 1 (username):       {repr(pub_groups[0])}\n"
        f"Group 2 (domain):         {repr(pub_groups[1])}\n"
        f"Group 3 (subdomain token): {repr(pub_groups[2])}\n"
        f"Group 4 (TLD 'com'):      {repr(pub_groups[3])}\n\n"
        "=== Smallest Supported Input Verification ===\n"
        f"Input:                    {repr(small_input)}\n"
        f"Expected Output:          {repr(small_expected)}\n"
        f"Actual Output:            {repr(small_actual)}\n"
        f"Matches Expected:         {small_actual == small_expected}\n"
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
    parser = argparse.ArgumentParser(description="Check Question 58 solution")
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="Run check with deliberately wrong expected output to test failure",
    )
    args = parser.parse_args()

    (
        code,
        pub_input,
        pub_expected,
        small_input,
        small_expected,
        pattern,
        expected_groups,
    ) = extract_question_58_data()

    if args.wrong:
        pub_expected = "WRONG_OUTPUT\n"

    # 1. Test published example
    pub_res = run_solution(code, pub_input)
    if pub_res.returncode != 0:
        sys.stderr.write(f"Process failed on published input: {pub_res.stderr}\n")
        sys.exit(pub_res.returncode)

    if pub_res.stdout != pub_expected:
        sys.stderr.write(
            f"AssertionError: Published output mismatch!\n"
            f"  Expected: {repr(pub_expected)}\n"
            f"  Actual:   {repr(pub_res.stdout)}\n"
        )
        sys.exit(1)

    # 2. Test smallest supported input
    small_res = run_solution(code, small_input)
    if small_res.returncode != 0:
        sys.stderr.write(f"Process failed on smallest input: {small_res.stderr}\n")
        sys.exit(small_res.returncode)

    if small_res.stdout != small_expected:
        sys.stderr.write(
            f"AssertionError: Smallest input output mismatch!\n"
            f"  Expected: {repr(small_expected)}\n"
            f"  Actual:   {repr(small_res.stdout)}\n"
        )
        sys.exit(1)

    # Verify extracted pattern directly on published input
    m = re.match(pattern, pub_input.strip())
    assert m is not None, "Failed to match published input with pattern extracted from solution code"
    actual_groups = m.groups()
    assert actual_groups == expected_groups, (
        f"Groups mismatch! Expected {expected_groups}, got {actual_groups}"
    )
    assert actual_groups == ('john', 'google.com', 'google.', 'com'), (
        f"Literal groups tuple mismatch: {actual_groups}"
    )
    assert m.group(1) == pub_expected.strip()

    if not args.wrong:
        record_evidence(
            pub_input=pub_input,
            pub_expected=pub_expected,
            pub_actual=pub_res.stdout,
            small_input=small_input,
            small_expected=small_expected,
            small_actual=small_res.stdout,
            pub_groups=actual_groups,
        )
        print("R28-T046 PASS: Published example, extracted pattern, and smallest input verified successfully.")


if __name__ == "__main__":
    main()
