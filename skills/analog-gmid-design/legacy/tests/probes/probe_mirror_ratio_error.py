# -*- coding: utf-8 -*-
"""매칭 쌍의 VDS 차이가 만드는 **계통 전류 오차**를 재는 조사 도구(계획 §10.2 A4의 근거).

`mirror_ratio_error` metric(2026-09-08 신설)이 계산하는 것과 같은 양을 topology/instance
파일에서 직접 계산해 쌍별로 펼쳐 보여준다 -- metric은 max/rss 하나만 돌려주므로, 어느 쌍이
문제인지 보려면 이 스크립트가 필요하다.

배경: 검토자가 "VDS 재배분이 매칭 쌍을 깬다"고 지적했는데, 실측하니 절반은 이미 해결돼 있었다.
`matching_pairs`가 `offset`/`ratio`로 갈려 있고
  offset : 공유 tail KCL이 강제하는 진짜 대칭 -> 헤드룸 해석기가 _hr_vfind() union으로 이미
           VDS를 같게 강제한다(파일럿 실측: 3쌍 전부 dVDS=0)
  ratio  : 전류미러 -> 레퍼런스(diode, Vgs 고정)와 출력(부하 노드 전압)의 VDS가 **원래 다른
           것이 정상**이다. 같게 강제하면 회로가 성립하지 않는다.
따라서 ratio 쌍은 제약이 아니라 **비용**으로 다뤄야 하고, 그 비용을 재는 것이 이 도구다.

측정 결과(2026-09-08, current_reuse_telescopic_ota, matching_pairs 21개 = offset 3 / ratio 18):
  M18_bg/M60  dVDS=+1.300V  V_A=2.04V  ->  dI/I = +63.6%   (미러비가 설계값의 1.6배)
  M18_bg/M8   dVDS=+0.606V  V_A=2.04V  ->  dI/I = +29.7%
  M10/M12     dVDS=+0.744V  V_A=4.74V  ->  dI/I = +15.7%
  나머지 18쌍은 dVDS=0.

B1(diode 고정점)을 고치면 M18_bg의 vds가 0.200 -> 0.989V로 잡히지만 M18_bg/M60은 25.0%,
M10/M12는 15.7%(diode 무관)가 그대로 남는다 -- A4는 B1의 부수효과가 아니라 독립 문제다.

`pelgrom_mismatch`는 `estimate_mismatch_sigma(vth0_slope, W, L)`이라 vds도 V_A도 인자로 받지
않는다 -- 랜덤 성분만 보므로 이 계통 오차는 구조적으로 시야 밖이다.

실행: assets 디렉터리에서 `python tests/probe_mirror_ratio_error.py`
(자동 테스트가 아니라 조사용.)
"""
import os, sys, json
ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # probes -> tests -> assets
sys.path.insert(0, ASSETS)
import sizing_recipe as sr

TOPO = os.path.join(ASSETS, "..", "assets", "library", "current_reuse_telescopic_ota.topology.json")
INST = os.path.join(ASSETS, "workspaces", "current-reuse-telescopic-ota-report", "current_reuse_telescopic_ota.instance.json")
topo = json.load(open(TOPO, encoding="utf-8"))
sized = json.load(open(INST, encoding="utf-8"))["sizing"]
pairs = topo["symmetry"]["matching_pairs"]

print("matching_pairs %d개  (offset %d / ratio %d)"
      % (len(pairs),
         sum(1 for p in pairs if p.get("matching_sensitivity") == "offset"),
         sum(1 for p in pairs if p.get("matching_sensitivity") == "ratio")))
print()
print("%-16s %-8s %9s %9s %9s %10s %10s %9s" %
      ("쌍", "sens", "vds_a", "vds_b", "dVDS(V)", "V_A_a(V)", "V_A_b(V)", "dI/I(%)"))
print("-" * 96)

rows = []
for p in pairs:
    a, b = p["names"][0], p["names"][1] if len(p["names"]) > 1 else None
    if b is None:
        continue
    ea, eb = sized.get(a), sized.get(b)
    if not ea or not eb or ea.get("vds") is None or eb.get("vds") is None:
        continue
    sens = p.get("matching_sensitivity", "?")
    dv = eb["vds"] - ea["vds"]
    va = ea["ID"] / ea["gds"] if ea.get("gds") else float("nan")
    vb = eb["ID"] / eb["gds"] if eb.get("gds") else float("nan")
    # 1차: I ∝ (1 + VDS/V_A) 이므로 ΔI/I ≈ ΔVDS / V_A (같은 V_A 가정 시)
    di = (dv / va * 100.0) if va == va and va else float("nan")
    rows.append((a + "/" + b, sens, ea["vds"], eb["vds"], dv, va, vb, di))
    print("%-16s %-8s %9.4f %9.4f %+9.4f %10.2f %10.2f %+9.3f"
          % (a + "/" + b, sens, ea["vds"], eb["vds"], dv, va, vb, di))

print()
bad = [r for r in rows if abs(r[4]) > 1e-9]
print("VDS가 실제로 다른 쌍: %d / %d" % (len(bad), len(rows)))
for sens in ("offset", "ratio"):
    sub = [r for r in bad if r[1] == sens]
    if sub:
        worst = max(sub, key=lambda r: abs(r[7]))
        print("  %-7s 중 VDS 불일치 %2d쌍, 최대 |dI/I| = %.2f%% (%s, dVDS=%+.3fV)"
              % (sens, len(sub), abs(worst[7]), worst[0], worst[4]))
    else:
        print("  %-7s 중 VDS 불일치 0쌍" % sens)

print()
print("=== pelgrom_mismatch가 이 계통 오차를 보는가 ===")
import inspect
src = inspect.getsource(sr.estimate_mismatch_sigma)
print("  estimate_mismatch_sigma 인자:", inspect.signature(sr.estimate_mismatch_sigma))
print("  -> vds/V_A/ΔVDS 를 인자로 받지 않는다 =", "vds" not in src and "V_A" not in src)
print("  즉 랜덤 Vth 미스매치(σ ∝ 1/sqrt(WL))만 보고, VDS 차이가 만드는 **계통** 오차는")
print("  구조적으로 볼 수 없다. 이를 재는 metric은 _METRICS_REGISTRY에도 없다:")
print("   ", [k for k in sr._METRIC_UNITS if "offset" in k or "systematic" in k] or "없음")
