#!/usr/bin/env python3
"""Check Question 29 in the Python 3 exercises markdown by executing its published code.

The solution block, the call's output comment and the hint are extracted from the markdown and run
with the real interpreter; variations are derived from the published function, not retyped.

Invariant: for strings a, b that int() accepts, printValue(a, b) prints exactly the decimal
text of int(a) + int(b) followed by one newline (not a + b), and returns None.

  python3 work/R28-T054/check.py                      # must exit 0
  python3 work/R28-T054/check.py --deliberate-wrong   # must exit non-zero
"""
import hashlib, json, platform, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "100+ Python challenging programming exercises for Python 3.md"
OUT = Path(__file__).resolve().parent
DELIBERATE_WRONG = "--deliberate-wrong" in sys.argv
# The deliberate-wrong run expects string concatenation (the Question 30 behaviour) instead of a sum.
expected_out = (lambda a, b: a + b + "\n") if DELIBERATE_WRONG else (lambda a, b: f"{int(a) + int(b)}\n")


def section(text, n):
    m = re.search(rf"^### Question {n}\n(.*?)(?=^### Question {n + 1}\n)", text, re.S | re.M)
    assert m, f"Question {n} not found"
    return m.group(1)


def run(code, check=True):
    """Run code in a fresh interpreter; failures propagate when check=True."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
    return subprocess.run([sys.executable, f.name], capture_output=True, text=True, check=check)


def assert_sum(out, a, b):
    assert out == expected_out(a, b), f"printValue({a!r}, {b!r}) printed {out!r}, expected {expected_out(a, b)!r}"


def main():
    text = MD.read_text(encoding="utf-8")
    body = section(text, 29)
    (solution,) = re.findall(r"```python\n(.*?)```", body, re.S)
    (comment,) = re.findall(r'^printValue\("3","4"\) #(\S+)$', solution, re.M)
    (hint,) = re.findall(r"^The function should print the sum.*$", body, re.M)
    defn = solution.split("\nprintValue(")[0]               # the published function definition
    call = lambda a, b: f"{defn}\nprintValue({a!r}, {b!r})\n"
    ev = {"source": MD.name, "md_sha256": hashlib.sha256(MD.read_bytes()).hexdigest(),
          "solution": solution, "cases": []}

    # 1. Negative controls: the assertion rejects wrong printed representations.
    for bad in ("34\n", "7", "7 \n", "7.0\n", "'7'\n", "07\n", " 7\n", "7\n\n", "[7]\n"):
        try:
            assert_sum(bad, "3", "4")
        except AssertionError:
            continue
        if not DELIBERATE_WRONG:
            raise SystemExit(f"checker accepted wrong output {bad!r}")
    try:                                                     # subprocess failures must propagate
        run("raise SystemExit(3)")
        raise SystemExit("subprocess failure was swallowed")
    except subprocess.CalledProcessError as e:
        assert e.returncode == 3

    # 2. The exact published example: value, printed form, and the published output comment.
    out = run(solution).stdout
    assert_sum(out, "3", "4")
    assert out == "7\n" or DELIBERATE_WRONG
    assert comment == "7" and out == comment + "\n", (comment, out)
    ev["cases"].append({"input": 'printValue("3","4") (published block, unchanged)', "expected": "'7\\n'", "actual": repr(out)})

    # 3. Prints rather than returns: the call's value is None.
    r = run(f'{defn}\nprint(printValue("3","4"))\n').stdout
    assert r == "7\nNone\n", r

    # 4. Smallest supported input plus bounded variations (explicit expected values, then the invariant).
    variations = [("0", "0", "0\n", "smallest supported input"),
                  ("-3", "4", "1\n", "negative sign"),
                  ("-5", "5", "0\n", "sum zero prints 0, not -0"),
                  ("+5", "6", "11\n", "plus sign"),
                  ("007", "3", "10\n", "leading zeros"),
                  (" 3 ", " 4 ", "7\n", "surrounding spaces"),
                  ("99999999999999999999", "1", "100000000000000000000\n", "beyond 64-bit, no overflow"),
                  ("1_000", "1", "1001\n", "underscore digit separator")]
    for a, b, want, why in variations:
        got = run(call(a, b)).stdout
        assert got == want or DELIBERATE_WRONG, (a, b, got, want)
        assert_sum(got, a, b)
        ev["cases"].append({"input": f"printValue({a!r}, {b!r})  # {why}", "expected": repr(want), "actual": repr(got)})
    assert run(call("-3", " 4 ")).stdout == "1\n"           # the hint's own examples
    assert len(variations) >= 5

    # 5. Bounded sweep -9..9 x -9..9: invariant holds for every pair.
    for x in range(-9, 10, 3):
        for y in range(-9, 10, 3):
            assert_sum(run(call(str(x), str(y))).stdout, str(x), str(y))
    ev["cases"].append({"input": "sweep a,b in {-9,-6,...,9} (49 pairs)", "expected": "str(int(a)+int(b)) + newline", "actual": "all equal"})

    # 6. Hint claims: sum not concatenation, and int() rejects non-integral text.
    assert 'print 7, not 34' in hint and "ValueError" in hint
    for a, b in (("3.5", "4"), ("", "1")):
        p = run(call(a, b), check=False)
        assert p.returncode != 0 and "ValueError" in p.stderr, (a, b, p.returncode, p.stderr)
        ev["cases"].append({"input": f"printValue({a!r}, {b!r})", "expected": "non-zero exit, ValueError",
                            "actual": f"exit {p.returncode}: {p.stderr.strip().splitlines()[-1]}"})

    ev["tools"] = {"python": sys.version, "platform": platform.platform(),
                   "git": subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()}
    if not DELIBERATE_WRONG:
        (OUT / "evidence.json").write_text(json.dumps(ev, indent=2) + "\n")
    print("OK: Question 29 checks passed")


if __name__ == "__main__":
    main()
