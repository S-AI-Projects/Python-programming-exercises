import sys, subprocess, os, re

here = os.path.dirname(os.path.abspath(__file__))
mdPath = os.path.join(here, '..', '..', '100+ Python challenging programming exercises for Python 3.md')

def getCode(mdPath):
    f = open(mdPath, 'r', encoding='utf-8')
    txt = f.read()
    f.close()
    pat = r"### Question 30\n.*?Solution\n```python\n(.*?)```"
    m = re.search(pat, txt, re.S)
    if not m:
        print('code block not found')
        sys.exit(1)
    return m.group(1).strip()

def run(code):
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

def main():
    code = getCode(mdPath)

    # published example
    res = run(code)
    exp = "34\n"
    act = res.stdout
    print("Expected:", repr(exp))
    print("Actual:", repr(act))
    assert act == exp

    # boundary case with empty string
    boundCode = code + '\nprintValue("","5")\n'
    boundRes = run(boundCode)
    boundExp = "34\n5\n"
    boundAct = boundRes.stdout
    print("Boundary expected:", repr(boundExp))
    print("Boundary actual:", repr(boundAct))
    assert boundAct == boundExp

    # int contrast case
    intCode = code + '\nprintValue(3,4)\n'
    intRes = run(intCode)
    intExp = "34\n7\n"
    intAct = intRes.stdout
    print("Int contrast expected:", repr(intExp))
    print("Int contrast actual:", repr(intAct))
    assert intAct == intExp

    # deliberate wrong-result self-test, comparing real output against "7\n"
    badExp = "7\n"
    if act == badExp:
        print("wrong result check failed: accepted wrong value")
        sys.exit(1)
    print("wrong result correctly rejected")

    print("all checks passed")

if __name__ == '__main__':
    main()
