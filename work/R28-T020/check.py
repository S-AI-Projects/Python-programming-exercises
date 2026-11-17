"""
R28-T020 check.py
Task: Protect the example against regression — Python Question 69
Issue: https://github.com/S-AI-Projects/Python-programming-exercises/issues/24

Extracts the Q69 code block from the markdown at runtime, runs it via
subprocess with stdin=100, asserts output=="0,35,70".
Also tests boundary input n=0 -> "0".
Also verifies the mutant (and->or) produces a DIFFERENT result,
proving the test catches the regression.
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


def extract_q69_code(md_path):
    """Extract the first ```python block under ### Question 69."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = r"### Question 69\b.*?```python\n(.*?)```"
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        raise RuntimeError("Could not find Q69 python code block in markdown")
    return m.group(1)


def run_code_with_input(code, stdin_val):
    result = subprocess.run(
        [sys.executable, "-c", code],
        input=str(stdin_val),
        capture_output=True, text=True,
        timeout=30
    )
    return result.stdout.strip(), result.returncode


def save_evidence(actual_main, actual_boundary, mutant_output):
    # inputs.json
    inputs = {
        "question": 69,
        "task": "R28-T020",
        "description": "Generator for numbers divisible by both 5 and 7",
        "inputs": {
            "main_example": {"n": 100, "expected_output": "0,35,70"},
            "boundary_example": {"n": 0, "expected_output": "0"},
            "mutant_test": {
                "mutation": "and -> or in condition",
                "n": 100,
                "mutant_output": mutant_output,
                "correct_output": "0,35,70",
                "mutant_caught": mutant_output != "0,35,70"
            }
        }
    }
    with open(os.path.join(WORK_DIR, "inputs.json"), "w") as f:
        json.dump(inputs, f, indent=2)

    # expected_vs_actual.txt
    with open(os.path.join(WORK_DIR, "expected_vs_actual.txt"), "w") as f:
        f.write("--- Main example (n=100) ---\n")
        f.write(f"Expected : 0,35,70\n")
        f.write(f"Actual   : {actual_main}\n")
        f.write(f"Match    : {actual_main == '0,35,70'}\n\n")
        f.write("--- Boundary example (n=0) ---\n")
        f.write(f"Expected : 0\n")
        f.write(f"Actual   : {actual_boundary}\n")
        f.write(f"Match    : {actual_boundary == '0'}\n\n")
        f.write("--- Mutant test (and -> or) ---\n")
        f.write(f"Mutant output : {mutant_output}\n")
        f.write(f"Correct output: 0,35,70\n")
        f.write(f"Mutant caught : {mutant_output != '0,35,70'}\n")

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
    code = extract_q69_code(MD_FILE)

    pub_expected = "0,35,70"
    boundary_expected = "0"

    if WRONG_MODE:
        pub_expected = "0,35,70,105"
        boundary_expected = "1"

    # Test main example: n=100
    actual_main, rc_main = run_code_with_input(code, 100)
    if rc_main != 0:
        print(f"FAIL: code execution error for n=100 (exit {rc_main})")
        sys.exit(rc_main)

    # Test boundary: n=0
    actual_boundary, rc_boundary = run_code_with_input(code, 0)
    if rc_boundary != 0:
        print(f"FAIL: code execution error for n=0 (exit {rc_boundary})")
        sys.exit(rc_boundary)

    # Run the mutant (and -> or) to verify the test catches it
    mutant_code = code.replace("i%5==0 and i%7==0", "i%5==0 or i%7==0")
    mutant_output, mutant_rc = run_code_with_input(mutant_code, 100)

    if not WRONG_MODE:
        save_evidence(actual_main, actual_boundary, mutant_output)

    # Assert main
    if actual_main != pub_expected:
        print(f"FAIL: expected {pub_expected!r}, got {actual_main!r}")
        sys.exit(1)
    print(f"PASS: n=100 output = {actual_main!r}")

    # Assert boundary
    if actual_boundary != boundary_expected:
        print(f"FAIL: boundary expected {boundary_expected!r}, got {actual_boundary!r}")
        sys.exit(1)
    print(f"PASS: n=0 output = {actual_boundary!r}  (boundary)")

    # Verify mutant produces different output (only in normal mode)
    if not WRONG_MODE:
        if mutant_output == "0,35,70":
            print("FAIL: mutant (and->or) was NOT caught — same output as correct code")
            sys.exit(1)
        print(f"PASS: mutant (and->or) caught — produces {len(mutant_output.split(','))} values vs 3 correct")


if __name__ == "__main__":
    main()
