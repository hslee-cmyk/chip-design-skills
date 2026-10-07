"""C22 접합 용량·확산 기하(Q6) + C3 확산 출처 순서.

근거: README C22·C3, schema devices[].diffusion / process.diffusion 만(오라클 소스 열람 없음).
- 출처 순서: (1) devices[].diffusion -> ad/as/pd/ps 그대로, (2) process.diffusion -> ad=as=ad_per_w_m*finger_w,
  pd=ps=finger_w+pd_extra_m, (3) 둘 다 없음 -> ad/as/pd/ps 없음.
- free(합격 실행, Z1 free 포함)에서 (3) 소자가 있으면 막힘, blocker `C22 접합 용량: 확산 기하 없는 소자 [...]`(이름 정렬).
  forced·iso 는 막지 않고 notes 에 소자 목록.
- meta geometry[<소자>].diffusion, compare.summary.junction_capacitance{included, by_source, missing, zero_area}.
- 측정 확인: 오라클이 쓴 확산 기하가 ngspice 에 실제로 닿는다(m 배 포함) -- 손으로 쓴 독립 넷리스트(finger 마다
  인스턴스 1개, m 없음, finger 마다 ad/pd)의 AC 응답과 오라클 AC 응답이 같고, ad/pd 없는 독립 넷리스트와는 다르다.
"""
import copy
import json
import re
import subprocess
from pathlib import Path

import pytest

from conftest import (CS, NFET, NGSPICE, OFF_ZERO, PFET, ZERO_DIFFUSION, _includes, cs_input, kv, make_lut, measure,
                      require_spice, run_netlist, run_oracle, run_simulate, run_spice, x_lines)

DEV_DIFF = {"ad_m2": 3e-12, "as_m2": 3.5e-12, "pd_m": 8e-6, "ps_m": 9e-6, "basis": "test"}
# 손계산(process 규칙, conftest.process_block): ad=as=5e-7*2e-6=1e-12, pd=ps=2e-6+2e-6=4e-6
RULE = {"ad": 1e-12, "as": 1e-12, "pd": 4e-6, "ps": 4e-6}
C22_MSG = "C22 접합 용량: 확산 기하 없는 소자"


@pytest.fixture
def lut(tmp_path):
    return make_lut(tmp_path / "lut.npz")


def _xkv(text, name):
    ln = [l for l in x_lines(text) if l.split()[0].lower() == f"x{name}".lower()]
    assert len(ln) == 1, ln
    return kv(ln[0].split())


def _c22_blocker(blockers):
    hit = [b for b in blockers if C22_MSG in b]
    assert len(hit) == 1, blockers
    m = re.search(re.escape(C22_MSG) + r"\s*\[([^\]]*)\]", hit[0])
    assert m, hit[0]
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*", m.group(1))


def _with_dev_diff(inp, **per_dev):
    for d in inp["devices"]:
        if d["name"] in per_dev:
            d["diffusion"] = dict(per_dev[d["name"]])
    return inp


# ------------------------------------------------------------------ 출처 순서 (넷리스트)
def test_source1_device_diffusion_overrides_process_rule(tmp_path, lut):
    """M1 은 devices[].diffusion(출처 1), MP1 은 process 규칙(출처 2). process.diffusion 이 있어도 출처 1 이 우선."""
    inp = _with_dev_diff(cs_input(lut, preds_devices=copy.deepcopy(OFF_ZERO)), M1=DEV_DIFF)
    p, text, meta = run_netlist(inp, tmp_path)
    assert p.returncode == 0 and meta["blockers"] == [], (p.stdout + p.stderr)[-1500:]
    m1, mp1 = _xkv(text, "M1"), _xkv(text, "MP1")
    for k, v in (("ad", 3e-12), ("as", 3.5e-12), ("pd", 8e-6), ("ps", 9e-6)):
        assert float(m1[k]) == pytest.approx(v, rel=1e-12), (k, m1)
    for k, v in RULE.items():
        assert float(mp1[k]) == pytest.approx(v, rel=1e-12), (k, mp1)
    # finger 규칙은 그대로(C3): m=n_fingers, nf 없음
    assert int(m1["m"]) == CS["n"] and int(mp1["m"]) == CS["pn"]
    assert "nf" not in m1 and "nf" not in mp1
    g = meta["geometry"]
    assert g["M1"]["diffusion"]["source"] == "device"
    assert g["M1"]["diffusion"]["ad"] == pytest.approx(3e-12) and g["M1"]["diffusion"]["ps"] == pytest.approx(9e-6)
    assert g["MP1"]["diffusion"]["source"] == "process_rule"
    assert g["MP1"]["diffusion"]["pd"] == pytest.approx(4e-6)


