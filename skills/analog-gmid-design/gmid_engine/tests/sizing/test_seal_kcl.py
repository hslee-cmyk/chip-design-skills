"""봉인 3 `dc_seal_kcl(snapshot, resistances)` -- CONTRACT 6절: 레일 아닌 넷마다 |Σ from − Σ to|, MOS = idu_forward·W/L,
저항 = (V(from) − V(to))/R, 이상원 = dc_current; tol = 채널이 닿는 MOS 의 tol_v·dc_gm 최댓값(정의된 것; MOS 는 있는데
모두 None 이면 None), MOS 없는 넷은 n·eps·Σ|I|.
[U17 ①] tol_I 의 gm = 후보 자기 동작점의 `device.dc_gm`(= ID × 그 동작점 LUT gm/ID, 설계 40 v1.6 §3.7-3·§2.4.11). 옛 `dc_gm_bound`
(S2p·곡선 최대 상계)는 폐기. 손 test 의 gm 은 conftest `hand_dc_gm`(LUT 파일을 직접 읽은 gm/ID × ID)이다.

비고: DC 원소가 하나도 닿지 않는 넷(gate 만 있는 넷)을 행으로 세는지는 계약 문장으로 정해지지 않아(그 행은 0 ≤ 0 pass),
n_checked 는 원소가 닿는 넷만으로 비교한다(보고: 모호).
"""
import dataclasses

import pytest

from gmid_engine.sizing import dc_seal_kcl

from .conftest import (EPS, assert_item, build_ctx, hand_dc_gm, judge_expect, mos, node_voltages, rel_close,
                       resistances_of, seal_item, tamper, theta_a, theta_c, topo, toy_npz, two, with_tol)
from .conftest import kschema  # [U17 ①-b] graph/kernel 필드 읽기(설계 40 v1.9.1 §2.4.7 KernelContext 행)


def _accum(snap, resistances):
    """넷마다 {sum_from, sum_to, abs, mos} -- 원소 끝(basis.ends)이 닿는 레일 아닌 넷. 값은 S1 열·dc_op·dc_current·노드 전압(입력 데이터)에서 손으로 모은다."""
    V = node_voltages(snap)
    R = dict(resistances)
    ops = dict(snap.column("device", "dc_op"))
    cur = dict(snap.column("device", "dc_current"))
    tolv = dict(snap.column("device", "dc_tol_v"))
    gmb = dict(snap.column("device", "dc_gm"))
    rails = {n for n, r in snap.column("node", "is_rail") if r}
    basis = snap.value("graph", "dc", "dc_current_basis")
    acc = {}
    for name, f, t in basis.ends:
        cls = snap.value("device", name, "element_class")
        if cls == "mos":
            i = ops[name].idu_forward * ops[name].W / ops[name].L
        elif snap.value("device", name, "kind") == "resistor":
            i = (V[f] - V[t]) / R[name]
        else:
            i = cur[name]
        for net, sgn in ((f, 1.0), (t, -1.0)):
            if net in rails:
                continue
            a = acc.setdefault(net, {"sum_from": 0.0, "sum_to": 0.0, "abs": [], "mos": []})
            if sgn > 0:
                a["sum_from"] += i
            else:
                a["sum_to"] += i
            a["abs"].append(abs(i))
            if cls == "mos":
                a["mos"].append(name)
    return acc


def input_nets_of(snap):
    """S1 `node.port_direction` 열에서 방향 "input" 인 넷 (카드 §3 '봉인 3 입력 포트' -- 판별은 포트 방향 하나)."""
    return {n for n, d in snap.column("node", "port_direction") if d == "input"}


def input_sum_of(snap, resistances):
    """((입력 넷, Σ), ...) -- 원소 끝이 닿는 입력 넷의 sum_from − sum_to (행 잔차와 같은 부호). 닿지 않는 입력 넷은 항목 없음."""
    acc = _accum(snap, resistances)
    ins = input_nets_of(snap)
    return tuple((n, acc[n]["sum_from"] - acc[n]["sum_to"]) for n in sorted(acc) if n in ins)


