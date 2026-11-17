#!/usr/bin/env python3
"""Check script for Question 18 (Task R28-T012)."""

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


def extract_question_18_data() -> tuple[str, str, str, str, str]:
    """Extract (solution_code, published_input, published_expected, boundary_input, boundary_expected) from Question 18 in markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    start_marker = "### Question 18"
    end_marker = "### Question 19"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        raise ValueError(f"Marker '{start_marker}' not found in {MARKDOWN_PATH}")

    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        raise ValueError(f"Marker '{end_marker}' not found after '{start_marker}' in {MARKDOWN_PATH}")

    section = content[start_idx:end_idx]

    # Extract solution code
    code_match = re.search(r"Solutions?:\s*\n+```python\s*\n(.*?)\n```", section, re.DOTALL)
    if not code_match:
        raise ValueError("Python code block not found in Question 18 Solution section")
    code = code_match.group(1).strip()

    # Extract published example
    pub_match = re.search(
        r"If the following passwords are given as input to the program:\s*\n+([^\n]+)\s*\n+Then, the output of the program should be:\s*\n+([^\n]+)",
        section,
    )
    if not pub_match:
        raise ValueError("Could not parse published example from Question 18 in markdown")

    pub_input = pub_match.group(1).strip() + "\n"
    pub_expected = pub_match.group(2).strip() + "\n"

    # Extract boundary example
    boundary_match = re.search(
        r"If the smallest supported boundary input is given as input to the program:\s*\n+([^\n]+)\s*\n+Then, the output of the program should be:\s*\n+([^\n]+)",
        section,
    )
    if not boundary_match:
        raise ValueError("Could not parse smallest supported boundary input from Question 18 in markdown")

    boundary_input = boundary_match.group(1).strip() + "\n"
    boundary_expected = boundary_match.group(2).strip() + "\n"

    return code, pub_input, pub_expected, boundary_input, boundary_expected


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


def run_solution_for_value_and_print(code: str, stdin_data: str) -> tuple[list[str], str]:
    """Execute solution and return both internal `value` list and printed output."""
    instrumented_code = f"""
{code}
import json
print("__VALUE_JSON__:" + json.dumps(value))
"""
    result = subprocess.run(
        [sys.executable, "-c", instrumented_code],
        input=stdin_data,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.write(f"Failed to execute instrumented code: {result.stderr}\n")
        sys.exit(result.returncode)

    lines = result.stdout.splitlines()
    value_line = None
    output_lines = []
    for line in lines:
        if line.startswith("__VALUE_JSON__:"):
            value_line = line[len("__VALUE_JSON__:"):]
        else:
            output_lines.append(line)

    val = json.loads(value_line) if value_line is not None else []
    printed = "\n".join(output_lines) + ("\n" if output_lines else "")
    return val, printed


def record_evidence(
    pub_input: str,
    pub_expected: str,
    pub_actual: str,
    pub_val: list[str],
    boundary_input: str,
    boundary_expected: str,
    boundary_actual: str,
    boundary_val: list[str],
) -> None:
    """Write the required evidence files into WORK_DIR."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    # 1. inputs.json
    inputs_data = {
        "published_input": pub_input,
        "smallest_boundary_input": boundary_input,
    }
    (WORK_DIR / "inputs.json").write_text(
        json.dumps(inputs_data, indent=2) + "\n", encoding="utf-8"
    )

    # 2. expected_vs_actual.txt
    comparison_text = (
        "=== Published Example ===\n"
        f"Input:         {repr(pub_input)}\n"
        f"Expected:      {repr(pub_expected)}\n"
        f"Actual:        {repr(pub_actual)}\n"
        f"Actual Value:  {pub_val}\n"
        f"Match:         {pub_actual == pub_expected}\n\n"
        "=== Smallest Boundary Input ===\n"
        f"Input:         {repr(boundary_input)}\n"
        f"Expected:      {repr(boundary_expected)}\n"
        f"Actual:        {repr(boundary_actual)}\n"
        f"Actual Value:  {boundary_val}\n"
        f"Match:         {boundary_actual == boundary_expected}\n"
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
    parser = argparse.ArgumentParser(description="Check Question 18 solution")
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="Run check with deliberately wrong expected output to test failure",
    )
    args = parser.parse_args()

    code, pub_input, pub_expected, boundary_input, boundary_expected = extract_question_18_data()

    if args.wrong:
        pub_expected = "WRONG_OUTPUT\n"

    # Test 1: Published example - assert both value and printed representation
    pub_result = run_solution(code, pub_input)
    if pub_result.returncode != 0:
        sys.stderr.write(
            f"Process failed on published input with exit code {pub_result.returncode}:\n{pub_result.stderr}\n"
        )
        sys.exit(pub_result.returncode)

    if pub_result.stdout != pub_expected:
        sys.stderr.write(
            f"AssertionError: Published example output mismatch!\n"
            f"  Expected: {repr(pub_expected)}\n"
            f"  Actual:   {repr(pub_result.stdout)}\n"
        )
        sys.exit(1)

    pub_val, pub_printed = run_solution_for_value_and_print(code, pub_input)
    if pub_val != ["ABd1234@1"]:
        sys.stderr.write(f"AssertionError: Published value mismatch: {pub_val} != ['ABd1234@1']\n")
        sys.exit(1)

    # Test 2: Smallest boundary input (length 6, meeting all criteria)
    boundary_result = run_solution(code, boundary_input)
    if boundary_result.returncode != 0:
        sys.stderr.write(
            f"Process failed on boundary input with exit code {boundary_result.returncode}:\n{boundary_result.stderr}\n"
        )
        sys.exit(boundary_result.returncode)

    if boundary_result.stdout != boundary_expected:
        sys.stderr.write(
            f"AssertionError: Boundary input output mismatch!\n"
            f"  Expected: {repr(boundary_expected)}\n"
            f"  Actual:   {repr(boundary_result.stdout)}\n"
        )
        sys.exit(1)

    boundary_val, boundary_printed = run_solution_for_value_and_print(code, boundary_input)
    if boundary_val != ["aB1#cd"]:
        sys.stderr.write(f"AssertionError: Boundary value mismatch: {boundary_val} != ['aB1#cd']\n")
        sys.exit(1)

    # If running normally (not --wrong), record all evidence files
    if not args.wrong:
        record_evidence(
            pub_input=pub_input,
            pub_expected=pub_expected,
            pub_actual=pub_result.stdout,
            pub_val=pub_val,
            boundary_input=boundary_input,
            boundary_expected=boundary_expected,
            boundary_actual=boundary_result.stdout,
            boundary_val=boundary_val,
        )
        print("R28-T012 PASS: Published example and boundary input verified successfully.")


if __name__ == "__main__":
    main()
