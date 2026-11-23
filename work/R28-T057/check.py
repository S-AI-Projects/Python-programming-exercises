#!/usr/bin/env python3
"""Check Question 21 in the Python 3 exercises markdown by executing its published code.

The example input/output, the solution block, the hints and the derivation are all extracted from
the markdown. The solution runs unmodified, fed through stdin; the only derived program is the
solution with one print(pos) added after its if/elif chain, used to read the intermediate states.

  python3 work/R28-T057/check.py                      # must exit 0
  python3 work/R28-T057/check.py --deliberate-wrong   # must exit non-zero
"""
import hashlib, json, math, platform, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "100+ Python challenging programming exercises for Python 3.md"
OUT = Path(__file__).resolve().parent
DELIBERATE_WRONG = "--deliberate-wrong" in sys.argv


def section(text, n):
    m = re.search(rf"^### Question {n}\n(.*?)(?=^### Question {n + 1}\n)", text, re.S | re.M)
    assert m, f"Question {n} not found"
    return m.group(1)


def run(code, stdin="", check=True):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
    return subprocess.run([sys.executable, "-I", f.name], input=stdin, capture_output=True, text=True, check=check)


def assert_printed(out, want):
    """Printed representation: the integer, no decimal point, one newline."""
    assert re.fullmatch(r"\d+\n", out), f"bad printed representation: {out!r}"
    assert out == want + "\n", f"printed {out!r}, expected {want + chr(10)!r}"


def oracle(lines):
    """Independent reference for expected values (not a copy of the article's code)."""
    x = y = 0
    for line in lines:
        d, n = line.split(" ")
        n = int(n)
        x += n if d == "UP" else -n if d == "DOWN" else 0
        y += n if d == "RIGHT" else -n if d == "LEFT" else 0
    return str(int(round(math.hypot(x, y))))


