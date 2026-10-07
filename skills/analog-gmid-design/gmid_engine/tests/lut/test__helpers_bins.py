"""`_helpers_bins` (bin_index) -- CONTRACT 4.0.1 [r4] bin 소속 규칙, 공개 API 경유(`load_lut_set` 의 `LBinMap`, 조회 거부 사유 키).

- 값 x 는 lo ≤ x ≤ hi 인 구간에 든다(양끝 닫힘), 경계 공유 시 아래(lo 가 작은) 구간 -- 사실상 lmin < L ≤ lmax. W 도 같다.
- 경계 비교는 그 경계값의 1 ulp 이내를 같은 값으로 본다(1 ulp 는 그 bin, 2 ulp 는 아님).
- 참값: toy 는 conftest 의 손계산 bin 표, 실데이터는 ngspice-46 `showmod`(시뮬레이터가 실제로 고른 bin)로 엔진과 독립.
"""
import math

import pytest

from gmid_engine.core import SchemaRejectedError, SealViolationError
from gmid_engine.lut import LBin, LBinMap, op_point

from .conftest import (BIN_ANCHOR_BIN_HI, BIN_ANCHOR_BIN_LO, BIN_BLOCKS, BIN_MODEL_REL, BIN_W_HI, BIN_W_LO,
                       detail_of, new_memo, parse_model_bins, same_bounds, um)


def blocks_with(changes):
    """BIN_BLOCKS 에서 {이름: {필드: 값}} 만 바꾼 tuple."""
    idx = {"lmin": 1, "lmax": 2, "wmin": 3, "wmax": 4}
    out = []
    for b in BIN_BLOCKS:
        b = list(b)
        for f, v in changes.get(b[0], {}).items():
            b[idx[f]] = v
        out.append(tuple(b))
    return tuple(out)


def _lbins(blocks):
    return tuple(LBin(n, a, b) for n, a, b, _, _ in blocks)


# ---------------------------------------------------------------------------
# toy: 손계산 bin 표 (conftest 머리 주석)
# ---------------------------------------------------------------------------

def test_toy_bin_map_structure(bin_toy):
    lo = bin_toy.slice_map[("nmos", 100)].l_bins
    hi = bin_toy.slice_map[("nmos", 200)].l_bins
    assert isinstance(lo, LBinMap) and isinstance(hi, LBinMap)
    assert lo.w_bin == BIN_W_LO                              # W = 1e-6 = 아래 범위 wmax -> 아래 범위(경계는 아래)
    assert hi.w_bin == BIN_W_HI
    assert lo.bins == _lbins(BIN_BLOCKS[:5])                 # (lmin, lmax, model) 오름차순, bin 아닌 .model 블록 무시
    assert hi.bins == _lbins(BIN_BLOCKS[5:])
    assert lo.anchor_bin == BIN_ANCHOR_BIN_LO                # 앵커 2 µm·4 µm(경계) -> 아래 bin, 1 µm(맨 아래 lmin) 포함
    assert hi.anchor_bin == BIN_ANCHOR_BIN_HI                # 4 µm = A' 의 lmax -> A'
    assert tuple(lo.model_files) == (BIN_MODEL_REL,)
    assert bin_toy.cap_map["nmos"].l_bins == lo              # 용량 표 = w_ref_m(1e-6) 폭 슬라이스의 지도


def test_toy_empty_map_without_model_record(toy):
    for sl in toy.slice_map.values():
        assert sl.l_bins == LBinMap((), None, (), ())
    assert toy.cap_map["nmos"].l_bins == LBinMap((), None, (), ())


def test_toy_bin_order_independent_of_file_order(bin_toy_build):
    lut = bin_toy_build(blocks=tuple(reversed(BIN_BLOCKS))).load()
    lo = lut.slice_map[("nmos", 100)].l_bins
    assert lo.bins == _lbins(BIN_BLOCKS[:5])
    assert lo.anchor_bin == BIN_ANCHOR_BIN_LO


