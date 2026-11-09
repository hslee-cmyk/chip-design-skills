"""design 30 §10 DoD 블록 정정 D1~D4 + history H2 한 행 -- 고정 문자열 앵커 패치(독립 검토 review_phase3_dod.md §2·§6).

    python -B design30_dod_corrections.py [--check] --design <design 30 경로> [--history <history.md 경로>] [--only D1,D2,D3,D4,H]

* 인자로 받은 두 파일만 읽고 쓴다(그 밖의 경로에는 아무것도 쓰지 않는다. 임시 파일도 만들지 않는다).
* 패치마다 '옛 문자열'(줄 머리부터 줄 끝 개행까지)이 정확히 1번 나와야 적용한다. 이미 적용된 판(새 문자열 1번·옛 0번)은 'applied'.
  그 밖(옛 2번 이상, 옛·새 모두 0번, 옛·새 둘 다 있음)은 하나라도 있으면 아무 파일도 쓰지 않고 exit 2.
* --check: 쓰지 않고 패치마다 pending/applied를 출력. 모두 applied면 exit 0, pending이 있으면 exit 1, 앵커 오류 exit 2.
* 사후 단정(쓰기 전에 메모리에서): design 줄 수 불변, 바뀐 줄이 DoD kit가 뽑는 판정 블록(E3_AST·E3B_AST heredoc, E5 판정 python,
  import_any, EXCL, MP_ARGS -- extract_design_blocks.py와 같은 표지) 밖, history는 정확히 1줄 증가. 어긋나면 exit 2.
* 줄 끝은 LF만(두 파일 모두 CR 0 -- 4a286f0 실측). CR이 있으면 exit 2.

D1(필수, S1): E5 `fresh()` -- 지우기 → detach → HEAD·status 단정, 실패 시 `E5 INVALID: 판 전환 실패 <판>` + return 1.
D2(선택, 채택): `fresh …;` 측정 줄을 `fresh … &&`로, 단독 `fresh` 두 줄은 `|| exit 1`.
D3(선택, 채택): E6 `--head HEAD` → `--head "$H"`.
D4(선택, 채택 -- E 통과 기준 문구·판정 블록 무변경): `GC` = H 판 `git archive` 캐시(`<iso>` 밖), PT3의 `<cache>`를 `$GC`로.
H: history H2 표 끝(`**닫힌 열린 이슈**` 앞)에 정정 행 하나.
"""
import argparse
import re
import sys

