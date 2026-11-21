import sys, subprocess, os, re, ast

here = os.path.dirname(os.path.abspath(__file__))
mdPath = os.path.join(here, '..', '..', '100+ Python challenging programming exercises for Python 3.md')

def getBlocks(mdPath):
    f = open(mdPath, 'r', encoding='utf-8')
    txt = f.read()
    f.close()
    qPat = r"### Question 41\n(.*?)(?=### Question 42)"
    m = re.search(qPat, txt, re.S)
    if not m:
        print('question 41 section not found')
        sys.exit(1)
    sec = m.group(1)
    blocks = re.findall(r"```python\n(.*?)```", sec, re.S)
    if len(blocks) < 2:
        print('expected at least 2 code blocks in question 41')
        sys.exit(1)
    return blocks[0].strip(), blocks[1].strip()

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
    srcCode, altCode = getBlocks(mdPath)

    # build expected tuple with plain loop
    expList = []
    for k in range(1, 21):
        expList.append(k * k)
    expTuple = tuple(expList)
    expStr = str(expTuple)

    # run source solution
    srcRes = run(srcCode)
    srcAct = srcRes.stdout.strip()
    srcVal = ast.literal_eval(srcAct)
    print("Source expected:", expStr)
    print("Source actual:", srcAct)
    assert isinstance(srcVal, tuple)
    assert len(srcVal) == 20
    assert srcVal == expTuple
    assert srcVal[0] == 1 and srcVal[-1] == 400
    for k in range(1, 21):
        assert srcVal[k - 1] == k * k
    assert srcAct == expStr

    # run alternative solution
    altRes = run(altCode)
    altAct = altRes.stdout.strip()
    altVal = ast.literal_eval(altAct)
    print("Alternative expected:", expStr)
    print("Alternative actual:", altAct)
    assert isinstance(altVal, tuple)
    assert len(altVal) == 20
    assert altVal == expTuple
    assert altVal[0] == 1 and altVal[-1] == 400
    for k in range(1, 21):
        assert altVal[k - 1] == k * k
    assert altAct == expStr

    # assert both methods produce identical outputs
    assert srcVal == altVal
    assert srcAct == altAct

    # backing up intermediate claim: range(1, 4) prints (1, 4, 9)
    subCode = re.sub(r"range\(1,\s*21\)", "range(1, 4)", srcCode)
    assert "range(1, 4)" in subCode
    subRes = run(subCode)
    subAct = subRes.stdout.strip()
    subVal = ast.literal_eval(subAct)
    print("Intermediate expected: (1, 4, 9)")
    print("Intermediate actual:", subAct)
    assert subVal == (1, 4, 9)

    # deliberate wrong-result self-test
    plainTuple = tuple(range(1, 21))
    if srcVal == plainTuple:
        print("wrong result check failed: accepted plain numbers")
        sys.exit(1)
    listVal = list(expTuple)
    if srcVal == listVal:
        print("wrong result check failed: accepted list instead of tuple")
        sys.exit(1)
    print("wrong result correctly rejected")

    print("all checks passed")

if __name__ == '__main__':
    main()
