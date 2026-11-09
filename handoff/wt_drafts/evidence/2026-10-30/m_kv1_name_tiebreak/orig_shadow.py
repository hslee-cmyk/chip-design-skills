# 13회로 원문 설계점의 pfet 동작점(orig_ops/*.jsonl, 원문 판독 agent 산출)을 sky130 LUT r2 로 옮겨
# gm/ID 다가 구간(혹 띠) 해당 여부와 '가장 큰 VGS 해' 규칙이 다른 동작점을 고르는지 판정.
# 옮김 = 전류 밀도 IDu = I/(W·m) 와 L 보존(원문 공정 ≠ sky130 -- '원문 설계점 근처'의 뜻은 current_reuse rep 와 같음).
#   L: LUT L 격자 중 원문 L 이상인 첫 점(원문 L < 0.15 um 이면 0.15 -- sky130 최소 L, LUT 첫 격자). 상수 없음(격자가 정함).
#   VSB: 원문 값 있으면 그것, source 가 레일이면 0, 아니면 VSG 로 닫히지 않으므로 'vsb_unknown' -- VSB 격자 전부에서 판정해 범위로 보고.
#   VDS: 원문 VSD 있으면 그것, 다이오드는 VDS = VGS, 아니면 그 점 포화 조건(VDS ≥ VDSAT)을 만족하는 VDS 격자 전부에서 판정해 범위로 보고.
# 판정: 실제 VGS(= ln IDu 로 역산, 단조라 유일) 에서 max_{x'>x} g(x') >= g(x) 이면 shadowed(규칙이 다른 점을 고름).
# 결과 append: orig_shadow.jsonl
import json, math, pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import kv1_tiebreak as K

HERE = pathlib.Path(__file__).parent
OUT = HERE / "orig_shadow.jsonl"


def snap_L(L_um):
    g = K.LG * 1e6
    up = g[g >= L_um - 1e-9]
    return float((up[0] if len(up) else g[-1]) * 1e-6)


def judge(kind, L, iu, vds, vsb, diode):
    vgs = K.vgs_from_idu(kind, L, iu, vds, vsb, diode)
    if vgs is None:
        return None
    g, lid = K.curve(kind, L, vds, vsb, diode)
    p = int(np.argmax(g))
    v, gb = K.FINE[p:], g[p:]
    if vgs < v[0]:
        return dict(vgs=vgs, region="left_of_peak", shadowed=False)
    gx = float(np.interp(vgs, K.FINE, g))
    later = gb[v > vgs]
    sh = bool(len(later) and later.max() >= gx)
    picked = None
    if sh:
        d = gb - gx
        idx = np.where(d[:-1] * d[1:] <= 0)[0]
        i = int(idx[-1])
        picked = float(v[i] + (v[i + 1] - v[i]) * d[i] / (d[i] - d[i + 1])) if d[i] != d[i + 1] else float(v[i])
    return dict(vgs=vgs, g=gx, shadowed=sh, picked=picked, dvgs=None if picked is None else picked - vgs)


def main():
    if OUT.exists():
        OUT.unlink()
    for f in sorted((HERE / "orig_ops").glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            rec = dict(circuit=r.get("circuit"), dev=r.get("dev"), status=r.get("status"))
            W, L, I, m = r.get("W_um"), r.get("L_um"), r.get("I_A"), r.get("m") or 1
            if not (W and L and I) or r.get("status") == "missing":
                rec.update(result="no_data")
                append(rec); continue
            iu = abs(I) / (W * 1e-6 * m)
            Ls = snap_L(L)
            diode = bool(r.get("is_diode"))
            vsb = r.get("VSB_V")
            if vsb is None and r.get("source_is_rail"):
                vsb = 0.0
            vsbs = [float(vsb)] if vsb is not None else [float(x) for x in K.VS]
            if any(not (K.VS[0] <= x <= K.VS[-1]) for x in vsbs):     # 원문 판독 VSB 가 LUT 축 밖(예: -0.02 V) -> 판정 안 함, 기록만
                rec.update(result="vsb_off_lut_axis", vsb=vsbs)
                append(rec); continue
            res = []
            for vb in vsbs:
                if diode:
                    vdss = [None]
                elif r.get("VSD_V") is not None:
                    vdss = [abs(float(r["VSD_V"]))]
                else:
                    vdss = [float(x) for x in K.VD if x > 0]
                for vd in vdss:
                    j = judge("p", Ls, iu, vd, vb, diode)
                    if j is None:
                        continue
                    if not diode and r.get("VSD_V") is None:
                        if vd < K.vdsat("p", Ls, j["vgs"], vd, vb):
                            continue          # 포화 아닌 VDS 는 제외
                    res.append(dict(vsb=vb, vds=vd, **j))
            n = len(res); ns = sum(x["shadowed"] for x in res)
            rec.update(IDu=iu, L_lut=Ls, n_cases=n, n_shadowed=ns,
                       verdict=("all" if n and ns == n else "some" if ns else "none") if n else "no_case",
                       g_range=[min(x.get("g", np.nan) for x in res), max(x.get("g", np.nan) for x in res)] if n else None,
                       dvgs_max=max((x["dvgs"] or 0) for x in res) if n else None,
                       exact=(len(vsbs) == 1 and (diode or r.get("VSD_V") is not None)))
            append(rec)


def append(o):
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(o, default=float) + "\n")


if __name__ == "__main__":
    main()
