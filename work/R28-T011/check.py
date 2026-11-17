#!/usr/bin/env python3
"""
Repeatable assertion-based check for Question 32 in:
100+ Python challenging programming exercises for Python 3.md

Task: R28-T011
Student: Parag Sanghavi (e26b07f0685)
"""

import sys
import os
import re
import platform
import subprocess
import json

def get_repo_root():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, "..", ".."))

def extract_question_32_code(md_path):
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown file not found: {md_path}")
    
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find Question 32 block
    q32_pattern = re.compile(
        r"###\s+Question\s+32\b(.*?)(?=###\s+Question|\Z)",
        re.DOTALL | re.IGNORECASE
    )
    match = q32_pattern.search(content)
    if not match:
        raise ValueError("Could not find '### Question 32' in the markdown file.")

    q32_text = match.group(1)

    # Extract python code block
    code_pattern = re.compile(r"```python\s*\n(.*?)\n```", re.DOTALL)
    code_match = code_pattern.search(q32_text)
    if not code_match:
        raise ValueError("Could not find a closed ```python ... ``` block in Question 32.")

    code = code_match.group(1).strip()
    return code

def run_code_in_subprocess(code):
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        sys.stderr.write(f"Subprocess failed with code {result.returncode}:\n{result.stderr}\n")
        sys.exit(result.returncode)
    return result.stdout

def run_function_with_input(func_code, arg):
    harness = f"""
{func_code}
checkValue({arg})
"""
    result = subprocess.run(
        [sys.executable, "-c", harness],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        sys.stderr.write(f"Execution failed for input {arg}:\n{result.stderr}\n")
        sys.exit(result.returncode)
    return result.stdout.strip()

def extract_function_definition(code):
    lines = code.splitlines()
    func_lines = []
    for line in lines:
        if line.strip().startswith("checkValue("):
            continue
        func_lines.append(line)
    return "\n".join(func_lines).strip()

def save_evidence(work_dir, inputs, expected_vs_actual, tool_versions):
    os.makedirs(work_dir, exist_ok=True)

    # 1. tool_versions.txt
    tv_path = os.path.join(work_dir, "tool_versions.txt")
    with open(tv_path, "w", encoding="utf-8") as f:
        f.write(f"Python Version: {tool_versions['python_version']}\n")
        f.write(f"Platform: {tool_versions['platform']}\n")
        f.write(f"OS: {tool_versions['os']}\n")
        f.write(f"Git Branch: {tool_versions['git_branch']}\n")
        f.write(f"Git Commit: {tool_versions['git_commit']}\n")

    # 2. inputs.txt
    inp_path = os.path.join(work_dir, "inputs.txt")
    with open(inp_path, "w", encoding="utf-8") as f:
        for item in inputs:
            f.write(f"Input: {item['input']}\n")
            f.write(f"Description: {item['description']}\n")
            f.write(f"Intermediate State (n % 2 == 0): {item['intermediate_state']}\n")
            f.write("-" * 40 + "\n")

    # 3. expected_vs_actual.txt
    eva_path = os.path.join(work_dir, "expected_vs_actual.txt")
    with open(eva_path, "w", encoding="utf-8") as f:
        f.write(f"{'Input':<10} | {'Intermediate':<15} | {'Expected Output':<25} | {'Actual Output':<25} | {'Status'}\n")
        f.write("-" * 90 + "\n")
        for row in expected_vs_actual:
            f.write(f"{str(row['input']):<10} | {str(row['intermediate']):<15} | {row['expected']:<25} | {row['actual']:<25} | {row['status']}\n")

    # 4. summary.json
    json_path = os.path.join(work_dir, "summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "task": "R28-T011",
            "student": "Parag Sanghavi",
            "enrollment": "e26b07f0685",
            "question": "Question 32",
            "tool_versions": tool_versions,
            "inputs": inputs,
            "results": expected_vs_actual,
            "status": "ALL_CHECKS_PASSED"
        }, f, indent=2)