def test_source3_none_no_area_params_forced_with_note(tmp_path, lut):
    """process.diffusion 없음 + MP1 만 devices[].diffusion 없음 -> forced: MP1 줄에 ad/as/pd/ps 없음, 막지 않음,
    notes 에 MP1(만), meta 출처 null 과 값 4개 None."""
    inp = _with_dev_diff(cs_input(lut, diffusion=False), M1=DEV_DIFF)
    p, text, meta = run_netlist(inp, tmp_path, "forced")
    assert p.returncode == 0 and meta["blockers"] == [], meta and meta["blockers"]
    assert not set(_xkv(text, "MP1")) & {"ad", "as", "pd", "ps"}
    assert float(_xkv(text, "M1")["ad"]) == pytest.approx(3e-12)
    d = meta["geometry"]["MP1"]["diffusion"]
    assert d["source"] is None and all(d[k] is None for k in ("ad", "as", "pd", "ps")), d
    notes = [n for n in meta["notes"] if "C22" in n]
    assert len(notes) == 1 and "MP1" in notes[0] and "'M1'" not in notes[0], meta["notes"]


def test_iso_uses_same_diffusion_rule_and_is_not_blocked(tmp_path, lut):
    """C17: iso 인스턴스도 C3 확산 규칙 그대로. 확산 없는 소자는 막지 않고 notes."""
    preds = {"M1": {"VGS": 0.7, "VDS": 0.9, "VSB": 0.0}, "MP1": {"VGS": 1.2, "VDS": 1.34, "VSB": 0.3}}
    inp = _with_dev_diff(cs_input(lut, diffusion=False, preds_devices=preds), M1=DEV_DIFF)
    inp["process"]["models"]["nmos"]["polarity"] = "n"
    inp["process"]["models"]["pmos"]["polarity"] = "p"
    p, text, meta = run_netlist(inp, tmp_path, "iso")
    assert p.returncode == 0 and meta["blockers"] == [], meta and meta["blockers"]
    assert float(_xkv(text, "M1")["pd"]) == pytest.approx(8e-6)
    assert not set(_xkv(text, "MP1")) & {"ad", "as", "pd", "ps"}
    assert any("C22" in n and "MP1" in n for n in meta["notes"]), meta["notes"]


# ------------------------------------------------------------------ free 막힘
def test_free_without_any_source_blocked_sorted_names(tmp_path, lut):
    """두 소자 모두 출처 없음 -> free 막힘. 입력 순서를 뒤집어도 blocker 의 이름은 정렬 순서."""
    inp = cs_input(lut, diffusion=False, preds_devices=copy.deepcopy(OFF_ZERO))
    inp["devices"] = inp["devices"][::-1]           # MP1, M1 순서로 입력
    p, text, meta = run_netlist(inp, tmp_path)
    assert meta is not None
    assert _c22_blocker(meta["blockers"]) == ["M1", "MP1"]
    q, res = run_oracle(inp, tmp_path / "o", sat_margin=0.05)
    c = res["free"]
    assert c["summary"]["verdict"] == "BLOCKED" and q.returncode == 2, (q.stdout + q.stderr)[-1500:]
    jc = c["summary"]["junction_capacitance"]
    assert jc["included"] is False and jc["missing"] == ["M1", "MP1"]
    assert jc["by_source"] == {"device": 0, "process_rule": 0, "none": 2}