D30_PATCHES = [
    ("D1",
     'fresh() { git -C "$ISO" checkout -q --detach "$1" && git -C "$ISO" checkout -q -- . && git -C "$ISO" clean -q -fdx; }\n',
     'fresh() { git -C "$ISO" checkout -q -- . ; git -C "$ISO" clean -q -fdx; git -C "$ISO" checkout -q --detach "$1" && [ "$(git -C "$ISO" rev-parse HEAD)" = "$(git -C "$ISO" rev-parse "$1^{commit}")" ] && [ -z "$(git -C "$ISO" status --porcelain --ignored)" ] || { echo "E5 INVALID: 판 전환 실패 $1"; return 1; }; }   # 산출을 먼저 지우고 옮긴 뒤 HEAD·status를 확인한다(design 20 §10 E4 순서, Phase 2 브리핑 §2 -- 2026-10-02 정정 D1)\n'),
    ("D2",
     '  fresh "$P2D"; $PY -P "$X/e_inst_df36.py" "$ISO" "$c" "$O/p2d_df36_$c.json"; echo "E5 p2d df36 $c exit=$?"   # 동등 확인용(F1 전 판)\n',
     '  fresh "$P2D" && $PY -P "$X/e_inst_df36.py" "$ISO" "$c" "$O/p2d_df36_$c.json"; echo "E5 p2d df36 $c exit=$?"   # 동등 확인용(F1 전 판). 판 전환 실패면 재지 않는다(정정 D2)\n'),
    ("D2",
     '  fresh "$P2D"; $PY -P "$X/e_inst_p3.py"   "$ISO" "$c" "$O/p2d_p3_$c.json";   echo "E5 p2d p3 $c exit=$?"\n',
     '  fresh "$P2D" && $PY -P "$X/e_inst_p3.py"   "$ISO" "$c" "$O/p2d_p3_$c.json";   echo "E5 p2d p3 $c exit=$?"\n'),
    ("D2",
     '  fresh "$H";   $PY -P "$X/e_inst_p3.py"   "$ISO" "$c" "$O/h_p3_$c.json";     echo "E5 head p3 $c exit=$?"\n',
     '  fresh "$H"   && $PY -P "$X/e_inst_p3.py"   "$ISO" "$c" "$O/h_p3_$c.json";     echo "E5 head p3 $c exit=$?"\n'),
    ("D2",
     '\nfresh "$P2D"\n$PY -P "$X/e_lib.py"    "$ISO" "$O/p2d_elib.json";',
     '\nfresh "$P2D" || exit 1   # 판 전환 실패면 E-LIB를 다른 판에서 재지 않는다(`E5 INVALID` 줄은 fresh가 냈다 -- 정정 D2)\n$PY -P "$X/e_lib.py"    "$ISO" "$O/p2d_elib.json";'),
    ("D2",
     '\nfresh "$H"\n$PY -P "$X/e_lib_p3.py" "$ISO" "$O/h_elibp3.json" rails;',
     '\nfresh "$H" || exit 1     # 정정 D2\n$PY -P "$X/e_lib_p3.py" "$ISO" "$O/h_elibp3.json" rails;'),
    ("D3",
     '$PY "$S/move_plan.py" check --root "$ISO" --base "$B0" --head HEAD --card ALL "${MP_ARGS[@]}" \\\n',
     '$PY "$S/move_plan.py" check --root "$ISO" --base "$B0" --head "$H" --card ALL "${MP_ARGS[@]}" \\\n'),
    ("D4",
     'GC="$ISO/tools/gates"     # 05 §4.4: 판정은 gate master 판 게이트 코드.',
     'GC="<05 §4.4 캐시: git archive <H> tools/gates를 <iso> 밖(또는 <git-common-dir>/gmid-gate-cache/<H>/)에 푼 것>/tools/gates"   # 정정 D4. 05 §4.4: 판정은 gate master 판 게이트 코드.'),
    ("D4",
     '                          # (05 §4.4 캐시 <git-common-dir>/gmid-gate-cache/<그 커밋>/를 쓰면 GC를 그 안의 tools/gates로)\n',
     '                          # (정정 D4: <iso> 밖이라 E5가 <iso>를 P2D로 옮겨도 GC는 H 판 그대로 -- 게이트 출처 하나, PT3도 같은 $GC)\n'),
    ("D4",
     'PT3() {   # 10 §10 PT에서 --gmid-phase=1만 =3으로(v8 -- 5차 검토 B1). <cache> = 05 §4.4 캐시.\n',
     'PT3() {   # 10 §10 PT에서 --gmid-phase=1만 =3으로(v8 -- 5차 검토 B1). 게이트 코드 = $GC(05 §4.4 캐시 -- 정정 D4).\n'),
    ("D4",
     '  PYTHONPATH="<cache>" PYTHONPYCACHEPREFIX="$(mktemp -d)" C:/Python314/python.exe -P -m pytest -c "<cache>/pytest_gate.ini" --rootdir',
     '  PYTHONPATH="$GC" PYTHONPYCACHEPREFIX="$(mktemp -d)" C:/Python314/python.exe -P -m pytest -c "$GC/pytest_gate.ini" --rootdir'),
]

