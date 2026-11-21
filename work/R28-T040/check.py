import sys, subprocess, os, re, ast, tempfile

here = os.path.dirname(os.path.abspath(__file__))
mdPath = os.path.join(here, '..', '..', '100+ Python challenging programming exercises for Python 3.md')

def getCode(mdPath):
    f = open(mdPath, 'r', encoding='utf-8')
    txt = f.read()
    f.close()

    qPat = r"### Question 93\n(.*?)(?=### Question 94)"
    m = re.search(qPat, txt, re.S)
    if not m:
        print('question 93 not found')
        sys.exit(1)
    sec = m.group(1)

    codePat = r"Solution:\s*```python\n(.*?)```"
    codeM = re.search(codePat, sec, re.S)
    if not codeM:
        print('solution code block not found')
        sys.exit(1)
    return codeM.group(1).strip()

def runCode(code):
    fd, tmp = tempfile.mkstemp(prefix='mut_', suffix='.py')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(code)
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

    # 1. run real example and assert published output
    res = runCode(code)
    exp = "[35]\n"
    act = res.stdout
    print("Expected:", repr(exp))
    print("Actual:", repr(act))
    assert act == exp
    actVal = ast.literal_eval(act.strip())
    assert actVal == [35]

    # 2. small input: set([1]) and set([1]) giving [1]
    subCode = re.sub(r"set1=set\(\[.*?\]\)", "set1=set([1])", code, count=1)
    subCode = re.sub(r"set2=set\(\[.*?\]\)", "set2=set([1])", subCode, count=1)
    assert "set1=set([1])" in subCode
    assert "set2=set([1])" in subCode
    subRes = runCode(subCode)
    print("Small input expected:", repr("[1]\n"))
    print("Small input actual:", repr(subRes.stdout))
    assert subRes.stdout == "[1]\n"

    # small input disjoint: set([1]) and set([2]) giving []
    disCode = re.sub(r"set1=set\(\[.*?\]\)", "set1=set([1])", code, count=1)
    disCode = re.sub(r"set2=set\(\[.*?\]\)", "set2=set([2])", disCode, count=1)
    assert "set1=set([1])" in disCode
    assert "set2=set([2])" in disCode
    disRes = runCode(disCode)
    print("Small disjoint expected:", repr("[]\n"))
    print("Small disjoint actual:", repr(disRes.stdout))
    assert disRes.stdout == "[]\n"

    # 3. mutant test on original code: replace &= with |=
    mutCode = code.replace("set1 &= set2", "set1 |= set2")
    assert "set1 |= set2" in mutCode
    assert mutCode != code
    mutRes = runCode(mutCode)
    mutVal = ast.literal_eval(mutRes.stdout.strip())
    print("Mutant tried: replaced &= with |=")
    print("Correct output (sorted):", sorted(actVal))
    print("Mutant output (sorted):", sorted(mutVal))
    if sorted(mutVal) == sorted(actVal):
        print("mutant survived!")
        sys.exit(1)
    print("mutant killed successfully")

    # 4. mutant test on small disjoint input (set([1]) and set([2]))
    # correct gives [], mutant gives [1, 2]
    disMutCode = disCode.replace("set1 &= set2", "set1 |= set2")
    assert "set1 |= set2" in disMutCode
    assert disMutCode != disCode
    disMutRes = runCode(disMutCode)
    disMutVal = ast.literal_eval(disMutRes.stdout.strip())
    disActVal = ast.literal_eval(disRes.stdout.strip())
    print("Disjoint small input correct:", sorted(disActVal))
    print("Disjoint small input mutant:", sorted(disMutVal))
    if sorted(disMutVal) == sorted(disActVal):
        print("disjoint mutant survived!")
        sys.exit(1)
    assert sorted(disActVal) == []
    assert sorted(disMutVal) == [1, 2]
    print("disjoint mutant killed successfully")

    # 5. deliberate wrong-result self-test
    bad = "[35, 55]\n"
    if act == bad:
        print("wrong result check failed: accepted mismatch")
        sys.exit(1)
    print("wrong result correctly rejected")

    print("all checks passed")

if __name__ == '__main__':
    main()