def test_free_partial_missing_blocks_only_that_device(tmp_path, lut):
    inp = _with_dev_diff(cs_input(lut, diffusion=False, preds_devices=copy.deepcopy(OFF_ZERO)), M1=DEV_DIFF)
    p, text, meta = run_netlist(inp, tmp_path)
    assert _c22_blocker(meta["blockers"]) == ["MP1"]
    # 음성 대조: MP1 에도 기하를 주면 같은 입력이 막히지 않는다(막힘 원인이 C22 하나뿐임)
    _with_dev_diff(inp, MP1=DEV_DIFF)
    p2, _, meta2 = run_netlist(inp, tmp_path / "ok")
    assert p2.returncode == 0 and meta2["blockers"] == [], meta2["blockers"]


def test_z1_free_also_blocked(tmp_path, lut):
    """C22: 'free 모드(합격 실행, Z1 free 포함)' -- --omit 진단 실행도 free 면 막힘."""
    inp = cs_input(lut, diffusion=False, preds_devices=copy.deepcopy(OFF_ZERO))
    p, text, meta = run_netlist(inp, tmp_path, extra=["--omit", "RP"])
    assert meta is not None and _c22_blocker(meta["blockers"]) == ["M1", "MP1"], meta and meta["blockers"]


def test_forced_and_iso_runs_not_blocked_and_recorded(tmp_path, lut):
    preds = {"M1": {"VGS": 0.7, "VDS": 0.9, "VSB": 0.0}, "MP1": {"VGS": 1.2, "VDS": 1.34, "VSB": 0.3}}
    inp = cs_input(lut, diffusion=False, preds_devices=preds)
    inp["process"]["models"]["nmos"]["polarity"] = "n"
    inp["process"]["models"]["pmos"]["polarity"] = "p"
    q, res = run_oracle(inp, tmp_path / "o", biases=("forced", "iso"), sat_margin=0.05)
    for b in ("forced", "iso"):
        c = res[b]
        assert c is not None and c["summary"]["verdict"] == "INCOMPLETE", (b, (q.stdout + q.stderr)[-1500:])
        assert not any(C22_MSG in x for x in c["blockers"])
        jc = c["summary"]["junction_capacitance"]
        assert jc["included"] is False and jc["missing"] == ["M1", "MP1"], (b, jc)
        assert any("C22" in n and "M1" in n and "MP1" in n for n in c["notes"]), (b, c["notes"])
    assert q.returncode == 0


# ------------------------------------------------------------------ summary.junction_capacitance
def test_summary_counts_and_zero_area(tmp_path, lut):
    """M1 = 면적 0 명시(출처 device, zero_area), MP1 = process 규칙 -> 막지 않음, included True."""
    inp = _with_dev_diff(cs_input(lut, preds_devices=copy.deepcopy(OFF_ZERO)), M1=ZERO_DIFFUSION)
    p, text, meta = run_netlist(inp, tmp_path)
    assert p.returncode == 0 and meta["blockers"] == []
    m1 = _xkv(text, "M1")
    assert all(float(m1[k]) == 0.0 for k in ("ad", "as", "pd", "ps")), m1     # 0 도 명시해 쓴다(출처 1)
    q, res = run_oracle(inp, tmp_path / "o", sat_margin=0.05)
    jc = res["free"]["summary"]["junction_capacitance"]
    assert jc == {"included": True, "by_source": {"device": 1, "process_rule": 1, "none": 0},
                  "missing": [], "zero_area": ["M1"]}, jc
    row = [d for d in res["free"]["devices"] if d["name"] == "MP1"][0]
    assert row["diffusion"]["source"] == "process_rule" and row["diffusion"]["ad"] == pytest.approx(1e-12)


