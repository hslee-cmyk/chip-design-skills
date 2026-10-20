"""[NFR-4 card 2, N-T23] 9 library 회로의 층 0 시작점 -- BP1 로 판정 경계에 놓인 `w_min:*` 행이 판정 쪽(c > 0)에 있다(interface card C4, 설계 41 §5.13).

무엇을 보나(회로마다 한 프로세스 안에서 순차 -- 단계 A -> B -> 커널 컨텍스트 -> 탐색 컨텍스트 -> `layer0_start`, 층 0 이 없는 `ngcc_3stage_ff`(단계 A
review_needed, 기준선 status) 제외 8회로): 층 0 결과 시작점(`Layer0Result.start`)을 `evaluate` 로 다시 평가해
- 경계 행 = `w_min:*` 행 중 |c| ≤ 1(분해능 한 칸 -- c 는 분해능 단위, 설계 40 §2.4.13 (4) 'ConstraintRow.c 분해능 1') -> 모두 c > 0.
  BP1(41 §5.13)은 W_min 경계에 놓는 점을 (1 + √ε) 여유로 판정 쪽에 둔다 -> c ≈ W_min·√ε/grid > 0. as-built(√ε 없음)는 경계 행이 반올림으로
  c < 0 이 될 수 있다(실측: folded_cascode `w_min:M8` c −4.68e-10, 설계 40 §2.4.13 (5) B-2).
- `hard_ok` = 시작점 경성 행(w_min·inversion_floor·원뿔) c ≥ 0 전부(BP2 판정 그대로, C4) -- 그래서 hard_ok 가 False 이면 그 원인 행에 경계 `w_min`
  행이 없다(위 단언이 그것을 막는다).
- 비공허: 8회로 전체에서 경계 `w_min` 행이 1개 이상 있다(없으면 이 test 는 아무것도 보지 않은 것). 층 0 이 시작점을 내지 못한 회로(start None --
  base 실측 current_reuse_telescopic_ota)는 볼 행이 없어 목록에만 남긴다(시작점이 없으면 경계 배치도 없다).
oracle (식): 판정식 c > 0(C4·41 §5.13 문장), 경계 대역 = 분해능 1 칸. 기대값을 피검 출력으로 만들지 않는다.
slow 마커 없음(층 0 까지만 -- 설계 40 §2.4.13 (5) '41 §5.13 셋째 test 는 표시하지 않는다'). 회로는 한 프로세스에서 순차(병렬 없음).
실 LUT 데이터가 없으면 FAIL(skip 아님).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, evaluate, layer0_start, open_run
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access

SKILL = Path(__file__).resolve().parents[3]
LIBRARY = SKILL / "assets" / "library"
CIRCUITS = sorted(p.name.removesuffix(".topology.json") for p in LIBRARY.glob("*.topology.json") if not p.name.startswith("_"))
BASELINE = json.loads((Path(__file__).resolve().parent / "fixtures" / "u17_1b_s0_baseline.json").read_text(encoding="utf-8"))
SEARCHED = [c for c in CIRCUITS if BASELINE[c]["status"] == ["ok", "ok"]]     # 층 0 이 있는 회로(기준선 단계 A·B 상태)
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
BAND = 1.0                      # 경계 대역 = ConstraintRow.c 분해능 1 칸(설계 40 §2.4.13 (4))


def _env():
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
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
    return lut, pdk, read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm)


def _settings():
    """탐색 설정 -- tests/integration/test_s0_layer_9circuits.py `_settings` 와 같은 입력(E_B 40 선언)."""
    return SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "nfr4c2 N-T23 test fixture"),), (1e-13, 1e-10))


def _hard_rows(ev):
    """경성 행(C4 BP2): w_min·inversion_floor 제약 행 + 원뿔 행."""
    return [c for c in ev.constraints if c.name.startswith("w_min:") or c.name.startswith("inversion_floor:")] + list(ev.cone)


def test_layer0_boundary_rows_positive_9circuits(tmp_path):
    lut, pdk, rule = _env()
    assert len(SEARCHED) == 8 and "ngcc_3stage_ff" not in SEARCHED, SEARCHED     # 전제: 기준선 상태(층 0 있는 8회로)
    bad, hard_mismatch, boundary, no_start = [], [], [], []
    for circuit in SEARCHED:
        out = tmp_path / circuit
        donors, counters = open_run()      # [XRUN-F1 card B C6·규칙 M M-c] 회로마다(반복문 본문) 새 실행 하나 -- 단계 A·B·커널 컨텍스트가 같은 쌍
        a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), lut, output_dir=out,
                        donors=donors, counters=counters)
        memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
        b = run_stage_b(a, memo, pdk, output_dir=out, diagnostic=True, settings=_settings())
        assert (a.status, b.status) == ("ok", "ok"), (circuit, a.status, b.status)
        kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
        sctx = build_search_context(kctx, a.spec, _settings(), None, pdk, rule, code_fp=a.code_fp)
        r = layer0_start(sctx)
        if r.start is None:                                # 층 0 이 시작점을 내지 못한 회로(실측 base: current_reuse_telescopic_ota
            no_start.append((circuit, r.stop))             # stop start_no_root_in_window+probe_eval_budget) -- 볼 행이 없다(기록, 공허 아님은 아래)
            continue
        ev = evaluate(sctx, r.start.theta, r.start.cells)
        rows = [(c.name, c.c) for c in ev.constraints if c.name.startswith("w_min:") and abs(c.c) <= BAND]
        boundary.extend((circuit, n, c) for n, c in rows)
        bad.extend((circuit, n, c) for n, c in rows if not c > 0)
        if r.hard_ok != all(c.c >= 0 for c in _hard_rows(ev)):
            hard_mismatch.append((circuit, r.hard_ok))
    assert not bad, bad                                    # 경계 w_min 행은 판정 쪽(c > 0)
    assert not hard_mismatch, hard_mismatch                # hard_ok = 경성 행 c ≥ 0 전부(BP2)
    assert boundary, ("경계 w_min 행이 한 회로에도 없다(공허)", no_start)
    assert len(no_start) < len(SEARCHED), no_start
