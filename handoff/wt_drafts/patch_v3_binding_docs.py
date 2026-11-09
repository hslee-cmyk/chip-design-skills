"""문서 커밋 패치 -- spec card 20260930-v3-exempt-binding 계약 10('문서').

바꾸는 곳(각각 정확히 한 군데):
  1. design 05 §10 V3 행 ⑤의 면제 문구
  2. design 10 §6.7 IC3(C8) 항목(382행) 끝 문장
  3. 계획 N4.2 V3 행의 면제 문구(plan_tables_hash 입력 아님 -- 실행 때 다시 잰다)

사용:  C:/Python314/python.exe -B patch_v3_binding_docs.py --root <저장소 또는 worktree 루트> [--check]
  --check  : 바꾸지 않고 상태만 판정(pending / applied / 거부)
종료 코드: 0 = 적용함 또는 이미 적용됨, 2 = 거부(부분 상태·앵커 불일치·줄 끝 혼합 등), 아무 파일도 쓰지 않는다.

성질: 바이트 단위(UTF-8)로 바꾸고 줄 끝(CRLF/LF)을 그대로 둔다(바꾸는 문자열에 개행이 없다), 줄 수 불변 단언,
멱등(전부 적용된 상태면 아무것도 쓰지 않고 0), 부분 상태(일부만 적용) 거부, 모든 파일 내용을 먼저 만든 뒤에만 쓴다.
"""
import argparse
import hashlib
import json
import os
import sys

sys.dont_write_bytecode = True

CARD = "20260930-v3-exempt-binding"
D05 = "docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md"
D10 = "docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md"
PLAN = "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"

# (경로, 이름, old, new) -- old/new는 card 계약 10 인용문 그대로(줄바꿈 자리 = 공백 하나), 앞뒤 앵커는 유일성 확보용으로 원문 그대로 붙였다.
EDITS = [
    (D05, "design05-V3-5-exempt",
     "등가 변이 면제는 `target_kind: decision`, `target` = 변이 id 목록인 승인 기록. 자체 AST 변이기(DEC-39) |",
     "등가 변이 면제는 `target_kind: decision`, `target` 원소 = `<변이 id>@<묶기 해시>`(승인할 때 head def 노드 원본 -- docstring 포함 -- 의 "
     "`ast.dump` sha256, 정의: spec card `20260930-v3-exempt-binding`)인 승인 기록 -- head의 그 def 묶기 해시가 같을 때만 적용. "
     "해시가 없거나 다르거나 형식이 틀린 원소는 적용하지 않고 출력 `exempt_ignored`에 싣는다. 자체 AST 변이기(DEC-39) |"),
    (D10, "design10-382-C8",
     "그래도 남는 등가 변이는 `target_kind: decision` 승인 기록(변이 id 목록)으로만 면제한다(N4.2 V3).",
     "그래도 남는 등가 변이는 `target_kind: decision` 승인 기록으로만 면제한다(N4.2 V3. 원소 형식은 design 05 §10 V3 ⑤ -- "
     "2026-10-01부터 `<변이 id>@<묶기 해시>`)."),
    (PLAN, "planN42-V3-exempt",
     "살아남은 변이가 있으면 FAIL. 등가 변이 면제는 승인 기록으로만. 변이는 worktree 밖 임시 복사본에서",
     "살아남은 변이가 있으면 FAIL. 등가 변이 면제는 승인 기록으로만(변이 id와 그 def의 AST 묶기 해시에 묶임). 변이는 worktree 밖 임시 복사본에서"),
]
PRECONDITIONS = []  # 이 card가 먼저다(범위 card가 이 card 결과 위에 적용된다)


def eol_style(b):
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n")
    if crlf == lf:
        return "crlf" if lf else "none"
    if crlf == 0:
        return "lf"
    return "mixed"


