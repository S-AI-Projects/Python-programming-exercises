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
        r"### Question 66\r?\n(.*?)(?=### Question 67\r?\n)",
        source,
        re.DOTALL,
    )
    if not match:
        raise ValueError("Question 66 section was not found")

    section = match.group(1)
    if len(re.findall(r"(?m)^```", section)) != 8:
        raise ValueError("Question 66 must contain four balanced fenced blocks")

    published = re.search(
        r"Example:\s*"
        r"If the following n is given as input to the program:\s*(\d+)\s*"
        r"Then, the output of the program should be:\s*(\d+)",
        section,
    )
    solution = re.search(
        r"Solution:\s*```python\r?\n(.*?)```",
        section,
        re.DOTALL,
    )
    experiment = re.search(
        r"\*\*Small Call-Count Experiment\*\*:.*?"
        r"```python\r?\n(.*?)```\s*"
        r"The observed calls are:\s*```text\r?\n(.*?)\r?\n```",
        section,
        re.DOTALL,
    )
    smallest = re.search(
        r"\*\*Smallest Supported Input\*\*:.*?"
        r"```text\r?\nInput:\s*(\d+)\s*Output:\s*(\d+)\s*```",
        section,
        re.DOTALL,
    )
    if not published or not solution or not experiment or not smallest:
        raise ValueError("A published, experiment, or smallest-input example is missing")

    return {
        "section": section,
        "published": {
            "input": published.group(1),
            "value": int(published.group(2)),
            "output": published.group(2) + "\n",
            "code": solution.group(1).strip() + "\n",
        },
        "experiment": {
            "code": experiment.group(1).strip() + "\n",
            "output": experiment.group(2) + "\n",
        },
        "smallest": {
            "input": smallest.group(1),
            "value": int(smallest.group(2)),
            "output": smallest.group(2) + "\n",
        },
    }


def run_code(code, input_text="", assertions="", label="question66"):
    script = code.rstrip() + "\n\n" + assertions + "\n"
    with tempfile.TemporaryDirectory(prefix="check_q66_") as temporary_directory:
        script_path = Path(temporary_directory) / f"{label}.py"
        script_path.write_text(script, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(script_path)],
            input=input_text,
            capture_output=True,
            text=True,
            check=True,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Extract and check Question 66 examples from the Markdown"
    )
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="compare the published result with an intentionally wrong value",
    )
    args = parser.parse_args()

    examples = extract_examples(ARTICLE)
    fixture = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert examples["published"]["input"] == fixture["published"]["input"]
    assert examples["published"]["output"] == fixture["published"]["expected_output"]
    assert examples["smallest"]["input"] == fixture["smallest"]["input"]
    assert examples["smallest"]["output"] == fixture["smallest"]["expected_output"]
    assert examples["experiment"]["output"] == fixture["call_count"]["expected_output"]

    published = run_code(
        examples["published"]["code"],
        input_text=examples["published"]["input"] + "\n",
        assertions=f"assert f({examples['published']['input']}) == {examples['published']['value']}",
        label="published",
    )
    smallest = run_code(
        examples["published"]["code"],
        input_text=examples["smallest"]["input"] + "\n",
        assertions=f"assert f({examples['smallest']['input']}) == {examples['smallest']['value']}",
        label="smallest",
    )
    experiment_assertions = []
    for case in fixture["call_count"]["cases"]:
        experiment_assertions.extend(
            [
                "calls.clear()",
                f"assert counted_f({case['input']}) == {case['result']}",
                f"assert sum(calls.values()) == {case['total_calls']}",
                f"assert calls[5] == {case['calls_to_f5']}",
            ]
        )
    experiment = run_code(
        examples["experiment"]["code"],
        assertions="\n".join(experiment_assertions),
        label="call_count_experiment",
    )
    for case in fixture["call_count"]["cases"]:
        published_case = run_code(
            examples["published"]["code"],
            input_text=f"{case['input']}\n",
            assertions=f"assert f({case['input']}) == {case['result']}",
            label=f"published_n{case['input']}",
        )
        assert published_case.stdout == f"{case['result']}\n", (
            f"Instrumented experiment disagrees with published f for n={case['input']}"
        )

    if args.wrong:
        wrong_output = "14\n"
        print(f"Actual published output: {published.stdout!r}")
        print(f"Deliberately wrong expected output: {wrong_output!r}")
        assert published.stdout == wrong_output, (
            "Deliberate negative test: actual output did not match the wrong result"
        )
        return

    assert published.stdout == fixture["published"]["expected_output"], (
        f"Published output mismatch: {published.stdout!r}"
    )
    assert smallest.stdout == fixture["smallest"]["expected_output"], (
        f"Smallest-input output mismatch: {smallest.stdout!r}"
    )
    assert experiment.stdout == fixture["call_count"]["expected_output"], (
        f"Call-count output mismatch: {experiment.stdout!r}"
    )
    required_explanations = (
        r"O\(2\^n\)",
        r"O\(n\).*call-stack frames",
        r"does not cache earlier results",
    )
    for pattern in required_explanations:
        assert re.search(pattern, examples["section"]), (
            f"Missing required complexity explanation matching: {pattern}"
        )

    print(f"Source: {ARTICLE}")
    print("Published example:")
    print(f"  Input: {fixture['published']['input']}")
    print(f"  Expected: {fixture['published']['expected_output']!r}")
    print(f"  Actual:   {published.stdout!r}")
    print("Smallest supported input:")
    print(f"  Input: {fixture['smallest']['input']}")
    print(f"  Expected: {fixture['smallest']['expected_output']!r}")
    print(f"  Actual:   {smallest.stdout!r}")
    print("Call-count experiment:")
    print(experiment.stdout, end="")
    print("Time/space complexity and no-memoization explanation: verified.")
    print("All Question 66 checks passed.")


if __name__ == "__main__":
    main()
