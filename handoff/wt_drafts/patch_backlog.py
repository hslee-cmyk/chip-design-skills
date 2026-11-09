# -*- coding: utf-8 -*-
"""오케스트레이터 백로그 초안(_drafts/backlog_additions.md B29~B50)을 `.ai/context.md` 백로그로 옮긴다.

    python -B patch_backlog.py --root <저장소> [--check] [--at eof|after-backlog] [--skip B38,...] [--with-p4]

* 정본 위치: `.ai/context.md`의 날짜별 진행 기록. 백로그는 `- 백로그 추가(...):` 머리 줄 아래 `  - Bnn ...` 하위 항목
  (gate 0f23786 15001~15010행: B29~B37·B32). 그 형식 그대로 새 머리 줄 + 하위 항목을 더한다.
* `--at eof`(기본): 파일 끝에 append(진행 기록은 시간순 -- post_p10b_context_append.py와 같은 방식).
  `--at after-backlog`: 기존 백로그 블록 마지막 줄(B32 앵커) 바로 뒤에 삽입. 둘 다 기존 바이트를 지우지 않는다(삭제 0줄).
* 이미 커밋된 B29~B37·B32는 다시 쓰지 않는다. B35는 원래 줄을 고치지 않고(삭제 0) `B35 보충` 하위 항목으로 더한다.
* 빠지는 것: B45(G1 초안 v7 계약 4 97행에 이미 반영). 근거는 backlog_commit_plan.md.
* `--with-p4`: Phase 4 설계 초안 §9-12가 'B48·B49·B50'으로 제안한 세 항목을 B51~B53으로(번호 겹침) 함께 더한다.
* 안전장치(하나라도 걸리면 아무것도 쓰지 않고 exit 1):
  - 앵커(기존 백로그 줄 B29~B37·B32)가 각각 정확히 1번 있어야 한다.
  - 표지 줄(새 머리 줄)이 이미 있으면 '이미 적용' -- exit 0, 쓰기 없음(멱등).
  - 새로 더할 Bnn이 `  - Bnn ` 모양 줄로 이미 있으면 거부(부분 중복).
  - 항목 문장이 기대는 사실(파일:줄:부분 문자열)을 --root 작업 트리에서 다시 잰다. 어긋나면 거부(줄 번호가 낡은 채 커밋 방지).
  - 파일 끝이 줄 끝이어야 한다. 줄 끝(LF/CRLF)은 파일의 것을 따른다. 쓴 뒤 '원래 바이트에 삽입분만 더해졌는가'를 다시 읽어 대조.
* `--check`: 위 검사와 삽입 미리보기만, 쓰기 없음. exit 0 = 적용 가능 또는 이미 적용, 1 = 거부.
"""
import argparse
import os
import sys

REL = ".ai/context.md"
BASE = "0f23786"

HEADER = ("- 백로그 추가(2026-10-01, 오케스트레이터 초안 `_drafts/backlog_additions.md` 이관 -- 줄 번호는 gate %s 기준 재측정, "
          "B29~B37·B32는 위 2026-09-30 블록에 이미 있음, B45는 G1 초안 v7 계약 4에 반영돼 뺌):" % BASE)

# 기존 백로그 블록(앵커). 각 줄 머리가 정확히 1번 있어야 한다.
ANCHORS = ["  - B29 ", "  - B30 ", "  - B31 ", "  - B33 ", "  - B34 ", "  - B35 ", "  - B36 ", "  - B37 ", "  - B32 "]
AFTER_ANCHOR = "  - B32 레지스트리 누락 -- "

