"""`vdsat` -- CONTRACT 4.3 [r6]: 열 = column_source(..., "VDSAT")(4.3 출처 규칙), L 위치 = 4.0(출처 표의 L 축·bin 지도),
축 검사 = 출처 표의 VGS·VDS·VS(context kind, table = 출처 origin, w_key), 값 = 4.0 의 L 장에서 **모든 축 선형(값 공간)**.
memo point 키 (kind, w_key, lo, hi, L 값, vgs, vds, vsb). 실패 = lut_column_unavailable(memo 에 저장 안 됨)·4.0·4.1 사유.
격자점에서는 저장값 그대로.

기대값: toy 는 손으로 정한 식(7.1 r6 표 0.15, 중점 toy 의 닫힌 식), 실데이터는 npz 직접 + 독립 선형 보간(conftest lin_point_ref),
ngspice .dc 재실행(@m[vdsat], 슬라이스 생성기와 같은 소자·기하)으로 격자점 값 확인.
"""
import json
import math
import os
import re
import subprocess

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import vdsat

from .conftest import (BIN_L, TOY_VGS, detail_of, l_weights, lin_point_ref, mid_toy_arrays, mid_vdsat, new_memo,
                       r6_toy_cap_arrays, rel_close, toy_slice_arrays)

BIN_AB = (0, 0, 0, 1, 1, 3, 3, 4)                    # conftest 머리 표: 폭 1e-6 슬라이스 anchor_bin(손계산)


def _slices_with_vdsat(V):
    a = toy_slice_arrays(1e-6, 1.0)
    a["VDSAT"] = V
    return [("toy_w100.npz", "toyn", a), ("toy_w200.npz", "toyn", toy_slice_arrays(2e-6, 2.0))]


def test_contract_toy_r6_row(toy_build):
    """7.1 r6: VDSAT_n = 0.1 + 0.2·VGS (기준 LUT) -> vdsat(nmos, 100, 1e-6, 0.25, 0.75, 0.25) = 0.15 (선형 정확)."""
    m = new_memo(toy_build("r6v", cap=r6_toy_cap_arrays()).load())
    assert rel_close(vdsat(m, "nmos", 100, 1e-6, 0.25, 0.75, 0.25), 0.15, 1e-12)
    # 격자점 = 저장값 그대로
    assert vdsat(m, "nmos", 100, 2e-6, 0.5, 1.0, 0.5) == 0.1 + 0.2 * 0.5


def test_contract_toy_r6_unavailable(toy_memo):
    """7.1 r6 표: 선택 열 없는 r5 toy -> lut_column_unavailable, detail column VDSAT, kind nmos, w_key 100, cap_w_key 100,
    slice_columns (), cap_columns (). 실패한 조회는 memo 에 저장되지 않는다."""
    for _ in range(2):
        with pytest.raises(SealViolationError) as ei:
            vdsat(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.0)
        det = detail_of(ei.value)
        assert det["reason"] == "lut_column_unavailable"
        assert (det["column"], det["kind"], det["w_key"], det["cap_w_key"]) == ("VDSAT", "nmos", 100, 100)
        assert tuple(det["slice_columns"]) == () and tuple(det["cap_columns"]) == ()
    st = dict(toy_memo.stats())["point"]
    assert st.hits == 0


def test_linear_value_space_not_hermite_or_log(toy_build):
    """모든 축 선형(값 공간): 슬라이스 VDSAT = 0.1 + 0.2·VGS² 이면 VGS 칸 중앙 값 = 이웃 마디 평균(0.1 + 0.2·0.125), 참 함수값
    (0.1 + 0.2·0.0625)이나 로그 공간 평균(기하 평균)과 다르다(판별)."""
    V = np.empty((3, 3, 2, 2))
    V[...] = (0.1 + 0.2 * np.asarray(TOY_VGS) ** 2)[None, :, None, None]
    m = new_memo(toy_build("lin", slices=_slices_with_vdsat(V)).load())
    got = vdsat(m, "nmos", 100, 1e-6, 0.25, 0.5, 0.0)
    assert rel_close(got, 0.125, 1e-12)
    assert not rel_close(got, 0.1125, 1e-6) and not rel_close(got, math.sqrt(0.1 * 0.15), 1e-6)


