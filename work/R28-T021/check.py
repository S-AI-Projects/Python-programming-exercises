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

    # Extract Question 43 section
    q_match = re.search(r"### Question 43\n(.*?)(?=### Question 44)", content, re.S)
    if not q_match:
        print("Error: Question 43 not found in markdown file")
        sys.exit(1)

    sec = q_match.group(1)
    code_match = re.search(r"Solution\s*```python\n(.*?)```", sec, re.S)
    if not code_match:
        print("Error: Question 43 solution code block not found")
        sys.exit(1)

    return code_match.group(1).strip()


def run_code(code):
    fd, tmp_file = tempfile.mkstemp(prefix="check_q43_", suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        res = subprocess.run([sys.executable, tmp_file], capture_output=True, text=True)
        return res
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)


def main():
    print(f"Reading solution from: {md_path}")
    code = get_solution_code(md_path)
    print("Extracted code:\n---")
    print(code)
    print("---")

    # 1. Run published example and assert output
    print("\n[1] Running published example...")
    res = run_code(code)
    if res.returncode != 0:
        print("Execution failed!")
        print("stderr:", res.stderr)
        sys.exit(1)

    expected_output = "(2, 4, 6, 8, 10)\n"
    actual_output = res.stdout
    print("Expected stdout:", repr(expected_output))
    print("Actual stdout:  ", repr(actual_output))
    assert actual_output == expected_output, f"Output mismatch: {actual_output!r} != {expected_output!r}"

    evaluated_val = ast.literal_eval(actual_output.strip())
    assert evaluated_val == (2, 4, 6, 8, 10), f"Evaluated value mismatch: {evaluated_val}"
    print("Published example verified successfully.")

    # 2. Test smallest supported inputs
    print("\n[2] Testing smallest supported inputs...")
    # 2a. Smallest single even element: (2,)
    small_even_code = re.sub(r"tp\s*=\s*\(.*?\)", "tp=(2,)", code, count=1)
    assert "tp=(2,)" in small_even_code, "Failed to substitute small even input"
    res_even = run_code(small_even_code)
    assert res_even.returncode == 0, f"Small even input crashed: {res_even.stderr}"
    print("Small even input expected: '(2,)\\n'")
    print("Small even input actual:  ", repr(res_even.stdout))
    assert res_even.stdout == "(2,)\n"
    assert ast.literal_eval(res_even.stdout.strip()) == (2,)

    # 2b. Smallest single odd element: (1,)
    small_odd_code = re.sub(r"tp\s*=\s*\(.*?\)", "tp=(1,)", code, count=1)
    assert "tp=(1,)" in small_odd_code, "Failed to substitute small odd input"
    res_odd = run_code(small_odd_code)
    assert res_odd.returncode == 0, f"Small odd input crashed: {res_odd.stderr}"
    print("Small odd input expected: '()\\n'")
    print("Small odd input actual:  ", repr(res_odd.stdout))
    assert res_odd.stdout == "()\n"
    assert ast.literal_eval(res_odd.stdout.strip()) == ()
    print("Smallest supported inputs verified successfully.")

    # 3. Mutant test / bug detection
    print("\n[3] Testing bug detection on original buggy snippet...")
    # The original buggy snippet used tp[i] % 2 == 0 with index out of bounds
    buggy_code = code.replace("if i%2==0:\n\t\tli.append(i)", "if tp[i]%2==0:\n\t\tli.append(tp[i])")
    assert buggy_code != code, "Failed to construct buggy mutant"
    buggy_res = run_code(buggy_code)
    if buggy_res.returncode == 0:
        print("Buggy code surprisingly succeeded!")
        sys.exit(1)
    print("Buggy code correctly failed with non-zero exit code (IndexError caught).")

    # Mutant test: changing condition to odd numbers
    odd_mutant_code = code.replace("i%2==0", "i%2!=0")
    assert odd_mutant_code != code, "Failed to construct odd mutant"
    odd_res = run_code(odd_mutant_code)
    assert odd_res.returncode == 0
    odd_val = ast.literal_eval(odd_res.stdout.strip())
    print("Odd mutant output:", odd_val)
    if odd_val == (2, 4, 6, 8, 10):
        print("Mutant survived!")
        sys.exit(1)
    print("Odd mutant successfully killed.")

    # 4. Deliberate wrong-result check
    print("\n[4] Deliberate wrong-result check...")
    wrong_expected = "(2, 4, 6, 8)\n"
    if actual_output == wrong_expected:
        print("Deliberate wrong result check failed: accepted mismatch!")
        sys.exit(1)
    print("Deliberate wrong result correctly detected and rejected.")

    print("\nAll checks passed successfully!")


if __name__ == "__main__":
    main()