ITEMS = [
    ("B35", "  - B35 보충(2026-10-01) -- B34 인계 사이트 5~8에 더해 **사이트 10·14**(`refine_differential_and_mirror_relations`의 "
            "`if _netclass_al is not None:`(stick_diagram.py 2495), `propose_device_roles_gap_fill`의 `if _idioms_lcmf is not None:`(4076)"
            "·`else`·`cascoded_active_load_legs = set()`(4100) -- 도달 불가 분기 삭제 + 블록 내어쓰기)도 B35 몫. 내어쓴 블록은 V3 새 문장이라 "
            "그 출력(`active_load_leg_candidates`·`signal_referenced_mirror_legs`·`branch_load_partner_candidates`, 뒤 "
            "`gain_role_candidates |= cascoded_active_load_legs`)의 판정 계약이 필요하다(B26-1 v4에서 B35로 넘긴 근거: "
            "`_drafts/review2_b26_1.md` E2·E2b, 모의 실측 생존 13+1)."),
    ("B38", "  - B38 gate master에 커밋된 instance.json 2개가 낡음 -- `workspaces/current-reuse-telescopic-ota-report/"
            "current_reuse_telescopic_ota.instance.json`·`workspaces/folded-cascode-report/folded_cascode.instance.json` 3행 "
            "`topology_ref`가 아직 메인 절대 경로(DF-36 뒤 재생성 안 됨), folded_cascode sizing 값도 현재 생성과 다름"
            "(`_drafts/dryrun_phase2_e4.md` ④). Phase 2 이전부터. 재생성은 기준선 변경(DEC-40, B14와 같은 자리)이라 그때 승인"
            "(초안 `_drafts/draft_e4_clarify.md` -- backlog_additions.md에서 빠졌던 번호를 회수)."),
    ("B39", "  - B39 B34 범위 밖으로 넘긴 analog-grammar 부재 폴백 사이트 -- 사이트 4 `find_differential_and_mirror_forks`"
            "(stick_diagram.py 1333, 기존 생존 변이 1개가 등가 `len(members) >= 2`→`>= 1`, 면제 승인 필요), 사이트 12 "
            "`propose_theta_kcl_gap_fill`(3431, 변이 242·인벤토리 5, 기존 생존 추정 ~48). B34(좁힌 범위) 뒤 처리."),
    ("B40", "  - B40 `propose_device_roles_gap_fill`이 analog-grammar가 있어도 gate 없는 입력에 \"analog-grammar를 import할 수 없어\" "
            "틀린 사유를 실음(stick_diagram.py 3957 `unavailable_reason`) -- B26-1에서 해당 분기 정리 때 함께(B34 초안 관찰)."),
    ("B41", "  - B41 DF-36 V3 판정(148bd6d, killed 22·exempt 4)의 exempt 4개는 `save_instance_json`이 바뀐 뒤 적용된 C8 승인"
            "(20260922-ic3-v3-exempt) id -- 승인 범위 밖 누수 실례. 판정 자동 번복 없음(3b 재판정은 V3 재실행 안 함). history 기록 + "
            "면제 묶기 card(20260930-v3-exempt-binding) 근거로 인용. 필요하면 DF-36 V3 재측정."),
    ("B42", "  - B42 V3 데코레이터 변이 NOOP -- `_replace_def`가 데코레이터 변이를 버림(tools/gates/mutate_changed.py 203 "
            "`nf.decorator_list = []`; 실측 예 topology_library.py:248 `lru_cache(maxsize=256)` 상수 변이가 적용 안 됨). "
            "현행 규칙에도 있는 도구 결함."),
    ("B43", "  - B43 V3 상수 변이에서 bool 제외(mutate_changed.py 160 `not isinstance(node.value, bool)`) -- def 머리 기본값 bool "
            "변경 등 동작 변경이 변이 0개가 될 수 있음(범위 정책 검토 B2)."),
    ("B44", "  - B44 `test_s120_section`(tests/unit/test_selftest_stick_diagram.py 2710, docstring 2714~2716)의 \"analog-grammar 미설치 "
            "상황(ImportError 경로)은 … self-test로 하기엔 위험 … 하지 않는다\"는 B34(`20260930-b34-grammar-explicit`) 병합 뒤 낡는 "
            "서술 -- B34 계약 test(`tests/contracts/test_b34_grammar_explicit.py`, gate %s에는 아직 없음)가 `sys.modules`로 재현한다. "
            "판정 불변, test-author 경로, B34 병합 뒤 그 파일을 고치는 card에서 참조로 고친다(review2_b34 §6)." % BASE),
    ("B46", "  - B46 V3 두 규칙 공통의 기존 한계(범위 정책 card의 약화 아님) -- 연산자 집합에 bool·문자열·이름 교체·예외 종류 변이가 "
            "없고(적대 사례 1a·3a·7·8·9·10b: 변경을 관찰하지 않는 test로 PASS), V3는 def만 보아 모듈·클래스 수준 상수·별칭 변경"
            "(사례 2·3b)은 변이 0개 -- test가 없어도 PASS. 검토: 연산자 확장, 모듈 수준 이름을 읽는 def를 대상으로 삼기"
            "(review2_v3_cards M3, `v3_scripts/out/v3_adv21.txt`)."),
    ("B47", "  - B47 추적 파일 library/folded_cascode.topology.md가 topology.json과 어긋남(낡음) -- md는 M1.gate=vin_p·M2.gate=vin_n"
            "(33·36행), json은 M1.gate=vin_n·M2.gate=vin_p. current_reuse_telescopic_ota.topology.md에도 json의 수동소자(CL·Cf·Cs)가 "
            "없음(오케스트레이터 점검 2026-10-01: library md 6개 중 2개 불일치, 나머지 4개 바이트 동일). topology_to_markdown.py는 "
            "실행하면 이 추적 파일을 덮어씀(2026-10-01 오케스트레이터가 표 출력 중 덮어써 즉시 복원). 처리 방침(md 2개 재생성 문서 커밋 + "
            "md·json 일치 test card `20261001-topology-md-sync`)은 승인 기록 `20261001-b47-md-sync`."),
    ("B48", "  - B48 test_lint (2) '확실한 복사' 오탐 -- 피검 함수의 누적 리스트 초기값 `[]`이 반환 변형으로 잡히고 빈 컨테이너가 잎으로 "
            "취급되지 않아 `assert findings == []`(계약상 '발견 0')가 FAIL(P10b 1차 V4, 2026-10-01). 이번 card는 test 모양"
            "(`len(...) == 0`, spec card 20260930-df23-registry-record 119행)으로 우회, 게이트 수정은 별도 card + 사용자 승인."),
    ("B49", "  - B49 design 20 §8 증거 형식 표기가 판정 기록과 다름 -- §8 표는 P6(`20260930-d-move-tests`)·P8(`20260930-dup-w-calc`)을 "
            "equivalence로 적지만(190·192행) 두 판정 기록의 `evidence_type`은 red-green이다. §8 아래 197행 문단이 P7·P8을 red-green으로 "
            "정정했으나 표 P8 칸은 그대로이고, P6은 표와 197행 문단 모두 equivalence로 남아 있다. Phase 2 DoD 판정 범위 밖(브리핑 v3는 "
            "기록의 evidence_type을 그대로 적게 함, 판정 영향 없음). 문서 정합 card에서 표·문단 정정(Phase 2 DoD 드라이런 2026-10-01 "
            "범위 밖 메모)."),
    ("B50", "  - B50 stick_diagram 층위1 폴백(1584~1596행 주석 \"못 찾던 것만 보충\")이 n=2에서 trace가 이미 찾은 쌍을 "
            "`layer1_fallback` 원소로 한 번 더 낸다 -- 주석 의도와 어긋나는 중복 의심. b26pre 계약 11은 이 원소를 판정에서 빼 거짓 "
            "기준값을 피함(2026-10-01). 결함 여부 확인·수정은 별도 card."),
]

