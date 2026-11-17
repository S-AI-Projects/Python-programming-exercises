#!/usr/bin/env python3
"""Check script for Question 65 (Task R28-T015)."""

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


def extract_question_65_data() -> tuple[str, str, str, str, str]:
    """Extract code, published input/output, and boundary input/output from Question 65 in markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    start_marker = "### Question 65"
    end_marker = "### Question 66"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        raise ValueError(f"Marker '{start_marker}' not found in {MARKDOWN_PATH}")

    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        raise ValueError(f"Marker '{end_marker}' not found after '{start_marker}' in {MARKDOWN_PATH}")

    section = content[start_idx:end_idx]

    # Extract solution code
    code_match = re.search(r"Solution:\s*\n+```python\s*\n(.*?)\n```", section, re.DOTALL)
    if not code_match:
        raise ValueError("Python code block not found in Question 65 Solution section")
    code = code_match.group(1).strip()

    # Extract published example
    pub_match = re.search(
        r"If the following n is given as input to the program:\s*\n+([^\n]+)\s*\n+Then, the output of the program should be:\s*\n+([^\n]+)",
        section,
    )
    if not pub_match:
        raise ValueError("Could not parse published example from Question 65 in markdown")

    pub_input = pub_match.group(1).strip() + "\n"
    pub_expected = pub_match.group(2).strip() + "\n"

    # Extract boundary input
    boundary_match = re.search(
        r"Suppose the smallest supported input is given as input to the program:\s*\n+([^\n]+)\s*\n+Then, the output of the program should be:\s*\n+([^\n]+)",
        section,
    )
    if not boundary_match:
        raise ValueError("Could not parse smallest supported input from Question 65 in markdown")

    boundary_input = boundary_match.group(1).strip() + "\n"
    boundary_expected = boundary_match.group(2).strip() + "\n"

    return code, pub_input, pub_expected, boundary_input, boundary_expected


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
    pub_actual: str,
    boundary_input: str,
    boundary_expected: str,
    boundary_actual: str,
) -> None:
    """Write the required evidence files into WORK_DIR."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    # 1. inputs.json
    inputs_data = {
        "published_input": pub_input,
        "smallest_supported_input": boundary_input,
        "base_case_input": "0\n",
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
        f"Numeric Value: {int(pub_actual.strip())}\n"
        f"Match:         {pub_actual == pub_expected}\n\n"
        "=== Smallest Supported Input (n = 1) ===\n"
        f"Input:         {repr(boundary_input)}\n"
        f"Expected:      {repr(boundary_expected)}\n"
        f"Actual:        {repr(boundary_actual)}\n"
        f"Numeric Value: {int(boundary_actual.strip())}\n"
        f"Match:         {boundary_actual == boundary_expected}\n\n"
        "=== Reproducibility & State Independence ===\n"
        "Deterministic: Yes (pure recursion on n)\n"
        "Hidden State:  None (no global state, side-effects, or random seeds)\n"
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
    parser = argparse.ArgumentParser(description="Check Question 65 solution")
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="Run check with deliberately wrong expected output to test failure",
    )
    args = parser.parse_args()

    code, pub_input, pub_expected, boundary_input, boundary_expected = extract_question_65_data()

    if args.wrong:
        pub_expected = "9999\n"

    # Test 1: Published example (n = 5)
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

    assert int(pub_result.stdout.strip()) == 500, "Numeric value mismatch for published example"

    # Test 2: Smallest supported input (n = 1)
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

    assert int(boundary_result.stdout.strip()) == 100, "Numeric value mismatch for boundary input"

    # Test 3: Reproducibility / state independence across multiple runs
    for run_idx in range(3):
        repeat_res = run_solution(code, pub_input)
        assert repeat_res.stdout == pub_expected, f"Run {run_idx} failed reproducibility check!"

    # If running normally (not --wrong), record all evidence files
    if not args.wrong:
        record_evidence(
            pub_input=pub_input,
            pub_expected=pub_expected,
            pub_actual=pub_result.stdout,
            boundary_input=boundary_input,
            boundary_expected=boundary_expected,
            boundary_actual=boundary_result.stdout,
        )
        print("R28-T015 PASS: Published example, boundary input, and reproducibility verified successfully.")


if __name__ == "__main__":
    main()
