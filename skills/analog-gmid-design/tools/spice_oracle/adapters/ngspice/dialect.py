# -*- coding: utf-8 -*-
"""adapters/ngspice/dialect.py -- IR·요청 -> ngspice 방언 텍스트 (design §4.2·§10.6, card 20261104-op23).

방언을 아는 곳은 이 파일(과 read.py)뿐이다. 소자 줄 작성기는 하나다(`device_line`). 기하 칸은 기술자 선언 단위 u 의 거듭제곱으로 나눈 숫자로 쓰고
(칸 목록·거듭제곱은 calibration.json `global_geometry_directive`), 전역 배율 지시 `.option scale = u` 줄을 직접 쓴다. 병렬 배수는 기술자
`parallel_multiplier.to` 의 모든 대상에 같은 값으로 넘긴다. R·C·L 값과 전원 값은 그대로다. 숫자 표기는 `format(x, ".10g")`.
"""
from __future__ import annotations

import json
import os
import re

from core.results import OracleError

_HERE = os.path.dirname(os.path.abspath(__file__))
# model_family 별 op 파라미터(코어 공통 이름) -- 같은 이름을 시뮬레이터 `@` 벡터 이름으로 쓴다
OP_PARAM_TABLES = {"bsim4": ("id", "gm", "gds", "vth", "vdsat", "vgs", "vds", "vbs")}
# 코어 공통 이름 -> 시뮬레이터가 보고하는 인스턴스 기하 칸 (design §6 name_map["geometry_fields"])
GEOMETRY_FIELDS = {"L": "l", "W": "w", "multiplier": "m", "ad": "ad", "pd": "pd"}
# 테스트벤치 원소 용도(`tb:<용도>:<대상>`) -> 방언 이름 접두사 (이름 접두사는 방언 규약, S-9)
PURPOSE_PREFIX = {"rail": "Vrail_", "fb": "Efb_", "ofs": "Vofs_", "fbl": "Lfb_", "dc": "Vdc_", "dcl": "Ldc_", "cac": "Cac_",
                  "vac": "Vac_", "bias": "Vbias_", "hold": "Vhold_", "holdl": "Lhold_", "lb": "Vlb_", "ilb": "Ilb_",
                  "short": "Vshort_", "iso_g": "Viso_g_", "iso_d": "Viso_d_", "iso_b": "Viso_b_", "rout": "Irout_"}
CIRCUIT_PREFIX = {"Mos": "X", "Resistor": "Rp_", "Capacitor": "Cp_", "Inductor": "Lp_", "ISource": "Isrc_", "VSource": "Vsrc_",
                  "Vcvs": "Ep_"}
LETTER = {"Mos": "X", "Resistor": "R", "Capacitor": "C", "Inductor": "L", "ISource": "I", "VSource": "V", "Vcvs": "E"}
# AC 항을 쓰는 테스트벤치 원소 용도 (여기 원)
AC_PURPOSES = ("vac", "lb", "ilb", "rout")


def fmt(x) -> str:
    return format(float(x), ".10g")


def load_calibration() -> dict:
    with open(os.path.join(_HERE, "calibration.json"), encoding="utf-8") as f:
        return json.load(f)


def _text(descriptor, spec):
    return spec["value"] if "value" in spec else descriptor.text(spec)


def _path(p):
    return p.replace("\\", "/")


# ---------------------------------------------------------------- 소자 줄
def _geometry_value(field_path, value, unit_u, powers):
    return value / (unit_u ** powers[field_path]) if field_path in powers else value


def device_line(mos, name_str, unit_u, to) -> str:
    """MOS 한 줄: X<이름> d g s b <호출 이름> l= w= <배수 대상들> [ad= as= pd= ps=] [sa= sb= sd=].
    unit_u = 기하 단위 u(m; 'si' 는 1.0), to = [{'target': 'instance_multiplier'} | {'target': 'model_param', 'name': str}] (이름은 풀린 꼴)."""
    pw = load_calibration()["global_geometry_directive"]["power"]
    g = lambda path, v: fmt(_geometry_value(path, float(v), unit_u, pw))     # noqa: E731
    parts = [f"X{mos.name}", mos.d, mos.g, mos.s, mos.b, name_str, f"l={g('Mos.L', mos.L)}", f"w={g('Mos.finger_w', mos.finger_w)}"]
    for t in to:
        parts.append(f"m={int(mos.n_fingers)}" if t["target"] == "instance_multiplier" else f"{t['name']}={int(mos.n_fingers)}")
    if mos.diffusion is not None:
        d = mos.diffusion
        parts += [f"ad={g('Mos.diffusion.ad', d.ad)}", f"as={g('Mos.diffusion.as_', d.as_)}",
                  f"pd={g('Mos.diffusion.pd', d.pd)}", f"ps={g('Mos.diffusion.ps', d.ps)}"]
    if mos.lod is not None:
        parts += [f"sa={g('Mos.lod.sa', mos.lod.sa)}", f"sb={g('Mos.lod.sb', mos.lod.sb)}", f"sd={g('Mos.lod.sd', mos.lod.sd)}"]
    return " ".join(parts)