def test_partial_zero_is_not_zero_area(tmp_path, lut):
    """zero_area 는 ad=as=pd=ps=0 전부일 때만. ad=as=0 이지만 pd/ps>0 이면 아니다."""
    part = {"ad_m2": 0.0, "as_m2": 0.0, "pd_m": 1e-6, "ps_m": 1e-6}
    inp = _with_dev_diff(cs_input(lut, preds_devices=copy.deepcopy(OFF_ZERO)), M1=part, MP1=ZERO_DIFFUSION)
    q, res = run_oracle(inp, tmp_path / "o", sat_margin=0.05)
    jc = res["free"]["summary"]["junction_capacitance"]
    assert jc["zero_area"] == ["MP1"] and jc["by_source"]["device"] == 2, jc


# ------------------------------------------------------------------ 측정: 접합 용량이 ngspice 에 닿는가
CL_SMALL = 5e-15     # 출력 용량을 줄여 드레인 접합 용량이 UGF 를 좌우하게 함


def _independent_ugf(workdir: Path, ad_pd_per_finger):
    """손으로 쓴 CS: finger 마다 인스턴스 1개(m 없음), 각 finger 에 ad/as/pd/ps(없으면 None). 같은 AC 격자에서 measure()."""
    c = CS
    def extra(d):
        return "" if d is None else f" ad={d['ad']} as={d['as']} pd={d['pd']} ps={d['ps']}"
    body = [f"Vdd vdd 0 DC {c['vdd']}", f"Vsp vsp 0 DC {c['vsp']}", f"Vin nin 0 DC {c['vin']} AC 1",
            f"Vpb pb 0 DC {c['pb']}", f"RL vdd nout {c['rload']}", f"CL nout 0 {CL_SMALL}", f"RP pout 0 {c['rp']}"]
    for i in range(c["n"]):
        body.append(f"XM1_{i} nout nin 0 0 {NFET} l={c['L']} w={c['finger_w']}{extra(ad_pd_per_finger)}")
    for i in range(c["pn"]):
        body.append(f"XMP1_{i} pout pb vsp vdd {PFET} l={c['pL']} w={c['pfinger_w']}")
    r = run_spice("\n".join(body), workdir, ["v(nout)"], ac_out="nout", ac=(0.01, 1e10, 40))
    return measure(r["f"], r["H"])


