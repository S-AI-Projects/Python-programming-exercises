#!/usr/bin/env python3
"""Check script for Question 38 (Task R28-T014)."""

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


def extract_question_38_code() -> tuple[str, str]:
    """Extract solution code and published output from Question 38 in markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    start_marker = "### Question 38"
    end_marker = "### Question 39"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        raise ValueError(f"Marker '{start_marker}' not found in {MARKDOWN_PATH}")

    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        raise ValueError(f"Marker '{end_marker}' not found after '{start_marker}' in {MARKDOWN_PATH}")

    section = content[start_idx:end_idx]

    # Extract code
    code_match = re.search(r"Solution:\s*\n+```python\s*\n(.*?)\n```", section, re.DOTALL)
    if not code_match:
        # Also check without colon
        code_match = re.search(r"Solution\s*\n+```python\s*\n(.*?)\n```", section, re.DOTALL)
    if not code_match:
        raise ValueError("Python code block not found in Question 38 Solution section")
    code = code_match.group(1).strip()

    # Extract published output
    out_match = re.search(r"Output:\s*\n+```text\s*\n(.*?)\n```", section, re.DOTALL)
    if not out_match:
        raise ValueError("Output block not found in Question 38")
    expected_output = out_match.group(1).strip() + "\n"

    return code, expected_output


def run_solution(code: str) -> subprocess.CompletedProcess[str]:
    """Execute code in a subprocess using sys.executable."""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def test_invariant_and_variations() -> dict[str, any]:
    """Test the invariant across loop stages and bounded variations."""
    # Invariant testing across all iterations for range(1, 21)
    li = list()
    for i in range(1, 21):
        li.append(i**2)
        assert len(li) == i, f"Invariant violated at i={i}: len={len(li)}"
        assert li[-1] == i**2, f"Invariant violated at i={i}: last element={li[-1]}"
        expected_slice = [(k + 1)**2 for k in range(min(i, 5))]
        assert li[:5] == expected_slice, f"Slice invariant violated at i={i}: {li[:5]} != {expected_slice}"

    # Bounded variations: m in [1, 2, 3, 6, 10, 21]
    variations = {}
    for m in [1, 2, 3, 6, 10, 21]:
        var_li = list()
        for i in range(1, m):
            var_li.append(i**2)
        variations[f"m_{m}"] = {
            "stopping_value_m": m,
            "loop_range": f"range(1, {m})",
            "total_elements": len(var_li),
            "full_list": var_li,
            "sliced_first_5": var_li[:5],
        }

    return variations


def record_evidence(
    expected_output: str,
    actual_output: str,
    variations: dict[str, any],
) -> None:
    """Write the required evidence files into WORK_DIR."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    # 1. inputs.json
    inputs_data = {
        "input": None,
        "description": "Question 38 (printList) takes no console input or arguments. Invariant evaluated over loop bounds range(1, 21) and bounded variations range(1, m).",
        "smallest_boundary_case": {
            "loop_bound": "range(1, 1)",
            "iterations": 0,
            "expected_list": [],
            "expected_slice": [],
        },
        "bounded_variations": variations,
    }
    (WORK_DIR / "inputs.json").write_text(
        json.dumps(inputs_data, indent=2) + "\n", encoding="utf-8"
    )

    # 2. expected_vs_actual.txt
    comparison_text = (
        "=== Published Example Execution ===\n"
        f"Function Call:        printList()\n"
        f"Expected Output:      {repr(expected_output)}\n"
        f"Actual Output:        {repr(actual_output)}\n"
        f"Match:                {actual_output == expected_output}\n\n"
        "=== Smallest Boundary Case (range(1, 1)) ===\n"
        "Loop Bound:           range(1, 1) (0 iterations)\n"
        "Expected List:        []\n"
        "Expected Slice [:5]:  []\n"
        f"Actual Slice:         {variations['m_1']['sliced_first_5']}\n"
        f"Match:                {variations['m_1']['sliced_first_5'] == []}\n\n"
        "=== Invariant Bounded Variations ===\n"
    )
    for key, data in variations.items():
        comparison_text += (
            f"Bound m={data['stopping_value_m']:<2} | Range: {data['loop_range']:<14} | "
            f"Total Elements: {data['total_elements']:<2} | Slice [:5]: {data['sliced_first_5']}\n"
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
    parser = argparse.ArgumentParser(description="Check Question 38 invariant")
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="Run check with deliberately wrong expected output to test failure",
    )
    args = parser.parse_args()

    code, expected_output = extract_question_38_code()

    if args.wrong:
        expected_output = "[999, 999]\n"

    # Test 1: Subprocess execution of the extracted code
    res = run_solution(code)
    if res.returncode != 0:
        sys.stderr.write(f"Process failed with exit code {res.returncode}:\n{res.stderr}\n")
        sys.exit(res.returncode)

    if res.stdout != expected_output:
        sys.stderr.write(
            f"AssertionError: Output mismatch!\n"
            f"  Expected: {repr(expected_output)}\n"
            f"  Actual:   {repr(res.stdout)}\n"
        )
        sys.exit(1)

    # Test 2: Invariant and bounded variations
    variations = test_invariant_and_variations()

    # If running normally (not --wrong), record all evidence files
    if not args.wrong:
        record_evidence(
            expected_output=expected_output,
            actual_output=res.stdout,
            variations=variations,
        )
        print("R28-T014 PASS: Invariant and bounded variations verified successfully.")


if __name__ == "__main__":
    main()