@pytest.mark.parametrize("pt", [(3e-6, 0.3, 0.6, 0.2), (3.5e-6, 0.3, 0.6, 0.2), (1.25e-6, 0.8, 0.9, 0.45),
                                (7.5e-6, 0.0, 1.0, 0.5), (1e-6, 1.0, 0.5, 0.0)])
def test_mid_toy_in_bin_closed_form(mid_toy_build, pt):
    """중점 toy 슬라이스 VDSAT = 0.1 + 0.2v + 0.05·Lu²·(1 + d): L 은 앵커 또는 같은 bin 두 장 선형(Lu² 의 선형 보간),
    다른 축은 정확(선형 식). 독립 lin_point_ref 와도 같다."""
    L, vgs, vds, vsb = pt
    m = new_memo(mid_toy_build("v%d" % int(L * 1e8)).load())
    got = vdsat(m, "nmos", 100, *pt)
    lw = l_weights(BIN_L, BIN_AB, L)
    Lu2 = sum(w * (BIN_L[i] / 1e-6) ** 2 for i, w in lw[0])
    assert rel_close(got, 0.1 + 0.2 * vgs + 0.05 * Lu2 * (1 + vds), 1e-12)
    z = mid_toy_arrays(1e-6, 1.0, {})
    grids = (tuple(BIN_L), tuple(z["VGS"]), tuple(z["VDS"]), tuple(z["VS"]))
    assert rel_close(got, lin_point_ref(grids, mid_vdsat(BIN_L), lw[0], vgs, vds, vsb), 1e-12)


@pytest.mark.parametrize("L,reason", [(2.5e-6, "lut_l_cross_bin"), (4.5e-6, "lut_l_bin_unbracketed"),
                                      (5.5e-6, "lut_l_outside_model_bins")])
def test_bin_rejections_with_origin_context(mid_toy_build, L, reason):
    m = new_memo(mid_toy_build("rj").load())
    with pytest.raises(SealViolationError) as ei:
        vdsat(m, "nmos", 100, L, 0.3, 0.6, 0.2)
    det = detail_of(ei.value)
    assert det["reason"] == reason and det["value"] == L
    assert det["kind"] == "nmos" and det["w_key"] == 100 and det["table"] == "slice"


def test_axis_out_of_range_context(toy_build):
    """4.1 축 검사 context = kind, table = 출처 origin, w_key (슬라이스 열 -> "slice", 기준 LUT 열 -> "cap_table")."""
    V = np.full((3, 3, 2, 2), 0.2)
    m = new_memo(toy_build("ax", slices=_slices_with_vdsat(V)).load())
    with pytest.raises(SealViolationError) as ei:
        vdsat(m, "nmos", 100, 1e-6, 0.5, 0.5, 0.6)
    det = detail_of(ei.value)
    assert (det["reason"], det["axis"], det["lo"], det["hi"]) == ("lut_axis_out_of_range", "VS", 0.0, 0.5)
    assert det["table"] == "slice" and det["kind"] == "nmos" and det["w_key"] == 100
    m2 = new_memo(toy_build("ax2", cap=r6_toy_cap_arrays(), empty_bins=True).load())
    with pytest.raises(SealViolationError) as ei:
        vdsat(m2, "nmos", 100, 1e-6, 1.2, 0.5, 0.0)
    det = detail_of(ei.value)
    assert det["axis"] == "VGS" and det["table"] == "cap_table" and det["w_key"] == 100
    with pytest.raises(SealViolationError) as ei:
        vdsat(m2, "nmos", 100, 1.5e-6, 0.5, 0.5, 0.0)                # 빈 bin 지도(r5 toy) -> 앵커만
    det = detail_of(ei.value)
    assert det["reason"] == "lut_l_not_anchor" and det["bins"] == "unavailable"


def test_memo_point_region_and_ulp_key(mid_toy_build):
    m = new_memo(mid_toy_build("memo").load())
    a = vdsat(m, "nmos", 100, 3e-6, 0.3, 0.6, 0.2)
    assert vdsat(m, "nmos", 100, 3e-6 + math.ulp(3e-6), 0.3, 0.6, 0.2) == a     # 앵커 1 ulp -> 같은 키(값 = 앵커 값)
    st = dict(m.stats())["point"]
    assert (st.misses, st.hits) == (1, 1)
    vdsat(m, "nmos", 100, 3.5e-6, 0.3, 0.6, 0.2)
    vdsat(m, "nmos", 100, 3.5e-6, 0.3, 0.6, 0.2)
    st = dict(m.stats())
    assert (st["point"].misses, st["point"].hits) == (2, 2)
    assert all(st[r].misses == 0 for r in ("curve", "root", "derived"))


