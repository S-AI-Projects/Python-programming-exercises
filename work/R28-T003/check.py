#!/usr/bin/env python3
"""Automated checker for Question 94 (Issue R28-T003).

This script:
1. Reads the authoritative Markdown file '100+ Python challenging programming exercises for Python 3.md'.
2. Extracts Question 94's original and alternative solution code dynamically (no retyping).
3. Executes the extracted code through subprocess.
4. Tests both methods against the published fixture:
   [12, 24, 35, 24, 88, 120, 155, 88, 120, 155]
   Asserts both produce: [12, 24, 35, 88, 120, 155].
5. Tests both methods against the smallest supported input:
   []
   Asserts both return [].
6. Asserts that the return values are lists and strictly preserve first-occurrence order.
7. Executes deliberate wrong-result tests proving the checker detects incorrect outputs.
8. Propagates subprocess failures with non-zero exit codes.
9. Updates evidence files in work/R28-T003/.
"""

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def find_markdown_file() -> Path:
    current_dir = Path(__file__).resolve().parent
    repo_root = current_dir.parent.parent
    candidate_paths = [
        repo_root / "100+ Python challenging programming exercises for Python 3.md",
        Path.cwd() / "100+ Python challenging programming exercises for Python 3.md",
        Path("100+ Python challenging programming exercises for Python 3.md"),
    ]
    for p in candidate_paths:
        if p.is_file():
            return p.resolve()
    raise FileNotFoundError(
        "Could not find '100+ Python challenging programming exercises for Python 3.md'"
    )


def extract_question_94_code_blocks(markdown_text: str):
    q94_match = re.search(
        r"### Question 94\b(.*?)(?=### Question 95\b|\Z)",
        markdown_text,
        re.DOTALL,
    )
    if not q94_match:
        raise AssertionError("Section '### Question 94' not found in Markdown article")

    q94_body = q94_match.group(1)

    code_blocks = re.findall(r"```(?:python)?\s*\n(.*?)\n```", q94_body, re.DOTALL)
    if len(code_blocks) < 2:
        raise AssertionError(
            f"Expected at least 2 code blocks in Question 94 (original and alternative), found {len(code_blocks)}"
        )

    original_code = None
    alt_code = None

    for block in code_blocks:
        if "def removeDuplicate(" in block or "def removeDuplicate (" in block:
            original_code = block
        elif "def removeDuplicateAlternative(" in block:
            alt_code = block

    if not original_code:
        raise AssertionError("Could not find original removeDuplicate code block in Question 94")
    if not alt_code:
        raise AssertionError("Could not find removeDuplicateAlternative code block in Question 94")

    # Also extract published expected output if available in markdown
    expected_match = re.search(
        r"output of the program should be:\s*\n\s*(.*?)(?=\n\s*Hints:|\n\s*Solution:?|\Z)",
        q94_body,
        re.DOTALL | re.IGNORECASE,
    )
    published_expected = expected_match.group(1).strip() if expected_match else "[12, 24, 35, 88, 120, 155]"

    return original_code, alt_code, published_expected


def extract_function_definition(code_str: str, func_name: str) -> str:
    """Extracts only the function definition for func_name from a code snippet."""
    tree = ast.parse(code_str)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            lines = code_str.splitlines()
            start = node.lineno - 1
            end = node.end_lineno
            return "\n".join(lines[start:end])
    raise AssertionError(f"Function {func_name} definition not found in extracted code block")


def execute_subprocess(code: str) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        sys.stderr.write(
            f"Subprocess failed with exit code {proc.returncode}:\nSTDERR:\n{proc.stderr}\n"
        )
        sys.exit(proc.returncode)
    return proc


def assert_is_list_and_preserves_order(original_input: list, result: list, test_name: str):
    if not isinstance(result, list):
        raise AssertionError(f"{test_name}: Expected result to be a list, got {type(result).__name__}")

    # Check that all elements in result come from original_input
    for x in result:
        if x not in original_input:
            raise AssertionError(f"{test_name}: Element {x} in result was not in original input")

    # Check for no duplicates in result
    if len(result) != len(set(result)):
        raise AssertionError(f"{test_name}: Result contains duplicates: {result}")

    # Check preservation of first-occurrence order
    # Each element's first index in original_input must be strictly increasing
    first_indices = [original_input.index(x) for x in result]
    if first_indices != sorted(first_indices):
        raise AssertionError(
            f"{test_name}: First-occurrence order not preserved. First indices: {first_indices}"
        )


