#!/usr/bin/env python3
"""Automated checker for Question 86 (Issue R28-T001).

This script:
1. Reads the markdown article '100+ Python challenging programming exercises for Python 3.md'.
2. Extracts Question 86's Python solution code block dynamically.
3. Executes that extracted code using Python 3 through subprocess.
4. Captures stdout and stderr.
5. Compares actual stdout against the published expected output.
6. Asserts that exactly eight sentences are printed.
7. Performs negative tests proving that incorrect expected outputs fail assertions.
8. Propagates subprocess failures and exits non-zero on assertion failures.
9. Updates evidence files (actual.txt, test-results.txt).
"""

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
    # Match Question 86 up to Question 87 or end of document
    q86_match = re.search(
        r"### Question 86\b(.*?)(?=### Question 87\b|\Z)",
        markdown_text,
        re.DOTALL,
    )
    if not q86_match:
        raise AssertionError("Section '### Question 86' not found in Markdown article")

    q86_body = q86_match.group(1)

    # Extract python solution code block
    code_match = re.search(
        r"Solution:\s*\n```(?:python)?\s*\n(.*?)\n```",
        q86_body,
        re.DOTALL,
    )
    if not code_match:
        # Fallback: search for first python code block in Question 86
        code_match = re.search(
            r"```(?:python)?\s*\n(.*?)\n```",
            q86_body,
            re.DOTALL,
        )
    if not code_match:
        raise AssertionError("Solution code block not found in Question 86")

    return code_match.group(1)


def extract_published_expected_output(markdown_text: str) -> str:
    q86_match = re.search(
        r"### Question 86\b(.*?)(?=### Question 87\b|\Z)",
        markdown_text,
        re.DOTALL,
    )
    if not q86_match:
        raise AssertionError("Section '### Question 86' not found in Markdown article")

    q86_body = q86_match.group(1)

    # Extract expected output from Example section
    expected_match = re.search(
        r"output of the program should be:\s*\n\s*(.*?)(?=\n\s*Hints:|\n\s*Solution:|\Z)",
        q86_body,
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


def validate_output(actual: str, expected: str) -> None:
    actual_clean = actual.strip()
    expected_clean = expected.strip()

    actual_lines = [line.strip() for line in actual_clean.splitlines() if line.strip()]
    expected_lines = [line.strip() for line in expected_clean.splitlines() if line.strip()]

    # Assert exactly 8 sentences are printed in actual output
    if len(actual_lines) != 8:
        raise AssertionError(f"Expected 8 sentences in actual output, but found {len(actual_lines)}")

    # Assert expected output also defines exactly 8 sentences
    if len(expected_lines) != 8:
        raise AssertionError(f"Expected output must specify 8 sentences, but specifies {len(expected_lines)}")

    # Compare actual lines with expected lines
    if actual_lines != expected_lines:
        raise AssertionError(
            f"Output mismatch.\n--- Expected ---\n{expected_clean}\n--- Actual ---\n{actual_clean}"
        )


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

    print("=== Running Automated Checker for Question 86 (Issue R28-T001) ===")
    results_lines.append("=== Automated Checker Results for Question 86 (Issue R28-T001) ===")

    # 1. Inspect source & locate markdown
    md_path = find_markdown_file()
    print(f"Reading Markdown article from: {md_path}")
    md_content = md_path.read_text(encoding="utf-8")

    # 2. Extract solution code
    code = extract_solution_code(md_content)
    print("Successfully extracted Question 86 Python solution code block.")
    results_lines.append("Code Extraction: SUCCESS")

    # 3. Extract published expected output
    expected_output = extract_published_expected_output(md_content)
    print("Successfully resolved published expected output.")
    results_lines.append("Expected Output Resolution: SUCCESS")

    # Save expected.txt
    expected_file = evidence_dir / "expected.txt"
    expected_file.write_text(expected_output, encoding="utf-8")

    # Ensure inputs.txt exists
    inputs_file = evidence_dir / "inputs.txt"
    if not inputs_file.exists():
        inputs_file.write_text("", encoding="utf-8")

    # Ensure python-version.txt exists
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
    validate_output(actual_output, expected_output)
    num_sentences = len([l for l in actual_output.strip().splitlines() if l.strip()])
    print(f"PASS: Positive test passed ({num_sentences} sentences matched expected output).")
    results_lines.append(f"Positive Test: PASSED ({num_sentences} sentences matched exact expected output)")

    # 6. Negative tests
    print("Running negative tests...")
    # Negative test 1: wrong content
    corrupted_expected = expected_output.replace("Hockey", "Baseball")
    run_negative_test(actual_output, corrupted_expected, "incorrect expected sentence text")
    results_lines.append("Negative Test 1 (incorrect sentence content): PASSED (assertion raised)")

    # Negative test 2: wrong sentence count (7 sentences)
    seven_sentences = "\n".join(expected_output.strip().splitlines()[:-1]) + "\n"
    run_negative_test(actual_output, seven_sentences, "insufficient sentence count (7 sentences)")
    results_lines.append("Negative Test 2 (insufficient sentence count): PASSED (assertion raised)")

    # Negative test 3: extra sentence (9 sentences)
    nine_sentences = expected_output + "You Love Basketball.\n"
    run_negative_test(actual_output, nine_sentences, "excess sentence count (9 sentences)")
    results_lines.append("Negative Test 3 (excess sentence count): PASSED (assertion raised)")

    results_lines.append("ALL CHECKS PASSED SUCCESSFULLY.")
    (evidence_dir / "test-results.txt").write_text("\n".join(results_lines) + "\n", encoding="utf-8")
    print("Evidence files written successfully.")
    print("ALL CHECKS PASSED.")


if __name__ == "__main__":
    main()
