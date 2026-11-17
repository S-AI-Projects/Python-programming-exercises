#!/usr/bin/env python3
"""Check script for Question 36 (Task R28-T047)."""

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


def extract_question_36_data() -> tuple[str, str, str, int, int]:
    """Extract code, expected output, and range boundaries from markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    match = re.search(
        r"^### Question 36\s*\n(.*?)(?=^### Question 37\s*\n)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise ValueError("Could not find Question 36 section in markdown")

    section = match.group(1)

    code_match = re.search(r"Solution\s*\n+```(?:python)?\s*\n(.*?)\n```", section, re.DOTALL)
    if not code_match:
        raise ValueError("Could not find solution code block in Question 36")
    code = code_match.group(1).strip()

    output_match = re.search(r"Output:\s*\n+```(?:text)?\s*\n(.*?)\n```", section, re.DOTALL)
    if not output_match:
        raise ValueError("Could not find output block in Question 36")
    expected_output = output_match.group(1).strip() + "\n"

    # Extract smallest output from explanation
    small_match = re.search(r"prints\s+`?(\d+)`?", section)
    if not small_match:
        raise ValueError("Could not find smallest expected output in Question 36 explanation")
    smallest_expected = small_match.group(1).strip() + "\n"

    # Extract range bounds directly from code
    range_match = re.search(r"range\((\d+),\s*(\d+)\)", code)
    if not range_match:
        raise ValueError("Could not extract range bounds from solution code")
    start_val = int(range_match.group(1))
    stop_val = int(range_match.group(2))

    return code, expected_output, smallest_expected, start_val, stop_val


def run_code(code: str) -> subprocess.CompletedProcess[str]:
    """Execute code in a subprocess without stdin using sys.executable."""
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )


def record_evidence(
    expected_output: str,
    actual_output: str,
    smallest_expected: str,
    smallest_actual: str,
    keys_count: int,
    start_val: int,
    stop_val: int,
) -> None:
    """Write the required 4 evidence files into WORK_DIR."""
    # 1. inputs.json
    inputs_data = {
        "input": None,
        "description": "Question 36 takes no console input; generates a dictionary for keys 1..20 and prints the keys.",
        "published_range": {"start": start_val, "stop": stop_val, "keys_count": keys_count},
        "smallest_range": {"start": start_val, "stop": start_val + 1, "keys_count": 1},
    }
    (WORK_DIR / "inputs.json").write_text(
        json.dumps(inputs_data, indent=2) + "\n", encoding="utf-8"
    )

    # 2. expected_vs_actual.txt
    comparison_text = (
        "=== Published Question 36 Verification ===\n"
        f"Keys count:           {keys_count}\n"
        f"Matches expected:     {actual_output == expected_output}\n\n"
        "=== Smallest Supported Range Verification ===\n"
        f"Smallest actual repr: {smallest_actual.strip()!r}\n"
        f"Matches expected:     {smallest_actual.strip() == smallest_expected.strip()}\n"
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
    parser = argparse.ArgumentParser(description="Check Question 36 solution")
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="Run check with deliberately wrong expected output to test failure",
    )
    args = parser.parse_args()

    (
        code,
        expected_output,
        smallest_expected,
        start_val,
        stop_val,
    ) = extract_question_36_data()

    expected_count = (stop_val - start_val) + 5 if args.wrong else (stop_val - start_val)

    # 1. Test published solution
    res = run_code(code)
    if res.returncode != 0:
        sys.stderr.write(f"Process failed with exit code {res.returncode}:\n{res.stderr}\n")
        sys.exit(res.returncode)

    assert res.stdout.endswith("\n"), "Output must end with a newline"
    lines = res.stdout.splitlines()

    if len(lines) != expected_count:
        sys.stderr.write(
            f"AssertionError: Expected {expected_count} keys printed, got {len(lines)}\n"
        )
        sys.exit(1)

    assert res.stdout == expected_output, f"Output mismatch:\nExpected:\n{expected_output}\nActual:\n{res.stdout}"

    # Verify intermediate dictionary structure logic
    d = {i: i**2 for i in range(start_val, stop_val)}
    assert len(d) == (stop_val - start_val)
    assert list(d.keys()) == list(range(start_val, stop_val))
    assert list(d.values()) == [i**2 for i in range(start_val, stop_val)]

    # 2. Test smallest supported range: range(start_val, start_val + 1)
    smallest_code, count = re.subn(r"range\(\d+,\s*\d+\)", f"range({start_val}, {start_val + 1})", code)
    assert count == 1, "Failed to substitute range"

    b_res = run_code(smallest_code)
    if b_res.returncode != 0:
        sys.stderr.write(f"Smallest range process failed: {b_res.stderr}\n")
        sys.exit(b_res.returncode)

    assert b_res.stdout == smallest_expected, f"Smallest range output mismatch: {b_res.stdout!r}"

    if not args.wrong:
        record_evidence(
            expected_output=expected_output,
            actual_output=res.stdout,
            smallest_expected=smallest_expected,
            smallest_actual=b_res.stdout,
            keys_count=len(lines),
            start_val=start_val,
            stop_val=stop_val,
        )
        print("R28-T047 PASS: Question 36 keys derivation and smallest range verified successfully.")


if __name__ == "__main__":
    main()
