# O-200 Q5 측정 2 -- pmos w_key 1000 꼬리 셀(앵커 2개 bin L 0.15/0.18 µm 의 중점 외부 값, 최대 32.5 mV @ VDS 1.8 V)에 엔진 평가 점이 닿는지,
# 그리고 닿을 때 그 점 자신의 L 방향 보간 오차가 얼마인지(셀 최댓값 구성 대 점 국소 값). 입력 q5_engine_rows.jsonl(find_front 평가 행),
# LUT 슬라이스 W5p0000um pfet·검증 중점 파일(resolve_lut_location, sha256 대조). 산출 q5_tail_reach.txt.
import os, sys, json, pathlib, bisect
import numpy as np
sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
from gmid_engine.lut import resolve_lut_location
LOC = resolve_lut_location(str(ENG / "assets/lut_v2_location.json"), os.environ)
HERE = pathlib.Path(__file__).parent
ROOT = pathlib.Path(LOC.manifest_path).parent
z = np.load(ROOT / "sky130_fd_pr__pfet_01v8__tt__W5p0000um_dc.npz", allow_pickle=True)
M = np.load(LOC.midpoints_path, allow_pickle=True)
L, VG, VD, VS = (np.asarray(z[k], float) for k in ("L", "VGS", "VDS", "VS"))
V = np.asarray(z["VDSAT"], float)
Lm = np.asarray(M["L"], float); Vm = np.asarray(M["VDSAT_p"], float)
cells = [json.loads(l) for l in (HERE / "q5_tolvdsat_indep.jsonl").read_text(encoding="utf-8").splitlines()]
rows = [json.loads(l) for l in (HERE / "q5_engine_rows.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
pm = [r for r in rows if r.get("kind") == "pmos" and r.get("tol") is not None]
i0, i1 = 0, 1                      # 앵커 0.15·0.18 µm (같은 PDK bin, 생성기 메타 model_bin_per_L)
m = int(np.argmin(np.abs(Lm - 0.165e-6))); t = (Lm[m] - L[i0]) / (L[i1] - L[i0])
ERR = np.abs(V[i0] + t * (V[i1] - V[i0]) - Vm[m])          # 중점 L 에서 [VGS, VDS, VS] 점별 L 선형 보간 오차
out = []
nb = lambda g, x: int(np.argmin(np.abs(g - x)))
in_tail = [r for r in pm if L[i0] - 1e-15 <= r["L"] <= L[i1] + 1e-15]
exact = [r for r in in_tail if min(abs(r["L"] - L[i0]), abs(r["L"] - L[i1])) <= 1e-15]
out.append(f"pmos 평가 행 {len(pm)}; L 이 [0.15, 0.18] µm(꼬리 bin) 안 {len(in_tail)}; 그중 앵커와 정확히 같은 L {len(exact)}; L 분포 µm {sorted({round(r['L']*1e6, 4) for r in pm})}")
vds = np.array([r["vds"] for r in in_tail]); tol = np.array([r["tol"] for r in in_tail]) * 1e3
out.append(f"꼬리 bin 행 VDS {vds.min():.3f}~{vds.max():.3f} V (꼬리 최댓값 셀 VDS 칸 = 1.7625~1.8 V; 닿은 행 {int((vds >= 1.7625).sum())}); 행 tol mV min {tol.min():.3f} med {np.median(tol):.3f} max {tol.max():.3f}")
loc = []
for r in in_tail:
    gi, ki, si = nb(VG, r["vgs"]), nb(VD, r["vds"]), nb(VS, r["vsb"])
    local_mid = float(ERR[gi, ki, si])
    at_anchor = min(abs(r["L"] - L[i0]), abs(r["L"] - L[i1])) <= 1e-15
    loc.append((r["tol"], 0.0 if at_anchor else local_mid, local_mid, r))
lt = np.array([x[1] for x in loc]) * 1e3; lm = np.array([x[2] for x in loc]) * 1e3
out.append(f"점 국소 L 방향 오차(앵커 L 이면 0 -- 앵커 조회는 L 보간이 없다; 아니면 그 점 최근접 격자 (VGS,VDS,VS)의 중점 오차) mV: med {np.median(lt):.4f} max {lt.max():.4f}")
out.append(f"같은 최근접 격자점의 중점 오차(앵커 여부 무시) mV: med {np.median(lm):.4f} max {lm.max():.4f}; 행 tol / 그 값 med {np.median(tol / np.maximum(lm, 1e-9)):.1f}")
k = np.unravel_index(np.argmax(ERR), ERR.shape)
out.append(f"꼬리 bin 중점 오차 최댓값 {ERR[k]*1e3:.3f} mV @ VGS {VG[k[0]]:.4f} VDS {VD[k[1]]:.4f} VS {VS[k[2]]:.1f} (VDSAT 앵커 0.15 {V[i0][k]:.4f} / 0.18 {V[i1][k]:.4f} / 중점 {Vm[m][k]:.4f})")
for vs_i in (0, len(VS) - 1):
    sl = ERR[:, :, vs_i]
    kk = np.unravel_index(np.argmax(sl), sl.shape)
    out.append(f"  VS {VS[vs_i]:.1f} 단면 최댓값 {sl[kk]*1e3:.3f} mV @ VGS {VG[kk[0]]:.4f} VDS {VD[kk[1]]:.4f}")
out.append("tol 상위 행:")
for x in sorted(loc, key=lambda x: -x[0])[:6]:
    r = x[3]
    out.append(f"  {r['circuit']} {r['device']} L {r['L']*1e6:.4f} VGS {r['vgs']:.4f} VDS {r['vds']:.4f} VSB {r['vsb']:.4f} tol {r['tol']*1e3:.3f} mV 국소 {x[1]*1e3:.4f} mV 여유 {r['slack0']*1e3:.1f} mV")
(HERE / "q5_tail_reach.txt").write_bytes(("\n".join(out) + "\n").encode("utf-8"))
