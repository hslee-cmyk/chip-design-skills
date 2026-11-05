"""B-T22 (slow) [XRUN-F1 card B C8·C1] 9 library 회로 -- 한 실행 안 같은 입력 재계산 0(G-10).

회로마다 실행 하나(`open_run()` 한 쌍): 단계 A -> 단계 B(진단) -> 커널 컨텍스트 -> 탐색 컨텍스트 -> `find_front`(선언 평가 예산 E_B 40).
단계 A·B 가 둘 다 ok 가 아닌 회로(card B: `ngcc_3stage_ff`)는 단계 B 까지 돌리고 그 실행 `counters.snapshot()` 으로 같은 단언을 한다.
oracle (식) interface card C8·C1:
- `perf.blocks` 모든 행 `recomputes_same_input` = 0, `perf.recompute_same_key` = 0(같은 입력 재계산 0), 행마다 calls = reuses + grafts + replays + computes.
- S0 수준 블록 행 `computes` = 1. S0 수준 블록 = tests/integration/test_s0_layer_9circuits.py 와 같은 정의(그 모듈의 `GRAPH_ROWS`·`DEVICE_START`
  를 그대로 쓴다 -- 정의 한 곳): S0 수준 스냅샷의 graph S0 레코드 필드 writer + 출발 구간 소자 필드 writer. 스냅샷은 탐색 회로면 `sctx.dc.base`,
  아니면 단계 B 결과 `s1.snapshot`. test 가 스냅샷 필드 writer 를 직접 모은다(피검 계수를 읽지 않는 목록).
- 전제: 선언 예산(`eval_budget_source == "declared"`, `eval_budget == 40`), 벽시계 정지 0(넉넉한 시간 예산 600 s).
실 LUT 데이터가 없으면 FAIL(skip 아님). 메모리: 회로마다 parametrize 한 항목, 결과를 모듈에 쌓지 않는다.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, find_front, open_run
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access

import o227_stop_pin      # 정지 사유 고정 헬퍼·표(O-227 임시) -- tests/integration/o227_stop_pin.py
from test_s0_layer_9circuits import DEVICE_START, GRAPH_ROWS, _baseline  # noqa: E402  S0 수준 블록 정의·기준선 조회 한 곳

pytestmark = pytest.mark.slow

SKILL = Path(__file__).resolve().parents[3]
LIBRARY = SKILL / "assets" / "library"
CIRCUITS = sorted(p.name.removesuffix(".topology.json") for p in LIBRARY.glob("*.topology.json") if not p.name.startswith("_"))
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
E_B = 40                                   # card B B-T22 '선언 E_B 40' -- 입력 선택
# card B B-T22: 단계 A·B 까지만인 회로(탐색을 하지 않는다 -- 단계 A·B 상태가 둘 다 ok 가 아니다). [O-227 (2)] cnr_ota·erfc_ota(단계 A·B 정지,
# 단계 B 정지 사유)·r2r_opamp(단계 A·B stopped, 단계 A 정지 표지 3건)·rfc_ota(review_needed)를 등록했다: 실행으로 잰 상태가 넷 다 [ok, ok] 가
# 아니다(탐색 안 함). 이 회로들의 G-10 은 탐색 행이 없고 **단계 A·B 계수만** 본다(탐색 G-10 은 이 회로에 대해 검사되지 않는다).
NOT_SEARCHED = {"ngcc_3stage_ff", "cnr_ota", "erfc_ota", "r2r_opamp", "rfc_ota"}
COUNT_FIELDS = ("calls", "reuses", "grafts", "replays", "computes", "recomputes_same_input")


def _settings():
    return SearchSettings(600.0, E_B, (1e2, 1e5), (("front_budget_s", "xrunf1b B-T22 fixture"),), (1e-13, 1e-10))


@pytest.fixture(scope="module")
def env():
    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = dict(DEVICE_KINDS)
    mins = {}
    for e in man["slices"]:
        mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
    dm = BoundedLRU(16)
    pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
    q = dict(pdk.quantities)
    spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                   noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path, bin_rule=loc.bin_rule_path)
    return SimpleNamespace(lut=lut, pdk=pdk, rule=read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm))


def _s0_writers(snapshot):
    """S0 수준 블록 = graph S0 레코드(GRAPH_ROWS 의 key) 필드 writer + 출발 구간 소자 필드(DEVICE_START) writer -- 스냅샷을 직접 읽는다."""
    keys = {k for k, _f, _w in GRAPH_ROWS}
    out = set()
    for kind in snapshot.kinds():
        for key in snapshot.keys(kind):
            rec = snapshot.record(kind, key)
            for name in rec.field_names():
                if (kind == "graph" and key in keys) or (kind == "device" and name in DEVICE_START[0]):
                    out.add(rec.get(name).writer)
    return sorted(out)


def _check_rows(rows, writers):
    """rows = [{block, part, 여섯 칸}]. 위반 목록(빈 목록이면 통과)."""
    bad = []
    by_block = {}
    for r in rows:
        if r["recomputes_same_input"] != 0:
            bad.append(("recomputes_same_input", r))
        if r["calls"] != r["reuses"] + r["grafts"] + r["replays"] + r["computes"]:
            bad.append(("calls_identity", r))
        by_block.setdefault(r["block"], []).append(r)
    for w in writers:
        got = by_block.get(w)
        if not got or sum(r["computes"] for r in got) != 1:
            bad.append(("s0_computes_not_1", w, got))
    return bad


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_no_same_input_recompute_in_one_run(env, circuit, tmp_path):
    pinned = o227_stop_pin.is_stop_pinned(circuit)      # [O-227 (2)] 단계 B 정지 회로(cnr_ota·erfc_ota): 기준선 없이 정지 사유 고정(임시)
    if not pinned:
        _baseline(circuit)                   # 전제: card B 회로 구분(NOT_SEARCHED)은 기준선이 있는 회로에만 정의됨 -- 없으면 이 회로만 실패
    out = tmp_path / "out"
    donors, counters = open_run()
    a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), env.lut, output_dir=out,
                    donors=donors, counters=counters)
    memo = LutMemo(env.lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    b = run_stage_b(a, memo, env.pdk, output_dir=out, diagnostic=True, settings=_settings())
    searched = (a.status, b.status) == ("ok", "ok")
    assert searched == (circuit not in NOT_SEARCHED), (circuit, a.status, b.status)     # 전제: card B 의 회로 구분
    if not searched:
        assert b.s1 is not None
        snap = a.counters.snapshot()
        rows = [dict({"block": r.block, "part": r.part}, **{f: getattr(r, f) for f in COUNT_FIELDS}) for r in snap.blocks]
        assert rows, "전제: 단계 A·B 블록 행이 있다"
        writers = _s0_writers(b.s1.snapshot)
        assert writers, "전제: S0 수준 블록이 있다"
        bad = _check_rows(rows, writers)
        assert not bad, "%s 단계 A·B 실행 계수 위반: %r" % (circuit, bad)
        if pinned:                           # [O-227 M3] 등록·계수 단언을 다 돈 뒤에만: 정지 사유가 표와 같으면 xfail, 다르거나 정지하지 않거나 기준선이 생겼으면 실패
            o227_stop_pin.pin_stop("test_no_same_input_recompute_in_one_run[%s]" % circuit, circuit, b.report, b.report["achievability"] is None)
        return
    root = tempfile.mkdtemp(prefix="g10", dir=os.environ.get("TEMP") or None)     # 짧은 경로(지문 64자 + 파일 이름)
    try:
        kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
        sctx = build_search_context(kctx, a.spec, _settings(), root, env.pdk, env.rule, code_fp=a.code_fp)
        fr = find_front(sctx, [])
        perf = dict(fr.perf)
        assert perf["eval_budget_source"] == "declared" and perf["eval_budget"] == E_B        # 전제: 선언 예산
        assert perf["stops_wall_budget"] == 0                                                  # 전제: 벽시계 정지 0
        assert perf["recompute_same_key"] == 0
        rows = [dict(r) for r in perf["blocks"]]
        assert rows, "전제: perf.blocks 행이 있다"
        writers = _s0_writers(sctx.dc.base)
        assert writers, "전제: S0 수준 블록이 있다"
        bad = _check_rows(rows, writers)
        assert not bad, "%s 한 실행 계수 위반: %r" % (circuit, bad)
    finally:
        shutil.rmtree(root, ignore_errors=True)
