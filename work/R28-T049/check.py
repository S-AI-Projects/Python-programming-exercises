#!/usr/bin/env python3
"""Check script for Question 59 (Task R28-T049)."""

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


def extract_question_59_data() -> tuple[str, str, str, str, str, str]:
    """Extract code, pattern, published example, and smallest example from Question 59 in markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    match = re.search(
        r"^### Question 59\s*\n(.*?)(?=^### Question 60\s*\n)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise ValueError("Could not find Question 59 section in markdown")

    section = match.group(1)

    code_match = re.search(r"Solution:\s*\n+```(?:python)?\s*\n(.*?)\n```", section, re.DOTALL)
    if not code_match:
        raise ValueError("Could not find solution code block in Question 59")
    code = code_match.group(1).strip()

    # Extract pattern from code without retyping
    pat_match = re.search(r'pat2\s*=\s*r?["\'](.*?)["\']\n', code)
    if not pat_match:
        raise ValueError("Could not extract regex pattern from solution code")
    pattern = pat_match.group(1)

    example_match = re.search(
        r"Example:\s*\nIf the following email address is given as input to the program:\s*\n+([^\n]+)\s*\n+Then, the output of the program should be:\s*\n+([^\n]+)",
        section,
    )
    if not example_match:
        raise ValueError("Could not parse published example from Question 59")

    pub_input = example_match.group(1).strip() + "\n"
    pub_expected = example_match.group(2).strip() + "\n"

    small_match = re.search(
        r"Smallest supported input:\s*\nIf the following email address is given as input to the program:\s*\n+([^\n]+)\s*\n+Then, the output of the program should be:\s*\n+([^\n]+)",
        section,
    )
    if not small_match:
        raise ValueError("Could not parse smallest supported input from Question 59")

    small_input = small_match.group(1).strip() + "\n"
    small_expected = small_match.group(2).strip() + "\n"

    return code, pattern, pub_input, pub_expected, small_input, small_expected


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
    match_groups: tuple[str, ...],
    string_is_same: bool,
    slice_equal: bool,
    group2_not_same: bool,
    match_vs_search: bool,
) -> None:
    """Write the required 4 evidence files into WORK_DIR."""
    # 1. inputs.json
    inputs_data = {
        "published_example": {
            "input": published_input.strip(),
            "expected_output": published_expected.strip(),
            "extracted_groups": list(match_groups),
        },
        "smallest_supported_input": {
            "input": smallest_input.strip(),
            "expected_output": smallest_expected.strip(),
        },
        "description": "Question 59 parses company name from email using re.match and group(2).",
    }
    (WORK_DIR / "inputs.json").write_text(
        json.dumps(inputs_data, indent=2) + "\n", encoding="utf-8"
    )

    # 2. expected_vs_actual.txt
    comparison_text = (
        "=== Published Example Verification ===\n"
        f"Input:                {published_input.strip()}\n"
        f"Expected output:      {published_expected.strip()!r}\n"
        f"Actual output:        {published_actual.strip()!r}\n"
        f"Matches:              {published_actual.strip() == published_expected.strip()}\n"
        f"Capture groups:       {match_groups}\n\n"
        "=== Resource & String Behavior Verification ===\n"
        f"m.string is emailAddress:                     {string_is_same}\n"
        f"m.group(2) == emailAddress[start:end]:        {slice_equal}\n"
        f"m.group(2) is not emailAddress:               {group2_not_same}\n"
        f"re.match('b','ab') is None vs re.search:      {match_vs_search}\n\n"
        "=== Smallest Supported Input Verification ===\n"
        f"Input:                {smallest_input.strip()}\n"
        f"Expected output:      {smallest_expected.strip()!r}\n"
        f"Actual output:        {smallest_actual.strip()!r}\n"
        f"Matches:              {smallest_actual.strip() == smallest_expected.strip()}\n"
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
    parser = argparse.ArgumentParser(description="Check Question 59 solution")
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="Run check with deliberately wrong expected output to test failure",
    )
    args = parser.parse_args()

    (
        code,
        pattern,
        pub_input,
        pub_expected,
        small_input,
        small_expected,
    ) = extract_question_59_data()

    expected_pub_output = "wrong_company\n" if args.wrong else pub_expected

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

    # 3. Verify pattern groups and string/resource behavior
    email_address = pub_input.strip()
    m = re.match(pattern, email_address)
    assert m is not None, "Failed to match email with extracted pattern"
    groups = m.groups()
    assert len(groups) == 3, f"Expected 3 capture groups, got {len(groups)}"
    assert m.group(1) == "john"
    assert m.group(2) == pub_expected.strip()
    assert m.group(3) == "com"

    # Behavior 1: m.string is the exact same object as the input string
    string_is_same = m.string is email_address
    assert string_is_same, "m.string must be the exact same object as email_address"

    # Behavior 2: m.group(2) is a str equal to input[m.start(2):m.end(2)] and is not the same object as input
    group2_val = m.group(2)
    assert isinstance(group2_val, str)
    start_pos, end_pos = m.span(2)
    slice_equal = group2_val == email_address[start_pos:end_pos]
    assert slice_equal, "m.group(2) must equal slice email_address[start:end]"
    group2_not_same = group2_val is not email_address
    assert group2_not_same, "m.group(2) must not be the same object as email_address"

    # Behavior 3: re.match only matches at index 0 while re.search scans
    match_at_zero = re.match("b", "ab") is None
    search_scans = re.search("b", "ab") is not None
    match_vs_search = match_at_zero and search_scans
    assert match_vs_search, "re.match('b', 'ab') must be None and re.search('b', 'ab') must find match"

    if not args.wrong:
        record_evidence(
            published_input=pub_input,
            published_expected=pub_expected,
            published_actual=res.stdout,
            smallest_input=small_input,
            smallest_expected=small_expected,
            smallest_actual=small_res.stdout,
            match_groups=groups,
            string_is_same=string_is_same,
            slice_equal=slice_equal,
            group2_not_same=group2_not_same,
            match_vs_search=match_vs_search,
        )
        print("R28-T049 PASS: Question 59 regex capture and string behavior verified successfully.")


if __name__ == "__main__":
    main()
