import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "100+ Python challenging programming exercises for Python 3.md"
FIXTURES = Path(__file__).with_name("inputs.json")


def extract_examples():
    source = ARTICLE.read_text(encoding="utf-8")
    question = re.search(
        r"(?ms)^### Question 62\s*\n(.*?)(?=^### Question 63\s*$)",
        source,
    )
    if not question:
        raise ValueError("Question 62 section was not found")

    section = question.group(1)
    fences = re.findall(r"(?m)^```", section)
    if len(fences) % 2:
        raise ValueError("Question 62 contains an unbalanced code fence")

    solution = re.search(
        r"(?ms)^Solution:\s*\n```python\s*\n(.*?)^```$",
        section,
    )
    published = re.search(
        r"(?ms)^\*\*Example\*\*:\s*"
        r"Input:\s*`([^`]+)`\s*"
        r"Intermediate:.*?"
        r"^Output:\s*\n```text\s*\n(.*?)^```$",
        section,
    )
    smallest = re.search(
        r"(?ms)^\*\*Smallest Non-Empty Input\*\*:\s*"
        r"Input:\s*`([^`]+)`.*?"
        r"^Output:\s*\n```text\s*\n(.*?)^```$",
        section,
    )
    if not solution or not published or not smallest:
        raise ValueError("Question 62 solution or demonstration is missing")
    return {
        "section": section,
        "solution": solution.group(1).strip() + "\n",
        "published": {
            "input": published.group(1),
            "expected_output": published.group(2).rstrip("\r\n") + "\n",
        },
        "smallest": {
            "input": smallest.group(1),
            "expected_output": smallest.group(2).rstrip("\r\n") + "\n",
        },
    }


def run_solution(code, input_text, check=True):
    assertions = (
        "\nassert type(s) is str\n"
        "assert type(u) is str\n"
        "assert u == s\n"
        "assert u is s\n"
    )
    with tempfile.TemporaryDirectory(prefix="check_q62_") as temporary_directory:
        script = Path(temporary_directory) / "question62.py"
        script.write_text(code.rstrip() + assertions, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(script)],
            input=input_text,
            capture_output=True,
            text=True,
            check=check,
        )


def main():
    examples = extract_examples()
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    for example_name in ("published", "smallest"):
        assert examples[example_name]["input"] == fixtures[example_name]["input"], (
            f"{example_name} input differs from its fixture"
        )
        assert (
            examples[example_name]["expected_output"]
            == fixtures[example_name]["expected_output"]
        ), f"{example_name} output differs from its fixture"

    published = run_solution(
        examples["solution"],
        fixtures["published"]["input"] + "\n",
    )
    assert published.stdout == fixtures["published"]["expected_output"], (
        f"Published output mismatch: {published.stdout!r}"
    )

    smallest = run_solution(
        examples["solution"],
        fixtures["smallest"]["input"] + "\n",
    )
    assert smallest.stdout == fixtures["smallest"]["expected_output"], (
        f"Smallest-input output mismatch: {smallest.stdout!r}"
    )

    mutant, replacements = re.subn(
        r"(?m)^u = s$",
        'u = s.encode("utf-8")',
        examples["solution"],
    )
    assert replacements == 1, "Expected exactly one assignment to mutate"
    mutant_result = run_solution(
        mutant,
        fixtures["published"]["input"] + "\n",
        check=False,
    )
    assert mutant_result.returncode != 0, "UTF-8 bytes mutant unexpectedly passed"
    assert mutant_result.stdout == fixtures["mutation"]["actual_output"], (
        f"Unexpected mutant output: {mutant_result.stdout!r}"
    )
    assert mutant_result.stdout != fixtures["published"]["expected_output"]
    assert "AssertionError" in mutant_result.stderr, (
        "The mutant was not rejected by the string type assertion"
    )

    print(f"Source: {ARTICLE.name}, Question 62 solution")
    print(
        f"Published input: {fixtures['published']['input']!r}; "
        f"expected: {fixtures['published']['expected_output']!r}; "
        f"actual: {published.stdout!r}"
    )
    print(
        f"Smallest input: {fixtures['smallest']['input']!r}; "
        f"expected: {fixtures['smallest']['expected_output']!r}; "
        f"actual: {smallest.stdout!r}"
    )
    print("Intermediate assertions passed: s and u are str, equal, and identical.")
    print(
        f"UTF-8 bytes mutant rejected: stdout={mutant_result.stdout!r}; "
        f"exit status={mutant_result.returncode}."
    )
    print("All Question 62 checks passed.")


if __name__ == "__main__":
    main()
