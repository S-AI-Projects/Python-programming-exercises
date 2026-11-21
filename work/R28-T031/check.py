import sys, subprocess, os, re

def getCode(mdPath):
    f = open(mdPath, 'r')
    txt = f.read()
    f.close()
    pat = r"### Question 45\n.*?Solution\n```python\n(.*?)```"
    m = re.search(pat, txt, re.S)
    if not m:
        print('code block not found')
        sys.exit(1)
    return m.group(1).strip()

def run(code, inp=''):
    tmp = 'tmp_check_script.py'
    open(tmp, 'w').write(code)
    # run the temp script
    res = subprocess.run([sys.executable, tmp], input=inp if inp else None, capture_output=True, text=True)
    os.remove(tmp)
    return res

def main():
    mdPath = '/Users/saisushrith/SnAi /Python-programming-exercises/100+ Python challenging programming exercises for Python 3.md'
    code = getCode(mdPath)
    exp = "[2, 4, 6, 8, 10]"
    res = run(code)
    if res.returncode != 0:
        print('crash')
        sys.exit(1)
    act = res.stdout.strip()
    print('Expected:', exp)
    print('Actual:', act)
    assert act == exp
    # tiny input test
    tiny = "li = [2]\n" + "evenNumbers = filter(lambda x: x%2==0, li)\nprint(list(evenNumbers))"
    tinyRes = run(tiny)
    assert tinyRes.stdout.strip() == "[2]"
    # wrong‑result self‑test (should fail)
    bad = "li = [1,2,3]\n" + "evenNumbers = filter(lambda x: x%2==0, li)\nprint([0])"
    badRes = run(bad)
    try:
        assert badRes.stdout.strip() == "[2]"
    except AssertionError:
        # expected failure
        pass
    else:
        print('wrong‑result test did not fail')
        sys.exit(1)
    print('all checks passed')

if __name__ == '__main__':
    main()
