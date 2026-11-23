import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "100+ Python challenging programming exercises for Python 3.md"
FIXTURES = Path(__file__).with_name("inputs.json")


def extract_examples(article):
    source = article.read_text(encoding="utf-8")
    match = re.search(
        r"### Question 61\r?\n(.*?)(?=### Question 62\r?\n)",
        source,
        re.DOTALL,
    )
    if not match:
        raise ValueError("Question 61 section was not found")

    section = match.group(1)
    if len(re.findall(r"(?m)^```", section)) != 12:
        raise ValueError("Question 61 must contain six balanced fenced blocks")

    published = re.search(
        r"Solution:\s*```python\r?\n(.*?)```\s*"
        r"Output:\s*```text\r?\n(.*?)\r?\n```",
        section,
        re.DOTALL,
    )
    smallest = re.search(
        r"\*\*Smallest Meaningful Demonstration\*\*:.*?"
        r"```python\r?\n(.*?)```\s*"
        r"Output:\s*```text\r?\n(.*?)\r?\n```",
        section,
        re.DOTALL,
    )
    limitation = re.search(
        r"\*\*Text and Bytes Are Different Types in Python 3\*\*:.*?"
        r"```python\r?\n(.*?)```\s*"
        r"Output:\s*```text\r?\n(.*?)\r?\n```",
        section,
        re.DOTALL,
    )
    if not published or not smallest or not limitation:
        raise ValueError("A Question 61 code example/output pair was not found")

    return {
        "section": section,
        "published": {
            "code": published.group(1).strip() + "\n",
            "output": published.group(2) + "\n",
        },
        "smallest": {
            "code": smallest.group(1).strip() + "\n",
            "output": smallest.group(2) + "\n",
        },
        "limitation": {
            "code": limitation.group(1).strip() + "\n",
            "output": limitation.group(2) + "\n",
        },
    }


def run_code(code, assertions, label):
    script = code.rstrip() + "\n\n" + assertions + "\n"
    with tempfile.TemporaryDirectory(prefix="check_q61_") as temporary_directory:
        script_path = Path(temporary_directory) / f"{label}.py"
        script_path.write_text(script, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            check=True,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Extract and check Question 61 examples from the Markdown"
    )
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="compare the published result with an intentionally wrong value",
    )
    args = parser.parse_args()

    examples = extract_examples(ARTICLE)
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    for name in ("published", "smallest", "limitation"):
        assert examples[name]["output"] == fixtures[name]["expected_stdout"], (
            f"{name} expected output in the article does not match its fixture"
        )

    published = run_code(
        examples["published"]["code"],
        "assert type(unicodeString) is str\n"
        f"assert unicodeString == {fixtures['published']['value']!r}",
        "published",
    )
    smallest = run_code(
        examples["smallest"]["code"],
        "assert type(emptyUnicodeString) is str\n"
        f"assert emptyUnicodeString == {fixtures['smallest']['value']!r}\n"
        "assert len(emptyUnicodeString) == 0",
        "smallest",
    )
    limitation = run_code(
        examples["limitation"]["code"],
        "assert type(unicodeString) is str\n"
        "assert type(encodedBytes) is bytes\n"
        f"assert unicodeString == {fixtures['published']['value']!r}\n"
        f"assert encodedBytes == {fixtures['limitation']['encoded_bytes_repr']}",
        "limitation",
    )

    if args.wrong:
        wrong_output = "not the published output\n"
        print(f"Actual published output: {published.stdout!r}")
        print(f"Deliberately wrong expected output: {wrong_output!r}")
        assert published.stdout == wrong_output, (
            "Deliberate negative test: actual output did not match the wrong result"
        )
        return

    assert published.stdout == fixtures["published"]["expected_stdout"], (
        f"Published output mismatch: {published.stdout!r}"
    )
    assert smallest.stdout == fixtures["smallest"]["expected_stdout"], (
        f"Smallest demonstration output mismatch: {smallest.stdout!r}"
    )
    assert limitation.stdout == fixtures["limitation"]["expected_stdout"], (
        f"Text/bytes limitation output mismatch: {limitation.stdout!r}"
    )
    assert "Python 3 does not implicitly concatenate text and bytes" in examples[
        "section"
    ]

    print(f"Source: {ARTICLE}")
    print("Published example:")
    print(f"  Expected: {fixtures['published']['expected_stdout']!r}")
    print(f"  Actual:   {published.stdout!r}")
    print("  Python 3 type str: verified.")
    print("Smallest supported demonstration:")
    print(f"  Empty Unicode string expected: {fixtures['smallest']['expected_stdout']!r}")
    print(f"  Actual:                        {smallest.stdout!r}")
    print("  Empty value and Python 3 str type: verified.")
    print("Python 3 text/bytes limitation:")
    print(f"  Expected: {fixtures['limitation']['expected_stdout']!r}")
    print(f"  Actual:   {limitation.stdout!r}")
    print("  TypeError for str + bytes and explanation: verified.")
    print("All Question 61 checks passed.")


if __name__ == "__main__":
    main()
