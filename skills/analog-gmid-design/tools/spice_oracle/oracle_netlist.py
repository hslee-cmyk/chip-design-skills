# -*- coding: utf-8 -*-
"""oracle_netlist.py -- SPICE 오라클 입력(JSON, oracle_input.schema.json) -> ngspice 넷리스트.

진입점(단독 실행):
    python oracle_netlist.py <oracle_input.json> <out.cir> --bias free|forced|iso
                             [--topology T] [--require-topology] [--omit N ...] [--short N ...]

  넷리스트(.cir)와 그 메타(<out.cir>.meta.json: 소자 probe 이름, 넷 목록, 고정한 넷, 경고/막힘)를 쓴다.
  ngspice 는 부르지 않는다(oracle_simulate.py 몫).

공개 함수: build_netlist(inp, bias, ac_file, loop=False|True|CM_LOOP) -> (text, meta), cm_loop_break_nets(inp), cm_loop_moved(inp, breaks), cm_loop_blockers(inp, breaks), write_netlists(inp, bias, out_cir, ...) -> meta,
          validate_input(inp) -> [위반], loop_break_nets(inp), load_input(path), read_lut_meta(npz_path),
          parse_netlist_elements(text, inp), topology_elements(topo), topology_identity(inp, text, path),
          resolve_topology_path(inp, input_path, override), apply_z1(inp, omit, short),
          diffusion_of(process, d), diffusion_gate(geometry, bias), ratio_views(inp),
          rout_views(inp), sense_key(view), excitation_weight_check(inp), dc_path_isolation(tb, inputs, fb),
          [신규 C10] stability_op_netlist(text, nodes), stability_netlist(text, mode, weights, output_nodes, plan)
          -- PM 안정성 근거용 동작점 패스·폐루프 .tran 넷리스트(본·루프 넷리스트 텍스트는 바꾸지 않는다)
  * [신규 C10] meta.outputs·output_nodes·tb_options(폐루프 .tran 이 쓴다).
  * [신규] C26 rout_ohm: 뷰마다 감지 넷에 Irout_<k>(DC 0, AC 0) 전류원을 두고 .control 안에서 모든 여기 원 acmag 0,
    그 뷰의 Irout 만 acmag 1 로 .ac 한 점(fstart).
  * [신규] C27: A 크기를 쓰는 measure 가 있으면 입력 AC 진폭이 정의값(차동 ±1/2, 단일 1)인지 검사(아니면 막힘),
    choke·결합 C 유효 조건은 meta.dc_path_isolation 에 기록만. [C14 보강] 두 단자가 모두 입력 포트 넷인 되먹임 소자는 막힘.
입력은 먼저 oracle_input.schema.json 으로 검증한다. 위반이면 넷리스트를 쓰지 않고 반환 2(README C13).
  * [신규] C15 topology 연결 동일성: 본 넷리스트를 다시 파싱한 (원소 이름, 종류, 단자 넷) 집합을 topology JSON
    (netlist + passive_elements + ideal_sources)과 비교한다. 다르면 막힘. topology 가 없으면 '미검증' 표시,
    --require-topology(합격 실행)이면 막힘.
  * [신규] bias=iso: 소자마다 단독 인스턴스를 엔진 예측 VGS·VDS·VSB 에 고정(models[kind].polarity 필요).
  * [신규] Z1 제거법: --omit(원소 제거)·--short(수동소자를 0 V 전압원으로 단락). 진단 실행 -- 합격 판정 안 함.

규칙(값은 전부 입력에서 온다 -- 이 파일은 회로·소자·공정 이름과 수치 상수를 갖지 않는다)
  * 코너·온도: process.lut_npz 의 메타(corner, temp_c). include 경로의 '{corner}' 자리를 npz corner 로 채우고
    `.temp` 는 npz temp_c. npz 에 메타가 없으면 막힘.
  * finger: 소자 하나 = 인스턴스 하나, `w=finger_w m=n_fingers`. nf 는 쓰지 않는다(ngspice 는 모델 bin 을
    총폭 w 로 고르고 BSIM4 크기식은 w/nf 로 계산해, nf>1 이면 다른 bin 계수를 외삽한다 -- lut_coverage_study 표 E).
    subckt 의 m 은 내부 소자를 m 배 하고 @ probe 값(id/gm/gds)도 m 배 총합으로 나온다(2026-10-07 실측).
  * 확산 면적(C22): devices[].diffusion(Euler 행 공유 확산, finger 평균) -> process.diffusion(LUT 생성 규칙
    ad=as=ad_per_w_m*finger_w, pd=ps=finger_w+pd_extra_m) -> 생략. free(합격 실행)에서 생략되는 소자가 있으면 막힘.
  * [신규] C24 ratio_db(CMRR·PSRR): 뷰마다 .control 안에서 여기 원 acmag 를 바꿔 .ac 2회(fstart 한 점), wrdata.
  * bias=free : 회로가 DC 해를 스스로 찾는다. 입력 DC 는 dc_choke_H 로, AC 는 ac_couple_F 로 넣고
    출력 -> 반대 극성 입력 DC 되먹임으로 출력 DC 를 예측값 근처에 묶는다(차동 출력은 차동 성분만).
    testbench.nodeset_from_predictions 이면 예측 노드전압을 .nodeset(뉴턴 초기값)으로 준다.
  * bias=forced: 예측 전압이 있는 모든 소자 단자 넷을 dc_choke_H 로 예측값에 묶는다. DC = 엔진이 의도한
    바이어스, 각 고정원 전류 = 그 넷의 KCL 잔차, AC 에서는 choke 가 열려 실제 모델의 개루프 응답.
  * 구동 소자 없는 게이트 전용 넷: bias_voltages 선언값, 없으면 예측 노드전압의 이상 전압원(경고로 남김).
"""
import argparse
import json
import os
import sys

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oracle_input.schema.json")
OP_PARAMS = ("id", "gm", "gds", "vth", "vdsat", "vgs", "vds", "vbs")  # BSIM 동작점 파라미터 이름
BIASES = ("free", "forced", "iso")
# 넷리스트 원소 이름 접두사. 회로 원소(topology 대조 대상)와 테스트벤치 원소(대조 제외)를 이 표로만 가른다(C15).
CIRCUIT_PREFIXES = {"X": "device", "Rp_": "resistor", "Cp_": "capacitor", "Isrc_": "current", "Vsrc_": "voltage"}
TESTBENCH_PREFIXES = ("Vrail_", "Efb_", "Vofs_", "Lfb_", "Vdc_", "Ldc_", "Cac_", "Vac_", "Vbias_", "Vhold_", "Lhold_",
                      "Vlb_", "Ilb_", "Vshort_", "Viso_", "Irout_")
# 테스트벤치 DC 경로 choke(인덕터) 접두사 -- [신규 C10 안정성] 폐루프 .tran 넷리스트에서 동작점 전류원 + .ic 로 바뀐다
CHOKE_PREFIXES = ("Lfb_", "Ldc_", "Lhold_")
# C27: 개루프 A 의 크기를 쓰는 measure(입력 AC 진폭에 비례하는 값). f3db_hz 는 배율 무관이라 빠진다.
A_SCALED_MEASURES = ("dc_gain_db", "ugf_hz", "pm_deg")
# topology ideal_sources 의 kind 어휘 -> 오라클 sources[].kind 어휘(같은 뜻의 두 이름)
TOPOLOGY_SOURCE_KINDS = {"current_source": "current", "voltage_source": "voltage", "current": "current",
                         "voltage": "voltage"}


