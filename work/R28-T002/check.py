#!/usr/bin/env python3
"""Automated checker for Question 37 (Issue R28-T002).

This script:
1. Reads the Markdown article '100+ Python challenging programming exercises for Python 3.md'.
2. Dynamically locates Question 37 and extracts its published Python solution code block.
3. Executes the extracted code using Python 3 through subprocess without retyping the solution.
4. Captures stdout and stderr.
5. Verifies the exact published output.
6. Verifies that the first generated square is 1.
7. Verifies that the last generated square is 400.
8. Verifies that exactly 20 values are generated.
9. Performs negative tests proving incorrect expected outputs fail assertions.
10. Propagates subprocess failures and exits non-zero if any assertion fails.
11. Saves and updates evidence files in work/R28-T002/.
"""

import ast
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


def extract_solution_code(markdown_text: str) -> str:
    # Match Question 37 up to Question 38 or end of document
    q37_match = re.search(
        r"### Question 37\b(.*?)(?=### Question 38\b|\Z)",
        markdown_text,
        re.DOTALL,
    )
    if not q37_match:
        raise AssertionError("Section '### Question 37' not found in Markdown article")

    q37_body = q37_match.group(1)

    # Extract python solution code block
    code_match = re.search(
        r"Solution:?\s*\n```(?:python)?\s*\n(.*?)\n```",
        q37_body,
        re.DOTALL,
    )
    if not code_match:
        # Fallback: search for first python code block in Question 37
        code_match = re.search(
            r"```(?:python)?\s*\n(.*?)\n```",
            q37_body,
            re.DOTALL,
        )
    if not code_match:
        raise AssertionError("Solution code block not found in Question 37")

    return code_match.group(1)


def extract_published_expected_output(markdown_text: str) -> str:
    q37_match = re.search(
        r"### Question 37\b(.*?)(?=### Question 38\b|\Z)",
        markdown_text,
        re.DOTALL,
    )
    if not q37_match:
        raise AssertionError("Section '### Question 37' not found in Markdown article")

    q37_body = q37_match.group(1)

    # Extract expected output from Example section
    expected_match = re.search(
        r"output of the program should be:\s*\n\s*(.*?)(?=\n\s*Hints:|\n\s*Solution:?|\Z)",
        q37_body,
        re.DOTALL | re.IGNORECASE,
    )
    if expected_match:
        return expected_match.group(1).strip() + "\n"

    # Fallback to expected.txt if present
    evidence_dir = Path(__file__).resolve().parent
    expected_file = evidence_dir / "expected.txt"
    if expected_file.is_file():
        return expected_file.read_text(encoding="utf-8")

    raise AssertionError("Published expected output not found in Markdown article or expected.txt")


def execute_code(code: str) -> subprocess.CompletedProcess:
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


def validate_output(actual: str, expected: str) -> list:
    actual_clean = actual.strip()
    expected_clean = expected.strip()

    # Verify exact string output match
    if actual_clean != expected_clean:
        raise AssertionError(
            f"Output mismatch.\n--- Expected ---\n{expected_clean}\n--- Actual ---\n{actual_clean}"
        )

    # Parse and validate the list structure
    try:
        parsed_list = ast.literal_eval(actual_clean)
    except Exception as e:
        raise AssertionError(f"Failed to parse output as a Python literal list: {e}")

    if not isinstance(parsed_list, list):
        raise AssertionError(f"Expected output to be a list, got {type(parsed_list).__name__}")

    # Verify that exactly 20 values are generated
    if len(parsed_list) != 20:
        raise AssertionError(f"Expected exactly 20 values, but got {len(parsed_list)}")

    # Verify that the first generated square is 1
    if parsed_list[0] != 1:
        raise AssertionError(f"Expected first value to be 1, but got {parsed_list[0]}")

    # Verify that the last generated square is 400
    if parsed_list[-1] != 400:
        raise AssertionError(f"Expected last value to be 400, but got {parsed_list[-1]}")

    return parsed_list


def run_negative_test(actual: str, faulty_expected: str, test_description: str) -> None:
    try:
        validate_output(actual, faulty_expected)
    except AssertionError as e:
        print(f"PASS: Negative test ({test_description}) correctly failed: {e}")
    else:
        raise AssertionError(
            f"FAIL: Negative test ({test_description}) unexpectedly passed validation!"
        )


