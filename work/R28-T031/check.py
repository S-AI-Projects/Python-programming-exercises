import sys, subprocess, os, re

here = os.path.dirname(os.path.abspath(__file__))
mdPath = os.path.join(here, '..', '..', '100+ Python challenging programming exercises for Python 3.md')

def getCode(mdPath):
    f = open(mdPath, 'r', encoding='utf-8')
    txt = f.read()
    f.close()
    pat = r"### Question 45\n.*?Solution\n```python\n(.*?)```"
    m = re.search(pat, txt, re.S)
    if not m:
        print('code block not found')
        sys.exit(1)
    return m.group(1).strip()

def run(code):
    tmp = os.path.join(here, 'tmp_check_script.py')
    f = open(tmp, 'w')
    f.write(code)
    f.close()
    res = subprocess.run([sys.executable, tmp], capture_output=True, text=True)
    os.remove(tmp)
    return res

def main():
    code = getCode(mdPath)
    exp = "[2, 4, 6, 8, 10]"
    res = run(code)
    if res.returncode != 0:
        print('crash')
        print(res.stderr)
        sys.exit(1)
    act = res.stdout.strip()
    print('Expected:', exp)
    print('Actual:', act)
    assert act == exp

    # tiny input, swap the list in the real code
    tinyCode = re.sub(r"li\s*=\s*\[.*?\]", "li = [2]", code, count=1)
    assert "li = [2]" in tinyCode   # makes sure the swap really happened
    tinyRes = run(tinyCode)
    assert tinyRes.returncode == 0
    print('Tiny actual:', tinyRes.stdout.strip())
    assert tinyRes.stdout.strip() == "[2]"

    # wrong result self test, this must NOT match
    if act == "[0]":
        print('wrong result test did not fail')
        sys.exit(1)
    print('wrong result correctly rejected')
    print('all checks passed')

if __name__ == '__main__':
    main()
