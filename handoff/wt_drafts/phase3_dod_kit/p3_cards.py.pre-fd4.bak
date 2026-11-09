"""Phase 3 DoD card 목록(design 30 §8·§8.1·§9.1, 기록 20261001-b26-phase3-cards). inputs_p3.py·n63_p3.py가 import한다.

id의 날짜 머리는 커밋 때 정해지므로(아직 spec card가 없는 M2~M10·T1 등) slug로 맞춘다. 이미 id가 정해진 card는 전체 id로 맞춘다.
판정 기준이 아니라 **목록 대조용**이다: N6.3 2번은 H 트리의 `^phase: 3$` spec card 전부를 세고, 이 목록과 다르면 그 차이를 FAIL로 적는다.
"""
import re

# (표지, id 정규식, design §8 판정 유형, 판정 기록이 공급하는 DoD 입력)
PHASE3 = [
    ("B34", r"20260930-b34-grammar-explicit", "red-green", "N6.3 목록, E5 D-28 (e) 의도된 변경 없음(B34 계약 7)"),
    ("b26pre", r"20260930-b26-pre-test-strengthen", "test-only", "N6.3 목록"),
    ("backfill", r"20261001-b26-backfill-interdig-final-audit", "red-green", "N6.3 목록, E5 D-28 (e)(interdig_ok는 instance.json 밖)"),
    ("B26-1", r"20260930-b26-rail-accessor-set", "red-green", "N6.3 목록, E5 MASK_META rails 계약값(B26-1 계약 1·2·8)"),
    ("T0", r"\d{8}-p3-tests-location-free", "test-only", "N6.3 목록(LOC-FREE는 card 판정)"),
    ("FU", r"\d{8}-p3-future-annotations", "equivalence", "N6.3 목록"),
    ("D0a", r"\d{8}-p3-move-plan-tool", "red-green", "MPC(move_plan.py 사본 출처) -- E2·E4·E6"),
    ("D0b", r"\d{8}-p3-registry-dest", "red-green", "E4 test contracts/test_p3_registry_dest.py"),
] + [("M%d" % n, r"\d{8}-p3-move-mod%d-[a-z0-9-]+" % n, "equivalence",
      "E2 cards.txt 한 줄(base·code·MOD·V1 --gmid-strict)" + (", B0 = base_commit(E2 INVALID 검사·E3 거부 확인·E3b·E6)" if n == 1 else ""))
     for n in (1, 2, 3, 4, 5, 6, 8, 9)] + [
    ("M10", r"\d{8}-p3-mod10-entry", "red-green", "E6 --allow-changed 두 단위(ENTRY)"),
    ("T1", r"\d{8}-p3-test-relocate", "test-only", "N6.3 목록"),
    ("F1", r"\d{8}-p3-callers-update", "equivalence", "N6.3 목록(E3·E3b의 대상 상태를 만든다)"),
    ("F2", r"\d{8}-p3-shim-delete", "red-green", "E1 LAYER·E3·E3b 판정 시점 = F2 병합 뒤"),
]
# Phase 3 기간 게이트 card(phase 0.5) -- G1의 선행(design §5.5.1)과 G1. N6.3 1번 전수에 들고, 2번 목록에는 넣지 않는다.
GATE05 = [
    ("34 면제 묶기", r"20260930-v3-exempt-binding"),
    ("35 범위 정책", r"20260930-v3-changed-stmt-scope"),
    ("B33", r"20260930-v7-registry-edges"),
    ("G1", r"\d{8}-p3-gate-move-aware"),
]


def match(cat, ids):
    """cat의 표지마다 ids 중 정규식에 정확히 맞는 id 목록."""
    return {lab: sorted(i for i in ids if re.fullmatch(rx, i)) for lab, rx, *_ in cat}