# ---------------------------------------------------------------- 이름 대응
def _sanitize(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.]", "_", s)


def build_name_map(circuit) -> dict:
    """IR 원소 이름 -> 방언 이름. 단사(대소문자 접기 포함)이고 모든 원소를 덮는다."""
    out, used = {}, set()
    for e in circuit.elements:
        cls = type(e).__name__
        if circuit.role.get(e.name) == "circuit":
            base = CIRCUIT_PREFIX[cls] + _sanitize(e.name)
        else:
            parts = e.name.split(":")
            purpose = parts[1] if len(parts) >= 3 and parts[0] == "tb" else None
            if purpose in PURPOSE_PREFIX and PURPOSE_PREFIX[purpose][0] == LETTER[cls]:
                base = PURPOSE_PREFIX[purpose] + _sanitize(":".join(parts[2:]))
            else:
                base = LETTER[cls] + "tb_" + _sanitize(e.name)
        name, i = base, 1
        while name.lower() in used:
            i += 1
            name = f"{base}_{i}"
        used.add(name.lower())
        out[e.name] = name
    return out


def _purpose(e):
    p = e.name.split(":")
    return p[1] if len(p) >= 3 and p[0] == "tb" else None


# ---------------------------------------------------------------- 식·요청
def _expr(ex, nm) -> str:
    k = type(ex).__name__
    if k == "NodeV":
        return f"v({ex.net})"
    if k == "DiffV":
        return f"v({ex.net_p}) - v({ex.net_n})"
    if k == "BranchI":
        return f"i({nm[ex.element].lower()})"
    if k == "Ratio":
        return f"({_expr(ex.num, nm)})/({_expr(ex.den, nm)})"
    raise TypeError(f"식 밖: {k}")


def data_file(rid: str) -> str:
    """요청 id -> 데이터 파일 이름 (작업 폴더 안 상대 이름)."""
    return f"bench.{_sanitize(rid)}.txt"


def op_marker(rid: str, end: bool) -> str:
    return f"{'OPEND' if end else 'OPSTART'}_{_sanitize(rid)}"


def probe(inst_lower: str, inner: str | None, param: str) -> str:
    return f"@m.{inst_lower}.{inner}[{param}]" if inner else f"@{inst_lower}[{param}]"


def _mos_probe_info(circuit, descriptor, nm):
    """MOS 이름 -> (인스턴스 소문자 이름, 내부 소자 이름 | None, 극성, model_family 파라미터 목록)."""
    fam = descriptor.doc["model_family"]
    params = OP_PARAM_TABLES.get(fam, ())       # 표에 없는 model_family 는 파라미터 0개 -- 값을 지어 넣지 않는다(코어가 능력 model_families 로 먼저 거른다)
    out = {}
    for e in circuit.elements:
        if type(e).__name__ == "Mos":
            kd = descriptor.doc["kinds"][e.kind]
            inner = kd.get("inner_device")
            out[e.name] = (nm[e.name].lower(), None if inner is None else _text(descriptor, inner).lower(), params)
    return out


