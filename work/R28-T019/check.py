"""
R28-T019 check.py
Task: Explain resource behavior — Python Question 10 (sort unique words)
Issue: https://github.com/S-AI-Projects/Python-programming-exercises/issues/23

Extracts the Q10 code block from the markdown at runtime, runs it via
subprocess with the published input, asserts the expected output.
Also tests boundary input (single word).
Exits non-zero on --wrong.
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

PUBLISHED_INPUT = "hello world and practice makes perfect and hello world again"
PUBLISHED_OUTPUT = "again and hello makes perfect practice world"
BOUNDARY_INPUT = "hello"
BOUNDARY_OUTPUT = "hello"


def extract_q10_code(md_path):
    """Extract the first ```python block under ### Question 10 (not 100)."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Match ### Question 10 followed by newline (not ### Question 100)
    pattern = r"### Question 10\n.*?```python\n(.*?)```"
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        raise RuntimeError("Could not find Q10 python code block in markdown")
    return m.group(1)


def run_code_with_input(code, stdin_val):
    result = subprocess.run(
        [sys.executable, "-c", code],
        input=stdin_val,
        capture_output=True, text=True,
        timeout=30
    )
    return result.stdout.strip(), result.returncode


def save_evidence(actual_main, actual_boundary):
    # inputs.json
    inputs = {
        "question": 10,
        "task": "R28-T019",
        "description": "Remove duplicate words and sort alphanumerically",
        "inputs": {
            "main_example": {
                "input": PUBLISHED_INPUT,
                "expected_output": PUBLISHED_OUTPUT
            },
            "boundary_example": {
                "input": BOUNDARY_INPUT,
                "expected_output": BOUNDARY_OUTPUT
            }
        }
    }
    with open(os.path.join(WORK_DIR, "inputs.json"), "w") as f:
        json.dump(inputs, f, indent=2)

    # expected_vs_actual.txt
    with open(os.path.join(WORK_DIR, "expected_vs_actual.txt"), "w") as f:
        f.write("--- Main example ---\n")
        f.write(f"Input    : {PUBLISHED_INPUT}\n")
        f.write(f"Expected : {PUBLISHED_OUTPUT}\n")
        f.write(f"Actual   : {actual_main}\n")
        f.write(f"Match    : {actual_main == PUBLISHED_OUTPUT}\n\n")
        f.write("--- Boundary example (single word) ---\n")
        f.write(f"Input    : {BOUNDARY_INPUT}\n")
        f.write(f"Expected : {BOUNDARY_OUTPUT}\n")
        f.write(f"Actual   : {actual_boundary}\n")
        f.write(f"Match    : {actual_boundary == BOUNDARY_OUTPUT}\n")

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
    code = extract_q10_code(MD_FILE)

    pub_expected = PUBLISHED_OUTPUT
    boundary_expected = BOUNDARY_OUTPUT

    if WRONG_MODE:
        pub_expected = "again and hello makes perfect practice world extra"
        boundary_expected = "goodbye"

    # Test main example
    actual_main, rc_main = run_code_with_input(code, PUBLISHED_INPUT)
    if rc_main != 0:
        print(f"FAIL: code execution error for main input (exit {rc_main})")
        sys.exit(rc_main)

    # Test boundary: single word
    actual_boundary, rc_boundary = run_code_with_input(code, BOUNDARY_INPUT)
    if rc_boundary != 0:
        print(f"FAIL: code execution error for boundary input (exit {rc_boundary})")
        sys.exit(rc_boundary)

    if not WRONG_MODE:
        save_evidence(actual_main, actual_boundary)

    # Assert main
    if actual_main != pub_expected:
        print(f"FAIL: expected {pub_expected!r}, got {actual_main!r}")
        sys.exit(1)
    print(f"PASS: main output = {actual_main!r}")

    # Assert boundary
    if actual_boundary != boundary_expected:
        print(f"FAIL: boundary expected {boundary_expected!r}, got {actual_boundary!r}")
        sys.exit(1)
    print(f"PASS: boundary (single word) = {actual_boundary!r}")


if __name__ == "__main__":
    main()