def load_input(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_lut_meta(npz_path):
    import numpy as np
    z = np.load(npz_path)
    meta = {}
    for k in ("corner", "temp_c"):
        meta[k] = z[k].item() if k in z.files else None
    return meta


def _num(v):
    return format(float(v), ".10g")


class _Nets:
    """넷 이름 -> SPICE 노드 이름. 기준 레일은 '0'. ngspice 는 대소문자를 가리지 않으므로 충돌을 막힘으로 보고."""

    def __init__(self, rails):
        refs = [r["net"] for r in rails if r.get("reference")]
        self.ref = set(refs)
        self.rail_v = {r["net"]: float(r["voltage"]) for r in rails}
        self.seen = {}
        self.blockers = []
        if len(refs) != 1:
            self.blockers.append(f"rails 에 reference=true 가 정확히 1개여야 한다(지금 {len(refs)}개)")

    def __call__(self, net):
        if net in self.ref:
            return "0"
        low = net.lower()
        prev = self.seen.setdefault(low, net)
        if prev != net:
            same_rail = (prev in self.rail_v and net in self.rail_v and self.rail_v[prev] == self.rail_v[net])
            if not same_rail:
                msg = f"넷 '{prev}' 와 '{net}' 이 대소문자만 다르다(ngspice 에서 같은 노드가 된다)"
                if msg not in self.blockers:
                    self.blockers.append(msg)
        return net


def _includes(process, kinds, corner):
    out = []
    seen = set()
    for kind in sorted(kinds):
        for tpl in process["models"][kind]["includes"]:
            p = tpl.replace("{corner}", str(corner))
            if p not in seen:
                seen.add(p)
                out.append(f'.include "{p}"')
    return out


def probe_name(process, kind, inst, param):
    """ngspice @ 표현. models[kind].op_probe 의 {inst}(소문자 인스턴스 이름), {param} 을 채운다."""
    return process["models"][kind]["op_probe"].replace("{inst}", inst.lower()).replace("{param}", param)


def diffusion_of(process, d):
    """소자 d 의 확산 기하(C22). 출처 순서: devices[].diffusion(Euler 행 공유 확산, finger 평균) -> process.diffusion
    (LUT 생성 규칙) -> 없음. 반환 {source: 'device'|'process_rule'|None, ad, as, pd, ps}(값은 m 단위 하나당, m 은 ngspice 가 곱함)."""
    own = d.get("diffusion")
    if own:
        return {"source": "device", "ad": float(own["ad_m2"]), "as": float(own["as_m2"]),
                "pd": float(own["pd_m"]), "ps": float(own["ps_m"])}
    dif = process.get("diffusion")
    if dif:
        fw = float(d["finger_w"])
        ad = float(dif["ad_per_w_m"]) * fw
        pd = fw + float(dif["pd_extra_m"])
        return {"source": "process_rule", "ad": ad, "as": ad, "pd": pd, "ps": pd}
    return {"source": None, "ad": None, "as": None, "pd": None, "ps": None}


def device_line(process, d, nodes):
    m = process["models"][d["kind"]]
    fw = float(d["finger_w"])
    parts = [f"X{d['name']}", nodes[0], nodes[1], nodes[2], nodes[3], m["subckt"],
             f"l={_num(d['L'])}", f"w={_num(fw)}", f"m={int(d['n_fingers'])}"]
    dif = diffusion_of(process, d)
    if dif["source"]:
        parts += [f"{k}={_num(dif[k])}" for k in ("ad", "as", "pd", "ps")]
    return " ".join(parts)


def diffusion_gate(geometry, bias):
    """C22: 확산 기하가 없는 소자 목록 -> (막힘 목록, 노트 목록). free(합격 실행)만 막힘, 나머지는 노트."""
    missing = sorted(n for n, g in geometry.items() if not (g.get("diffusion") or {}).get("source"))
    if not missing:
        return [], []
    msg = f"C22 접합 용량: 확산 기하 없는 소자 {missing} (devices[].diffusion 도 process.diffusion 도 없음)"
    if bias == "free":
        return [msg + " -- 합격 실행(free)은 접합 용량을 넣어야 한다"], []
    return [], [msg + f" -- {bias} 진단 실행이라 막지 않음(그 소자는 접합 용량 없음)"]


def ratio_views(inp):
    """C24: 제약·metric 중 measure == ratio_db 인 항목의 view 목록(dict 동등 기준 중복 제거, 처음 나온 순서)."""
    out = []
    items = list((inp.get("acceptance") or {}).get("constraints") or []) + \
        list((inp.get("predictions") or {}).get("metrics") or [])
    for it in items:
        if it.get("measure") == "ratio_db" and it.get("view") is not None and it["view"] not in out:
            out.append(it["view"])
    return out


def sense_key(view):
    """C26: 감지 전용 뷰의 정규형 (sense_p, sense_n 또는 None, sense_mode). sense_n 이 없는 것과 null 은 같은 뷰다."""
    return (view.get("sense_p"), view.get("sense_n"), view.get("sense_mode"))


def rout_views(inp):
    """C26: 제약·metric 중 measure == rout_ohm 인 항목의 view 목록(sense_key 기준 중복 제거, 처음 나온 순서).
    반환 원소 = {sense_p, sense_n(없으면 None), sense_mode}."""
    out, seen = [], set()
    items = list((inp.get("acceptance") or {}).get("constraints") or []) + \
        list((inp.get("predictions") or {}).get("metrics") or [])
    for it in items:
        if it.get("measure") != "rout_ohm" or it.get("view") is None:
            continue
        k = sense_key(it["view"])
        if k not in seen:
            seen.add(k)
            out.append({"sense_p": k[0], "sense_n": k[1], "sense_mode": k[2]})
    return out


def excitation_weight_check(inp):
    """C27: 개루프 A 의 크기를 쓰는 measure(A_SCALED_MEASURES)가 metric·제약에 있으면 입력 AC 진폭이 정의값이어야 한다 --
    차동 입력(input_p·input_n): input_p_ac - input_n_ac == 1 이고 input_p_ac + input_n_ac == 0(v_id = 1, v_cm = 0, 즉 ±1/2),
    단일 입력(input): input_ac == 1. 같은 키가 β 루프 절단 가중이다(README 'PM 정의'). 값이 없으면 여기서는 보지 않는다
    (C11 이 막는다). 반환 막힘 목록. 정의값(0·1) 검사이지 숫자 기본값이 아니다(C11 과 충돌 없음)."""
    items = list((inp.get("acceptance") or {}).get("constraints") or []) + \
        list((inp.get("predictions") or {}).get("metrics") or [])
    used = sorted({it.get("measure") for it in items if it.get("measure") in A_SCALED_MEASURES})
    if not used:
        return []
    ports, ac = inp["ports"], (inp["testbench"].get("ac") or {})
    if ports.get("input_p") and ports.get("input_n"):
        p, n = ac.get("input_p_ac"), ac.get("input_n_ac")
        if p is None or n is None or (p - n == 1 and p + n == 0):
            return []
        return [f"C27 가중 정의: 차동 입력은 input_p_ac - input_n_ac == 1, input_p_ac + input_n_ac == 0 이어야 한다"
                f"(v_id = 1, v_cm = 0) -- 지금 input_p_ac={p!r}, input_n_ac={n!r} (measure {used})"]
    if ports.get("input"):
        v = ac.get("input_ac")
        if v is None or v == 1:
            return []
        return [f"C27 가중 정의: 단일 입력은 input_ac == 1 이어야 한다 -- 지금 {v!r} (measure {used})"]
    return []


def validate_input(inp, schema_path=SCHEMA_PATH):
    """oracle_input.schema.json 위반 목록(빈 목록이면 통과). 위반 입력은 진입점이 거부한다(README C13)."""
    import jsonschema
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    v = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(str(x) for x in e.absolute_path) or '(최상위)'}: {e.message}"
            for e in sorted(v.iter_errors(inp), key=lambda e: list(map(str, e.absolute_path)))]


def loop_break_nets(inp):
    """β 루프를 끊을 넷 = 선언된 되먹임 수동소자(feedback_passives)가 물린 입력 포트 넷. (넷 목록, 막힘 목록)."""
    names = inp.get("feedback_passives") or []
    if not names:
        return [], []
    ports = inp["ports"]
    in_nets = [ports[k] for k in ("input_p", "input_n", "input") if ports.get(k)]
    by = {p["name"]: p for p in inp.get("passives") or []}
    # 소자 단위 판정(fail-closed): 선언된 되먹임 수동소자 각각이 passives 에 있고 입력 포트 넷에 물려 있어야 한다.
    blockers = [f"feedback_passives 의 {n} 이 passives 에 없다" for n in names if n not in by]
    blockers += [f"feedback_passives 의 {n} 이 입력 포트 넷 {in_nets} 에 물려 있지 않다(단자 {by[n]['terminals']})"
                 for n in names if n in by and not set(by[n]["terminals"]) & set(in_nets)]
    # [C14 보강] 절단 단자는 정확히 1개: 두 단자가 모두 입력 포트 넷이면 어느 쪽을 떼는지 정해지지 않는다(엔진 feedback_cut_ambiguous)
    blockers += [f"feedback_passives 의 {n} 은 두 단자 {by[n]['terminals']} 가 모두 입력 포트 넷이다 -- 절단 단자가 "
                 f"하나로 정해지지 않는다(엔진 feedback_cut_ambiguous 와 같은 조건)"
                 for n in names if n in by and sum(t in in_nets for t in by[n]["terminals"]) == 2]
    nets =[n for n in in_nets if any(n in by[x]["terminals"] for x in names if x in by)]
    if not nets:
        blockers.append("feedback_passives 가 어느 입력 포트 넷에도 물려 있지 않다")
    return nets, blockers


CM_LOOP = "cm"      # build_netlist(loop=CM_LOOP): 공통 모드 루프(출력 포트 CM 주입) 넷리스트
def cm_loop_break_nets(inp):
    """[CM] 공통 모드 루프를 끊는 곳 = 선언된 차동 출력 포트 쌍(ports.output_p·output_n) -- 두 출력 넷에 동일 부호 Middlebrook 주입(엔진
    cm_loop 뷰 `cm_output` 과 같은 정의). 입력 `cm_output_loop` 가 있을 때만. (넷 목록, 막힘 목록)."""
    if not inp.get("cm_output_loop"):
        return [], []
    ports = inp["ports"]
    if not (ports.get("output_p") and ports.get("output_n")):
        return [], ["cm_output_loop: ports 에 차동 출력 output_p/output_n 이 없다"]
    return [ports["output_p"], ports["output_n"]], []


def cm_loop_moved(inp, breaks):
    """[CM] 출력 넷에서 새 노드 lbx 로 옮길 구동자 단자: 입력 `cm_output_loop.drivers`(엔진 cm_partition 이 정한 구동자 MOS) 각각의 출력 넷 쪽 channel 단자.
    {소자 이름: "drain" | "source"}. 소비자(수동소자·gate·감지망 MOS)는 n 쪽에 남는다. 소자가 없거나 channel 단자가 출력 넷에 정확히 하나가 아니면 KeyError 대신
    빈 항목 없이 막힘을 만들도록 `cm_loop_blockers` 가 따로 알린다."""
    b = set(breaks)
    by = {d["name"]: d for d in inp["devices"]}
    out = {}
    for name in (inp.get("cm_output_loop") or {}).get("drivers") or []:
        d = by.get(name)
        ends = [] if d is None else [t for t in ("drain", "source") if d[t] in b]
        if len(ends) == 1:
            out[name] = ends[0]
    return out


def cm_loop_blockers(inp, breaks):
    """[CM] cm_output_loop.drivers 검사: 소자가 devices 에 있고 drain·source 중 정확히 하나가 출력 넷이어야 한다. 막힘 목록."""
    moved = cm_loop_moved(inp, breaks)
    return [f"cm_output_loop.drivers 의 {n} 이 devices 에 없거나 drain·source 중 정확히 하나가 출력 넷 {sorted(breaks)} 이 아니다"
            for n in (inp.get("cm_output_loop") or {}).get("drivers") or [] if n not in moved]


