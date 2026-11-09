"""문서 커밋 패치 -- spec card 20260930-p3-gate-move-aware 계약 13('문서'). **34·35·B33 문서 패치 뒤에만** 적용한다.

바꾸는 곳(각각 정확히 한 군데, 줄 안 삽입만 -- 줄 수 불변):
  1. design 05 §10 V3 행: ' ② 연산자:' 바로 앞에 문장 삽입(① 끝 -- 범위 정책 card가 고친 ① 문구 뒤, 그 문구는 지우지 않는다)
  2. design 05 §10 V6 행: 행 끝 ' |' 앞
  3. design 05 §10 V7 행: 행 끝 ' |' 앞(B33이 고친 문구 뒤)
  4. design 05 §10 거부 증명 줄: 끝 '.' 앞에 공격 32(B33 선례 -- 공격 33을 같은 줄에 적었다)
  5. 계획 N3.10 '이동 규칙' 줄(0f23786 533행): '해시가 같은 함수는 V3 대상에서 뺀다.' 뒤
선행 조건(없으면 거부): 35의 V3 ① 문구, B33의 V7 행 문구·거부 증명 줄 문구. --no-preconditions는 측정(0f23786 위 시험)용.

사용:  C:/Python314/python.exe -B patch_g1_docs.py --root <저장소 루트> [--check] [--no-preconditions]
종료: 0 = 적용함(applied N) 또는 이미 적용됨(already applied), 2 = 거부(앵커 0개·2개 이상, 부분 적용 상태, 선행 문구 없음) -- 거부면 아무것도 쓰지 않는다.
바이트 단위(UTF-8), 줄 끝(CRLF/LF) 보존, 멱등.
"""
import argparse
import json
import os
import sys

sys.dont_write_bytecode = True
CARD = "20260930-p3-gate-move-aware"
D05 = "docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md"
PLAN = "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
REF = "정의: spec card `%s`" % CARD
S_V3 = ". 옮긴 단위(design 30 §3 MOVED)는 이동 원본과 비교, 옮긴 def는 V3 대상 def가 아니다(%s)" % REF
S_V6 = ". 옮긴 단위(design 30 §3 MOVED)는 이동 원본(원본 파일 맥락)과 비교(%s)" % REF
S_V7 = ". 옮긴 단위(design 30 §3 MOVED)는 이동 원본과 비교 -- 옮긴 def는 새 def가 아니다(%s)" % REF
S_RJ = ", V3·V6·V7 이동 인식 → 공격 32(`attacks/32-moved-defs`)"
S_PL = " V6·V7의 '새'도 같은 규칙(옮긴 단위는 이동 원본과 비교, 옮긴 단위의 정의는 design 30 §3)."

# (경로, 이름, 줄 머리, 줄 안 앵커, 삽입 위치('before'|'after'), 삽입문)
EDITS = [
    (D05, "design05-V3", "| `mutate_changed.py`(V3) | 뮤테이션 |", " ② 연산자:", "before", S_V3),
    (D05, "design05-V6", "| `source_lint.py`(V6) | 소스 |", " |", "before-last", S_V6),
    (D05, "design05-V7", "| `reachability.py`(V7) | 배선 |", " |", "before-last", S_V7),
    (D05, "design05-reject", "거부 증명: V3 → `redteam/v3_survivor`", ".", "before-last", S_RJ),
    (PLAN, "planN310-533", "* **이동 규칙**: 모듈 하나당 이동 전용 커밋.", "해시가 같은 함수는 V3 대상에서 뺀다.", "after", S_PL),
]
PRECONDITIONS = [
    (D05, "35-design05-V3", "`20260930-v3-changed-stmt-scope` 계약 1). 대상 밖 변이는 실행하지 않고 수와 id를 출력한다(판정 제외)"),
    (D05, "B33-design05-V7", "V3 인벤토리는 같은 그래프를 test 노드에서 출발해 쓴다(범위 제한 없음)"),
    (D05, "B33-design05-reject", "V7 → `redteam/v7_unwired`·공격 33(`attacks/33-v7-registry-edges`)"),
]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--no-preconditions", action="store_true")
    ns = ap.parse_args(argv)
    root = os.path.abspath(ns.root)
    data = {}
    for p in {e[0] for e in EDITS}:
        with open(os.path.join(root, *p.split("/")), "rb") as fh:
            data[p] = fh.read()
    errs = []
    if not ns.no_preconditions:
        for p, name, s in PRECONDITIONS:
            if data[p].count(s.encode("utf-8")) != 1:
                errs.append("선행 문구 %s: %d개" % (name, data[p].count(s.encode("utf-8"))))
    new = dict(data)
    state = []
    for p, name, head, anchor, where, ins in EDITS:
        lines = new[p].split(b"\n")
        idx = [i for i, ln in enumerate(lines) if ln.lstrip().startswith(head.encode("utf-8"))]
        if len(idx) != 1:
            errs.append("%s: 줄 머리 %d개" % (name, len(idx)))
            continue
        i = idx[0]
        ln = lines[i]
        cr = ln.endswith(b"\r")
        body = ln[:-1] if cr else ln
        b_ins, b_anc = ins.encode("utf-8"), anchor.encode("utf-8")
        if b_ins in body:
            state.append((name, "already", i + 1))
            continue
        if where == "before":
            if body.count(b_anc) != 1:
                errs.append("%s: 앵커 %d개" % (name, body.count(b_anc)))
                continue
            body = body.replace(b_anc, b_ins + b_anc)
        elif where == "after":
            if body.count(b_anc) != 1:
                errs.append("%s: 앵커 %d개" % (name, body.count(b_anc)))
                continue
            body = body.replace(b_anc, b_anc + b_ins)
        else:
            if not body.endswith(b_anc):
                errs.append("%s: 줄 끝이 %r 아님" % (name, anchor))
                continue
            body = body[:-len(b_anc)] + b_ins + b_anc
        lines[i] = body + (b"\r" if cr else b"")
        new[p] = b"\n".join(lines)
        state.append((name, "applied", i + 1))
    kinds = {s[1] for s in state}
    if not errs and kinds == {"already", "applied"}:
        errs.append("부분 적용 상태: %s" % state)
    if errs:
        print(json.dumps({"result": "REFUSED", "errors": errs}, ensure_ascii=False))
        return 2
    for p in data:
        if new[p].count(b"\n") != data[p].count(b"\n"):
            print(json.dumps({"result": "REFUSED", "errors": ["줄 수가 바뀜: " + p]}, ensure_ascii=False))
            return 2
    if kinds == {"already"}:
        print("already applied %s" % json.dumps(state, ensure_ascii=False))
        return 0
    if ns.check:
        print("check ok (would apply %d) %s" % (len(state), json.dumps(state, ensure_ascii=False)))
        return 0
    for p in data:
        if new[p] != data[p]:
            with open(os.path.join(root, *p.split("/")), "wb") as fh:
                fh.write(new[p])
    print("applied %d replacement(s) %s" % (len(state), json.dumps(state, ensure_ascii=False)))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
