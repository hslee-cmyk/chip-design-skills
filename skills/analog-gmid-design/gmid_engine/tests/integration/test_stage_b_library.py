"""단계 B(`pipeline.run_stage_b`, GB4 달성가능성) 9회로 진단 표 -- 독립 계산할 수 있는 칸만 (pipeline CONTRACT 5절, metrics CONTRACT 10.9, 설계 41 0절·4절).

`run_stage_a(topology, spec)` 뒤 `run_stage_b(diagnostic=True)`(단계 A 가 정지여도 측정)를 회로마다 한 번 돌리고 다음을 엔진과 별개로 계산해 대조한다.
- N_S(oracle (b)): 회로가 쓰는 kind(topology netlist 의 kind 집합)의 모든 슬라이스 npz 축 길이 곱의 합.
- 블록 격자 곱 Π(oracle (a)): Π = ∏ 축 크기, 축 크기는 축 종류의 LUT 격자 길이(vgs |VGS|, L |L|, vds |VDS|, vsb |VS|, current·resistor |VGS| --
  계약 10.3 '로그 균등 |VGS 격자| 점'); Π > N_S 면 미상(`grid_product_over_budget`), 인증이면 Π ≤ N_S (41 4.2 예산 게이트).
  손 유도 블록: two_stage_ota(_sf) 둘째 단 CS(M6 pmos·M7 nmos, 소스 = bulk, 같은 전류 하나 -> 정규화) Π = |VGS|²·|L|²·|VDS|²;
  two_stage_ota_sf 출력 팔로워(M8 하나, 소스 ≠ bulk) Π = |VGS|·|L|·|VDS|·|VS|, 인증, A_max = 레이아웃 전 폭(5 µm) nmos 슬라이스 원시 배열에서
  강반전 분지(곡선 gm/ID 정점 이상) 마디의 GM/(GM + GDS + GMBS) 최댓값, b = 그 최대 행과 격자 이웃(축마다 ±1) 비의 dB 최댓값.
- gain 목표(oracle (d)): spec 의 `gain_ss_db >=` 값(value_from_file 은 참조 파일의 값), 판정 = 미상 블록이 있으면 undetermined, 목표가 없으면 no_target.
- 면적 하한(oracle (a), 41 4.4): 측정 부하가 아닌 커패시터의 C_min(선언값 또는 spec θ 하한) / ρ_MIM(PDK 선언 `mim_cap_density_f_per_m2`) +
  값 선언 이상 전류원만으로 전류가 정해지는 MOS 항 I·L_min²/IDu_max(손 회로 해석: current_reuse 의 Iref 1.2 µA -> diode M18_bg,
  sf_pushpull 의 IBias 50 µA -> diode M4; IDu_max = kind 의 모든 슬라이스 on_mask 점 ID·L/W 최댓값, L_min = L 격자 최솟값).
- 진단 모드(oracle (d), 계약 5절): 정지 판정은 바뀌지 않는다 -> exit code = 단계 A 의 것.
실 LUT 데이터가 없으면 FAIL(skip 아님).
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
import pytest

import o227_stop_pin as pin       # 정지 사유 고정 헬퍼·표(O-227 임시) -- tests/integration/o227_stop_pin.py
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b

SKILL = Path(__file__).resolve().parents[3]
LIBRARY = SKILL / "assets" / "library"
CIRCUITS = sorted(p.name.removesuffix(".topology.json") for p in LIBRARY.glob("*.topology.json") if not p.name.startswith("_"))
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
PRE_LAYOUT_W_KEY = 1000                     # 레이아웃 전 폭 5 µm(sizing CONTRACT 1.3 실측 nmos·pmos 1000)


@pytest.fixture(scope="module")
def env():
    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    names = dict(DEVICE_KINDS)
    from pdk_min_w import min_finger_w_m
    mins = min_finger_w_m(names.values())      # PDK 선언 양(card 20261104-wb1)
    grid = float(man.get("manufacturing_grid_m", 5e-9))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, LutSpec(grid, tuple(sorted(mins.items())), DEVICE_KINDS, (("nmos", "_n"), ("pmos", "_p"))),
                       pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_paths, bin_rule=loc.bin_rule_path)
    pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), BoundedLRU(8))
    # 원시 npz 통계(엔진 미사용)
    root = Path(loc.manifest_path).parent
    stats = {"count": {}, "idu_max": {}, "l_min": {}, "axes": None, "follower": None}
    for e in man["slices"]:
        kind = names[e["device"]]
        with np.load(root / e["file"]) as z:
            n = (len(z["L"]), len(z["VGS"]), len(z["VDS"]), len(z["VS"]))
            stats["axes"] = stats["axes"] or n
            stats["count"][kind] = stats["count"].get(kind, 0) + int(np.prod(n))
            ID, GM, L, W = np.asarray(z["ID"]), np.asarray(z["GM"]), np.asarray(z["L"]), float(z["W"])
            on = (ID > 0) & (GM > 0)
            idu = float(np.where(on, ID * L[:, None, None, None] / W, -np.inf).max())
            stats["idu_max"][kind] = max(stats["idu_max"].get(kind, -np.inf), idu)
            stats["l_min"][kind] = min(stats["l_min"].get(kind, np.inf), float(L.min()))
            if kind == "nmos" and int(round(W / grid)) == PRE_LAYOUT_W_KEY:
                stats["follower"] = _follower_anchor(z)
    return {"lut": lut, "pdk": pdk, "stats": stats, "cache": {}}


def _follower_anchor(z):
    """max GM/(GM + GDS + GMBS) over 강반전 분지 마디(곡선 (L, VDS, VS) 마다 gm/ID 정점 index 이상, 분지에 NaN 이 있는 곡선 제외) + 이웃 분해능."""
    ID, GM, GDS, GMBS = (np.asarray(z[k], float) for k in ("ID", "GM", "GDS", "GMBS"))
    with np.errstate(all="ignore"):
        gmid = np.where((ID > 0) & (GM > 0), GM / ID, np.nan)
        ratio = GM / (GM + GDS + GMBS)
    valid = np.zeros(ID.shape, bool)
    nL, nG, nD, nS = ID.shape
    for l in range(nL):
        for d in range(nD):
            for s in range(nS):
                c = gmid[l, :, d, s]
                if np.isnan(c).all():
                    continue
                p = int(np.nanargmax(c))
                if not np.isnan(c[p:]).any():
                    valid[l, p:, d, s] = True
    r = np.where(valid, ratio, np.nan)
    i = np.unravel_index(int(np.nanargmax(r)), r.shape)
    b = 0.0
    for ax in range(4):
        for dl in (-1, 1):
            j = list(i)
            j[ax] += dl
            if 0 <= j[ax] < r.shape[ax] and valid[tuple(j)]:
                b = max(b, abs(20.0 * math.log10(r[i] / r[tuple(j)])))
    return 20.0 * math.log10(r[i]), b


def _settings():
    """탐색 실행 설정(입력, 기대값 아님) -- tests/search/u13_real.py·integration/test_s0_layer_9circuits.py 와 같은 값."""
    from gmid_engine.search import SearchSettings
    return SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "stage_b library test fixture"),), (1e-13, 1e-10))


def _run(env, circuit, tmp_path_factory):
    if circuit not in env["cache"]:
        out = tmp_path_factory.mktemp("sbl_" + circuit)
        # [xrun J-1] run_stage_a 는 선언 값·선언 경로 인자를 받지 않는다(S0 키에만 쓰이던 인자, interface card C1)
        from types import SimpleNamespace
        from gmid_engine.search import open_run
        donors, counters = open_run()      # [XRUN-F1 card B C6·규칙 M M-c] 회로 실행 하나 = 새 쌍
        a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), env["lut"], output_dir=out,
                        donors=donors, counters=counters)
        memo = LutMemo(env["lut"], point=200000, curve=200000, root=4096)
        # [U17 ①-b 2차, 사용자 결정 4] run_stage_b(settings=) 필수 -- 탐색 설정 입력(test_s0_layer_9circuits `_settings` 와 같은 값)
        b = run_stage_b(a, memo, env["pdk"], output_dir=out, diagnostic=True, settings=_settings())
        # [규칙 M M-d] 모듈 캐시에는 실행의 두 객체를 쥔 결과(StageAResult)를 두지 않고 test 가 읽는 칸만 꺼내 둔다
        env["cache"][circuit] = (SimpleNamespace(status=a.status, exit_code=a.exit_code),
                                 SimpleNamespace(status=b.status, exit_code=b.exit_code, report=b.report, s1=b.s1))
    return env["cache"][circuit]


def _topo(circuit):
    return json.loads((LIBRARY / (circuit + ".topology.json")).read_text(encoding="utf-8"))


def _spec(circuit):
    return json.loads((LIBRARY / (circuit + ".sizing_spec.json")).read_text(encoding="utf-8"))


def _gain_target(circuit):
    for c in _spec(circuit)["human"]["constraints"]:
        if c.get("metric") == "gain_ss_db" and c.get("op") == ">=":
            if "value" in c:
                return float(c["value"])
            ref, metric = c["value_from_file"].split("#")
            return _gain_target(ref) if metric == "gain_ss_db" else None
    return None


# [O-227 (2) 2026-11-04] 정지 사유 고정 -- O-227 임시 고정, LA-1 재점검에서 해제 판단. 표(사유·정지 소자 집합·불량 블록)는 o227_stop_pin.py 한 자리다.
# 아래 (test, 회로) 8건(cnr_ota·erfc_ota)은 엔진이 사유를 내고 정지(achievability null)해 기존 단언에 닿지 못한다. 기대값은 머리에서 실행해 잰
# 관측값(oracle (c) 기준선 -- 사유가 물리적으로 맞는지는 판정하지 않는다). 사유·정지 소자 집합이 표와 정확히 같으면 pytest.xfail(통과로 세지 않음),
# 다르거나 정지하지 않거나 읽을 수 없으면 실패한다. r2r_opamp block_grid 1건은 정지가 아니다(stop_reasons 0건, achievability verdict ok, 블록 하나
# (n_gn, n_gp)가 unknown/block_input_pattern_unsupported 이고 pi 0·axes 빈 목록이라 `pi == ∏ 축`을 어긴다): 그 블록 하나일 때만 고정하고,
# 그 블록의 `pi == ∏ 축` 외 단언과 다른 블록 단언은 전부 돈 뒤 마지막에 xfail 한다. 표에 없는 조합은 헬퍼가 아무것도 하지 않아 기존 단언이 그대로 적용된다.
_STOP_PINNED = {(t, c) for t in ("test_block_grid_products_and_budget_gate", "test_gain_target_and_verdict",
                                 "test_area_lower_bound_from_declared_values", "test_diagnostic_mode_keeps_stage_a_exit_code")
                for c in ("cnr_ota", "erfc_ota")}
_BLOCK_PINNED = {("test_block_grid_products_and_budget_gate", "r2r_opamp")}


def _pin_stop(test, circuit, b, failing):
    if (test, circuit) in _STOP_PINNED:
        pin.pin_stop(f"{test}[{circuit}]", circuit, b.report, failing)


def _pin_blocks(test, circuit, blocks):
    return pin.pin_blocks(f"{test}[{circuit}]", circuit, blocks) if (test, circuit) in _BLOCK_PINNED else []


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_count_budget_is_lut_grid_sum_of_used_kinds(env, circuit, tmp_path_factory):
    _, b = _run(env, circuit, tmp_path_factory)
    kinds = {e["kind"] for e in _topo(circuit)["netlist"]}
    assert b.report["count_budget"] == sum(env["stats"]["count"][k] for k in kinds)


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_block_grid_products_and_budget_gate(env, circuit, tmp_path_factory):
    _, b = _run(env, circuit, tmp_path_factory)
    _pin_stop("test_block_grid_products_and_budget_gate", circuit, b, b.report["achievability"] is None)
    nL, nG, nD, nS = env["stats"]["axes"]
    size_of = {"vgs": nG, "L": nL, "vds": nD, "vsb": nS, "current": nG, "resistor": nG}
    ns = b.report["count_budget"]
    g = b.report["achievability"]["gain"]
    pinned_bad = _pin_blocks("test_block_grid_products_and_budget_gate", circuit, list(g["blocks"]) + list(g["ff"]))
    for blk in list(g["blocks"]) + list(g["ff"]):
        assert all(size == size_of[kind] for kind, size in blk["axes"]), blk["axes"]
        if not any(blk is x for x in pinned_bad):                          # 고정한 불량 블록만 이 등식을 건너뛴다(그 블록의 나머지 단언도 돈다)
            assert blk["pi"] == math.prod(size for _, size in blk["axes"])
        if blk["pi"] > ns:
            assert blk["status"] == "unknown" and blk["reason"] == "grid_product_over_budget"
            assert blk["a_max_db"] is None and blk["b_db"] is None
        if blk["status"] == "certified":
            assert blk["pi"] <= ns and blk["a_max_db"] is not None
    pin.finish_blocks(circuit, pinned_bad)                                 # 모든 단언을 돈 뒤 마지막에 xfail


@pytest.mark.parametrize("circuit", ["two_stage_ota", "two_stage_ota_sf"])
def test_second_stage_cs_grid_product_by_hand(env, circuit, tmp_path_factory):
    _, b = _run(env, circuit, tmp_path_factory)
    nL, nG, nD, nS = env["stats"]["axes"]
    blocks = {tuple(x["key"]): x for x in b.report["achievability"]["gain"]["blocks"]}
    assert blocks[("OUT",)]["pi"] == nG ** 2 * nL ** 2 * nD ** 2
    assert sorted(blocks[("OUT",)]["members"]) == ["M6", "M7"]
    assert blocks[("OUT",)]["status"] == "unknown"


def test_output_follower_is_certified_with_raw_array_bound(env, tmp_path_factory):
    _, b = _run(env, "two_stage_ota_sf", tmp_path_factory)
    nL, nG, nD, nS = env["stats"]["axes"]
    blocks = {tuple(x["key"]): x for x in b.report["achievability"]["gain"]["blocks"]}
    fol = blocks[("vout",)]
    assert list(fol["members"]) == ["M8"]
    assert fol["pi"] == nG * nL * nD * nS
    assert fol["status"] == "certified"
    a_max, res = env["stats"]["follower"]
    assert fol["a_max_db"] == pytest.approx(a_max, abs=1e-12)
    assert fol["b_db"] == pytest.approx(res, abs=1e-12)
    assert fol["a_max_db"] <= 0.0                                          # 버퍼 블록 상한 ≤ 0 dB (41 4.2)


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_gain_target_and_verdict(env, circuit, tmp_path_factory):
    _, b = _run(env, circuit, tmp_path_factory)
    _pin_stop("test_gain_target_and_verdict", circuit, b, b.report["achievability"] is None)
    g = b.report["achievability"]["gain"]
    target = _gain_target(circuit)
    assert g["target_db"] == target
    unknown = [x for x in list(g["blocks"]) + list(g["ff"]) if x["status"] == "unknown"]
    if target is None:
        assert g["verdict"] == "no_target"
    elif unknown:
        assert g["verdict"] == "undetermined" and g["sum_db"] is None


# [O-196 2026-10-31] r2r_opamp: M21·M22(pmos)는 Ib5, M23·M24(nmos)는 Ib2 하나로 전류가 정해진다(회로 해석 -- 연결: n_abp·n_abn 에 전류원,
# 직렬 diode, 게이트만 닿는다. 사용자 "둘 다 그렇게 (Recommended)"). 소자·전류원 이름은 topology 연결에서 읽은 해석 표다.
_CURRENT_FED = {"current_reuse_telescopic_ota": {"M18_bg": ("pmos", "Iref")},
                "sf_pushpull_output_opamp": {"M4": ("nmos", "IBias")},
                "r2r_opamp": {"M21": ("pmos", "Ib5"), "M22": ("pmos", "Ib5"), "M23": ("nmos", "Ib2"), "M24": ("nmos", "Ib2")}}


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_area_lower_bound_from_declared_values(env, circuit, tmp_path_factory):
    _, b = _run(env, circuit, tmp_path_factory)
    _pin_stop("test_area_lower_bound_from_declared_values", circuit, b, b.report["achievability"] is None)
    area = b.report["achievability"]["area"]
    spec = _spec(circuit)["human"]
    ev = spec["element_values"]
    theta = spec["search"].get("theta_bounds", {})
    rho = env["pdk"].value("mim_cap_density_f_per_m2")
    want = {}
    for e in _topo(circuit).get("passive_elements", []):
        if e["kind"] != "capacitor":
            continue
        decl = ev.get(e["name"], {})
        if isinstance(decl, dict) and decl.get("measurement_load"):
            continue
        if isinstance(decl, dict) and "value_farad" in decl:
            want[e["name"]] = decl["value_farad"] / rho
        elif isinstance(theta.get(e["name"]), dict) and "min" in theta[e["name"]]:
            want[e["name"]] = theta[e["name"]]["min"] / rho
    st = env["stats"]
    for mos, (kind, src) in _CURRENT_FED.get(circuit, {}).items():
        want[mos] = ev[src]["value_dc_amp"] * st["l_min"][kind] ** 2 / st["idu_max"][kind]
    got = {k: v for k, v in area["terms"]}
    assert set(got) == set(want)
    for k in want:
        assert got[k] == pytest.approx(want[k], rel=1e-9), k
    assert area["a_lb_m2"] == pytest.approx(sum(want.values()), rel=1e-9)
    budget = [c["value"] for c in spec["constraints"] if c.get("metric") == "area_search_m2" and c.get("op") == "<="]
    assert area["budget_m2"] == (min(budget) if budget else None)


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_diagnostic_mode_keeps_stage_a_exit_code(env, circuit, tmp_path_factory):
    a, b = _run(env, circuit, tmp_path_factory)
    # [O-227 m1] 종료 코드 단언은 정지 고정 앞에서 항상 돈다(정지와 무관하게 잴 수 있다)
    if a.status != "ok":
        assert b.exit_code == a.exit_code, (a.status, b.status)
    else:
        assert b.exit_code in (0, 3)
    _pin_stop("test_diagnostic_mode_keeps_stage_a_exit_code", circuit, b,
              b.s1 is None or b.s1.snapshot.record("graph", "ach") is None)
    # [U17 ①-b] StageBResult.achievability 묶음 삭제 -> 결과 S0 수준 스냅샷의 graph/ach 레코드(설계 40 v1.9.1 §2.4.7·§2.4.8 GB4 행, D2)
    assert b.s1 is not None and b.s1.snapshot.record("graph", "ach") is not None    # 진단 모드: s1v 가 있으면 계산한다