def validate_result_against_expected(actual, expected, test_name: str):
    if not isinstance(actual, list):
        raise AssertionError(f"{test_name}: Expected list type, got {type(actual).__name__}")
    if actual != expected:
        raise AssertionError(f"{test_name}: Output mismatch.\nExpected: {expected}\nActual:   {actual}")


def run_deliberate_wrong_result_test(faulty_output, expected, original_input, test_name: str):
    try:
        validate_result_against_expected(faulty_output, expected, test_name)
        assert_is_list_and_preserves_order(original_input, faulty_output, test_name)
    except AssertionError as e:
        print(f"PASS: Deliberate wrong-result test ({test_name}) correctly caught error: {e}")
        return True
    else:
        raise AssertionError(
            f"FAIL: Checker failed to detect deliberate wrong result for ({test_name})!"
        )


def main():
    evidence_dir = Path(__file__).resolve().parent
    results_lines = []

    print("=== Running Automated Checker for Question 94 (Issue R28-T003) ===")
    results_lines.append("=== Automated Checker Results for Question 94 (Issue R28-T003) ===")

    # 1. Locate markdown source
    md_path = find_markdown_file()
    print(f"Reading Markdown article from: {md_path}")
    md_content = md_path.read_text(encoding="utf-8")

    # 2. Extract code blocks from Question 94
    original_code, alt_code, published_expected_str = extract_question_94_code_blocks(md_content)
    print("Successfully extracted Question 94 original and alternative code blocks.")
    results_lines.append("Code Extraction: SUCCESS")

    # 3. Extract pure function definitions dynamically
    orig_func_def = extract_function_definition(original_code, "removeDuplicate")
    alt_func_def = extract_function_definition(alt_code, "removeDuplicateAlternative")
    print("Dynamically extracted function definitions without retyping.")

    # 4. Execute standalone original code via subprocess
    proc_orig = execute_subprocess(original_code)
    actual_orig_stdout = proc_orig.stdout.strip()
    print(f"Original code subprocess execution: SUCCESS. Output: {actual_orig_stdout}")
    results_lines.append(f"Original Code Subprocess Output: {actual_orig_stdout}")

    # 5. Execute standalone alternative code via subprocess
    proc_alt = execute_subprocess(alt_code)
    actual_alt_stdout = proc_alt.stdout.strip()
    print(f"Alternative code subprocess execution: SUCCESS. Output: {actual_alt_stdout}")
    results_lines.append(f"Alternative Code Subprocess Output: {actual_alt_stdout}")

    # 6. Build and execute test runner via subprocess
    published_fixture = [12, 24, 35, 24, 88, 120, 155, 88, 120, 155]
    smallest_fixture = []
    expected_published = [12, 24, 35, 88, 120, 155]
    expected_smallest = []

    test_harness_code = f"""
{orig_func_def}

{alt_func_def}

import json

pub = {published_fixture}
small = {smallest_fixture}

res = {{
    "orig_pub": removeDuplicate(list(pub)),
    "alt_pub": removeDuplicateAlternative(list(pub)),
    "orig_small": removeDuplicate(list(small)),
    "alt_small": removeDuplicateAlternative(list(small)),
}}
print(json.dumps(res))
"""

    runner_proc = execute_subprocess(test_harness_code)
    test_data = json.loads(runner_proc.stdout.strip())

    orig_pub = test_data["orig_pub"]
    alt_pub = test_data["alt_pub"]
    orig_small = test_data["orig_small"]
    alt_small = test_data["alt_small"]

    # 7. Assert both methods produce expected output on published fixture
    validate_result_against_expected(orig_pub, expected_published, "removeDuplicate(published)")
    validate_result_against_expected(alt_pub, expected_published, "removeDuplicateAlternative(published)")
    print("PASS: Both methods produced exact published output [12, 24, 35, 88, 120, 155].")
    results_lines.append("Published Fixture Assertion: PASSED (both methods produced [12, 24, 35, 88, 120, 155])")

    # 8. Assert both methods return [] for smallest input
    validate_result_against_expected(orig_small, expected_smallest, "removeDuplicate([])")
    validate_result_against_expected(alt_small, expected_smallest, "removeDuplicateAlternative([])")
    print("PASS: Both methods returned [] for the smallest input.")
    results_lines.append("Smallest Input Assertion: PASSED (both methods returned [])")

    # 9. Assert results are lists and preserve first-occurrence order
    assert_is_list_and_preserves_order(published_fixture, orig_pub, "removeDuplicate(published)")
    assert_is_list_and_preserves_order(published_fixture, alt_pub, "removeDuplicateAlternative(published)")
    assert_is_list_and_preserves_order(smallest_fixture, orig_small, "removeDuplicate([])")
    assert_is_list_and_preserves_order(smallest_fixture, alt_small, "removeDuplicateAlternative([])")
    print("PASS: Verified that results are lists and strictly preserve first-occurrence order.")
    results_lines.append("List Type & Order Preservation Assertion: PASSED")

    # 10. Deliberate wrong-result tests
    print("Running deliberate wrong-result tests...")

    # Case 1: Corrupted value
    corrupted_result = [12, 24, 35, 88, 120, 999]
    run_deliberate_wrong_result_test(
        corrupted_result, expected_published, published_fixture, "corrupted value"
    )
    results_lines.append("Wrong-Result Test 1 (corrupted value): PASSED (error detected)")

    # Case 2: Inverted order (not preserving first occurrence)
    inverted_order_result = [24, 12, 35, 88, 120, 155]
    run_deliberate_wrong_result_test(
        inverted_order_result, expected_published, published_fixture, "inverted order"
    )
    results_lines.append("Wrong-Result Test 2 (inverted order): PASSED (error detected)")

    # Case 3: Non-empty result for empty input
    wrong_empty_result = [0]
    run_deliberate_wrong_result_test(
        wrong_empty_result, expected_smallest, smallest_fixture, "non-empty for empty input"
    )
    results_lines.append("Wrong-Result Test 3 (non-empty for empty input): PASSED (error detected)")

    # Case 4: Non-list return type
    non_list_result = {12, 24, 35, 88, 120, 155}
    run_deliberate_wrong_result_test(
        non_list_result, expected_published, published_fixture, "non-list type (set)"
    )
    results_lines.append("Wrong-Result Test 4 (non-list type): PASSED (error detected)")

    # 11. Write evidence files
    (evidence_dir / "actual.txt").write_text(f"{actual_orig_stdout}\n", encoding="utf-8")
    (evidence_dir / "expected.txt").write_text(f"{published_expected_str}\n", encoding="utf-8")

    inputs_content = (
        f"Published Input Fixture:\n{published_fixture}\n\n"
        f"Smallest Supported Input Fixture:\n{smallest_fixture}\n"
    )
    (evidence_dir / "inputs.txt").write_text(inputs_content, encoding="utf-8")
    (evidence_dir / "input-fixture.txt").write_text(inputs_content, encoding="utf-8")

    py_ver = subprocess.run([sys.executable, "--version"], capture_output=True, text=True).stdout.strip()
    git_ver = subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()
    (evidence_dir / "python-version.txt").write_text(f"{py_ver}\n{git_ver}\n", encoding="utf-8")

    results_lines.append(f"Python Version: {py_ver}")
    results_lines.append(f"Git Version: {git_ver}")
    results_lines.append("ALL CHECKS PASSED SUCCESSFULLY.")
    (evidence_dir / "test-results.txt").write_text("\n".join(results_lines) + "\n", encoding="utf-8")

    print("Evidence files saved successfully in work/R28-T003/.")
    print("ALL CHECKS PASSED.")


if __name__ == "__main__":
    main()

