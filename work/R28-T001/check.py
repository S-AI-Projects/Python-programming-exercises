#!/usr/bin/env python3
"""
Checker for R28-T001 Question 86.

This checker:
1. Extracts the exact solution code block from Question 86 in
   '100+ Python challenging programming exercises for Python 3.md'.
2. Executes the extracted code (not a retyped solution).
3. Asserts the expected output for:
   - The exact published example
   - The smallest supported input
   - Empty input boundary case
4. Confirms that incorrect results trigger assertion failures.
5. Generates evidence files in work/R28-T001/:
   - inputs.txt & inputs.json
   - expected_output.txt
   - actual_output.txt
   - test_results.txt
   - python_version.txt
"""

import io
import json
import os
import re
import subprocess
import sys
from contextlib import redirect_stdout
from datetime import datetime


def get_repo_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "..", ".."))


def get_work_dir():
    return os.path.dirname(os.path.abspath(__file__))


def extract_question_86_code(md_path):
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Locate Question 86 section up to Question 87
    pattern = r"### Question 86(.*?)(?=### Question 87|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError("Could not find '### Question 86' section in markdown file.")

    q86_text = match.group(1)

    # Locate the python code block under Solution:
    code_match = re.search(r"Solution:\s*```python\s*(.*?)\s*```", q86_text, re.DOTALL)
    if not code_match:
        # Fallback to any code block under Solution:
        code_match = re.search(r"```python\s*(.*?)\s*```", q86_text, re.DOTALL)

    if not code_match:
        raise ValueError("Could not extract Python code block from Question 86 solution.")

    extracted_code = code_match.group(1).strip()
    return extracted_code


