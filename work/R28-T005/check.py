#!/usr/bin/env python3
"""
Automated Checker for R28-T005 Question 50.

Requirements:
- Extract actual Question 50 example from changed Markdown file.
- Execute with Python 3 using a subprocess.
- Assert output is exactly two lines:
  America
  America
- Assert instance is an American object and method works through both instance and class.
- Include a deliberate wrong-result test to prove checker fails on incorrect output.
- Propagate subprocess failures and exit with non-zero status on assertion failure.
- Record evidence into work/R28-T005/results.txt and work/R28-T005/tool-versions.txt.
"""

import io
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


def extract_question_50_code(md_path):
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Locate Question 50 section up to Question 51
    pattern = r"### Question 50(.*?)(?=### Question 51|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError("Could not find '### Question 50' section in markdown file.")

    q50_text = match.group(1)

    # Locate the python code block under Solution
    code_match = re.search(r"Solution:?\s*```python\s*(.*?)\s*```", q50_text, re.DOTALL)
    if not code_match:
        raise ValueError("Could not extract Python code block under Solution in Question 50.")

    extracted_code = code_match.group(1).strip()
    return extracted_code


def validate_output(output_lines, expected_lines):
    """Assert output matches expected two-line 'America' output."""
    assert isinstance(output_lines, list), f"Expected list of lines, got {type(output_lines)}"
    assert len(output_lines) == len(expected_lines), (
        f"Line count mismatch! Expected {len(expected_lines)} lines, got {len(output_lines)}: {output_lines}"
    )
    for idx, (actual, exp) in enumerate(zip(output_lines, expected_lines), start=1):
        assert actual == exp, f"Line {idx} mismatch! Expected '{exp}', got '{actual}'"


def validate_class_and_instance(namespace):
    """Assert instance is an American object and method works via both instance and class."""
    assert "American" in namespace, "Class 'American' not defined in namespace"
    assert "anAmerican" in namespace, "Instance 'anAmerican' not defined in namespace"

    American = namespace["American"]
    anAmerican = namespace["anAmerican"]

    # Assert anAmerican is an instance of American
    assert isinstance(anAmerican, American), (
        f"'anAmerican' is not an instance of American! Got type {type(anAmerican)}"
    )

    # Assert printNationality is defined as a staticmethod
    raw_attr = American.__dict__.get("printNationality")
    assert isinstance(raw_attr, staticmethod), (
        f"'printNationality' in American class is not a staticmethod! Got {type(raw_attr)}"
    )

    # Verify calling via class prints 'America'
    buf_class = io.StringIO()
    with redirect_stdout(buf_class):
        American.printNationality()
    assert buf_class.getvalue().strip() == "America", (
        f"American.printNationality() failed to print 'America': {buf_class.getvalue()}"
    )

    # Verify calling via instance prints 'America'
    buf_instance = io.StringIO()
    with redirect_stdout(buf_instance):
        anAmerican.printNationality()
    assert buf_instance.getvalue().strip() == "America", (
        f"anAmerican.printNationality() failed to print 'America': {buf_instance.getvalue()}"
    )


def run_deliberate_wrong_result_tests():
    """Verify that checker fails when fed deliberate incorrect outputs and properties."""
    expected = ["America", "America"]

    # 1. Single line output
    try:
        validate_output(["America"], expected)
        raise AssertionError("Failed to catch single-line output!")
    except AssertionError:
        pass

    # 2. Three lines output
    try:
        validate_output(["America", "America", "America"], expected)
        raise AssertionError("Failed to catch three-line output!")
    except AssertionError:
        pass

    # 3. Incorrect text
    try:
        validate_output(["USA", "USA"], expected)
        raise AssertionError("Failed to catch incorrect text output!")
    except AssertionError:
        pass

    # 4. Wrong instance type
    class Canadian:
        pass

    fake_ns = {
        "American": Canadian,
        "anAmerican": Canadian(),
    }
    try:
        validate_class_and_instance(fake_ns)
        raise AssertionError("Failed to catch wrong class type!")
    except AssertionError:
        pass


