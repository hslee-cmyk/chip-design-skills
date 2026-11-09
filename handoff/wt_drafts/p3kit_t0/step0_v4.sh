#!/usr/bin/env bash
# T0 착수 0단계 (아) V4 재측정(측정 전용, 격리 복제본에서만 -- r2t 2026-10-02, review_t0_fu T0-B1).
#   bash step0_v4.sh <복제본 루트(작업 트리 깨끗, = B checkout)> <B sha> <게이트 캐시 tools/gates> <spec 초안> <출력 디렉터리>
# 모의 T = B 위에 계약 1~4 시제품(install_t0_proto.py) + 계약 11(install_t0_c11.py) -- 복제본에 브랜치 t0mock 커밋 하나(실제 저장소 무관).
# V4 공식 입력 = `--interface-card` 단독(브리프 3.2). interface card는 spec 초안에서 게이트 캐시 interface_card.py로 만든다(B26-1 뒤 rail_declaration 행 포함 가능).
# 계약 10 대상 test_b26_rail_accessor.py가 B에 있으면 그 파일(B 판 -- T0는 래퍼 설치 모듈만 넓힌다)도 같은 card로 따로 lint한다(T0 diff에 들어가 V4가 파일 전체를 본다).
# 판단: FAIL test id 집합 = {test_selftest_sizing_recipe.py::test_s009_revalidate_finger_override}이면 MATCH(card '결정 필요 항목' [T0-V4] 기록 그대로),
#   다르면 DIFF -- 늘어난 id를 같은 근거(피검이 입력을 만들어 양쪽에 남는 기존 줄인가)로 검토하고 질문을 다시 올린다. 결과는 출력 디렉터리 파일에(WP-11).
set -euo pipefail
ISO=$1; B=$2; C=$3; SPEC=$4; OUT=$5
K="$(cd "$(dirname "$0")" && pwd)"
export APPDATA='C:\Users\HSLEE\AppData\Roaming' HOME='C:\Users\HSLEE' PYTHONIOENCODING=utf-8
PY=/c/Python314/python.exe
A=skills/analog-gmid-design/assets
RAILT=$A/tests/contracts/test_b26_rail_accessor.py
mkdir -p "$OUT"
test -z "$(git -C "$ISO" status --porcelain)" || { echo "[중단] 복제본 작업 트리가 깨끗하지 않다" >&2; exit 1; }
git -C "$ISO" checkout -q -B t0mock "$B"
"$PY" -B "$K/install_t0_proto.py" "$ISO" > "$OUT/install.txt"
"$PY" -B "$K/install_t0_c11.py" "$ISO" >> "$OUT/install.txt"
git -C "$ISO" add -A
git -C "$ISO" -c user.name=t0mock -c user.email=t0mock@sandbox commit -q -m "t0mock: contracts 1-4 proto + contract 11"
T=$(git -C "$ISO" rev-parse HEAD)
git -C "$ISO" diff --name-only "$B" "$T" > "$OUT/diff_paths.txt"
PYTHONPATH=$C "$PY" -B "$C/interface_card.py" "$SPEC" --root "$ISO" --out "$OUT/t0.ifc.md" > "$OUT/ifc.log" 2>&1
rc=0; PYTHONPATH=$C "$PY" -B "$C/test_lint.py" --root "$ISO" --base "$B" --head "$T" --interface-card "$OUT/t0.ifc.md" > "$OUT/v4_iface.json" 2>&1 || rc=$?
echo "test_lint(iface, base..T) exit $rc" > "$OUT/v4_summary.txt"
if git -C "$ISO" cat-file -e "$T:$RAILT" 2>/dev/null; then
  rc2=0; PYTHONPATH=$C "$PY" -B "$C/test_lint.py" --root "$ISO" --head "$T" --interface-card "$OUT/t0.ifc.md" "$RAILT" > "$OUT/v4_rail.json" 2>&1 || rc2=$?
  echo "test_lint(iface, $RAILT B 판) exit $rc2" >> "$OUT/v4_summary.txt"
else
  echo "test_lint(rail): $RAILT 없음(B26-1 전) -- 생략" >> "$OUT/v4_summary.txt"
fi
"$PY" -B - "$OUT" "$ISO" "$T" >> "$OUT/v4_summary.txt" <<'EOF'
import ast, collections, json, os, subprocess, sys
out, iso, T = sys.argv[1:4]
TS2 = "caac9101b2fb4c36c8bc0e049a661a1731f36ecf"   # TS2 병합본(판정 기록 20260922-ts2-pytest-split V4 basis = 이관본 전수 대조)


def asserts(rev, path):
    r = subprocess.run(["git", "-C", iso, "show", "%s:%s" % (rev, path)], capture_output=True)
    if r.returncode:
        return None
    return {n.lineno: ast.unparse(n.test) for n in ast.walk(ast.parse(r.stdout.decode("utf-8"))) if isinstance(n, ast.Assert)}
EXP = {"skills/analog-gmid-design/assets/tests/unit/test_selftest_sizing_recipe.py::test_s009_revalidate_finger_override"}
fails, uj, cnt = set(), [], collections.Counter()
for n in ("v4_iface.json", "v4_rail.json"):
    p = os.path.join(out, n)
    if not os.path.exists(p):
        continue
    d = json.loads(open(p, encoding="utf-8").read().strip().splitlines()[-1])
    print(n, "verdict", d.get("verdict"), "files", len(d.get("files", [])), d.get("error", ""))
    for x in d.get("findings", []):
        cnt[(x["rule"], x["output"])] += 1
        if x["output"] == "FAIL":
            fails.add("%s::%s" % (x["file"], x["test"]))
            print("  FAIL", x["rule"], x["file"].split("/")[-1], x["test"], x["line"])
        if x["output"] == "UNJUDGED":
            uj.append((x["file"], x["line"]))
print("counts", dict(cnt), "UNJUDGED", len(uj))
# UNJUDGED 출처: 같은 파일 TS2 병합본의 assert 식(ast.unparse)과 같은가 -- 다르면 그 줄을 바꾼 card의 V4 basis를 찾아 auditor에게 넘긴다
same, other = 0, []
cache = {}
for f, ln in uj:
    if f not in cache:
        cache[f] = (asserts(T, f) or {}, set((asserts(TS2, f) or {}).values()))
    cur, old = cache[f]
    if cur.get(ln) in old:
        same += 1
    else:
        other.append("%s:%d" % (f.split("/")[-1], ln))
print("UNJUDGED assert 식 = TS2 병합본(%s) 식: %d / %d, 다름 %s" % (TS2[:7], same, len(uj), other))
print("FAIL ids", sorted(fails))
print("판단:", "MATCH" if fails == EXP else "DIFF(기대 %s)" % sorted(EXP))
EOF
cat "$OUT/v4_summary.txt"
