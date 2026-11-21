import sys, subprocess, os, re, ast

here = os.path.dirname(os.path.abspath(__file__))
mdPath = os.path.join(here, '..', '..', '100+ Python challenging programming exercises for Python 3.md')

def getCode(mdPath):
    f = open(mdPath, 'r', encoding='utf-8')
    txt = f.read()
    f.close()
    pat = r"### Question 46\n.*?Solution\n```python\n(.*?)```"
    m = re.search(pat, txt, re.S)
    if not m:
        print('code block not found')
        sys.exit(1)
    return m.group(1).strip()

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

def checkInvariant(inp, act):
    assert isinstance(act, list)
    assert len(act) == len(inp)
    for i in range(len(inp)):
        assert act[i] == inp[i]**2
        assert act[i] >= 0

def main():
    code = getCode(mdPath)

    # published fixture: li = [1,2,3,4,5,6,7,8,9,10]
    fixRes = runCode(code)
    fixExpStr = "[1, 4, 9, 16, 25, 36, 49, 64, 81, 100]\n"
    print("Expected:", repr(fixExpStr))
    print("Actual:", repr(fixRes.stdout))
    assert fixRes.stdout == fixExpStr
    fixVal = ast.literal_eval(fixRes.stdout.strip())
    checkInvariant([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], fixVal)

    # bounded variations (including smallest input [3])
    variations = [
        [],
        [0],
        [1],
        [3],
        [-3, 3],
        [2, 4, 6],
        [10, 20, 30]
    ]

    for inp in variations:
        sub = f"li = {inp}"
        subCode = re.sub(r"li\s*=\s*\[.*?\]", sub, code, count=1)
        assert sub in subCode
        res = runCode(subCode)
        act = ast.literal_eval(res.stdout.strip())
        exp = [x**2 for x in inp]
        print(f"Variation inp={inp}")
        print("Expected:", exp)
        print("Actual:", act)
        checkInvariant(inp, act)
        assert act == exp
        if inp == [3]:
            # smallest input check
            assert act == [9]
            print("Smallest input [3] gave [9]")

    # deliberate wrong-result self-test
    badInp = [1, 2, 3]
    badAct = [1, 2, 9]
    try:
        checkInvariant(badInp, badAct)
    except AssertionError:
        print("wrong result correctly rejected")
    else:
        print("wrong result check failed: accepted unsquared value")
        sys.exit(1)

    print("all checks passed")

if __name__ == '__main__':
    main()