@pytest.mark.parametrize("steps,expect_lower", [(1, True), (2, False)])
def test_toy_shared_l_boundary_one_ulp(bin_toy_build, steps, expect_lower):
    """경계 b = 2e-6 − n·ulp(A 의 lmax = B 의 lmin): 앵커 2e-6 은 b 의 1 ulp 이내면 경계로 보아 아래 bin(A), 2 ulp 면 위 bin(B)."""
    b = 2e-6 - steps * math.ulp(2e-6)
    assert math.ulp(b) == math.ulp(2e-6)
    lut = bin_toy_build(blocks=blocks_with({"toyn__model.0": {"lmax": b}, "toyn__model.1": {"lmin": b}})).load()
    ab = lut.slice_map[("nmos", 100)].l_bins.anchor_bin
    assert ab[2] == (0 if expect_lower else 1)
    assert ab[:2] == (0, 0) and ab[3:] == BIN_ANCHOR_BIN_LO[3:]


@pytest.mark.parametrize("steps,ok", [(1, True), (2, False)])
def test_toy_bottom_lmin_one_ulp(bin_toy_build, steps, ok):
    """맨 아래 bin lmin = 1e-6 + n·ulp: 앵커 1e-6 은 1 ulp 면 그 bin, 2 ulp 면 어느 bin 에도 없음(로드 거부)."""
    lmin = 1e-6 + steps * math.ulp(1e-6)
    bt = bin_toy_build(blocks=blocks_with({"toyn__model.0": {"lmin": lmin}}))
    if ok:
        assert bt.load().slice_map[("nmos", 100)].l_bins.anchor_bin == BIN_ANCHOR_BIN_LO
        return
    with pytest.raises(SchemaRejectedError) as ei:
        bt.load()
    det = detail_of(ei.value)
    assert det["reason"] == "lut_l_anchor_outside_model_bins"
    assert det["L"] == 1e-6 and det["w_m"] == 1e-6


@pytest.mark.parametrize("steps,ok", [(1, True), (2, False)])
def test_toy_top_lmax_one_ulp(bin_toy_build, steps, ok):
    lmax = 9e-6 - steps * math.ulp(9e-6)
    bt = bin_toy_build(blocks=blocks_with({"toyn__model.4": {"lmax": lmax}}))
    if ok:
        assert bt.load().slice_map[("nmos", 100)].l_bins.anchor_bin == BIN_ANCHOR_BIN_LO
        return
    with pytest.raises(SchemaRejectedError) as ei:
        bt.load()
    det = detail_of(ei.value)
    assert det["reason"] == "lut_l_anchor_outside_model_bins" and det["L"] == 9e-6


@pytest.mark.parametrize("steps,expect_lower", [(1, True), (2, False)])
def test_toy_shared_w_boundary_one_ulp(bin_toy_build, steps, expect_lower):
    """W 경계 wb = 1e-6 − n·ulp(아래 범위 wmax = 위 범위 wmin): 슬라이스 W 1e-6 은 1 ulp 면 아래 범위, 2 ulp 면 위 범위."""
    wb = 1e-6 - steps * math.ulp(1e-6)
    ch = {b[0]: ({"wmax": wb} if b[4] == 1e-6 else {"wmin": wb}) for b in BIN_BLOCKS}
    lut = bin_toy_build(blocks=blocks_with(ch)).load()
    lm = lut.slice_map[("nmos", 100)].l_bins
    if expect_lower:
        assert lm.w_bin == (BIN_W_LO[0], wb) and lm.anchor_bin == BIN_ANCHOR_BIN_LO
    else:
        assert lm.w_bin == (wb, BIN_W_HI[1]) and lm.anchor_bin == BIN_ANCHOR_BIN_HI


