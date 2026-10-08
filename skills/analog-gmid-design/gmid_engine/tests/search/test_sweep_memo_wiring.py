"""설계 40 §7.3 'LUT memo 상한'(D-PF1) 배선 -- `build_search_context` 가 평가 커널 컨텍스트를 만들 때 `LutMemo.from_sweep`
(상한 = (n_θ + 1)·U_eval, U_eval = 첫 평가에서 센 서로 다른 키 수)을 부르고, test 의 고정 상한 상수(4096)가 탐색에 영향을 주지 않는다.
lut CONTRACT 2.2 [2026-10-09 배선]: 첫 평가 = layer0 첫 점(`centre_start`, n_θ = 그 `variables` 수), 결과 memo 가 `sctx.dc.lut` 의 memo.

oracle:
- 상한: (a) 구성 -- 같은 첫 점을 이 파일의 계수 memo(`_CountingMemo`, 엔진 계수기·엔진 계수 memo 를 쓰지 않음)로 `evaluate` 해 영역마다
  서로 다른 (fn_name, key) 수를 직접 센다 -> 기대 상한 = (n_θ + 1)·그 수. n_θ 는 설계가 정한 '첫 점의 변수 수'(`centre_start` 의
  variables -- 첫 점의 정의를 읽을 뿐 상한 계산은 쓰지 않는다).
- 값 동일: (c) 동작 보존 -- memo 는 값을 바꾸지 않는다(CONTRACT 2 lookup: 적중이면 저장 값, 아니면 compute 1회). 같은 입력의
  탐색을 sweep memo 와 호출자 memo(4096)로 돌려 front·평가 결과가 비트 단위로 같아야 한다.
- 상수 무영향: (a) 구성 -- 호출자 memo 상한만 1 과 4096 으로 바꾼 두 실행의 sweep memo 상한·정의역·front 가 같아야 한다.
search·lut `.py` 소스의 상한 계산은 열람하지 않았다(시그니처·docstring 만).
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

from gmid_engine.lut import LutMemo
from gmid_engine.search import evaluate, find_front
from gmid_engine.search.layer0_center import centre_start

from .conftest import build_case, circuit_c, front_signature, theta_r4c

SWEEP = ("point", "curve", "root")


class _CountingMemo:
    """이 test 의 계수 memo: (영역, fn_name + key) 를 한 번만 계산해 저장하고 서로 다른 키를 센다. 나머지 속성(lut 등)은 안쪽
    LutMemo 로 넘긴다. 엔진의 계수 memo·계수기와 무관."""

    def __init__(self, inner):
        self._inner = inner
        self.keys = {}
        self.calls = 0

    def lookup(self, region, fn_name, key, compute):
        self.calls += 1
        d = self.keys.setdefault(region, {})
        k = (fn_name,) + tuple(key)
        if k not in d:
            d[k] = compute()
        return d[k]

    def __getattr__(self, name):
        return getattr(self._inner, name)


def _caps(memo):
    return {r: s.capacity for r, s in memo.stats() if r in SWEEP}


def _build_with_caller_cap(tmp, lut, cap, **kw):
    """search conftest `build_case` 와 같은 입력, 호출자 memo 상한만 `cap`(영역 셋 모두)."""
    from gmid_engine.graph import build_s1
    from gmid_engine.search import SearchSettings, build_search_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
    from .conftest import SRC, load_spec, write_decls
    tmp = Path(tmp)
    acc = pre_layout_lut_access(LutMemo(lut, point=cap, curve=cap, root=cap))
    td, spec = load_spec(tmp / "case", circuit_c())
    inputs = dc_inputs_from_spec(spec)
    dc = build_kernel_context(build_s1(td, dict(inputs.supplies_v)), inputs, acc)
    pdk, rule = write_decls(tmp / "pdk")
    settings = SearchSettings(600.0, kw.get("eval_budget", 30), None, tuple(SRC), None)
    return acc, build_search_context(dc, spec, settings, None, pdk, rule)


def _eval_table(sctx):
    """sctx.cache 의 평가 결과 -> {키 repr: 비트 비교용 repr}. float repr 은 왕복 정확(비트 동일 ⇔ repr 동일)."""
    out = {}
    for k, r in sctx.cache.items():
        fail = None if r.failure is None else repr(r.failure)
        out[repr(k)] = repr((r.theta, r.status, r.objectives, r.constraints, r.cone, r.unmeasured, r.warnings, r.seq, fail))
    return out


def test_search_memo_is_not_callers_and_capacity_is_sweep_bound(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    s = case.sctx
    memo = s.dc.lut.memo
    assert memo is not case.acc.memo                                   # 탐색은 호출자 memo 를 쓰지 않는다
    assert case.dc.lut.memo is case.acc.memo                           # 호출자 kernel context 는 바꾸지 않는다
    # 첫 점(설계: layer0 첫 점)과 n_θ
    variables, theta, cells, _u = centre_start(s)
    n_theta = len(variables)
    assert n_theta >= len(s.domain.variables)
    # 독립 계수: 같은 첫 점을 이 test 의 계수 memo 로 한 번 평가(빈 캐시 -- build 직후 s.cache 는 비어 있다)
    assert len(s.cache) == 0
    cm = _CountingMemo(LutMemo(lut_sealed, point=4096, curve=4096, root=4096))
    probe = dataclasses.replace(s.dc, lut=dataclasses.replace(s.dc.lut, memo=cm))
    s.dc, kept = probe, s.dc
    try:
        evaluate(s, theta, cells)
    finally:
        s.dc = kept
    assert cm.calls > 0                                                # 첫 평가가 LUT 를 실제로 부른다(공허한 비교 방지)
    u_eval = {r: len(cm.keys.get(r, {})) for r in SWEEP}
    assert _caps(memo) == {r: (n_theta + 1) * u_eval[r] for r in SWEEP}   # oracle (a): (n_θ + 1)·U_eval
    assert _caps(memo) != {r: 4096 for r in SWEEP}                     # 호출자 상수가 아니다


def test_eval_results_identical_with_and_without_sweep_memo(tmp_path, lut_sealed):
    """같은 입력의 탐색을 (A) sweep memo(배선 그대로), (B) 호출자 memo(상한 4096)로 돌린다 -> front·모든 평가 결과 비트 동일."""
    a = build_case(tmp_path / "a", circuit_c(), lut_sealed, eval_budget=30)
    b = build_case(tmp_path / "b", circuit_c(), lut_sealed, eval_budget=30)
    assert b.dc.lut.memo is b.acc.memo
    b.sctx.dc = b.dc                                                   # (B) 탐색이 호출자 memo 를 쓴다
    fa = find_front(a.sctx, [theta_r4c()])
    fb = find_front(b.sctx, [theta_r4c()])
    assert a.sctx.dc.lut.memo is not a.acc.memo and b.sctx.dc.lut.memo is b.acc.memo
    assert dict(fa.perf)["stops_wall_budget"] == 0 and dict(fb.perf)["stops_wall_budget"] == 0
    assert front_signature(fa) == front_signature(fb)
    assert fa.front or fa.pending_front or fa.unmeasured_front        # 공허한 비교 방지
    ta, tb = _eval_table(a.sctx), _eval_table(b.sctx)
    assert len(ta) > 1
    assert ta == tb
    assert fa.run_id == fb.run_id


def test_caller_capacity_constant_does_not_influence_search(tmp_path, lut_sealed):
    """호출자 memo 상한 1 과 4096 -> sweep memo 상한·정의역·front·평가 결과 모두 같다."""
    acc1, s1 = _build_with_caller_cap(tmp_path / "c1", lut_sealed, 1)
    acc2, s2 = _build_with_caller_cap(tmp_path / "c4096", lut_sealed, 4096)
    assert s1.dc.lut.memo is not acc1.memo and s2.dc.lut.memo is not acc2.memo
    assert _caps(s1.dc.lut.memo) == _caps(s2.dc.lut.memo)
    assert all(v != 1 and v != 4096 for v in _caps(s1.dc.lut.memo).values())
    assert s1.domain == s2.domain
    f1 = find_front(s1, [theta_r4c()])
    f2 = find_front(s2, [theta_r4c()])
    assert dict(f1.perf)["stops_wall_budget"] == 0 and dict(f2.perf)["stops_wall_budget"] == 0
    assert front_signature(f1) == front_signature(f2)
    assert _eval_table(s1) == _eval_table(s2)