def main() -> None:
    evidence_dir = Path(__file__).resolve().parent
    results_lines = []

    print("=== Running Automated Checker for Question 37 (Issue R28-T002) ===")
    results_lines.append("=== Automated Checker Results for Question 37 (Issue R28-T002) ===")

    # 1. Locate markdown source
    md_path = find_markdown_file()
    print(f"Reading Markdown article from: {md_path}")
    md_content = md_path.read_text(encoding="utf-8")

    # 2. Extract solution code dynamically
    code = extract_solution_code(md_content)
    print("Successfully extracted Question 37 Python solution code block.")
    results_lines.append("Code Extraction: SUCCESS")

    # 3. Extract published expected output
    expected_output = extract_published_expected_output(md_content)
    print("Successfully resolved published expected output.")
    results_lines.append("Expected Output Resolution: SUCCESS")

    # Save expected.txt
    expected_file = evidence_dir / "expected.txt"
    expected_file.write_text(expected_output, encoding="utf-8")

    # Save inputs.txt (explicitly state no stdin required)
    inputs_file = evidence_dir / "inputs.txt"
    inputs_file.write_text("No stdin is required (Question 37 is a no-input demonstration).\n", encoding="utf-8")

    # Save python-version.txt
    py_ver_proc = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
    py_ver_str = py_ver_proc.stdout.strip() or py_ver_proc.stderr.strip()
    (evidence_dir / "python-version.txt").write_text(f"{py_ver_str}\n", encoding="utf-8")
    results_lines.append(f"Python Version: {py_ver_str}")

    # 4. Execute code through subprocess
    proc = execute_code(code)
    actual_output = proc.stdout
    (evidence_dir / "actual.txt").write_text(actual_output, encoding="utf-8")
    print("Subprocess execution completed with exit code 0.")
    results_lines.append("Subprocess Execution: SUCCESS (exit code 0)")

    # 5. Positive verification
    parsed_values = validate_output(actual_output, expected_output)
    print(f"PASS: Positive test passed.")
    print(f"  - Total values generated: {len(parsed_values)} (asserted == 20)")
    print(f"  - First generated square: {parsed_values[0]} (asserted == 1)")
    print(f"  - Last generated square: {parsed_values[-1]} (asserted == 400)")
    print(f"  - Exact output string matched published example.")
    results_lines.append("Positive Test: PASSED (exact match with published example)")
    results_lines.append(f"Assertion (total count == 20): PASSED ({len(parsed_values)})")
    results_lines.append(f"Assertion (first square == 1): PASSED ({parsed_values[0]})")
    results_lines.append(f"Assertion (last square == 400): PASSED ({parsed_values[-1]})")

    # 6. Negative tests
    print("Running negative tests...")

    # Negative test 1: wrong expected string content compared against actual
    corrupted_expected = expected_output.replace("400", "999")
    run_negative_test(actual_output, corrupted_expected, "incorrect expected string content")
    results_lines.append("Negative Test 1 (incorrect expected content): PASSED (assertion raised)")

    # Negative test 2: output where first element is not 1
    faulty_first = str([0] + parsed_values[1:]) + "\n"
    run_negative_test(faulty_first, faulty_first, "incorrect first element (0 instead of 1)")
    results_lines.append("Negative Test 2 (incorrect first element): PASSED (assertion raised)")

    # Negative test 3: output where last element is not 400
    faulty_last = str(parsed_values[:-1] + [441]) + "\n"
    run_negative_test(faulty_last, faulty_last, "incorrect last element (441 instead of 400)")
    results_lines.append("Negative Test 3 (incorrect last element): PASSED (assertion raised)")

    # Negative test 4: output where length is not 20
    faulty_len = str(parsed_values[:-1]) + "\n"
    run_negative_test(faulty_len, faulty_len, "incorrect length (19 elements instead of 20)")
    results_lines.append("Negative Test 4 (incorrect length 19 elements): PASSED (assertion raised)")

    results_lines.append("ALL CHECKS PASSED SUCCESSFULLY.")
    (evidence_dir / "test-results.txt").write_text("\n".join(results_lines) + "\n", encoding="utf-8")
    print("Evidence files written successfully.")
    print("ALL CHECKS PASSED.")


if __name__ == "__main__":
    main()

