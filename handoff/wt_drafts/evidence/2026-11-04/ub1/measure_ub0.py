"""UB-1 착수 사실 -- UB-0 규칙 차이 자리 코드 대조(계획 N6.1 측정 게이트 표 (나), 13회로 구조만, LUT·커널 평가 0).

* 두 구현(`block_model._select` as-built, `block_gain_model_of` 집합 규칙)의 스탬프 소자·미지수 집합을 library 13회로 전달 뷰 블록마다 대조한다.
* 값은 `tests/metrics/u7_ngcc.library_case`의 합성 값(test 입력 생성기). 잔차 칸은 '§2.5 규칙 시제품'이 체인 잔차를 어떻게 바꾸는지 보려는 참고이고
  UB-0 값 차이((가), LA-1 측정 시점)가 아니다. 시제품은 구현물이 아니다.

실행: PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 PYTHONPATH=<skill dir> C:/Python314/python.exe measure_ub0.py
결과: 같은 폴더 ub0_structure.jsonl(회로마다 append), ub0_summary.txt
"""
import json
import math
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(SKILL))

import numpy  # noqa: E402

from gmid_engine.metrics import block_model as BM  # noqa: E402
from gmid_engine.metrics import block_local_gain  # noqa: E402
from gmid_engine.metrics._helpers_nodal import conductance_matrix, nodal_factor, nodal_solve  # noqa: E402
from gmid_engine.metrics._helpers_view import view_system  # noqa: E402
from gmid_engine.metrics.block_residual import block_residual  # noqa: E402
from gmid_engine.metrics.records import SmallSignalCircuit  # noqa: E402
from gmid_engine.tests.metrics import u7_ngcc as N  # noqa: E402

import s1v_hand  # noqa: E402  (u7_ngcc 가 경로를 넣는다)

LIB = SKILL / "assets" / "library"
_ORIG_SUPPLIES = s1v_hand.lib_supplies


def _supplies(name):
    """test helper 가 `_declared_target_spec` 없는 4회로에서 멈춘다 -- spec `human.supplies_v.values`(엔진 밖 선언)로 메운다(이 스크립트 안에서만)."""
    try:
        return _ORIG_SUPPLIES(name)
    except KeyError:
        raw = json.loads((LIB / (name + ".sizing_spec.json")).read_text(encoding="utf-8"))
        return dict(raw["human"]["supplies_v"]["values"])


s1v_hand.lib_supplies = _supplies
CIRCUITS = sorted(p.name[: -len(".topology.json")] for p in LIB.glob("*.topology.json") if not p.name.startswith("_"))
OUT = open(HERE / "ub0_structure.jsonl", "w", encoding="utf-8")
SUM = open(HERE / "ub0_summary.txt", "w", encoding="utf-8")


def emit(row):
    OUT.write(json.dumps(row, ensure_ascii=False) + "\n")
    OUT.flush()


def say(*parts):
    line = " ".join(str(p) for p in parts)
    print(line)
    SUM.write(line + "\n")
    SUM.flush()


def charge_only_nets(doc, ground):
    """전회로에서 DC 전도 단자(MOS d·s, 저항, 이상 전압원 아님)가 하나도 없는 넷 = 용량 전용 후보(정의 §2.5-7, 교류접지·입력 제외)."""
    conduct = set()
    touch = {}
    for e in doc["netlist"]:
        conduct |= {e["drain"], e["source"]}
        touch.setdefault(e["gate"], []).append(("gate", e["name"]))
    for e in doc.get("passive_elements") or ():
        for t in e["terminals"]:
            if e["kind"] == "resistor":
                conduct.add(t)
            touch.setdefault(t, []).append((e["kind"], e["name"]))
    inputs = {n for n, q in doc["ports"].items() if isinstance(q, dict) and q.get("direction") == "input"}
    out = {}
    for net, who in sorted(touch.items()):
        if net in conduct or net in ground or net in inputs:
            continue
        out[net] = sorted(who)
    return out