@pytest.mark.parametrize("source", ["device", "process_rule"])
def test_junction_cap_reaches_ngspice_with_m_scaling(tmp_path, lut, source):
    require_spice()
    big = {"ad": 1e-11, "as": 1e-11, "pd": 1.2e-5, "ps": 1.2e-5}     # finger 하나당
    inp = cs_input(lut, diffusion=(source == "process_rule"), preds_devices=copy.deepcopy(OFF_ZERO))
    if source == "process_rule":
        # 손계산: ad = 5e-6 * 2e-6 = 1e-11, pd = 2e-6 + 1e-5 = 1.2e-5
        inp["process"]["diffusion"] = {"ad_per_w_m": 5e-6, "pd_extra_m": 1e-5}
        inp["devices"][1]["diffusion"] = dict(ZERO_DIFFUSION)
    else:
        inp["devices"][0]["diffusion"] = {"ad_m2": big["ad"], "as_m2": big["as"], "pd_m": big["pd"], "ps_m": big["ps"]}
        inp["devices"][1]["diffusion"] = dict(ZERO_DIFFUSION)
    for ps in inp["passives"]:
        if ps["name"] == "CL":
            ps["value"] = CL_SMALL
    p, text, meta = run_netlist(inp, tmp_path)
    assert p.returncode == 0 and meta["blockers"] == [], meta and meta["blockers"]
    sim = tmp_path / "t.free.sim.json"
    q = run_simulate(tmp_path / "t.free.cir", sim, tmp_path)
    assert q.returncode == 0, (q.stdout + q.stderr)[-1500:]
    ac = json.loads(sim.read_text(encoding="utf-8"))["ac"]

    with_j = _independent_ugf(tmp_path / "ind_j", big)
    no_j = _independent_ugf(tmp_path / "ind_0", None)
    unscaled = _independent_ugf(tmp_path / "ind_half", {k: v / CS["n"] for k, v in big.items()})  # m 배 안 한 가설
    # 독립 넷리스트끼리: 접합 용량이 UGF 를 충분히 움직여 test 가 민감함(>10%)
    assert no_j["ugf_hz"] is not None and abs(with_j["ugf_hz"] / no_j["ugf_hz"] - 1) > 0.10, (with_j, no_j)
    assert abs(with_j["ugf_hz"] / unscaled["ugf_hz"] - 1) > 0.05, (with_j, unscaled)
    # 오라클 = finger 마다 ad/pd 를 단 독립 넷리스트(m 배 포함), 기존 C10 비교와 같은 허용(2e-3)
    assert ac["ugf_hz"] == pytest.approx(with_j["ugf_hz"], rel=2e-3), (ac["ugf_hz"], with_j, no_j, unscaled)
    assert ac["dc_gain_db"] == pytest.approx(with_j["dc_gain_db"], abs=2e-3)


def _drain_cap(workdir: Path, m=1, area=False):
    """README C22 확인 조건의 독립 재현: nfet L=0.5u W=5u, VGS 0.7, VDS 0.9, 1 MHz 드레인 AC 전류 허수부/omega."""
    workdir.mkdir(parents=True, exist_ok=True)
    extra = " ad=2.5p as=2.5p pd=7u ps=7u" if area else ""
    f = 1e6
    lines = ["* drain cap", _includes("tt"), ".temp 27", "Vd d 0 DC 0.9 AC 1", "Vg g 0 DC 0.7",
             f"X1 d g 0 0 {NFET} l=0.5u w=5u m={m}{extra}", ".control", "set noaskquit", f"ac lin 1 {f} {f}",
             "let cdd = imag(i(vd))/(2*pi*1e6)", "print cdd", "quit", ".endc", ".end"]
    (workdir / "c.cir").write_text("\n".join(lines) + "\n", encoding="utf-8")
    p = subprocess.run([str(NGSPICE), "-b", "c.cir"], capture_output=True, text=True, cwd=str(workdir),
                       encoding="utf-8", errors="replace", timeout=120)
    for ln in p.stdout.splitlines():
        if ln.strip().lower().startswith("cdd"):
            return abs(float(ln.split("=", 1)[1].split()[0].rstrip(",")))
    raise AssertionError(p.stdout[-2000:] + p.stderr[-2000:])


def test_readme_drain_cap_claim_reproduced(tmp_path):
    """README C22 의 실측 문장(1.927 -> 4.350 fF, m=2 3.854 -> 8.700 fF)을 독립 넷리스트로 재현: subckt 가 ad/pd 를
    받아 접합 용량을 넣고, m 이 접합분까지 곱한다."""
    require_spice()
    c = {(m, a): _drain_cap(tmp_path / f"m{m}_{a}", m, a) for m in (1, 2) for a in (False, True)}
    assert c[(1, False)] == pytest.approx(1.927e-15, rel=5e-3), c
    assert c[(1, True)] == pytest.approx(4.350e-15, rel=5e-3), c
    assert c[(2, False)] == pytest.approx(2 * c[(1, False)], rel=1e-4), c
    assert c[(2, True)] == pytest.approx(2 * c[(1, True)], rel=1e-4), c
    assert (c[(2, True)] - c[(2, False)]) == pytest.approx(2 * (c[(1, True)] - c[(1, False)]), rel=1e-4)
