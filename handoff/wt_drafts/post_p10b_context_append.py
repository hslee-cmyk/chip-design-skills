# -*- coding: utf-8 -*-
"""post_p10b_runbook.sh 전용 -- `.ai/context.md`에 줄을 **바이너리 append**로만 더한다(메모리 규칙: heredoc append 금지).

    python -B post_p10b_context_append.py --root <저장소> --mode c1  --plan-hash <64hex> [--p10b-note <파일>]
    python -B post_p10b_context_append.py --root <저장소> --mode b47 --d-commit <sha> --measured-at <sha>

* c1  : P10 완료 + P10b 완료 + 이 문서 커밋(설계서 20·양식·history) 줄. P10b 판정 기록 커밋은 sha가 아니라 gate master 이력에서
        제목 접두 `audit: 20260930-df23-registry-record`로 찾는다(정확히 1개). 수치는 지어내지 않고 판정 기록 커밋 제목을 그대로 인용한다.
        `--p10b-note`(선택, UTF-8 한 줄)는 재시도 경위 등 오케스트레이터가 확인한 사실을 덧붙일 때만.
* b47 : 사용자 결정 B47 줄(승인 기록 20261001-b47-md-sync와 같은 커밋). 방침 1·2 원문과 답을 함께 옮긴다(spec card 결정 문단).
안전장치: 파일 끝이 줄 끝이어야 하고, 쓴 뒤 다시 읽어 '원래 바이트 + 더한 바이트'인지 대조한다. 같은 표지 줄이 이미 있으면 중단(중복 append 방지).
"""
import argparse
import os
import subprocess
import sys

REL = ".ai/context.md"
P10_AUDIT = "62ae24f"
P10B_ID = "20260930-df23-registry-record"
MARK_C1 = "- P10b %s 완료" % P10B_ID
MARK_B47 = "- 사용자 결정 2026-10-01 B47"


def git(root, *args):
    return subprocess.run(["git", "-C", root] + list(args), check=True, capture_output=True).stdout.decode("utf-8").strip()


def lines_c1(root, plan_hash, note):
    hits = [l for l in git(root, "log", "--format=%H\t%s", "gate/master").splitlines()
            if l.split("\t", 1)[1].startswith("audit: %s " % P10B_ID) or l.split("\t", 1)[1] == "audit: %s" % P10B_ID]
    if len(hits) != 1:
        raise SystemExit("중단: gate/master에 P10b 판정 기록 커밋 %d개(기대 1)" % len(hits))
    p10b_sha, p10b_subj = hits[0].split("\t", 1)
    p10_subj = git(root, "log", "-1", "--format=%s", P10_AUDIT)
    if not p10_subj.startswith("audit: 20260930-p10-df23-inventory"):
        raise SystemExit("중단: %s 제목이 P10 판정 기록이 아니다" % P10_AUDIT)
    out = [
        "",
        "- P10 20260930-p10-df23-inventory 완료(gate %s, test-only, 재시도 없음): 문서 커밋 0fa6ca2(df23_inventory measured_at 766b5c2) -> spec·interface card b8d4c4d -> test 56b86c6 -> 판정 기록. 판정 기록 커밋 제목: \"%s\"." % (P10_AUDIT, p10_subj),
        "%s(gate %s): 판정 기록 커밋 제목: \"%s\"." % (MARK_C1, p10b_sha[:7], p10b_subj) + ((" " + note) if note else ""),
        "- 문서 커밋(P10b 뒤): design 20 §11-1 정정(DF-19·DF-26 교체는 MG1과 한 자리가 아님 -- A2 뒤 넷 몫 = B26-1~B26-4, 전압 몫 = MG1), spec card 양식 '작성 전 실측' 8~13(V3 규모·승인 줄·범위 계약·test 이름·같음 판정·red 모양), history H1 2026-09-30 6행·10-01 7행 + H2 DF-36 V3 면제 누수 1행. plan_tables_hash 전후 동일 %s." % plan_hash,
    ]
    return out


def lines_b47(root, d_commit, measured_at):
    d_full = git(root, "rev-parse", d_commit)
    if git(root, "rev-parse", d_full + "^") != git(root, "rev-parse", measured_at):
        raise SystemExit("중단: D^ != measured_at")
    return [
        "%s(승인 기록 20261001-b47-md-sync, decision): 오케스트레이터 B47 점검 보고(15:30 KST) '처리 방침 (원칙상 기본안이라 따로 여쭙지 않고 진행합니다)' -- "
        "\"1. **md 2개 재생성:** 계획 쓰기 경로표상 이 md는 승인 조건이 없는 파생 문서입니다. 다음 문서 커밋에 함께 넣겠습니다. 커밋 전에 다른 4개 md의 diff가 0인지 확인합니다.\" / "
        "\"2. **일치 test card 추가:** md 표를 직접 파싱해 json과 대조하는 test-only card입니다. 렌더러를 부르지 않으므로 작성자와 검증자가 분리됩니다. 재발 방지를 위한 것이고, spec card 초안을 띄웠습니다(C:/g95).\" "
        "-- 사용자 답 \"응, 그렇게 진행해\"(15:32), md 일치 card 검토 요약(16:34) 뒤 같은 답(16:40). 메시지 전체 원문은 승인 기록. "
        "재생성은 card 계약 8·9 때문에 Change-Id 20261001-topology-md-sync를 단 별도 문서 커밋 D %s(measured_at = D^ = %s), card는 단독 test-only." % (MARK_B47, d_full[:7], git(root, "rev-parse", "--short=7", measured_at)),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--mode", required=True, choices=("c1", "b47"))
    ap.add_argument("--plan-hash")
    ap.add_argument("--p10b-note")
    ap.add_argument("--d-commit")
    ap.add_argument("--measured-at")
    ns = ap.parse_args()
    path = os.path.join(ns.root, *REL.split("/"))
    with open(path, "rb") as f:
        data = f.read()
    if not data.endswith(b"\n"):
        raise SystemExit("중단: %s 끝이 줄 끝이 아니다" % REL)
    eol = b"\r\n" if data.endswith(b"\r\n") else b"\n"
    if ns.mode == "c1":
        if not ns.plan_hash or len(ns.plan_hash) != 64:
            raise SystemExit("중단: --plan-hash(64자리) 필요")
        note = ""
        if ns.p10b_note:
            with open(ns.p10b_note, "rb") as f:
                note = f.read().decode("utf-8").strip()
            if "\n" in note:
                raise SystemExit("중단: --p10b-note는 한 줄")
        mark, new = MARK_C1, lines_c1(ns.root, ns.plan_hash, note)
    else:
        if not (ns.d_commit and ns.measured_at):
            raise SystemExit("중단: --d-commit, --measured-at 필요")
        mark, new = MARK_B47, lines_b47(ns.root, ns.d_commit, ns.measured_at)
    if mark.encode("utf-8") in data:
        raise SystemExit("중단: 표지 줄이 이미 있다(중복 append 방지): %s" % mark)
    add = b"".join(l.encode("utf-8") + eol for l in new)
    with open(path, "ab") as f:
        f.write(add)
    with open(path, "rb") as f:
        after = f.read()
    if after != data + add:
        raise SystemExit("중단: append 뒤 바이트 대조 실패 -- git diff로 확인")
    print("append: %s +%d줄 (%d바이트)" % (REL, len(new), len(add)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
