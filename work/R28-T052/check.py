#!/usr/bin/env python3
"""Check Question 77 in the Python 3 exercises markdown by executing its published code.

Nothing here is a retyped copy of the article: the solution block, hint line and
output example are extracted from the markdown file and run with the real interpreter.

  python3 work/R28-T052/check.py                  # must exit 0
  python3 work/R28-T052/check.py --deliberate-wrong   # must exit non-zero
"""
import hashlib, json, platform, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "100+ Python challenging programming exercises for Python 3.md"
OUT = Path(__file__).resolve().parent
CANDIDATES = [i for i in range(201) if i % 5 == 0 and i % 7 == 0]  # spec: multiples of 5 and 7 in 0..200
SEEDS = range(100)
DELIBERATE_WRONG = "--deliberate-wrong" in sys.argv
# Printed representation: one bare integer + newline (the deliberate-wrong run expects a list instead).
FORMAT = r"\[\d+\]\n" if DELIBERATE_WRONG else r"\d+\n"


def section(text, n):
    m = re.search(rf"^### Question {n}\n(.*?)(?=^### Question {n + 1}\n)", text, re.S | re.M)
    assert m, f"Question {n} not found"
    return m.group(1)


def fences(body, lang):
    return re.findall(rf"```{lang}\n(.*?)```", body, re.S)


def run(code, seed):
    """Run code in a fresh interpreter after seeding; subprocess failures propagate (check=True)."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(f"import random; random.seed({seed})\n{code}")
    return subprocess.run([sys.executable, f.name], capture_output=True, text=True, check=True).stdout


def assert_printed(out, allowed):
    assert re.fullmatch(FORMAT, out), f"bad printed representation: {out!r}"
    assert int(re.search(r"\d+", out).group()) in allowed, f"value not allowed: {out!r}"


def main():
    text = MD.read_text(encoding="utf-8")
    body = section(text, 77)
    (solution,) = fences(body, "python")
    (example,) = re.findall(r"^Output[^\n]*\n```\n(.*?)```", body, re.S | re.M)
    (hint,) = re.findall(r"^A number divisible by both.*$", body, re.M)
    evidence = {"source": str(MD.name), "md_sha256": hashlib.sha256(MD.read_bytes()).hexdigest(),
                "solution": solution, "cases": []}

    # 1. Negative controls: the assertion helper rejects wrong representations/values.
    for bad in ("[105]\n", "'105'\n", "105", "105 \n", "100\n", "-35\n"):
        try:
            assert_printed(bad, CANDIDATES)
        except AssertionError:
            continue
        if not DELIBERATE_WRONG:
            raise SystemExit(f"checker accepted wrong output {bad!r}")
    # subprocess failures must propagate
    try:
        run("raise SystemExit(3)", 0)
        raise SystemExit("subprocess failure was swallowed")
    except subprocess.CalledProcessError as e:
        assert e.returncode == 3

    # 2. Hint lists exactly the candidates; published output example is a valid output.
    listed = [int(x) for x in re.findall(r"\d+", hint.split("are", 1)[1].split(".")[0])]
    assert listed == CANDIDATES, (listed, CANDIDATES)
    assert_printed(example, CANDIDATES)

    # 3. Execute the published solution: value + printed representation, all candidates reachable.
    seen = set()
    for s in SEEDS:
        out = run(solution, s)
        assert_printed(out, CANDIDATES)
        seen.add(int(out))
    assert seen == set(CANDIDATES), seen
    evidence["cases"].append({"input": "published solution, seeds 0-99", "expected": f"one of {CANDIDATES}, format \\d+\\n",
                              "actual_values_seen": sorted(seen), "sample_actual": repr(run(solution, 0))})

    # 4. Smallest case, derived from the published block (bound 200 -> 0): only candidate is 0.
    assert solution.count("range(201)") == 1, "published block changed; update the boundary derivation"
    small = solution.replace("range(201)", "range(1)")
    for s in SEEDS:
        assert run(small, s) == "0\n", s
    evidence["cases"].append({"input": "range(1) (upper bound 0), seeds 0-99", "expected": "'0\\n'", "actual": repr(run(small, 0))})

    # 5. Hint's precondition: any bound below 35 leaves 0 as the only candidate.
    for ub in (0, 10, 34):
        code = solution.replace("range(201)", f"range({ub + 1})")
        assert all(run(code, s) == "0\n" for s in range(10)), ub
    code35 = solution.replace("range(201)", "range(36)")
    assert {int(run(code35, s)) for s in SEEDS} == {0, 35}
    evidence["cases"].append({"input": "bounds 0, 10, 34 -> '0\\n'; bound 35 -> {0, 35}", "expected": "as stated", "actual": "as stated"})

    evidence["tools"] = {"python": sys.version, "platform": platform.platform(),
                         "git": subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()}
    if not DELIBERATE_WRONG:
        (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print("OK: Question 77 checks passed")


if __name__ == "__main__":
    main()