def norm_sha(b):
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def plan_tables_hash(root, data):
    """root에 tools/gates가 있으면 merge_gate.plan_tables_hash(읽기 전용 import), 없으면 None."""
    gates = os.path.join(root, "tools", "gates")
    if not os.path.isfile(os.path.join(gates, "merge_gate.py")):
        return None
    if gates not in sys.path:
        sys.path.insert(0, gates)
    import merge_gate  # noqa: E402
    return merge_gate.plan_tables_hash(data.decode("utf-8"))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--check", action="store_true")
    ns = ap.parse_args(argv)
    root = os.path.abspath(ns.root)
    errs, report = [], {"card": CARD, "root": root, "edits": [], "files": {}}

    files = {}
    for p in sorted({e[0] for e in EDITS} | {c[0] for c in PRECONDITIONS}):
        fp = os.path.join(root, *p.split("/"))
        if not os.path.isfile(fp):
            errs.append("파일 없음: %s" % p)
            continue
        with open(fp, "rb") as fh:
            files[p] = fh.read()
    if errs:
        return finish(report, errs)

    for p, name, needle in PRECONDITIONS:
        if files[p].count(needle.encode("utf-8")) != 1:
            errs.append("선행 card 문구가 정확히 한 번 있지 않다(선행 card 문서 커밋 먼저): %s %s" % (p, name))

    states = []
    for p, name, old, new in EDITS:
        b = files[p]
        o, n = b.count(old.encode("utf-8")), b.count(new.encode("utf-8"))
        if o == 1 and n == 0:
            st = "pending"
        elif o == 0 and n == 1:
            st = "applied"
        else:
            st = "error"
            errs.append("앵커 상태 이상: %s %s (old %d회, new %d회)" % (p, name, o, n))
        states.append(st)
        report["edits"].append({"path": p, "name": name, "state": st})
    if errs:
        return finish(report, errs)
    if "pending" in states and "applied" in states:
        return finish(report, ["부분 적용 상태 -- 거부(수동 확인 필요): %s" % states])

    out = dict(files)
    for (p, name, old, new), st in zip(EDITS, states):
        if st == "pending":
            out[p] = out[p].replace(old.encode("utf-8"), new.encode("utf-8"), 1)

    for p in sorted({e[0] for e in EDITS}):
        before, after = files[p], out[p]
        eb, ea = eol_style(before), eol_style(after)
        if eb == "mixed" or eb != ea:
            errs.append("줄 끝 이상: %s %s -> %s" % (p, eb, ea))
        if before.startswith(b"\xef\xbb\xbf") != after.startswith(b"\xef\xbb\xbf"):
            errs.append("BOM 변화: %s" % p)
        lb, la = before.split(b"\n"), after.split(b"\n")
        if len(lb) != len(la):
            errs.append("줄 수 변화: %s %d -> %d" % (p, len(lb), len(la)))
        changed = [i + 1 for i, (x, y) in enumerate(zip(lb, la)) if x != y]
        try:
            after.decode("utf-8")
        except UnicodeDecodeError:
            errs.append("UTF-8 아님: %s" % p)
        report["files"][p] = {"eol": eb, "changed_lines": changed,
                              "sha256_lf_before": norm_sha(before), "sha256_lf_after": norm_sha(after)}
    if PLAN in out:
        try:
            hb, ha = plan_tables_hash(root, files[PLAN]), plan_tables_hash(root, out[PLAN])
        except Exception as e:  # 판정 표 파싱 실패는 거부(표 파손 의심)
            hb, ha = "ERROR", "ERROR"
            errs.append("plan_tables_hash 계산 실패: %r" % (e,))
        report["plan_tables_hash"] = {"before": hb, "after": ha,
                                      "unchanged": (hb == ha) if hb is not None else "skipped(tools/gates 없음)"}
        if hb is not None and hb != ha:
            errs.append("계획서 판정 표 해시가 바뀐다 -- plan_tables 승인 필요, 거부")
    if errs:
        return finish(report, errs)

    if all(s == "applied" for s in states):
        report["result"] = "already-applied(쓰지 않음)"
        return finish(report, [])
    if ns.check:
        report["result"] = "pending(--check, 쓰지 않음)"
        return finish(report, [])
    for p in sorted({e[0] for e in EDITS}):
        if out[p] == files[p]:
            continue
        fp = os.path.join(root, *p.split("/"))
        tmp = fp + ".v3patch.tmp"
        with open(tmp, "wb") as fh:
            fh.write(out[p])
        os.replace(tmp, fp)
    report["result"] = "applied"
    return finish(report, [])


def finish(report, errs):
    if errs:
        report["result"] = "REFUSED"
        report["errors"] = errs
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 2 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
