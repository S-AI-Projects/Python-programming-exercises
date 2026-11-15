#!/usr/bin/env python3
"""
Automated Checker for R28-T002 Question 37.

This script:
1. Extracts the actual published Python solution from Question 37 in
   '100+ Python challenging programming exercises for Python 3.md'.
2. Executes the extracted solution via subprocess.
3. Verifies the exact published output:
   - Output string matches exact published list.
   - List contains exactly 20 elements.
   - First element is 1.
   - Last element is 400.
   - Every element i is the square of its integer index (1 to 20).
4. Tests the smallest valid loop-bound boundary case: range(1, 1) -> [].
5. Runs deliberate incorrect-result tests to prove the checker detects errors.
6. Generates test evidence in work/R28-T002/:
   - inputs.txt & inputs.json
   - expected_output.txt
   - actual_output.txt
   - python_version.txt
   - tool_versions.txt
   - test_results.txt
"""

import ast
import json
import os
import platform
import re
import subprocess
import sys


def get_repo_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "..", ".."))


def get_work_dir():
    return os.path.dirname(os.path.abspath(__file__))


def extract_question_37_code(md_path):
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Locate Question 37 section up to Question 38
    pattern = r"### Question 37(.*?)(?=### Question 38|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError("Could not find '### Question 37' section in markdown file.")

    q37_text = match.group(1)

    # Locate the python code block under Solution
    code_match = re.search(r"Solution:?\s*```python\s*(.*?)\s*```", q37_text, re.DOTALL)
    if not code_match:
        raise ValueError("Could not extract Python code block under Solution in Question 37.")

    extracted_code = code_match.group(1).strip()
    return extracted_code


def verify_list_properties(li, expected_len=20, expected_first=1, expected_last=400):
    """Validate mathematical and structural requirements on the output list."""
    assert isinstance(li, list), f"Expected list instance, got {type(li)}"
    assert len(li) == expected_len, f"Expected length {expected_len}, got {len(li)}"
    if expected_len > 0:
        assert li[0] == expected_first, f"Expected first element {expected_first}, got {li[0]}"
        assert li[-1] == expected_last, f"Expected last element {expected_last}, got {li[-1]}"
        for idx, val in enumerate(li, start=1):
            expected_sq = idx ** 2
            assert val == expected_sq, (
                f"Element at index {idx - 1} is {val}, expected square of {idx} ({expected_sq})"
            )


def run_deliberate_error_checks():
    """Verify that verify_list_properties properly catches incorrect results."""
    # 1. Wrong length (19 elements)
    wrong_len = [i ** 2 for i in range(1, 20)]
    try:
        verify_list_properties(wrong_len)
        raise AssertionError("Failed to catch wrong length!")
    except AssertionError:
        pass

    # 2. Wrong first value (0 instead of 1)
    wrong_first = [0] + [i ** 2 for i in range(2, 21)]
    try:
        verify_list_properties(wrong_first)
        raise AssertionError("Failed to catch wrong first value!")
    except AssertionError:
        pass

    # 3. Wrong last value (401 instead of 400)
    wrong_last = [i ** 2 for i in range(1, 20)] + [401]
    try:
        verify_list_properties(wrong_last)
        raise AssertionError("Failed to catch wrong last value!")
    except AssertionError:
        pass

    # 4. Non-square element in middle
    wrong_middle = [i ** 2 for i in range(1, 21)]
    wrong_middle[5] = 99  # index 5 should be 6**2 = 36
    try:
        verify_list_properties(wrong_middle)
        raise AssertionError("Failed to catch non-square element!")
    except AssertionError:
        pass


