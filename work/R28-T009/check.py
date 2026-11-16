#!/usr/bin/env python3
"""Verify Question 91's output and list-copy/resource explanation."""

from __future__ import annotations

import json
import platform
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MARKDOWN = ROOT / "100+ Python challenging programming exercises for Python 3.md"
WORK = Path(__file__).resolve().parent


def extract_section() -> str:
    text = MARKDOWN.read_text(encoding="utf-8")
    section = re.search(r"### Question 91(.*?)(?=### Question 92|\Z)", text, re.S)
    if not section:
        raise AssertionError("Question 91 section was not found")
    return section.group(1)


def extract_code_blocks(section: str) -> list[str]:
    return [block.strip() for block in re.findall(r"```python\s*(.*?)```", section, re.S)]


def run(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )


def main() -> None:
    section = extract_section()
    assert "Resource behavior:" in section
    assert "O(n)" in section and "additional space" in section
    blocks = extract_code_blocks(section)
    assert len(blocks) >= 2, "expected the solution and resource experiment blocks"
    solution, experiment = blocks[:2]

    published_result = run(solution)
    assert published_result.returncode == 0, published_result.stderr
    published = published_result.stdout.strip()
    assert published == "[24, 35, 70, 155]", published

    experiment_result = run(experiment)
    assert experiment_result.returncode == 0, experiment_result.stderr
    experiment_output = experiment_result.stdout.strip()
    expected_experiment = (
        "[24, 35, 70, 155]\n"
        "[12, 24, 35, 70, 88, 120, 155]\n"
        "False"
    )
    assert experiment_output == expected_experiment, experiment_output

    empty_experiment = experiment.replace(
        "source = [12,24,35,70,88,120,155]", "source = []", 1
    )
    empty_result = run(empty_experiment)
    assert empty_result.returncode == 0, empty_result.stderr
    assert empty_result.stdout.strip() == "[]\n[]\nFalse"

    # Deliberately keep the removed indexes instead; the published fixture must catch it.
    mutant = solution.replace("i not in (0,4,5)", "i in (0,4,5)", 1)
    mutant_result = run(mutant)
    assert mutant_result.returncode == 0, mutant_result.stderr
    assert mutant_result.stdout.strip() != published

    (WORK / "inputs.json").write_text(
        json.dumps(
            {
                "published_list": [12, 24, 35, 70, 88, 120, 155],
                "removed_indexes": [0, 4, 5],
                "smallest_collection": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (WORK / "expected_output.txt").write_text(
        "published: [24, 35, 70, 155]\n"
        "experiment: [24, 35, 70, 155] / [12, 24, 35, 70, 88, 120, 155] / False\n"
        "empty experiment: [] / [] / False\n",
        encoding="utf-8",
    )
    (WORK / "actual_output.txt").write_text(
        f"published: {published}\nexperiment:\n{experiment_output}\n"
        f"empty experiment:\n{empty_result.stdout.strip()}\n",
        encoding="utf-8",
    )
    (WORK / "python_version.txt").write_text(sys.version + "\n", encoding="utf-8")
    (WORK / "tool_versions.txt").write_text(
        f"Python: {sys.version.split()[0]}\nPlatform: {platform.platform()}\n",
        encoding="utf-8",
    )
    (WORK / "test_results.txt").write_text(
        "R28-T009 PASS\n"
        "Executed the exact Question 91 solution and the documented resource experiment.\n"
        "Verified output, new-list identity, empty collection behavior, and mutant detection.\n",
        encoding="utf-8",
    )
    print("R28-T009 PASS: resource behavior, output, and mutant checks succeeded")


if __name__ == "__main__":
    main()
