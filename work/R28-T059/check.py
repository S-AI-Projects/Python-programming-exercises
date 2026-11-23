#!/usr/bin/env python3
"""
R28-T059 check: extract and execute the published Question 100 solution
from the markdown source, assert the expected results, and fail on a
deliberate wrong result. Propagates subprocess failures.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "100+ Python challenging programming exercises for Python 3.md"
OUT_DIR = Path(__file__).resolve().parent

EXPECTED_PUBLISHED = "(23, 12)\n"
EXPECTED_SMALLEST = "(1, 0)\n"


def extract_solve_source() -> str:
    text = MD.read_text(encoding="utf-8")
    # Locate Question 100 solution fence
    m = re.search(
        r"### Question 100\b.*?Solution:\s*```python\n(.*?)```",
        text,
        re.DOTALL,
    )
    if not m:
        raise AssertionError("Could not locate Question 100 solution code fence in the markdown")
    src = m.group(1)
    # Sanity: must contain the solve definition
    if "def solve(numheads,numlegs):" not in src:
        raise AssertionError("Extracted block does not contain the expected solve definition")
    return src


def run_snippet(code: str, extra: str = "") -> str:
    """Execute the extracted source (or a variant) and return stdout."""
    full = code + "\n" + extra
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(full)
        path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            print("STDERR:", proc.stderr, file=sys.stderr)
            proc.check_returncode()  # propagate
        return proc.stdout
    finally:
        os.unlink(path)


def main() -> int:
    versions = {
        "python": sys.version,
        "executable": sys.executable,
    }
    (OUT_DIR / "versions.txt").write_text(
        "\n".join(f"{k}: {v}" for k, v in versions.items()) + "\n",
        encoding="utf-8",
    )

    src = extract_solve_source()
    (OUT_DIR / "extracted_source.py").write_text(src, encoding="utf-8")

    # 1. Exact published example
    out = run_snippet(src)
    (OUT_DIR / "published_actual.txt").write_text(out, encoding="utf-8")
    (OUT_DIR / "published_expected.txt").write_text(EXPECTED_PUBLISHED, encoding="utf-8")
    assert out == EXPECTED_PUBLISHED, (
        f"Published example mismatch:\nexpected {EXPECTED_PUBLISHED!r}\nactual   {out!r}"
    )
    print("PASS: published example (35, 94) -> (23, 12)")

    # 2. Smallest supported non-negative input
    smallest_driver = """
numheads=1
numlegs=2
solutions=solve(numheads,numlegs)
print(solutions)
"""
    # Strip the original driver so we only keep the function
    func_only = re.sub(
        r"\nnumheads=35\nnumlegs=94\nsolutions=solve\(numheads,numlegs\)\nprint\(solutions\)\s*",
        "\n",
        src,
    )
    out_s = run_snippet(func_only, smallest_driver)
    (OUT_DIR / "smallest_actual.txt").write_text(out_s, encoding="utf-8")
    (OUT_DIR / "smallest_expected.txt").write_text(EXPECTED_SMALLEST, encoding="utf-8")
    assert out_s == EXPECTED_SMALLEST, (
        f"Smallest input mismatch:\nexpected {EXPECTED_SMALLEST!r}\nactual   {out_s!r}"
    )
    print("PASS: smallest supported input (1, 2) -> (1, 0)")

    # 3. Deliberate wrong result must fail the assertion (self-check)
    wrong_expected = "(0, 0)\n"
    try:
        assert out == wrong_expected
        print("ERROR: deliberate wrong assertion did not fire", file=sys.stderr)
        return 1
    except AssertionError:
        print("PASS: deliberate wrong result correctly rejected")

    # 4. Structural property of the extracted function (no-input demonstration)
    #    Assert that solve is a function object with the expected arity.
    ns: dict = {}
    exec(func_only, ns)
    solve = ns["solve"]
    assert callable(solve), "solve is not callable"
    assert solve.__code__.co_argcount == 2, "solve must take exactly two parameters"
    print("PASS: solve is a 2-arg callable (type/property assertion)")

    # Record intermediate observation used in the scaling note
    (OUT_DIR / "observation.txt").write_text(
        "Loop bound for published example: range(35+1) -> at most 36 iterations\n"
        "Loop bound for smallest input: range(1+1) -> at most 2 iterations\n"
        "Extra space: O(1) (only scalar integers i, j and the ns string)\n",
        encoding="utf-8",
    )

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
