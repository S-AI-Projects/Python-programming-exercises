#!/usr/bin/env python3
"""Check script for Question 9 (Task R28-T050)."""

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


def extract_question_9_data() -> tuple[str, str, str, str, str]:
    """Extract code, published input/output, and smallest input/output from markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    match = re.search(
        r"^### Question 9\s*\n(.*?)(?=^### Question 10\s*\n)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise ValueError("Could not find Question 9 section in markdown")

    section = match.group(1)

    code_match = re.search(r"Solution:\s*\n+```(?:python)?\s*\n(.*?)\n```", section, re.DOTALL)
    if not code_match:
        raise ValueError("Could not find solution code block in Question 9")
    code = code_match.group(1).strip()

    # Parse published input and expected output from markdown text
    pub_match = re.search(
        r"Suppose the following input is supplied to the program:\s*\n(.*?)\nThen,\s*the output should be:\s*\n(.*?)(?=\n\nSmallest|\n\nHints)",
        section,
        re.DOTALL,
    )
    if not pub_match:
        raise ValueError("Could not parse published example from Question 9")

    pub_input = pub_match.group(1).strip() + "\n\n"
    pub_expected = pub_match.group(2).strip() + "\n"

    # Parse smallest supported input and output from markdown text
    small_match = re.search(
        r"Smallest supported input:\s*\nSuppose the following input is supplied to the program:\s*\n(.*?)\nThen,\s*the output should be:\s*\n(.*?)(?=\n\nHints)",
        section,
        re.DOTALL,
    )
    if not small_match:
        raise ValueError("Could not parse smallest example from Question 9")

    small_input = small_match.group(1).strip() + "\n\n"
    small_expected = small_match.group(2).strip() + "\n"

    return code, pub_input, pub_expected, small_input, small_expected


def run_code(code: str, input_text: str) -> subprocess.CompletedProcess[str]:
    """Execute code in a subprocess with provided stdin using sys.executable."""
    return subprocess.run(
        [sys.executable, "-c", code],
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
    )


def record_evidence(
    published_input: str,
    published_expected: str,
    published_actual: str,
    smallest_input: str,
    smallest_expected: str,
    smallest_actual: str,
    mutant1_output: str,
    mutant1_killed: bool,
    mutant2_output: str,
    mutant2_killed: bool,
) -> None:
    """Write the required 4 evidence files into WORK_DIR."""
    # 1. inputs.json
    inputs_data = {
        "published_example": {
            "input": published_input,
            "expected_output": published_expected,
        },
        "smallest_supported_input": {
            "input": smallest_input,
            "expected_output": smallest_expected,
        },
        "mutation_tests": [
            {
                "mutant_operation": "s.upper() -> s (omitted upper)",
                "mutant_output": mutant1_output,
                "mutant_killed": mutant1_killed,
            },
            {
                "mutant_operation": "s.upper() -> s.lower() (substituted lower)",
                "mutant_output": mutant2_output,
                "mutant_killed": mutant2_killed,
            },
        ],
        "description": "Question 9 capitalizes multiline console input until an empty line is encountered.",
    }
    (WORK_DIR / "inputs.json").write_text(
        json.dumps(inputs_data, indent=2) + "\n", encoding="utf-8"
    )

    # 2. expected_vs_actual.txt
    comparison_text = (
        "=== Published Example Verification ===\n"
        f"Input:\n{published_input}"
        f"Expected output:\n{published_expected}"
        f"Actual output:\n{published_actual}"
        f"Matches: {published_actual == published_expected}\n\n"
        "=== Smallest Supported Input Verification ===\n"
        f"Input:\n{smallest_input}"
        f"Expected output:\n{smallest_expected}"
        f"Actual output:\n{smallest_actual}"
        f"Matches: {smallest_actual == smallest_expected}\n\n"
        "=== Mutation Test Verification ===\n"
        f"Mutant 1 (omitted upper) killed: {mutant1_killed}\n"
        f"Mutant 2 (substituted lower) killed: {mutant2_killed}\n"
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
    parser = argparse.ArgumentParser(description="Check Question 9 solution")
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
    ) = extract_question_9_data()

    expected_pub_output = "WRONG OUTPUT\n" if args.wrong else pub_expected

    # 1. Test published example
    res = run_code(code, pub_input)
    if res.returncode != 0:
        sys.stderr.write(f"Process failed with exit code {res.returncode}:\n{res.stderr}\n")
        sys.exit(res.returncode)

    if res.stdout != expected_pub_output:
        sys.stderr.write(
            f"AssertionError: Expected output {expected_pub_output!r}, got {res.stdout!r}\n"
        )
        sys.exit(1)

    # 2. Test smallest supported input
    small_res = run_code(code, small_input)
    if small_res.returncode != 0:
        sys.stderr.write(f"Smallest input failed with exit code {small_res.returncode}:\n{small_res.stderr}\n")
        sys.exit(small_res.returncode)

    assert small_res.stdout == small_expected, f"Expected {small_expected!r}, got {small_res.stdout!r}"

    # 3. Mutation test 1: replace s.upper() with s (omitted upper)
    mutant1_code, count1 = re.subn(r"s\.upper\(\)", "s", code)
    assert count1 == 1, "Failed to substitute s.upper() for mutant 1"
    mutant1_res = run_code(mutant1_code, pub_input)
    assert mutant1_res.returncode == 0
    mutant1_killed = mutant1_res.stdout != pub_expected
    assert mutant1_killed, "Mutant 1 (omitted upper) survived! Test suite failed to kill mutant."

    # 4. Mutation test 2: replace s.upper() with s.lower() (substituted lower)
    mutant2_code, count2 = re.subn(r"s\.upper\(\)", "s.lower()", code)
    assert count2 == 1, "Failed to substitute s.upper() for mutant 2"
    mutant2_res = run_code(mutant2_code, pub_input)
    assert mutant2_res.returncode == 0
    mutant2_killed = mutant2_res.stdout != pub_expected
    assert mutant2_killed, "Mutant 2 (substituted lower) survived! Test suite failed to kill mutant."

    if not args.wrong:
        record_evidence(
            published_input=pub_input,
            published_expected=pub_expected,
            published_actual=res.stdout,
            smallest_input=small_input,
            smallest_expected=small_expected,
            smallest_actual=small_res.stdout,
            mutant1_output=mutant1_res.stdout,
            mutant1_killed=mutant1_killed,
            mutant2_output=mutant2_res.stdout,
            mutant2_killed=mutant2_killed,
        )
        print("R28-T050 PASS: Question 9 capitalization and both mutation tests verified successfully.")


if __name__ == "__main__":
    main()
