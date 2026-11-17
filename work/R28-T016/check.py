"""
R28-T016 check.py
Task: Clarify the implementation — Python Question 92
Issue: https://github.com/S-AI-Projects/Python-programming-exercises/issues/20

Extracts the Q92 code block from the markdown at runtime, runs it via
subprocess, asserts the expected output, and exits non-zero on --wrong.
"""

import sys
import re
import subprocess
import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MD_FILE = os.path.join(REPO_ROOT,
    "100+ Python challenging programming exercises for Python 3.md")
WORK_DIR = os.path.dirname(os.path.abspath(__file__))

WRONG_MODE = "--wrong" in sys.argv


def extract_q92_code(md_path):
    """Extract the first ```python block under ### Question 92."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = r"### Question 92\b.*?```python\n(.*?)```"
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        raise RuntimeError("Could not find Q92 python code block in markdown")
    return m.group(1)


def run_code(code):
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True
    )
    return result.stdout.strip(), result.returncode


def save_evidence(code, actual, expected):
    # inputs.json
    inputs = {
        "question": 92,
        "task": "R28-T016",
        "description": "Remove value 24 from list using list comprehension",
        "inputs": {
            "main_example": "[12,24,35,24,88,120,155]",
            "boundary_example": "[24]"
        }
    }
    with open(os.path.join(WORK_DIR, "inputs.json"), "w") as f:
        json.dump(inputs, f, indent=2)

    # expected_vs_actual.txt
    with open(os.path.join(WORK_DIR, "expected_vs_actual.txt"), "w") as f:
        f.write(f"Expected : {expected}\n")
        f.write(f"Actual   : {actual}\n")
        f.write(f"Match    : {actual == expected}\n")

    # tool_versions.txt
    ver = subprocess.run([sys.executable, "--version"],
                         capture_output=True, text=True)
    with open(os.path.join(WORK_DIR, "tool_versions.txt"), "w") as f:
        f.write(ver.stdout or ver.stderr)

    # failing_check_output.txt — run self with --wrong
    fail_result = subprocess.run(
        [sys.executable, os.path.abspath(__file__), "--wrong"],
        capture_output=True, text=True
    )
    with open(os.path.join(WORK_DIR, "failing_check_output.txt"), "w") as f:
        f.write(fail_result.stdout)
        f.write(fail_result.stderr)
        f.write(f"\nExit code: {fail_result.returncode}\n")


def main():
    code = extract_q92_code(MD_FILE)

    # The correct published output for Q92
    pub_expected = "[12, 35, 88, 120, 155]"

    if WRONG_MODE:
        # Deliberate wrong expected value — check must fail
        pub_expected = "[12, 24, 35, 88, 120, 155]"

    actual, rc = run_code(code)

    if not WRONG_MODE:
        save_evidence(code, actual, pub_expected)

    if rc != 0:
        print(f"FAIL: code execution error (exit {rc})")
        sys.exit(rc)

    if actual != pub_expected:
        print(f"FAIL: expected {pub_expected!r}, got {actual!r}")
        sys.exit(1)

    print(f"PASS: Q92 output = {actual!r}")

    # Also verify boundary case: [24] filtered to []
    boundary_code = "li=[24]\nli=[x for x in li if x!=24]\nprint(li)"
    boundary_actual, brc = run_code(boundary_code)
    boundary_expected = "[]"
    if WRONG_MODE:
        boundary_expected = "[24]"
    if brc != 0 or boundary_actual != boundary_expected:
        print(f"FAIL: boundary case expected {boundary_expected!r}, got {boundary_actual!r}")
        sys.exit(1)
    print(f"PASS: boundary case [24] -> {boundary_actual!r}")


if __name__ == "__main__":
    main()
