#!/usr/bin/env python3
"""Check script for Question 78 (Task R28-T044)."""

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


def extract_question_78_code() -> str:
    """Extract the solution code from Question 78 in markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    match = re.search(
        r"^### Question 78\s*\n(.*?)(?=^### Question 79\s*\n)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise ValueError("Could not find Question 78 section in markdown")

    section = match.group(1)

    code_match = re.search(r"Solution:\s*\n+```python\s*\n(.*?)\n```", section, re.DOTALL)
    if not code_match:
        raise ValueError("Could not find solution code block in Question 78")

    return code_match.group(1).strip()


def run_code(code: str) -> subprocess.CompletedProcess[str]:
    """Execute code in a subprocess without stdin using sys.executable."""
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )


def assert_sample_output(stdout: str, expected_k: int, n: int) -> list[int]:
    """Verify that stdout satisfies the random.sample(range(n), k) invariant."""
    assert stdout.endswith("\n"), "Output must end with a newline"
    raw_str = stdout.strip()

    try:
        val = ast.literal_eval(raw_str)
    except Exception as e:
        raise AssertionError(f"Could not parse stdout as a Python literal: {raw_str!r}") from e

    assert isinstance(val, list), f"Expected list, got {type(val).__name__}"
    assert len(val) == expected_k, f"Expected length {expected_k}, got {len(val)}"
    assert all(isinstance(x, int) for x in val), f"All elements must be ints: {val}"
    assert len(set(val)) == expected_k, f"Elements must be distinct without replacement: {val}"
    assert all(0 <= x < n for x in val), f"All elements must be in [0, {n}): {val}"
    assert repr(val) == raw_str, f"Printed representation mismatch: {raw_str!r} vs {repr(val)!r}"

    return val


def record_evidence(
    variation_results: dict[str, str],
) -> None:
    """Write the required 4 evidence files into WORK_DIR deterministically."""
    # 1. inputs.json
    inputs_data = {
        "input": None,
        "description": "Question 78 takes no console input; samples from range(n) without replacement.",
        "published_fixture": {"n": 100, "k": 5},
        "tested_variations": [
            {"n": 1, "k": 1, "note": "Minimal domain and sample; output must be exactly [0]"},
            {"n": 5, "k": 5, "note": "Full-domain boundary; output must be a permutation of [0, 1, 2, 3, 4]"},
            {"n": 10, "k": 1, "note": "Single draw from 10 elements"},
            {"n": 50, "k": 25, "note": "Half-domain draw"},
            {"n": 200, "k": 10, "note": "Larger population draw"},
        ],
    }
    (WORK_DIR / "inputs.json").write_text(
        json.dumps(inputs_data, indent=2) + "\n", encoding="utf-8"
    )

    # 2. expected_vs_actual.txt (Deterministic record)
    lines = [
        "=== Published Example Invariant Verification ===",
        "Code: random.sample(range(100), 5)",
        "Invariant: List of 5 distinct integers in [0, 99], followed by newline",
        "Total independent runs tested: 50",
        "Result: All 50 runs passed invariant assertions.",
        "",
        "=== Bounded Variations Verification ===",
    ]
    for var_name, res in variation_results.items():
        lines.append(f"{var_name}: {res}")

    (WORK_DIR / "expected_vs_actual.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

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
    parser = argparse.ArgumentParser(description="Check Question 78 invariant")
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="Run check with deliberately wrong expected output to test failure",
    )
    args = parser.parse_args()

    code = extract_question_78_code()

    # Extract published parameters directly from the code
    m_param = re.search(r"range\((\d+)\),\s*(\d+)", code)
    assert m_param, "Could not extract parameters from published code"
    pub_n = int(m_param.group(1))
    pub_k = int(m_param.group(2))

    expected_k_published = pub_k + 1 if args.wrong else pub_k

    # 1. Test published solution across 50 runs
    for _ in range(50):
        res = run_code(code)
        if res.returncode != 0:
            sys.stderr.write(f"Process failed with exit code {res.returncode}:\n{res.stderr}\n")
            sys.exit(res.returncode)

        try:
            assert_sample_output(res.stdout, expected_k_published, pub_n)
        except AssertionError as e:
            sys.stderr.write(f"AssertionError: {e}\n")
            sys.exit(1)

    # 2. Test 5 parameter variations
    variations = [
        (1, 1),
        (5, 5),
        (10, 1),
        (50, 25),
        (200, 10),
    ]

    variation_results: dict[str, str] = {}
    for n, k in variations:
        var_code, subs_count = re.subn(r"range\(\d+\),\s*\d+", f"range({n}), {k}", code)
        assert subs_count == 1, f"Regex substitution failed for variation ({n}, {k})"

        for _ in range(20):
            var_res = run_code(var_code)
            if var_res.returncode != 0:
                sys.stderr.write(f"Variation ({n}, {k}) failed with code {var_res.returncode}:\n{var_res.stderr}\n")
                sys.exit(var_res.returncode)

            val = assert_sample_output(var_res.stdout, k, n)

            # Specific boundary checks
            if (n, k) == (1, 1):
                assert val == [0], f"Expected exactly [0] for (1, 1), got {val}"
            elif (n, k) == (5, 5):
                assert sorted(val) == [0, 1, 2, 3, 4], f"Expected permutation of [0, 1, 2, 3, 4], got {val}"

        variation_results[f"Variation (n={n}, k={k})"] = "All 20 runs passed invariant assertions."

    if not args.wrong:
        record_evidence(variation_results)
        print("R28-T044 PASS: Published invariant and 5 bounded variations verified successfully.")


if __name__ == "__main__":
    main()
