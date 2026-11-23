#!/usr/bin/env python3
"""Check Question 24 in the Python 3 exercises markdown by executing its published code.

The solution block and hints are extracted from the markdown and run with real interpreters;
variations are derived from the published block, not retyped.

Fixture: the example prints text that depends on the interpreter, so each interpreter is run in
isolated mode (-I, which ignores PYTHON* environment variables such as PYTHONOPTIMIZE) and the
expected output is built from that same interpreter's own abs/int/input documents plus the
version rule stated in the hint for square.__doc__. The checker never changes its own environment;
it asserts os.environ is identical at the end.

  python3 work/R28-T055/check.py                      # must exit 0
  python3 work/R28-T055/check.py --deliberate-wrong   # must exit non-zero
Other interpreters (python3.11, python3.12, python3.13) are also checked when found on PATH.
"""
import ast, hashlib, json, os, platform, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "100+ Python challenging programming exercises for Python 3.md"
OUT = Path(__file__).resolve().parent
DELIBERATE_WRONG = "--deliberate-wrong" in sys.argv


def section(text, n):
    m = re.search(rf"^### Question {n}\n(.*?)(?=^### Question {n + 1}\n)", text, re.S | re.M)
    assert m, f"Question {n} not found"
    return m.group(1)


def strip_margin(doc):
    """What Python 3.13 does to a docstring: drop the common indentation, blank lines become empty."""
    lines = doc.expandtabs().split("\n")
    margin = min((len(l) - len(l.lstrip()) for l in lines[1:] if l.strip()), default=0)
    return "\n".join([lines[0].lstrip()] + [l[margin:] if l.strip() else "" for l in lines[1:]])


def make_runner(exe):
    def run(code, flags=("-I",), env=None, check=True):
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code)
        child_env = {**os.environ, **(env or {})}          # child only; our own environment is untouched
        return subprocess.run([exe, *flags, f.name], capture_output=True, text=True, check=check, env=child_env)
    return run


def check_interpreter(exe, solution, raw_doc, removed_ver, comment, hint_a, hint_b, ev):
    run = make_runner(exe)
    ver = tuple(int(x) for x in subprocess.run([exe, "-c", "import sys;print('%d.%d' % sys.version_info[:2])"],
                                               capture_output=True, text=True, check=True).stdout.strip().split("."))
    tag = "%d.%d" % ver
    use_raw = (ver < removed_ver) != DELIBERATE_WRONG       # the deliberate-wrong run applies the opposite rule
    sq_doc = raw_doc if use_raw else strip_margin(raw_doc)
    prefix = run("print(abs.__doc__)\nprint(int.__doc__)\nprint(input.__doc__)\n").stdout
    expected = prefix + "4\n" + sq_doc + "\n"

    def assert_stdout(out):
        assert out == expected, f"[{tag}] stdout {out[-120:]!r}\n expected tail {expected[-120:]!r}"

    # 1. Negative controls: the assertion rejects wrong values/representations.
    for bad in (expected.replace("\n4\n", "\n5\n"), expected.rstrip("\n"), prefix + "4\nNone\n",
                prefix + "4\n" + (strip_margin(raw_doc) if use_raw else raw_doc) + "\n", expected + "\n"):
        try:
            assert_stdout(bad)
        except AssertionError:
            continue
        if not DELIBERATE_WRONG:
            raise SystemExit(f"[{tag}] checker accepted wrong output {bad[-60:]!r}")

    # 2. The exact published example: value and printed representation.
    out = run(solution).stdout
    assert_stdout(out)
    assert out.startswith("Return the absolute value of the argument.\n")
    assert "Read a string from standard input." in out
    assert comment == "4"
    ev["cases"].append({"interpreter": tag, "input": "published block, unchanged, python -I",
                        "expected": f"abs/int/input docs of this interpreter, '4\\n', square doc ({'indented' if use_raw else 'dedented'}), newline",
                        "actual_tail": out[-110:], "builtin_docs_sha256": hashlib.sha256(prefix.encode()).hexdigest()[:12]})

    # 3. Fixtures that change the output: -OO removes docstrings; -I shields the run from PYTHONOPTIMIZE.
    oo = run(solution, flags=("-I", "-OO")).stdout
    assert oo == prefix + "4\nNone\n", oo[-60:]
    assert run(solution, flags=(), env={"PYTHONOPTIMIZE": "2"}).stdout == prefix + "4\nNone\n"
    assert run(solution, env={"PYTHONOPTIMIZE": "2"}).stdout == out                # -I ignores it
    ev["cases"].append({"interpreter": tag, "input": "python -I -OO / PYTHONOPTIMIZE=2 without -I", "expected": "square doc prints None", "actual_tail": oo[-12:]})

    # 4. Smallest supported input and variations, derived from the published call.
    call = "print(square(2)) #4"
    assert solution.count(call) == 1, "published block changed; update the derivation"
    for n in (0, 1, -1, 2, -5, 5, 10**20):
        o = run(solution.replace(call, f"print(square({n}))")).stdout
        assert o.startswith(prefix) and o[len(prefix):] == f"{n * n}\n{sq_doc}\n", (n, o[len(prefix):][:30])
    ev["cases"].append({"interpreter": tag, "input": "square(0) smallest, plus 1, -1, 2, -5, 5, 10**20", "expected": "n*n then the square doc", "actual": "all equal"})

    # 5. The docstring is a contract the code does not enforce.
    assert run(solution.replace(call, "print(square(1.5))")).stdout[len(prefix):].startswith("2.25\n")
    p = run(solution.replace(call, 'print(square("2"))'), check=False)
    assert p.returncode != 0 and "TypeError" in p.stderr, p.stderr
    p2 = run("print(raw_input.__doc__)", check=False)
    assert p2.returncode != 0 and "NameError" in p2.stderr
    ev["cases"].append({"interpreter": tag, "input": 'square(1.5); square("2"); raw_input', "expected": "2.25; TypeError; NameError",
                        "actual": "2.25; " + p.stderr.strip().splitlines()[-1][:40] + "; " + p2.stderr.strip().splitlines()[-1]})
    return tag


