# -*- coding: utf-8 -*-
"""세션21 -- 순수 수치(부동소수점) MNA. sympy 기호해는 M10/M19를 넣는 순간 항 개수가
수천~수만으로 불어나 손도 못 대지만(stage2_dump_exact_forms.py 실측), **수치**로는 18노드든
31소자든 그냥 선형대수라 순식간이다(이게 이번 세션 핵심 교훈 -- 폐형식이 아니라 수치 MNA로
가야 하는 이유). 두 모델을 비교한다:
  (1) FULL: 31소자(1단11+battery A/B 20) 그대로 numeric MNA.
  (2) REDUCED: 1단 11 + M10/M19 부하(gds) + M8/M17을 "-gm*vdd를 Vop1/Vom1에 직접 주입"으로
      축약(세션21 STEP4에서 대수적으로 확인된 leading-order 축약, gm≫gds 가정).
  REDUCED가 FULL과 충분히 가까우면(수 dB 이내) 구현에 REDUCED를 쓴다 -- 소자 수가 훨씬 적어
  metric_spec 키도 적고 유지보수하기 쉽다.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
    "skills", "analog-gmid-design", "assets")))
from stick_diagram import load_topology  # noqa: E402

TOPO_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
                          "skills", "analog-gmid-design", "assets", "library",
                          "current_reuse_telescopic_ota.topology.json")

STAGE1 = ["M6", "M7", "M1a", "M1b", "M2a", "M2b", "M3a", "M3b", "M4a", "M4b", "M5"]
BATTERY_A = ["M8", "M9a", "M9b", "M11a", "M11b", "M12", "M10", "M13", "M14a", "M14b"]
BATTERY_B = ["M17", "M18a", "M18b", "M20a", "M20b", "M21", "M19", "M22", "M23a", "M24b"]
AC_GROUND = {"gnd", "Vbias1", "Vbias2", "Vbias3", "Vbias4", "Vcmfb"}


def mna_solve(devices, unknown_nodes, fixed):
    """devices: [(drain, source, gate, gm, gds), ...]. 순수 Python Gaussian elimination."""
    n = len(unknown_nodes)
    idx = {name: i for i, name in enumerate(unknown_nodes)}
    A = [[0.0] * n for _ in range(n)]
    b = [0.0] * n

    def add(node, other, coeff):
        if node not in idx:
            return
        r = idx[node]
        if other in idx:
            A[r][idx[other]] += coeff
        else:
            A_val = fixed.get(other, 0.0)
            b[r] -= coeff * A_val

    for (d, s, g, gm, gds) in devices:
        add(d, g, gm)
        add(d, s, -gm - gds)
        add(d, d, gds)
        add(s, g, -gm)
        add(s, s, gm + gds)
        add(s, d, -gds)

    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(A[r][col]))
        if abs(A[piv][col]) < 1e-30:
            raise ValueError("singular MNA matrix")
        A[col], A[piv] = A[piv], A[col]
        b[col], b[piv] = b[piv], b[col]
        pv = A[col][col]
        for r in range(col + 1, n):
            f = A[r][col] / pv
            if f == 0.0:
                continue
            for c in range(col, n):
                A[r][c] -= f * A[col][c]
            b[r] -= f * b[col]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s_ = b[r] - sum(A[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s_ / A[r][r]
    return dict(zip(unknown_nodes, x))


def load_devs(names):
    trs, _ = load_topology(TOPO_JSON)
    by = {t.name: t for t in trs}
    return [by[n] for n in names]


def build_device_tuples(dev_objs, params, ac_ground, fixed_extra=()):
    out = []
    for t in dev_objs:
        gm, gds = params[t.name]
        out.append((t.drain, t.source, t.gate, gm, gds))
    return out


def full_model(params, vip, vim, vdd):
    devs = load_devs(STAGE1 + BATTERY_A + BATTERY_B)
    tuples = build_device_tuples(devs, params, AC_GROUND)
    nodes = []
    for t in devs:
        for n in (t.source, t.drain, t.gate):
            if n not in AC_GROUND and n not in ("Vip", "Vim", "vdd") and n not in nodes:
                nodes.append(n)
    fixed = {"gnd": 0.0, "Vbias1": 0.0, "Vbias2": 0.0, "Vbias3": 0.0, "Vbias4": 0.0,
              "Vcmfb": 0.0, "Vip": vip, "Vim": vim, "vdd": vdd}
    sol = mna_solve(tuples, nodes, fixed)
    return sol["Vop1"], sol["Vom1"]


def reduced_model(params, vip, vim, vdd):
    devs = load_devs(STAGE1)
    tuples = build_device_tuples(devs, params, AC_GROUND)
    nodes = []
    for t in devs:
        for n in (t.source, t.drain, t.gate):
            if n not in AC_GROUND and n not in ("Vip", "Vim", "vdd") and n not in nodes:
                nodes.append(n)
    # M10/M19 부하(gds) + M8/M17 직접주입(-gm*vdd)을 "가상 소자"로 추가:
    #   부하: (Vop1,gnd) 저항 1/gds10, (Vom1,gnd) 저항 1/gds19 -- gm=0,gds=params 그대로.
    #   주입: gate 대신 "vdd" 자체를 gm으로 매핑하는 가상소자 (D=Vop1,S=vdd,G=vdd,gm=0,gds=0)로는
    #   안 되므로, 그냥 KCL에 직접 상수항을 더하는 방식이 아니라 "M8 자체"를(S=vdd,D=Vop1,G=고정)
    #   가상 배치해 원래 stamp 공식을 그대로 쓴다: i = gm*(0-vdd)+gds*(vop1-vdd) -- gds8은
    #   leading order에서 버렸으므로 0으로 둔다(축약 모델의 정의 그대로).
    gm8, _ = params["M8"]
    gm17, _ = params["M17"]
    gds10 = params["M10"][1]
    gds19 = params["M19"][1]
    virt = [
        ("Vop1", "vdd", "vdd_fixed0", gm8, 0.0),   # M8 축약 주입(Vop1측)
        ("Vom1", "vdd", "vdd_fixed0", gm17, 0.0),  # M17 축약 주입(Vom1측)
        ("Vop1", "gnd", "gnd", 0.0, gds10),        # M10 부하
        ("Vom1", "gnd", "gnd", 0.0, gds19),        # M19 부하
    ]
    tuples += virt
    fixed = {"gnd": 0.0, "Vbias1": 0.0, "Vbias2": 0.0, "Vbias3": 0.0, "Vbias4": 0.0,
              "Vcmfb": 0.0, "Vip": vip, "Vim": vim, "vdd": vdd, "vdd_fixed0": 0.0}
    sol = mna_solve(tuples, nodes, fixed)
    return sol["Vop1"], sol["Vom1"]


def all_device_names():
    return STAGE1 + BATTERY_A + BATTERY_B


BASE_GM = {"M1a": 119e-6, "M1b": 119e-6, "M2a": 130e-6, "M2b": 130e-6,
           "M4a": 140e-6, "M4b": 140e-6, "M3a": 150e-6, "M3b": 150e-6,
           "M6": 60e-6, "M7": 25e-6, "M5": 0.0, "M8": 40e-6, "M17": 40e-6,
           "M9a": 50e-6, "M9b": 50e-6, "M18a": 50e-6, "M18b": 50e-6,
           "M11a": 30e-6, "M11b": 30e-6, "M20a": 30e-6, "M20b": 30e-6,
           "M12": 0.0, "M21": 0.0, "M10": 0.0, "M19": 0.0,
           "M13": 40e-6, "M22": 40e-6, "M14a": 30e-6, "M14b": 30e-6,
           "M23a": 30e-6, "M24b": 30e-6}
BASE_GDS = {"M1a": 1 / 600e3, "M1b": 1 / 600e3, "M2a": 1 / 700e3, "M2b": 1 / 700e3,
            "M4a": 1 / 250e3, "M4b": 1 / 250e3, "M3a": 1 / 300e3, "M3b": 1 / 300e3,
            "M6": 0.5e-6, "M7": 0.4e-6, "M5": 1.0e-6, "M8": 0.3e-6, "M17": 0.3e-6,
            "M9a": 0.4e-6, "M9b": 0.4e-6, "M18a": 0.4e-6, "M18b": 0.4e-6,
            "M11a": 0.5e-6, "M11b": 0.5e-6, "M20a": 0.5e-6, "M20b": 0.5e-6,
            "M12": 0.6e-6, "M21": 0.6e-6, "M10": 0.6e-6, "M19": 0.6e-6,
            "M13": 0.3e-6, "M22": 0.3e-6, "M14a": 0.5e-6, "M14b": 0.5e-6,
            "M23a": 0.5e-6, "M24b": 0.5e-6}


def rand_params(seed):
    random.seed(seed)
    p = {}
    for n in all_device_names():
        gm = BASE_GM[n] * (math.exp(random.uniform(-math.log(4), math.log(4))) if BASE_GM[n] else 0.0)
        gds = BASE_GDS[n] * math.exp(random.uniform(-math.log(4), math.log(4)))
        p[n] = (gm, gds)
    return p


def main():
    print("PSRR(open-loop, battery 포함) FULL(31소자) vs REDUCED(11+M10/M19+M8/M17축약) 비교")
    worst = 0.0
    for i in range(20):
        p = rand_params(i)
        vop1_f, vom1_f = full_model(p, 0, 0, 1.0)
        ann_f = (vop1_f + vom1_f) / 2
        vop1_r, vom1_r = reduced_model(p, 0, 0, 1.0)
        ann_r = (vop1_r + vom1_r) / 2

        # Adm은 vdd=0, DM 여기(둘 다 동일 stage1이라 같은 값이어야 함 -- 참고용)
        vop1_fd, vom1_fd = full_model(p, 0.5, -0.5, 0)
        adm_f = vop1_fd - vom1_fd
        vop1_rd, vom1_rd = reduced_model(p, 0.5, -0.5, 0)
        adm_r = vop1_rd - vom1_rd

        db_f = 20 * math.log10(abs(adm_f / ann_f))
        db_r = 20 * math.log10(abs(adm_r / ann_r))
        err = abs(db_r - db_f)
        worst = max(worst, err)
        adm_diff = abs(adm_r / adm_f - 1)
        print(f"  rand{i:<2d} PSRR FULL={db_f:9.4f}dB  REDUCED={db_r:9.4f}dB (err={db_r-db_f:+.4f})"
              f"   Adm rel diff(FULL vs REDUCED, stage1 loading만 있으면 같아야함)={adm_diff:.4f}")
    print(f"WORST |REDUCED - FULL| PSRR(dB) = {worst:.4f}")


if __name__ == "__main__":
    main()