def build_netlist(inp, bias, ac_file, loop=False):
    """loop=False: 본 넷리스트(.op + 개루프 A 의 .ac). loop=True: β 루프 이득 측정용 넷리스트
    (되먹임 수동소자의 입력 쪽 단자를 lbx_<넷> 으로 떼고 직렬 전압원 Vlb·주입 전류원 Ilb 를 넣어 .ac 2회 --
    Middlebrook 이중 주입). loop=True 에서 ac_file 은 두 데이터 파일 이름의 접두사."""
    if bias not in BIASES:
        raise ValueError(f"bias 는 {'|'.join(BIASES)}: {bias!r}")
    if bias == "iso":
        return build_iso_netlist(inp)
    process, tb = inp["process"], inp["testbench"]
    pred = (inp.get("predictions") or {}).get("nodes") or {}
    lut = read_lut_meta(process["lut_npz"])
    blockers, notes = [], []
    for k in ("corner", "temp_c"):
        if lut[k] is None:
            blockers.append(f"LUT npz 에 {k} 메타가 없다: {process['lut_npz']}")
    blockers += excitation_weight_check(inp)
    cm = loop == CM_LOOP
    cm_moved = cm_loop_moved(inp, cm_loop_break_nets(inp)[0]) if cm else {}
    N = _Nets(inp["rails"])
    devs = inp["devices"]
    kinds = {d["kind"] for d in devs}
    choke, coup = _num(tb["dc_choke_H"]), _num(tb["ac_couple_F"])

    L = [f"* spice_oracle: {inp.get('circuit', '?')} bias={bias}"]
    L += _includes(process, kinds, lut["corner"])
    if lut["temp_c"] is not None:
        L.append(f".temp {_num(lut['temp_c'])}")
    if tb.get("options"):
        L.append(".option " + " ".join(f"{k}={v}" for k, v in tb["options"].items()))
    rail_src = {}
    for r in inp["rails"]:
        if r.get("reference"):
            continue
        nm = f"Vrail_{r['net']}"
        rail_src[r["net"]] = nm
        L.append(f"{nm} {N(r['net'])} 0 DC {_num(r['voltage'])}")
    rail_nets = set(N.rail_v)

    driven, dev_nets, geometry, probes = set(), [], {}, {}
    for d in devs:
        nodes = [N(d[t]) for t in ("drain", "gate", "source", "bulk")]
        if cm and d["name"] in cm_moved:      # [CM] 출력 넷에 channel 단자가 물린 MOS 는 그 단자를 구동자 쪽(lbx)에 둔다
            slot = 0 if cm_moved[d["name"]] == "drain" else 2
            nodes[slot] = f"lbx_{d[cm_moved[d['name']]]}"
        L.append(device_line(process, d, nodes))
        driven.update([d["drain"], d["source"]])
        for t in ("drain", "gate", "source", "bulk"):
            if d[t] not in dev_nets:
                dev_nets.append(d[t])
        W_f = float(d["finger_w"]) * int(d["n_fingers"])
        geometry[d["name"]] = {"L": float(d["L"]), "finger_w": float(d["finger_w"]),
                               "n_fingers": int(d["n_fingers"]), "W_from_fingers": W_f,
                               "W_declared": None if d.get("W") is None else float(d["W"]),
                               "diffusion": diffusion_of(process, d)}
        probes[d["name"]] = {p: probe_name(process, d["kind"], f"X{d['name']}", p) for p in OP_PARAMS}
    dg_block, dg_note = diffusion_gate(geometry, bias)
    blockers += dg_block
    notes += dg_note

    for s in inp.get("sources") or []:
        a, b = s["terminals"]
        driven.update([a, b])
        letter = {"current": "I", "voltage": "V"}.get(s["kind"])
        if letter is None:
            blockers.append(f"source {s['name']} kind={s['kind']} 미지원")
            continue
        L.append(f"{letter}src_{s['name']} {N(a)} {N(b)} DC {_num(s['value'])}")
        notes.append(f"{s['kind']} source {s['name']}={_num(s['value'])} ({s.get('value_basis', '근거 미기재')})")

    if cm:      # 공통 모드 루프: 끊는 곳은 차동 출력 포트 쌍 -- 입력은 전부 AC 접지(Vac AC 0)
        breaks, bb = cm_loop_break_nets(inp)
        fbp = set()                       # [CM] 수동소자는 옮기지 않는다
        bb = bb + cm_loop_blockers(inp, breaks)
        driven.update(breaks)
    else:
        breaks, bb = loop_break_nets(inp) if loop else ([], [])
        fbp = set(inp.get("feedback_passives") or [])
    blockers += bb
    passive_nets = []
    for p in inp.get("passives") or []:
        a, b = p["terminals"]
        if loop and p["name"] in fbp:
            a, b = (f"lbx_{a}" if a in breaks else a), (f"lbx_{b}" if b in breaks else b)
        driven.update([a, b])
        if p["kind"] == "short":  # Z1 제거법 --short: 0 V 전압원으로 단락(apply_z1 이 만든 원소)
            L.append(f"Vshort_{p['name']} {N(a)} {N(b)} DC 0")
            notes.append(f"Z1 --short: {p['name']} 을 0 V 전압원으로 단락")
            for n in (a, b):
                if n not in dev_nets and n not in passive_nets:
                    passive_nets.append(n)
            continue
        letter = {"resistor": "R", "capacitor": "C"}.get(p["kind"])
        if letter is None:
            blockers.append(f"passive {p['name']} kind={p['kind']} 미지원")
            continue
        L.append(f"{letter}p_{p['name']} {N(a)} {N(b)} {_num(p['value'])}")
        notes.append(f"{p['kind']} {p['name']}={_num(p['value'])} ({p.get('value_basis', '근거 미기재')})")
        for n in (a, b):
            if n not in dev_nets and n not in passive_nets:
                passive_nets.append(n)

    ports = inp["ports"]
    inp_p, inp_n = ports.get("input_p"), ports.get("input_n")
    out_p, out_n, out_se = ports.get("output_p"), ports.get("output_n"), ports.get("output")
    in_se = ports.get("input")
    inputs = [x for x in (inp_p, inp_n, in_se) if x]
    if not inputs:
        blockers.append("ports 에 input_p/input_n 또는 input 이 없다")
    if not (out_se or (out_p and out_n)):
        blockers.append("ports 에 output 또는 output_p/output_n 이 없다")
    # 입력 DC + AC
    fb = {}
    if bias == "free" and inp_p and inp_n:
        if out_se:
            fb[inp_n] = ("se", out_se)
        elif out_p and out_n:
            fb[inp_n] = ("diff", out_p, out_n)
            fb[inp_p] = ("diff", out_n, out_p)
    ac_mag = {}
    need = {inp_p: "input_p_ac", inp_n: "input_n_ac"} if (inp_p and inp_n) else ({in_se: "input_ac"} if in_se else {})
    for net, key in need.items():
        if tb["ac"].get(key) is None:
            blockers.append(f"testbench.ac.{key} 없음 -- 입력 {net} 의 AC 크기를 정할 수 없다")
        else:
            ac_mag[net] = tb["ac"][key]
    # C24 여기 수단: 테스트벤치가 이상 전압원으로 구동하는 넷 -> 그 원 이름(레일·입력 Vac·게이트 바이어스)
    ac_src = dict(rail_src)
    loop_choke = None
    if loop and breaks and not cm:
        if tb.get("loop_dc_choke_H") is None:
            blockers.append("testbench.loop_dc_choke_H 없음 -- β 루프 측정의 입력 DC 경로를 정할 수 없다")
        else:
            loop_choke = _num(tb["loop_dc_choke_H"])
    for net in inputs:
        driven.add(net)
        ch = loop_choke if (loop and net in breaks and loop_choke) else choke
        vin = pred.get(net)
        if vin is None:
            blockers.append(f"입력 {net} 의 예측 DC 전압 없음(predictions.nodes)")
            continue
        if net in fb and fb[net][0] == "diff":
            _, o, o_other = fb[net]
            if tb["ac"].get("diff_feedback_gain") is None:
                blockers.append("testbench.ac.diff_feedback_gain 없음 -- free 차동 되먹임을 만들 수 없다")
                continue
            L.append(f"Efb_{net} fbs_{net} 0 {N(o)} {N(o_other)} {_num(tb['ac']['diff_feedback_gain'])}")
            L.append(f"Vofs_{net} fbs_{net} fbd_{net} DC {_num(-vin)}")
            L.append(f"Lfb_{net} fbd_{net} {N(net)} {ch}")
            notes.append(f"free: 차동 DC 되먹임 k*(V({o})-V({o_other})) -> {net}, 입력 공통모드 {vin:.6g} V(예측)")
        elif net in fb:
            o = fb[net][1]
            vo = pred.get(o)
            if vo is None:
                blockers.append(f"출력 {o} 예측 DC 전압 없음 -- 되먹임 오프셋을 정할 수 없다")
                continue
            L.append(f"Efb_{net} fbs_{net} 0 {N(o)} 0 1")
            L.append(f"Vofs_{net} fbs_{net} fbd_{net} DC {_num(vo - vin)}")
            L.append(f"Lfb_{net} fbd_{net} {N(net)} {ch}")
            notes.append(f"free: DC 되먹임 {o} -> {net} (V({o})_pred={vo:.6g}, V({net})_pred={vin:.6g})")
        else:
            L.append(f"Vdc_{net} dcs_{net} 0 DC {_num(vin)}")
            L.append(f"Ldc_{net} dcs_{net} {N(net)} {ch}")
        if net in breaks:
            L.append(f"Vlb_{net} {N(net)} lbx_{net} DC 0 AC {_num(ac_mag.get(net, 0))}")
            L.append(f"Ilb_{net} 0 {N(net)} DC 0 AC 0")
        else:
            L.append(f"Cac_{net} {N(net)} acs_{net} {coup}")
            L.append(f"Vac_{net} acs_{net} 0 DC 0 AC {_num(0 if loop else ac_mag.get(net, 0))}")
            ac_src[net] = f"Vac_{net}"

    if cm and breaks:   # 절단 직렬 전압원(구동자 쪽 +)과 구동자 쪽 주입 전류원 -- DM 루프와 같은 Middlebrook 이중 주입, 두 출력에 동일 부호 가중
        ac_mag = {net: 1 / len(breaks) for net in breaks}
        for net in breaks:
            L.append(f"Vlb_{net} {N(net)} lbx_{net} DC 0 AC {_num(ac_mag[net])}")
            L.append(f"Ilb_{net} 0 {N(net)} DC 0 AC 0")

    # 게이트 전용 넷
    declared_bias = {b["net"]: float(b["value"]) for b in inp.get("bias_voltages") or []}
    gate_bias = {}
    for d in devs:
        g = d["gate"]
        if g in driven or g in rail_nets or g in gate_bias:
            continue
        if g in declared_bias:
            gate_bias[g] = (declared_bias[g], "bias_voltages 선언")
        elif pred.get(g) is not None:
            gate_bias[g] = (float(pred[g]), "예측 노드전압(선언 없음 -- 자동)")
        else:
            blockers.append(f"구동 소자 없는 게이트 넷 {g}: bias_voltages 선언도 예측 전압도 없다")
            continue
        L.append(f"Vbias_{g} {N(g)} 0 DC {_num(gate_bias[g][0])}")
        ac_src[g] = f"Vbias_{g}"
    for net, (v, why) in gate_bias.items():
        notes.append(f"게이트 전용 넷 {net} = {v:.6g} V ({why})")

    held, unheld = [], []
    if bias == "forced":
        for n in dev_nets:
            if n in rail_nets or n in gate_bias or n in inputs:
                continue
            v = pred.get(n)
            if v is None:
                unheld.append(n)
                continue
            L.append(f"Vhold_{n} hs_{n} 0 DC {_num(v)}")
            L.append(f"Lhold_{n} hs_{n} {N(n)} {choke}")
            held.append(n)
        notes.append(f"forced: 소자 단자 넷 {len(held)}개를 예측 전압에 choke 로 고정")
        if unheld:
            notes.append(f"forced: 예측 전압이 없어 고정 못 한 넷(자유): {unheld}")
    elif tb.get("nodeset_from_predictions"):
        ns = [f"v({N(n)})={_num(pred[n])}" for n in dev_nets + passive_nets
              if n not in rail_nets and n not in gate_bias and pred.get(n) is not None]
        step = max(1, int(tb.get("nodeset_per_line", len(ns) or 1)))
        for i in range(0, len(ns), step):
            L.append(".nodeset " + " ".join(ns[i:i + step]))
        notes.append(f"free: .nodeset {len(ns)}개 = 예측 노드전압(뉴턴 초기값)")

    all_nets = [n for n in dev_nets + passive_nets if N(n) != "0"]
    if loop:
        return _loop_tail(L, tb, breaks, ac_mag, ac_file, N, notes, blockers, bias, lut, loop_choke)
    rout_plan = _rout_plan(inp, ac_src, all_nets, N, blockers)
    for k, view in enumerate(rout_plan):  # C26 감지 전류원(DC 0, AC 0 -- 자기 .ac 에서만 alter 로 1)
        L.append(f"Irout_{k} 0 {N(view['sense_p'])} DC 0 AC 0")
        if view["sense_mode"] == "differential":
            L.append(f"Irout_{k}n {N(view['sense_n'])} 0 DC 0 AC 0")
    L.append(".control")
    L.append("set noaskquit")
    L.append("op")
    L.append("echo OPSTART")
    for d in devs:
        for p in OP_PARAMS:
            L.append(f"print {probes[d['name']][p]}")
    for n in all_nets:
        L.append(f"print v({N(n)})")
    for net, nm in rail_src.items():
        L.append(f"print i({nm.lower()})")
    for n in held:
        L.append(f"print i(vhold_{n.lower()})")
    L.append("echo OPEND")
    has_ac = bool(inputs) and bool(out_se or (out_p and out_n))
    if has_ac:
        ac = tb["ac"]
        miss = [k for k in ("points_per_decade", "fstart_hz", "fstop_hz") if ac.get(k) is None]
        if miss:
            blockers.append(f"testbench.ac 에 {miss} 없음")
            ac = {k: ac.get(k) or 0 for k in ("points_per_decade", "fstart_hz", "fstop_hz")}
        L.append(f"ac dec {int(ac['points_per_decade'])} {_num(ac['fstart_hz'])} {_num(ac['fstop_hz'])}")
        L.append(f"let hout = v({N(out_se)})" if out_se else f"let hout = v({N(out_p)}) - v({N(out_n)})")
        L.append("set wr_singlescale")
        L.append(f"wrdata {ac_file} hout")
    ratio_runs = _ratio_runs(L, inp, ac_src, all_nets, N, ac_file, blockers)
    rout_runs = _rout_runs(L, rout_plan, inp, ac_src, N, ac_file)
    L.append("quit")
    L.append(".endc")
    L.append(".end")
    blockers = N.blockers + blockers
    outs = [out_se] if out_se else ([out_p, out_n] if (out_p and out_n) else [])
    meta = {"bias": bias, "lut_meta": lut, "geometry": geometry, "probes": probes, "nets": all_nets,
            "spice_node": {n: N(n) for n in all_nets}, "rail_sources": rail_src, "held": held,
            "unheld": unheld, "gate_bias": {k: v[0] for k, v in gate_bias.items()},
            "inputs": inputs, "has_ac": has_ac, "ac_file": ac_file if has_ac else None,
            # [신규 C10 안정성] 출력 넷과 그 SPICE 노드 쌍(차동이면 (p, n), 단일이면 (out, 0)), 테스트벤치 .option
            "outputs": outs, "output_nodes": [N(outs[0]), N(outs[1]) if len(outs) == 2 else "0"] if outs else [],
            "tb_options": dict(tb.get("options") or {}),
            "ratio_runs": ratio_runs, "rout_runs": rout_runs, "input_ac_weights": dict(ac_mag),
            "dc_path_isolation": dc_path_isolation(tb, inputs, fb),
            "notes": notes, "blockers": blockers}
    return "\n".join(L) + "\n", meta


