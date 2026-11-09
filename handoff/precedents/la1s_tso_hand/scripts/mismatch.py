"""Pelgrom σ_VT 손계산 -- 모델 카드가 그 (L, w_s) bin 에서 쓰는 vth0 slope 이름을 찾아 mismatch 파일 값으로 σ = slope/sqrt(W·L·mult)
(PDK scale 1u 아래 µm 단위, 선언 mismatch_slope_geometry_unit_m). 값은 PDK 원본 파일에서만 읽는다."""
import json, math, re

DECL = json.load(open("C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/sky130_pdk_decl.json", encoding="utf-8"))
ROOT = DECL["pdk_root"]
_bins = {}
_slopes = {}
CELL = {"nmos": ("nfet_01v8_tt_model_card", "nfet_01v8_mismatch_slopes"), "pmos": ("pfet_01v8_tt_model_card", "pfet_01v8_mismatch_slopes")}


def _load(kind):
    if kind in _bins:
        return
    card = DECL["sources"][CELL[kind][0]]
    txt = open(ROOT + "/" + card["path"], encoding="utf-8", errors="replace").read()
    bins = []
    for m in re.finditer(r"^\.model\s+(\S+)\s+[np]mos\b(.*?)(?=^\.model|^\.ends|\Z)", txt, re.S | re.M | re.I):
        body = m.group(2)
        g = {k: float(re.search(r"\b%s\s*=\s*([-+0-9.eE]+)" % k, body).group(1)) for k in ("lmin", "lmax", "wmin", "wmax")}
        sm = re.search(r"vth0\s*=\s*\{[^}]*?(\w+__vth0_slope\w*)\s*/\s*sqrt", body)
        g["slope"] = sm.group(1) if sm else None
        bins.append(g)
    _bins[kind] = bins
    ms = DECL["sources"][CELL[kind][1]]
    sl = {}
    for line in open(ROOT + "/" + ms["path"], encoding="utf-8", errors="replace"):
        mm = re.match(r"^\.param\s+(\S+)\s*=\s*([-+0-9.eE]+)", line.strip())
        if mm:
            sl[mm.group(1)] = float(mm.group(2))
    _slopes[kind] = sl


def sigma_vt(kind, L, w_s, m):
    """손가락 m 개(각 w_s) 소자의 σ_VT [V]. bin 은 (L, w_s) 로 고른다(경계는 아래 bin -- LUT meta 와 같은 규약)."""
    _load(kind)
    cand = [b for b in _bins[kind] if b["lmin"] <= L * (1 + 1e-9) and L <= b["lmax"] * (1 + 1e-9)
            and b["wmin"] <= w_s * (1 + 1e-9) and w_s <= b["wmax"] * (1 + 1e-9)]
    if not cand:
        raise ValueError("bin 없음 %s L=%g w=%g" % (kind, L, w_s))
    b = sorted(cand, key=lambda b: (b["lmax"], b["wmax"]))[0]
    slope = _slopes[kind][b["slope"]]
    unit = 1e-6  # mismatch_slope_geometry_unit_m (scale=1.0u)
    return slope / math.sqrt((L / unit) * (w_s / unit) * m), b["slope"]


def offset_excess(gm1, gm3, s1, s3):
    """입력환산 offset 의 부하 몫 / 입력쌍 몫 -- excess = sqrt(1 + (gm3·σ3)² / (gm1·σ1)²) (쌍 둘씩 같은 꼴이라 2 는 약분)."""
    return math.sqrt(1 + (gm3 * s3) ** 2 / (gm1 * s1) ** 2)
