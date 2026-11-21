import sys, subprocess, os, re, ast

here = os.path.dirname(os.path.abspath(__file__))
mdPath = os.path.join(here, '..', '..', '100+ Python challenging programming exercises for Python 3.md')

def getBlocks(mdPath):
    f = open(mdPath, 'r', encoding='utf-8')
    txt = f.read()
    f.close()

    qPat = r"### Question 80\n(.*?)(?=### Question 81)"
    m = re.search(qPat, txt, re.S)
    if not m:
        print('question 80 not found')
        sys.exit(1)
    sec = m.group(1)

    solPat = r"Solution:\s*```python\n(.*?)```"
    solM = re.search(solPat, sec, re.S)
    if not solM:
        print('solution code block not found')
        sys.exit(1)
    solCode = solM.group(1).strip()

    expPat = r"Experiment:\s*```python\n(.*?)```"
    expM = re.search(expPat, sec, re.S)
    if not expM:
        print('experiment code block not found')
        sys.exit(1)
    expCode = expM.group(1).strip()

    return solCode, expCode

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

def checkProperties(li, k=5):
    assert isinstance(li, list)
    assert len(li) == k
    assert len(set(li)) == len(li)
    for x in li:
        assert isinstance(x, int)
        assert 1 <= x <= 1000
        assert x % 5 == 0 and x % 7 == 0

def main():
    solCode, expCode = getBlocks(mdPath)

    # 1. test solution properties over 20 runs
    for i in range(20):
        res = runCode(solCode)
        act = ast.literal_eval(res.stdout.strip())
        checkProperties(act, k=5)
    print("Expected: 5 distinct multiples of 35 between 1 and 1000")
    print("Actual (sample run):", act)
    print("All 20 solution runs passed property check")

    # 2. smallest supported input k = 1
    sub1 = ", 1)"
    subCode1 = re.sub(r",\s*5\)", sub1, solCode)
    assert sub1 in subCode1
    res1 = runCode(subCode1)
    act1 = ast.literal_eval(res1.stdout.strip())
    checkProperties(act1, k=1)
    print("k = 1 expected: 1 multiple of 35 in 1..1000")
    print("k = 1 actual:", act1)

    # empty-result contrast k = 0
    sub0 = ", 0)"
    subCode0 = re.sub(r",\s*5\)", sub0, solCode)
    assert sub0 in subCode0
    res0 = runCode(subCode0)
    act0 = ast.literal_eval(res0.stdout.strip())
    checkProperties(act0, k=0)
    print("k = 0 expected: []")
    print("k = 0 actual:", act0)

    # 3. experiment check
    expRes = runCode(expCode)
    expOut = expRes.stdout.strip()
    expExpected = """len(pop): 28
len(picked): 5
pop unchanged: True
different object: True
all in pop and no repeats: True"""
    print("Experiment expected:\n" + expExpected)
    print("Experiment actual:\n" + expOut)
    assert expOut == expExpected
    print("Experiment output matches doc exactly")

    # 4. deliberate wrong-result self-test
    # reject repeat
    bad1 = [35, 70, 70, 105, 140]
    try:
        checkProperties(bad1, k=5)
    except AssertionError:
        print("wrong result (repeat) correctly rejected")
    else:
        print("wrong result check failed: accepted repeat")
        sys.exit(1)

    # reject non-multiple of 35
    bad2 = [35, 70, 105, 140, 36]
    try:
        checkProperties(bad2, k=5)
    except AssertionError:
        print("wrong result (non-multiple) correctly rejected")
    else:
        print("wrong result check failed: accepted non-multiple")
        sys.exit(1)

    print("all checks passed")

if __name__ == '__main__':
    main()