def stability_op_netlist(text, nodes):
    """[신규 C10 안정성] 폐루프 .tran 넷리스트를 만들기 전 동작점 패스: text(오라클 넷리스트)의 .control 앞 본문 그대로에
    `op` 와 print(테스트벤치 choke 전류 i(<choke>), 주어진 SPICE 노드와 choke 회로 쪽 노드의 v(..))를 붙인다.
    반환 (텍스트, choke 이름 목록, 노드 목록). 이 패스의 값이 stability_netlist 의 choke_I·node_V 가 된다(같은 본문의 .op)."""
    body, chokes, nn = [], [], [n for n in nodes if n != "0"]
    for raw in text.splitlines():
        if raw.strip().lower().startswith(".control"):
            break
        body.append(raw)
        tok = raw.split()
        if tok and tok[0].startswith(CHOKE_PREFIXES):
            chokes.append(tok[0])
            if tok[2] not in nn and tok[2] != "0":
                nn.append(tok[2])
        if tok and tok[0].startswith("Vlb_"):    # [U6] 절단 직렬원 양쪽 노드(CM 루프 개루프 .pz 가 소비자 쪽 lbx 를 구동하는 데 쓴다)
            for n_ in (tok[1], tok[2]):
                if n_ not in nn and n_ != "0":
                    nn.append(n_)
    body += [".control", "set noaskquit", "op", "echo OPSTART"]
    body += [f"print i({c.lower()})" for c in chokes] + [f"print v({n.lower()})" for n in nn]
    body += ["echo OPEND", "quit", ".endc", ".end"]
    return "\n".join(body) + "\n", chokes, nn


def stability_netlist(text, mode, weights, output_nodes, plan):
    """[신규 C10 안정성] 폐루프 과도(.tran) 넷리스트. text = 오라클이 쓴 넷리스트(.control 앞 본문만 쓴다).
    mode = 'beta_loop': text 는 루프 넷리스트 -- Vlb_<넷>(DC 0) 이 이미 루프 안 직렬 원이고 Vlb = 0 이면 실제 폐루프다.
      끊은 넷마다 Vlb 에 PULSE(0 -> w_k*kick) 를 건다(w_k = weights[넷]).
    mode = 'beta_1': text 는 본 넷리스트 -- 입력 넷마다 그 넷의 테스트벤치 원(Cac_·Vac_·Vdc_·Ldc_·Efb_·Vofs_·Lfb_)을 빼고
      `Ecl_<넷> <넷 노드> ecl_<넷> <출력 노드 쌍> g` + `Vcl_<넷> ecl_<넷> 0 PULSE(V0 -> V0 + w_k*kick)` 로 직접 구동한다:
      V(넷) = V_op(넷) + g*(H - H_op) + w_k*kick(t), g = -sign*w_k, V0 = V_op(넷) - g*H_op(H = 출력 차동/단일 전압).
      입력 AC = -sign*w_k*H 라 루프 이득 = sign*A(β=1, sign = 기준점 A 실수부 부호 -> 기준점에서 음되먹임), 동작점은
      H = H_op 에서 본 동작점과 같다. (결합 C 1 F 를 이상 VCVS 로 구동하면 큰 진동에서 .tran 이 'Timestep too small' --
      2026-10-08 실측 nmcnr_amplifier.)
    나머지 테스트벤치 choke(CHOKE_PREFIXES: Lfb_·Ldc_·Lhold_ <tb 노드> <회로 노드> L)는 `Itb_<이름> <tb 노드> <회로 노드>
    DC <I_op>`(같은 본문의 동작점 패스 stability_op_netlist 가 잰 그 choke 전류) + `.ic v(<회로 노드>) = <V_op>` 로 바꾼다:
    .ic 는 uic 없이 쓰면 과도 시작 전
    바이어스 해에서만 그 노드를 묶고 t > 0 에서 푼다(SPICE .ic 의미) -- 바이어스 = 본 동작점, 과도 중에는 전류가 얼어 있는
    이상적 choke 와 같다(큰 L 을 그대로 두면 ngspice .tran 이 'Timestep too small' 로 멈춘다, 2026-10-08 실측:
    1e20/1e12 H 실패, 1e8 H 성공). plan = {kick_V, td, tr, pw, tstop, tmax, file, sign, choke_I{이름 소문자: A},
    node_V{SPICE 노드 소문자: V}, input_nodes{넷: SPICE 노드}}. 반환 (텍스트, 못 만든 것 목록)."""
    def pulse(v0, a):
        return (f"PULSE({_num(v0)} {_num(v0 + a)} {_num(plan['td'])} {_num(plan['tr'])} {_num(plan['tr'])} "
                f"{_num(plan['pw'])} {_num(2 * plan['tstop'])})")
    body, done, ics, bad = [], set(), [], []
    ci, nv = plan.get("choke_I") or {}, plan.get("node_V") or {}
    drop, h_op = set(), None
    if mode == "beta_1":
        drop = {f"{p}{net}" for net in weights for p in ("Cac_", "Vac_", "Vdc_", "Ldc_", "Efb_", "Vofs_", "Lfb_")}
        vo = [0.0 if n == "0" else nv.get(n.lower()) for n in output_nodes]
        h_op = None if None in vo else vo[0] - vo[1]
    for raw in text.splitlines():
        if raw.strip().lower().startswith(".control"):
            break
        tok = raw.split()
        if tok and tok[0] in drop:
            continue
        if tok and tok[0].startswith(CHOKE_PREFIXES):
            i_op, v_op = ci.get(tok[0].lower()), nv.get(tok[2].lower())
            if i_op is None or v_op is None:
                bad.append(f"{tok[0]}(동작점 전류 {i_op}, 노드 {tok[2]} 전압 {v_op})")
                body.append(raw)
                continue
            body.append(f"Itb_{tok[0]} {tok[1]} {tok[2]} DC {_num(i_op)}")
            ics.append(f".ic v({tok[2]})={_num(v_op)}")
            continue
        if mode == "beta_loop" and tok and tok[0].startswith("Vlb_") and tok[0][4:] in weights:
            net = tok[0][4:]
            body.append(f"{tok[0]} {tok[1]} {tok[2]} DC 0 " + pulse(0.0, weights[net] * plan["kick_V"]))
            done.add(net)
            continue
        body.append(raw)
    if mode == "beta_1":
        for net, w in weights.items():
            node = (plan.get("input_nodes") or {}).get(net)
            v_in = None if node is None else nv.get(node.lower())
            if v_in is None or h_op is None:
                bad.append(f"입력 {net}(동작점 전압 {v_in}, 출력 H_op {h_op})")
                continue
            g = -plan["sign"] * w
            body.append(f"Ecl_{net} {node} ecl_{net} {output_nodes[0]} {output_nodes[1]} {_num(g)}")
            body.append(f"Vcl_{net} ecl_{net} 0 " + pulse(v_in - g * h_op, w * plan["kick_V"]))
            done.add(net)
    body += ics
    body += stability_control(output_nodes, plan)
    return "\n".join(body) + "\n", sorted(set(weights) - done) + bad


