# -*- coding: utf-8 -*-
"""면적 예산을 바꿔가며 **달성 가능한 경계**를 재는 도구 (계획 §7.9 v3.4 Pareto fallback).

## 왜 필요한가

파일럿 `sizing_roles`는 `objective = minimize power_uA`이고 제약이 gain/mismatch/cmrr/
psrr/classab 5개인데, **`area_um2`는 metric으로 선언만 돼 있고 제약에 없다**. 그래서 탐색이
면적을 아예 보지 않고, B16 배선 후 실제 면적이 1050um^2(v3.3 예시 예산 200um^2의 5.3배)로
나왔다. 반면 `gain_db`는 75.4dB로 목표 54dB를 21dB나 넘긴다 -- **여유를 면적과 맞바꿀 수
있다**는 뜻이다.

그럼 면적 예산을 얼마로 걸어야 하나? **엔진도 나도 그 값을 지어내면 안 된다**(§3.2 P1,
v3.4). 대신 예산을 훑어 **어디까지 가능한지**를 재고, 그 표를 사람에게 준다.

## 무엇을 하나

`area_um2 <= cap` 제약을 임시 topology 사본에 추가해 cap을 바꿔가며 SLSQP를 돌린다.
각 cap에서 (성공 여부, 실제 면적, 전력, gain, 공급전류)를 기록한다. 원본
topology.json은 건드리지 않는다.

⚠️ **이 스크립트는 예산을 고르지 않는다.** 경계를 보여줄 뿐이고, 고르는 것은 사람 몫이다
(v3.4: "빠진 스펙 하나를 사람에게 받아오는 경로").

실행: assets 디렉터리에서 `python tests/probe_area_pareto.py`
결과는 `tests/probe_area_pareto.result.txt`에 케이스마다 append된다(오래 걸리므로
중간에 끊겨도 거기까지는 남는다).
"""
import sys
import os
import json
import tempfile
import time

ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "..", "..", "..", "workspaces"))
import numpy as np
import sizing_recipe as sr
import run_harness as H


# ---------------------------------------------------------------------------
# 결과는 **파일에도 남긴다**(사용자 지시, 2026-09-08).
# ---------------------------------------------------------------------------
_RESULT_PATH = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first_emit = [True]


def emit(*parts):
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

# 훑을 예산: 제약 없음(현재값 확인) + 1000부터 아래로. 값 자체는 "설계 목표"가 아니라
# **경계를 찾기 위한 탐침**이다 -- 어디서 실패로 바뀌는지가 이 스크립트의 산출물이다.
CAPS = [None, 1000.0, 900.0, 800.0, 700.0, 600.0, 500.0, 400.0, 300.0, 200.0]

emit("면적 예산을 바꿔가며 달성 가능한 경계 측정 (SLSQP 1 start, maxiter 40)")
emit("원본 topology.json은 수정하지 않는다 -- 임시 사본에 제약만 추가한다.")
emit()
emit("%-10s %-9s %-11s %-11s %-10s %-10s %s"
     % ("면적예산", "판정", "실제면적", "diode면적", "power_uA", "gain_db", "비고"))
emit("-" * 88)

trs, _meta = sr.load_topology(TOPO)
DIODE = {t.name for t in trs if sr.is_diode_connected(t)}
base = json.load(open(TOPO, encoding="utf-8"))

for cap in CAPS:
    topo = json.loads(json.dumps(base))
    if cap is not None:
        topo["sizing_roles"]["constraints"].append(
            {"metric": "area_um2", "op": "<=", "value": cap})
    t0 = time.time()
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "current_reuse_telescopic_ota.topology.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(topo, f)
        try:
            res = sr.optimize_full_circuit_budget(
                p, SPEC, search_method="slsqp",
                slsqp_kwargs={"n_starts": 1, "maxiter": 40})
        except Exception as e:
            emit("%-10s %-9s %-11s %-11s %-10s %-10s %s"
                 % ("제약없음" if cap is None else "%.0f" % cap, "실패", "-", "-", "-", "-",
                    "%s: %s" % (type(e).__name__, str(e)[:70])))
            continue
    s = res.get("sizing") or {}
    m = res.get("metrics") or {}
    ar = lambda names=None: sum(v["W"] * v["L"] for k, v in s.items()
                                 if v.get("W") and v.get("L")
                                 and (names is None or k in names))
    emit("%-10s %-9s %-11.2f %-11.2f %-10.2f %-10.2f %s"
         % ("제약없음" if cap is None else "%.0f" % cap, "성공",
            ar() * 1e12, ar(DIODE) * 1e12,
            m.get("power_uA", float("nan")), m.get("gain_db", float("nan")),
            "%.0fs" % (time.time() - t0)))

emit()
emit("판정: '실패'로 바뀌는 지점이 이 회로가 현재 구조에서 낼 수 있는 면적 하한이다.")
emit("이 스크립트는 예산을 고르지 않는다 -- 고르는 것은 사람 몫이다(계획 v3.4).")