def rows_of(snap, resistances):
    """봉인 3 판정 행 (개정 2026-11-06, O-244): 레일도 입력 포트도 아닌 넷만 행이다."""
    acc = _accum(snap, resistances)
    ins = input_nets_of(snap)
    tolv = dict(snap.column("device", "dc_tol_v"))
    gmb = dict(snap.column("device", "dc_gm"))
    rows = []
    for net in sorted(acc):
        if net in ins:
            continue
        a = acc[net]
        if a["mos"]:
            d = [tolv[m] * gmb[m] for m in a["mos"] if tolv[m] is not None]
            tol = max(d) if d else None
        else:
            tol = len(a["abs"]) * EPS * sum(a["abs"])
        rows.append((net, abs(a["sum_from"] - a["sum_to"]), tol, tuple(sorted(set(a["mos"]))), (net,)))
    return rows


def run(snap, res=()):
    from gmid_engine.search import open_run
    donors, counters = open_run()          # [XRUN-F1 card B C4] 블록 단독 호출 = 새 실행 하나
    return seal_item(dc_seal_kcl(snap, tuple(res), donors=donors, counters=counters), 3)


@pytest.mark.parametrize("which", ["C", "A"])
def test_pass(ctx_c, ctx_a, which):
    ctx, th = (ctx_c[2], theta_c()) if which == "C" else (ctx_a[2], theta_a())
    snap, _ = with_tol(ctx, th)
    res = resistances_of(ctx, th)
    exp = judge_expect(rows_of(snap, res))
    assert exp["status"] == "pass"
    assert_item(run(snap, res), exp, 3, atol=1e-18)


