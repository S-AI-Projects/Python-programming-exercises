import argparse
import ast
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

    # Extract Question 53 section
    q_match = re.search(r"### Question 53\n(.*?)(?=### Question 54)", content, re.S)
    if not q_match:
        print("Error: Question 53 not found in markdown file")
        sys.exit(1)

    sec = q_match.group(1)
    code_match = re.search(r"Solution:\s*```python\n(.*?)```", sec, re.S)
    if not code_match:
        print("Error: Question 53 solution code block not found")
        sys.exit(1)

    return code_match.group(1).strip()


def run_code(code):
    fd, tmp_file = tempfile.mkstemp(prefix="check_q53_", suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        res = subprocess.run([sys.executable, tmp_file], capture_output=True, text=True)
        return res
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)


def main():
    parser = argparse.ArgumentParser(description="Automated checker for Question 53")
    parser.add_argument("--wrong", action="store_true", help="Trigger deliberate failure to test checker rejection")
    args = parser.parse_args()

    print(f"Reading solution from: {md_path}")
    code = get_solution_code(md_path)
    print("Extracted code from markdown:\n---")
    print(code)
    print("---")

    # If --wrong flag is passed, simulate deliberate failure
    if args.wrong:
        print("\n[SIMULATING DELIBERATE FAILURE (--wrong flag active)]")
        res = run_code(code)
        assert res.returncode == 0
        actual = res.stdout.strip()
        deliberate_wrong = "40"
        print(f"Actual: {actual!r} | Deliberate Wrong Expected: {deliberate_wrong!r}")
        assert actual == deliberate_wrong, f"DELIBERATE FAILURE TRIGGERED: Output {actual!r} did not match wrong expectation {deliberate_wrong!r}"
        print("Error: Deliberate failure should have raised an AssertionError!")
        sys.exit(1)

    # 1. Run Published Example (Rectangle(2, 10))
    print("\n[1] Running published example (Rectangle(2, 10))...")
    res_pub = run_code(code)
    if res_pub.returncode != 0:
        print("Execution failed!")
        print("stderr:", res_pub.stderr)
        sys.exit(1)

    expected_pub = "20\n"
    actual_pub = res_pub.stdout
    print(f"Expected stdout: {expected_pub!r}")
    print(f"Actual stdout:   {actual_pub!r}")
    assert actual_pub == expected_pub, f"Mismatch: expected {expected_pub!r}, got {actual_pub!r}"
    assert int(actual_pub.strip()) == 20
    print("Published example verified successfully.")

    # 2. Verify Object Internal State and Attribute Storage
    print("\n[2] Verifying Rectangle internal attribute state and dictionary...")
    state_test_code = code + "\nprint(repr(aRectangle.__dict__))\n"
    res_state = run_code(state_test_code)
    assert res_state.returncode == 0, f"State check crashed: {res_state.stderr}"
    lines = res_state.stdout.strip().split("\n")
    dict_repr = lines[-1]
    parsed_dict = ast.literal_eval(dict_repr)
    print(f"Instance attribute dict: {parsed_dict}")
    assert parsed_dict == {"length": 2, "width": 10}, f"Unexpected internal state: {parsed_dict}"
    print("Object attributes length=2 and width=10 confirmed stored in instance state.")

    # 3. Test Smallest Supported Inputs
    print("\n[3] Testing smallest supported inputs...")
    # 3a. Smallest positive integer input: Rectangle(1, 1) -> 1
    small_code_1 = re.sub(r"Rectangle\(2,\s*10\)", "Rectangle(1, 1)", code, count=1)
    assert "Rectangle(1, 1)" in small_code_1, "Failed to substitute Rectangle(1, 1)"
    res_small_1 = run_code(small_code_1)
    assert res_small_1.returncode == 0, f"Small input crashed: {res_small_1.stderr}"
    print(f"Smallest positive input Rectangle(1, 1) output: {res_small_1.stdout.strip()!r} (Expected: '1')")
    assert res_small_1.stdout == "1\n"
    assert int(res_small_1.stdout.strip()) == 1

    # 3b. Zero boundary: Rectangle(0, 0) -> 0
    zero_code = re.sub(r"Rectangle\(2,\s*10\)", "Rectangle(0, 0)", code, count=1)
    assert "Rectangle(0, 0)" in zero_code, "Failed to substitute Rectangle(0, 0)"
    res_zero = run_code(zero_code)
    assert res_zero.returncode == 0, f"Zero input crashed: {res_zero.stderr}"
    print(f"Zero boundary Rectangle(0, 0) output: {res_zero.stdout.strip()!r} (Expected: '0')")
    assert res_zero.stdout == "0\n"
    assert int(res_zero.stdout.strip()) == 0
    print("Smallest supported inputs verified successfully.")

    # 4. Compare with Independent Alternative on the Same Fixture (2, 10)
    print("\n[4] Comparing class method with independent functional alternative on fixture (2, 10)...")
    comparison_code = """
def direct_area(l, w):
    return l * w

print(direct_area(2, 10))
"""
    res_alt = run_code(comparison_code)
    assert res_alt.returncode == 0
    alt_out = res_alt.stdout
    print(f"Class method output:       {actual_pub!r}")
    print(f"Alternative method output: {alt_out!r}")
    assert alt_out == actual_pub, f"Alternative output {alt_out!r} != class output {actual_pub!r}"
    assert int(alt_out.strip()) == 20
    print("Both class-based and functional alternatives produce identical output (20) on fixture (2, 10).")

    # 5. Internal Deliberate Wrong-Result Self-Test
    print("\n[5] Running internal deliberate wrong-result self-test...")
    wrong_expectation = "99\n"
    if actual_pub == wrong_expectation:
        print("Self-test FAILED: accepted incorrect expected output!")
        sys.exit(1)
    print("Self-test PASSED: mismatch against wrong expectation correctly detected and rejected.")

    print("\nAll checks passed successfully! (exit code 0)")


if __name__ == "__main__":
    main()