def proto_local(ss, block, drive, roles, every, excluded, extra, view_ground):
    """§2.5 규칙 시제품: U_b = 블록 소자 채널·저항 단자 넷 + 저항 폐포 − 접지·여기·남의 블록 넷. 밖 소자의 d·s 가 U_b 에 닿으면 그 소자 스탬프(나머지 단자 고정 0)."""
    index = {n: i for i, n in enumerate(ss.nodes)}
    names = list(ss.nodes)
    ground = {index[n] for n in tuple(ss.ground_nets) + tuple(view_ground)}
    driven = {index[n] for n in drive} | {index[n] for n in block.inputs}
    outside = {index[n] for n in every if n in index} - {index[n] for n in block.nodes}
    stop = ground | driven | outside
    unknown = set()
    label_mos = {m.label: m for m in ss.circuit.mos}
    label_res = {r.label: r for r in ss.circuit.resistors}
    for label in tuple(roles) + tuple(extra):
        if label in label_mos:
            m = label_mos[label]
            unknown |= {m.d, m.s}
        elif label in label_res:
            r = label_res[label]
            unknown |= {r.a, r.b}
    unknown |= {index[n] for n in block.nodes}
    unknown -= stop
    changed = True
    res_on = set()
    while changed:                                 # 저항 폐포
        changed = False
        for r in ss.circuit.resistors:
            if r.label in res_on or not ({r.a, r.b} & unknown):
                continue
            res_on.add(r.label)
            new = {r.a, r.b} - stop - unknown
            if new:
                unknown |= new
            changed = True
    mos_on = []
    gate_driven_loads = []
    for m in ss.circuit.mos:
        if m.label in excluded and m.label not in extra:
            continue
        if m.label in roles or m.label in extra or m.d in unknown or m.s in unknown:
            mos_on.append(m)
            if m.label not in roles and m.label not in extra and m.g in driven:
                gate_driven_loads.append(m.label)
    sub = SmallSignalCircuit(mos=tuple(mos_on), resistors=tuple(r for r in ss.circuit.resistors if r.label in res_on))
    size = len(names)
    factor = nodal_factor(conductance_matrix(sub, size), set(range(size)) - unknown)
    volt, _res = nodal_solve(factor, size, {index[n]: v for n, v in drive.items()})
    if volt is None:
        return None, gate_driven_loads
    return {names[i]: float(volt[i]) for i in unknown | driven}, gate_driven_loads


def proto_residual(ss, decl, vs, raw_blocks, view_ground):
    system = view_system(ss, decl)
    fixed, drive_idx, sense, pairs, sense_nets = system
    size = len(ss.nodes)
    volt, _r = nodal_solve(nodal_factor(conductance_matrix(ss.circuit, size), fixed), size, drive_idx)
    if volt is None:
        return None, []
    full = float(sense @ volt)
    excluded = tuple(sorted({m for f in vs.ff for m in f.members}))
    every = {n for b in vs.blocks for n in b.nodes}
    volts = dict(pairs)
    flagged = []
    for block in vs.blocks:
        here = tuple(f for f in vs.ff if f.merge_block == block.key)
        drive = {n: volts.get(n, 0.0) for n in block.inputs}
        for f in here:
            if f.tap in volts:
                drive[f.tap] = volts[f.tap]
        roles = tuple(n for n, _ in raw_blocks[block.key].roles if n not in excluded)
        got, loads = proto_local(ss, block, drive, roles, every, excluded, tuple(m for f in here for m in f.members), view_ground)
        flagged += loads
        if got is None:
            return None, flagged
        volts.update(got)
    dec = volts.get(sense_nets[0], 0.0) - (0.0 if sense_nets[1] is None else volts.get(sense_nets[1], 0.0))
    if dec == 0 or full == 0:
        return None, flagged
    return 20 * math.log10(abs(full)) - 20 * math.log10(abs(dec)), flagged


