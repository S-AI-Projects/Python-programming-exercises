#!/usr/bin/env python3
"""Check Question 79 in the Python 3 exercises markdown by executing its published code.

The solution, alternative, hint and output example are extracted from the markdown and run
with the real interpreter; nothing is validated from a retyped copy.

  python3 work/R28-T053/check.py                      # must exit 0
  python3 work/R28-T053/check.py --deliberate-wrong   # must exit non-zero
"""
import ast, hashlib, json, platform, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "100+ Python challenging programming exercises for Python 3.md"
OUT = Path(__file__).resolve().parent
EVENS = [i for i in range(100, 201) if i % 2 == 0]   # spec fixture: even numbers 100..200 inclusive
SEEDS = range(100)
DELIBERATE_WRONG = "--deliberate-wrong" in sys.argv
K = 6 if DELIBERATE_WRONG else 5                      # the deliberate-wrong run expects 6 numbers
FORMAT = rf"\[\d+(?:, \d+){{{K - 1}}}\]\n"            # printed list repr, newline-terminated


def section(text, n):
    m = re.search(rf"^### Question {n}\n(.*?)(?=^### Question {n + 1}\n)", text, re.S | re.M)
    assert m, f"Question {n} not found"
    return m.group(1)


def run(code, seed, check=True):
    """Run code in a fresh interpreter after seeding; failures propagate when check=True."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(f"import random; random.seed({seed})\n{code}")
    return subprocess.run([sys.executable, f.name], capture_output=True, text=True, check=check)


def assert_printed(out, allowed):
    """Printed representation + stated property: list of K distinct allowed ints."""
    assert re.fullmatch(FORMAT, out), f"bad printed representation: {out!r}"
    vals = ast.literal_eval(out)
    assert isinstance(vals, list) and len(vals) == K and all(type(v) is int for v in vals), out
    assert all(v in allowed for v in vals), f"value not allowed: {out!r}"
    assert len(set(vals)) == len(vals), f"repeated value: {out!r}"
    return vals


def main():
    text = MD.read_text(encoding="utf-8")
    body = section(text, 79)
    solution, alt = re.findall(r"```python\n(.*?)```", body, re.S)
    (example,) = re.findall(r"^Output[^\n]*\n```\n(.*?)```", body, re.S | re.M)
    (hint,) = re.findall(r"^random\.sample\(\) picks.*$", body, re.M)
    ev = {"source": MD.name, "md_sha256": hashlib.sha256(MD.read_bytes()).hexdigest(),
          "solution": solution, "alternative": alt, "cases": []}
    allowed = set(EVENS)

    # 1. Negative controls: the assertion helper rejects wrong representations/values.
    bads = ["(104, 106, 108, 110, 112)\n", "[104, 104, 106, 108, 110]\n", "[101, 102, 104, 106, 108]\n",
            "[104,106,108,110,112]\n", "[104, 106, 108, 110]\n", "[104, 106, 108, 110, 112]",
            "[104, 106, 108, 110, 202]\n", "['104', '106', '108', '110', '112']\n"]
    for bad in bads:
        try:
            assert_printed(bad, allowed)
        except AssertionError:
            continue
        if not DELIBERATE_WRONG:
            raise SystemExit(f"checker accepted wrong output {bad!r}")
    try:                                                # subprocess failures must propagate
        run("raise SystemExit(3)", 0)
        raise SystemExit("subprocess failure was swallowed")
    except subprocess.CalledProcessError as e:
        assert e.returncode == 3

    # 2. Hint's count matches the fixture.
    assert str(len(EVENS)) == "51" and re.search(r"\b51 even numbers\b", hint), hint
    assert "ValueError" in hint

    # 3. Execute the published solution: printed form + stated property; example is real output.
    outs = {s: run(solution, s).stdout for s in SEEDS}
    for out in outs.values():
        assert_printed(out, allowed)
    assert example in set(outs.values()), "output example is not an output of the published code"
    assert len({v for o in outs.values() for v in ast.literal_eval(o)}) > 40   # draws from the whole fixture
    ev["cases"].append({"input": "published solution, seeds 0-99", "expected": "list of 5 distinct even ints in [100,200], printed as a list repr + newline",
                        "actual_sample": [outs[0], outs[1]]})

    # 4. Smallest supported population, derived from the published block: exactly 5 evens -> all 5 returned.
    assert solution.count("range(100,201)") == 1, "published block changed; update the derivation"
    small = solution.replace("range(100,201)", "range(100,109)")          # evens: 100,102,104,106,108
    orders = set()
    for s in SEEDS:
        vals = assert_printed(run(small, s).stdout, {100, 102, 104, 106, 108})
        assert sorted(vals) == [100, 102, 104, 106, 108], vals
        orders.add(tuple(vals))
    assert len(orders) > 1, "order should still be random"
    ev["cases"].append({"input": "range(100,109): 5 evens, k=5", "expected": "a permutation of [100,102,104,106,108]",
                        "actual": run(small, 0).stdout, "distinct_orders_seen": len(orders)})

    # 5. Precondition: one fewer candidate (4 evens < k=5) makes this sample() call fail with ValueError.
    p = run(solution.replace("range(100,201)", "range(100,107)"), 0, check=False)
    assert p.returncode != 0 and "ValueError" in p.stderr, (p.returncode, p.stderr)
    ev["cases"].append({"input": "range(100,107): 4 evens, k=5", "expected": "non-zero exit, ValueError",
                        "actual": f"exit {p.returncode}: {p.stderr.strip().splitlines()[-1]}"})

    # 6. Alternative on the same fixture: same property, same populations, different intermediate objects.
    assert list(range(100, 201, 2)) == EVENS
    scanned, kept = len(range(100, 201)), len(EVENS)
    assert (scanned, kept, len(range(100, 201, 2))) == (101, 51, 51)
    same_seed = 0
    for s in SEEDS:
        a = run(alt, s).stdout
        assert_printed(a, allowed)
        same_seed += (a == outs[s])
    assert same_seed == len(SEEDS), f"only {same_seed} same-seed matches"   # observed on this runtime
    ev["cases"].append({"input": "alternative random.sample(range(100,201,2), 5), seeds 0-99",
                        "expected": "same property; source scans 101 numbers and keeps 51 in a list, alternative is a step-2 range of 51",
                        "actual": f"{same_seed}/{len(SEEDS)} seeds print the same list as the source"})

    ev["tools"] = {"python": sys.version, "platform": platform.platform(),
                   "git": subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()}
    if not DELIBERATE_WRONG:
        (OUT / "evidence.json").write_text(json.dumps(ev, indent=2) + "\n")
    print("OK: Question 79 checks passed")


if __name__ == "__main__":
    main()