def main():
    env_before = dict(os.environ)
    text = MD.read_text(encoding="utf-8")
    body = section(text, 24)
    (solution,) = re.findall(r"```python\n(.*?)```", body, re.S)
    (comment,) = re.findall(r"^print\(square\(2\)\) #(\S+)$", solution, re.M)
    (hint_a,) = re.findall(r"^In Python 3, .*$", body, re.M)
    (hint_b,) = re.findall(r"^The docstring asks for an integer.*$", body, re.M)
    a, b = hint_a.replace("`", ""), hint_b.replace("`", "")

    # Raw docstring of square exactly as written in the article (no clean-up).
    fn = next(n for n in ast.parse(solution).body if isinstance(n, ast.FunctionDef) and n.name == "square")
    raw_doc = ast.get_docstring(fn, clean=False)
    assert raw_doc.startswith("Return the square value of the input number.\n    \n    The input") and raw_doc.endswith("\n    ")

    # Version rule stated in the hint, parsed so the check cannot drift from the article.
    m = re.search(r"Python (3\.\d+) and (3\.\d+) keep its indentation, Python (3\.\d+) removes it", a)
    assert m, a
    removed_ver = tuple(int(x) for x in m.group(3).split("."))
    assert all(tuple(int(x) for x in v.split(".")) < removed_ver for v in m.group(1, 2))
    for needle in ("raw_input() from the question is called input()", "`square(2)` prints 4".replace("`", ""), "-OO", "None"):
        assert needle in a, needle
    assert 'square(1.5) prints 2.25 and square("2") raises TypeError' in b

    ev = {"source": MD.name, "md_sha256": hashlib.sha256(MD.read_bytes()).hexdigest(), "solution": solution, "cases": []}
    tested = [check_interpreter(sys.executable, solution, raw_doc, removed_ver, comment, hint_a, hint_b, ev)]
    for name in ("python3.11", "python3.12", "python3.13"):
        exe = shutil.which(name)
        if exe and not DELIBERATE_WRONG:
            extra = {"cases": []}
            try:
                v = check_interpreter(exe, solution, raw_doc, removed_ver, comment, hint_a, hint_b, extra)
            except subprocess.CalledProcessError as e:
                raise SystemExit(f"{name} failed: {e}")
            if v not in tested:                             # keep evidence once per Python version
                tested.append(v)
                ev["cases"] += extra["cases"]
    assert dict(os.environ) == env_before, "checker changed the process environment"

    ev["interpreters_tested"] = tested
    ev["tools"] = {"python": sys.version, "platform": platform.platform(),
                   "git": subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()}
    if not DELIBERATE_WRONG:
        (OUT / "evidence.json").write_text(json.dumps(ev, indent=2) + "\n")
    print("OK: Question 24 checks passed on Python " + ", ".join(tested))


if __name__ == "__main__":
    main()
