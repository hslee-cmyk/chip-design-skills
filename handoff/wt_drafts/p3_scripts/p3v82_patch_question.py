"""v8.1 -> v8.2 승인 질문(phase3_approval_question.md)·문서 개정(p3_doc_amendments.md) 교체. '현재' 문자열마다 정확히 1번.
사용: python -B p3v82_patch_question.py <question.md> <amendments.md> <e_lib_p3.py sha256 전체>"""
import sys
Q, AM, LSHA = sys.argv[1], sys.argv[2], sys.argv[3]

def patch(path, pairs):
    t = open(path, encoding="utf-8", newline="").read()
    assert "\r\n" not in t
    for old, new in pairs:
        n = t.count(old)
        assert n == 1, (path, n, old[:80])
        t = t.replace(old, new, 1)
    open(path, "w", encoding="utf-8", newline="").write(t)
    print("patched", path)

def cut(path, start, end_incl, new):
    t = open(path, encoding="utf-8", newline="").read()
    assert t.count(start) == 1
    i = t.index(start); j = t.index(end_incl, i) + len(end_incl)
    open(path, "w", encoding="utf-8", newline="").write(t[:i] + new + t[j:])

patch(Q, [
    ("# Phase 3 승인 질문 문안 -- design `30-module-split`(초안 v8.1)", "# Phase 3 승인 질문 문안 -- design `30-module-split`(초안 v8.2)"),
    ("(새 측정 스크립트 §7 포함, 문안 `_drafts/p3_scripts/e_inst_p3_proposed/e_inst_p3.py`)",
     "(새 측정 스크립트 §7·§8 포함, 문안 `_drafts/p3_scripts/e_inst_p3_proposed/e_inst_p3.py`·`_drafts/p3_scripts/e_lib_p3_proposed/e_lib_p3.py`)"),
    ("m-a~m-c를 v8.1에서 반영; 개정 전 사본 `phase3_approval_question.v8.md`).",
     "m-a~m-c를 v8.1에서 반영; 개정 전 사본 `phase3_approval_question.v8.md`).\n"
     "**v8.2(오케스트레이터 결정)**: UD-0 (c)의 기본안(Recommended)을 선례 `20260930-phase2-e4-baseline` 모양으로 바꿨다 -- 같은 상황에서 사용자가 고른 쪽(\"둘다 기본안으로 진행해\")을 따른다는 원칙. "
     "B0 비교는 대안. 개정 전 사본 `phase3_approval_question.v8.1.md`, design 사본 `draft_phase3_design_v8.1.md`."),
    ("같은 해시를 재는 새 측정 스크립트 하나를 design과 함께 넣습니다(옛 스크립트와 같은 결과임을 완료 판정 때 먼저 확인).",
     "같은 해시를 재는 새 측정 스크립트를 design과 함께 넣습니다(E-INST용 하나, 그리고 (c)의 의도된 필드를 빼고 재는 E-LIB용 하나 -- 둘 다 옛 스크립트와 같은 결과임을 완료 판정 때 먼저 확인)."),
    ("> - 새 파일 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`(Phase 3 E-INST 측정 스크립트)",
     "> - 새 파일 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`(Phase 3 E-INST 측정 스크립트)와 같은 디렉터리 `e_lib_p3.py`(E-LIB 측정 스크립트 -- 기존 것에 '뺄 meta 키' 인자 하나만 더함)"),
    ("/ (c) 선례 모양(대안) -- Phase 2 완료 판정 대상 커밋과 비교, 의도된 필드만 따로 판정).",
     "/ (c) 대안 -- B0와 비교하고 Phase 2 완료 판정 판과는 card 판정 기록 사슬로 잇는다)."),
    ("v8.1에서 고친 것(6차 검토):", "v8.2에서 고친 것(오케스트레이터 결정): UD-0 (c) 기본안을 선례 모양으로(Phase 2 완료 판정 대상 커밋과 비교 + 의도된 필드 `meta[\"rails\"]`만 계약값으로 따로 판정), E-LIB용 `e_lib_p3.py` 추가(문서 개정 §8).\nv8.1에서 고친 것(6차 검토):"),
])

