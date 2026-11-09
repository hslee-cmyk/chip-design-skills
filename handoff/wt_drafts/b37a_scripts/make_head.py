"""B37a 개정 card(v2) 모의 head: C:/g68/base(= git archive 7535799) + 범위 1~4(개정).

개정 반영: (B2) 명시적 `ports: {}` 수용(입력·출력 0), 포트 넷 존재 검사, 포트 ∩ 레일 거부(B26-1 전이라
레일 = raw `supply_nets` 대역), offset 쌍이 있는데 입력 0이면 input_referred_offset_pairs 거부 유지.
거부 예외는 CC-4a 전이라 ValueError 대역. 치환 대상은 정확히 1회 나오는지 assert.
사용: python -B make_head.py <dst_dir>   (dst_dir = C:/g68/head 등, base를 통째로 복사한 뒤 패치)
"""
import ast, os, shutil, sys

BASE = "C:/g68/base"
DST = sys.argv[1] if len(sys.argv) > 1 else "C:/g68/head"
A = "skills/analog-gmid-design/assets"
SD = A + "/stick_diagram.py"
SR = A + "/sizing_recipe.py"


def sub(src, old, new, count=1):
    n = src.count(old)
    assert n == count, (n, old[:120])
    return src.replace(old, new)


def patch_sd(src):
    accessor = '''
_PORT_ROLE_SIDE = {
    "single_ended_input": "input", "differential_input_p": "input", "differential_input_n": "input",
    "single_ended_output": "output", "differential_output_p": "output", "differential_output_n": "output",
}


@dataclass(frozen=True)
class PortDeclaration:
    inputs: tuple
    outputs: tuple


def port_declaration(topology: dict) -> PortDeclaration:
    """topology 최상위 `ports`(사람 선언)를 role로 읽는다(B37a mock).

    검사하지 않는 것: 포트 넷이 netlist에 있는가, 레일과 겹치는가(load_topology가 본다)."""
    if "ports" not in topology:
        raise ValueError("ports: 선언이 없다(DEC-62)")
    ports = topology["ports"]
    if not isinstance(ports, dict):
        raise ValueError("ports: dict가 아니다(DEC-62)")
    ins, outs = [], []
    for net, entry in ports.items():
        if net.startswith("_"):
            continue
        if not net:
            raise ValueError("ports: 빈 넷 이름(DEC-62)")
        if not isinstance(entry, dict) or "role" not in entry:
            raise ValueError("ports: 항목 형식 오류 %r(DEC-62)" % net)
        side = _PORT_ROLE_SIDE.get(entry["role"])
        if side is None:
            raise ValueError("ports: role 어휘 밖 %r(DEC-62)" % net)
        if "direction" in entry and entry["direction"] != side:
            raise ValueError("ports: direction과 role 모순 %r(DEC-62)" % net)
        (ins if side == "input" else outs).append(net)
    return PortDeclaration(tuple(sorted(ins)), tuple(sorted(outs)))


def load_topology(json_path: str) -> tuple[list[Transistor], dict]:'''
    src = sub(src, "\ndef load_topology(json_path: str) -> tuple[list[Transistor], dict]:", accessor)
    src = sub(src, '''    data = _read_one(json_path)
    all_netlist = list(data["netlist"])''', '''    data = _read_one(json_path)
    ports = port_declaration(data)
    all_netlist = list(data["netlist"])''')
    src = sub(src, '''    all_ideal_sources = list(data.get("ideal_sources") or [])

    linked =''', '''    all_ideal_sources = list(data.get("ideal_sources") or [])
    all_passive = list(data.get("passive_elements") or [])

    linked =''')
    src = sub(src, '''        linked_data = _read_one(os.path.join(base_dir, rel_path))
        all_netlist.extend(linked_data["netlist"])''', '''        linked_data = _read_one(os.path.join(base_dir, rel_path))
        if "ports" in linked_data and port_declaration(linked_data) != ports:
            raise ValueError("ports: 연결 파일 선언이 진입 파일과 다르다 %s(DEC-62)" % rel_path)
        all_passive.extend(linked_data.get("passive_elements") or [])
        all_netlist.extend(linked_data["netlist"])''')
    src = sub(src, '''    _name_verdict = check_topology_name_uniqueness(''', '''    _terminals = {n for t in transistors for n in (t.source, t.drain, t.gate)}
    _terminals |= {n for e in all_passive + all_ideal_sources for n in (e.get("terminals") or [])}
    _missing = [n for n in ports.inputs + ports.outputs if n not in _terminals]
    if _missing:
        raise ValueError("ports: netlist에 없는 넷 %r(DEC-62)" % _missing)
    _on_rail = sorted(set(ports.inputs + ports.outputs) & set(data.get("supply_nets") or []))
    if _on_rail:
        raise ValueError("ports: 레일과 겹치는 포트 %r(DEC-62)" % _on_rail)
    _name_verdict = check_topology_name_uniqueness(''')
    src = sub(src, '''    _vsid_gap_fill = propose_vertical_stack_id_gap_fill(
        transistors, _vsid_forced_pairs, all_device_roles)''', '''    _vsid_gap_fill = propose_vertical_stack_id_gap_fill(
        transistors, _vsid_forced_pairs, all_device_roles,
        inputs=ports.inputs, outputs=ports.outputs)''')
    src = sub(src, '''        vds_theta_authoritative=find_authoritative_sizing_devices(data))
    # 2026-08-14 -- device_roles_proposals''', '''        vds_theta_authoritative=find_authoritative_sizing_devices(data),
        inputs=ports.inputs, outputs=ports.outputs)
    # 2026-08-14 -- device_roles_proposals''')
    src = sub(src, '''        "_device_roles_gap_fill_review_needed": _droles_gap_fill["review_needed"] or None,
    }
    return transistors, meta''', '''        "_device_roles_gap_fill_review_needed": _droles_gap_fill["review_needed"] or None,
        "ports": ports,
    }
    return transistors, meta''')
    return src


