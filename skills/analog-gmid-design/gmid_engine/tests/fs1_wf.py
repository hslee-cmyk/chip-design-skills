"""[FS-1 서명 맞춤] 공개 `size_and_seal(ctx, theta, wf, ...)`·`size_and_seal_local(ctx, theta_block, fixed, columns, wf)` 에 손 `WfInput` 을 끼우는 래퍼.
기존 test 가 `from gmid_engine.sizing import size_and_seal` 대신 `from fs1_wf import size_and_seal` 로 부른다 -- 호출 모양은 그대로(wf 는 키워드로도 줄 수 있다).
손 wf: 칸 = 그 ctx 스냅샷 `graph.matching_groups` 폐포(손, sizing.conftest.hand_cells), 칸 키 = 그 kind 후보(`widths`) 가운데 가장 좁은 것 (기존 단일 슬라이스 LUT 에서는 그 슬라이스).
**칸 키 '가장 좁은 후보' 는 이 test 가 정한 입력 선택이지 interface 가 정한 값이 아니다** (옛 선택 함수의 결과를 기대하던 test 가 코드 뒤 어긋나면 판정자가 본다). 평가 입력이지 기대값이 아니다. 필수 인자 `wf` 를 생략하면 TypeError 인 계약(D-4)은 `sizing/test_block_dc.py` 가 공개 함수를 직접 불러 단언한다.
"""
from gmid_engine import sizing as _sz
from gmid_engine.lut import widths


def hand_wf_default(ctx, keys=None):
    from sizing.conftest import hand_cells
    keys = dict(keys or {})
    kinds = dict(ctx.base.column("device", "kind"))
    cells, ks = [], []
    for members in hand_cells(ctx):
        k = keys.get(members[0], widths(ctx.lut, kinds[members[0]])[0])
        cells.append(_sz.WfCell(members, k))
        ks.append(k)
    return _sz.WfInput(tuple(cells), tuple(ks))


def size_and_seal(ctx, theta, *args, wf=None, **kw):
    return _sz.size_and_seal(ctx, theta, hand_wf_default(ctx) if wf is None else wf, *args, **kw)


def size_and_seal_local(ctx, theta_block, fixed, columns, *args, wf=None, **kw):
    return _sz.size_and_seal_local(ctx, theta_block, fixed, columns, hand_wf_default(ctx) if wf is None else wf, *args, **kw)
