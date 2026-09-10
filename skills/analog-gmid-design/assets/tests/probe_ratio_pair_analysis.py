# -*- coding: utf-8 -*-
"""`ratio` 매칭 쌍이 **실제로 전류미러인지**, 그렇다면 사이징이 미러 규약을 지키는지
connectivity로 확인하는 조사 도구(2026-09-08, (나) 3쌍 공동분석용).

## 배경

`probe_matching_pair_divergence.py`가 갈리는 매칭 쌍 6개를 찾았고, 그중 동작점이 완전히
같은 3쌍(M2a/M2b, M3a/M3b, M37a/M37b)은 gm_id 전파로 고쳤다. 남은 3쌍은 ID/vds가 애초에
달라서 W가 달라도 정당할 수 있는 `ratio` 매칭이라 손대지 않았다:

    ['M18_bg','M8','M13','M17','M22','M60','M61']   ratio, current_forced=False
    ['M18_bg','M60','M61']                          ratio, current_forced=True
    ['M10','M12','M19','M21']                       ratio, current_forced=False

## 판정 기준 -- 전류미러의 물리

게이트와 소스를 공유하는 소자들은 **VGS가 KVL로 완전히 같다**. 그러면:

  - 같은 L에서 전류비는 **W비로 정해진다**:  ID_i / ID_j = W_i / W_j
  - gm_id는 VGS의 함수이므로 vds 차이만큼만 갈린다(채널길이변조) -- 크게 다를 수 없다

따라서 **게이트를 공유하는데 `ID비 != W비`이면 그 사이징은 미러로서 틀렸다.**
반대로 게이트를 공유하지 않으면 "미러"가 아니므로 이 잣대를 들이대면 안 된다.

이 스크립트는 그 두 가지를 실제 netlist로 확인만 한다 -- **고치지 않는다.**
`matching_sensitivity="ratio"`의 의도가 무엇인지는 회로 설계자의 판단이다.

## 측정 결과 (2026-09-08)

**세 그룹 모두 게이트와 소스를 공유하는 진짜 전류미러다**(순수 connectivity 사실):

    그룹 1,2  M18_bg/M8/M13/M17/M22/M60/M61  PMOS  gate=Vbias1  source=vdd
              (M18_bg는 gate=drain=Vbias1인 diode 레퍼런스)
    그룹 3    M10/M12/M19/M21                NMOS  gate=Vbias4  source=gnd

즉 각 그룹 안에서 **VGS가 KVL로 완전히 강제 동일**해야 한다. 그런데 사이징은:

    그룹 1  VGS  0.675 / 1.139 / 0.917 / 1.139 / 0.917 / 0.981 / 0.938 V
                 -> 최대 464mV 벌어져 있다
    그룹 3  VGS  0.714 / 0.573 / 0.714 / 0.573 V
                 -> 141mV 벌어져 있다

미러 규약(`ID_i/ID_j == W_i/W_j`)도 전부 깨진다:

    M8    ID비 15.0000  W비 0.0098   -> 1530배 어긋남
    M13   ID비  1.0000  W비 0.0120   ->   83배 어긋남
    M12   ID비  0.0667  W비 1.1667   ->   17배 어긋남

**따라서 이 3그룹은 "의도된 미러비"가 아니라 깨진 미러다.** 엔진이 각 소자를
`gm_id_role="matching"`으로 **독립 탐색**하고, 게이트가 물려 있다는 사실을 보지 않는다.
세션38이 M203/M204에서 발견해 `gm_id_match_vgs_of`를 만든 것과 **같은 클래스**인데,
이 소자들은 그 필드를 선언하지 않았다(M10은 `vds_match_vgs_of`만 있다).

## ⚠️ 고치면 무슨 일이 생기나 (미리 계산)

미러를 강제하면 6개 미러 소자가 레퍼런스 M18_bg의 VGS(0.675V)를 따라야 한다. 그런데
M18_bg는 W=103.02um인데(diode 자기일관 제약이 gm_id=21.36을 강제 -> 전류밀도가 낮아
W가 크다), 같은 VGS에서 15배 전류를 흘리는 M8/M17은 **W ~ 1545um**가 필요하다 --
`W_bounds` 상한 200um의 7.7배로 **불가능**하다.

즉 이 미러 그룹은 현재 동작점에서 원리적으로 성립하지 않는다. 원인을 거슬러 가면
M18_bg의 vds(0.675V)가 diode 구간의 **하한**이고, 그 하한이 낮을수록 VGS가 낮아
미러들이 감당 못 할 W를 요구한다. 고치려면 bias generator의 전류/L 자체를 다시
잡아야 한다 -- 이건 회로 설계 판단이라 사람이 결정해야 한다.

실행: assets 디렉터리에서 `python tests/probe_ratio_pair_analysis.py`
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

res = sr.optimize_full_circuit_budget(TOPO, SPEC, search_method="slsqp",
                                       slsqp_kwargs={"n_starts": 1, "maxiter": 40})
sized = res["sizing"]
trs, meta = sr.load_topology(TOPO)
by = {t.name: t for t in trs}
topo = json.load(open(TOPO, encoding="utf-8"))
pairs = (topo.get("symmetry") or {}).get("matching_pairs") or []
roles = topo.get("device_roles") or {}

TARGETS = [
    ["M18_bg", "M8", "M13", "M17", "M22", "M60", "M61"],
    ["M18_bg", "M60", "M61"],
    ["M10", "M12", "M19", "M21"],
]

for names in TARGETS:
    p = next((x for x in pairs if x.get("names") == names), None)
    emit()
    emit("=" * 92)
    emit("그룹 %s" % names)
    if p:
        emit("  선언: matching_sensitivity=%s, current_forced=%s"
             % (p.get("matching_sensitivity"), p.get("current_forced")))

    emit()
    emit("  [1] connectivity -- 게이트/소스를 공유하는가(공유하면 VGS가 KVL로 강제 동일)")
    emit("  %-8s %-6s %-14s %-14s %-14s %s"
         % ("소자", "kind", "gate", "source", "drain", "diode?"))
    emit("  " + "-" * 76)
    for n in names:
        t = by.get(n)
        if not t:
            emit("  %-8s (netlist에 없음)" % n)
            continue
        emit("  %-8s %-6s %-14s %-14s %-14s %s"
             % (n, t.kind, t.gate, t.source, t.drain,
                "diode" if sr.is_diode_connected(t) else ""))
    gates = {by[n].gate for n in names if n in by}
    srcs = {by[n].source for n in names if n in by}
    shared_g = len(gates) == 1
    shared_s = len(srcs) == 1
    emit("  -> 게이트 공유: %s (%s) / 소스 공유: %s (%s)"
         % ("예" if shared_g else "아니오", sorted(gates),
            "예" if shared_s else "아니오", sorted(srcs)))
    emit("  -> 이 그룹은 %s"
         % ("**전류미러**다(VGS 동일 강제)" if shared_g and shared_s
            else "게이트/소스를 모두 공유하진 않는다 -- 단순 미러 잣대를 그대로 대면 안 된다"))

    emit()
    emit("  [2] 사이징이 미러 규약(ID비 == W비)을 지키는가")
    ref = names[0]
    e0 = sized.get(ref) or {}
    emit("  %-8s %-11s %-11s %-11s %-11s %-9s %s"
         % ("소자", "ID(uA)", "W(um)", "ID비", "W비", "gm_id", "판정"))
    emit("  " + "-" * 84)
    for n in names:
        e = sized.get(n) or {}
        if not (e.get("ID") and e.get("W")):
            continue
        r_id = e["ID"] / e0["ID"]
        r_w = e["W"] / e0["W"]
        ok = abs(r_id - r_w) <= 0.05 * max(abs(r_id), 1.0)
        emit("  %-8s %-11.4f %-11.4f %-11.4f %-11.4f %-9.3f %s"
             % (n, e["ID"] * 1e6, e["W"] * 1e6, r_id, r_w, e.get("gm_id", float("nan")),
                "OK" if ok else "★어긋남"))

    emit()
    emit("  [3] VGS -- 게이트를 공유하면 이 값들이 같아야 한다")
    emit("  %-8s %-9s %-9s %-9s %s" % ("소자", "gm_id", "vds", "vsb", "VGS(V)"))
    emit("  " + "-" * 52)
    for n in names:
        e = sized.get(n) or {}
        if e.get("gm_id") is None:
            continue
        lut = SPEC["lut_by_kind"][e["kind"]]
        try:
            vgs = lut.vgs_for_gm_id(e["gm_id"], e["L"], e["vds"], e.get("vsb", 0.0))
        except ValueError:
            vgs = float("nan")
        emit("  %-8s %-9.3f %-9.4f %-9.4f %.4f"
             % (n, e["gm_id"], e["vds"], e.get("vsb", 0.0), vgs))

    emit()
    emit("  [4] 선언된 device_roles")
    for n in names:
        emit("     %-8s %s" % (n, json.dumps(
            {k: v for k, v in (roles.get(n) or {}).items() if not k.startswith("_")},
            ensure_ascii=False)))