def main():
    text = MD.read_text(encoding="utf-8")
    body = section(text, 21)
    (solution,) = re.findall(r"```python\n(.*?)```", body, re.S)
    ex = re.search(r"input to the program:\n(.*?)\nThen, the output of the program should be:\n(.*?)\n\nHints:", body, re.S)
    assert ex, "published example not found"
    ex_lines, ex_out = ex.group(1).split("\n"), ex.group(2)
    assert ex_lines == ["UP 5", "DOWN 3", "LEFT 3", "RIGHT 2"] and ex_out == "2", (ex_lines, ex_out)
    want_example = "3" if DELIBERATE_WRONG else ex_out                 # the deliberate-wrong run expects 3
    (hint,) = re.findall(r"^The program reads lines until.*$", body, re.M)
    (axes,) = re.findall(r"^`pos\[0\]` is the vertical.*$", body, re.M)
    (deriv,) = re.findall(r"```\n(pos = \[0, 0\]\n.*?)```", body, re.S)
    plain = hint.replace("`", "")
    ev = {"source": MD.name, "md_sha256": hashlib.sha256(MD.read_bytes()).hexdigest(), "solution": solution, "cases": []}
    feed = lambda lines: "".join(l + "\n" for l in lines) + "\n"        # movements, then the terminating empty line

    # 1. Negative controls: the assertion rejects wrong values and representations.
    for bad in ("2", "2.0\n", "2 \n", "02\n", "3\n", "\n2\n", "2\n\n", "[2]\n", "-2\n"):
        try:
            assert_printed(bad, "2")
        except AssertionError:
            continue
        if not DELIBERATE_WRONG:
            raise SystemExit(f"checker accepted wrong output {bad!r}")
    try:                                                                # subprocess failures must propagate
        run("raise SystemExit(3)")
        raise SystemExit("subprocess failure was swallowed")
    except subprocess.CalledProcessError as e:
        assert e.returncode == 3

    # 2. The exact published example, unmodified code: value and printed representation.
    cp = run(solution, feed(ex_lines))
    assert cp.stderr == ""
    assert_printed(cp.stdout, want_example)
    ev["cases"].append({"input": repr(feed(ex_lines)), "expected": repr(want_example + "\n"), "actual": repr(cp.stdout)})

    # 3. Derivation: every state and operation in the article is what the code does.
    assert solution.count("    else:\n        pass\n") == 1, "published block changed; update the instrumentation"
    instrumented = solution.replace("    else:\n        pass\n", "    else:\n        pass\n    print(pos)\n")
    actual_states = run(instrumented, feed(ex_lines)).stdout.split("\n")
    states = [tuple(map(int, m)) for m in re.findall(r"^\[(-?\d+), (-?\d+)\]$", "\n".join(actual_states), re.M)]
    code_ops = {d: (int(i), sign) for d, i, sign in re.findall(r'direction=="(\w+)":\n\s+pos\[(\d)\]([+-])=steps', solution)}
    assert set(code_ops) == {"UP", "DOWN", "LEFT", "RIGHT"}, code_ops
    rows = re.findall(r"^(\w+) (\d+)\s+-> pos\[(\d)\] ([+-])= (\d+) -> \[(-?\d+), (-?\d+)\]$", deriv, re.M)
    assert len(rows) == len(ex_lines) == len(states) == 4, (rows, states)
    for line, (d, n, idx, sign, n2, a, b), st in zip(ex_lines, rows, states):
        assert f"{d} {n}" == line and n == n2, (line, d, n)
        assert code_ops[d] == (int(idx), sign), f"derivation says {d} -> pos[{idx}] {sign}=, code does {code_ops[d]}"
        assert (int(a), int(b)) == st, f"derivation state {(a, b)} != actual {st}"
    assert actual_states[:4] == ["[5, 0]", "[2, 0]", "[2, -3]", "[2, -1]"], actual_states
    final = re.search(r"sqrt\((-?\d+)\*\*2 \+ \((-?\d+)\)\*\*2\) = sqrt\((\d+)\) = ([\d.]+)\.\.\., which round\(\) turns into (\d+)$", deriv, re.M)
    assert final, deriv
    a, b, n, approx, rounded = final.groups()
    x, y = states[-1]
    assert (int(a), int(b)) == (x, y) and int(n) == x * x + y * y and str(math.sqrt(int(n))).startswith(approx) and rounded == ex_out
    assert "pos[0]` is the vertical position and `pos[1]` the horizontal" in axes
    ev["cases"].append({"input": "published example with print(pos) added after the if/elif chain",
                        "expected": "[5, 0], [2, 0], [2, -3], [2, -1], then 2", "actual": " | ".join(actual_states[:5])})

    # 4. Precondition from the hint: the program needs the terminating empty line.
    cp = run(solution, "".join(l + "\n" for l in ex_lines), check=False)         # input ends without an empty line
    assert cp.returncode != 0 and cp.stdout == "" and cp.stderr.strip().endswith("EOFError: EOF when reading a line"), cp
    for needle in ("end the input with an empty line", "raises EOFError", "just an empty line", "0 is printed", "capital letters", "any other word is ignored"):
        assert needle in plain, needle
    ev["cases"].append({"input": repr("".join(l + "\n" for l in ex_lines)) + " (no empty line)", "expected": "EOFError, nothing printed",
                        "actual": f"exit {cp.returncode}: {cp.stderr.strip().splitlines()[-1]}"})

    # 5. Smallest supported input and bounded variations (explicit values, then the independent oracle).
    for lines, want, why in (([], "0", "smallest: just an empty line"), (["UP 1"], "1", "single step"),
                             (["UP 3", "RIGHT 4"], "5", "exact 3-4-5, prints 5 not 5.0"), (["UP 1", "RIGHT 1"], "1", "sqrt(2)=1.41 rounds down"),
                             (["UP 2", "RIGHT 2"], "3", "sqrt(8)=2.83 rounds up"), (["LEFT 5"], "5", "negative axis, distance is positive"),
                             (["UP 5", "DOWN 5"], "0", "back at the origin"), (["UP 10", "DOWN 3", "LEFT 3", "RIGHT 2"], "7", "sqrt(50)=7.07"),
                             (["UP 5", "SIDEWAYS 7"], "5", "unknown direction ignored"), (["up 5"], "0", "lowercase direction ignored")):
        got = run(solution, feed(lines)).stdout
        assert_printed(got, want)
        assert want == oracle(lines), (lines, want, oracle(lines))
        ev["cases"].append({"input": repr(feed(lines)) + f"  # {why}", "expected": repr(want + "\n"), "actual": repr(got)})

    ev["tools"] = {"python": sys.version, "platform": platform.platform(),
                   "git": subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()}
    if not DELIBERATE_WRONG:
        (OUT / "evidence.json").write_text(json.dumps(ev, indent=2) + "\n")
    print("OK: Question 21 checks passed")


if __name__ == "__main__":
    main()
