#!/usr/bin/env python3
"""Focused verification check for Task R28-T060 (Question 89)."""

from __future__ import annotations

import ast
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTICLE_PATH = REPO_ROOT / "100+ Python challenging programming exercises for Python 3.md"
WORK_DIR = Path(__file__).resolve().parent

PUBLISHED_INPUT = [12, 24, 35, 70, 88, 120, 155]
PUBLISHED_EXPECTED = [24, 70, 120]
SMALLEST_INPUT = [12]
SMALLEST_EXPECTED: list[int] = []


def extract_question_89_code(markdown_text: str) -> str:
    """Extract the code block under Question 89 (supporting any heading level and fence)."""
    section_match = re.search(
        r"(?ms)^#{1,6}\s*Question\s+89\b(.*?)(?=^#{1,6}\s*Question\s+90\b|\Z)",
        markdown_text,
    )
    section = section_match.group(1) if section_match else markdown_text

    # Match fenced code blocks first (``` or ```python), or fallback to `li = [...]` lines
    fence_match = re.search(r"(?ms)^[ \t]*```[^\n]*\n(.*?)^[ \t]*```", section)
    if fence_match:
        candidate = fence_match.group(1).strip()
        if candidate:
            return candidate

    lines = section.splitlines()
    code_lines = [
        line.strip()
        for line in lines
        if re.match(r"^(li\s*=|print\s*\()", line.strip())
    ]
    if code_lines:
        return "\n".join(code_lines)

    raise RuntimeError(
        "Could not locate Question 89 code block in 100+ Python challenging programming exercises for Python 3.md."
    )


def build_snippet_for_input(base_code: str, input_list: list[int]) -> str:
    """Replace the `li` list assignment in `base_code` via AST while keeping `enumerate` and `print`."""
    tree = ast.parse(base_code)
    updated_nodes: list[ast.stmt] = []
    replaced_li = False

    for stmt in tree.body:
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and stmt.targets[0].id == "li"
            and isinstance(stmt.value, ast.List)
        ):
            stmt.value = ast.parse(repr(input_list), mode="eval").body
            replaced_li = True
        updated_nodes.append(stmt)

    if not replaced_li:
        raise RuntimeError("Could not find `li = [...]` assignment inside extracted Question 89 code.")

    module = ast.Module(body=updated_nodes, type_ignores=[])
    ast.fix_missing_locations(module)
    return ast.unparse(module)


def execute_python_code(code: str) -> tuple[list[int], str]:
    """Run Python code in a subprocess and propagate non-zero exit codes on failure."""
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    stdout = proc.stdout.strip()
    parsed = ast.literal_eval(stdout)
    if not isinstance(parsed, list):
        raise AssertionError(f"Expected list output, got {type(parsed).__name__}: {stdout}")
    return parsed, stdout


def make_one_operation_mutant(code: str) -> str:
    """Create a temporary one-operation mutant by flipping `!=` to `==` in the index filter."""
    mutated = re.sub(r"\b(i\s*%\s*2)\s*!=\s*0\b", r"\1 == 0", code, count=1)
    if mutated == code:
        raise RuntimeError("Failed to create one-operation mutant (`i % 2 != 0` -> `i % 2 == 0`).")
    return mutated


def verify_deliberate_failure_exits_nonzero(code: str) -> dict[str, object]:
    """Confirm a deliberate wrong assertion causes a non-zero subprocess exit."""
    snippet = build_snippet_for_input(code, PUBLISHED_INPUT)
    failing_script = f"{snippet}\nassert li == [12, 35, 88], f'Deliberate mismatch: {{li}}'\n"
    proc = subprocess.run(
        [sys.executable, "-c", failing_script],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        raise RuntimeError("Deliberate wrong assertion unexpectedly exited with code 0.")
    return {
        "returncode": proc.returncode,
        "failed_as_expected": True,
        "stderr_summary": proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "",
    }


def main() -> int:
    if not ARTICLE_PATH.exists():
        print(f"ERROR: Article not found: {ARTICLE_PATH}", file=sys.stderr)
        return 1

    try:
        markdown_text = ARTICLE_PATH.read_text(encoding="utf-8")
        extracted_code = extract_question_89_code(markdown_text)

        test_cases = [
            {
                "name": "published_example",
                "input": PUBLISHED_INPUT,
                "expected": PUBLISHED_EXPECTED,
            },
            {
                "name": "smallest_supported_input",
                "input": SMALLEST_INPUT,
                "expected": SMALLEST_EXPECTED,
            },
        ]

        case_results = []
        for case in test_cases:
            snippet = build_snippet_for_input(extracted_code, case["input"])
            actual, raw_stdout = execute_python_code(snippet)
            if actual != case["expected"]:
                print(
                    f"FAIL [{case['name']}]: expected {case['expected']}, got {actual}",
                    file=sys.stderr,
                )
                return 1
            case_results.append(
                {
                    "case": case["name"],
                    "input": case["input"],
                    "expected": case["expected"],
                    "actual": actual,
                    "raw_stdout": raw_stdout,
                    "passed": True,
                }
            )

        # Temporary one-operation mutant check (not committed as production code)
        mutant_code = make_one_operation_mutant(extracted_code)
        mutant_pub_actual, _ = execute_python_code(build_snippet_for_input(mutant_code, PUBLISHED_INPUT))
        mutant_min_actual, _ = execute_python_code(build_snippet_for_input(mutant_code, SMALLEST_INPUT))

        distinguished = (mutant_pub_actual != PUBLISHED_EXPECTED) and (
            mutant_min_actual != SMALLEST_EXPECTED
        )
        if not distinguished:
            print(
                "FAIL [mutant]: one-operation mutant was not distinguished from expected outputs.",
                file=sys.stderr,
            )
            return 1

        deliberate_fail_info = verify_deliberate_failure_exits_nonzero(extracted_code)

        git_proc = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, check=False
        )
        tool_versions = {
            "python": sys.version.replace("\n", " "),
            "platform": platform.platform(),
            "git": git_proc.stdout.strip() if git_proc.returncode == 0 else "unavailable",
        }

        WORK_DIR.mkdir(parents=True, exist_ok=True)
        (WORK_DIR / "inputs.json").write_text(
            json.dumps(
                [{"name": c["name"], "input": c["input"]} for c in test_cases],
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (WORK_DIR / "results.json").write_text(
            json.dumps(
                {
                    "extracted_code": extracted_code,
                    "cases": case_results,
                    "one_operation_mutant": {
                        "mutation": "i % 2 != 0 -> i % 2 == 0",
                        "published_input_output": mutant_pub_actual,
                        "smallest_input_output": mutant_min_actual,
                        "distinguished": distinguished,
                    },
                    "deliberate_wrong_result_check": deliberate_fail_info,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (WORK_DIR / "tool_versions.txt").write_text(
            "\n".join(f"{k}: {v}" for k, v in tool_versions.items()) + "\n",
            encoding="utf-8",
        )

    except subprocess.CalledProcessError as exc:
        print(
            f"FAIL [subprocess]: exited with {exc.returncode}\nSTDERR:\n{exc.stderr}",
            file=sys.stderr,
        )
        return exc.returncode or 1
    except Exception as exc:
        print(f"FAIL [check]: {exc}", file=sys.stderr)
        return 1

    print("PASS: Question 89 verified (published + smallest input + mutant + failure check).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