cut(Q, "> - (c) **D-28 동작 보존 비교 판** -- 완료 판정의 E-LIB·E-INST를 무엇과 비교할지입니다.", "대안을 고르면 E5 행과 측정 명령을 그 모양으로 고친 판을 다시 올립니다.\n",
    "> - (c) **D-28 동작 보존 비교 판** -- 완료 판정의 E-LIB·E-INST를 무엇과 비교할지입니다.\n"
    ">   **기본안 (Recommended)**: **Phase 2 완료 판정 대상 커밋**과 Phase 3 마지막 병합본을 같은 경로에서 비교합니다. 그 사이 card가 의도적으로 바꾼 필드만 빼서 그 card의 계약값으로 따로 판정하고,\n"
    ">   나머지는 해시가 같아야 합니다. 빼는 필드는 card 계약에서 유도하고 실측으로 확인했습니다 -- E-LIB의 `load_topology` `meta[\"rails\"]` **하나**(B26-1이 더하는 키, 계약값 = 그 회로의 `supply_nets` 선언).\n"
    ">   E-INST(instance.json)에서 빼는 필드는 **없습니다**: B34·B26-1은 계약상 같은 값이고, test 보강 card는 엔진을 바꾸지 않으며, backfill 결함 card가 바꾸는 `relaxed_pairs`의 `interdig_ok`는\n"
    ">   instance.json·보고서에 쓰이지 않습니다(파일럿에서 그 값이 저장 함수까지 넘어가지만 파일에 0회 -- 실측).\n"
    ">   **대안**: 비교 판 = **B0**(M1 판정 기록의 `base_commit`, Phase 3 이동 직전 판). Phase 2 완료 판정 판과 B0 사이(B34 → test 보강 card → backfill 결함 card → B26-1)는 각 card의 판정 기록이 잇습니다.\n"
    ">   측정 명령은 같고 비교 커밋 하나만 바뀝니다.\n"
    ">   **선례**: Phase 2 완료 판정의 같은 질문(승인 기록 `20260930-phase2-e4-baseline`)에서 선택지는 \"기본안 = da03c0e와 Phase 2 마지막 병합본을 같은 경로에서 비교하고 `topology_ref`만 DF-36 계약값으로 판정,\n"
    ">   대안 = card별 판정 기록 사슬로 갈음\"이었고, 답은 \"둘다 기본안으로 진행해\"였습니다. 이번 기본안은 그 선례와 같은 모양입니다(v8.1 문안은 반대로 B0를 기본안으로 두었습니다).\n"
    ">   대안이 나은 경우: 비교 창을 Phase 3 이동만으로 좁혀, 앞선 card의 의도된 변경과 Phase 3 결함이 한 비교에 섞이지 않게 하고 싶을 때입니다.\n")

patch(AM, [
    ("**v8의 새 측정 스크립트 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`(§7)**를 덮는다",
     "**v8의 새 측정 스크립트 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`(§7)와 v8.2의 `e_lib_p3.py`(§8)**를 덮는다"),
    ("이유·동등 근거는 design 30 D-28·§10 E5(동등 확인은 DoD가 B0에서 먼저 잰다).",
     "이유·동등 근거는 design 30 D-28·§10 E5(동등 확인은 DoD가 비교 판 P2D -- 대안이면 B0 -- 에서 먼저 잰다, v8.2)."),
])
t = open(AM, encoding="utf-8", newline="").read()
assert "## §8." not in t
t = t.rstrip("\n") + "\n\n## §8. 새 파일 -- Phase 3 E-LIB 측정 스크립트 (D-28 (e), v8.2 -- UD-0 (c) 선례 모양)\n\n" \
    "경로: `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_lib_p3.py`(지금 없음 -- 새 파일). 내용 = `_drafts/p3_scripts/e_lib_p3_proposed/e_lib_p3.py` 그대로(sha256 `%s`).\n" \
    "오케스트레이터가 design 30 커밋에 같은 바이트로 넣고, 승인 기록 `diff_path`가 덮는다. `e_lib.py`(design 20 §10 E4 정본, `.ai/verification/20260930-df36-instance-relpath/scripts/`)와의 차이는 한 곳뿐이다\n" \
    "(`<root> <out.json>` 뒤에 meta 키 이름을 받아, 회로마다 `load_topology` 반환의 meta에서 그 키를 빼고 해시를 계산하며 뺀 값은 `circuits.<회로>.masked`에 따로 싣는다 -- 출력에 `masked_meta_keys`·`circuits.*.masked` 두 키가 더해진다).\n" \
    "키를 주지 않으면 `hash`와 나머지 출력이 `e_lib.py`와 같다(실측 design 30 부록 A F2v82). DoD E5만 쓴다(M card는 `e_lib.py` 그대로). 이유·판정은 design 30 D-28 (e)·§10 E5.\n" \
    "계획서·design 문장이 아니므로 '적용 확인'의 표 점검 대상이 아니다 -- `sha256sum`이 위 값과 같은지만 본다.\n" % LSHA
open(AM, "w", encoding="utf-8", newline="").write(t)
print("appended §8", AM)
