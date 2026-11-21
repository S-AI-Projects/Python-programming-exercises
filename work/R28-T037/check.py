import sys, subprocess, os, re, ast

here = os.path.dirname(os.path.abspath(__file__))
mdPath = os.path.join(here, '..', '..', '100+ Python challenging programming exercises for Python 3.md')

def getMdParts(mdPath):
    f = open(mdPath, 'r', encoding='utf-8')
    txt = f.read()
    f.close()
    qPat = r"### Question 88\n(.*?)(?=### Question 89)"
    m = re.search(qPat, txt, re.S)
    if not m:
        print('question 88 not found')
        sys.exit(1)
    sec = m.group(1)

    codePat = r"Solution:\s*```(?:python)?\n(.*?)```"
    codeM = re.search(codePat, sec, re.S)
    if not codeM:
        print('code block not found')
        sys.exit(1)
    code = codeM.group(1).strip()

    # extract table rows
    rowPat = r"\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(kept|dropped)\s*\|\s*([^|]+?)\s*\|"
    tableRows = re.findall(rowPat, sec)

    return code, tableRows

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

def main():
    code, tableRows = getMdParts(mdPath)

    # published fixture: li = [12,24,35,70,88,120,155]
    res = runCode(code)
    expStr = "[12, 24, 88]\n"
    actStr = res.stdout
    print("Expected:", repr(expStr))
    print("Actual:", repr(actStr))
    assert actStr == expStr
    actVal = ast.literal_eval(actStr.strip())
    assert actVal == [12, 24, 88]

    # smallest input: li = [1]
    subCode = re.sub(r"li\s*=\s*\[.*?\]", "li = [1]", code, count=1)
    assert "li = [1]" in subCode
    smallRes = runCode(subCode)
    smallExp = "[1]\n"
    smallAct = smallRes.stdout
    print("Smallest expected:", repr(smallExp))
    print("Smallest actual:", repr(smallAct))
    assert smallAct == smallExp
    assert ast.literal_eval(smallAct.strip()) == [1]

    # backup derivation table: compute values for fixture elements
    fixture = [12, 24, 35, 70, 88, 120, 155]
    computedRows = []
    keptList = []
    for x in fixture:
        m5 = x % 5
        m7 = x % 7
        if m5 != 0 and m7 != 0:
            status = "kept"
            keptList.append(x)
        else:
            status = "dropped"
        computedRows.append((x, m5, m7, status))

    print("Computed kept elements:", keptList)
    assert keptList == actVal

    # assert doc table rows match computed derivation
    assert len(tableRows) == len(computedRows)
    for i in range(len(computedRows)):
        cx, cm5, cm7, cstatus = computedRows[i]
        dx, dm5, dm7, dstatus, _ = tableRows[i]
        assert int(dx) == cx
        assert int(dm5) == cm5
        assert int(dm7) == cm7
        assert dstatus == cstatus
    print("Derivation table in doc matches computed values")

    # deliberate wrong-result self-test: wrong list keeping 35
    badAct = [12, 24, 35, 88]
    if actVal == badAct:
        print("wrong result check failed: accepted 35 in output")
        sys.exit(1)
    print("wrong result correctly rejected")

    print("all checks passed")

if __name__ == '__main__':
    main()