# 조회 L 의 bin(거부 경로의 b) -- 같은 규칙·같은 1 ulp. 양옆 앵커 4 µm(B)·7 µm(D).
@pytest.mark.parametrize("L,reason,bin_name", [
    (5e-6, "lut_l_bin_unbracketed", "toyn__model.2"),                         # C 의 lmax 그 자체(닫힘), C 앵커 0개
    (5e-6 + math.ulp(5e-6), "lut_l_bin_unbracketed", "toyn__model.2"),        # 1 ulp 위 = 경계
    (5e-6 + 2 * math.ulp(5e-6), "lut_l_outside_model_bins", None),           # 2 ulp 위 = 빈틈
    (5.5e-6, "lut_l_outside_model_bins", None),
    (6e-6, "lut_l_cross_bin", "toyn__model.3"),                               # D 의 lmin(공유 안 한 경계 -- 닫힘)
    (6e-6 - math.ulp(6e-6), "lut_l_cross_bin", "toyn__model.3"),
    (6e-6 - 2 * math.ulp(6e-6), "lut_l_outside_model_bins", None),
])
def test_toy_query_bin_membership(bin_memo, L, reason, bin_name):
    with pytest.raises(SealViolationError) as ei:
        op_point(bin_memo, "nmos", 100, L, 0.5, 0.5, 0.0)
    det = detail_of(ei.value)
    assert det["reason"] == reason
    assert det["below"] == 4e-6 and det["above"] == 7e-6
    if bin_name is None:
        assert "bin" not in det
    else:
        assert det["bin"] == bin_name


@pytest.mark.parametrize("decoy", [
    "+ rdswmin = 0.0 rdwmin = 0.0 lmin2 = 9.0",          # sky130 블록에 실제로 있는 rdswmin·rdwmin
    "+ xwmin = 1.0 xlmax = 1.0 wmaxx = 1.0",
])
def test_toy_key_must_be_whole_word(bin_toy_build, decoy):
    """`키 = 숫자` 의 키는 lmin·lmax·wmin·wmax 그 자체. decoy 줄을 각 블록의 bin 줄 **앞** 에 넣어도 지도는 그대로다."""
    text = []
    for ln in bin_toy_build("plain").model_path.read_text(encoding="utf-8").splitlines():
        if ln.startswith("+ lmin"):
            text.append(decoy)
        text.append(ln)
    lut = bin_toy_build("decoy", model_text="\n".join(text) + "\n").load()
    lm = lut.slice_map[("nmos", 100)].l_bins
    assert lm.w_bin == BIN_W_LO and lm.anchor_bin == BIN_ANCHOR_BIN_LO
    assert lm.bins == _lbins(BIN_BLOCKS[:5])


def test_toy_keys_case_insensitive(bin_toy_build):
    plain = bin_toy_build("plain").model_path.read_text(encoding="utf-8")
    text = (plain.replace("lmin =", "LMIN =").replace("lmax =", "Lmax =")
            .replace("wmin =", "WMIN=").replace("wmax =", "wMax  ="))
    lut = bin_toy_build("upper", model_text=text).load()
    lm = lut.slice_map[("nmos", 100)].l_bins
    assert lm.w_bin == BIN_W_LO and lm.anchor_bin == BIN_ANCHOR_BIN_LO


# ---------------------------------------------------------------------------
# 실데이터: ngspice-46 showmod 참값
# ---------------------------------------------------------------------------

KIND_DEVICE = (("nmos", "nfet_01v8"), ("pmos", "pfet_01v8"))


