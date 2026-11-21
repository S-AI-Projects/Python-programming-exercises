import sys, subprocess, os, re

here = os.path.dirname(os.path.abspath(__file__))
mdPath = os.path.join(here, '..', '..', '100+ Python challenging programming exercises for Python 3.md')

def getMdParts(mdPath):
    f = open(mdPath, 'r', encoding='utf-8')
    txt = f.read()
    f.close()
    qPat = r"### Question 22\n(.*?)(?=### Question 23)"
    m = re.search(qPat, txt, re.S)
    if not m:
        print('question 22 not found')
        sys.exit(1)
    sec = m.group(1)

    inPat = r"Suppose the following input is supplied to the program:\n(.*?)\nThen, the output should be:"
    inM = re.search(inPat, sec, re.S)
    if not inM:
        print('published input not found')
        sys.exit(1)
    pubInp = inM.group(1).strip()

    outPat = r"Then, the output should be:\n(.*?)\n\nHints"
    outM = re.search(outPat, sec, re.S)
    if not outM:
        print('published output not found')
        sys.exit(1)
    pubOut = outM.group(1).strip() + "\n"

    codePat = r"Solution:\s*```python\n(.*?)```"
    codeM = re.search(codePat, sec, re.S)
    if not codeM:
        print('code block not found')
        sys.exit(1)
    code = codeM.group(1).strip()

    return code, pubInp, pubOut

def runCode(code, inp):
    tmp = os.path.join(here, 'tmp_check_script.py')
    f = open(tmp, 'w', encoding='utf-8')
    f.write(code)
    f.close()
    res = subprocess.run([sys.executable, tmp], input=inp, capture_output=True, text=True)
    if os.path.exists(tmp):
        os.remove(tmp)
    if res.returncode != 0:
        print('crash')
        print(res.stderr)
        sys.exit(1)
    return res

def main():
    code, pubInp, pubOut = getMdParts(mdPath)

    # published example
    res = runCode(code, pubInp + "\n")
    act = res.stdout
    print("Expected:\n" + pubOut)
    print("Actual:\n" + act)
    assert act == pubOut

    # smallest input case: "a" gives "a:1\n"
    smallRes = runCode(code, "a\n")
    smallAct = smallRes.stdout
    smallExp = "a:1\n"
    print("Smallest expected:", repr(smallExp))
    print("Smallest actual:", repr(smallAct))
    assert smallAct == smallExp

    # intermediate-state claim: append print(freq) for short input "b a b"
    claimCode = code + "\nprint(freq)\n"
    assert "\nprint(freq)" in claimCode
    claimRes = runCode(claimCode, "b a b\n")
    claimAct = claimRes.stdout
    expectedDictRepr = "{'b': 2, 'a': 1}"
    print("Intermediate dict expected:", expectedDictRepr)
    print("Intermediate claim output:\n" + claimAct)
    assert expectedDictRepr in claimAct

    # deliberate wrong-result self-test
    # 1. wrong count test
    badOut1 = pubOut.replace("Python:5", "Python:4")
    if act == badOut1:
        print("wrong result check failed: accepted wrong count")
        sys.exit(1)

    # 2. unsorted lines test
    lines = pubOut.strip().split("\n")
    unsortedOut = "\n".join(reversed(lines)) + "\n"
    if act == unsortedOut:
        print("wrong result check failed: accepted unsorted lines")
        sys.exit(1)

    print("wrong result correctly rejected")
    print("all checks passed")

if __name__ == '__main__':
    main()