# ---------------------------------------------------------------------------
# 실데이터 (LUT v2 -- 재생성 슬라이스, 출처 "slice")
# ---------------------------------------------------------------------------

@pytest.mark.lut_realdata
def test_real_grid_points_equal_npz(real_memo, raw_slice):
    rng = np.random.default_rng(17)
    for kind, wk in (("nmos", 72), ("nmos", 1000), ("pmos", 84), ("pmos", 1000)):
        z = raw_slice(kind, wk)
        for _ in range(25):
            iL, iG, k, s = (int(rng.integers(0, n)) for n in z["VDSAT"].shape)
            got = vdsat(real_memo, kind, wk, float(z["L"][iL]), float(z["VGS"][iG]), float(z["VDS"][k]), float(z["VS"][s]))
            assert got == float(z["VDSAT"][iL, iG, k, s]), (kind, wk, iL, iG, k, s)


@pytest.mark.lut_realdata
def test_real_offgrid_matches_independent_linear(real_memo, real_lut, raw_slice):
    rng = np.random.default_rng(19)
    for kind, wk in (("nmos", 1000), ("pmos", 84)):
        z = raw_slice(kind, wk)
        Lg = [float(x) for x in z["L"]]
        ab = tuple(real_lut.slice_map[(kind, wk)].l_bins.anchor_bin)
        grids = (tuple(Lg), tuple(float(x) for x in z["VGS"]), tuple(float(x) for x in z["VDS"]),
                 tuple(float(x) for x in z["VS"]))
        n = 0
        while n < 20:
            i = int(rng.integers(0, len(Lg) - 1))
            L = float(Lg[i] + rng.uniform(0.1, 0.9) * (Lg[i + 1] - Lg[i]))
            pos = l_weights(Lg, ab, L)
            vgs, vds, vsb = (float(rng.uniform(0.0, 1.8)) for _ in range(3))
            if pos is None:
                with pytest.raises(SealViolationError):
                    vdsat(real_memo, kind, wk, L, vgs, vds, vsb)
                continue
            exp = lin_point_ref(grids, z["VDSAT"], pos[0], vgs, vds, vsb)
            got = vdsat(real_memo, kind, wk, L, vgs, vds, vsb)
            assert rel_close(got, exp, 1e-12), (kind, wk, L, vgs, vds, vsb)
            n += 1


@pytest.mark.lut_realdata
@pytest.mark.parametrize("kind,wk,pt,val", [
    ("nmos", 1000, (1e-6, 0.9, 0.9, 0.0), 0.2557), ("nmos", 1000, (0.85e-6, 0.9, 0.9, 0.3), 0.2107),
    ("nmos", 72, (1e-6, 0.9, 0.9, 0.3), 0.2576), ("pmos", 84, (1e-6, 0.9, 0.9, 0.3), 0.0586)])
def test_real_contract_examples(real_memo, raw_slice, real_lut, kind, wk, pt, val):
    """CONTRACT 5.2 실측 예(4자리): 값은 독립 선형 보간과 대조하고, 계약의 표기 자릿수 안에서 같다.
    [해석] pmos w_key 84 의 0.0586 V 는 nmos w_key 72 와 같은 인자(1 µm, 0.9, 0.9, 0.3)로 읽었다."""
    got = vdsat(real_memo, kind, wk, *pt)
    z = raw_slice(kind, wk)
    Lg = [float(x) for x in z["L"]]
    pos = l_weights(Lg, tuple(real_lut.slice_map[(kind, wk)].l_bins.anchor_bin), pt[0])
    grids = (tuple(Lg), tuple(float(x) for x in z["VGS"]), tuple(float(x) for x in z["VDS"]), tuple(float(x) for x in z["VS"]))
    assert rel_close(got, lin_point_ref(grids, z["VDSAT"], pos[0], *pt[1:]), 1e-12)
    assert abs(got - val) <= 0.5e-4, (got, val)


# --- ngspice: 같은 넷리스트(슬라이스 생성기와 같은 소자·기하·극성·바디 부호)로 격자점 @m[vdsat] 재실행 = LUT 열 ---------------

_NGSPICE = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
_DEV = {"nmos": ("nfet_01v8", +1, -1), "pmos": ("pfet_01v8", -1, +1)}