@pytest.mark.lut_realdata
@pytest.mark.parametrize("kind,device", KIND_DEVICE)
def test_real_anchor_bins_match_ngspice(real_lut, ngspice_bins, kind, device):
    """모든 슬라이스 × 모든 L 앵커: 엔진 anchor_bin 이 가리키는 bin 의 (lmin, lmax)·w_bin 이 showmod 와 같고,
    그 bin 이름이 모델 파일에서 그 경계 4값을 가진 블록 이름(test 독립 파서)과 같다."""
    names = parse_model_bins(ngspice_bins.pm3(device))
    keys = sorted(k for k in real_lut.slice_map if k[0] == kind)
    assert keys
    pts, where = [], []
    for key in keys:
        sl = real_lut.slice_map[key]
        for i, L in enumerate(sl.grids[0]):
            pts.append((um(sl.w_m), um(L)))
            where.append((key, i))
    got = ngspice_bins.query(device, pts)
    bad = []
    for (key, i), g in zip(where, got):
        lm = real_lut.slice_map[key].l_bins
        b = lm.bins[lm.anchor_bin[i]]
        eng = (b.lmin, b.lmax) + tuple(lm.w_bin)
        if not same_bounds(eng, g):
            bad.append((key, i, eng, g))
            continue
        hit = [n for n, bnd in names.items() if same_bounds(bnd, g)]
        if hit != [b.model]:
            bad.append((key, i, b.model, hit))
    assert not bad, bad[:10]
    assert len(got) == len(pts) == 12 * len(keys)


# 경계값·경계 한 제조 격자(5 nm) 위 -- 비앵커 조회의 b(거부 detail 의 bin 경계·bin 앵커)가 showmod 의 bin 과 같다
BOUNDARY_L_UM = (0.18, 0.185, 0.255, 0.505, 1.005, 2.0, 2.005)


@pytest.mark.lut_realdata
@pytest.mark.parametrize("kind,device", KIND_DEVICE)
@pytest.mark.parametrize("l_um", BOUNDARY_L_UM)
def test_real_boundary_queries_match_ngspice(real_lut, ngspice_bins, kind, device, l_um):
    sl = real_lut.slice_map[(kind, 1000)]
    W = um(sl.w_m)
    anchors = [float(x) for x in sl.grids[0]]
    L = l_um * 1e-6
    assert all(abs(L - a) > math.ulp(a) for a in anchors)
    q = ngspice_bins.query(device, [(W, l_um)] + [(W, um(a)) for a in anchors])
    gL, ga = q[0], q[1:]
    assert gL is not None and all(g is not None for g in ga)
    k = next(j for j, a in enumerate(anchors) if a > L)
    in_bin = tuple(a for a, g in zip(anchors, ga) if same_bounds(g, gL))
    assert not same_bounds(ga[k - 1], ga[k]), "고른 경계 L 은 모두 bin 경계를 건너는 앵커 쌍 사이여야 한다"
    with pytest.raises(SealViolationError) as ei:
        op_point(new_memo(real_lut), kind, 1000, L, 0.9, 0.9, 0.0)
    det = detail_of(ei.value)
    assert det["reason"] == ("lut_l_bin_unbracketed" if len(in_bin) <= 1 else "lut_l_cross_bin")
    assert same_bounds((det["bin_lmin"], det["bin_lmax"]), gL[:2])
    assert tuple(det["bin_anchors"]) == in_bin
    assert det["below"] == anchors[k - 1] and det["above"] == anchors[k]


@pytest.mark.lut_realdata
def test_real_contract_anchor_bin_table(real_lut):
    """CONTRACT 1.4 [r4 실측] 표: 모든 슬라이스 anchor_bin = (0, 1, 1, 2, 2, 2, 2, 3, 3, 4, 5, 5), w_key 1000 은 w_bin (3e-6, 5e-6),
    pmos w_key 84·110 은 같은 w_bin (4.2e-7, 5.5e-7). (값 자체의 참은 위 ngspice 대조가 정한다.)"""
    for key, sl in real_lut.slice_map.items():
        assert sl.l_bins.anchor_bin == (0, 1, 1, 2, 2, 2, 2, 3, 3, 4, 5, 5), key
    for kind in ("nmos", "pmos"):
        assert same_bounds(real_lut.slice_map[(kind, 1000)].l_bins.w_bin, (3e-6, 5e-6))
    assert same_bounds(real_lut.slice_map[("pmos", 84)].l_bins.w_bin, (4.2e-7, 5.5e-7))
    assert same_bounds(real_lut.slice_map[("pmos", 110)].l_bins.w_bin, (4.2e-7, 5.5e-7))
