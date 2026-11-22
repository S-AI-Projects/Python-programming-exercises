import argparse
import os
import re
import subprocess
import sys
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
md_path = os.path.join(here, "..", "..", "100+ Python challenging programming exercises for Python 3.md")


def get_solution_code(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract Question 44 section
    q_match = re.search(r"### Question 44\n(.*?)(?=### Question 45)", content, re.S)
    if not q_match:
        print("Error: Question 44 not found in markdown file")
        sys.exit(1)

    sec = q_match.group(1)
    code_match = re.search(r"Solution\s*```python\n(.*?)```", sec, re.S)
    if not code_match:
        print("Error: Question 44 solution code block not found")
        sys.exit(1)

    return code_match.group(1).strip()


def run_code(code, stdin_input):
    fd, tmp_file = tempfile.mkstemp(prefix="check_q44_", suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        res = subprocess.run(
            [sys.executable, tmp_file],
            input=stdin_input,
            capture_output=True,
            text=True
        )
        return res
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)


def main():
    parser = argparse.ArgumentParser(description="Automated checker for Question 44")
    parser.add_argument("--wrong", action="store_true", help="Trigger deliberate failure to test checker rejection")
    args = parser.parse_args()

    print(f"Reading solution from: {md_path}")
    code = get_solution_code(md_path)
    print("Extracted code from markdown:\n---")
    print(code)
    print("---")

    # If --wrong flag is passed, deliberately simulate an incorrect expectation
    if args.wrong:
        print("\n[SIMULATING DELIBERATE FAILURE (--wrong flag active)]")
        # Run published input "yes", but assert expected "No"
        res = run_code(code, "yes\n")
        assert res.returncode == 0
        actual = res.stdout.strip()
        print(f"Input: 'yes' | Actual: '{actual}' | Deliberate Wrong Expected: 'No'")
        assert actual == "No", f"DELIBERATE FAILURE TRIGGERED: Output '{actual}' did not match deliberate wrong expected 'No'"
        print("Error: Deliberate failure should have raised an AssertionError!")
        sys.exit(1)

    # 1. Test Published Examples (exact matches for "yes", "YES", "Yes")
    print("\n[1] Testing published examples...")
    published_cases = [
        ("yes", "Yes"),
        ("YES", "Yes"),
        ("Yes", "Yes"),
    ]
    for inp, exp in published_cases:
        res = run_code(code, f"{inp}\n")
        if res.returncode != 0:
            print(f"Execution crashed for input {inp!r}!")
            print("stderr:", res.stderr)
            sys.exit(1)
        actual = res.stdout.strip()
        print(f"Input: {inp!r:8} | Expected: {exp!r:6} | Actual: {actual!r:6}")
        assert actual == exp, f"Published case failed for {inp!r}: expected {exp!r}, got {actual!r}"
    print("Published examples verified successfully.")

    # 2. Test Smallest Supported Input (empty string "")
    print("\n[2] Testing smallest supported input (empty string '')...")
    res_empty = run_code(code, "\n")
    if res_empty.returncode != 0:
        print("Execution crashed on empty string input!")
        print("stderr:", res_empty.stderr)
        sys.exit(1)
    act_empty = res_empty.stdout.strip()
    print(f"Input: '' (empty line) | Expected: 'No' | Actual: {act_empty!r}")
    assert act_empty == "No", f"Smallest supported input failed: expected 'No', got {act_empty!r}"
    print("Smallest supported input verified successfully.")

    # 3. Test Boundary Cases (case variation, partial match, trailing space, contrast)
    print("\n[3] Testing boundary cases...")
    boundary_cases = [
        ("yEs", "No", "Mixed case variation not in allowed set"),
        ("y", "No", "Single character prefix"),
        ("yes ", "No", "Trailing whitespace"),
        ("no", "No", "Distinct word"),
    ]
    for inp, exp, desc in boundary_cases:
        res = run_code(code, f"{inp}\n")
        if res.returncode != 0:
            print(f"Execution crashed on boundary input {inp!r} ({desc})!")
            print("stderr:", res.stderr)
            sys.exit(1)
        actual = res.stdout.strip()
        print(f"Input: {inp!r:8} | Expected: {exp!r:6} | Actual: {actual!r:6} | Reason: {desc}")
        assert actual == exp, f"Boundary case failed for {inp!r}: expected {exp!r}, got {actual!r}"
    print("Boundary cases verified successfully.")

    # 4. Internal Deliberate Wrong-Result Self-Test
    print("\n[4] Running internal wrong-result self-test...")
    sample_res = run_code(code, "yes\n")
    sample_actual = sample_res.stdout.strip()
    wrong_expectation = "No"
    if sample_actual == wrong_expectation:
        print("Self-test FAILED: check accepted a wrong result!")
        sys.exit(1)
    print("Self-test PASSED: mismatch against wrong expectation correctly detected and rejected.")

    print("\nAll checks passed successfully! (exit code 0)")


if __name__ == "__main__":
    main()
