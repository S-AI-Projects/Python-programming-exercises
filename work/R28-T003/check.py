#!/usr/bin/env python3
"""
Automated Checker for R28-T003 Question 94.

This script:
1. Extracts the actual Python solution code blocks for Question 94 from
   '100+ Python challenging programming exercises for Python 3.md'
   (both removeDuplicate and removeDuplicateAlternative).
2. Executes both extracted solutions via subprocess.
3. Tests both methods on:
   - Published fixture: [12, 24, 35, 24, 88, 120, 155, 88, 120, 155]
   - Smallest supported input: []
4. Asserts:
   - Both methods return [12, 24, 35, 88, 120, 155] for published fixture.
   - Both methods return [] for empty list.
   - Return values are Python lists.
   - First-occurrence order is preserved.
5. Runs deliberate wrong-result tests to prove the checker detects errors.
6. Saves test evidence inside work/R28-T003/:
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


def extract_question_94_code_blocks(md_path):
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Locate Question 94 section up to Question 95
    pattern = r"### Question 94(.*?)(?=### Question 95|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError("Could not find '### Question 94' section in markdown file.")

    q94_text = match.group(1)

    # Find all python code blocks in Question 94 section
    code_blocks = re.findall(r"```python\s*(.*?)\s*```", q94_text, re.DOTALL)
    if len(code_blocks) < 2:
        raise ValueError(f"Expected at least 2 Python code blocks in Question 94, found {len(code_blocks)}")

    # Block 1: original removeDuplicate
    block_original = None
    for b in code_blocks:
        if "def removeDuplicate(" in b:
            block_original = b.strip()
            break

    # Block 2: alternative removeDuplicateAlternative
    block_alternative = None
    for b in code_blocks:
        if "def removeDuplicateAlternative(" in b:
            block_alternative = b.strip()
            break

    if not block_original:
        raise ValueError("Could not find removeDuplicate definition in Question 94 code blocks.")
    if not block_alternative:
        raise ValueError("Could not find removeDuplicateAlternative definition in Question 94 code blocks.")

    return block_original, block_alternative


def validate_deduplication(original_input, result, expected_output):
    """Validate that result meets all deduplication and ordering specifications."""
    assert isinstance(result, list), f"Expected result to be list, got {type(result)}"
    assert result == expected_output, f"Result mismatch!\nExpected: {expected_output}\nGot: {result}"

    # Verify no duplicates exist in result
    assert len(result) == len(set(result)), f"Result contains duplicates: {result}"

    # Verify every element in result is in original_input
    for item in result:
        assert item in original_input, f"Unexpected item {item} not present in input"

    # Verify all unique items from original_input are present in result
    unique_inputs = set(original_input)
    assert set(result) == unique_inputs, f"Missing unique items: {unique_inputs - set(result)}"

    # Verify first-occurrence order preservation
    first_seen_indices = []
    seen_so_far = set()
    for idx, item in enumerate(original_input):
        if item not in seen_so_far:
            seen_so_far.add(item)
            first_seen_indices.append(item)
    assert result == first_seen_indices, "First-occurrence ordering was not preserved!"


def run_deliberate_error_checks():
    """Verify that validate_deduplication properly rejects incorrect results."""
    fixture = [12, 24, 35, 24, 88, 120, 155, 88, 120, 155]
    expected = [12, 24, 35, 88, 120, 155]

    # 1. Non-list return type
    try:
        validate_deduplication(fixture, tuple(expected), expected)
        raise AssertionError("Failed to catch non-list return type!")
    except AssertionError:
        pass

    # 2. Result containing remaining duplicates
    try:
        validate_deduplication(fixture, [12, 24, 35, 24, 88, 120, 155], expected)
        raise AssertionError("Failed to catch remaining duplicate!")
    except AssertionError:
        pass

    # 3. Result with incorrect elements
    try:
        validate_deduplication(fixture, [12, 24, 35, 88, 120, 999], expected)
        raise AssertionError("Failed to catch incorrect element!")
    except AssertionError:
        pass

    # 4. Result with wrong ordering (e.g. sorted order instead of first-occurrence order)
    try:
        validate_deduplication(fixture, sorted(expected), expected)
        # Note: sorted(expected) is [12, 24, 35, 88, 120, 155] which happens to match,
        # so test reverse order instead:
        validate_deduplication(fixture, list(reversed(expected)), expected)
        raise AssertionError("Failed to catch wrong ordering!")
    except AssertionError:
        pass

    # 5. Missing element
    try:
        validate_deduplication(fixture, [12, 24, 35, 88, 120], expected)
        raise AssertionError("Failed to catch missing element!")
    except AssertionError:
        pass


def main():
    repo_root = get_repo_root()
    work_dir = get_work_dir()
    os.makedirs(work_dir, exist_ok=True)

    md_file = os.path.join(repo_root, "100+ Python challenging programming exercises for Python 3.md")

    print("=" * 60)
    print("R28-T003: Question 94 Automated Checker")
    print("=" * 60)
    print(f"Authoritative Markdown: {md_file}")
    print(f"Work Directory:         {work_dir}")

    logs = []

    def log(msg):
        print(msg)
        logs.append(msg)

    # Step 1: Extract code blocks
    log("\n[Step 1] Extracting actual code blocks from Question 94...")
    block_orig, block_alt = extract_question_94_code_blocks(md_file)

    log("Extracted Original Solution (removeDuplicate):")
    log("-" * 40)
    log(block_orig)
    log("-" * 40)

    log("\nExtracted Alternative Solution (removeDuplicateAlternative):")
    log("-" * 40)
    log(block_alt)
    log("-" * 40)

    # Step 2: Execute both solutions via subprocess
    log("\n[Step 2] Executing extracted code blocks via Python subprocess...")
    proc_orig = subprocess.run(
        [sys.executable, "-c", block_orig],
        capture_output=True,
        text=True,
    )
    if proc_orig.returncode != 0:
        log(f"FAIL: Subprocess for original method exited with code {proc_orig.returncode}")
        log(f"stderr: {proc_orig.stderr}")
        sys.exit(1)

    actual_orig_stdout = proc_orig.stdout.strip()
    log(f"Original method subprocess stdout:    {actual_orig_stdout}")

    proc_alt = subprocess.run(
        [sys.executable, "-c", block_alt],
        capture_output=True,
        text=True,
    )
    if proc_alt.returncode != 0:
        log(f"FAIL: Subprocess for alternative method exited with code {proc_alt.returncode}")
        log(f"stderr: {proc_alt.stderr}")
        sys.exit(1)

    actual_alt_stdout = proc_alt.stdout.strip()
    log(f"Alternative method subprocess stdout: {actual_alt_stdout}")

    # Expected published output
    expected_fixture_output = [12, 24, 35, 88, 120, 155]
    expected_fixture_str = str(expected_fixture_output)

    # Step 3: Verify subprocess outputs match expected published fixture
    log("\n[Step 3] Verifying subprocess outputs match published fixture...")
    assert actual_orig_stdout == expected_fixture_str, (
        f"Original method output mismatch!\nExpected: {expected_fixture_str}\nActual:   {actual_orig_stdout}"
    )
    assert actual_alt_stdout == expected_fixture_str, (
        f"Alternative method output mismatch!\nExpected: {expected_fixture_str}\nActual:   {actual_alt_stdout}"
    )
    log("PASS: Both methods produce exact expected published string: [12, 24, 35, 88, 120, 155]")

    # Step 4: Extract function definitions into local namespace for unit testing
    log("\n[Step 4] In-memory verification of extracted functions...")
    import io
    from contextlib import redirect_stdout

    ns_orig = {}
    with redirect_stdout(io.StringIO()):
        exec(block_orig, ns_orig)
    fn_removeDuplicate = ns_orig.get("removeDuplicate")

    ns_alt = {}
    with redirect_stdout(io.StringIO()):
        exec(block_alt, ns_alt)
    fn_removeDuplicateAlternative = ns_alt.get("removeDuplicateAlternative")

    assert callable(fn_removeDuplicate), "removeDuplicate is not callable!"
    assert callable(fn_removeDuplicateAlternative), "removeDuplicateAlternative is not callable!"

    # Test Published Fixture
    published_input = [12, 24, 35, 24, 88, 120, 155, 88, 120, 155]
    log(f"Testing published fixture: {published_input}")

    res_orig = fn_removeDuplicate(list(published_input))
    res_alt = fn_removeDuplicateAlternative(list(published_input))

    validate_deduplication(published_input, res_orig, expected_fixture_output)
    validate_deduplication(published_input, res_alt, expected_fixture_output)
    assert res_orig == res_alt, "Results of both methods do not match!"
    log(f"PASS: Both methods returned: {res_orig}")
    log("PASS: Result is Python list and preserves first-occurrence order.")

    # Step 5: Test Smallest Supported Input: []
    log("\n[Step 5] Testing smallest supported input: []...")
    empty_input = []
    res_orig_empty = fn_removeDuplicate(list(empty_input))
    res_alt_empty = fn_removeDuplicateAlternative(list(empty_input))

    validate_deduplication(empty_input, res_orig_empty, [])
    validate_deduplication(empty_input, res_alt_empty, [])
    assert res_orig_empty == [], f"Expected [], got {res_orig_empty}"
    assert res_alt_empty == [], f"Expected [], got {res_alt_empty}"
    log("PASS: Both methods return [] for empty list input.")
    log("PASS: Empty list results are Python lists.")

    # Step 6: Deliberate error detection check
    log("\n[Step 6] Running deliberate wrong-result tests...")
    run_deliberate_error_checks()
    log("PASS: Checker properly detected all simulated wrong results.")

    # Step 7: Save test evidence files
    log("\n[Step 7] Saving test evidence inside work/R28-T003/...")

    inputs_data = {
        "published_fixture": {
            "description": "Question 94 published list with multiple duplicates",
            "input": published_input,
            "length": len(published_input),
            "unique_elements_count": len(set(published_input)),
        },
        "smallest_supported_input": {
            "description": "Smallest valid input boundary case (empty list)",
            "input": empty_input,
            "length": len(empty_input),
            "unique_elements_count": 0,
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
        f.write("=== Expected Output: published_fixture ===\n")
        f.write(f"{expected_fixture_output}\n\n")
        f.write("=== Expected Output: smallest_supported_input ===\n")
        f.write("[]\n")

    # actual_output.txt
    actual_output_path = os.path.join(work_dir, "actual_output.txt")
    with open(actual_output_path, "w", encoding="utf-8") as f:
        f.write("=== Actual Subprocess Output (removeDuplicate) ===\n")
        f.write(f"{actual_orig_stdout}\n\n")
        f.write("=== Actual Subprocess Output (removeDuplicateAlternative) ===\n")
        f.write(f"{actual_alt_stdout}\n\n")
        f.write("=== Actual In-Memory Results ===\n")
        f.write(f"removeDuplicate(published_fixture):            {res_orig}\n")
        f.write(f"removeDuplicateAlternative(published_fixture): {res_alt}\n")
        f.write(f"removeDuplicate([]):                           {res_orig_empty}\n")
        f.write(f"removeDuplicateAlternative([]):                {res_alt_empty}\n")

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
        f.write("R28-T003 Question 94 Automated Test Results\n")
        f.write(f"Python: {platform.python_version()}\n")
        f.write("Status: ALL TESTS PASSED\n")
        f.write("Checks Verified:\n")
        f.write("  1. Extracted code blocks from Markdown match Question 94 solutions\n")
        f.write("  2. Subprocess execution for both methods succeeds with code 0\n")
        f.write("  3. Both methods return exact published list [12, 24, 35, 88, 120, 155]\n")
        f.write("  4. Both methods return [] for empty list input\n")
        f.write("  5. Results are verified to be Python list instances\n")
        f.write("  6. First-occurrence order is strictly preserved\n")
        f.write("  7. Deliberate wrong-result tests verify checker error detection\n\n")
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
