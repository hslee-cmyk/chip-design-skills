"""FS-1 M-1 손 oracle -- mismatch σ(L, vgs, vds, vsb; w_f, W) 를 엔진 함수 없이 LUT mismatch npz 원 열 + PDK 모델 카드·mismatch slope 원본으로 손 계산한다
(interface card 20261107-fs1 §3.4 M-1 절차 4·5). 엔진 함수(`mismatch_sigma_vgs`·`_sigma_vgs`·`_l_lower`·`matching_bounds`)를 부르지 않는다.

oracle (식): σ(L, vgs, vds, vsb; w_f, W) = √(Σ_k (D_k · s_k(w_f, L) / s_k^ref(L))²) · √(w_ref / W)  [V, 단일 소자]
- D_k = npz 열 `DVGS_<변수>_<접미사>`[L, VGS, VDS, VS] 의 L 축 index 에서 (VGS, VDS, VS) 3축 다중 선형 보간 (점 = (vgs, vds, vsb)).
- s_k^ref(L) = `meta_json` `slope_ref`[소자 키][L 의 µm 글자][변수]["value"] (None 이면 0.0).
- s_k(w_f, L) = PDK 모델 카드 `.model` 블록(lmin ≤ L ≤ lmax, wmin ≤ w_f ≤ wmax, 경계는 아래 블록)의 그 변수 식에 나오는 slope 식별자의 mismatch slope 원본 `.param` 값 (없으면 0.0).
PDK 이름 꼴은 `.param` 이름 집합(원본 파일)에서 읽는다 -- 규칙에 특정 PDK 이름을 쓰지 않는다 (O-197).
"""
import hashlib
import json
import math
import os
import re
from pathlib import Path

import numpy as np

SKILL = Path(__file__).resolve().parents[3]
LOC = json.loads((SKILL / "assets" / "lut_v2_location.json").read_text(encoding="utf-8"))
PDK_DECL = json.loads((SKILL / "assets" / "sky130_pdk_decl.json").read_text(encoding="utf-8"))