P4_ITEMS = [
    ("B51", "  - B51 VS 축 0.2 V 간격의 보간 오차 대 tol_V 판단 -- U-27 VS 격자 간격은 0.2 V 유지(Phase 4 설계 초안 P-5), auditor가 "
            "#27에서 VS 축 leave-one-out 오차를 기록(E6), 간격 변경 판단은 6b 봉인 설계 때. (Phase 4 설계 초안 §9-12·"
            "decision_package U-27의 'B48' 제안 -- 위 B48과 번호가 겹쳐 B51)"),
    ("B52", "  - B52 sf_pushpull `resolve_stack_layout` 경로 3 결과에 base·head 모두 M1~M4가 어느 그룹에도 없다(반환 그룹이 소자 전체를 "
            "덮지 않음, 기존 동작) -- `_drafts/b37a_revision_log.md` §5. (Phase 4 설계 초안 'B49' 제안 -- 번호 겹침으로 B52)"),
    ("B53", "  - B53 측정 브리핑 규칙: 엔진 사본은 `skills/analog-grammar`를 함께 복사한다 -- 빠지면 current_reuse θ* 평가가 "
            "`vertical_stack_id` 순환 `ValueError`로 바뀐다(B34와 같은 뿌리, 근본 수정은 B34; ud17_coanalysis_pack §6.3). "
            "(Phase 4 설계 초안 'B50' 제안 -- 번호 겹침으로 B53)"),
]