def _read_raw(path):
    b = open(path, "rb").read()
    i = b.index(b"Binary:\n")
    hdr = b[:i].decode("latin1").splitlines()
    nv = npt = None
    names, invars = [], False
    for ln in hdr:
        if ln.startswith("No. Variables:"):
            nv = int(ln.split(":")[1])
        elif ln.startswith("No. Points:"):
            npt = int(ln.split(":")[1])
        elif ln.startswith("Variables:"):
            invars = True
        elif invars and ln.strip():
            names.append(ln.split()[1])
    a = np.frombuffer(b[i + 8:], dtype="<f8", count=nv * npt).reshape(npt, nv)
    out = {}
    for k, n in enumerate(names):
        mm = re.search(r"\[(\w+)\]", n)
        out[mm.group(1) if mm else n] = a[:, k]
    return out


@pytest.mark.lut_realdata
@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_ngspice_grid_vdsat_equals_lut(raw_slice, tmp_path, kind):
    """슬라이스 (kind, 1000), L 앵커 1 µm, VS index 0·3: VGS·VDS 격자 dc 스윕의 @m[vdsat] 크기 = LUT VDSAT 열(정의 통일 DEC-88 --
    오라클과 같은 양). 허용 = 슬라이스 생성기 기록과 같은 시뮬레이터·같은 점이라 비트 동일(계약 4.4 결정 B 검증 '기존 열 비트 동일')."""
    exe = os.environ.get("GMID_NGSPICE", _NGSPICE)
    if not os.path.isfile(exe):
        pytest.fail("ngspice 없음 (GMID_NGSPICE=%r)" % exe, pytrace=False)
    z = raw_slice(kind, 1000)
    cell, pol, body = _DEV[kind]
    meta = json.loads(str(z["meta_json"]))
    VGS, VDS, VS = (np.asarray(z[a], dtype=float) for a in ("VGS", "VDS", "VS"))
    Lum = [round(float(x) * 1e6, 6) for x in z["L"]]
    iL = Lum.index(1.0)
    w_um = round(float(z["W"]) * 1e6, 6)
    hg, hd = float(VGS[1] - VGS[0]), float(VDS[1] - VDS[0])
    inst = "@m.xdut.msky130_fd_pr__%s" % cell
    lines = ["* vdsat grid rerun"]
    for rel in meta["model_files_sha256"]:
        if rel.endswith(".spice"):
            lines.append('.include "%s"' % os.path.join(meta["pdk_root"], rel).replace("\\", "/"))
    ad, pd = w_um * 0.5, w_um + 2.0
    lines += ["vgs g 0 dc 0", "vds d 0 dc 0", "vb b 0 dc 0",
              "xdut d g 0 b sky130_fd_pr__%s l=%su w=%su ad=%sp as=%sp pd=%su ps=%su nf=1"
              % (cell, repr(1.0), repr(w_um), "%.6g" % ad, "%.6g" % ad, "%.6g" % pd, "%.6g" % pd),
              ".save v(g) v(d) %s[vdsat] %s[id]" % (inst, inst), ".control", "set filetype=binary"]
    raws = []
    for si in (0, 3):
        lines.append("alter vb dc = %.9g" % (round(body * float(VS[si]), 9) + 0.0))
        lines.append("dc vds %.12g %.12g %.12g vgs %.12g %.12g %.12g"
                     % (pol * VDS[0], pol * VDS[-1], pol * hd, pol * VGS[0], pol * VGS[-1], pol * hg))
        rp = str(tmp_path / ("v_%s_%d.raw" % (kind, si))).replace("\\", "/")
        lines.append("write %s" % rp)
        raws.append((si, rp))
    lines += ["quit", ".endc", ".end"]
    cir = tmp_path / ("v_%s.cir" % kind)
    cir.write_text("\n".join(lines) + "\n", encoding="utf-8")
    r = subprocess.run([exe, "-b", str(cir)], cwd=str(tmp_path), capture_output=True, text=True, timeout=600)
    assert not [ln for ln in (r.stdout + r.stderr).splitlines() if re.search(r"\b(error|fatal)\b", ln, re.I)]
    for si, rp in raws:
        d = _read_raw(rp)
        v = np.abs(d["vdsat"]).reshape(len(VGS), len(VDS))
        lut = np.asarray(z["VDSAT"][iL, :, :, si], dtype=float)
        assert np.array_equal(v, lut), (kind, si, float(np.max(np.abs(v - lut))))