def open_loop_parts(text, input_nets, input_nodes, node_V, choke_I, loop_kind=None, break_nets=()):
    """[신규 U6] 개루프 회로 본문 -- `.pz` 와 개루프 과도 확인이 같이 쓴다. text = 오라클이 쓴 넷리스트(본 또는 루프 넷리스트), 동작점
    패스(stability_op_netlist)의 node_V{SPICE 노드 소문자: V}·choke_I{choke 이름 소문자: A} 로 **큰 L·큰 C 없이** 같은 바이어스의 개루프
    회로를 만든다(ngspice `.pz` 근 찾기는 1e12 H·1 F 테스트벤치 소자가 낳는 1e-12 ~ 1e11 rad/s 동적 범위에서 반복 한도에 걸려 실패한다 --
    5T OTA 실측; 이 형태는 같은 회로에서 수렴한다).
      * 입력 넷마다 테스트벤치 사슬(Cac_·Vac_·Vdc_·Ldc_·Efb_·Vofs_·Lfb_·Vlb_·Ilb_)을 빼고 입력 노드를 동작점 전압의 이상 전압원
        `Vpz_<넷> <노드> 0 DC V_op` 로 구동한다(AC 0 = 입력 단락 = 개루프 A 의 자연 주파수).
      * 남은 choke(Lhold_ 등, 강제 바이어스)는 `Itb_<이름> <tb 노드> <회로 노드> DC <I_op>` + 초기 전압 V_op(`ics` 목록).
      * 절단 직렬원: `Vlb_<넷>`/`Ilb_<넷>` 을 빼고 절단 양쪽을 AC 로 나눈다. loop_kind = 'cm'(CM 루프, 절단 넷 = 출력 포트): 소비자 쪽 노드
        lbx_<넷>(루프 순방향 입력)만 동작점 전압의 이상 전압원으로 구동하고 구동자 쪽(출력)은 그대로 둔다. 'dm'(β 루프, 절단 넷 = 입력 포트): 증폭기 쪽 n(위
        입력 사슬 처리)과 되먹임 망 쪽 lbx_<넷> 을 모두 구동한다 -- 닫힌 루프에서 n 은 (높은 이득 때문에) 가상 접지라 되먹임 소자의 반대편 끝이 AC 접지에
        놓이는 부하와 같고, 용량만 물린 lbx 를 띄워 두면 `.pz` 가 'singular matrix' 로 실패한다(smoke 파일럿 실측). RHP 극은 능동 증폭기 내부(국소 양되먹임)에서만
        나오고 수동 β 망은 RHP 극을 만들지 않는다.
    반환 (본문 줄 목록, 초기 전압 사전 {SPICE 노드 소문자: V}). 못 만들면 ValueError."""
    drop_tb = set()
    for net in list(input_nets) + ([] if loop_kind == "cm" else list(break_nets)):
        drop_tb |= {f"{p}{net}" for p in ("Cac_", "Vac_", "Vdc_", "Ldc_", "Efb_", "Vofs_", "Lfb_", "Vlb_", "Ilb_")}
    cm_drop = {f"{p}{net}" for net in break_nets for p in ("Vlb_", "Ilb_")} if loop_kind == "cm" else set()
    body, ics = [], {}
    for raw in text.splitlines():
        if raw.strip().lower().startswith(".control"):
            break
        tok = raw.split()
        if tok and (tok[0] in drop_tb or tok[0] in cm_drop):
            continue
        if tok and tok[0].startswith(CHOKE_PREFIXES):
            i_op, v_op = choke_I.get(tok[0].lower()), node_V.get(tok[2].lower())
            if i_op is None or v_op is None:
                raise ValueError(f"{tok[0]}: 동작점 전류 {i_op} 또는 노드 {tok[2]} 전압 {v_op} 없음")
            body.append(f"Itb_{tok[0]} {tok[1]} {tok[2]} DC {_num(i_op)}")
            ics[tok[2].lower()] = v_op
            continue
        body.append(raw)
    for net, node in zip(input_nets, input_nodes):
        v = node_V.get(node.lower())
        if v is None:
            raise ValueError(f"입력 {net}({node}) 동작점 전압 없음")
        body.append(f"Vpz_{net} {node} 0 DC {_num(v)}")
    if loop_kind in ("cm", "dm"):
        for net in break_nets:
            v = node_V.get(f"lbx_{net}".lower())
            if v is None:
                raise ValueError(f"절단 넷 {net} 의 반대편 노드 lbx_{net} 동작점 전압 없음")
            body.append(f"Vpz_lbx_{net} lbx_{net} 0 DC {_num(v)}")
    return body, ics


def pz_netlist(text, input_nets, input_nodes, output_node, node_V, choke_I, loop_kind=None, break_nets=()):
    """[신규 U6] 개루프 `.pz` 넷리스트(open_loop_parts 본문 + `.nodeset` + `op` + `pz`). `.pz` 는 입력 포트가 이미 전압원에 묶인 노드에 못 건다
    ('input signal is shorted') -- 극점은 포트와 무관한 자연 주파수라 포트는 출력 노드의 전류 입력(`pz <출력> 0 <출력> 0 cur pol`)으로 둔다
    (회로를 바꾸지 않는다). 못 만들면 ValueError."""
    body, ics = open_loop_parts(text, input_nets, input_nodes, node_V, choke_I, loop_kind, break_nets)
    body += [f".nodeset v({n})={_num(v)}" for n, v in ics.items()]
    body += [".control", "set noaskquit", "op", "echo PZSTART", f"pz {output_node} 0 {output_node} 0 cur pol", "print all",
             "echo PZEND", "quit", ".endc", ".end"]
    return "\n".join(body) + "\n"


def openloop_tran_netlist(text, input_nets, input_nodes, output_nodes, node_V, choke_I, loop_kind, break_nets, plan, kick_V):
    """[신규 U6] 개루프 과도 확인 넷리스트: `.pz` 가 낸 RHP 극이 진짜인지 SPICE 시간 영역으로 확인한다(ngspice `.pz` 는 큰 BSIM4 회로에서 근을
    놓치거나 가짜 근을 낸다 -- smoke 파일럿 실측: 개루프 forced 에서 RHP 극 23 개를 냈지만 400 ns 개루프 과도는 증가가 없다). open_loop_parts 본문
    (`.nodeset` 대신 `.ic`) + 출력 노드 하나에 초기 변위 `.ic v(<출력>) = V_op + kick`(킥 = V_T, 폐루프 과도와 같은 크기; `.ic` 는 uic 없이 바이어스 해에서만
    그 노드를 묶고 t > 0 에서 풀어 준다 = 초기 변위가 풀려 나가는 과도) + stability_control 의 창 단위 실행(plan.t_kick_end = 0, 기준 H_ref = 동작점 H 값).
    RHP 극이 있으면 변위가 지수로 자라거나(포화 한계 사이클) 아니면 창마다 감쇠한다 -- 폐루프 과도와 같은 판정 규칙(transient_decision)을 쓴다.
    반환 (텍스트). 못 만들면 ValueError."""
    body, ics = open_loop_parts(text, input_nets, input_nodes, node_V, choke_I, loop_kind, break_nets)
    o1 = output_nodes[0]
    v_o1 = node_V.get(o1.lower())
    if v_o1 is None:
        raise ValueError(f"출력 {o1} 동작점 전압 없음")
    ics[o1.lower()] = v_o1 + kick_V
    body += [f".ic v({n})={_num(v)}" for n, v in ics.items()]
    body += stability_control(output_nodes, plan)
    return "\n".join(body) + "\n"


# wrdata 가 찍는 가수 자릿수 = numdgt + 1 (ngspice-46 실측: numdgt 4 -> 5 자리, 8 -> 9 자리, 12 -> 13 자리).
# 파일 반올림 반 단위 u = 0.5 * 10^-numdgt 를 .control 과 파이썬 판정(data_rel_resolution)이 같은 값으로 쓰도록 numdgt 를 명시한다.
WRDATA_NUMDGT = 8


def stability_control(output_nodes, plan):
    """[신규 C10 조기 종결 계약 (b)(d)] 폐루프 과도 `.save` 카드 + `.control` 블록 줄 목록.
    * `.save`: H 식의 피연산자 v(..) 와 time 만 저장(메모리 오류 완화; 전체 벡터 저장 안 함).
    * 창 단위 실행: ngspice 가 `stop when time > <창 j 끝>` / `resume` 으로 창 j = 1..K 를 차례로 끝내며(마지막 창은 tstop 에서
      저절로 끝난다), 창마다 로그에 `STABWIN j M_j`(M_j = 창 [t_end+(j-1)W, t_end+jW] 안 max|H - H(0)|) 한 줄을 쓴다. 경계 조건이
      `>` 인 것은 ngspice 의 `stop when` 이 `>=` 를 받지 않아서다(경계를 처음 넘은 표본에서 멈춘다 -- 그 표본은 창 j 밖).
      멈출 때마다 `delete all`(끝난 조건을 지우지 않으면 resume 이 같은 조건에서 곧바로 다시 멈춘다 -- 실측).
    * 조기 종결: 파이썬 oracle_simulate.early_window 와 같은 식을 창마다 스크립트로 평가한다.
        growth      : j >= 3, g↑(M_{j-2}, M_{j-1}), g↑(M_{j-1}, M_j), g↑(M_1, M_j)
        limit_cycle : j >= 3, 창 j-1 과 j 에서 flat 이다. flat(j) := M_j(1-reltol) > floor' 이고 g↑(M_{j-1},M_j)·g↓(M_{j-1},M_j) 둘 다 아님
      g↑(a,b) := b(1-reltol) > a(1+reltol) + floor', g↓(a,b) := a(1-reltol) > b(1+reltol) + floor'.
      (ngspice 명령 줄의 `>`·`<` 는 출력/입력 리다이렉션으로 읽혀 `let x = (a > b)` 가 조용히 틀리거나 실패한다 -- 실측. 비교는 `>=`·`<=`
      만 쓰고(`>=` 는 정상 비교), 한 줄에 하나씩 `let x = (a >= b)` 로 계산해 곱은 그 변수로 한다. 엄격 부등식(`>`)과 `>=` 는 값이
      정확히 같을 때만 다르고 floor' > 0 이라 실제로 같을 수 없다.)
      floor' = plan.floor_V + u·max|H|(지금까지 표본; u = 0.5·10^-numdgt). 충족하면 즉시 데이터 파일을 쓰고 끝낸다
      (파이썬은 파일에서 같은 기준을 다시 계산해 증명한다 -- ngspice 는 멈출 시점만 정한다).
    * 마지막 시각이 창 끝에 못 닿으면(ngspice 가 중간에 죽음) 더 돌리지 않고 파일만 쓴다(파이썬이 failed 로 판정)."""
    a, b = output_nodes[0], output_nodes[1]
    hst = f"v({a})" + ("" if b == "0" else f" - v({b})")
    save = f".save v({a})" + ("" if b == "0" else f" v({b})")
    u = 0.5 * 10.0 ** (-WRDATA_NUMDGT)
    tke, W, K = plan["t_kick_end"], plan["window_s"], int(plan["windows"])
    c = [save, ".control", "set noaskquit", f"set numdgt={WRDATA_NUMDGT}", "set wr_singlescale",
         f"let sw_tke = {_num(tke)}", f"let sw_w = {_num(W)}", f"let sw_k = {K}",
         f"let sw_rt = {_num(plan['reltol'])}", f"let sw_fl0 = {_num(plan['floor_V'])}", f"let sw_u = {_num(u)}",
         "let sw_j = 0", "let sw_m1 = 0", "let sw_p1 = 0", "let sw_p2 = 0", "let sw_fin = 0", "let sw_kind = 0"]
    if K > 1:
        c.append(f"stop when time > {_num(tke + W)}")
    c.append(f"tran {_num(plan['tmax'])} {_num(plan['tstop'])} 0 {_num(plan['tmax'])}")
    c += ["while sw_fin = 0",
          "  let sw_j = sw_j + 1",
          f"  let hst = {hst}",
          "  let sw_lo = sw_tke + (sw_j - 1) * sw_w",
          "  let sw_hi = sw_tke + sw_j * sw_w",
          "  let sw_tl = time[length(time) - 1]",
          "  if sw_tl >= sw_hi * (1 - 2 * sw_u)",
          f"    let sw_m = maximum(abs(hst - ({_num(plan['h_ref']) if plan.get('h_ref') is not None else 'hst[0]'})) * (time >= sw_lo) * (time <= sw_hi))",
          "    echo STABWIN $&sw_j $&sw_m",
          "    if sw_j = 1",
          "      let sw_m1 = sw_m",
          "    end",
          "    let sw_fl = sw_fl0 + sw_u * maximum(abs(hst))",
          "    let sw_up = (sw_m * (1 - sw_rt) >= sw_p1 * (1 + sw_rt) + sw_fl)",
          "    let sw_dn = (sw_p1 * (1 - sw_rt) >= sw_m * (1 + sw_rt) + sw_fl)",
          "    let sw_up0 = (sw_p1 * (1 - sw_rt) >= sw_p2 * (1 + sw_rt) + sw_fl)",
          "    let sw_dn0 = (sw_p2 * (1 - sw_rt) >= sw_p1 * (1 + sw_rt) + sw_fl)",
          "    let sw_upf = (sw_m * (1 - sw_rt) >= sw_m1 * (1 + sw_rt) + sw_fl)",
          "    let sw_ab1 = (sw_m * (1 - sw_rt) >= sw_fl)",
          "    let sw_ab0 = (sw_p1 * (1 - sw_rt) >= sw_fl)",
          "    let sw_fl1 = sw_ab1 * (1 - sw_up) * (1 - sw_dn)",
          "    let sw_fl0f = sw_ab0 * (1 - sw_up0) * (1 - sw_dn0)",
          "    let sw_gr = sw_up0 * sw_up * sw_upf",
          "    let sw_lc = sw_fl0f * sw_fl1",
          "    if sw_j >= 3",
          "      if sw_gr >= 1",
          "        let sw_fin = 1",
          "        let sw_kind = 1",
          "      end",
          "      if sw_lc >= 1",
          "        let sw_fin = 1",
          "        let sw_kind = 2",
          "      end",
          "    end",
          "    if sw_fin = 0",
          "      if sw_j >= sw_k",
          "        let sw_fin = 2",
          "      else",
          "        let sw_p2 = sw_p1",
          "        let sw_p1 = sw_m",
          "        let sw_nb = sw_tke + (sw_j + 1) * sw_w",
          "        delete all",
          "        if sw_k >= sw_j + 2",
          "          stop when time > $&sw_nb",
          "        end",
          "        resume",
          "      end",
          "    end",
          "  else",
          "    let sw_fin = 3",
          "  end",
          "end",
          "echo STABEND $&sw_j $&sw_fin $&sw_kind",
          f"let hst = {hst}",
          f"wrdata {plan['file']} hst",
          "quit", ".endc", ".end"]
    return c