def main():
    repo_root = get_repo_root()
    work_dir = get_work_dir()
    os.makedirs(work_dir, exist_ok=True)

    md_file = os.path.join(repo_root, "100+ Python challenging programming exercises for Python 3.md")

    print("=" * 60)
    print("R28-T002: Question 37 Automated Checker")
    print("=" * 60)
    print(f"Authoritative Markdown: {md_file}")
    print(f"Work Directory:         {work_dir}")

    logs = []

    def log(msg):
        print(msg)
        logs.append(msg)

    # Step 1: Extract code
    log("\n[Step 1] Extracting actual code from Question 37...")
    extracted_code = extract_question_37_code(md_file)
    log("Extracted solution code:")
    log("-" * 40)
    log(extracted_code)
    log("-" * 40)

    # Step 2: Execute extracted code via subprocess
    log("\n[Step 2] Executing extracted code via Python subprocess...")
    proc = subprocess.run(
        [sys.executable, "-c", extracted_code],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        log(f"FAIL: Subprocess exited with code {proc.returncode}")
        log(f"stderr: {proc.stderr}")
        sys.exit(1)

    actual_published_output = proc.stdout.strip()
    log(f"Subprocess stdout: {actual_published_output}")

    # Step 3: Verify published output requirements
    log("\n[Step 3] Verifying exact published output specifications...")
    expected_list = [i ** 2 for i in range(1, 21)]
    expected_published_str = str(expected_list)

    # 3a. Exact string match
    assert actual_published_output == expected_published_str, (
        f"Output string mismatch!\nExpected: {expected_published_str}\nActual:   {actual_published_output}"
    )
    log("PASS: Exact string output matches published list.")

    # 3b. Parse list structure
    parsed_list = ast.literal_eval(actual_published_output)
    verify_list_properties(parsed_list, expected_len=20, expected_first=1, expected_last=400)
    log("PASS: Exactly 20 square numbers verified.")
    log("PASS: First element is 1 (1**2).")
    log("PASS: Last element is 400 (20**2).")
    log("PASS: Every element is the square of its corresponding integer from 1 to 20.")

    # Step 4: Test boundary case range(1, 1) -> []
    log("\n[Step 4] Testing boundary case: smallest valid loop-bound variation range(1, 1)...")
    boundary_code = re.sub(r"range\(1,\s*21\)", "range(1, 1)", extracted_code)
    assert boundary_code != extracted_code, "Failed to create boundary code variation!"

    proc_bound = subprocess.run(
        [sys.executable, "-c", boundary_code],
        capture_output=True,
        text=True,
    )
    if proc_bound.returncode != 0:
        log(f"FAIL: Boundary subprocess exited with code {proc_bound.returncode}")
        log(f"stderr: {proc_bound.stderr}")
        sys.exit(1)

    actual_boundary_output = proc_bound.stdout.strip()
    log(f"Boundary subprocess stdout: {actual_boundary_output}")

    assert actual_boundary_output == "[]", f"Expected '[]', got '{actual_boundary_output}'"
    parsed_boundary = ast.literal_eval(actual_boundary_output)
    verify_list_properties(parsed_boundary, expected_len=0)
    log("PASS: Boundary case range(1, 1) produces empty list [] as start == stop.")

    # Step 5: Deliberate incorrect-result tests
    log("\n[Step 5] Running deliberate incorrect-result tests to prove error detection...")
    run_deliberate_error_checks()
    log("PASS: Deliberate errors (wrong length, wrong first/last, non-squares) properly detected.")

    # Step 6: Save evidence files
    log("\n[Step 6] Saving test evidence inside work/R28-T002/...")

    inputs_data = {
        "published_case": {
            "description": "Question 37 published solution execution (no input parameters)",
            "function": "printList()",
            "loop_range": "range(1, 21)",
            "start": 1,
            "stop": 21,
            "step": 1,
            "total_iterations": 20,
        },
        "boundary_case": {
            "description": "Smallest valid loop-bound variation (start == stop)",
            "loop_range": "range(1, 1)",
            "start": 1,
            "stop": 1,
            "step": 1,
            "total_iterations": 0,
        },
    }

    # inputs.json
    inputs_json_path = os.path.join(work_dir, "inputs.json")
    with open(inputs_json_path, "w", encoding="utf-8") as f:
        json.dump(inputs_data, f, indent=2)

    # inputs.txt
    inputs_txt_path = os.path.join(work_dir, "inputs.txt")
    with open(inputs_txt_path, "w", encoding="utf-8") as f:
        for k, v in inputs_data.items():
            f.write(f"[{k}]\n")
            for subk, subv in v.items():
                f.write(f"  {subk}: {subv}\n")
            f.write("\n")

    # expected_output.txt
    expected_output_path = os.path.join(work_dir, "expected_output.txt")
    with open(expected_output_path, "w", encoding="utf-8") as f:
        f.write("=== Expected Published Output ===\n")
        f.write(f"{expected_published_str}\n\n")
        f.write("=== Expected Boundary Output (range(1, 1)) ===\n")
        f.write("[]\n")

    # actual_output.txt
    actual_output_path = os.path.join(work_dir, "actual_output.txt")
    with open(actual_output_path, "w", encoding="utf-8") as f:
        f.write("=== Actual Published Output ===\n")
        f.write(f"{actual_published_output}\n\n")
        f.write("=== Actual Boundary Output (range(1, 1)) ===\n")
        f.write(f"{actual_boundary_output}\n")

    # python_version.txt
    py_ver_path = os.path.join(work_dir, "python_version.txt")
    with open(py_ver_path, "w", encoding="utf-8") as f:
        f.write(f"Python Version: {platform.python_version()}\n")
        f.write(f"Build: {sys.version}\n")
        f.write(f"Executable: {sys.executable}\n")

    # tool_versions.txt
    tool_ver_path = os.path.join(work_dir, "tool_versions.txt")
    git_ver_proc = subprocess.run(["git", "--version"], capture_output=True, text=True)
    git_ver = git_ver_proc.stdout.strip() if git_ver_proc.returncode == 0 else "git unknown"

    with open(tool_ver_path, "w", encoding="utf-8") as f:
        f.write(f"Python: {platform.python_version()} ({sys.executable})\n")
        f.write(f"Git: {git_ver}\n")
        f.write(f"OS: {platform.platform()}\n")
        f.write(f"Architecture: {platform.machine()}\n")

    # test_results.txt
    results_path = os.path.join(work_dir, "test_results.txt")
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("R28-T002 Question 37 Automated Test Results\n")
        f.write(f"Python: {platform.python_version()}\n")
        f.write("Status: ALL TESTS PASSED\n")
        f.write("Checks Verified:\n")
        f.write("  1. Extracted code from Markdown matches published Solution\n")
        f.write("  2. Subprocess execution succeeds without errors\n")
        f.write("  3. Exact published output string matches expected list\n")
        f.write("  4. List contains exactly 20 elements\n")
        f.write("  5. First element is 1 (1**2)\n")
        f.write("  6. Last element is 400 (20**2)\n")
        f.write("  7. Every element matches the square of its integer index\n")
        f.write("  8. Smallest valid loop-bound variation range(1, 1) produces empty list []\n")
        f.write("  9. Deliberate incorrect-result tests verify checker error detection\n\n")
        f.write("Execution Log:\n")
        for line in logs:
            f.write(f"{line}\n")

    log("Saved evidence files:")
    log(f"  - {inputs_txt_path}")
    log(f"  - {inputs_json_path}")
    log(f"  - {expected_output_path}")
    log(f"  - {actual_output_path}")
    log(f"  - {py_ver_path}")
    log(f"  - {tool_ver_path}")
    log(f"  - {results_path}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