SD = "skills/analog-gmid-design/assets/stick_diagram.py"
# (항목, 경로, 줄 번호(1부터) 또는 None(파일 어디든), 부분 문자열, 기대: True=있어야 함 / False=없어야 함(경로 부재 포함))
FACTS = [
    ("B35", SD, 2495, "if _netclass_al is not None:", True),
    ("B35", SD, 4076, "if _idioms_lcmf is not None:", True),
    ("B35", SD, 4100, "cascoded_active_load_legs = set()", True),
    ("B38", "workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.instance.json", 3,
     "\"topology_ref\": \"C:\\\\Users\\\\HSLEE", True),
    ("B38", "workspaces/folded-cascode-report/folded_cascode.instance.json", 3, "\"topology_ref\": \"C:\\\\Users\\\\HSLEE", True),
    ("B39", SD, 1333, "len(members) >= 2", True),
    ("B39", SD, 3431, "def propose_theta_kcl_gap_fill(", True),
    ("B40", SD, 3957, "analog-grammar를 import할 수 없어", True),
    ("B42", "tools/gates/mutate_changed.py", 203, "nf.decorator_list = []", True),
    ("B42", "skills/analog-gmid-design/assets/topology_library.py", 248, "@functools.lru_cache(maxsize=256)", True),
    ("B43", "tools/gates/mutate_changed.py", 160, "not isinstance(node.value, bool)", True),
    ("B44", "skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py", 2710, "def test_s120_section(", True),
    ("B44", "skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py", 2714, "analog-grammar 미설치 상황", True),
    ("B44", "skills/analog-gmid-design/assets/tests/contracts/test_b34_grammar_explicit.py", None, "", False),
    ("B47", "skills/analog-gmid-design/assets/library/folded_cascode.topology.md", 33, "| M1 | pmos | `tail` | `X` | `vin_p` |", True),
    ("B47", "skills/analog-gmid-design/assets/library/folded_cascode.topology.md", 36, "| M2 | pmos | `tail` | `Y` | `vin_n` |", True),
    ("B47", "skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.md", None, "Cf", False),
    ("B48", "docs/02-design/specs/20260930-df23-registry-record.spec.md", 119, "assert len(findings) == 0", True),
    ("B49", "docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md", 190, "| P6 | `d-move-tests` |", True),
    ("B49", "docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md", 192, "| P8 | `dup-w-calc` | 인라인 6곳 → `size_transistor` | equivalence |", True),
    ("B49", "docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md", 197, "P5·P6·P9는 equivalence", True),
    ("B49", ".ai/verification/20260930-d-move-tests.json", None, "\"evidence_type\": \"red-green\"", True),
    ("B49", ".ai/verification/20260930-dup-w-calc.json", None, "\"evidence_type\": \"red-green\"", True),
    ("B50", SD, 1584, "2026-08-14 층위1 폴백 추가", True),
    ("B50", SD, 1595, "못 찾던 것만 보충", True),
]