def dc_path_isolation(tb, inputs, fb):
    """C27 기록(판정 아님): 본 넷리스트에서 입력 넷마다 DC 경로 choke(dc_choke_H)와 AC 결합 C(ac_couple_F)의
    (2*pi*fstart)^2 * L * C. 결합 C 가 fstart 에서 입력을 AC 접지하는 동안 choke 로 들어오는 경로(free 출력 DC 되먹임
    Efb·Lfb, 또는 Vdc·Ldc)가 입력 넷 전압에 남기는 몫이 약 1/(ω²LC) 이다 -- >> 1 이면 그 입력은 fstart 에서 AC 0
    고정(개루프)으로 본다. 숫자 문턱은 두지 않는다. 반환 [{net, choke_H, couple_F, f_hz, omega2_LC, output_feedback}]."""
    import math
    f0 = (tb.get("ac") or {}).get("fstart_hz")
    out = []
    for net in inputs:
        Lh, Cf = tb.get("dc_choke_H"), tb.get("ac_couple_F")
        w2lc = None if f0 is None or Lh is None or Cf is None else (2 * math.pi * float(f0)) ** 2 * float(Lh) * float(Cf)
        out.append({"net": net, "choke_H": Lh, "couple_F": Cf, "f_hz": f0, "omega2_LC": w2lc,
                    "output_feedback": net in fb})
    return out


def _rout_plan(inp, ac_src, all_nets, N, blockers):
    """C26: rout_ohm 뷰 목록을 검사해 잴 뷰만 돌려준다(하나라도 막히면 빈 목록 + 막힘).
    막힘: fstart_hz 없음, 감지 넷이 회로 넷(reference 제외)이 아님, reference 레일, 테스트벤치가 이상 전압원으로 구동하는
    넷(레일·입력 Vac·게이트 바이어스 = 엔진의 고정 노드), differential 에서 sense_p == sense_n."""
    views = rout_views(inp)
    if not views:
        return []
    if (inp["testbench"].get("ac") or {}).get("fstart_hz") is None:
        blockers.append("C26 rout_ohm: testbench.ac.fstart_hz 없음 -- 측정 주파수를 정할 수 없다")
        return []
    ref = {r["net"] for r in inp["rails"] if r.get("reference")}
    circuit = set(all_nets)
    ok = True
    for k, view in enumerate(views):
        keys = ("sense_p", "sense_n") if view["sense_mode"] == "differential" else ("sense_p",)
        for key in keys:
            net = view[key]
            if net in ref:
                blockers.append(f"C26 rout_ohm 뷰 {k}: {key} {net} 은 reference 레일(SPICE 노드 0)이다")
                ok = False
            elif net not in circuit:
                blockers.append(f"C26 rout_ohm 뷰 {k}: {key} {net} 이 회로 넷(reference 제외)이 아니다")
                ok = False
            elif net in ac_src:
                blockers.append(f"C26 rout_ohm 뷰 {k}: {key} {net} 은 테스트벤치가 이상 전압원으로 구동하는 넷"
                                f"(레일·입력·게이트 바이어스 {sorted(ac_src)})이다 -- 엔진 출력 포트 뷰의 고정 노드라 정의 밖")
                ok = False
        if view["sense_mode"] == "differential" and view["sense_p"] == view["sense_n"]:
            blockers.append(f"C26 rout_ohm 뷰 {k}: sense_p 와 sense_n 이 같은 넷 {view['sense_p']} 이다")
            ok = False
    return views if ok else []


def _rout_runs(L, plan, inp, ac_src, N, ac_file):
    """C26: 뷰마다 .ac 한 점(fstart): 여기 가능한 모든 AC 원(레일·입력 Vac·게이트 바이어스) acmag 0, 그 뷰의 감지 전류원만
    acmag 1(single_ended: sense_p 로 1 A 주입, differential: sense_p 로 +1 A, sense_n 에서 1 A 뽑음), 다른 뷰의 감지
    전류원은 0. H = V(sense_p) [- V(sense_n)] 를 <stem>.rout<k>.txt 로. 반환 meta 용 목록."""
    if not plan:
        return []
    f0 = inp["testbench"]["ac"]["fstart_hz"]
    stem = ac_file[:-len(".ac.txt")] if ac_file.endswith(".ac.txt") else ac_file
    srcs = []
    for k, view in enumerate(plan):
        srcs.append(f"irout_{k}")
        if view["sense_mode"] == "differential":
            srcs.append(f"irout_{k}n")
    L.append("set wr_singlescale")
    runs = []
    for k, view in enumerate(plan):
        for net, src in sorted(ac_src.items()):
            L.append(f"alter @{src.lower()}[acmag] = 0")
        mine = {f"irout_{k}", f"irout_{k}n"}
        for s in srcs:
            L.append(f"alter @{s}[acmag] = {1 if s in mine else 0}")
        L.append(f"ac lin 1 {_num(f0)} {_num(f0)}")
        sp = f"v({N(view['sense_p'])})"
        L.append(f"let hrout{k} = {sp} - v({N(view['sense_n'])})" if view["sense_mode"] == "differential"
                 else f"let hrout{k} = {sp}")
        fn = f"{stem}.rout{k}.txt"
        L.append(f"wrdata {fn} hrout{k}")
        runs.append({"view": view, "f_hz": float(f0), "file": fn})
    return runs


def _ratio_runs(L, inp, ac_src, all_nets, N, ac_file, blockers):
    """C24: ratio_db 뷰마다 .ac 2회(num, den)를 .control 에 덧붙인다. 한 번의 .ac 에서 ac_excite 넷의 원은 그 진폭,
    나머지 여기 가능한 원(레일·입력 Vac·게이트 바이어스)은 0. 측정 주파수 = testbench.ac.fstart_hz 한 점.
    여기 넷이 그 원들 밖이거나 sense 넷이 회로 넷이 아니면 막힘. 반환 meta 용 목록."""
    views = ratio_views(inp)
    if not views:
        return []
    f0 = (inp["testbench"].get("ac") or {}).get("fstart_hz")
    if f0 is None:
        blockers.append("C24 ratio_db: testbench.ac.fstart_hz 없음 -- 측정 주파수를 정할 수 없다")
        return []
    ref = {r["net"] for r in inp["rails"] if r.get("reference")}
    circuit = set(all_nets)
    stem = ac_file[:-len(".ac.txt")] if ac_file.endswith(".ac.txt") else ac_file
    runs, ok = [], True
    for k, view in enumerate(views):
        for side in ("num", "den"):
            tv = view[side]
            for net in sorted(tv["ac_excite"]):
                if net in ref:
                    blockers.append(f"C24 ratio_db 뷰 {k} {side}: reference 레일 {net} 은 여기할 수 없다(SPICE 노드 0)")
                    ok = False
                elif net not in ac_src:
                    blockers.append(f"C24 ratio_db 뷰 {k} {side}: 여기 넷 {net} 을 테스트벤치가 이상 전압원으로 구동하지 않는다"
                                    f"(여기 가능 넷 = 레일·입력·게이트 바이어스 {sorted(ac_src)}) -- DC 를 바꾸지 않고 AC 만 고정할 수 없다")
                    ok = False
            for key in ("sense_p", "sense_n"):
                net = tv.get(key)
                if net is not None and net not in circuit:
                    blockers.append(f"C24 ratio_db 뷰 {k} {side}: {key} {net} 이 회로 넷(reference 제외)이 아니다")
                    ok = False
    if not ok:
        return []
    L.append("set wr_singlescale")
    for k, view in enumerate(views):
        run = {"view": view, "f_hz": float(f0)}
        for side in ("num", "den"):
            tv = view[side]
            for net, src in sorted(ac_src.items()):
                L.append(f"alter @{src.lower()}[acmag] = {_num(tv['ac_excite'].get(net, 0))}")
            L.append(f"ac lin 1 {_num(f0)} {_num(f0)}")
            sp = f"v({N(tv['sense_p'])})"
            L.append(f"let hr{k}{side} = {sp} - v({N(tv['sense_n'])})" if tv["sense_mode"] == "differential"
                     else f"let hr{k}{side} = {sp}")
            fn = f"{stem}.ratio{k}.{side}.txt"
            L.append(f"wrdata {fn} hr{k}{side}")
            run[f"{side}_file"] = fn
        runs.append(run)
    return runs


