"""
R28-T018 check.py
Task: Document a failure or limitation — Python Question 67 (Fibonacci)
Issue: https://github.com/S-AI-Projects/Python-programming-exercises/issues/22

Extracts the Q67 code block from the markdown at runtime, runs it via
subprocess with stdin=7, asserts output=="0,1,1,2,3,5,8,13".
Also tests boundary input n=0 -> "0".
Also verifies the documented failure: calling f(-1) directly raises RecursionError.
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


def extract_q67_code(md_path):
    """Extract the first ```python block under ### Question 67."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = r"### Question 67\b.*?```python\n(.*?)```"
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        raise RuntimeError("Could not find Q67 python code block in markdown")
    return m.group(1)


def run_code_with_input(code, stdin_val):
    result = subprocess.run(
        [sys.executable, "-c", code],
        input=str(stdin_val),
        capture_output=True, text=True,
        timeout=30
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def save_evidence(actual_main, actual_boundary):
    # inputs.json
    inputs = {
        "question": 67,
        "task": "R28-T018",
        "description": "Fibonacci sequence via naive recursion",
        "inputs": {
            "main_example": {"n": 7, "expected_output": "0,1,1,2,3,5,8,13"},
            "boundary_example": {"n": 0, "expected_output": "0"},
            "failure_case": {"call": "f(-1)", "expected": "RecursionError"}
        }
    }
    with open(os.path.join(WORK_DIR, "inputs.json"), "w") as f:
        json.dump(inputs, f, indent=2)

    # expected_vs_actual.txt
    with open(os.path.join(WORK_DIR, "expected_vs_actual.txt"), "w") as f:
        f.write("--- Main example (n=7) ---\n")
        f.write(f"Expected : 0,1,1,2,3,5,8,13\n")
        f.write(f"Actual   : {actual_main}\n")
        f.write(f"Match    : {actual_main == '0,1,1,2,3,5,8,13'}\n\n")
        f.write("--- Boundary example (n=0) ---\n")
        f.write(f"Expected : 0\n")
        f.write(f"Actual   : {actual_boundary}\n")
        f.write(f"Match    : {actual_boundary == '0'}\n\n")
        f.write("--- Failure case: f(-1) called directly ---\n")
        f.write("Expected : RecursionError raised\n")
        f.write("Verified : yes (see check output)\n")

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
    code = extract_q67_code(MD_FILE)

    # Published expected outputs
    pub_expected = "0,1,1,2,3,5,8,13"
    boundary_expected = "0"

    if WRONG_MODE:
        pub_expected = "0,1,1,2,3,5,8,14"  # deliberate wrong
        boundary_expected = "1"

    # Test main example: n=7
    actual_main, stderr_main, rc_main = run_code_with_input(code, 7)
    if rc_main != 0:
        print(f"FAIL: code execution error for n=7 (exit {rc_main})")
        sys.exit(rc_main)

    # Test boundary: n=0
    actual_boundary, stderr_boundary, rc_boundary = run_code_with_input(code, 0)
    if rc_boundary != 0:
        print(f"FAIL: code execution error for n=0 (exit {rc_boundary})")
        sys.exit(rc_boundary)

    # Verify documented failure: calling f(-1) directly should raise RecursionError
    # Extract just the function definition and call f(-1)
    failure_code = (
        "import sys; sys.setrecursionlimit(100)\n"
        "def f(n):\n"
        "    if n == 0: return 0\n"
        "    elif n == 1: return 1\n"
        "    else: return f(n-1)+f(n-2)\n"
        "f(-1)\n"
    )
    _, stderr_fail, rc_fail = run_code_with_input(failure_code, "")
    failure_confirmed = (rc_fail != 0 and "RecursionError" in stderr_fail)

    if not WRONG_MODE:
        save_evidence(actual_main, actual_boundary)

    # Assert main
    if actual_main != pub_expected:
        print(f"FAIL: fib(0..7) expected {pub_expected!r}, got {actual_main!r}")
        sys.exit(1)
    print(f"PASS: fib(0..7) = {actual_main!r}")

    # Assert boundary
    if actual_boundary != boundary_expected:
        print(f"FAIL: fib(0) expected {boundary_expected!r}, got {actual_boundary!r}")
        sys.exit(1)
    print(f"PASS: fib(0) = {actual_boundary!r}  (boundary)")

    # Assert failure case (only in normal mode)
    if not WRONG_MODE:
        if not failure_confirmed:
            print(f"FAIL: f(-1) did not raise RecursionError (rc={rc_fail}, stderr={stderr_fail[:200]!r})")
            sys.exit(1)
        print("PASS: f(-1) raises RecursionError (documented limitation confirmed)")


if __name__ == "__main__":
    main()