def sha256_of(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def lut_root():
    return Path(os.environ.get(LOC["root"]["env"], LOC["root"]["default"]))


def pdk_root():
    return Path(os.environ.get(LOC["pdk_root"]["env"], LOC["pdk_root"]["default"]))


def locate_pdk_file(rel):
    for base in (pdk_root(), pdk_root().parent):
        p = base / rel
        if p.is_file():
            return p
    raise FileNotFoundError(rel)


def load_mismatch_npz():
    """-> (npz 열 dict, meta dict). sha256 은 위치 선언 값과 먼저 대조한다."""
    spec = LOC["files"]["mismatch"]
    p = lut_root() / spec["path"]
    assert sha256_of(p) == spec["sha256"], "mismatch npz sha256 != 위치 선언"
    z = np.load(p, allow_pickle=False)
    cols = {k: z[k] for k in z.files if k != "meta_json"}
    return cols, json.loads(str(z["meta_json"]))


def _source(role_key):
    s = PDK_DECL["sources"][role_key]
    p = locate_pdk_file(s["path"])
    assert sha256_of(p) == s["sha256"], role_key
    return p


def _params(path):
    """`.param name = value` 줄 -> {name: float} (한 줄에 여러 개 가능, 값이 수식이면 건너뜀)."""
    out = {}
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^\.param\s+(.*)$", line.strip())
        if not m:
            continue
        for name, val in re.findall(r"([A-Za-z0-9_]+)\s*=\s*([-+0-9.eE]+)(?=\s|$)", m.group(1)):
            try:
                out[name] = float(val)
            except ValueError:
                pass
    return out


def model_blocks(card_path):
    """모델 카드 -> [{name, lmin, lmax, wmin, wmax, exprs{변수: 식 문자열}}]."""
    blocks, cur = [], None
    for line in Path(card_path).read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(".model"):
            cur = {"name": line.split()[1], "exprs": {}}
            blocks.append(cur)
            continue
        if cur is None or not line.startswith("+"):
            continue
        body = line[1:].strip()
        m = re.match(r"lmin\s*=\s*(\S+)\s+lmax\s*=\s*(\S+)\s+wmin\s*=\s*(\S+)\s+wmax\s*=\s*(\S+)", body)
        if m:
            cur.update(lmin=float(m.group(1)), lmax=float(m.group(2)), wmin=float(m.group(3)), wmax=float(m.group(4)))
            continue
        m = re.match(r"([A-Za-z0-9_]+)\s*=\s*(.*)$", body)
        if m:
            cur["exprs"][m.group(1)] = m.group(2)
    return [b for b in blocks if "lmin" in b]


def pick_block(blocks, L, w):
    """경계는 아래 블록: lmin ≤ L ≤ lmax·wmin ≤ w ≤ wmax 인 블록 가운데 (lmin, wmin) 사전식 최소 (L 이 경계면 lmin 이 작은 블록, W 가 경계면 wmin 이 작은 블록)."""
    tol = 1e-9
    cand = [b for b in blocks if b["lmin"] * (1 - tol) <= L <= b["lmax"] * (1 + tol) and b["wmin"] * (1 - tol) <= w <= b["wmax"] * (1 + tol)]
    assert cand, (L, w)
    return min(cand, key=lambda b: (b["lmin"], b["wmin"]))


class NfetSigma:
    """nmos 하나에 대한 손 σ. role_prefix = PDK 선언 sources 키 접두사 ('nfet_01v8' 같은 소자 키 -- LUT meta 의 소자 키와 같은 글자)."""

    def __init__(self, dev_key="nfet_01v8", suffix=None):
        self.cols, self.meta = load_mismatch_npz()
        self.dev = dev_key
        self.suffix = suffix or self.meta["column_suffix"][dev_key]
        self.variables = list(self.meta["variables"][dev_key])
        self.w_ref = float(self.cols["w_ref_m"])
        self.Ls = np.asarray(self.cols["L"], dtype=float)
        card = _source(dev_key + "_tt_model_card")
        self.blocks = model_blocks(card)
        self.slope_values = _params(_source(dev_key + "_mismatch_slopes"))
        self.slope_names = set(self.slope_values)

    # --- 모델 카드 쪽
    def slope(self, var, L, w_f):
        b = pick_block(self.blocks, L, w_f)
        expr = b["exprs"].get(var, "")
        ids = [t for t in re.findall(r"[A-Za-z0-9_]+", expr) if t in self.slope_names]
        if not ids:
            return 0.0, None, b["name"]
        assert len(ids) == 1, (var, ids)
        return self.slope_values[ids[0]], ids[0], b["name"]

    def slope_ref(self, var, L):
        keys = [k for k in self.meta["slope_ref"][self.dev] if math.isclose(float(k) * 1e-6, L, rel_tol=1e-9)]
        assert len(keys) == 1, (L, keys)
        item = self.meta["slope_ref"][self.dev][keys[0]][var]
        return 0.0 if item is None else float(item["value"])

    # --- npz 쪽
    def l_index(self, L):
        i = [k for k, v in enumerate(self.Ls) if math.isclose(v, L, rel_tol=1e-12)]
        assert len(i) == 1, ("L 이 앵커가 아니다 -- 멈추고 보고", L)
        return i[0]

    def d_k(self, var, L, vgs, vds, vsb):
        """3축 다중 선형 보간. 가중치 > 0 인 모서리에 NaN 이 있으면 None (손값 없음 -- 멈추고 보고)."""
        li = self.l_index(L)
        arr = np.asarray(self.cols["DVGS_%s%s" % (var, self.suffix)], dtype=float)[li]
        axes = [np.asarray(self.cols[n], dtype=float) for n in ("VGS", "VDS", "VS")]
        pts = (vgs, vds, vsb)
        idx, frac = [], []
        for ax, x in zip(axes, pts):
            assert ax[0] <= x <= ax[-1], ("축 밖", x)
            j = int(np.searchsorted(ax, x, side="right")) - 1
            j = min(max(j, 0), len(ax) - 2)
            idx.append(j)
            frac.append((x - ax[j]) / (ax[j + 1] - ax[j]))
        total = 0.0
        for corner in range(8):
            w, pos = 1.0, []
            for a in range(3):
                bit = (corner >> a) & 1
                w *= frac[a] if bit else 1.0 - frac[a]
                pos.append(idx[a] + bit)
            if w <= 0.0:
                continue
            v = arr[tuple(pos)]
            if not np.isfinite(v):
                return None
            total += w * float(v)
        return total

    def sigma(self, L, vgs, vds, vsb, w_f, W):
        """-> (σ [V], 변수별 상세) 또는 (None, 사유) -- 손값 없음이면 호출자가 멈추고 보고한다."""
        acc, detail = 0.0, []
        for var in self.variables:
            s, ident, blk = self.slope(var, L, w_f)
            sref = self.slope_ref(var, L)
            if sref == 0.0 and s != 0.0:
                return None, ("slope_ref_zero_but_slope_nonzero", var, L)
            d = self.d_k(var, L, vgs, vds, vsb)
            if d is None:
                return None, ("nan_corner", var, L)
            ratio = 0.0 if (sref == 0.0 and s == 0.0) else s / sref
            acc += (d * ratio) ** 2
            detail.append((var, ident, blk))
        return math.sqrt(acc) * math.sqrt(self.w_ref / W), detail


def check_bin_rule_against_evidence(sig):
    """`lut_v2_bin_rule.json` evidence.points 의 nfet 점마다 손 선택 블록 이름 == chosen_bin (판정 꼴을 먼저 대조 -- 인터페이스 M-1 4)."""
    rule = json.loads((SKILL / "assets" / "lut_v2_bin_rule.json").read_text(encoding="utf-8"))
    n = 0
    for pt in rule["evidence"]["points"]:
        if "nfet_01v8" not in pt["chosen_bin"]:
            continue
        got = pick_block(sig.blocks, pt["L"], pt["W"])["name"]
        assert got == pt["chosen_bin"], (pt, got)
        n += 1
    assert n >= 10
    return n


def nmos_slice_widths_m():
    """LUT 위치 선언 `files.manifest` (엔진 밖 자료) 의 nmos 소자 슬라이스 폭 [m] 오름차순."""
    spec = LOC["files"]["manifest"]
    p = lut_root() / spec["path"]
    assert sha256_of(p) == spec["sha256"], "manifest sha256 != 위치 선언"
    rows = json.loads(p.read_text(encoding="utf-8"))["slices"]
    return sorted(float(r["w_um"]) * 1e-6 for r in rows if r["device"] == "nfet_01v8")


def pick_anchor(sig, args_by_L, w_min_finger):
    """M-1 절차 5·6: 실행 A 의 앵커별 4단계 호출 인자 args_by_L = {L: {vgs, vds, vsb, W}} 로 (k, w_alt, σ_share) 를 손으로 고른다.
    -> dict(k_L, prev_L, w_alt, sigma_share, s_alt_k, s_ref_k, s_ref_prev, premise) 또는 None (전제 P2·P3 를 만족하는 앵커가 없음).
    손값이 없는 앵커(NaN 모서리·slope 비 정의 불가)를 만나면 AssertionError('멈추고 보고')."""
    Ls = sorted(args_by_L)
    w_ref = sig.w_ref
    widths = [w for w in nmos_slice_widths_m() if w >= w_min_finger * (1 - 1e-9)]

    def s_of(L, w_f):
        a = args_by_L[L]
        out, detail = sig.sigma(L, a["vgs"], a["vds"], a["vsb"], w_f, a["W"])
        assert out is not None, ("손값 없음 -- 멈추고 보고", L, detail)
        return math.sqrt(2.0) * out        # 쌍 s(L) = √2·σ (interface §3.4 단계 4, DEC-23 A_eff: DVGS 열은 소자 하나의 1σ 섭동 -- A-196 m1-pair-sigma)
    s_ref = {L: s_of(L, w_ref) for L in Ls}
    for k in range(1, len(Ls)):
        Lk, Lp = Ls[k], Ls[k - 1]
        if pick_block(sig.blocks, Lp, w_ref)["name"] == pick_block(sig.blocks, Lk, w_ref)["name"]:
            continue                                                         # L bin 이 서로 달라야 한다
        if not s_ref[Lp] > s_ref[Lk]:
            continue
        share = (s_ref[Lp] + s_ref[Lk]) / 2.0
        if not all(s_ref[L] > share for L in Ls[:k - 1]):
            continue                                                         # P3
        blk_ref = sig.slope("vth0", Lk, w_ref)[1]
        for w_alt in widths:
            if w_alt == w_ref or sig.slope("vth0", Lk, w_alt)[1] == blk_ref:
                continue                                                     # L_k bin 에서 slope 블록이 w_ref 와 달라야 한다
            s_alt = s_of(Lk, w_alt)
            if s_alt > share:                                                # P2
                return dict(k_L=Lk, prev_L=Lp, w_alt=w_alt, sigma_share=share, s_alt_k=s_alt, s_ref_k=s_ref[Lk], s_ref_prev=s_ref[Lp])
    return None