def _loop_tail(L, tb, breaks, ac_mag, prefix, N, notes, blockers, bias, lut, loop_choke=None):
    """i 파일 열 = 끊은 넷마다 i(Vlb) 뒤에 (C27 기록용) 끊은 넷마다 V(넷) -- 2회(전류 주입) 실행의 증폭기 쪽 노드 전압."""
    ac = tb["ac"]
    L.append(".control")
    L.append("set noaskquit")
    L.append("set wr_singlescale")
    L.append(f"ac dec {int(ac['points_per_decade'])} {_num(ac['fstart_hz'])} {_num(ac['fstop_hz'])}")
    L.append("wrdata " + f"{prefix}.v.txt " + " ".join(f"v(lbx_{n}) v({N(n)})" for n in breaks))
    for n in breaks:
        L.append(f"alter @vlb_{n.lower()}[acmag] = 0")
        L.append(f"alter @ilb_{n.lower()}[acmag] = {_num(ac_mag.get(n, 0))}")
    L.append(f"ac dec {int(ac['points_per_decade'])} {_num(ac['fstart_hz'])} {_num(ac['fstop_hz'])}")
    L.append("wrdata " + f"{prefix}.i.txt " + " ".join(f"i(vlb_{n.lower()})" for n in breaks)
             + "".join(f" v({N(n)})" for n in breaks))
    L.append("quit")
    L.append(".endc")
    L.append(".end")
    meta = {"bias": bias, "lut_meta": lut, "break_nets": breaks, "weights": [ac_mag.get(n, 0) for n in breaks],
            "v_file": f"{prefix}.v.txt", "i_file": f"{prefix}.i.txt", "notes": notes,
            "choke_H": None if loop_choke is None else float(loop_choke),
            "blockers": N.blockers + blockers}
    return "\n".join(L) + "\n", meta


def build_iso_netlist(inp):
    """bias=iso(단독 소자): 소자마다 X<name> 인스턴스 하나를 자기 전용 노드에 두고 소스를 0 으로, 게이트·드레인·바디를
    엔진 예측 VGS·VDS·VSB(크기 규칙)에 이상 전압원으로 고정한다. 극성 부호 = models[kind].polarity(n: +1, p: -1):
    V(g) = s*VGS, V(d) = s*VDS, V(b) = -s*VSB. 회로 연결·테스트벤치 없음(.op 만). 예측이나 polarity 가 없는 소자는
    인스턴스를 만들지 않고 meta.iso_skipped 에 이유를 적는다(비교 N/A). 한 소자도 못 만들면 막힘."""
    process = inp["process"]
    pdev = (inp.get("predictions") or {}).get("devices") or {}
    lut = read_lut_meta(process["lut_npz"])
    blockers, notes = [], []
    for k in ("corner", "temp_c"):
        if lut[k] is None:
            blockers.append(f"LUT npz 에 {k} 메타가 없다: {process['lut_npz']}")
    devs = inp["devices"]
    L = [f"* spice_oracle: {inp.get('circuit', '?')} bias=iso (단독 소자, 엔진 예측 VGS/VDS/VSB 고정)"]
    L += _includes(process, {d["kind"] for d in devs}, lut["corner"])
    if lut["temp_c"] is not None:
        L.append(f".temp {_num(lut['temp_c'])}")
    tb = inp.get("testbench") or {}
    if tb.get("options"):
        L.append(".option " + " ".join(f"{k}={v}" for k, v in tb["options"].items()))
    geometry, probes, skipped, applied = {}, {}, {}, {}
    sign = {"n": 1.0, "p": -1.0}
    for d in devs:
        n = d["name"]
        W_f = float(d["finger_w"]) * int(d["n_fingers"])
        geometry[n] = {"L": float(d["L"]), "finger_w": float(d["finger_w"]), "n_fingers": int(d["n_fingers"]),
                       "W_from_fingers": W_f, "W_declared": None if d.get("W") is None else float(d["W"]),
                       "diffusion": diffusion_of(process, d)}
        pol = process["models"][d["kind"]].get("polarity")
        p = pdev.get(n) or {}
        miss = [k for k in ("VGS", "VDS", "VSB") if p.get(k) is None]
        if pol not in sign:
            skipped[n] = f"process.models[{d['kind']}].polarity 없음(n|p)"
            continue
        if miss:
            skipped[n] = f"예측 {miss} 없음"
            continue
        sg = sign[pol]
        vg, vd, vb = sg * float(p["VGS"]), sg * float(p["VDS"]), -sg * float(p["VSB"])
        g_, d_, b_ = f"iso_g_{n}", f"iso_d_{n}", f"iso_b_{n}"
        L.append(f"Viso_g_{n} {g_} 0 DC {_num(vg)}")
        L.append(f"Viso_d_{n} {d_} 0 DC {_num(vd)}")
        L.append(f"Viso_b_{n} {b_} 0 DC {_num(vb)}")
        L.append(device_line(process, d, [d_, g_, "0", b_]))
        probes[n] = {q: probe_name(process, d["kind"], f"X{n}", q) for q in OP_PARAMS}
        applied[n] = {"V_g": vg, "V_d": vd, "V_s": 0.0, "V_b": vb, "polarity": pol}
    if not probes:
        blockers.append("iso: 단독 인스턴스를 만들 소자가 없다(예측 VGS/VDS/VSB 또는 polarity 없음)")
    notes += diffusion_gate(geometry, "iso")[1]
    for n, why in skipped.items():
        notes.append(f"iso: {n} 단독 인스턴스 안 만듦 -- {why}")
    L += [".control", "set noaskquit", "op", "echo OPSTART"]
    for n, pr in probes.items():
        for q in OP_PARAMS:
            L.append(f"print {pr[q]}")
    L += ["echo OPEND", "quit", ".endc", ".end"]
    meta = {"bias": "iso", "lut_meta": lut, "geometry": geometry, "probes": probes, "nets": [], "spice_node": {},
            "rail_sources": {}, "held": [], "unheld": [], "gate_bias": {}, "inputs": [], "has_ac": False,
            "ac_file": None, "iso_applied": applied, "iso_skipped": skipped, "notes": notes, "blockers": blockers}
    return "\n".join(L) + "\n", meta


def apply_z1(inp, omit=(), short=()):
    """Z1 제거법(README C18): omit = 원소(소자·수동소자·이상원) 이름 -> 넷리스트에서 뺌, short = 수동소자 이름 -> 0 V 전압원.
    입력을 바꾸지 않고 바뀐 사본을 돌려준다. 반환 (사본, 변경 기록, 막힘). 변경 대상이 feedback_passives 이면 막힘
    (β 루프 정의가 바뀐다)."""
    import copy
    omit, short = list(omit or []), list(short or [])
    mods = {"omit": omit, "short": short}
    if not omit and not short:
        return inp, None, []
    x = copy.deepcopy(inp)
    names = {"device": {d["name"] for d in x["devices"]}, "passive": {p["name"] for p in x.get("passives") or []},
             "source": {s["name"] for s in x.get("sources") or []}}
    allnames = set().union(*names.values())
    blockers = [f"Z1 --omit {n}: 그런 원소가 없다" for n in omit if n not in allnames]
    blockers += [f"Z1 --short {n}: 수동소자(passives)만 단락할 수 있다" for n in short if n not in names["passive"]]
    # 같은 옵션 안 반복(예: --omit RL RL)도 막는다 -- 반복 이름은 대개 오타라 조용히 합치면 의도한 다른 원소가 빠진다
    blockers += [f"Z1 --{opt} {n}: 같은 원소를 같은 옵션에 두 번 적었다"
                 for opt, lst in (("omit", omit), ("short", short)) for n in sorted({m for m in lst if lst.count(m) > 1})]
    blockers += [f"Z1 --omit/--short {n}: 같은 원소를 두 번 바꿀 수 없다" for n in set(omit) & set(short)]
    fbp = set(x.get("feedback_passives") or [])
    blockers += [f"Z1 변경 대상 {n} 이 feedback_passives 에 있다(β 루프 정의가 바뀐다)" for n in (set(omit) | set(short)) & fbp]
    om = set(omit)
    x["devices"] = [d for d in x["devices"] if d["name"] not in om]
    x["sources"] = [s for s in x.get("sources") or [] if s["name"] not in om]
    ps = []
    for p in x.get("passives") or []:
        if p["name"] in om:
            continue
        if p["name"] in short:
            p = {"name": p["name"], "kind": "short", "terminals": list(p["terminals"]), "value": 0.0}
        ps.append(p)
    x["passives"] = ps
    return x, mods, blockers


def repo_root(start):
    """start 폴더에서 위로 올라가며 처음 만나는 '.git'(폴더 또는 worktree 의 파일)이 있는 폴더. 없으면 None."""
    d = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up


def resolve_topology_path(inp, input_path=None, override=None):
    """topology JSON 경로: --topology 인자가 우선(그대로 절대화), 없으면 입력 topology.path.
    topology.path 가 상대 경로면 **저장소 루트 기준**(README C15): 루트 = 입력 파일 폴더에서 위로 처음 '.git' 이 있는 폴더,
    없으면 이 오라클 코드 폴더에서 같은 방법. 루트를 못 찾으면 None(-> 미검증). 절대 경로는 그대로(이식성 없음)."""
    if override:
        return os.path.abspath(override)
    p = (inp.get("topology") or {}).get("path")
    if not p:
        return None
    if os.path.isabs(p):
        return os.path.abspath(p)
    root = (repo_root(os.path.dirname(os.path.abspath(input_path))) if input_path else None) \
        or repo_root(os.path.dirname(os.path.abspath(__file__)))
    return None if root is None else os.path.abspath(os.path.join(root, *p.split("/")))


def parse_netlist_elements(text, inp):
    """오라클이 쓴 넷리스트 본문(.control 앞)을 다시 읽어 회로 원소 표를 만든다(C15). 반환
    (elements{이름: (종류, 단자 넷 tuple)}, testbench[원소 이름], unclassified[원소 이름]).
    노드 '0' 은 reference 레일 넷 이름으로 되돌린다. 소자 종류 = subckt 이름 -> models 의 kind(같은 subckt 가 여러 kind 면
    정렬해 '|' 로 이은 문자열)."""
    ref = [r["net"] for r in inp["rails"] if r.get("reference")]
    ref_net = ref[0] if len(ref) == 1 else "0"
    by_sub = {}
    for kind, m in inp["process"]["models"].items():
        by_sub.setdefault(m["subckt"].lower(), []).append(kind)
    elems, tbe, unk = {}, [], []
    back = lambda n: ref_net if n == "0" else n  # noqa: E731
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("*") or ln.startswith("+"):
            continue
        if ln.lower().startswith(".control"):
            break
        if ln.startswith("."):
            continue
        tok = ln.split()
        nm = tok[0]
        if any(nm.startswith(pfx) for pfx in TESTBENCH_PREFIXES):
            tbe.append(nm)
            continue
        hit = None
        for pfx, kind in CIRCUIT_PREFIXES.items():
            if nm.startswith(pfx):
                hit = (pfx, kind)
                break
        if hit is None:
            unk.append(nm)
            continue
        pfx, kind = hit
        name = nm[len(pfx):]
        if kind == "device":
            nodes = tuple(back(n) for n in tok[1:5])
            kinds = sorted(by_sub.get(tok[5].lower(), [])) if len(tok) > 5 else []
            elems[name] = ("|".join(kinds) or f"subckt:{tok[5] if len(tok) > 5 else '?'}", nodes)
        else:
            elems[name] = (kind, tuple(back(n) for n in tok[1:3]))
    return elems, tbe, unk