HIST_ANCHOR = "\n\n**닫힌 열린 이슈**(계획서 N5.3에서 뺀 항목)\n"
HIST_ROW = (
    "| design 30 §10 E5 `fresh()` 판 전환(v8.5 승인본 1034행) | `checkout --detach \"$1\" && checkout -- . && clean -fdx` 순서였다. "
    "직전 E-INST가 추적 산출물(`workspaces/*/…instance.json`)을 고친 상태에서 두 판의 그 파일이 다르면 `checkout --detach`가 거부되고(rc 1) "
    "HEAD가 이전 판에 남는데, 호출부가 `fresh \"$X\"; $PY …`로 이어 **이전 판에서 측정이 돌아 E-INST '같음'이 나올 수 있었다**(실패해야 할 곳에서 통과). "
    "HEAD 확인도 없었다. design 20 §10 E4와 Phase 2 DoD 브리핑 §2의 '지우기 → detach → HEAD 대조 → status 0줄' 순서를 거꾸로 옮긴 것이다. "
    "독립 검토 `_drafts/review_phase3_dod.md` §2.1이 합성 저장소로 재현했다. `5f643a9..4a286f0`에서는 그 파일이 두 판에서 같아 리허설에는 드러나지 않았다 | "
    "2026-10-02 정정 D1(지우기 → detach → HEAD = 대상·status `--ignored` 0줄 단정, 실패 시 `E5 INVALID: 판 전환 실패 <판>` + return 1 -- "
    "E5 통과 기준 '`E5 INVALID` 줄 없음'이 그대로 FAIL로 만든다), D2(측정 줄 `fresh … &&`, 단독 줄 `|| exit 1`), D3(E6 `--head \"$H\"`), "
    "D4(`GC` = H 판 `git archive` 캐시를 `<iso>` 밖에, PT3 `<cache>`를 `$GC`로 통일). §10 표의 통과 기준 문구와 DoD kit가 뽑는 판정 블록 5개(sha256)는 그대로다 -- "
    "실행을 실패 시 멈추게 하는 절차 강화라 승인 기록을 새로 받지 않았다(게이트: 계획 N3.12.2 `오케스트레이터 | docs/02-design/**` 조건 '없음', "
    "UD-0 승인 `20260930-30-module-split-design`은 `diff_base`..`diff_head` 고정 해시라 이후 편집과 무관) | design 30 §10 E5·E6 블록 |\n"
)

# extract_design_blocks.py와 같은 표지(§10~§11 머리 사이)
SEC10, SEC11 = "## 10. ", "## 11. "


def block_lines(lines):
    """DoD kit가 바이트 그대로 뽑는 줄 번호 집합(0부터). 표지를 못 찾으면 None."""
    sec = [i for i, ln in enumerate(lines) if ln.startswith(SEC10)]
    nxt = [i for i, ln in enumerate(lines) if ln.startswith(SEC11)]
    if len(sec) != 1 or len(nxt) != 1:
        return None
    lo, hi = sec[0], nxt[0]
    out = set()

    def one(pred):
        idx = [i for i in range(lo + 1, hi) if pred(lines[i])]
        return idx[0] if len(idx) == 1 else None

    for start in ("E3_AST=$(cat <<'PYEOF'", "E3B_AST=$(cat <<'PYEOF'", '$PY - "$O" "$ISO" "$P2D" <<\'PYEOF\''):
        s = one(lambda ln, st=start: ln == st)
        if s is None:
            return None
        e = next((j for j in range(s + 1, len(lines)) if lines[j] == "PYEOF"), None)
        if e is None:
            return None
        out.update(range(s, e + 1))
    s = one(lambda ln: ln.startswith("import_any() {"))
    e = next((j for j in range(s + 1, len(lines)) if lines[j] == "}"), None) if s is not None else None
    if e is None:
        return None
    out.update(range(s, e + 1))
    ex = one(lambda ln: ln.startswith("EXCL='"))
    ms = one(lambda ln: ln.startswith("MP_ARGS=("))
    if ex is None or ms is None:
        return None
    me = next((j for j in range(ms, len(lines)) if re.search(r"'\)\s*(#.*)?$", lines[j])), None)
    if me is None:
        return None
    out.add(ex)
    out.update(range(ms, me + 1))
    return out


