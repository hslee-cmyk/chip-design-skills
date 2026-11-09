#!/usr/bin/env bash
# 순서 7 계약 5 (a)(b) + E0(계약 2): 병합본 도구 실행. $1 = 병합본 격리 복제본(M), $2 = base 격리 복제본, $3 = 출력 디렉터리.
# 도구는 스크립트 형태로(-P 없이 -- 도구가 자기 디렉터리를 sys.path[0]로 쓴다), 바이트코드 쓰기 없음.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
export PYTHONDONTWRITEBYTECODE=1
PY=C:/Python314/python.exe
M=$1; B=$2; O=$3
REG=docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
INV=docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json
T=$M/skills/analog-gmid-design/assets/tests/tools/reg_check.py
# E0: 인자 추가 없음 -- exit 0, 발견 0
$PY $T --registry $M/$REG --root $M > $O/e0_M.txt 2>&1; echo "e0_M exit $?" >> $O/regcheck_status.txt
# 계약 5 (a): 병합본 레지스트리 + 목록 -- exit 0, 발견 0
$PY $T --registry $M/$REG --root $M --df23-inventory $M/$INV > $O/c5a_M.txt 2>&1; echo "c5a_M exit $?" >> $O/regcheck_status.txt
# 계약 5 (b): base 레지스트리(§8 없음) + 병합본 도구 -- df23-section 발견, exit 1
$PY $T --registry $B/$REG --root $M --df23-inventory $M/$INV > $O/c5b_baseReg.txt 2>&1; echo "c5b_baseReg exit $?" >> $O/regcheck_status.txt
# 비교: base 도구로 base·병합본 레지스트리 E0(인자 없음) -- 출력이 같아야 한다
$PY $B/skills/analog-gmid-design/assets/tests/tools/reg_check.py --registry $M/$REG --root $M > $O/e0_baseTool_M.txt 2>&1; echo "e0_baseTool_M exit $?" >> $O/regcheck_status.txt
$PY $B/skills/analog-gmid-design/assets/tests/tools/reg_check.py --registry $B/$REG --root $B > $O/e0_baseTool_B.txt 2>&1; echo "e0_baseTool_B exit $?" >> $O/regcheck_status.txt
echo DONE >> $O/regcheck_status.txt
