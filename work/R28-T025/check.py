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

    # Extract Question 68 section
    q_match = re.search(r"### Question 68\n(.*?)(?=### Question 69)", content, re.S)
    if not q_match:
        print("Error: Question 68 not found in markdown file")
        sys.exit(1)

    sec = q_match.group(1)
    code_match = re.search(r"Solution:\s*```python\n(.*?)```", sec, re.S)
    if not code_match:
        print("Error: Question 68 solution code block not found")
        sys.exit(1)

    return code_match.group(1).strip()


def run_code(code, input_str):
    fd, tmp_file = tempfile.mkstemp(prefix="check_q68_", suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        res = subprocess.run(
            [sys.executable, tmp_file],
            input=input_str,
            capture_output=True,
            text=True
        )
        return res
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)


def main():
    parser = argparse.ArgumentParser(description="Automated checker for Question 68")
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
        res = run_code(code, "10\n")
        assert res.returncode == 0
        actual = res.stdout.strip()
        deliberate_wrong = "1,3,5,7,9"
        print(f"Input: '10' | Actual: {actual!r} | Deliberate Wrong Expected: {deliberate_wrong!r}")
        assert actual == deliberate_wrong, f"DELIBERATE FAILURE TRIGGERED: Output {actual!r} did not match wrong expectation {deliberate_wrong!r}"
        print("Error: Deliberate failure should have raised an AssertionError!")
        sys.exit(1)

    # 1. Test Published Example (input: 10, expected: 0,2,4,6,8,10)
    print("\n[1] Testing published example (input: 10)...")
    res_pub = run_code(code, "10\n")
    if res_pub.returncode != 0:
        print("Execution crashed on published input 10!")
        print("stderr:", res_pub.stderr)
        sys.exit(1)

    expected_pub_str = "0,2,4,6,8,10\n"
    actual_pub_str = res_pub.stdout
    print(f"Published Expected: {expected_pub_str!r}")
    print(f"Published Actual:   {actual_pub_str!r}")
    assert actual_pub_str == expected_pub_str, f"Mismatch: expected {expected_pub_str!r}, got {actual_pub_str!r}"

    # Also assert underlying integer list values
    actual_vals = [int(x) for x in actual_pub_str.strip().split(",")]
    expected_vals = [0, 2, 4, 6, 8, 10]
    assert actual_vals == expected_vals, f"Value mismatch: {actual_vals} != {expected_vals}"
    print("Published example verified successfully (both string representation and parsed values).")

    # 2. Test Smallest Supported Inputs (n = 0 and n = 1)
    print("\n[2] Testing smallest supported inputs (n = 0 and n = 1)...")
    # n = 0 -> output "0\n"
    res_0 = run_code(code, "0\n")
    assert res_0.returncode == 0, f"n=0 crashed: {res_0.stderr}"
    print(f"Input 0 Expected: '0\\n' | Actual: {res_0.stdout!r}")
    assert res_0.stdout == "0\n"

    # n = 1 -> output "0\n" (1 is odd)
    res_1 = run_code(code, "1\n")
    assert res_1.returncode == 0, f"n=1 crashed: {res_1.stderr}"
    print(f"Input 1 Expected: '0\\n' | Actual: {res_1.stdout!r}")
    assert res_1.stdout == "0\n"
    print("Smallest supported inputs verified successfully.")

    # 3. Test Additional Bounded Variations
    print("\n[3] Testing additional bounded variations (n = 2, 5, 12)...")
    test_cases = [
        (2, "0,2\n", [0, 2]),
        (5, "0,2,4\n", [0, 2, 4]),
        (12, "0,2,4,6,8,10,12\n", [0, 2, 4, 6, 8, 10, 12]),
    ]
    for inp_n, exp_str, exp_lst in test_cases:
        res = run_code(code, f"{inp_n}\n")
        assert res.returncode == 0, f"Input {inp_n} crashed: {res.stderr}"
        act_str = res.stdout
        print(f"Input {inp_n:2} Expected: {exp_str.strip():20} | Actual: {act_str.strip():20}")
        assert act_str == exp_str, f"Mismatch for n={inp_n}: expected {exp_str!r}, got {act_str!r}"
        parsed = [int(x) for x in act_str.strip().split(",")]
        assert parsed == exp_lst, f"List mismatch for n={inp_n}: {parsed} != {exp_lst}"
    print("All bounded variations verified successfully.")

    # 4. Internal Deliberate Wrong-Result Self-Test
    print("\n[4] Running internal wrong-result self-test...")
    wrong_pub = "0,1,2,3,4,5,6,7,8,9,10\n"
    if actual_pub_str == wrong_pub:
        print("Self-test FAILED: accepted incorrect expected output!")
        sys.exit(1)
    print("Self-test PASSED: mismatch against wrong expectation correctly detected and rejected.")

    print("\nAll checks passed successfully! (exit code 0)")


if __name__ == "__main__":
    main()
