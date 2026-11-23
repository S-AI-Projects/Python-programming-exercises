import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_PATH = ROOT / "100+ Python challenging programming exercises for Python 3.md"
FIXTURE_PATH = Path(__file__).with_name("inputs.json")


def extract_question(markdown_path):
    markdown = markdown_path.read_text(encoding="utf-8")
    question_match = re.search(
        r"### Question 42\r?\n(.*?)(?=### Question 43\r?\n)",
        markdown,
        re.DOTALL,
    )
    if not question_match:
        raise ValueError("Question 42 section was not found")
    section = question_match.group(1)

    if len(re.findall(r"(?m)^```", section)) != 8:
        raise ValueError("Question 42 must contain four balanced fenced blocks")

    solution_match = re.search(
        r"(?m)^Solution\s*\r?\n```python\r?\n(.*?)```",
        section,
        re.DOTALL,
    )
    if not solution_match:
        raise ValueError("Question 42 solution code block was not found")

    demo_match = re.search(
        r"\*\*Smallest Meaningful Demonstration\*\*:.*?"
        r"```python\r?\n(.*?)```",
        section,
        re.DOTALL,
    )
    if not demo_match:
        raise ValueError("Question 42 smallest demonstration code block was not found")

    published_output_match = re.search(
        r"The displayed result is:\s*```text\r?\n(.*?)\r?\n```",
        section,
        re.DOTALL,
    )
    demo_output_match = re.search(
        r"It displays:\s*```text\r?\n(.*?)\r?\n```",
        section,
        re.DOTALL,
    )
    if not published_output_match or not demo_output_match:
        raise ValueError("Question 42 displayed output was not found")

    return {
        "solution": solution_match.group(1).strip() + "\n",
        "smallest_demo": demo_match.group(1).strip() + "\n",
        "published_output": published_output_match.group(1) + "\n",
        "demo_output": demo_output_match.group(1) + "\n",
    }


def tuple_literal(values):
    return repr(tuple(values))


def run_extracted_code(code, assertions, label):
    script = code.rstrip() + "\n\n" + assertions + "\n"
    with tempfile.TemporaryDirectory(prefix="check_q42_") as temporary_directory:
        script_path = Path(temporary_directory) / f"{label}.py"
        script_path.write_text(script, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            check=True,
        )


def verify_output(actual, expected, label):
    assert actual == expected, (
        f"{label} printed output mismatch: expected {expected!r}, got {actual!r}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Extract and verify Question 42 examples from the Markdown"
    )
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="use a deliberately incorrect published output expectation",
    )
    args = parser.parse_args()

    question = extract_question(MARKDOWN_PATH)
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    published = fixture["published_example"]
    smallest = fixture["smallest_demonstration"]

    assert question["published_output"] == published["expected_stdout"], (
        "Published output in Markdown does not match the fixture"
    )
    assert question["demo_output"] == smallest["expected_stdout"], (
        "Smallest demonstration output in Markdown does not match the fixture"
    )

    published_assertions = "\n".join(
        [
            f"assert type(tp) is tuple and tp == {tuple_literal(published['tuple'])}",
            f"assert type(tp1) is tuple and tp1 == {tuple_literal(published['first_slice'])}",
            f"assert type(tp2) is tuple and tp2 == {tuple_literal(published['last_slice'])}",
            f"assert tp == {tuple_literal(published['tuple'])}",
        ]
    )
    demo_assertions = "\n".join(
        [
            "assert type(smallest) is tuple",
            f"assert smallest == {tuple_literal(smallest['tuple'])}",
            "assert type(first) is tuple",
            f"assert first == {tuple_literal(smallest['first_slice'])}",
            "assert type(last) is tuple",
            f"assert last == {tuple_literal(smallest['last_slice'])}",
            "assert first + last == smallest",
            "assert smallest == " + tuple_literal(smallest["tuple"]),
        ]
    )

    published_result = run_extracted_code(
        question["solution"], published_assertions, "published_question42"
    )
    demo_result = run_extracted_code(
        question["smallest_demo"], demo_assertions, "smallest_question42"
    )

    if args.wrong:
        incorrect_expected = "(1, 2, 3, 4, 6)\n(6, 7, 8, 9, 10)\n"
        print(f"Actual published output: {published_result.stdout!r}")
        print(f"Deliberately wrong expected output: {incorrect_expected!r}")
        verify_output(
            published_result.stdout,
            incorrect_expected,
            "Deliberate wrong-result check",
        )
        return

    verify_output(
        published_result.stdout,
        question["published_output"],
        "Published example",
    )
    verify_output(demo_result.stdout, question["demo_output"], "Smallest demonstration")

    print(f"Source: {MARKDOWN_PATH}")
    print("Both Python examples were extracted from Question 42 and executed.")
    print("\nPublished tuple:")
    print(f"  tp:  {tuple_literal(published['tuple'])}")
    print(f"  tp1: {tuple_literal(published['first_slice'])} (tuple)")
    print(f"  tp2: {tuple_literal(published['last_slice'])} (tuple)")
    print(f"  Expected output: {question['published_output']!r}")
    print(f"  Actual output:   {published_result.stdout!r}")
    print("  Original tp remains unchanged: verified.")
    print("\nSmallest meaningful demonstration:")
    print(f"  tuple:  {tuple_literal(smallest['tuple'])}")
    print(f"  first:  {tuple_literal(smallest['first_slice'])} (tuple)")
    print(f"  second: {tuple_literal(smallest['last_slice'])} (tuple)")
    print(f"  Expected output: {question['demo_output']!r}")
    print(f"  Actual output:   {demo_result.stdout!r}")
    print("\nAll Question 42 checks passed.")


if __name__ == "__main__":
    main()