def check_facts(root, ids):
    bad = []
    cache = {}
    for item, rel, line, sub, want in FACTS:
        if item not in ids:
            continue
        p = os.path.join(root, *rel.split("/"))
        if not os.path.exists(p):
            if want:
                bad.append("%s: %s 없음" % (item, rel))
            continue
        if rel not in cache:
            with open(p, "rb") as f:
                cache[rel] = f.read().decode("utf-8").splitlines()
        lines = cache[rel]
        if line is None:
            found = (sub in "\n".join(lines)) if sub else True
        else:
            found = line <= len(lines) and sub in lines[line - 1]
        if found != want:
            bad.append("%s: %s:%s %r %s" % (item, rel, line if line else "*", sub, "기대와 다름(있어야 함)" if want else "기대와 다름(없어야 함)"))
    return bad


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--at", choices=("eof", "after-backlog"), default="eof")
    ap.add_argument("--skip", default="", help="뺄 항목 id, 쉼표 구분(예: B38)")
    ap.add_argument("--with-p4", action="store_true", help="Phase 4 초안 제안 3개를 B51~B53으로 함께")
    ns = ap.parse_args()

    skip = {s.strip() for s in ns.skip.split(",") if s.strip()}
    items = [it for it in ITEMS + (P4_ITEMS if ns.with_p4 else []) if it[0] not in skip]
    unknown = skip - {i for i, _ in ITEMS + P4_ITEMS}
    if unknown:
        print("거부: 모르는 --skip id %s" % sorted(unknown))
        return 1

    path = os.path.join(ns.root, *REL.split("/"))
    with open(path, "rb") as f:
        data = f.read()
    if not data.endswith(b"\n"):
        print("거부: %s 끝이 줄 끝이 아니다" % REL); return 1
    eol = b"\r\n" if data.endswith(b"\r\n") else b"\n"
    text_lines = data.split(b"\n")

    errs = []
    for a in ANCHORS:
        n = sum(1 for l in text_lines if l.startswith(a.encode("utf-8")))
        if n != 1:
            errs.append("앵커 %r %d번(기대 1)" % (a.strip(), n))
    hdr = HEADER.encode("utf-8")
    if any(l.rstrip(b"\r") == hdr for l in text_lines):
        print("이미 적용: 표지 줄이 있다 -- 쓰기 없음")
        return 0
    for iid, _ in items:
        if iid == "B35":
            pre = b"  - B35 \xeb\xb3\xb4\xec\xb6\xa9"  # '  - B35 보충'
        else:
            pre = ("  - %s " % iid).encode("utf-8")
        if any(l.startswith(pre) for l in text_lines):
            errs.append("%s 하위 항목 줄이 이미 있다(부분 중복)" % iid)
    errs += check_facts(ns.root, {i for i, _ in items})

    add_lines = [HEADER] + [t for _, t in items]
    add = b"".join(l.encode("utf-8") + eol for l in add_lines)

    if ns.at == "eof":
        pos = len(data)
    else:
        anc = AFTER_ANCHOR.encode("utf-8")
        starts = [i for i in range(len(data)) if data.startswith(anc, i) and (i == 0 or data[i - 1:i] == b"\n")]
        if len(starts) != 1:
            errs.append("삽입 앵커 %d번(기대 1)" % len(starts))
            pos = None
        else:
            nl = data.index(b"\n", starts[0])
            pos = nl + 1

    if errs:
        print("거부(쓰기 없음):")
        for e in errs:
            print("  - " + e)
        return 1

    print("적용 가능: %s +%d줄(%d바이트), 위치 %s, 줄 끝 %r, 항목 %s" % (
        REL, len(add_lines), len(add), ns.at, eol, " ".join(i for i, _ in items)))
    if ns.check:
        for l in add_lines:
            print("    " + l[:160] + ("…" if len(l) > 160 else ""))
        return 0

    new = data[:pos] + add + data[pos:]
    with open(path, "wb") as f:
        f.write(new)
    with open(path, "rb") as f:
        after = f.read()
    if after != new or after[:pos] != data[:pos] or after[pos + len(add):] != data[pos:]:
        print("중단: 쓴 뒤 바이트 대조 실패 -- git diff로 확인")
        return 1
    print("적용함")
    return 0


if __name__ == "__main__":
    sys.exit(main())
