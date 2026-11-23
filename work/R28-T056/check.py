#!/usr/bin/env python3
"""Check Question 48 in the Python 3 exercises markdown by executing its published code.

The solution block and hint are extracted from the markdown and run with the real interpreter;
variations are derived from the published block, not retyped. When the pinned base commit is
available in git, the original (pre-change) block is read from it and compared.

Stated property (from the question): the program prints a list of the even numbers from 1 to 20,
both included, in Python's list notation: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20].

  python3 work/R28-T056/check.py                      # must exit 0
  python3 work/R28-T056/check.py --deliberate-wrong   # must exit non-zero
"""
import ast, hashlib, json, platform, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "100+ Python challenging programming exercises for Python 3.md"
OUT = Path(__file__).resolve().parent
PIN = "d6e381fa6090469e59b7d54dc0cbbabf46450fc5"
DELIBERATE_WRONG = "--deliberate-wrong" in sys.argv
# Question text: even numbers between 1 and 20, both included. The deliberate-wrong run expects the odd ones.
SPEC = [x for x in range(1, 21) if (x % 2 == 1 if DELIBERATE_WRONG else x % 2 == 0)]


def section(text, n):
    m = re.search(rf"^### Question {n}\n(.*?)(?=^### Question {n + 1}\n)", text, re.S | re.M)
    assert m, f"Question {n} not found"
    return m.group(1)


def run(code, check=True):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
    return subprocess.run([sys.executable, "-I", f.name], capture_output=True, text=True, check=check)


def assert_list_output(out, want):
    """Printed representation + type + property: Python list repr of ints, newline-terminated."""
    assert re.fullmatch(r"\[(\d+(, \d+)*)?\]\n", out), f"bad printed representation: {out!r}"
    vals = ast.literal_eval(out)
    assert type(vals) is list and all(type(v) is int for v in vals), out
    assert vals == want, f"{vals} != {want}"
    assert out == str(want) + "\n"


def main():
    text = MD.read_text(encoding="utf-8")
    body = section(text, 48)
    (solution,) = re.findall(r"```python\n(.*?)```", body, re.S)
    (comment,) = re.findall(r"^print\(list\(evenNumbers\)\) #(\[.*\])$", solution, re.M)
    (hint,) = re.findall(r"^In Python 3, .*$", body, re.M)
    plain = hint.replace("`", "")
    core = re.sub(r" #\[.*\]$", "", solution, flags=re.M)             # published code without its output comment
    assign = core.splitlines()[0]
    assert assign == "evenNumbers = filter(lambda x: x%2==0, range(1,21))", assign
    ev = {"source": MD.name, "md_sha256": hashlib.sha256(MD.read_bytes()).hexdigest(), "solution": solution, "cases": []}

    # 1. Negative controls: the assertion rejects wrong representations/values.
    good = str(SPEC) + "\n"
    for bad in ("<filter object at 0x7f0000000000>\n", good.rstrip("\n"), good.replace(", ", ","), "(" + good[1:-2] + ")\n",
                str([1] + SPEC) + "\n", str(SPEC[:-1]) + "\n", str(SPEC + [22]) + "\n", str([str(x) for x in SPEC]) + "\n"):
        try:
            assert_list_output(bad, SPEC)
        except AssertionError:
            continue
        if not DELIBERATE_WRONG:
            raise SystemExit(f"checker accepted wrong output {bad!r}")
    try:                                                              # subprocess failures must propagate
        run("raise SystemExit(3)")
        raise SystemExit("subprocess failure was swallowed")
    except subprocess.CalledProcessError as e:
        assert e.returncode == 3

    # 2. The published example: value, type and printed representation; matches the output comment.
    out = run(solution).stdout
    assert_list_output(out, SPEC)
    assert out == comment + "\n" or DELIBERATE_WRONG, (out, comment)
    ev["cases"].append({"input": "published block (range(1,21))", "expected": repr(good), "actual": repr(out)})

    # 3. What the code printed before the change: a filter object (address varies), not the numbers.
    old = run(core.replace("print(list(evenNumbers))", "print(evenNumbers)")).stdout
    assert re.fullmatch(r"<filter object at 0x[0-9a-fA-F]+>\n", old), old
    assert "2, 4" not in old
    try:
        orig = subprocess.run(["git", "-C", str(ROOT), "show", f"{PIN}:{MD.name}"], capture_output=True, text=True, check=True).stdout
        orig_block = re.findall(r"```python\n(.*?)```", section(orig, 48), re.S)[0]
        assert orig_block == core.replace("print(list(evenNumbers))", "print(evenNumbers)"), "derived original differs from the pinned original"
        pinned = "pinned original compared"
    except subprocess.CalledProcessError:
        pinned = "pinned commit not available; derived original used"
    ev["cases"].append({"input": "original block: print(evenNumbers)", "expected": "<filter object at 0x...>", "actual": old.strip(), "note": pinned})

    # 4. Exact intermediate values: lazy iterator, one element at a time, then the rest.
    steps = run(assign + "\nprint(type(evenNumbers).__name__)\nprint(next(evenNumbers))\nprint(next(evenNumbers))\nprint(list(evenNumbers))\n").stdout
    assert steps == "filter\n2\n4\n[6, 8, 10, 12, 14, 16, 18, 20]\n", steps
    ev["cases"].append({"input": "assignment line, then next(), next(), list()", "expected": "filter, 2, 4, [6..20]", "actual": steps})

    # 5. Work done: nothing is checked until the values are read; then 20 checks, 10 kept; iterator is single-use.
    counting = assign.replace("lambda x: x%2==0", "lambda x: (calls.append(x), x%2==0)[1]")
    assert counting != assign
    work = run("calls = []\n" + counting + "\nprint(len(calls))\nresult = list(evenNumbers)\n"
               "print(calls == list(range(1, 21)), len(calls), len(result))\nprint(list(evenNumbers))\n").stdout
    assert work == "0\nTrue 20 10\n[]\n", work
    for needle in ("returns an iterator, not a list", "<filter object at 0x...>", "20 numbers from 1 to 20", "10 even ones", "gives []"):
        assert needle in plain, needle
    ev["cases"].append({"input": "counting lambda: before list(), after list(), second list()", "expected": "0 checks; 20 checks, 10 kept; []", "actual": work})

    # 6. Smallest supported input and boundaries (stop 21 is exclusive; 20 included, 1 excluded).
    assert core.count("range(1,21)") == 1, "published block changed; update the derivation"
    for args, want in (("1,1", []), ("1,2", []), ("2,3", [2]), ("1,3", [2]), ("20,21", [20]), ("1,22", list(range(2, 21, 2)))):
        o = run(core.replace("range(1,21)", f"range({args})")).stdout
        lo, hi = (int(v) for v in args.split(","))
        assert_list_output(o, want)
        assert want == [x for x in range(lo, hi) if x % 2 == 0]       # the stated property for this range
        ev["cases"].append({"input": f"range({args})", "expected": str(want), "actual": o.strip()})

    ev["tools"] = {"python": sys.version, "platform": platform.platform(),
                   "git": subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()}
    if not DELIBERATE_WRONG:
        (OUT / "evidence.json").write_text(json.dumps(ev, indent=2) + "\n")
    print("OK: Question 48 checks passed")


if __name__ == "__main__":
    main()