totals = {"blocks": 0, "same_mos": 0, "same_unknown": 0, "dead_end": 0, "view_ground_extra": 0}
for name in CIRCUITS:
    try:
        doc = json.loads((LIB / (name + ".topology.json")).read_text(encoding="utf-8"))
        ss, structs, decls = N.library_case(name)
        _s1, s1v = s1v_hand.build_lib(name)
        ground = set(ss.ground_nets)
        charge = charge_only_nets(doc, ground)
        cls = {e["name"]: e["kind"] for e in doc.get("passive_elements") or ()}
        raw = {v.id: v for v in s1v.views}
        emit({"circuit": name, "kind": "charge_only_nets", "nets": charge,
              "passive_kinds": sorted(set(cls.values())), "n_mos": len(doc["netlist"])})
        say("##", name, "views", len(structs), "charge_only", sorted(charge))
        block_gates_on_charge = []
        for vs, decl in zip(structs, decls):
            view = raw[vs.id]
            raw_blocks = {b.key: b for b in view.blocks}
            view_ground = set(view.ac_ground)
            extra_ground = sorted(view_ground - ground)
            if extra_ground:
                totals["view_ground_extra"] += 1
            emit({"circuit": name, "kind": "view_ground", "view": vs.id, "view_ac_ground_minus_ss_ground": extra_ground})
            every = {n for b in vs.blocks for n in b.nodes}
            excluded = tuple(sorted({m for f in vs.ff for m in f.members}))
            attach = {}
            for e in doc["netlist"]:
                for t in (e["drain"], e["source"]):
                    attach[t] = attach.get(t, 0) + 1
            for e in doc.get("passive_elements") or ():
                if e["kind"] == "resistor":
                    for t in e["terminals"]:
                        attach[t] = attach.get(t, 0) + 1
            for block in vs.blocks:
                rb = raw_blocks[block.key]
                roles = dict(rb.roles)
                totals["blocks"] += 1
                # ---- as-built 집합 (block_model.block_local_gain 머리와 같은 계산)
                index = {n: i for i, n in enumerate(ss.nodes)}
                names = {i: n for n, i in index.items()}
                g_idx = {index[n] for n in ss.ground_nets}
                inputs = {index[n] for n in block.inputs}
                owned = {index[n] for n in block.nodes} - inputs - g_idx
                outside = {index[n] for n in every - set(block.nodes) if n in index} - owned
                fixed_out = g_idx | inputs | outside
                stamped = tuple(m for f in vs.ff if f.merge_block == block.key for m in f.members)
                a_mos, a_res, a_unk = BM._select(ss, owned, fixed_out, frozenset(excluded), frozenset(stamped))
                # ---- U9 집합 (block_gain_model_of 머리와 같은 계산: members = roles MOS, 밖 넷 attach>1 접지, 막다른 저항 제외)
                mos_by = {e["name"]: e for e in doc["netlist"]}
                res_by = {e["name"]: e for e in doc.get("passive_elements") or () if e["kind"] == "resistor"}
                u_mos = {n for n in roles if n in mos_by}
                u_res = {n for n in roles if n in res_by}
                u_ground = set(view_ground) | set(doc["supply_nets"])
                drive = {n for n in block.inputs if n not in u_ground}
                channel = {mos_by[m][t] for m in u_mos for t in ("drain", "source")}
                resistive = {t for r in u_res for t in res_by[r]["terminals"]}
                u_ground |= {n for n in channel | resistive if n not in block.nodes and n not in drive and attach.get(n, math.inf) > 1}
                active = set(u_res)
                while True:
                    degree = {}
                    for m in u_mos:
                        for t in ("drain", "source"):
                            degree[mos_by[m][t]] = degree.get(mos_by[m][t], 0) + 1
                    for r in active:
                        for t in res_by[r]["terminals"]:
                            degree[t] = degree.get(t, 0) + 1
                    dead = {r for r in active if any(t not in u_ground and t not in drive and degree[t] == 1 for t in res_by[r]["terminals"])}
                    if not dead:
                        break
                    active -= dead
                touched = {mos_by[m][t] for m in u_mos for t in ("drain", "source")} | {t for r in active for t in res_by[r]["terminals"]}
                u_unk = {n for n in touched if n not in u_ground and n not in drive}
                a_unk_names = {names[i] for i in a_unk}
                only_a_mos = sorted(a_mos - u_mos)
                only_u_mos = sorted(u_mos - a_mos)
                cases = []
                for m in only_a_mos:
                    e = mos_by[m]
                    other_block = sorted({str(b.key) for b in view.blocks if m in dict(b.roles)})
                    at = [t for t in ("drain", "source") if e[t] in a_unk_names]
                    cases.append({"device": m, "terminals_in_asbuilt_unknown": at, "member_of_other_block": other_block,
                                  "ff": m in excluded, "gate_is_block_input": e["gate"] in block.inputs,
                                  "other_end_in_asbuilt_unknown": all(e[t] in a_unk_names for t in ("drain", "source"))})
                gates_charge = sorted({mos_by[m]["gate"] for m in u_mos if mos_by[m]["gate"] in charge})
                if gates_charge:
                    block_gates_on_charge.append((vs.id, block.key, gates_charge))
                same_m, same_u = not only_a_mos and not only_u_mos, a_unk_names == u_unk
                totals["same_mos"] += same_m
                totals["same_unknown"] += same_u
                dead_res = sorted(u_res - active)
                totals["dead_end"] += bool(dead_res)
                emit({"circuit": name, "kind": "block", "view": vs.id, "block": block.key, "block_kind": block.kind, "same_mos": same_m, "same_unknown": same_u,
                      "only_asbuilt_mos": cases, "only_u9_mos": only_u_mos, "only_asbuilt_res": sorted(a_res - u_res), "only_u9_res": sorted(u_res - a_res),
                      "only_asbuilt_unknown": sorted(a_unk_names - u_unk), "only_u9_unknown": sorted(u_unk - a_unk_names), "u9_dead_end_res": dead_res,
                      "gates_on_charge_only": gates_charge})
            # ---- 체인 잔차(합성 값, 참고)
            got = block_residual(ss, decl, vs)
            proto, flagged = proto_residual(ss, decl, vs, raw_blocks, tuple(view.ac_ground))
            emit({"circuit": name, "kind": "chain_residual_synthetic", "view": vs.id, "asbuilt_db": got.gain_residual_db, "proto_s25_db": proto,
                  "load_devices_gate_on_driven": sorted(set(flagged))})
            say("  view", vs.id, "blocks", len(vs.blocks), "ff", len(vs.ff), "as-built residual", got.gain_residual_db, "proto", proto, "flagged", sorted(set(flagged)))
        emit({"circuit": name, "kind": "block_gate_on_charge_only", "rows": block_gates_on_charge})
    except Exception:  # noqa: BLE001 -- 측정 스크립트: 회로마다 실패를 기록하고 다음 회로로 간다
        emit({"circuit": name, "kind": "failure", "trace": traceback.format_exc()})
        say("## FAIL", name, traceback.format_exc())
say("totals", totals)