def topology_elements(topo):
    """topology JSON(netlist + passive_elements + ideal_sources) -> {이름: (종류, 단자 넷 tuple, 바디 선언 여부)}.
    MOS 단자 = (drain, gate, source[, bulk]) -- bulk 는 topology 가 선언한 원소만. 2단자 = terminals 순서 그대로.
    _ 로 시작하는 키·dict 가 아닌 원소는 무시한다(주석). 반환 (원소 표, 이름 중복 목록)."""
    out, dup = {}, []

    def put(name, val):
        if name in out:
            dup.append(name)
        out[name] = val
    for e in topo.get("netlist") or []:
        if not isinstance(e, dict):
            continue
        t = (e.get("drain"), e.get("gate"), e.get("source")) + ((e["bulk"],) if "bulk" in e else ())
        put(e.get("name"), (e.get("kind"), t, "bulk" in e))
    for e in topo.get("passive_elements") or []:
        if isinstance(e, dict):
            put(e.get("name"), (e.get("kind"), tuple(e.get("terminals") or ()), False))
    for e in topo.get("ideal_sources") or []:
        if isinstance(e, dict):
            put(e.get("name"), (TOPOLOGY_SOURCE_KINDS.get(e.get("kind"), f"topology:{e.get('kind')}"),
                                tuple(e.get("terminals") or ()), False))
    return out, dup


def topology_identity(inp, text, topology_path):
    """C15: 넷리스트(text)를 다시 파싱한 원소 집합과 topology JSON 의 집합 비교. 반환 dict
    {status: verified|mismatch|unverified, topology_path, sha256_actual, sha256_declared, diffs[...], compared,
     excluded_testbench, declared_not_in_topology{이름: 이유}, bulk_compared, notes}.
    비교 규칙: 원소 이름 집합이 같고, 원소마다 종류가 같고, 단자 넷이 같아야 한다. MOS 는 (d, g, s) 순서 그대로(+ topology
    가 bulk 를 선언했으면 bulk), 저항·커패시터는 순서 무관, 이상원은 순서 그대로(방향). 입력 passives/sources 중
    not_in_topology_reason 이 있는 원소는 비교에서 빼고 이유와 함께 기록한다(topology 에 같은 이름이 있으면 차이)."""
    import hashlib
    res = {"status": "unverified", "topology_path": topology_path, "sha256_actual": None,
           "sha256_declared": (inp.get("topology") or {}).get("sha256"), "diffs": [], "compared": 0,
           "excluded_testbench": [], "declared_not_in_topology": {}, "bulk_compared": [], "notes": []}
    if not topology_path:
        res["notes"].append("topology 미지정(입력 topology.path 도 --topology 도 없음) -- 연결 동일성 미검증")
        return res
    if not os.path.exists(topology_path):
        res["notes"].append(f"topology 파일 없음: {topology_path} -- 연결 동일성 미검증")
        return res
    with open(topology_path, "rb") as f:
        raw = f.read()
    res["sha256_actual"] = hashlib.sha256(raw).hexdigest()
    if res["sha256_declared"] and res["sha256_declared"] != res["sha256_actual"]:
        res["notes"].append(f"topology 파일 sha256 이 입력 선언값과 다르다(입력 변환 뒤 파일이 바뀜): "
                            f"선언 {res['sha256_declared'][:12]}.. 실제 {res['sha256_actual'][:12]}..")
    try:
        topo = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        res["status"] = "mismatch"
        res["diffs"].append(f"topology JSON 을 읽을 수 없다: {e}")
        return res
    want, dup = topology_elements(topo)
    got, tbe, unk = parse_netlist_elements(text, inp)
    res["excluded_testbench"] = tbe
    diffs = [f"topology 원소 이름 중복: {n}" for n in sorted(set(dup))]
    diffs += [f"넷리스트 원소 {n}: 접두사로 회로/테스트벤치를 가를 수 없다" for n in unk]
    extra = {e["name"]: e["not_in_topology_reason"] for k in ("passives", "sources") for e in inp.get(k) or []
             if e.get("not_in_topology_reason")}
    res["declared_not_in_topology"] = extra
    for n in sorted(extra):
        got.pop(n, None)
    for n in sorted(set(want) - set(got)):
        diffs.append(f"{n}: topology 에 있고 넷리스트에 없다")
    for n in sorted(set(got) - set(want)):
        diffs.append(f"{n}: 넷리스트에 있고 topology 에 없다")
    for n in sorted(set(want) & set(got)):
        wk, wt, has_bulk = want[n]
        gk, gt = got[n]
        res["compared"] += 1
        if gk != wk:
            diffs.append(f"{n}: 종류 topology {wk} != 넷리스트 {gk}")
        if wk in ("resistor", "capacitor"):
            same = sorted(wt) == sorted(gt)
        elif len(gt) == 4 and not has_bulk:
            same = tuple(gt[:3]) == tuple(wt)
        else:
            same = tuple(gt) == tuple(wt)
        if has_bulk:
            res["bulk_compared"].append(n)
        if not same:
            diffs.append(f"{n}: 단자 넷 topology {list(wt)} != 넷리스트 {list(gt[:len(wt)]) if len(gt) == 4 else list(gt)}")
    # [Q6] 외부 바이어스 입력 대조(엄격): 입력 bias_voltages 의 넷 집합 == topology bias_inputs. 키가 없으면 빈 집합과 대조한다.
    # (authoring 게이트가 bias_inputs = gate 전용 넷 전부임을 보장하므로, 같다 = 구동 소자 없는 게이트 넷마다 전압이 선언됨.
    #  키가 없으면 authoring 게이트를 통과한 topology 는 gate 전용 넷이 없으므로 bias_voltages 도 비어 있어야 한다.)
    bi = topo.get("bias_inputs", [])
    if not isinstance(bi, list) or not all(isinstance(x, str) for x in bi):
        diffs.append(f"topology bias_inputs 가 문자열 list 가 아니다: {bi!r}")
    else:
        want_b = set(bi)
        got_b = {b["net"] for b in inp.get("bias_voltages") or []}
        res["bias_inputs"] = sorted(want_b)
        if want_b != got_b:
            diffs.append(f"bias_voltages 넷 {sorted(got_b)} != topology bias_inputs {sorted(want_b)} "
                         f"(topology 에만 {sorted(want_b - got_b)}, 입력에만 {sorted(got_b - want_b)})")
    res["diffs"] = diffs
    res["status"] = "mismatch" if diffs else "verified"
    return res


def write_netlists(inp, bias, out_cir, topology_path=None, require_topology=False, omit=(), short=()):
    """본 넷리스트 + (feedback_passives 가 있으면) 루프 넷리스트를 쓰고 meta 를 돌려준다.
    루프 넷리스트는 <out_cir 확장자 뺀 이름>.loop.cir, meta['loop'] 에 그 메타.
    [신규] meta['topology_identity'] = C15 결과(free/forced: 변경 전 본 넷리스트로 비교, iso: 해당 없음).
    mismatch 이면 막힘, unverified 이고 require_topology 이면 막힘. omit/short 가 있으면 Z1 제거법(meta['z1'])."""
    stem = os.path.splitext(os.path.basename(out_cir))[0]
    work, z1, zb = apply_z1(inp, omit, short)
    text, meta = build_netlist(work, bias, f"{stem}.ac.txt")
    meta["blockers"] = meta["blockers"] + [b for b in zb if b not in meta["blockers"]]
    meta["z1"] = z1
    if bias == "iso":
        ti = {"status": "not_applicable", "topology_path": topology_path, "diffs": [],
              "notes": ["iso 는 회로 연결이 없는 단독 소자 넷리스트 -- C15 대상 아님"]}
    else:
        base_text = text if z1 is None else build_netlist(inp, bias, f"{stem}.ac.txt")[0]
        ti = topology_identity(inp, base_text, topology_path)
        if z1 is not None:
            ti["notes"].append("Z1 변경 전 넷리스트로 비교했다(제거·단락은 진단용 의도된 변경)")
        if ti["status"] == "mismatch":
            meta["blockers"].append(f"C15 topology 연결 동일성 불일치 {len(ti['diffs'])}건: " + "; ".join(ti["diffs"][:8]))
        elif ti["status"] == "unverified" and require_topology:
            meta["blockers"].append("C15 topology 연결 동일성 미검증(--require-topology): " + "; ".join(ti["notes"]))
    ti["required"] = bool(require_topology)
    meta["topology_identity"] = ti
    meta["cm_loop"] = None
    if work.get("cm_output_loop") and bias != "iso":
        ctext, cmeta = build_netlist(work, bias, f"{stem}.cmloop", loop=CM_LOOP)
        ccir = os.path.join(os.path.dirname(os.path.abspath(out_cir)), f"{stem}.cmloop.cir")
        with open(ccir, "w", encoding="utf-8") as f:
            f.write(ctext)
        cmeta["netlist"] = os.path.basename(ccir)
        meta["cm_loop"] = cmeta
        for b in cmeta["blockers"]:
            if b not in meta["blockers"]:
                meta["blockers"].append(b)
    meta["loop"] = None
    if work.get("feedback_passives") and bias != "iso":
        ltext, lmeta = build_netlist(work, bias, f"{stem}.loop", loop=True)
        lcir = os.path.join(os.path.dirname(os.path.abspath(out_cir)), f"{stem}.loop.cir")
        with open(lcir, "w", encoding="utf-8") as f:
            f.write(ltext)
        lmeta["netlist"] = os.path.basename(lcir)
        meta["loop"] = lmeta
        for b in lmeta["blockers"]:
            if b not in meta["blockers"]:
                meta["blockers"].append(b)
    with open(out_cir, "w", encoding="utf-8") as f:
        f.write(text)
    with open(out_cir + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return meta


def main(argv=None):
    ap = argparse.ArgumentParser(description="오라클 입력 JSON -> ngspice 넷리스트")
    ap.add_argument("oracle_input")
    ap.add_argument("out_cir")
    ap.add_argument("--bias", choices=BIASES, required=True)
    ap.add_argument("--topology", default=None, help="C15 대조용 topology JSON(입력 topology.path 보다 우선)")
    ap.add_argument("--require-topology", action="store_true", help="합격 실행: topology 미검증이면 막힘")
    ap.add_argument("--omit", nargs="+", default=[], help="Z1 제거법: 뺄 원소 이름")
    ap.add_argument("--short", nargs="+", default=[], help="Z1 제거법: 0 V 로 단락할 수동소자 이름")
    a = ap.parse_args(argv)
    inp = load_input(a.oracle_input)
    errs = validate_input(inp)
    if errs:
        print("입력이 oracle_input.schema.json 위반 -- 거부(넷리스트를 쓰지 않음):")
        for e in errs:
            print("  ", e)
        return 2
    os.makedirs(os.path.dirname(os.path.abspath(a.out_cir)), exist_ok=True)
    meta = write_netlists(inp, a.bias, a.out_cir, resolve_topology_path(inp, a.oracle_input, a.topology),
                          a.require_topology, a.omit, a.short)
    print("wrote", a.out_cir, "| C15 topology:", meta["topology_identity"]["status"])
    if meta["blockers"]:
        print("BLOCKERS:", meta["blockers"])
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
