#!/usr/bin/env bash
# design v6 §10 E3 명령(그 절 bash 블록과 같은 식)의 실행 확인 -- 읽기 전용.
# 사용: p3v6_e3_check.sh <iso> <rev>   (rev = 판정할 커밋. Phase 3 전 base에서는 결과가 비지 않아야 한다)
# 출력: 줄 머리 import 파일 수(git grep 식), AST import 문장·문자열 import 호출 목록과 파일 수, 제외 집합 밖 결과.
set -uo pipefail
ISO="$1"; REV="$2"; PY="C:/Python314/python.exe -B"
E3_RE='^[[:space:]]*(import|from)[[:space:]]+(sizing_recipe|topology_library|design_report)\b'
EXCL='^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)'
E3_AST=$(cat <<'PYEOF'
import ast, subprocess, sys
iso, rev = sys.argv[1], sys.argv[2]
mods = {"sizing_recipe", "topology_library", "design_report"}
r = subprocess.run(["git", "-C", iso, "grep", "-l", "-E", "sizing_recipe|topology_library|design_report",
                    rev, "--", "*.py"], capture_output=True, text=True)
if r.returncode not in (0, 1):
    sys.exit("git grep failed: " + r.stderr)
for line in r.stdout.splitlines():
    p = line.split(":", 1)[1]
    src = subprocess.run(["git", "-C", iso, "show", rev + ":" + p], capture_output=True, check=True).stdout
    try:
        tree = ast.parse(src)
    except SyntaxError:
        print("PARSE-ERROR " + p)
        continue
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] in mods for a in n.names):
            print("stmt %s:%d" % (p, n.lineno))
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module and n.module.split(".")[0] in mods:
            print("stmt %s:%d" % (p, n.lineno))
        elif isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.Constant) \
                and isinstance(n.args[0].value, str):
            f = n.func
            fn = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if fn in ("import_module", "_import", "__import__") and n.args[0].value.split(".")[0] in mods:
                print("call %s:%d" % (p, n.lineno))
PYEOF
)
echo "== (참고) 줄 머리 import 정규식, 파일 수 at $REV"
git -C "$ISO" grep -l -E "$E3_RE" "$REV" -- '*.py' | sed "s|^$REV:||" | wc -l
OUT=$($PY -c "$E3_AST" "$ISO" "$REV")
echo "== AST stmt: 줄 $(printf '%s\n' "$OUT" | grep -c '^stmt '), 파일 $(printf '%s\n' "$OUT" | grep '^stmt ' | sed 's/^stmt //; s/:[0-9]*$//' | sort -u | wc -l)"
echo "== AST call: 줄 $(printf '%s\n' "$OUT" | grep -c '^call '), 파일 $(printf '%s\n' "$OUT" | grep '^call ' | sed 's/^call //; s/:[0-9]*$//' | sort -u | wc -l)"
printf '%s\n' "$OUT" | grep '^call '
echo "== PARSE-ERROR: $(printf '%s\n' "$OUT" | grep -c '^PARSE-ERROR')"
echo "== 제외 집합 밖 파일 수(판정 대상): $(printf '%s\n' "$OUT" | sed 's/^[a-zA-Z-]* //; s/:[0-9]*$//' | sort -u | grep -v -E "$EXCL" | grep -c .)"
echo "== 제외 집합 안 파일: $(printf '%s\n' "$OUT" | sed 's/^[a-zA-Z-]* //; s/:[0-9]*$//' | sort -u | grep -E "$EXCL" | tr '\n' ' ')"
