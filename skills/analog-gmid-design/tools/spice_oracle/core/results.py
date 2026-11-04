# -*- coding: utf-8 -*-
"""core/results.py -- 정규화 결과 자료형과 실패 신호(design §6·§7, card 20261104-op23 interface §1·§5).

어댑터가 코어에 돌려주는 값의 모양이다. 결과 칸 이름에 시뮬레이터 이름을 넣지 않는다(옛 `ngspice_rc` -> `status.rc`).
이 card 몫: RunStatus, OpTable, FreqSeries, Resolution, ResultBundle. Tran·Pz·Noise·OpSweep·Mc*·Tf 는 만들지 않는다
(OP-4·OP-5 몫, 기간 동작 D-1).
"""
from __future__ import annotations

from dataclasses import dataclass, field


class OracleError(Exception):
    """오라클이 입력·기술자·어댑터 선언을 거부하는 신호. code = design §7 코드, detail = 그 코드의 detail, stage = §7.2 단계 문자열."""

    def __init__(self, code: str, detail=None, stage: str | None = None):
        super().__init__(f"{code}: {detail!r}" if detail is not None else code)
        self.code = code
        self.detail = detail
        self.stage = stage


@dataclass(frozen=True)
class Resolution:
    """DC 풀이 허용오차와 출처. reltol·abstol{양: 값}은 입력 simulator.options 또는 어댑터 보정값에서 온다(design §8.3)."""
    reltol: float | None
    abstol: dict
    data_rel: float | None
    source: str                      # 'input_options' | 'adapter_declared'


@dataclass(frozen=True)
class RunStatus:
    rc: int | None
    timed_out: bool
    error: str | None
    warnings: tuple
    log_excerpt: tuple
    log_path: str | None
    cache_state: str | None          # None | 'hit' | 'miss' | 'off'


@dataclass(frozen=True)
class OpTable:
    devices: dict                    # {이름: {id, gm, gds, vth, vdsat, vgs, vds, vbs}}  (None = 시뮬레이터가 값을 안 줌)
    nodes: dict                      # {넷: V}
    currents: dict                   # {원소 이름: A}  (SPICE 부호: + 단자로 들어가 - 단자로 나감)
    resolution: Resolution
    error: str | None
    instance_geometry_reported: dict | None


@dataclass(frozen=True)
class FreqSeries:
    f: object                        # numpy array
    values: dict                     # {expr_key: 복소 numpy array}
    resolution: Resolution
    error: str | None


@dataclass(frozen=True)
class ResultBundle:
    bench_id: str
    adapter_fp: str
    descriptor_fp: str
    status: RunStatus
    by_request: dict
    name_map: dict
    method: str
    bundle_files: dict = field(default_factory=dict)