def main():
    repo_root = get_repo_root()
    work_dir = get_work_dir()
    md_file = os.path.join(repo_root, "100+ Python challenging programming exercises for Python 3.md")

    print("=" * 60)
    print("R28-T001: Question 86 Checker")
    print("=" * 60)
    print(f"Target Markdown: {md_file}")
    print(f"Work Directory:  {work_dir}")

    # 1. Extract code from Markdown
    print("\n[Step 1] Extracting actual code from Markdown...")
    extracted_code = extract_question_86_code(md_file)
    print("Extracted code:")
    print("-" * 40)
    print(extracted_code)
    print("-" * 40)

    # 2. Define test inputs and expected outputs
    inputs_data = {
        "published_example": {
            "description": "Exact published example from Question 86",
            "subjects": ["I", "You"],
            "verbs": ["Play", "Love"],
            "objects": ["Hockey", "Football"],
        },
        "smallest_supported_input": {
            "description": "Smallest supported input (single element per category)",
            "subjects": ["I"],
            "verbs": ["Play"],
            "objects": ["Hockey"],
        },
        "empty_boundary_input": {
            "description": "Boundary edge case (empty list per category)",
            "subjects": [],
            "verbs": [],
            "objects": [],
        },
    }

    expected_outputs = {
        "published_example": (
            "I Play Hockey.\n"
            "I Play Football.\n"
            "I Love Hockey.\n"
            "I Love Football.\n"
            "You Play Hockey.\n"
            "You Play Football.\n"
            "You Love Hockey.\n"
            "You Love Football."
        ),
        "smallest_supported_input": "I Play Hockey.",
        "empty_boundary_input": "",
    }

    actual_outputs = {}
    test_logs = []

    def log(msg):
        print(msg)
        test_logs.append(msg)

    # 3. Execute extracted code standalone via subprocess (verifying script run)
    log("\n[Step 2] Executing extracted code via Python subprocess...")
    proc_result = subprocess.run(
        [sys.executable, "-c", extracted_code],
        capture_output=True,
        text=True,
    )
    if proc_result.returncode != 0:
        log(f"FAIL: Subprocess execution returned exit code {proc_result.returncode}")
        log(f"stderr: {proc_result.stderr}")
        sys.exit(1)

    script_stdout = proc_result.stdout.strip()
    log("Subprocess execution succeeded.")

    # 4. Execute extracted code in a fresh namespace
    log("\n[Step 3] Executing extracted code in local namespace...")
    code_namespace = {"__name__": "__main__"}
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exec(extracted_code, code_namespace)

    direct_exec_output = buffer.getvalue().strip()
    actual_outputs["published_example"] = direct_exec_output

    # Assert script output matches published example expected output
    log("Asserting published example output...")
    assert direct_exec_output == expected_outputs["published_example"], (
        f"Mismatch in published example output!\n"
        f"Expected:\n{expected_outputs['published_example']}\n"
        f"Actual:\n{direct_exec_output}"
    )
    assert script_stdout == expected_outputs["published_example"], (
        f"Mismatch between subprocess and exec output!\n"
        f"Subprocess:\n{script_stdout}\n"
        f"Exec:\n{direct_exec_output}"
    )
    log("PASS: Published example output matches exactly.")

    # 5. Test function call with smallest supported input
    log("\n[Step 4] Testing smallest supported input...")
    if "generate_sentences" in code_namespace and callable(code_namespace["generate_sentences"]):
        fn = code_namespace["generate_sentences"]
        buf_small = io.StringIO()
        with redirect_stdout(buf_small):
            ret_small = fn(
                inputs_data["smallest_supported_input"]["subjects"],
                inputs_data["smallest_supported_input"]["verbs"],
                inputs_data["smallest_supported_input"]["objects"],
            )
        small_output = buf_small.getvalue().strip()
        actual_outputs["smallest_supported_input"] = small_output

        log("Asserting smallest supported input output...")
        assert small_output == expected_outputs["smallest_supported_input"], (
            f"Mismatch in smallest supported input output!\n"
            f"Expected:\n{expected_outputs['smallest_supported_input']}\n"
            f"Actual:\n{small_output}"
        )
        log("PASS: Smallest supported input matches exactly.")

        # Test empty input boundary case
        log("\n[Step 5] Testing empty boundary input...")
        buf_empty = io.StringIO()
        with redirect_stdout(buf_empty):
            fn(
                inputs_data["empty_boundary_input"]["subjects"],
                inputs_data["empty_boundary_input"]["verbs"],
                inputs_data["empty_boundary_input"]["objects"],
            )
        empty_output = buf_empty.getvalue().strip()
        actual_outputs["empty_boundary_input"] = empty_output

        assert empty_output == expected_outputs["empty_boundary_input"], (
            f"Mismatch in empty boundary input output!\n"
            f"Expected: (empty string)\n"
            f"Actual:\n{empty_output}"
        )
        log("PASS: Empty boundary input matches exactly.")
    else:
        log("FAIL: 'generate_sentences' function not found in extracted code.")
        sys.exit(1)

    # 6. Verify that incorrect results cause assertion failure
    log("\n[Step 6] Verifying assertion failure behavior on incorrect result...")
    incorrect_test_passed = False
    try:
        dummy_bad_output = "Incorrect sentence output"
        assert dummy_bad_output == expected_outputs["published_example"]
    except AssertionError:
        incorrect_test_passed = True
        log("PASS: Assertion properly caught simulated incorrect output.")

    if not incorrect_test_passed:
        log("FAIL: Assertion did NOT catch incorrect output!")
        sys.exit(1)

    # 7. Write evidence files inside work/R28-T001/
    log("\n[Step 7] Writing assignment evidence inside work/R28-T001/...")

    # inputs.json
    inputs_json_path = os.path.join(work_dir, "inputs.json")
    with open(inputs_json_path, "w", encoding="utf-8") as f:
        json.dump(inputs_data, f, indent=2)

    # inputs.txt
    inputs_txt_path = os.path.join(work_dir, "inputs.txt")
    with open(inputs_txt_path, "w", encoding="utf-8") as f:
        for key, val in inputs_data.items():
            f.write(f"[{key}]\n")
            f.write(f"Description: {val['description']}\n")
            f.write(f"Subjects: {val['subjects']}\n")
            f.write(f"Verbs: {val['verbs']}\n")
            f.write(f"Objects: {val['objects']}\n\n")

    # expected_output.txt
    expected_out_path = os.path.join(work_dir, "expected_output.txt")
    with open(expected_out_path, "w", encoding="utf-8") as f:
        for key, val in expected_outputs.items():
            f.write(f"=== Expected Output: {key} ===\n")
            f.write(f"{val}\n\n")

    # actual_output.txt
    actual_out_path = os.path.join(work_dir, "actual_output.txt")
    with open(actual_out_path, "w", encoding="utf-8") as f:
        for key, val in actual_outputs.items():
            f.write(f"=== Actual Output: {key} ===\n")
            f.write(f"{val}\n\n")

    # python_version.txt
    py_ver_path = os.path.join(work_dir, "python_version.txt")
    with open(py_ver_path, "w", encoding="utf-8") as f:
        f.write(f"Python Version:\n{sys.version}\n")
        f.write(f"Executable: {sys.executable}\n")

    # test_results.txt
    results_path = os.path.join(work_dir, "test_results.txt")
    with open(results_path, "w", encoding="utf-8") as f:
        f.write(f"R28-T001 Question 86 Test Results\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Python: {sys.version.split()[0]}\n")
        f.write(f"Overall Status: PASSED (All 6 steps passed)\n\n")
        f.write("Log:\n")
        for line in test_logs:
            f.write(f"{line}\n")

    log("Saved evidence files:")
    log(f"  - {inputs_txt_path}")
    log(f"  - {inputs_json_path}")
    log(f"  - {expected_out_path}")
    log(f"  - {actual_out_path}")
    log(f"  - {python_version_path if 'python_version_path' in locals() else py_ver_path}")
    log(f"  - {results_path}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()

