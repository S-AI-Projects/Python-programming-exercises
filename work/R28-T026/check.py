import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_PATH = ROOT / "100+ Python challenging programming exercises for Python 3.md"


def extract_question(path):
    markdown = path.read_text(encoding="utf-8")
    question_match = re.search(
        r"### Question 6\r?\n(.*?)(?=### Question 7\r?\n)",
        markdown,
        re.DOTALL,
    )
    if not question_match:
        raise ValueError("Question 6 section was not found")

    section = question_match.group(1)
    fence_count = len(re.findall(r"(?m)^```", section))
    if fence_count != 2:
        raise ValueError(f"Expected one balanced solution code fence, found {fence_count}")

    example_match = re.search(
        r"Example\r?\n"
        r"Let us assume the following comma separated input sequence is given to the program:\r?\n"
        r"([^\r\n]+)\r?\n"
        r"The output of the program should be:\r?\n"
        r"([^\r\n]+)",
        section,
    )
    if not example_match:
        raise ValueError("Question 6 published input/output example was not found")

    solution_match = re.search(
        r"Solution:\s*```python\r?\n(.*?)```",
        section,
        re.DOTALL,
    )
    if not solution_match:
        raise ValueError("Question 6 Python solution code block was not found")

    smallest_match = re.search(
        r"\*\*Smallest Supported Input\*\*:\s*"
        r"- Since the square root requires \$D \\ge 0\$, "
        r"the smallest supported input is \$D = (\d+)\$:(.*?)"
        r"(?=\r?\n\r?\nSolution:)",
        section,
        re.DOTALL,
    )
    if not smallest_match:
        raise ValueError("Question 6 smallest supported input was not found")
    smallest_output_match = re.search(
        r"Output:\s*`([^`]+)`",
        smallest_match.group(2),
    )
    if not smallest_output_match:
        raise ValueError("Question 6 smallest-input output was not found")

    return {
        "code": solution_match.group(1).strip() + "\n",
        "published_input": example_match.group(1).strip(),
        "published_output": example_match.group(2).strip(),
        "smallest_input": smallest_match.group(1),
        "smallest_output": smallest_output_match.group(1),
    }


def solution_constants(code):
    constants = {}
    for name in ("c", "h"):
        match = re.search(rf"(?m)^{name}\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*$", code)
        if not match:
            raise ValueError(f"Could not read {name} from the extracted solution")
        constants[name] = float(match.group(1))
    return constants["c"], constants["h"]


def execute_solution(code, input_text):
    with tempfile.TemporaryDirectory(prefix="check_q6_") as temporary_directory:
        solution_path = Path(temporary_directory) / "question6.py"
        solution_path.write_text(code, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(solution_path)],
            input=f"{input_text}\n",
            capture_output=True,
            text=True,
            check=True,
        )


def intermediate_values(d, c, h):
    converted_d = float(d)
    multiplied = 2 * c * converted_d
    divided = multiplied / h
    square_root = math.sqrt(divided)
    rounded = round(square_root)
    converted_to_int = int(rounded)
    return {
        "d": d,
        "float_d": converted_d,
        "multiplied": multiplied,
        "divided": divided,
        "sqrt": square_root,
        "round": rounded,
        "int": converted_to_int,
    }


def verify_case(code, input_text, expected_output):
    result = execute_solution(code, input_text)
    expected_printed = expected_output + "\n"
    actual_printed = result.stdout
    expected_values = [int(value) for value in expected_output.split(",")]
    actual_values = [int(value) for value in actual_printed.rstrip("\n").split(",")]
    assert actual_printed == expected_printed, (
        f"Printed output mismatch: expected {expected_printed!r}, "
        f"got {actual_printed!r}"
    )
    assert actual_values == expected_values, (
        f"Numerical result mismatch: expected {expected_values!r}, "
        f"got {actual_values!r}"
    )
    return expected_printed, actual_printed, actual_values


def main():
    parser = argparse.ArgumentParser(
        description="Extract and check Question 6 directly from the Markdown source"
    )
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="use a deliberately incorrect expected result; the check must fail",
    )
    arguments = parser.parse_args()

    question = extract_question(MARKDOWN_PATH)
    code = question["code"]
    c, h = solution_constants(code)

    print(f"Source: {MARKDOWN_PATH}")
    print(f"Extracted published input: {question['published_input']!r}")
    print(f"Extracted published expected output: {question['published_output']!r}")
    print("Extracted solution code is executed as a subprocess.")
    print("Question 6 solution code fence is balanced; no Markdown links are present.")

    if arguments.wrong:
        result = execute_solution(code, question["published_input"])
        wrong_values = [
            int(value) for value in question["published_output"].split(",")
        ]
        wrong_values[-1] += 1
        deliberately_wrong = ",".join(str(value) for value in wrong_values) + "\n"
        print(f"Actual output: {result.stdout!r}")
        print(f"Deliberately wrong expected output: {deliberately_wrong!r}")
        assert result.stdout == deliberately_wrong, (
            "Deliberate failure: checker correctly rejected the wrong expected output"
        )
        return

    published_expected, published_actual, published_values = verify_case(
        code,
        question["published_input"],
        question["published_output"],
    )
    print("\nPublished example:")
    print(f"  Input:           {question['published_input']}")
    print(f"  Expected output: {published_expected!r}")
    print(f"  Actual output:   {published_actual!r}")
    print(f"  Numerical value: {published_values!r}")

    print("\nIntermediate values for the published example:")
    published_inputs = question["published_input"].split(",")
    for d, actual_value in zip(published_inputs, published_values):
        values = intermediate_values(d, c, h)
        assert values["int"] == actual_value, (
            f"Intermediate result for D={d} does not match executed solution"
        )
        print(
            f"  D={d}: float={values['float_d']!r}, "
            f"multiply={values['multiplied']!r}, divide={values['divided']!r}, "
            f"sqrt={values['sqrt']!r}, round={values['round']!r}, "
            f"int={values['int']!r}"
        )

    smallest_expected, smallest_actual, smallest_values = verify_case(
        code,
        question["smallest_input"],
        question["smallest_output"],
    )
    smallest_breakdown = intermediate_values(question["smallest_input"], c, h)
    assert smallest_breakdown["int"] == smallest_values[0]
    print("\nSmallest supported input:")
    print(f"  Input:           {question['smallest_input']}")
    print(f"  Expected output: {smallest_expected!r}")
    print(f"  Actual output:   {smallest_actual!r}")
    print(f"  Intermediate:    {json.dumps(smallest_breakdown, sort_keys=True)}")
    print("\nAll Question 6 checks passed.")


if __name__ == "__main__":
    main()
