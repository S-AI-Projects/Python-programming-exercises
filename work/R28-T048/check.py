#!/usr/bin/env python3
"""Check script for Question 57 (Task R28-T048)."""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

# Paths relative to this script
WORK_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_PATH = REPO_ROOT / "100+ Python challenging programming exercises for Python 3.md"


def extract_question_57_data() -> tuple[str, str]:
    """Extract the solution code and instantiation argument from Question 57 in markdown."""
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Markdown file not found: {MARKDOWN_PATH}")

    content = MARKDOWN_PATH.read_text(encoding="utf-8")

    match = re.search(
        r"^### Question 57\s*\n(.*?)(?=^### Question 58\s*\n)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise ValueError("Could not find Question 57 section in markdown")

    section = match.group(1)

    code_match = re.search(r"Solution:\s*\n+```(?:python)?\s*\n(.*?)\n```", section, re.DOTALL)
    if not code_match:
        raise ValueError("Could not find solution code block in Question 57")

    code = code_match.group(1).strip()

    # Extract instantiation argument directly from code
    arg_match = re.search(r'error\s*=\s*MyError\(["\'](.*?)["\']\)', code)
    if not arg_match:
        raise ValueError("Could not extract MyError argument from solution code")
    published_arg = arg_match.group(1)

    return code, published_arg


def run_code(code: str) -> subprocess.CompletedProcess[str]:
    """Execute code in a subprocess without stdin using sys.executable."""
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )


def record_evidence(
    published_msg: str,
    published_args: tuple[str, ...],
    published_str: str,
    smallest_msg: str,
    type_error_raised: bool,
) -> None:
    """Write the required 4 evidence files into WORK_DIR."""
    # 1. inputs.json
    inputs_data = {
        "input": None,
        "description": "Question 57 defines custom exception MyError with attribute msg and instantiates it.",
        "published_instantiation": f"MyError({published_msg!r})",
        "smallest_instantiation": "MyError('')",
        "invalid_instantiation": "MyError() raises TypeError",
    }
    (WORK_DIR / "inputs.json").write_text(
        json.dumps(inputs_data, indent=2) + "\n", encoding="utf-8"
    )

    # 2. expected_vs_actual.txt
    comparison_text = (
        "=== Published Question 57 Verification ===\n"
        f"Published error.msg:           {published_msg!r}\n"
        f"Published error.args:          {published_args!r}\n"
        f"str(error):                    {published_str!r}\n"
        f"Matches msg attribute:         {published_str == published_msg}\n\n"
        "=== Smallest Supported Input Verification ===\n"
        f"Smallest error.msg:            {smallest_msg!r}\n"
        f"Matches '':                    {smallest_msg == ''}\n\n"
        "=== Limitation / Misconception Verification ===\n"
        f"Zero-argument call raised TypeError: {type_error_raised}\n"
    )
    (WORK_DIR / "expected_vs_actual.txt").write_text(comparison_text, encoding="utf-8")

    # 3. tool_versions.txt (Python version and OS name only)
    versions_text = (
        f"Python: {platform.python_version()}\n"
        f"OS: {platform.system()}\n"
    )
    (WORK_DIR / "tool_versions.txt").write_text(versions_text, encoding="utf-8")

    # 4. failing_check_output.txt
    failing_proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--wrong"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert failing_proc.returncode != 0, (
        "Expected check.py --wrong to exit with non-zero code, but got 0"
    )
    (WORK_DIR / "failing_check_output.txt").write_text(
        f"Return code: {failing_proc.returncode}\n"
        f"Stdout:\n{failing_proc.stdout}\n"
        f"Stderr:\n{failing_proc.stderr}\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Question 57 solution")
    parser.add_argument(
        "--wrong",
        action="store_true",
        help="Run check with deliberately wrong expected output to test failure",
    )
    args = parser.parse_args()

    code, published_arg = extract_question_57_data()

    expected_msg = "deliberately_wrong" if args.wrong else published_arg

    # 1. Test published solution via subprocess
    res = run_code(code)
    if res.returncode != 0:
        sys.stderr.write(f"Process failed with exit code {res.returncode}:\n{res.stderr}\n")
        sys.exit(res.returncode)

    assert res.stdout == "", f"Expected empty stdout from published code, got {res.stdout!r}"

    # Verify namespace objects
    env: dict = {}
    exec(code, env)
    my_error_cls = env.get("MyError")
    error_obj = env.get("error")

    assert my_error_cls is not None, "MyError class not defined in code"
    assert issubclass(my_error_cls, Exception), "MyError must inherit from Exception"
    assert isinstance(error_obj, my_error_cls), "error must be an instance of MyError"
    assert isinstance(error_obj, Exception), "error must be an instance of Exception"

    if error_obj.msg != expected_msg:
        sys.stderr.write(
            f"AssertionError: Expected error.msg to be {expected_msg!r}, got {error_obj.msg!r}\n"
        )
        sys.exit(1)

    # BaseException.__new__ sets args; str and repr reflect args
    assert error_obj.args == (published_arg,), f"Expected args { (published_arg,) }, got {error_obj.args}"
    assert str(error_obj) == published_arg, f"Expected str(error) == {published_arg!r}, got {str(error_obj)!r}"
    assert repr(error_obj) == f"MyError({published_arg!r})", f"repr mismatch: {repr(error_obj)!r}"

    # 2. Test smallest supported input: empty string
    smallest_err = my_error_cls("")
    assert smallest_err.msg == "", f"Expected empty string msg, got {smallest_err.msg!r}"
    assert smallest_err.args == ("",), f"Expected ('',) args, got {smallest_err.args!r}"
    assert str(smallest_err) == "", f"Expected empty str(error), got {str(smallest_err)!r}"

    # 3. Test limitation / misconception: zero arguments raises TypeError
    type_error_raised = False
    try:
        my_error_cls()
    except TypeError:
        type_error_raised = True
    except Exception as e:
        sys.stderr.write(f"Expected TypeError, got {type(e).__name__}\n")
        sys.exit(1)

    assert type_error_raised, "Expected TypeError when calling MyError() without arguments"

    if not args.wrong:
        record_evidence(
            published_msg=error_obj.msg,
            published_args=error_obj.args,
            published_str=str(error_obj),
            smallest_msg=smallest_err.msg,
            type_error_raised=type_error_raised,
        )
        print("R28-T048 PASS: Question 57 MyError contract and limitation verified successfully.")


if __name__ == "__main__":
    main()
