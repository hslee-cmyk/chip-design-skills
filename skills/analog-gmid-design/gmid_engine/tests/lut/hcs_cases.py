"""[card 20261104-hcs] lut test 공용 입력 -- r4 합성 LUT(sizing conftest 해석식)에서 VDSAT 열만 바꾼 LUT 를 쓴다.

피검 함수(sat_threshold·sat_threshold_grid·derived)를 부르지 않는다. 입력 생성과 npz 직접 읽기만 둔다.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from gmid_engine.lut import LutMemo, load_lut_set

from sizing.conftest import DEVICE_OF, R4_GRIDS, SUFFIX, TOY_SPEC, W_M, _sha, r4_arrays

KINDS = ("nmos", "pmos")


class LutCalls:
    """모든 gmid_engine 모듈의 지정 이름(기본 `vdsat`·`tol_vdsat_table`·`sat_threshold`)을 계수 래퍼로 바꾼다 -- 호출 수 단언용.
    monkeypatch fixture 로 되돌린다. 이름이 모듈에 없으면(아직 없는 심볼) 건드리지 않는다."""

    def __init__(self, monkeypatch, names=("vdsat", "tol_vdsat_table", "sat_threshold")):
        import sys
        self.n = {name: 0 for name in names}
        for modname, mod in list(sys.modules.items()):
            if not modname.startswith("gmid_engine") or mod is None:
                continue
            for name in self.n:
                real = getattr(mod, name, None)
                if callable(real) and not isinstance(real, type) and getattr(real, "__module__", "").startswith("gmid_engine"):
                    monkeypatch.setattr(mod, name, self._wrap(name, real))

    def _wrap(self, name, real):
        def counting(*a, **k):
            self.n[name] += 1
            return real(*a, **k)
        return counting


def memo_of(lut, n=4096):
    return LutMemo(lut, point=n, curve=n, root=n)


def lookups(memo):
    """memo 영역별 (hits, misses, size) -- 조회가 있었는지 보는 값(LUT 조회 0 = 전후 같음)."""
    return {k: (v.hits, v.misses, v.size) for k, v in memo.stats()}


def write_lut_with_vdsat(root: Path, vdsat_of, grids=R4_GRIDS):
    """r4 LUT 와 같은 식이되 VDSAT 열 = vdsat_of(kind, arrays) -> 배열(ID 와 같은 모양). -> LutSet."""
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for kind in KINDS:
        a = r4_arrays(kind, vdsat=False, grids=grids)
        a["VDSAT"] = np.asarray(vdsat_of(kind, a), dtype=float) + np.zeros(a["ID"].shape)
        p = root / ("h_%s.npz" % kind)
        np.savez(p, **a)
        entries.append({"device": DEVICE_OF[kind], "file": p.name, "sha256": _sha(p)})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    gL, gG, gD, gS = (np.asarray(g, dtype=float) for g in grids)
    shp = (len(gL), len(gG), len(gD), len(gS))
    cap = {"L": gL, "VGS": gG, "VDS": gD, "VS": gS, "w_ref_m": np.float64(W_M), "corner": np.str_("tt"),
           "temp_c": np.float64(27.0)}
    for kind in KINDS:
        cap["CGG" + SUFFIX[kind]] = np.full(shp, 1e-15)
        cap["CGD" + SUFFIX[kind]] = np.full(shp, 2e-16)
    np.savez(root / "cap.npz", **cap)
    from toy_bins import retrofit_bins as _retro
    _tb = _retro(root)
    return load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), TOY_SPEC, bin_rule=_tb.bin_rule, pdk_root=_tb.pdk_root)

