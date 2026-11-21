import sys, subprocess, os, re, ast

here = os.path.dirname(os.path.abspath(__file__))
mdPath = os.path.join(here, '..', '..', '100+ Python challenging programming exercises for Python 3.md')

def getCode(mdPath):
    f = open(mdPath, 'r', encoding='utf-8')
    txt = f.read()
    f.close()
    qPat = r"### Question 85\n(.*?)(?=### Question 86)"
    m = re.search(qPat, txt, re.S)
    if not m:
        print('question 85 not found')
        sys.exit(1)
    sec = m.group(1)

    codePat = r"Solution:\s*```python\n(.*?)```"
    codeM = re.search(codePat, sec, re.S)
    if not codeM:
        print('code block not found')
        sys.exit(1)
    return codeM.group(1).strip()

def runCode(code):
    tmp = os.path.join(here, 'tmp_check_script.py')
    f = open(tmp, 'w', encoding='utf-8')
    f.write(code)
    f.close()
    res = subprocess.run([sys.executable, tmp], capture_output=True, text=True)
    if os.path.exists(tmp):
        os.remove(tmp)
    if res.returncode != 0:
        print('crash')
        print(res.stderr)
        sys.exit(1)
    return res

def checkPermutation(actVal):
    assert isinstance(actVal, list)
    assert len(actVal) == 4
    assert sorted(actVal) == [3, 6, 7, 8]

def main():
    code = getCode(mdPath)

    # test fixture permutation across 20 runs
    expSorted = [3, 6, 7, 8]
    print("Expected sorted elements:", expSorted)
    for i in range(20):
        res = runCode(code)
        actVal = ast.literal_eval(res.stdout.strip())
        checkPermutation(actVal)
    print("Actual (last run):", actVal)
    print("All 20 random permutation runs passed")

    # smallest input: li = [1] -> [1]
    sub1 = "li = [1]"
    subCode1 = re.sub(r"li\s*=\s*\[.*?\]", sub1, code, count=1)
    assert sub1 in subCode1
    res1 = runCode(subCode1)
    print("Smallest [1] expected: [1]")
    print("Smallest [1] actual:", res1.stdout.strip())
    assert res1.stdout == "[1]\n"

    # empty list contrast: li = [] -> []
    sub0 = "li = []"
    subCode0 = re.sub(r"li\s*=\s*\[.*?\]", sub0, code, count=1)
    assert sub0 in subCode0
    res0 = runCode(subCode0)
    print("Empty [] expected: []")
    print("Empty [] actual:", res0.stdout.strip())
    assert res0.stdout == "[]\n"

    # misconception: print(shuffle(li)) prints None because shuffle works in place
    added = "\nprint(shuffle(li))\n"
    misCode = code + added
    assert added in misCode
    misRes = runCode(misCode)
    lines = misRes.stdout.strip().split("\n")
    print("Misconception last line expected: None")
    print("Misconception last line actual:", lines[-1])
    assert lines[-1] == "None"

    # deliberate wrong-result self-test: missing/repeated element [3, 6, 7, 7]
    badVal = [3, 6, 7, 7]
    try:
        checkPermutation(badVal)
    except AssertionError:
        print("wrong result correctly rejected")
    else:
        print("wrong result check failed: accepted invalid permutation")
        sys.exit(1)

    print("all checks passed")

if __name__ == '__main__':
    main()

