"""MOD7 box 용 행 접기 `apply_explicit_row_split`(총 W 보존) -- 옛 stick_diagram.py 본문 복사(L10).

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations

from dataclasses import replace as _dc_replace


def apply_explicit_row_split(rows: dict, row_split: dict) -> dict:
    """`row_split`(`{stack_id: n_rows}`)에 명시된 stack을 `n_rows`개 물리 행으로 균등
    분할한다 -- box-shape 비율을 맞추기 위한 **명시적 소자 folding**(2026-08-13 세션31,
    사용자 승인 -- `two_stage_ota`의 M6처럼 매칭 파트너가 없는 단독 소자가 box-shape
    비율을 지배할 때, 그 소자 자체를 여러 병렬 물리 인스턴스로 접는 것 -- 추가 contact/via
    비용이 실제로 든다). `repair_matching_safety()`/`common_centroid_layout()`이 이미
    하는 "매칭 품질(3c) 개선을 위한 자동 재배치"와는 목적이 다르다 -- 그건 자동 판단이지만,
    이건 순수 면적/비율 목적이라 자동으로 판단하지 않고 **호출자가 명시적으로 선언**해야만
    적용된다(§8.5 원칙: box-shape FAIL을 수용할지 분할할지는 설계자 판단).

    `rows`의 각 stack 안에 소자가 여러 개(예: 매칭쌍)여도 **소자별로 독립적으로** 접는다
    (`_fixup_euler_blocked_rows()`의 `_connected_components()`처럼 여러 소자를 하나로
    묶어 재배치하는 게 아니다 -- 이건 "이 stack의 모든 소자를 각자 n_rows로 접어라"는
    단순 요청). 소자의 `n_fingers`를 `n_rows`로 최대한 고르게 나누고(나머지는 앞쪽 조각부터
    +1), 0개가 되는 조각은 만들지 않는다(n_fingers < n_rows면 실제로는 그보다 적은 행만
    생긴다 -- 조용히 무시하지 않고 반환된 행 개수로 그 사실이 드러난다).

    각 조각은 새 `stack_id` `f"{sid}_split{i}"`를 받는다. `row_split`에 없는 stack은
    손대지 않고 그대로 반환한다(기본 동작 100% 보존, opt-in).

    반환: 갱신된 `rows` dict."""
    new_rows = {}
    for sid, devs in rows.items():
        n_rows = row_split.get(sid)
        if not n_rows or n_rows <= 1:
            new_rows[sid] = list(devs)
            continue
        per_device_chunks = {}
        for t in devs:
            base, rem = divmod(t.n_fingers, n_rows)
            chunk_ns = [base + (1 if i < rem else 0) for i in range(n_rows)]
            per_device_chunks[t.name] = [n for n in chunk_ns if n > 0]
        max_chunks = max((len(v) for v in per_device_chunks.values()), default=0)
        for i in range(max_chunks):
            split_sid = f"{sid}_split{i}"
            row_devs = []
            for t in devs:
                chunks = per_device_chunks[t.name]
                if i < len(chunks):
                    row_devs.append(_dc_replace(t, n_fingers=chunks[i], stack_id=split_sid))
            if row_devs:
                new_rows[split_sid] = row_devs
    return new_rows
