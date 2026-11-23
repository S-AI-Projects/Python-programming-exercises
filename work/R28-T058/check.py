#!/usr/bin/env python3
"""Check Question 13 in the Python 3 exercises markdown by executing its published code.

The example, solution block and hints are extracted from the markdown. The solution runs unmodified,
fed through stdin. Fixture: the child interpreter runs with -I -X utf8 and stdin/stdout are exchanged
as UTF-8 bytes, so the Unicode examples do not depend on the locale or on PYTHON* variables.

  python3 work/R28-T058/check.py                      # must exit 0
  python3 work/R28-T058/check.py --deliberate-wrong   # must exit non-zero
"""
import hashlib, json, platform, re, subprocess, sys, tempfile, unicodedata
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
    """Run the code in a fresh UTF-8 interpreter; returns (returncode, stdout, stderr) as text."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
    cp = subprocess.run([sys.executable, "-I", "-X", "utf8", f.name], input=stdin.encode("utf-8"), capture_output=True, check=check)
    dec = lambda b: b.decode("utf-8").replace("\r\n", "\n")
    return cp.returncode, dec(cp.stdout), dec(cp.stderr)


def assert_printed(out, letters, digits):
    """Printed representation: exactly two lines, LETTERS first, one space, newline-terminated."""
    assert re.fullmatch(r"LETTERS \d+\nDIGITS \d+\n", out), f"bad printed representation: {out!r}"
    assert out == f"LETTERS {letters}\nDIGITS {digits}\n", f"printed {out!r}, expected LETTERS {letters} / DIGITS {digits}"


def count(solution, line):
    rc, out, err = run(solution, line + "\n")
    assert rc == 0 and err == "", err
    m = re.fullmatch(r"LETTERS (\d+)\nDIGITS (\d+)\n", out)
    assert m, out
    return int(m.group(1)), int(m.group(2)), out


def main():
    text = MD.read_text(encoding="utf-8")
    body = section(text, 13)
    (solution,) = re.findall(r"```python\n(.*?)```", body, re.S)
    ex = re.search(r"input is supplied to the program:\n(.*?)\nThen, the output should be:\nLETTERS (\d+)\nDIGITS (\d+)\n\nHints:", body, re.S)
    assert ex, "published example not found"
    ex_in, ex_l, ex_d = ex.group(1), int(ex.group(2)), int(ex.group(3))
    assert (ex_in, ex_l, ex_d) == ("hello world! 123", 10, 3), (ex_in, ex_l, ex_d)
    want_l, want_d = (ex_l, ex_d + 1) if DELIBERATE_WRONG else (ex_l, ex_d)    # the deliberate-wrong run expects 4 digits
    (hint1,) = re.findall(r"^The program reads one line.*$", body, re.M)
    (hint2,) = re.findall(r"^Here `.` counts as a letter.*$", body, re.M)
    (mi_in, mi_out) = re.findall(r"if the input is `(.+?)`, the output is:\n```\n(.*?)```", body, re.S)[0]
    plain1, plain2 = hint1.replace("`", ""), hint2.replace("`", "")
    ev = {"source": MD.name, "md_sha256": hashlib.sha256(MD.read_bytes()).hexdigest(), "solution": solution, "cases": []}

    # 1. Negative controls: the assertion rejects wrong values, order and formatting.
    for bad in ("LETTERS 10 DIGITS 3\n", "LETTERS: 10\nDIGITS: 3\n", "DIGITS 3\nLETTERS 10\n", "LETTERS 10\nDIGITS 3",
                "LETTERS 10\nDIGITS 3\n\n", "LETTERS  10\nDIGITS 3\n", "letters 10\ndigits 3\n", "LETTERS 9\nDIGITS 3\n", "LETTERS 10\nDIGITS 4\n"):
        try:
            assert_printed(bad, 10, 3)
        except AssertionError:
            continue
        raise SystemExit(f"checker accepted wrong output {bad!r}")
    try:                                                                       # subprocess failures must propagate
        run("raise SystemExit(3)")
        raise SystemExit("subprocess failure was swallowed")
    except subprocess.CalledProcessError as e:
        assert e.returncode == 3

    # 2. The exact published example, unmodified code: value and printed representation.
    rc, out, err = run(solution, ex_in + "\n")
    assert rc == 0 and err == ""
    assert_printed(out, want_l, want_d)
    assert out == "LETTERS 10\nDIGITS 3\n" or DELIBERATE_WRONG
    ev["cases"].append({"input": repr(ex_in + "\n"), "expected": repr(f"LETTERS {want_l}\nDIGITS {want_d}\n"), "actual": repr(out)})

    # 3. Smallest supported input (an empty line) and the empty-result vs no-input contrast.
    assert_printed(count(solution, "")[2], 0, 0)
    ev["cases"].append({"input": repr("\n"), "expected": "'LETTERS 0\\nDIGITS 0\\n'", "actual": repr(count(solution, "")[2])})
    rc, out, err = run(solution, "", check=False)                              # EOF: no line at all
    assert rc != 0 and out == "" and err.strip().endswith("EOFError: EOF when reading a line"), (rc, out, err)
    ev["cases"].append({"input": repr(""), "expected": "EOFError, nothing printed", "actual": f"exit {rc}: {err.strip().splitlines()[-1]}"})

    # 4. The misconception from the hint: the contract is Unicode isalpha()/isdigit(), not a-z / 0-9.
    letter, digit, other = re.search(r"^Here `(.)` counts as a letter and `(.)` as a digit, but `(.)` would not be counted at all\.", hint2).groups()
    assert unicodedata.normalize("NFC", mi_in) == mi_in and letter in mi_in and digit in mi_in, "example must use single code points"
    assert letter.isalpha() and not letter.isascii() and digit.isdigit() and digit not in "0123456789"
    assert not other.isalpha() and not other.isdigit() and other.isnumeric(), "excluded character must be numeric but neither letter nor digit"
    l4, d1, o = count(solution, mi_in)
    assert o == mi_out, (o, mi_out)
    assert (l4, d1) == (4, 1) and mi_out == "LETTERS 4\nDIGITS 1\n"
    assert count(solution, mi_in + other)[:2] == (4, 1)                        # the excluded character changes nothing
    ev["cases"].append({"input": repr(mi_in + "\n"), "expected": repr(mi_out), "actual": repr(o),
                        "note": f"U+{ord(letter):04X} counts as a letter, U+{ord(digit):04X} as a digit, U+{ord(other):04X} not at all"})
    for line, want in (("\u4e2d\u6587 \u0663\u0664", (2, 2)), ("stra\u00dfe", (6, 0)), ("\u00bd \u2167 \u00b9", (0, 1))):
        l, d, o = count(solution, line)
        assert (l, d) == want, (line, (l, d), want)
        ev["cases"].append({"input": repr(line + "\n"), "expected": f"LETTERS {want[0]} / DIGITS {want[1]}", "actual": repr(o)})

    # 5. Only the first line is read.
    rc, out, err = run(solution, "abc\n123\n")
    assert rc == 0 and out == "LETTERS 3\nDIGITS 0\n", out
    ev["cases"].append({"input": repr("abc\n123\n"), "expected": "'LETTERS 3\\nDIGITS 0\\n' (second line unread)", "actual": repr(out)})
    for needle in ("isalpha() or isdigit()", "Unicode rules", "spaces and punctuation, is ignored",
                   "An empty line gives LETTERS 0 and DIGITS 0", "no input at all raises EOFError", "only the first line is read"):
        assert needle in plain1 + " " + plain2, needle

    # 6. ASCII variations against an independent regex count.
    for line in ("abc123", "A1b2C3", "!!! ???", "   ", "a_b-c", "Python 3.12", "x" * 50 + "7" * 5):
        l, d, o = count(solution, line)
        assert (l, d) == (len(re.findall("[A-Za-z]", line)), len(re.findall("[0-9]", line))), (line, l, d)
        ev["cases"].append({"input": repr(line + "\n"), "expected": f"LETTERS {l} / DIGITS {d} (regex count)", "actual": repr(o)})

    ev["tools"] = {"python": sys.version, "platform": platform.platform(),
                   "git": subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()}
    if not DELIBERATE_WRONG:
        (OUT / "evidence.json").write_text(json.dumps(ev, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("OK: Question 13 checks passed")


if __name__ == "__main__":
    main()