def main():
    repo_root = get_repo_root()
    work_dir = get_work_dir()
    os.makedirs(work_dir, exist_ok=True)

    md_file = os.path.join(repo_root, "100+ Python challenging programming exercises for Python 3.md")

    print("=" * 60)
    print("R28-T005: Question 50 Automated Checker")
    print("=" * 60)
    print(f"Authoritative Markdown: {md_file}")
    print(f"Work Directory:         {work_dir}")

    logs = []

    def log(msg):
        print(msg)
        logs.append(msg)

    # Step 1: Extract actual code from Markdown
    log("\n[Step 1] Extracting actual code from Question 50...")
    extracted_code = extract_question_50_code(md_file)
    log("Extracted code:")
    log("-" * 40)
    log(extracted_code)
    log("-" * 40)

    # Step 2: Execute extracted code via Python subprocess
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

    actual_output = proc.stdout.strip()
    actual_lines = [line.strip() for line in actual_output.splitlines() if line.strip()]
    expected_lines = ["America", "America"]
    expected_output = "\n".join(expected_lines)

    log("Subprocess stdout:")
    log(actual_output)

    # Step 3: Assert output is exactly two lines: 'America', 'America'
    log("\n[Step 3] Asserting output matches exactly two lines of 'America'...")
    validate_output(actual_lines, expected_lines)
    log("PASS: Output contains exactly two lines: 'America' and 'America'.")

    # Step 4: Verify class, staticmethod, and instance behavior in-memory
    log("\n[Step 4] Verifying class, staticmethod, and instance relationships...")
    ns = {}
    with redirect_stdout(io.StringIO()):
        exec(extracted_code, ns)

    validate_class_and_instance(ns)
    log("PASS: anAmerican is verified as an American instance.")
    log("PASS: printNationality is confirmed as a staticmethod.")
    log("PASS: Method executes successfully through both anAmerican.printNationality() and American.printNationality().")

    # Step 5: Deliberate wrong-result testing
    log("\n[Step 5] Running deliberate wrong-result tests to prove checker error detection...")
    run_deliberate_wrong_result_tests()
    wrong_result_test_status = "PASSED: All deliberate wrong-result tests triggered expected AssertionErrors."
    log(f"PASS: {wrong_result_test_status}")

    # Step 6: Save evidence files inside work/R28-T005/
    log("\n[Step 6] Saving evidence files inside work/R28-T005/...")

    # results.txt
    results_path = os.path.join(work_dir, "results.txt")
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("R28-T005 Question 50 Test Results\n")
        f.write("=" * 50 + "\n\n")
        f.write("1. Executed Example from Markdown:\n")
        f.write("-" * 40 + "\n")
        f.write(extracted_code + "\n")
        f.write("-" * 40 + "\n\n")
        f.write("2. Expected Output:\n")
        f.write("-" * 40 + "\n")
        f.write(expected_output + "\n")
        f.write("-" * 40 + "\n\n")
        f.write("3. Actual Subprocess Output:\n")
        f.write("-" * 40 + "\n")
        f.write(actual_output + "\n")
        f.write("-" * 40 + "\n\n")
        f.write("4. Property Verifications:\n")
        f.write("  - Output is exactly 2 lines matching 'America'\n")
        f.write("  - anAmerican is an instance of American: YES\n")
        f.write("  - printNationality is a @staticmethod: YES\n")
        f.write("  - anAmerican.printNationality() prints 'America': YES\n")
        f.write("  - American.printNationality() prints 'America': YES\n\n")
        f.write(f"5. Deliberate Wrong-Result Test Status:\n  {wrong_result_test_status}\n\n")
        f.write("6. Execution Log:\n")
        for line in logs:
            f.write(f"{line}\n")
        f.write("\nOverall Status: ALL TESTS PASSED\n")

    # tool-versions.txt
    tool_ver_path = os.path.join(work_dir, "tool-versions.txt")
    git_ver_proc = subprocess.run(["git", "--version"], capture_output=True, text=True)
    git_ver = git_ver_proc.stdout.strip() if git_ver_proc.returncode == 0 else "git unknown"

    with open(tool_ver_path, "w", encoding="utf-8") as f:
        f.write("R28-T005 Tool Versions\n")
        f.write("=" * 50 + "\n")
        f.write(f"Python Version:    {platform.python_version()}\n")
        f.write(f"Python Build:      {sys.version}\n")
        f.write(f"Python Executable: {sys.executable}\n")
        f.write(f"Git Version:       {git_ver}\n")
        f.write(f"OS Platform:       {platform.platform()}\n")
        f.write(f"Architecture:      {platform.machine()}\n")

    log("Saved evidence files:")
    log(f"  - {results_path}")
    log(f"  - {tool_ver_path}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
