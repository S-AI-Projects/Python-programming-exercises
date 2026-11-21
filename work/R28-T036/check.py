import sys, subprocess, os, re

here = os.path.dirname(os.path.abspath(__file__))
mdPath = os.path.join(here, '..', '..', '100+ Python challenging programming exercises for Python 3.md')

def getCode(mdPath):
    f = open(mdPath, 'r', encoding='utf-8')
    txt = f.read()
    f.close()
    qPat = r"### Question 63\n(.*?)(?=### Question 64)"
    m = re.search(qPat, txt, re.S)
    if not m:
        print('question 63 not found')
        sys.exit(1)
    sec = m.group(1)

    codePat = r"Solution:\s*```python\n(.*?)```"
    codeM = re.search(codePat, sec, re.S)
    if not codeM:
        print('code block not found')
        sys.exit(1)
    return codeM.group(1).strip()

def runCode(code, inp=""):
    tmp = os.path.join(here, 'tmp_check_script.py')
    f = open(tmp, 'w', encoding='utf-8')
    f.write(code)
    f.close()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run([sys.executable, tmp], input=inp, capture_output=True, text=True, encoding="utf-8", env=env)
    if os.path.exists(tmp):
        os.remove(tmp)
    if res.returncode != 0:
        print('crash')
        print(res.stderr)
        sys.exit(1)
    return res

def main():
    code = getCode(mdPath)

    # assert stated property: PEP 263 encoding declaration comment is utf-8
    pep263Pat = r"coding[:=]\s*([-\w.]+)"
    m = re.search(pep263Pat, code)
    assert m
    enc = m.group(1)
    print("Expected encoding: utf-8")
    print("Actual encoding:", enc)
    assert enc == "utf-8"

    # run original solution (no input arguments, prints empty output)
    res = runCode(code)
    exp = ""
    act = res.stdout
    print("Expected:", repr(exp))
    print("Actual:", repr(act))
    assert act == exp
    assert res.returncode == 0

    # smallest input / stated property check (no input, clean exit)
    smallRes = runCode(code, "")
    assert smallRes.stdout == ""
    assert smallRes.returncode == 0
    print("Smallest input run passed")

    # intermediate values: concrete unicode character 'é'
    added1 = "\ns = 'é'\nprint('char: %s' % s)\nprint('codepoint: %d' % ord(s))\nprint('utf-8 bytes: %s' % list(s.encode('utf-8')))\n"
    subCode1 = code + added1
    assert "s = 'é'" in subCode1
    res1 = runCode(subCode1)
    act1 = res1.stdout
    exp1 = "char: é\ncodepoint: 233\nutf-8 bytes: [195, 169]\n"
    print("Intermediate 'é' expected:\n" + exp1)
    print("Intermediate 'é' actual:\n" + act1)
    assert act1 == exp1

    # intermediate values: smallest ASCII input character 'a'
    added2 = "\ns = 'a'\nprint('char: %s' % s)\nprint('codepoint: %d' % ord(s))\nprint('utf-8 bytes: %s' % list(s.encode('utf-8')))\n"
    subCode2 = code + added2
    assert "s = 'a'" in subCode2
    res2 = runCode(subCode2)
    act2 = res2.stdout
    exp2 = "char: a\ncodepoint: 97\nutf-8 bytes: [97]\n"
    print("Intermediate 'a' expected:\n" + exp2)
    print("Intermediate 'a' actual:\n" + act2)
    assert act2 == exp2

    # deliberate wrong-result self-test
    badExp = "char: é\ncodepoint: 233\nutf-8 bytes: [195, 170]\n"
    if act1 == badExp:
        print("wrong result check failed: accepted wrong byte value")
        sys.exit(1)
    print("wrong result correctly rejected")

    print("all checks passed")

if __name__ == '__main__':
    main()
