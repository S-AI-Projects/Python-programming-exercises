"""
R28-T017 check.py
Task: Derive the result step by step — Python Question 2 (factorial)
Issue: https://github.com/S-AI-Projects/Python-programming-exercises/issues/21

Extracts the Q2 code block from the markdown at runtime, runs it via
subprocess with stdin=8, asserts output==40320, also tests boundary
input x=0 -> 1. Exits non-zero on --wrong.
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


def extract_q2_code(md_path):
    """Extract the first ```python block under ### Question 2."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = r"### Question 2\b.*?```python\n(.*?)```"
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        raise RuntimeError("Could not find Q2 python code block in markdown")
    return m.group(1)


def run_code_with_input(code, stdin_val):
    result = subprocess.run(
        [sys.executable, "-c", code],
        input=str(stdin_val),
        capture_output=True, text=True
    )
    return result.stdout.strip(), result.returncode


def save_evidence(actual_main, actual_boundary):
    # inputs.json
    inputs = {
        "question": 2,
        "task": "R28-T017",
        "description": "Compute factorial of a given number",
        "inputs": {
            "main_example": {"x": 8, "expected_output": "40320"},
            "boundary_example": {"x": 0, "expected_output": "1"}
        }
    }
    with open(os.path.join(WORK_DIR, "inputs.json"), "w") as f:
        json.dump(inputs, f, indent=2)

    # expected_vs_actual.txt
    with open(os.path.join(WORK_DIR, "expected_vs_actual.txt"), "w") as f:
        f.write("--- Main example (x=8) ---\n")
        f.write(f"Expected : 40320\n")
        f.write(f"Actual   : {actual_main}\n")
        f.write(f"Match    : {actual_main == '40320'}\n\n")
        f.write("--- Boundary example (x=0) ---\n")
        f.write(f"Expected : 1\n")
        f.write(f"Actual   : {actual_boundary}\n")
        f.write(f"Match    : {actual_boundary == '1'}\n")

    # tool_versions.txt
    ver = subprocess.run([sys.executable, "--version"],
                         capture_output=True, text=True)
    with open(os.path.join(WORK_DIR, "tool_versions.txt"), "w") as f:
        f.write(ver.stdout or ver.stderr)

    # failing_check_output.txt
    fail_result = subprocess.run(
        [sys.executable, os.path.abspath(__file__), "--wrong"],
        capture_output=True, text=True
    )
    with open(os.path.join(WORK_DIR, "failing_check_output.txt"), "w") as f:
        f.write(fail_result.stdout)
        f.write(fail_result.stderr)
        f.write(f"\nExit code: {fail_result.returncode}\n")


def main():
    code = extract_q2_code(MD_FILE)

    # Published expected output for fact(8)
    pub_expected = "40320"
    boundary_expected = "1"

    if WRONG_MODE:
        # Deliberate wrong values — must trigger failure
        pub_expected = "40321"
        boundary_expected = "0"

    # Test main example: x=8
    actual_main, rc_main = run_code_with_input(code, 8)
    if rc_main != 0:
        print(f"FAIL: code execution error for x=8 (exit {rc_main})")
        sys.exit(rc_main)

    # Test boundary example: x=0
    actual_boundary, rc_boundary = run_code_with_input(code, 0)
    if rc_boundary != 0:
        print(f"FAIL: code execution error for x=0 (exit {rc_boundary})")
        sys.exit(rc_boundary)

    if not WRONG_MODE:
        save_evidence(actual_main, actual_boundary)

    # Assert main
    if actual_main != pub_expected:
        print(f"FAIL: fact(8) expected {pub_expected!r}, got {actual_main!r}")
        sys.exit(1)
    print(f"PASS: fact(8) = {actual_main!r}")

    # Assert boundary
    if actual_boundary != boundary_expected:
        print(f"FAIL: fact(0) expected {boundary_expected!r}, got {actual_boundary!r}")
        sys.exit(1)
    print(f"PASS: fact(0) = {actual_boundary!r}  (base case)")


if __name__ == "__main__":
    main()
