# -*- coding: utf-8 -*-
"""diode 구간의 **어느 끝을 고를지**가 면적/헤드룸에 얼마나 영향을 주는지 재는 도구.

B16 배선 후 `allocate_stack_headroom()`은 diode에게 구간 `[lo, hi]`의 **하한**을 준다.
근거는 "헤드룸이 더 희소한 자원"이라는 §7.9 판단이었는데, 배선하고 나서 재보니 그 선택의
대가가 컸다: 총 면적이 117 -> 1043um^2(8.9배)로 늘고 그중 diode가 9 -> 670um^2(74배)다.

`W(v)`가 감소함수이므로 lo는 W 최대(면적 큼), hi는 W 최소(면적 작음·헤드룸 많이 씀)다.
그럼 반대 끝은 성립하는가? 두 코너를 모두 돌려 비교한다 -- 이 표가 §7.9의 배분 탐색이
실제로 다뤄야 할 트레이드오프의 크기를 보여준다.

⚠️ 이 스크립트는 `allocate_stack_headroom()`/`_singleton_vds()`가 쓰는 선택 규칙을
monkeypatch로 바꿔 본다(엔진 기본값은 건드리지 않는다).

## 측정 결과 (2026-09-08, 7앵커 LUT, 파일럿 현재 L/ID)

    선택   총면적(um2)   diode(um2)   gain_db   supply_uA   판정
    lo     1042.93       669.75       68.2039   82.7210     OK
    mid    -             -            -         -           infeasible
                                        ('biasgen_vom_floatsrc_sink' 예산 음수)
    hi     -             -            -         -           infeasible
                                        ('biasgen_vom_battery_a' 그룹)

**하한이 유일하게 성립하는 코너다.** 구간의 절반만 올려도 스택 예산이 음수가 된다 --
즉 지금 사이징에서 diode 구간의 자유도는 **쓸 수 없다**(폭 0.19~0.41V가 있지만 스택이
그만큼 빡빡하다). 배분기가 하한을 고르는 것은 선호가 아니라 **강제**다.

따라서 총 면적 1043um^2(v3.3 예시 예산 200um^2의 5.2배)를 줄이려면 구간 안에서
미끄러지는 게 아니라 **L/ID를 바꿔야 한다** -- 정확히 §7.9 재탐색이 할 일이다.
이전 사이징의 117um^2는 물리적으로 불가능한 상태(M11a가 vds=0.2V에서 동작한다는
가정)의 면적이었으므로 비교 대상이 아니다.

실행: assets 디렉터리에서 `python tests/probe_diode_window_corner.py`
"""
import sys
import os
import json

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "..", "..", "..", "workspaces"))
import numpy as np
import sizing_recipe as sr
import run_harness as H


# ---------------------------------------------------------------------------
# 결과는 **파일에도 남긴다**(사용자 지시, 2026-09-08). stdout에만 쓰면
# `| grep | tail` 파이프가 백그라운드 전환 때 버퍼째 날아가, 계산은 성공했는데
# 결과만 잃는다(이 세션에서 실제로 두 번). 한 줄 쓸 때마다 append하므로 중간에
# 죽어도 거기까지는 건진다. 파일은 이 스크립트 옆에 `<이름>.result.txt`로 남는다.
# ---------------------------------------------------------------------------
_RESULT_PATH = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first_emit = [True]


def emit(*parts):
    """print와 같은 시그니처로 쓰되 파일에도 남긴다."""
    line = " ".join(str(p) for p in parts)
    print(line, flush=True)
    mode = "w" if _first_emit[0] else "a"
    _first_emit[0] = False
    with open(_RESULT_PATH, mode, encoding="utf-8") as _f:
        _f.write(line + "\n")



TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
d = np.load(os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz"))
mk = lambda k: sr.SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_" + k],
                                        d["GM_" + k], d["GDS_" + k], d["CGG_" + k],
                                        W_ref=5e-6, SID_1F=d["SID_1F_" + k])
nmos, pmos = mk("n"), mk("p")
# 2026-09-10 -- 손으로 복붙한 spec 블록을 폐기하고 **정본**을 쓴다. 복제본은 정본과
# 갈려 있었다(gm_id_grid 21점 vs 57점, L_candidates 12점 vs 41점, VDS_candidates 9점 vs
# 13점, stage_power_tolerance 누락). 같은 블록이 여러 파일에 그대로 퍼져 있었으므로
# 파일마다 다른 판단을 한 게 아니라 복제본 하나가 번진 것이다. 이제
# `sizing_recipe.require_declared_spec_source()`가 라이브러리 회로에 출처 선언을 강제하고,
# 일부러 다르게 쓸 때는 `H.derived_spec(key, why, **overrides)`로 무엇을 왜 바꿨는지 남긴다.
SPEC = H.canonical_spec("current_reuse_telescopic_ota")
nmos = SPEC["lut_by_kind"]["nmos"]
pmos = SPEC["lut_by_kind"]["pmos"]

trs, _meta = sr.load_topology(TOPO)
DIODE = {t.name for t in trs if sr.is_diode_connected(t)}

_orig_alloc = sr.allocate_stack_headroom
_orig_singleton_window = sr.diode_vds_window


def run(pick):
    """pick='lo'|'hi'|'mid' -- 구간 안 어디를 고를지 바꿔 돌린다."""
    def patched_window(lut, kind, L, ID, vsb, W_bounds):
        lo, hi = _orig_singleton_window(lut, kind, L, ID, vsb, W_bounds)
        if lo is None:
            return (None, None)
        v = {"lo": lo, "hi": hi, "mid": 0.5 * (lo + hi)}[pick]
        # 배분기는 항상 구간의 **하한**을 먼저 주므로, 하한을 원하는 지점으로 옮겨
        # 그 선택을 강제한다(상한은 그대로 둬서 남은 예산 흡수 여지는 유지).
        return (v, hi)
    sr.diode_vds_window = patched_window
    try:
        res = sr.optimize_full_circuit_budget(TOPO, SPEC, search_method="slsqp",
                                               slsqp_kwargs={"n_starts": 1, "maxiter": 40})
        return res, None
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, str(e)[:160])
    finally:
        sr.diode_vds_window = _orig_singleton_window


def area(s, names=None):
    return sum(v["W"] * v["L"] for k, v in s.items()
               if v.get("W") and v.get("L") and (names is None or k in names))


emit("diode 구간에서 어디를 고르느냐에 따른 결과 (SLSQP 1 start)")
emit()
emit("%-6s %-12s %-12s %-11s %-11s %s"
      % ("선택", "총면적(um2)", "diode(um2)", "gain_db", "supply_uA", "판정"))
emit("-" * 74)
for pick in ("lo", "mid", "hi"):
    res, err = run(pick)
    if err:
        emit("%-6s %-12s %-12s %-11s %-11s %s" % (pick, "-", "-", "-", "-", err))
        continue
    s = res.get("sizing") or {}
    m = res.get("metrics") or {}
    emit("%-6s %-12.2f %-12.2f %-11.4f %-11.4f %s"
          % (pick, area(s) * 1e12, area(s, DIODE) * 1e12,
             m.get("gain_db", float("nan")), m.get("supply_current_uA", float("nan")), "OK"))
