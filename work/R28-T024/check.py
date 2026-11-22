import argparse
import ast
import math
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

    # Extract Question 49 section
    q_match = re.search(r"### Question 49\n(.*?)(?=### Question 50)", content, re.S)
    if not q_match:
        print("Error: Question 49 not found in markdown file")
        sys.exit(1)

    sec = q_match.group(1)
    code_match = re.search(r"Solution\s*```python\n(.*?)```", sec, re.S)
    if not code_match:
        print("Error: Question 49 solution code block not found")
        sys.exit(1)

    return code_match.group(1).strip()


def run_code(code):
    fd, tmp_file = tempfile.mkstemp(prefix="check_q49_", suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        res = subprocess.run([sys.executable, tmp_file], capture_output=True, text=True)
        return res
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)


def main():
    parser = argparse.ArgumentParser(description="Automated checker for Question 49")
    parser.add_argument("--wrong", action="store_true", help="Trigger deliberate failure to test checker rejection")
    args = parser.parse_args()

    print(f"Reading solution from: {md_path}")
    code = get_solution_code(md_path)
    print("Extracted code from markdown:\n---")
    print(code)
    print("---")

    # If --wrong flag is active, trigger deliberate failure
    if args.wrong:
        print("\n[SIMULATING DELIBERATE FAILURE (--wrong flag active)]")
        res = run_code(code)
        assert res.returncode == 0
        actual = res.stdout.strip()
        deliberate_wrong = "[1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256, 289, 324, 361, 400]"
        print(f"Actual stdout: {actual!r} | Deliberate Wrong Expected: {deliberate_wrong!r}")
        assert actual == deliberate_wrong, f"DELIBERATE FAILURE TRIGGERED: Output {actual!r} did not match wrong expectation {deliberate_wrong!r}"
        print("Error: Deliberate failure should have raised an AssertionError!")
        sys.exit(1)

    # 1. Run Published Example directly
    print("\n[1] Running published example...")
    res_pub = run_code(code)
    if res_pub.returncode != 0:
        print("Execution failed!")
        print("stderr:", res_pub.stderr)
        sys.exit(1)

    actual_stdout = res_pub.stdout
    print(f"Actual stdout: {actual_stdout!r}")
    # In Python 3, print(map_object) displays '<map object at 0x...>\n'
    map_obj_pattern = r"^<map object at 0x[0-9a-fA-F]+>\n$"
    assert re.match(map_obj_pattern, actual_stdout), (
        f"Expected map object string representation, got {actual_stdout!r}"
    )
    print("Verified: print(squaredNumbers) outputs the map iterator object representation.")

    # 2. Assert Stated Property and Invariant on Published Fixture
    print("\n[2] Verifying stated property, type and mathematical invariant on published fixture...")
    eval_code = code + """
print(type(squaredNumbers).__name__)
print(list(map(lambda x: x**2, range(1, 21))))
"""
    res_eval = run_code(eval_code)
    assert res_eval.returncode == 0, f"Evaluation crashed: {res_eval.stderr}"
    eval_lines = res_eval.stdout.strip().split("\n")
    type_name = eval_lines[1]
    materialized_list = ast.literal_eval(eval_lines[2])

    print(f"Object type: {type_name}")
    assert type_name == "map", f"Expected type 'map', got {type_name}"

    expected_squares = [i**2 for i in range(1, 21)]
    print(f"Materialized count: {len(materialized_list)}")
    print(f"First 5 squares:   {materialized_list[:5]}")
    print(f"Last 5 squares:    {materialized_list[-5:]}")
    assert materialized_list == expected_squares, "Materialized squares do not match expected range squares"

    # Verify Invariant across all elements:
    # Invariant: y >= 0, len(y) == 20, y_i == (1 + i)**2, strictly increasing
    assert len(materialized_list) == 20
    for idx, val in enumerate(materialized_list):
        orig_x = 1 + idx
        assert val == orig_x ** 2, f"Invariant broken: {val} != {orig_x}**2"
        assert val >= 0, f"Non-negative invariant broken: {val} < 0"
        assert int(math.isqrt(val)) == orig_x, f"Square root invariant broken for {val}"
        if idx > 0:
            assert val > materialized_list[idx - 1], f"Monotonicity invariant broken: {val} <= {materialized_list[idx - 1]}"
    print("Mathematical invariant strictly holds on published fixture: all y = x^2, monotonic, non-negative.")

    # 3. Test at Least Five Bounded Variations Where the Domain Permits
    print("\n[3] Testing bounded variations of the domain...")
    bounded_variations = [
        ("range(1, 2)", [1], "Smallest positive single-element domain {1}"),
        ("range(0, 1)", [0], "Zero boundary domain {0}"),
        ("range(1, 6)", [1, 4, 9, 16, 25], "Bounded domain [1, 5]"),
        ("range(10, 16)", [100, 121, 144, 169, 196, 225], "Bounded domain [10, 15]"),
        ("range(1, 1)", [], "Empty domain boundary {}"),
        ("range(-3, 4)", [9, 4, 1, 0, 1, 4, 9], "Negative to positive domain [-3, 3]"),
    ]

    for var_range, expected_vals, desc in bounded_variations:
        var_code = re.sub(r"range\(1,\s*21\)", var_range, code)
        assert var_range in var_code, f"Failed to substitute {var_range}"
        var_eval_code = var_code + f"\nprint(list(map(lambda x: x**2, {var_range})))\n"
        res_var = run_code(var_eval_code)
        assert res_var.returncode == 0, f"Variation {var_range} crashed: {res_var.stderr}"
        lines_var = res_var.stdout.strip().split("\n")
        actual_vals = ast.literal_eval(lines_var[-1])
        print(f"Domain: {var_range:14} | Expected: {str(expected_vals):32} | Actual: {str(actual_vals):32} | {desc}")
        assert actual_vals == expected_vals, f"Variation {var_range} mismatch: {actual_vals} != {expected_vals}"
        # Invariant check: all y >= 0
        for y in actual_vals:
            assert y >= 0, f"Invariant y >= 0 violated in {var_range}"
    print("All 6 bounded domain variations verified successfully.")

    # 4. Internal Deliberate Wrong-Result Self-Test
    print("\n[4] Running internal wrong-result self-test...")
    wrong_type = "list"
    if type_name == wrong_type:
        print("Self-test FAILED: accepted incorrect type 'list'!")
        sys.exit(1)
    print("Self-test PASSED: mismatch against wrong type correctly detected and rejected.")

    print("\nAll checks passed successfully! (exit code 0)")


if __name__ == "__main__":
    main()