def main():
    work_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = get_repo_root()
    md_file = os.path.join(repo_root, "100+ Python challenging programming exercises for Python 3.md")

    print("[1/5] Extracting Question 32 code directly from markdown...")
    extracted_code = extract_question_32_code(md_file)
    print("Extracted code snippet:\n---")
    print(extracted_code)
    print("---\n")

    # Verify extracted code contains expected elements
    assert "def checkValue(n):" in extracted_code, "checkValue definition missing in code block"
    assert "checkValue(7)" in extracted_code, "Published example checkValue(7) missing in code block"
    assert "checkValue(0)" in extracted_code, "Smallest supported input checkValue(0) missing in code block"
    print("[✓] Code block structure and function calls validated.")

    print("\n[2/5] Executing full extracted example in subprocess...")
    full_output = run_code_in_subprocess(extracted_code)
    expected_full_output = "It is an odd number\nIt is an even number\n"
    assert full_output == expected_full_output, (
        f"Full output mismatch!\nExpected: {repr(expected_full_output)}\nGot: {repr(full_output)}"
    )
    print(f"Subprocess stdout matches expected output:\n{full_output.strip()}")
    print("[✓] Full example execution check passed.")

    print("\n[3/5] Testing individual inputs and intermediate states...")
    func_def = extract_function_definition(extracted_code)

    inputs = [
        {
            "input": 7,
            "description": "Exact published example (odd integer)",
            "intermediate_state": "7 % 2 == 0 evaluates to False -> branches to else",
            "expected": "It is an odd number"
        },
        {
            "input": 0,
            "description": "Smallest supported non-negative integer input (even integer)",
            "intermediate_state": "0 % 2 == 0 evaluates to True -> branches to if",
            "expected": "It is an even number"
        }
    ]

    expected_vs_actual = []
    for item in inputs:
        actual = run_function_with_input(func_def, item["input"])
        assert actual == item["expected"], (
            f"Assertion failed for input {item['input']}: expected {item['expected']!r}, got {actual!r}"
        )
        expected_vs_actual.append({
            "input": item["input"],
            "intermediate": item["intermediate_state"].split("->")[0].strip(),
            "expected": item["expected"],
            "actual": actual,
            "status": "PASS"
        })
        print(f"  Input {item['input']}: intermediate state: '{item['intermediate_state']}' => actual: '{actual}' [PASS]")

    print("\n[4/5] Verifying failure on deliberate wrong result...")
    # Deliberate wrong check: assert that 7 produces "It is an even number"
    if "--deliberate-fail" in sys.argv:
        print("Deliberate failure mode triggered by --deliberate-fail flag.")
        actual_7 = run_function_with_input(func_def, 7)
        assert actual_7 == "It is an even number", "Deliberate wrong result triggered assertion failure as intended."

    # Normal verification: ensure test framework catches deliberate wrong result
    actual_7 = run_function_with_input(func_def, 7)
    wrong_expected = "It is an even number"
    deliberate_failure_caught = False
    try:
        assert actual_7 == wrong_expected, f"Deliberate assertion: expected {wrong_expected}, got {actual_7}"
    except AssertionError:
        deliberate_failure_caught = True

    assert deliberate_failure_caught, "Check failed to trigger AssertionError on deliberate wrong result!"
    print("[✓] Deliberate wrong result correctly triggers an assertion failure.")

    print("\n[5/5] Gathering tool versions and saving evidence in work/R28-T011/...")
    # Get git information
    try:
        git_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root, text=True
        ).strip()
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root, text=True
        ).strip()
    except Exception:
        git_branch = "student/e26b07f0685/R28-T011"
        git_commit = "unknown"

    tool_versions = {
        "python_version": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "os": platform.system(),
        "git_branch": git_branch,
        "git_commit": git_commit
    }

    save_evidence(work_dir, inputs, expected_vs_actual, tool_versions)
    print(f"[✓] Evidence saved to {work_dir}")
    print("\nAll checks passed successfully! (exit code 0)")

if __name__ == "__main__":
    main()
