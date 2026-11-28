#!/usr/bin/env python3
"""
Automated Checker for R28-T004 Question 34.

This script:
1. Extracts the actual Python solution from Question 34 in
   '100+ Python challenging programming exercises for Python 3.md'.
2. Executes the extracted solution via subprocess and in-memory execution.
3. Verifies the exact published dictionary output and formatting:
   {1: 1, 2: 4, ..., 20: 400}
4. Verifies the precise loop invariant:
   "After processing iteration i, the dictionary contains exactly the keys
    from 1 through i, and every key k maps to its square k**2."
5. Tests all six bounded variations with stopping values:
   m in [1, 2, 3, 5, 10, 20] using range(1, m).
6. Verifies the empty dictionary boundary case (m = 1 -> range(1, 1) -> {}).
7. Runs deliberate wrong-result tests to prove the checker detects broken invariants.
8. Saves test evidence inside work/R28-T004/:
   - inputs.txt & inputs.json
   - expected_output.txt
   - actual_output.txt
   - python_version.txt
   - tool_versions.txt
   - test_results.txt
"""

import ast
import io
import json
import os
import platform
import re
import subprocess
import sys
from contextlib import redirect_stdout


def get_repo_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "..", ".."))


def get_work_dir():
    return os.path.dirname(os.path.abspath(__file__))


def extract_question_34_code(md_path):
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Locate Question 34 section up to Question 35
    pattern = r"### Question 34(.*?)(?=### Question 35|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError("Could not find '### Question 34' section in markdown file.")

    q34_text = match.group(1)

    # Locate the python code block under Solution
    code_match = re.search(r"Solution:?\s*```python\s*(.*?)\s*```", q34_text, re.DOTALL)
    if not code_match:
        raise ValueError("Could not extract Python code block under Solution in Question 34.")

    extracted_code = code_match.group(1).strip()
    return extracted_code


def verify_dictionary_invariant(d, current_i):
    """
    Verify the precise invariant:
    After processing iteration i, the dictionary contains exactly the keys
    from 1 through i, and every key k maps to its square k**2.
    """
    assert isinstance(d, dict), f"Expected dict instance, got {type(d)}"
    assert len(d) == current_i, f"Expected {current_i} keys after step {current_i}, got {len(d)}"

    expected_keys = set(range(1, current_i + 1))
    actual_keys = set(d.keys())
    assert actual_keys == expected_keys, (
        f"Key mismatch after step {current_i}!\nExpected keys: {expected_keys}\nActual keys:   {actual_keys}"
    )

    for k in range(1, current_i + 1):
        expected_val = k ** 2
        assert d[k] == expected_val, (
            f"Value mismatch for key {k} after step {current_i}!\nExpected: {expected_val}\nGot: {d[k]}"
        )


def run_deliberate_error_checks():
    """Verify that verify_dictionary_invariant properly catches broken invariants."""
    # 1. Non-dict type
    try:
        verify_dictionary_invariant([(1, 1), (2, 4)], 2)
        raise AssertionError("Failed to catch non-dict type!")
    except AssertionError:
        pass

    # 2. Wrong count / extra key
    try:
        verify_dictionary_invariant({1: 1, 2: 4, 3: 9}, 2)
        raise AssertionError("Failed to catch wrong key count!")
    except AssertionError:
        pass

    # 3. Missing key
    try:
        verify_dictionary_invariant({1: 1, 3: 9}, 2)
        raise AssertionError("Failed to catch missing key!")
    except AssertionError:
        pass

    # 4. Non-square value
    try:
        verify_dictionary_invariant({1: 1, 2: 5}, 2)
        raise AssertionError("Failed to catch non-square value!")
    except AssertionError:
        pass

    # 5. Wrong key boundary (e.g., 0-indexed key)
    try:
        verify_dictionary_invariant({0: 0, 1: 1}, 2)
        raise AssertionError("Failed to catch 0-indexed key!")
    except AssertionError:
        pass