def _control(circuit, requests, nm, descriptor):
    L = [".control", "set noaskquit", "set wr_singlescale"]
    byname = {e.name: e for e in circuit.elements}
    info = _mos_probe_info(circuit, descriptor, nm)
    for r in requests:
        kind = type(r).__name__
        if kind == "Op":
            L.append("op")
            L.append(f"echo {op_marker(r.id, False)}")
            names = list(info) if r.outputs.devices == "all" else list(r.outputs.devices)
            for n in names:
                inst, inner, params = info[n]
                L += [f"print {probe(inst, inner, p)}" for p in params]
                L += [f"print {probe(inst, inner, f)}" for f in GEOMETRY_FIELDS.values()]
            L += [f"print v({n})" for n in r.outputs.nodes]
            L += [f"print i({nm[c].lower()})" for c in r.outputs.currents]
            L.append(f"echo {op_marker(r.id, True)}")
        elif kind == "Ac":
            for (el, field, val) in r.exc:
                L.append(f"alter @{nm[el].lower()}[{'acmag' if field == 'ac_mag' else field}] = {fmt(val)}")
            if r.f_list is not None:
                if len(r.f_list) != 1:
                    raise OracleError("adapter_capability_missing", "ac_f_list", "5")
                L.append(f"ac lin 1 {fmt(r.f_list[0])} {fmt(r.f_list[0])}")
            else:
                L.append(f"ac dec {int(r.points_per_decade)} {fmt(r.f_start)} {fmt(r.f_stop)}")
            names = []
            for k, ex in enumerate(r.outputs):
                L.append(f"let o{k} = {_expr(ex, nm)}")
                names.append(f"o{k}")
            L.append(f"wrdata {data_file(r.id)} {' '.join(names)}")
            for (el, field, val) in r.exc:           # 덮어쓰기는 이 요청에서만 -- 다음 요청이 본 회로 값으로 돌아오게 되돌린다
                base = getattr(byname[el], "ac_mag" if field == "ac_mag" else field)
                L.append(f"alter @{nm[el].lower()}[{'acmag' if field == 'ac_mag' else field}] = {fmt(base)}")
        else:
            raise OracleError("adapter_capability_missing", kind.lower(), "5")
    L += ["quit", ".endc", ".end"]
    return L


# ---------------------------------------------------------------- 전체
def render(circuit, requests, descriptor, cond, options):
    """(텍스트, name_map). 줄 끝 \\n. .temp, include, .option, 소자 줄, .control 포함."""
    nm = build_name_map(circuit)
    kinds = sorted({e.kind for e in circuit.elements if type(e).__name__ == "Mos"})
    units = {}
    for k in kinds:
        kd = descriptor.doc["kinds"][k]
        gu, pm = kd.get("geometry_unit"), kd.get("parallel_multiplier")
        if gu is None or pm is None:
            raise OracleError("descriptor_geometry_undeclared", {"kind": k, "missing": [n for n, v in (("geometry_unit", gu), ("parallel_multiplier", pm)) if v is None]}, "3")
        units[k] = 1.0 if gu == "si" else float(descriptor.quantity(gu["source"]))
    if len(set(units.values())) > 1:
        raise OracleError("adapter_capability_missing", "geometry_unit_application", "5")   # 전역 배율 지시는 하나뿐이다
    u = next(iter(units.values())) if units else 1.0
    L = [f"* spice_oracle bench ({len(circuit.elements)} elements)"]
    seen = set()
    for k in kinds:
        for inc in descriptor.doc["kinds"][k]["includes"]:
            p = _path(descriptor.source_path(inc["source"]))
            if p not in seen:
                seen.add(p)
                L.append(f'.include "{p}"')
    L.append(f".temp {fmt(cond.temp_c)}")
    if u != 1.0:
        L.append(f".option scale={fmt(u)}")
    if options:
        L.append(".option " + " ".join(f"{k}={v}" for k, v in options.items()))
    for e in circuit.elements:
        cls = type(e).__name__
        name = nm[e.name]
        if cls == "Mos":
            kd = descriptor.doc["kinds"][e.kind]
            to = [dict(t, name=_text(descriptor, t["name"])) if "name" in t else dict(t) for t in kd["parallel_multiplier"]["to"]]
            ln = device_line(e, _text(descriptor, kd["name"]), units[e.kind], to).split(" ", 1)[1]
            L.append(f"{name} {ln}")
        elif cls in ("Resistor", "Capacitor", "Inductor"):
            L.append(f"{name} {e.a} {e.b} {fmt(e.value)}")
        elif cls in ("VSource", "ISource"):
            ac = f" AC {fmt(e.ac_mag)}" if (e.ac_mag != 0 or _purpose(e) in AC_PURPOSES) else ""
            L.append(f"{name} {e.p} {e.n} DC {fmt(e.dc)}{ac}")
        elif cls == "Vcvs":
            L.append(f"{name} {e.p} {e.n} {e.cp} {e.cn} {fmt(e.gain)}")
        else:
            raise TypeError(f"IR 원소 밖: {cls}")
    ns = circuit.meta.get("nodeset") or []
    step = max(1, int(circuit.meta.get("nodeset_per_line", len(ns) or 1)))
    for i in range(0, len(ns), step):
        L.append(".nodeset " + " ".join(f"v({n})={fmt(v)}" for n, v in ns[i:i + step]))
    L += _control(circuit, requests, nm, descriptor)
    out_map = dict(nm)
    out_map["geometry_fields"] = dict(GEOMETRY_FIELDS)
    return "\n".join(L) + "\n", out_map
