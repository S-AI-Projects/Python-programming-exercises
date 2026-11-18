#!/usr/bin/env python3
"""Check script for Question 90 (Task R28-T045)."""

from __future__ import annotations

import argparse
import ast
import contextlib
import io
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


def extract_question_90_data() -> tuple[str, str]:
    """Extract the solution code and expected output from Question 90 in markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    match = re.search(
        r"^### Question 90\s*\n(.*?)(?=^### Question 91\s*\n)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise ValueError("Could not find Question 90 section in markdown")

    section = match.group(1)

    code_match = re.search(r"Solution:\s*\n+```(?:python)?\s*\n(.*?)\n```", section, re.DOTALL)
    if not code_match:
        raise ValueError("Could not find solution code block in Question 90")
    code = code_match.group(1).strip()

    output_match = re.search(r"Output:\s*\n+```(?:text)?\s*\n(.*?)\n```", section, re.DOTALL)
    if not output_match:
        raise ValueError("Could not find output block in Question 90")
    expected_output = output_match.group(1).strip() + "\n"

    return code, expected_output


def run_code(code: str) -> subprocess.CompletedProcess[str]:
    """Execute code in a subprocess without stdin using sys.executable."""
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )


def count_distinct_objects(arr_obj: list) -> tuple[int, int]:
    """Return count of distinct block list objects and distinct row list objects."""
    distinct_blocks = len({id(b) for b in arr_obj})
    distinct_rows = len({id(r) for b in arr_obj for r in b})
    return distinct_blocks, distinct_rows


def record_evidence(
    expected_repr: str,
    actual_repr: str,
    boundary_actual: str,
    dim_d1: int,
    dim_d2: int,
    dim_d3: int,
    total_zeros: int,
    distinct_rows: int,
    distinct_blocks: int,
    shared_blocks: int,
    shared_rows: int,
) -> None:
    """Write the required 4 evidence files into WORK_DIR."""
    # 1. inputs.json
    inputs_data = {
        "input": None,
        "description": "Question 90 takes no console input; generates a 3x5x8 3D array of zeros via nested list comprehensions.",
        "published_dimensions": {
            "blocks": dim_d1,
            "rows_per_block": dim_d2,
            "cols_per_row": dim_d3,
            "total_zeros": total_zeros,
            "distinct_block_objects": distinct_blocks,
            "distinct_row_objects": distinct_rows,
        },
        "boundary_dimensions": {"blocks": 1, "rows_per_block": 1, "cols_per_row": 1, "total_zeros": 1},
    }
    (WORK_DIR / "inputs.json").write_text(
        json.dumps(inputs_data, indent=2) + "\n", encoding="utf-8"
    )

    # 2. expected_vs_actual.txt
    comparison_text = (
        "=== Published 3x5x8 3D Array Verification ===\n"
        f"Outer blocks count:    {dim_d1}\n"
        f"Rows per block:        {dim_d2}\n"
        f"Columns per row:       {dim_d3}\n"
        f"Total elements:        {total_zeros}\n"
        f"Distinct block objects:{distinct_blocks}\n"
        f"Distinct row objects:  {distinct_rows}\n"
        f"Matches Expected repr: {actual_repr == expected_repr}\n\n"
        "=== Shared-Reference Negative Control Verification ===\n"
        "Shared code:           array = [[[0]*8]*5]*3\n"
        f"Distinct block objects:{shared_blocks}\n"
        f"Distinct row objects:  {shared_rows}\n"
        f"Fails distinct check (< 15 rows): {shared_rows < 15}\n\n"
        "=== Boundary 1x1x1 Array Verification ===\n"
        f"Output repr:           {boundary_actual.strip()}\n"
        f"Matches [[[0]]]:       {boundary_actual.strip() == '[[[0]]]'}\n"
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
    parser = argparse.ArgumentParser(description="Check Question 90 solution")
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="Run check with deliberately wrong expected output to test failure",
    )
    args = parser.parse_args()

    expected_dim_d1 = 4 if args.wrong else 3

    code, expected_repr = extract_question_90_data()

    # 1. Test published solution via subprocess for stdout and value checks
    res = run_code(code)
    if res.returncode != 0:
        sys.stderr.write(f"Process failed with exit code {res.returncode}:\n{res.stderr}\n")
        sys.exit(res.returncode)

    assert res.stdout.endswith("\n"), "Output must end with a newline"
    raw_str = res.stdout.strip()

    try:
        arr = ast.literal_eval(raw_str)
    except Exception as e:
        sys.stderr.write(f"Failed to parse stdout as literal: {e}\n")
        sys.exit(1)

    assert isinstance(arr, list), f"Expected outer list, got {type(arr).__name__}"
    if len(arr) != expected_dim_d1:
        sys.stderr.write(
            f"AssertionError: Dimension mismatch! Expected {expected_dim_d1} outer blocks, got {len(arr)}\n"
        )
        sys.exit(1)

    assert all(isinstance(block, list) and len(block) == 5 for block in arr), "Each block must have 5 rows"
    assert all(isinstance(row, list) and len(row) == 8 for block in arr for row in block), "Each row must have 8 columns"
    total_zeros = sum(len(row) for block in arr for row in block)
    assert total_zeros == 120, f"Expected 120 total elements, got {total_zeros}"
    assert all(x == 0 for block in arr for row in block for x in row), "All elements must be integer 0"

    assert res.stdout == expected_repr, "Exact stdout string representation mismatch against markdown output block"

    # 2. Exec extracted solution in-process on real objects to assert reference independence
    env: dict = {}
    f_capture = io.StringIO()
    with contextlib.redirect_stdout(f_capture):
        exec(code, env)
    real_array = env.get("array")
    assert isinstance(real_array, list), "Variable 'array' not found as list in execution environment"

    distinct_blocks, distinct_rows = count_distinct_objects(real_array)
    assert distinct_blocks == 3, f"Expected 3 distinct block list objects, got {distinct_blocks}"
    assert distinct_rows == 15, f"Expected 15 distinct row list objects across blocks, got {distinct_rows}"

    for i in range(len(real_array)):
        for j in range(i + 1, len(real_array)):
            assert real_array[i] is not real_array[j], f"Blocks {i} and {j} must be distinct list objects"
    for block in real_array:
        for r1 in range(len(block)):
            for r2 in range(r1 + 1, len(block)):
                assert block[r1] is not block[r2], f"Rows {r1} and {r2} must be distinct list objects"

    # 3. Control: prove that identity check detects shared references
    shared_env: dict = {}
    shared_code = "array = [[[0]*8]*5]*3\nprint(array)"
    f_shared = io.StringIO()
    with contextlib.redirect_stdout(f_shared):
        exec(shared_code, shared_env)
    shared_array = shared_env.get("array")
    assert isinstance(shared_array, list), "Shared array control failed to initialize"
    shared_blocks, shared_rows = count_distinct_objects(shared_array)
    assert shared_rows < 15, f"Control must report fewer than 15 distinct rows, got {shared_rows}"
    assert shared_blocks < 3, f"Control must report fewer than 3 distinct blocks, got {shared_blocks}"

    # 4. Test smallest boundary variation (1x1x1)
    boundary_code, count = re.subn(r"range\(8\)", "range(1)", code)
    assert count == 1, "Failed to substitute range(8)"
    boundary_code, count = re.subn(r"range\(5\)", "range(1)", boundary_code)
    assert count == 1, "Failed to substitute range(5)"
    boundary_code, count = re.subn(r"range\(3\)", "range(1)", boundary_code)
    assert count == 1, "Failed to substitute range(3)"

    b_res = run_code(boundary_code)
    if b_res.returncode != 0:
        sys.stderr.write(f"Boundary process failed: {b_res.stderr}\n")
        sys.exit(b_res.returncode)

    assert b_res.stdout.strip() == "[[[0]]]", f"Boundary output mismatch: {b_res.stdout!r}"

    if not args.wrong:
        record_evidence(
            expected_repr=expected_repr,
            actual_repr=res.stdout,
            boundary_actual=b_res.stdout,
            dim_d1=len(arr),
            dim_d2=5,
            dim_d3=8,
            total_zeros=total_zeros,
            distinct_rows=distinct_rows,
            distinct_blocks=distinct_blocks,
            shared_blocks=shared_blocks,
            shared_rows=shared_rows,
        )
        print("R28-T045 PASS: 3x5x8 array, real object identity, and boundary 1x1x1 verified successfully.")


if __name__ == "__main__":
    main()
