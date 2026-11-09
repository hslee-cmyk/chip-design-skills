# -*- coding: utf-8 -*-
"""spec card 양식 '작성 전 실측' 절에 이번 세션(2026-09-30 ~ 10-01) 교훈 6항목(8~13)을 더한다.

근거: review_b26_1(B1·S3)·review2_b26_1·review_b34(B1~B3)·review2_b34(B1)·review_b37a(B3)·review_v3_cards·
P10 판정 기록 V2 계약 6 auditor 주(.ai/verification/20260930-p10-df23-inventory.json).

사용: python -B patch_template.py [--root <저장소 루트>]
- 바이너리 읽기/쓰기, 파일의 줄 끝(LF/CRLF)을 감지해 새 줄에 같은 줄 끝을 쓴다.
- 기준 줄(7항목 끝)이 정확히 1번 있어야 넣는다. 8번 항목이 이미 있으면 '이미 적용'(멱등).
"""
import argparse
import os
import sys

REL = "docs/02-design/specs/_TEMPLATE.spec.md"

ANCHOR = ("7. 기존 계약 test: 바뀌는 이름·파일을 참조하는 기존 계약 test(`A/tests/contracts/`)를 grep했고, "
          "조정이 필요하면 V5 승인 경로를 적었다.")

ITEMS = [
    "8. V3 규모: 초안 단계에서 `tools/gates/mutate_changed.py`의 `changed_defs`·`mutants`·`inventory`를 "
    "시뮬레이션 head에 돌려 대상 def 수·변이 수·인벤토리 test 수를 적었다(그 시점 gate에서 유효한 V3 대상 규칙으로). "
    "바뀌는 def는 작게 유지했다 -- 인자를 넘기려고 호출부 def를 고치면 그 def도 V3 대상이 된다.",
    "9. 승인 줄: 동작을 바꾸거나 다른 Phase의 일을 당겨오는 card는 그것을 덮는 사용자 결정 승인 기록"
    "(`target_kind: decision`)이 `approval` 줄에 있다. design 승인은 '동작이 바뀌는 수정'을 범위에서 뺀 것이 있어 "
    "덮지 않는다 -- 기록의 범위 설명에 이 card id와 바뀌는 동작이 적혀 있는지 원문으로 확인했다.",
    "10. 범위 계약: '바뀐 파일·변경 0' 같은 범위·diff 계약은 '이 card `Change-Id` 커밋들의 diff'로 한정해 적었다"
    "(기준 커밋과 판정 대상 사이에 다른 card 커밋이 끼면 그 diff까지 걸린다).",
    "11. test 이름·모양: 새 test·보조 함수 이름은 card 접두(예: `_b26_`)로 기존 test와 겹치지 않고, 피검 함수는 "
    "test 본문에서 직접 부른다(`parametrize` 이름 문자열·모듈 상수 + `getattr`은 V3 인벤토리 간선으로 잡히지 않는다).",
    "12. 같음 판정: `__eq__`가 없는 객체나 프로세스마다 순서가 다른 `set`을 `==`로 비교하는 계약이 없다 -- "
    "비교할 필드와 정렬·튜플화 규칙(정규화)을 계약에 적었다.",
    "13. red 모양: 각 계약의 base red가 허용 예외 타입(00-common §8.1)이다. `try/except Exception: pytest.fail`로 "
    "다른 예외를 `Failed`로 바꾸지 않고, 새 키워드 인자 직접 호출의 base `TypeError`는 red로 세지 않는다"
    "(red는 시그니처가 안 바뀌는 진입점이 맡는다).",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills")
    ns = ap.parse_args()
    path = os.path.join(ns.root, *REL.split("/"))
    with open(path, "rb") as f:
        data = f.read()
    eol = b"\r\n" if b"\r\n" in data else b"\n"
    anchor_line = ANCHOR.encode("utf-8") + eol
    first_new = ITEMS[0].encode("utf-8")
    if data.count(first_new) == 1 and all(it.encode("utf-8") in data for it in ITEMS):
        print("이미 적용: " + REL)
        return 0
    if data.count(anchor_line) != 1 or b"\n8. " in data:
        print("중단: 기준 줄 %d회(기대 1) 또는 8번 항목이 다른 문안으로 있음 -- %s" % (data.count(anchor_line), REL))
        return 1
    block = b"".join(it.encode("utf-8") + eol for it in ITEMS)
    out = data.replace(anchor_line, anchor_line + block, 1)
    assert out.count(b"\r\n") == data.count(b"\r\n") + (len(ITEMS) if eol == b"\r\n" else 0)
    assert out.count(b"\n") == data.count(b"\n") + len(ITEMS)
    assert out.startswith(data[: data.index(anchor_line) + len(anchor_line)])
    assert out.endswith(data[data.index(anchor_line) + len(anchor_line):])
    with open(path, "wb") as f:
        f.write(out)
    print("적용: %s (+%d줄)" % (REL, len(ITEMS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
