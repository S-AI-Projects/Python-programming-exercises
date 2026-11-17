#!/usr/bin/env python3
"""Check script for Question 17 (Task R28-T013)."""

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


def extract_question_17_data() -> tuple[str, str, str, str, str, str]:
    """Extract (src_code, alt_code, pub_input, pub_expected, boundary_input, boundary_expected) from Question 17 in markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    start_marker = "### Question 17"
    end_marker = "### Question 18"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        raise ValueError(f"Marker '{start_marker}' not found in {MARKDOWN_PATH}")

    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        raise ValueError(f"Marker '{end_marker}' not found after '{start_marker}' in {MARKDOWN_PATH}")

    section = content[start_idx:end_idx]

    # Extract source solution
    src_match = re.search(r"Solution:\s*\n+```python\s*\n(.*?)\n```", section, re.DOTALL)
    if not src_match:
        raise ValueError("Source python code block not found in Question 17")
    src_code = src_match.group(1).strip()

    # Extract alternative solution
    alt_match = re.search(r"Alternative solution:\s*\n+```python\s*\n(.*?)\n```", section, re.DOTALL)
    if not alt_match:
        raise ValueError("Alternative python code block not found in Question 17")
    alt_code = alt_match.group(1).strip()

    # Extract published example
    pub_match = re.search(
        r"Suppose the following input is supplied to the program:\s*\n+(.*?)\n+Then, the output should be:\s*\n+([^\n]+)",
        section,
        re.DOTALL,
    )
    if not pub_match:
        raise ValueError("Could not parse published example from Question 17 in markdown")

    pub_input = pub_match.group(1).strip() + "\n\n"
    pub_expected = pub_match.group(2).strip() + "\n"

    # Extract boundary input
    boundary_match = re.search(
        r"Suppose the smallest supported input is supplied to the program:\s*\n+(.*?)\n+Then, the output should be:\s*\n+([^\n]+)",
        section,
        re.DOTALL,
    )
    if not boundary_match:
        raise ValueError("Could not parse smallest supported input from Question 17 in markdown")

    boundary_input = boundary_match.group(1).strip() + "\n\n"
    boundary_expected = boundary_match.group(2).strip() + "\n"

    return src_code, alt_code, pub_input, pub_expected, boundary_input, boundary_expected


def run_solution(code: str, stdin_data: str) -> subprocess.CompletedProcess[str]:
    """Execute code with stdin_data using sys.executable."""
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
    src_pub_actual: str,
    alt_pub_actual: str,
    boundary_input: str,
    boundary_expected: str,
    src_boundary_actual: str,
    alt_boundary_actual: str,
) -> None:
    """Write the required evidence files into WORK_DIR."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    # 1. inputs.json
    inputs_data = {
        "published_input": pub_input,
        "smallest_supported_input": boundary_input,
    }
    (WORK_DIR / "inputs.json").write_text(
        json.dumps(inputs_data, indent=2) + "\n", encoding="utf-8"
    )

    # 2. expected_vs_actual.txt
    comparison_text = (
        "=== Published Example ===\n"
        f"Input:                {repr(pub_input)}\n"
        f"Expected Output:      {repr(pub_expected)}\n"
        f"Source Output:        {repr(src_pub_actual)}\n"
        f"Alternative Output:   {repr(alt_pub_actual)}\n"
        f"Source Matches:       {src_pub_actual == pub_expected}\n"
        f"Alternative Matches:  {alt_pub_actual == pub_expected}\n"
        f"Methods Equivalent:   {src_pub_actual == alt_pub_actual}\n\n"
        "=== Smallest Supported Input ===\n"
        f"Input:                {repr(boundary_input)}\n"
        f"Expected Output:      {repr(boundary_expected)}\n"
        f"Source Output:        {repr(src_boundary_actual)}\n"
        f"Alternative Output:   {repr(alt_boundary_actual)}\n"
        f"Source Matches:       {src_boundary_actual == boundary_expected}\n"
        f"Alternative Matches:  {alt_boundary_actual == boundary_expected}\n"
        f"Methods Equivalent:   {src_boundary_actual == alt_boundary_actual}\n"
    )
    (WORK_DIR / "expected_vs_actual.txt").write_text(comparison_text, encoding="utf-8")

    # 3. tool_versions.txt (Python version and OS name)
    versions_text = (
        f"Python: {platform.python_version()}\n"
        f"OS: {platform.system()}\n"
    )
    (WORK_DIR / "tool_versions.txt").write_text(versions_text, encoding="utf-8")

    # 4. failing_check_output.txt
    # Run self with --wrong in a subprocess to capture deliberate failing output
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
    parser = argparse.ArgumentParser(description="Check Question 17 solutions")
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="Run check with deliberately wrong expected output to test failure",
    )
    args = parser.parse_args()

    src_code, alt_code, pub_input, pub_expected, boundary_input, boundary_expected = extract_question_17_data()

    if args.wrong:
        pub_expected = "WRONG_OUTPUT\n"

    # Test 1: Published example on Source solution
    src_pub = run_solution(src_code, pub_input)
    if src_pub.returncode != 0:
        sys.stderr.write(
            f"Source solution failed on published input with code {src_pub.returncode}:\n{src_pub.stderr}\n"
        )
        sys.exit(src_pub.returncode)

    if src_pub.stdout != pub_expected:
        sys.stderr.write(
            f"AssertionError: Source published output mismatch!\n"
            f"  Expected: {repr(pub_expected)}\n"
            f"  Actual:   {repr(src_pub.stdout)}\n"
        )
        sys.exit(1)

    # Test 2: Published example on Alternative solution
    alt_pub = run_solution(alt_code, pub_input)
    if alt_pub.returncode != 0:
        sys.stderr.write(
            f"Alternative solution failed on published input with code {alt_pub.returncode}:\n{alt_pub.stderr}\n"
        )
        sys.exit(alt_pub.returncode)

    if alt_pub.stdout != pub_expected:
        sys.stderr.write(
            f"AssertionError: Alternative published output mismatch!\n"
            f"  Expected: {repr(pub_expected)}\n"
            f"  Actual:   {repr(alt_pub.stdout)}\n"
        )
        sys.exit(1)

    assert src_pub.stdout == alt_pub.stdout, "Source and alternative outputs do not match on published input!"
    assert int(src_pub.stdout.strip()) == 500, "Numerical value does not equal 500!"

    # Test 3: Smallest supported input on Source solution
    src_bound = run_solution(src_code, boundary_input)
    if src_bound.returncode != 0:
        sys.stderr.write(
            f"Source solution failed on boundary input with code {src_bound.returncode}:\n{src_bound.stderr}\n"
        )
        sys.exit(src_bound.returncode)

    if src_bound.stdout != boundary_expected:
        sys.stderr.write(
            f"AssertionError: Source boundary output mismatch!\n"
            f"  Expected: {repr(boundary_expected)}\n"
            f"  Actual:   {repr(src_bound.stdout)}\n"
        )
        sys.exit(1)

    # Test 4: Smallest supported input on Alternative solution
    alt_bound = run_solution(alt_code, boundary_input)
    if alt_bound.returncode != 0:
        sys.stderr.write(
            f"Alternative solution failed on boundary input with code {alt_bound.returncode}:\n{alt_bound.stderr}\n"
        )
        sys.exit(alt_bound.returncode)

    if alt_bound.stdout != boundary_expected:
        sys.stderr.write(
            f"AssertionError: Alternative boundary output mismatch!\n"
            f"  Expected: {repr(boundary_expected)}\n"
            f"  Actual:   {repr(alt_bound.stdout)}\n"
        )
        sys.exit(1)

    assert src_bound.stdout == alt_bound.stdout, "Source and alternative outputs do not match on boundary input!"
    assert int(src_bound.stdout.strip()) == 100, "Numerical value does not equal 100!"

    # If running normally (not --wrong), record all evidence files
    if not args.wrong:
        record_evidence(
            pub_input=pub_input,
            pub_expected=pub_expected,
            src_pub_actual=src_pub.stdout,
            alt_pub_actual=alt_pub.stdout,
            boundary_input=boundary_input,
            boundary_expected=boundary_expected,
            src_boundary_actual=src_bound.stdout,
            alt_boundary_actual=alt_bound.stdout,
        )
        print("R28-T013 PASS: Source and alternative solutions verified successfully.")


if __name__ == "__main__":
    main()