def plan(text, patches):
    """[(label, state, old, new)], state ∈ pending/applied/ERROR:<이유>."""
    res = []
    for lab, old, new in patches:
        if not old.startswith("\n"):   # 줄 머리 고정: 앞 개행까지 앵커에 넣는다
            old, new = "\n" + old, "\n" + new
        no, nn = text.count(old), text.count(new)
        if no == 1 and nn == 0:
            st = "pending"
        elif no == 0 and nn == 1:
            st = "applied"
        else:
            st = "ERROR: 옛 앵커 %d번·새 문자열 %d번" % (no, nn)
        res.append((lab, st, old, new))
    return res


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True)
    ap.add_argument("--history")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--only", default="D1,D2,D3,D4,H")
    ns = ap.parse_args(argv)
    want = {x.strip() for x in ns.only.split(",") if x.strip()}
    if not want <= {"D1", "D2", "D3", "D4", "H"} or "D1" not in want and want & {"D2", "D3", "D4"}:
        print("ERROR --only 값: %s(D1은 필수 -- D2~D4는 D1과 함께만)" % ns.only); return 2
    if "H" in want and not ns.history:
        print("ERROR H에는 --history 경로가 필요하다"); return 2
    raw = open(ns.design, "rb").read()
    if b"\r" in raw:
        print("ERROR design에 CR이 있다(LF 전제)"); return 2
    text = raw.decode("utf-8")
    rows = plan(text, [p for p in D30_PATCHES if p[0] in want])
    hrows, htext = [], None
    if "H" in want:
        hraw = open(ns.history, "rb").read()
        if b"\r" in hraw:
            print("ERROR history에 CR이 있다(LF 전제)"); return 2
        htext = hraw.decode("utf-8")
        na, nr = htext.count(HIST_ANCHOR), htext.count(HIST_ROW)
        if na == 1 and nr == 0:
            prev = htext[:htext.index(HIST_ANCHOR)].rsplit("\n", 1)[-1]
            hrows.append(("H", "pending" if prev.startswith("| ") else "ERROR: 앵커 앞 줄이 H2 표 행이 아니다", HIST_ANCHOR,
                          "\n" + HIST_ROW + HIST_ANCHOR[1:]))
        elif nr == 1:
            hrows.append(("H", "applied", None, None))
        else:
            hrows.append(("H", "ERROR: 앵커 %d번·행 %d번" % (na, nr), None, None))
    for lab, st, old, _ in rows + hrows:
        print("%s %s%s" % (lab, st, "" if old is None else " | " + old.strip("\n")[:90]))
    if any(st.startswith("ERROR") for _, st, _, _ in rows + hrows):
        print("결과: 앵커 오류 -- 아무 파일도 쓰지 않음"); return 2
    pend = [r for r in rows + hrows if r[1] == "pending"]
    if ns.check:
        print("결과: --check pending %d / applied %d" % (len(pend), len(rows + hrows) - len(pend)))
        return 1 if pend else 0
    new = text
    for lab, st, old, nw in rows:
        if st == "pending":
            new = new.replace(old, nw, 1)
    a, b = text.split("\n"), new.split("\n")
    if len(a) != len(b):
        print("ERROR design 줄 수가 바뀐다(%d → %d)" % (len(a), len(b))); return 2
    blk_a, blk_b = block_lines(a), block_lines(b)
    if blk_a is None or blk_a != blk_b:
        print("ERROR 판정 블록 표지를 찾지 못했거나 위치가 바뀐다"); return 2
    changed = [i for i in range(len(a)) if a[i] != b[i]]
    if any(i in blk_a for i in changed):
        print("ERROR 판정 블록 안의 줄이 바뀐다: %s" % [i + 1 for i in changed if i in blk_a]); return 2
    hnew = htext
    if hrows and hrows[0][1] == "pending":
        hnew = htext.replace(HIST_ANCHOR, hrows[0][3], 1)
        if hnew.count("\n") != htext.count("\n") + 1:
            print("ERROR history 줄 증가가 1이 아니다"); return 2
    if new != text:
        with open(ns.design, "wb") as fh:
            fh.write(new.encode("utf-8"))
    if htext is not None and hnew != htext:
        with open(ns.history, "wb") as fh:
            fh.write(hnew.encode("utf-8"))
    print("결과: design 바뀐 줄 %s(판정 블록 밖), history %s" % (
        [i + 1 for i in changed], "+1행" if (htext is not None and hnew != htext) else "변경 없음"))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