def patch_sr(src):
    src = sub(src, '''def resolve_stack_layout(transistors: list, matching_pairs: list, device_roles: dict,
                          stack_groups_override: dict | None = None) -> dict:''', '''def resolve_stack_layout(transistors: list, matching_pairs: list, device_roles: dict,
                          stack_groups_override: dict | None = None, *, ports) -> dict:''')
    src = sub(src, '''    refined = refine_differential_and_mirror_relations(transistors)
    if refined is not None and refined.get("vertical_stack_id_candidates"):''', '''    refined = refine_differential_and_mirror_relations(transistors, ports.inputs, ports.outputs)
    if refined is not None and refined.get("vertical_stack_id_candidates"):''')
    src = sub(src, '''        stack_groups_override=spec.get("stack_groups_override"))
    stack_id_of =''', '''        stack_groups_override=spec.get("stack_groups_override"), ports=meta["ports"])
    stack_id_of =''')
    old_body = src[src.index('''    if "input_offset_pairs" not in entry:
        ports = entry["ports"]'''):src.index('''        entry["input_offset_pairs"] = out
    return entry["input_offset_pairs"]''')]
    new_body = '''    if "input_offset_pairs" not in entry:
        in_nets = set(entry["meta"]["ports"].inputs)
        by_name = entry["by_name"]
        offset = [list(p.get("names") or []) for p in entry["matching_pairs"]
                  if p.get("matching_sensitivity") == "offset" and len(p.get("names") or []) >= 2]
        if offset and not in_nets:
            raise ValueError(
                f"{topology_path}: offset 쌍이 있는데 `ports`에 입력 role 넷이 없다(DEC-62)")
        out = []
        for names in offset:
            if all(n in by_name and by_name[n].gate in in_nets for n in names):
                out.append(list(names))
'''
    assert src.count(old_body) == 1
    src = src.replace(old_body, new_body)
    src = sub(src, '''            # 2026-09-10 -- `input_referred_offset_pairs()`가 "게이트가 **신호 입력**에
            # 물렸는가"를 판정하는 데 쓴다. raw는 여기서 이미 읽고 있으므로 비용 0.
            "ports": (raw.get("ports") or {}),
''', "")
    return src


def main():
    if os.path.exists(DST):
        shutil.rmtree(DST)
    shutil.copytree(BASE, DST)
    for rel, fn in ((SD, patch_sd), (SR, patch_sr)):
        p = os.path.join(DST, rel)
        with open(p, encoding="utf-8", newline="") as fh:
            s = fh.read()
        crlf = "\r\n" in s
        s2 = fn(s.replace("\r\n", "\n"))
        ast.parse(s2)
        if crlf:
            s2 = s2.replace("\n", "\r\n")
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(s2)
    print("head built", DST)


if __name__ == "__main__":
    main()