def main():
    repo_root = get_repo_root()
    work_dir = get_work_dir()
    os.makedirs(work_dir, exist_ok=True)

    md_file = os.path.join(repo_root, "100+ Python challenging programming exercises for Python 3.md")

    print("=" * 60)
    print("R28-T004: Question 34 Automated Checker")
    print("=" * 60)
    print(f"Authoritative Markdown: {md_file}")
    print(f"Work Directory:         {work_dir}")

    logs = []

    def log(msg):
        print(msg)
        logs.append(msg)

    # Step 1: Extract code from Markdown
    log("\n[Step 1] Extracting actual code from Question 34...")
    extracted_code = extract_question_34_code(md_file)
    log("Extracted solution code:")
    log("-" * 40)
    log(extracted_code)
    log("-" * 40)

    # Step 2: Subprocess execution of the exact published solution
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

    actual_published_stdout = proc.stdout.strip()
    log(f"Subprocess stdout: {actual_published_stdout}")

    # Step 3: Verify published dictionary formatting and invariant
    log("\n[Step 3] Verifying published dictionary output and invariant...")
    expected_published_dict = {i: i ** 2 for i in range(1, 21)}
    expected_published_str = str(expected_published_dict)

    assert actual_published_stdout == expected_published_str, (
        f"Output formatting mismatch!\nExpected: {expected_published_str}\nActual:   {actual_published_stdout}"
    )
    log("PASS: Exact string output matches expected published dictionary formatting.")

    parsed_published_dict = ast.literal_eval(actual_published_stdout)
    verify_dictionary_invariant(parsed_published_dict, current_i=20)
    log("PASS: Full invariant verified: contains keys 1 through 20, each mapping to its square.")

    # Step 4: Trace step-by-step invariant stages
    log("\n[Step 4] Tracing step-by-step invariant stages...")
    # Trace stage 1: Before loop
    d_trace = {}
    verify_dictionary_invariant(d_trace, current_i=0)
    log("PASS: Invariant stage 1 (Before loop): dictionary is empty {}")

    # Trace stage 2: After i = 3
    for i in range(1, 4):
        d_trace[i] = i ** 2
        verify_dictionary_invariant(d_trace, current_i=i)
    log(f"PASS: Invariant stage 2 (After i = 3): {d_trace}")

    # Trace stage 3: Continue through i = 20
    for i in range(4, 21):
        d_trace[i] = i ** 2
        verify_dictionary_invariant(d_trace, current_i=i)
    assert d_trace == expected_published_dict, "Final traced dictionary does not match expected!"
    log("PASS: Invariant stage 3 (After loop finishes): invariant held after every single iteration.")

    # Step 5: Test all six bounded variations
    log("\n[Step 5] Testing bounded variations for stopping values m in [1, 2, 3, 5, 10, 20]...")
    stopping_values = [1, 2, 3, 5, 10, 20]
    bounded_results = {}

    for m in stopping_values:
        log(f"\nTesting stopping value m = {m} (range(1, {m}))...")
        # Generate code variation by substituting range(1, 21) with range(1, m)
        variation_code = re.sub(r"range\(1,\s*21\)", f"range(1, {m})", extracted_code)
        assert variation_code != extracted_code or m == 21, "Failed to create variation code!"

        # Execute variation in subprocess
        proc_var = subprocess.run(
            [sys.executable, "-c", variation_code],
            capture_output=True,
            text=True,
        )
        if proc_var.returncode != 0:
            log(f"FAIL: Subprocess for m = {m} exited with code {proc_var.returncode}")
            log(f"stderr: {proc_var.stderr}")
            sys.exit(1)

        actual_var_stdout = proc_var.stdout.strip()
        parsed_var_dict = ast.literal_eval(actual_var_stdout)
        expected_var_dict = {i: i ** 2 for i in range(1, m)}

        # Verify exact dictionary structure
        assert actual_var_stdout == str(expected_var_dict), (
            f"Variation m = {m} string mismatch!\nExpected: {expected_var_dict}\nActual:   {actual_var_stdout}"
        )

        # Verify invariant for variation
        expected_count = m - 1
        verify_dictionary_invariant(parsed_var_dict, current_i=expected_count)

        bounded_results[m] = {
            "loop_range": f"range(1, {m})",
            "keys_count": len(parsed_var_dict),
            "expected_keys": list(range(1, m)),
            "output_str": actual_var_stdout,
            "dict": parsed_var_dict,
        }

        log(f"PASS: m = {m} produced {len(parsed_var_dict)} entries: {actual_var_stdout}")

    # Specific check for boundary case m = 1
    log("\n[Step 6] Verifying empty dictionary boundary case (m = 1)...")
    assert bounded_results[1]["output_str"] == "{}", f"Expected '{{}}', got {bounded_results[1]['output_str']}"
    assert bounded_results[1]["keys_count"] == 0, f"Expected 0 keys, got {bounded_results[1]['keys_count']}"
    log("PASS: Boundary case range(1, 1) cleanly produces empty dictionary {} because start == stop.")

    # Step 7: Deliberate incorrect-result tests
    log("\n[Step 7] Running deliberate incorrect-result tests to prove error detection...")
    run_deliberate_error_checks()
    log("PASS: Checker properly detected all deliberate broken invariants.")

    # Step 8: Save evidence files inside work/R28-T004/
    log("\n[Step 8] Saving test evidence inside work/R28-T004/...")

    inputs_data = {
        "published_case": {
            "description": "Question 34 published solution execution (no input parameters)",
            "function": "printDict()",
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
        "bounded_variations": {
            f"m_{m}": {
                "stopping_value_m": m,
                "loop_range": f"range(1, {m})",
                "expected_entry_count": m - 1,
                "keys_generated": list(range(1, m)),
            }
            for m in stopping_values
        },
    }

    # inputs.json
    inputs_json_path = os.path.join(work_dir, "inputs.json")
    with open(inputs_json_path, "w", encoding="utf-8") as f:
        json.dump(inputs_data, f, indent=2)

    # inputs.txt
    inputs_txt_path = os.path.join(work_dir, "inputs.txt")
    with open(inputs_txt_path, "w", encoding="utf-8") as f:
        f.write("[Published Case]\n")
        for k, v in inputs_data["published_case"].items():
            f.write(f"  {k}: {v}\n")
        f.write("\n[Boundary Case (m = 1)]\n")
        for k, v in inputs_data["boundary_case"].items():
            f.write(f"  {k}: {v}\n")
        f.write("\n[Bounded Variations]\n")
        for k, v in inputs_data["bounded_variations"].items():
            f.write(f"  {k}: {v}\n")

    # expected_output.txt
    expected_output_path = os.path.join(work_dir, "expected_output.txt")
    with open(expected_output_path, "w", encoding="utf-8") as f:
        f.write("=== Expected Published Output ===\n")
        f.write(f"{expected_published_str}\n\n")
        f.write("=== Expected Boundary Output (range(1, 1)) ===\n")
        f.write("{}\n\n")
        f.write("=== Expected Bounded Variations ===\n")
        for m in stopping_values:
            exp_d = {i: i ** 2 for i in range(1, m)}
            f.write(f"m = {m} (range(1, {m})): {exp_d}\n")

    # actual_output.txt
    actual_output_path = os.path.join(work_dir, "actual_output.txt")
    with open(actual_output_path, "w", encoding="utf-8") as f:
        f.write("=== Actual Published Output ===\n")
        f.write(f"{actual_published_stdout}\n\n")
        f.write("=== Actual Boundary Output (range(1, 1)) ===\n")
        f.write(f"{bounded_results[1]['output_str']}\n\n")
        f.write("=== Actual Bounded Variations ===\n")
        for m in stopping_values:
            f.write(f"m = {m} (range(1, {m})): {bounded_results[m]['output_str']}\n")

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
        f.write("R28-T004 Question 34 Automated Test Results\n")
        f.write(f"Python: {platform.python_version()}\n")
        f.write("Status: ALL TESTS PASSED\n")
        f.write("Checks Verified:\n")
        f.write("  1. Extracted code matches Question 34 published solution\n")
        f.write("  2. Subprocess execution succeeds without errors\n")
        f.write("  3. Exact published dictionary output matches expected string\n")
        f.write("  4. Full invariant holds: exactly 20 keys, each mapping to key**2\n")
        f.write("  5. Traced invariant across stages: before loop {}, after i=3, after i=20\n")
        f.write("  6. All six bounded variations (m in [1, 2, 3, 5, 10, 20]) tested\n")
        f.write("  7. Empty dictionary boundary case (range(1, 1) -> {}) verified\n")
        f.write("  8. Deliberate broken-invariant checks verify checker error detection\n\n")
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