def test_hand_tol_is_max_tolv_times_own_dc_gm(ctx_c, toy_lut_paths):
    """설계 40 §3.7-3: tol_I(out) = max(tol_V·gm) over out 에 채널이 닿는 MOS(M1·M2), gm = 자기 동작점 ID × LUT 파일 gm/ID(손계산)."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    item = run(snap)
    tolv = dict(snap.column("device", "dc_tol_v"))
    ops = dict(snap.column("device", "dc_op"))
    gm = {m: hand_dc_gm(lambda kind: toy_npz(toy_lut_paths[0], kind), ops[m]) for m in ("M1", "M2")}
    assert dict(item.detail)["worst"] == "out"
    assert rel_close(item.tol, max(tolv["M1"] * gm["M1"], tolv["M2"] * gm["M2"]), 1e-9)


def test_fail_mos_current_mismatch(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    op = dict(snap.column("device", "dc_op"))["M1"]
    bad = tamper(snap, "dc_solve", "device", "dc_op", {"M1": dataclasses.replace(op, idu_forward=op.idu_forward * 1e6)})
    exp = judge_expect(rows_of(bad, ()))
    assert exp["status"] == "fail" and exp["nodes"] == ("out",)
    assert_item(run(bad), exp, 3)
    # 손계산: |1e6·I − I| = 999999·1e-5 (tol_I = tol_V × 동작점 gm 보다 훨씬 큰 잔차)
    assert rel_close(run(bad).magnitude, 999999 * 1e-5, 1e-6)


def test_fail_wrong_resistance(ctx_a):
    ctx, th = ctx_a[2], theta_a()
    snap, _ = with_tol(ctx, th)
    res = (("R1", 1.0),)                    # 노드전압은 R = 9e4 로 풀었는데 봉인에 1 Ω -> 저항 전류 0.9 A
    exp = judge_expect(rows_of(snap, res))
    assert exp["status"] == "fail" and exp["nodes"] == ("out",)
    item = run(snap, res)
    assert_item(item, exp, 3)
    assert rel_close(item.magnitude, abs(0.9 / 1.0 - 1e-5), 1e-9)


def test_undefined_when_all_mos_tol_none(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = tamper(snap, "dc_tolerances", "device", "dc_tol_v", {"M1": None, "M2": None})
    exp = judge_expect(rows_of(s2, ()))
    assert exp["status"] == "undefined"
    assert_item(run(s2), exp, 3)


def test_one_mos_tol_none_uses_other(ctx_c, toy_lut_paths):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = tamper(snap, "dc_tolerances", "device", "dc_tol_v", {"M1": None})
    item = run(s2)
    assert item.status == "pass"
    gm2 = hand_dc_gm(lambda kind: toy_npz(toy_lut_paths[0], kind), dict(snap.column("device", "dc_op"))["M2"])
    assert rel_close(item.tol, dict(s2.column("device", "dc_tol_v"))["M2"] * gm2, 1e-9)


def test_ideal_source_term(tmp_path, toy_access):
    """n 넷: I1·I2(고정) 가 들어오고 M1·M2 가 나간다. 이상원 항 = dc_current."""
    doc = topo("hand_two_src_kcl",
               [mos("M1", "nmos", "n", "in", "gnd"), mos("M2", "nmos", "n", "b2", "gnd")],
               {"in": ("input", "x"), "n": ("output", "y")},
               sources=[two("I1", "current_source", "vdd", "n"), two("I2", "current_source", "vdd", "n")],
               bias=["b2"])                                                                  # b2: M2 gate 에만
    from .conftest import Oracle
    ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 1e-5), ("I2", 2e-5)))[2]
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("y", "n"): 0.5,
          ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.9, 0.0), ("ln_idu", "M2"): Oracle.ln_idu("nmos", 0.5, 0.9, 0.0)}
    from .conftest import free_currents
    th.update(free_currents(ctx, {"M1": 2e-5, "M2": 1e-5}))              # M1 + M2 = I1 + I2
    assert set(th) == set(kschema(ctx).components)
    snap, _ = with_tol(ctx, th)
    exp = judge_expect(rows_of(snap, ()))
    assert exp["status"] == "pass"
    assert_item(run(snap), exp, 3, atol=1e-18)
    bad = tamper(snap, "dc_currents", "device", "dc_current", {"I1": 1e3})
    exp = judge_expect(rows_of(bad, ()))
    assert exp["status"] == "fail" and exp["nodes"] == ("n",)
    assert_item(run(bad), exp, 3)


# ---------------------------------------------------------------------------
# 봉인 3 입력 포트 (card 20261104-wb1 §3 '봉인 3 입력 포트', 사용자 결정 O-244, 계획 N3.6 '측정 구성 원 넷')  S3-2 ~ S3-5
#
# oracle 종류와 출처
# - S3-2 (손/식): 입력 넷 `in` 에 MOS 채널 끝점(소스)과 이상 전류원이 닿는다. 판정 행 = 레일도 입력 포트도 아닌 넷(카드 표). 기대 행·Σ 는 이 파일 `rows_of`·
#   `input_sum_of` 가 S1 열·dc_op(IDu·W/L)·dc_current·노드 전압에서 손으로 모은다(피검 함수 호출 0). Σ = sum_from − sum_to (행 잔차와 같은 부호). 독립 대조:
#   탐색 KCL 이 M1 채널 전류 = 이상원 θ 값(basis row)이므로 I_M = I_s(원래 값), tamper 로 전류원 기록만 3·I_s 로 바꾸면 Σ = 3·I_s − I_M = 2·I_s.
#   비교 허용 = 카드 '봉인 3 의 MOS 없는 넷과 같은 부동소수 한계 식 n·eps·Σ|I|'(새 상수 0).
# - S3-3 (식): 같은 규칙 -- servo 출력 `out` 은 입력도 레일도 아니라 행 유지. 입력 `inp`·`inn` 은 MOS gate 에만 닿아 행·기록 항목 없음.
# - S3-4 (식): spec 노드 목표 넷은 입력 포트가 아니므로 행 유지(판별은 포트 방향 하나, 목표 관계를 판별에 쓰지 않음).
# - S3-5 (식): gate 에만 닿는 입력 -> 판정 행·잔차·상태는 옛 규칙과 같고 `input_source_current` = ().
# 회로는 이름 없는 새 topology 이고, 꼴이 깨지면(전제 단언 실패) 회로·기대값을 고치지 말고 멈추고 보고한다.
# ---------------------------------------------------------------------------

def circuit_input_channel():
    """S3-2 회로: M1 nmos (drain out, gate vb, source in, bulk in), 저항 R1 vdd -> out, 이상 전류원 I1 in -> gnd. 레일 vdd·vb·gnd, 포트 in 입력·out 출력."""
    return topo("wb1_s3_input_channel", [mos("M1", "nmos", "out", "vb", "in", "in")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                passives=[two("R1", "resistor", "vdd", "out")], sources=[two("I1", "current_source", "in", "gnd")],
                rails=("vdd", "gnd", "vb"))


S3_I = 1e-5                      # 이상 전류원 선언 값(입력)
S3_R = 4e4                       # 저항 θ (V(out)_탐색 = 1.8 − I·R = 1.4 V)
S3_SUPPLIES = {"vdd": 1.8, "gnd": 0.0, "vb": 1.0}


def input_channel_setup(tmp_path, toy_access):
    """-> (ctx, θ, 평가 스냅샷(tol 포함), 저항 tuple). 손 설계점: V(in) = V(vb) − VGS = 1.0 − 0.6 = 0.4, M1 VDS = 1.4 − 0.4 = 1.0, VSB = 0."""
    from .conftest import Oracle
    ctx = build_ctx(tmp_path, circuit_input_channel(), toy_access, supplies=S3_SUPPLIES, element_values=(("I1", S3_I),))[2]
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 1.0, 0.0), ("resistance", "R1"): S3_R}
    assert set(th) == set(kschema(ctx).components)
    snap, _ = with_tol(ctx, th)
    return ctx, th, snap, resistances_of(ctx, th)


def test_s3_2_input_net_with_channel_end_has_no_row_and_records_source_current(tmp_path, toy_access):
    ctx, th, snap, res = input_channel_setup(tmp_path, toy_access)
    # 전제: 입력 넷 `in` 에 원소 끝점이 실제로 닿고(MOS 채널 + 이상 전류원), 포트 방향이 input 이다
    basis = snap.value("graph", "dc", "dc_current_basis")
    touching = sorted(n for n, f, t in basis.ends if "in" in (f, t))
    assert touching == ["I1", "M1"] and input_nets_of(snap) == {"in"}
    # 탐색 평가의 KCL 이 M1 채널 전류 = 전류원 값을 내므로 먼저 통과 (옛·새 규칙 모두 통과)
    assert dict(snap.column("device", "dc_current"))["I1"] == S3_I
    # 전류원 기록만 3·I_s 로 바꿔 I_M ≠ I_s 인 스냅샷 (θ 로는 basis row 가 두 전류를 묶어 I_M ≠ I_s 를 만들 수 없다 -- 보고)
    bad = tamper(snap, "dc_currents", "device", "dc_current", {"I1": 3 * S3_I})
    op = dict(bad.column("device", "dc_op"))["M1"]
    i_m = op.idu_forward * op.W / op.L
    tol_in = dict(bad.column("device", "dc_tol_v"))["M1"] * dict(bad.column("device", "dc_gm"))["M1"]
    assert abs(i_m - S3_I) <= 1e-6 * S3_I                                    # 손: 채널 전류 = 탐색 KCL 값 I_s
    assert abs(i_m - 3 * S3_I) > tol_in                                      # 전제: 차 |I_M − I_s| > 그 넷 tol_I (옛 규칙이면 `in` 행 거부)
    rows = rows_of(bad, res)
    assert [r[0] for r in rows] == ["out"]                                   # 판정 행에 `in` 없음, `out` 남음
    exp = judge_expect(rows)
    assert exp["status"] == "pass" and exp["n_checked"] == 1
    item = run(bad, res)
    assert_item(item, exp, 3)                                                # 다른 행이 통과하면 봉인 3 통과
    rec = dict(item.detail)["input_source_current"]
    assert len(rec) == 1 and rec[0][0] == "in"
    hand = input_sum_of(bad, res)
    assert [n for n, _ in hand] == ["in"]
    n_el = 2                                                                 # `in` 에 닿는 원소 수 (M1, I1)
    bound = n_el * EPS * (abs(i_m) + abs(3 * S3_I))                          # n·eps·Σ|I|
    assert abs(rec[0][1] - hand[0][1]) <= bound
    assert abs(rec[0][1] - 2 * S3_I) <= 1e-6 * S3_I                          # 독립 손 값 Σ = 3·I_s − I_s (부호 = 행 잔차와 같은 sum_from − sum_to)


def test_s3_2_unchanged_when_currents_agree(tmp_path, toy_access):
    """통과 쪽 대조: 탐색 평가 그대로(I_M = I_s)이면 입력 넷 합 ≈ 0 이 기록되고 상태는 통과."""
    ctx, th, snap, res = input_channel_setup(tmp_path, toy_access)
    item = run(snap, res)
    exp = judge_expect(rows_of(snap, res))
    assert exp["status"] == "pass"
    assert_item(item, exp, 3)
    rec = dict(item.detail)["input_source_current"]
    assert [n for n, _ in rec] == ["in"] and abs(rec[0][1]) <= 1e-6 * S3_I


def servo_setup(tmp_path):
    """S3-3 회로 (R-2 꼴, 회로 이름 없음): 입력 쌍 inp·inn 은 MOS gate 에만 닿는다. 합성 bin LUT(슬라이스 {1, 2} µm)."""
    from search.wb1_flow import R2_CELLS, circuit_r2, r2_theta       # 회로·θ 입력은 WB-1 search 공용 helper 한 곳
    from sizing.wb1_toy import access_of, write_r4_bins_lut
    lut, _, _ = write_r4_bins_lut(tmp_path / "lut")
    ctx = build_ctx(tmp_path, circuit_r2(), access_of(lut), engine_elements=("I0",))[2]
    th = r2_theta(ctx)
    snap, _ = with_tol(ctx, th)
    return ctx, th, snap, resistances_of(ctx, th)


def test_s3_3_servo_output_row_kept_and_input_pair_has_no_row_or_record(tmp_path):
    ctx, th, snap, res = servo_setup(tmp_path)
    assert input_nets_of(snap) == {"inp", "inn"}
    basis = snap.value("graph", "dc", "dc_current_basis")
    assert not any(n in ("inp", "inn") for _, f, t in basis.ends for n in (f, t))        # 전제: 입력 쌍은 gate 에만 닿는다(원소 끝점 없음)
    ok = run(snap, res)
    assert ok.status == "pass"
    # tamper: 출력에 닿는 소자 전류 하나(M4 pmos, out 에 드레인)를 바꿔 out 잔차 > tol_I
    import dataclasses as dc
    ops = dict(snap.column("device", "dc_op"))
    bad = tamper(snap, "dc_solve", "device", "dc_op", {"M4": dc.replace(ops["M4"], idu_forward=ops["M4"].idu_forward * 1e3)})
    rows = rows_of(bad, res)
    row = {r[0]: r for r in rows}
    assert "out" in row and row["out"][1] > row["out"][2]                    # 전제: out 잔차 > 그 넷 tol_I
    assert "inp" not in row and "inn" not in row
    exp = judge_expect(rows)
    assert exp["status"] == "fail" and "out" in exp["nodes"]
    item = run(bad, res)
    assert_item(item, exp, 3)                                                # 거부 = 기존 봉인 3 위반 (out 행 판정에 남음)
    assert item.status == "fail" and "out" in item.nodes
    assert dict(item.detail)["input_source_current"] == ()                   # 입력 넷 항목 없음


def circuit_target_net():
    """S3-4 회로: M1 nmos (out, in, s1), M2 pmos (out, pb, vdd), M5 nmos (s1, vb5, gnd). s1 = spec 노드 목표 넷 (W3), in = 입력(M1 gate 에만)."""
    return topo("wb1_s3_target", [mos("M1", "nmos", "out", "in", "s1"), mos("M2", "pmos", "out", "pb", "vdd"),
                                  mos("M5", "nmos", "s1", "vb5", "gnd")],
                {"in": ("input", "x"), "out": ("output", "y")}, bias=["pb", "vb5"])


def test_s3_4_declared_target_net_row_is_kept_and_rejects(tmp_path, toy_access):
    from .conftest import Oracle, free_currents, kfixed
    ctx = build_ctx(tmp_path, circuit_target_net(), toy_access, node_targets=(("s1", 0.3),))[2]
    assert kfixed(ctx) == (("s1", 0.3),)
    y = 0.4
    vout = 0.3 + y * 1.5
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M5"): 2e-6,
          ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.5, vout - 0.3, 0.3),
          ("ln_idu", "M2"): Oracle.ln_idu("pmos", 0.7, 1.8 - vout, 0.0),
          ("ln_idu", "M5"): Oracle.ln_idu("nmos", 0.65, 0.3, 0.0), ("y", "out"): y}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M5": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
    snap, _ = with_tol(ctx, th)
    res = resistances_of(ctx, th)
    assert "s1" not in input_nets_of(snap)                                   # 목표 넷은 입력 포트가 아니다
    ok_rows = rows_of(snap, res)
    assert {r[0] for r in ok_rows} == {"out", "s1"}                          # 목표 넷 행이 판정에 있다
    assert judge_expect(ok_rows)["status"] == "pass"
    assert run(snap, res).status == "pass"
    op = dict(snap.column("device", "dc_op"))["M5"]
    bad = tamper(snap, "dc_solve", "device", "dc_op", {"M5": dataclasses.replace(op, idu_forward=op.idu_forward * 1e6)})
    exp = judge_expect(rows_of(bad, res))
    assert exp["status"] == "fail" and exp["nodes"] == ("s1",)
    item = run(bad, res)
    assert_item(item, exp, 3)
    assert item.status == "fail" and item.nodes == ("s1",)                    # 거부 유지
    assert dict(item.detail)["input_source_current"] == ()


def test_s3_5_gate_only_input_keeps_rows_residuals_and_records_nothing(ctx_c, ctx_a):
    """입력이 MOS gate 에만 닿는 회로(C·A): 판정 행·잔차·상태는 옛 규칙(입력 제외 없음)과 같다 -- 입력 넷에 원소 끝이 없어 행 집합이 같다 --
    그리고 `input_source_current` = ()."""
    for ctx, th in ((ctx_c[2], theta_c()), (ctx_a[2], theta_a())):
        snap, _ = with_tol(ctx, th)
        res = resistances_of(ctx, th)
        assert input_nets_of(snap) == {"in"}
        basis = snap.value("graph", "dc", "dc_current_basis")
        assert not any("in" in (f, t) for _, f, t in basis.ends)             # 전제: 입력 넷에 원소 끝점 없음
        assert input_sum_of(snap, res) == ()
        exp = judge_expect(rows_of(snap, res))
        assert exp["status"] == "pass"
        item = run(snap, res)
        assert_item(item, exp, 3, atol=1e-18)
        assert dict(item.detail)["input_source_current"] == ()
    # 거부 쪽 비트 동일: 기존 test_fail_mos_current_mismatch 의 tamper 가 같은 행·같은 사유를 낸다
    snap, _ = with_tol(ctx_c[2], theta_c())
    op = dict(snap.column("device", "dc_op"))["M1"]
    bad = tamper(snap, "dc_solve", "device", "dc_op", {"M1": dataclasses.replace(op, idu_forward=op.idu_forward * 1e6)})
    exp = judge_expect(rows_of(bad, ()))
    assert exp["status"] == "fail" and exp["nodes"] == ("out",)
    item = run(bad)
    assert_item(item, exp, 3)
    assert dict(item.detail)["input_source_current"] == ()


# ---- 소스 grep (카드 §3 '봉인 3 입력 포트': 직접 비교 0, 판정 소비자 0) -- 관찰 지점이 아니라 소스 텍스트 단언
def _engine_py_files():
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[2]            # .../gmid_engine
    return root, [p for p in root.rglob("*.py") if "tests" not in p.relative_to(root).parts]


def test_s3_no_direct_input_direction_comparison_and_helper_is_called():
    import re
    root, _ = _engine_py_files()
    for rel in ("sizing/seal_kcl.py", "sizing/block_dc.py"):
        text = (root / rel).read_text(encoding="utf-8")
        assert re.search(r"INPUT_DIRECTION\s*(==|!=)|(==|!=)\s*INPUT_DIRECTION", text) is None, rel
        assert "input_port_nets(" in text, rel                       # 양성 대조: 판별은 공개 helper 하나를 부른다


def test_s3_input_source_current_has_no_judging_consumer():
    root, files = _engine_py_files()
    hits = sorted(str(p.relative_to(root)).replace("\\", "/") for p in files if "input_source_current" in p.read_text(encoding="utf-8"))
    assert hits == ["sizing/seal_kcl.py"], hits                       # 기록 칸의 writer 한 곳만, 읽는 쪽 0
