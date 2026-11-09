"""#21(mg1-rail-voltage) meta/instance 영향 실측용 시제품 패치 (draft_phase4_design.md v0.9.2 §5.4 #21, §10.4).

사용: python -B patch.py <root> <variant>
  p1  : B26-1 계약 1·2 시제품 (SD RailDeclaration(nets)·rail_declaration(topology), load_topology가 진입 파일로 정확히 한 번 불러
        meta["rails"]에 싣고, 연결 파일 선언은 같은 형식 검사 + 집합 다르면 ValueError)
  p20 : p1 + CC-5 최소 시제품(#21의 선행 #20 -- LEGACY_NAMES 표 + reject_legacy_names + load_topology의 파일 읽기 직후 where="topology"
        검사, 행은 `vs`(/device_roles/*) 하나)
  p21 : p20 + #21 시제품 -- (1) LEGACY_NAMES MG1 행 3개(harness_spec 루트 `supplies`·`vdd`, topology /sizing_roles/metrics/* `supply_nets`)
        (2) 하네스 SPECS 4회로 스칼라 `vdd` -> `supplies_v`(two_stage·current_reuse·folded {vdd 1.8, gnd 0.0}, nmcnr {vdd 1.8, vss 0.0}),
        spec_fn() 반환 직후 reject_legacy_names(spec, "harness_spec") 2곳 (3) SR RailVoltages·rail_voltages(spec, rails)
        (_build_theta_evaluator의 load_topology 직후 1회 -- set(supplies_v) != rails.nets 거부) (4) F4 20줄 + 레일 0 V 리터럴 3곳을
        §10.4 분류표대로 span/hi/lo/hi+lo로 교체. 값은 spec 밖 보관(spec dict에 키를 더하지 않음).
  x1  : p21, 단 metric `supply_nets` 행의 scope를 ""(문서 루트)로 잘못 둔 판 (음성 대조)
  x2  : p21 + load_topology가 meta["rail_voltages"]를 더하는 판(전압을 로드 결과에 싣는 잘못된 보관 위치, 음성 대조)
  x4  : p21 + RailDeclaration에 voltages 필드(topology _declared_target_spec.supplies_v)를 더한 판 (음성 대조)
  x3  : p21, 단 harness_spec `vdd` 행이 하위 전체(자손)를 훑는 판 (음성 대조 -- supplies_v/vdd를 거부해야 함)
"""
import os, re, sys
root, variant = sys.argv[1], sys.argv[2]
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
SD, SR, H = os.path.join(A, "stick_diagram.py"), os.path.join(A, "sizing_recipe.py"), os.path.join(root, "workspaces", "run_harness.py")

_CRLF = {}
def rd(p):
    t = open(p, encoding="utf-8", newline="").read()
    _CRLF[p] = chr(13) + chr(10) in t
    return t.replace(chr(13) + chr(10), chr(10))
def wr(p, t): open(p, "w", encoding="utf-8", newline="").write(t.replace(chr(10), chr(13) + chr(10)) if _CRLF.get(p) else t)
def rep(t, old, new, n=1):
    c = t.count(old)
    assert c == n, (c, n, old[:100])
    return t.replace(old, new)

def b26_1():
    t = rd(SD)
    t = t.rstrip("\n") + '''


@dataclass(frozen=True)
class RailDeclaration:
    nets: frozenset


def rail_declaration(topology: dict) -> RailDeclaration:
    """B26-1 계약 1 시제품(c21 측정용)."""
    if "supply_nets" not in topology:
        raise ValueError("supply_nets 선언 없음(DEC-60)")
    v = topology["supply_nets"]
    if not isinstance(v, list):
        raise ValueError("supply_nets가 list가 아님(DEC-60)")
    if any((not isinstance(x, str)) or x == "" for x in v):
        raise ValueError("supply_nets 원소 오류(DEC-60)")
    if len(set(v)) != len(v):
        raise ValueError("supply_nets 중복(DEC-60)")
    return RailDeclaration(nets=frozenset(v))
'''
    t = rep(t, "    data = _read_one(json_path)\n    all_netlist = list(data[\"netlist\"])\n",
            "    data = _read_one(json_path)\n    _rails = rail_declaration(data)\n    all_netlist = list(data[\"netlist\"])\n")
    t = rep(t, "        linked_data = _read_one(os.path.join(base_dir, rel_path))\n",
            "        linked_data = _read_one(os.path.join(base_dir, rel_path))\n"
            "        if \"supply_nets\" in linked_data and rail_declaration(linked_data).nets != _rails.nets:\n"
            "            raise ValueError(\"linked supply_nets mismatch\")\n")
    t = rep(t, "        \"topology_name\": data[\"topology_name\"],\n", "        \"topology_name\": data[\"topology_name\"],\n        \"rails\": _rails,\n")
    wr(SD, t)

def cc5_min():
    t = rd(SD)
    t = t.rstrip("\n") + '''


@dataclass(frozen=True)
class LegacyName:
    old: str
    new: str
    where: str
    scope: str     # JSON pointer, 세그먼트 "*" = 아무 키. "" = 문서 루트(JSON pointer 정의)
    match: str     # "key"
    stage: str
    reason: str
    descend: bool = False   # x3 음성 대조 전용: scope 아래 자손 매핑의 키까지 훑는다


LEGACY_NAMES = [
    LegacyName("vs", "vsb", "topology", "/device_roles/*", "key", "MG0", "B9 개명"),
]


def _ln_locate(doc, segs):
    if not segs:
        yield doc
        return
    if not isinstance(doc, Mapping):
        return
    s, rest = segs[0], segs[1:]
    if s == "*":
        for v in doc.values():
            yield from _ln_locate(v, rest)
    elif s in doc:
        yield from _ln_locate(doc[s], rest)


def _ln_mappings(x, descend):
    if isinstance(x, Mapping):
        yield x
        if descend:
            for v in x.values():
                yield from _ln_mappings(v, descend)
    elif descend and isinstance(x, list):
        for v in x:
            yield from _ln_mappings(v, descend)


def reject_legacy_names(doc, where: str) -> None:
    hits = []
    for row in LEGACY_NAMES:
        if row.where != where:
            continue
        segs = [s for s in row.scope.split("/")[1:]] if row.scope else []
        for loc in _ln_locate(doc, segs):
            for m in _ln_mappings(loc, row.descend):
                if row.old in m:
                    hits.append((row.scope, row.old, row.new, row.stage))
    if hits:
        raise ValueError("SCHEMA_REJECTED legacy_names where=%s hits=%r" % (where, hits))
'''
    t = rep(t, "        with open(path, \"r\", encoding=\"utf-8\") as f:\n            return json.load(f)\n\n    data = _read_one(json_path)\n",
            "        with open(path, \"r\", encoding=\"utf-8\") as f:\n            _d = json.load(f)\n        reject_legacy_names(_d, \"topology\")\n        return _d\n\n    data = _read_one(json_path)\n")
    wr(SD, t)

SPAN_SITES = {  # §10.4 분류표: 폭·노드전압 프레임 인자 = span
    '    vdd = ctx.spec.get("vdd")\n': '    vdd = _rv_span_or_none(ctx.spec)\n',
    '    vdd = ctx.spec["vdd"]\n': '    vdd = _rv_of(ctx.spec).span\n',
    '    vdd = spec["vdd"]\n': '    vdd = _rv_of(spec).span\n',
    '    base_budget = spec["vdd"]\n': '    base_budget = _rv_of(spec).span\n',
    '        base_budget = spec["vdd"] - ref_vds\n': '        base_budget = _rv_of(spec).span - ref_vds\n',
    '                        member_cap = spec["vdd"] - reserved\n': '                        member_cap = _rv_of(spec).span - reserved\n',
    "VDS 합이 vdd({spec['vdd']}V)를": "VDS 합이 vdd({_rv_of(spec).span}V)를",
    'vds_kvl_groups=comp.get("vds_kvl_groups"), vdd=spec.get("vdd"),': 'vds_kvl_groups=comp.get("vds_kvl_groups"), vdd=_rv_span_or_none(spec),',
    '        _vsb_vdd = spec.get("vdd")\n': '        _vsb_vdd = _rv_span_or_none(spec)\n',
}

def mg1(mis_scope_supply_nets=False, descend_vdd=False):
    # (1) LEGACY_NAMES MG1 행
    t = rd(SD)
    sn_scope = "" if mis_scope_supply_nets else "/sizing_roles/metrics/*"
    t = rep(t, '    LegacyName("vs", "vsb", "topology", "/device_roles/*", "key", "MG0", "B9 개명"),\n]\n',
            '    LegacyName("vs", "vsb", "topology", "/device_roles/*", "key", "MG0", "B9 개명"),\n'
            '    LegacyName("supplies", "supplies_v", "harness_spec", "", "key", "MG1", "DEC-60 레일 전압"),\n'
            '    LegacyName("vdd", "supplies_v", "harness_spec", "", "key", "MG1", "DEC-60 레일 전압", %s),\n'
            '    LegacyName("supply_nets", "(삭제 -- 레일별 기록)", "topology", "%s", "key", "MG1", "공급 전류 셀 레일"),\n]\n'
            % ("True" if descend_vdd else "False", sn_scope))
    wr(SD, t)
    # (2) 하네스 SPECS + 게이트 배선
    h = rd(H)
    old = '        "vdd": 1.8,\n'
    assert h.count(old) == 4, h.count(old)
    parts = h.split(old)
    vals = ['{"vdd": 1.8, "gnd": 0.0}'] * 3 + ['{"vdd": 1.8, "vss": 0.0}']
    h = parts[0] + "".join('        "supplies_v": %s,\n' % v + p for v, p in zip(vals, parts[1:]))
    # 순서 확인: two_stage, current_reuse, folded, nmcnr
    order = [m.start() for m in re.finditer(r"^def _spec_(two_stage_ota|current_reuse_telescopic_ota|folded_cascode|nmcnr_amplifier)\(", h, re.M)]
    names = re.findall(r"^def _spec_(two_stage_ota|current_reuse_telescopic_ota|folded_cascode|nmcnr_amplifier)\(", h, re.M)
    assert names == ["two_stage_ota", "current_reuse_telescopic_ota", "folded_cascode", "nmcnr_amplifier"], names
    sv = [m.start() for m in re.finditer(r'"supplies_v": ', h)]
    assert all(order[i] < sv[i] < (order[i + 1] if i + 1 < 4 else len(h)) for i in range(4)), (order, sv)
    h = rep(h, "from stick_diagram import save_instance_json, run_full_circuit_audit_from_topology\n",
            "from stick_diagram import save_instance_json, run_full_circuit_audit_from_topology, reject_legacy_names\n")
    h = rep(h, '    return SPECS[circuit_key]["spec_fn"]()\n',
            '    _s = SPECS[circuit_key]["spec_fn"]()\n    reject_legacy_names(_s, "harness_spec")\n    return _s\n')
    h = rep(h, '    spec = cfg["spec_fn"]()\n', '    spec = cfg["spec_fn"]()\n    reject_legacy_names(spec, "harness_spec")\n')
    wr(H, h)
    # (3)(4) SR
    t = rd(SR)
    for o, n in SPAN_SITES.items():
        t = rep(t, o, n)
    # 노드전압 프레임 인자(7290·7295·7296, 7445·7449·7450) = span
    t = rep(t, '                    if spec.get("vdd") is not None:\n', '                    if _rv_span_or_none(spec) is not None:\n')
    t = rep(t, '            if spec.get("vdd") is not None:\n', '            if _rv_span_or_none(spec) is not None:\n')
    t = rep(t, '_bn_pair, ctx.sized, spec["vdd"]).nodes,\n', '_bn_pair, ctx.sized, _rv_of(spec).span).nodes,\n', n=2)
    t = rep(t, '                                spec["vdd"])\n', '                                _rv_of(spec).span)\n')
    t = rep(t, '                        spec["vdd"])\n', '                        _rv_of(spec).span)\n')
    # hi / lo / hi+lo
    t = rep(t, '    rail_v = ctx.spec["vdd"] if spec["rail"] == "vdd" else 0.0\n',
            '    rail_v = _rv_of(ctx.spec).hi if spec["rail"] == "vdd" else _rv_of(ctx.spec).lo\n')
    t = rep(t, '    return abs((high + low) - ctx.spec["vdd"])\n', '    return abs((high + low) - (_rv_of(ctx.spec).hi + _rv_of(ctx.spec).lo))\n')
    t = rep(t, '        level_h = (spec["vdd"] - vgs_h) if kind_of[high] == "pmos" else (0.0 + vgs_h)\n',
            '        level_h = (_rv_of(spec).hi - vgs_h) if kind_of[high] == "pmos" else (_rv_of(spec).lo + vgs_h)\n')
    t = rep(t, '        level_l = (spec["vdd"] - vgs_l) if kind_of[low] == "pmos" else (0.0 + vgs_l)\n',
            '        level_l = (_rv_of(spec).hi - vgs_l) if kind_of[low] == "pmos" else (_rv_of(spec).lo + vgs_l)\n')
    t = rep(t, '        return abs((level_h + level_l) - spec["vdd"])\n', '        return abs((level_h + level_l) - (_rv_of(spec).hi + _rv_of(spec).lo))\n')
    t = rep(t, "spec['vdd']가 없다", "spec['supplies_v']가 없다")  # 오류 메시지 문구(읽기 아님)
    left = re.findall(r'spec(?:\.get\("vdd"\)|\["vdd"\]|\[\'vdd\'\])', t)
    assert not left, left
    # rail_voltages 정의 + 평가 문맥 1회 호출
    t = rep(t, "    transistors, meta = load_topology(topology_path)\n",
            "    transistors, meta = load_topology(topology_path)\n    rail_voltages(spec, meta[\"rails\"])  # c21: set(supplies_v) == rails.nets 게이트\n")
    t = t.rstrip("\n") + '''


@dataclass(frozen=True)
class RailVoltages:
    by_net: dict
    hi: float
    lo: float

    @property
    def span(self) -> float:
        return self.hi - self.lo


_RV_CACHE = {}   # id(spec) -> (spec, RailVoltages): spec dict 밖 보관(시제품 -- 실제 card는 ctx)
_RV_CALLS = {"build": 0, "read": 0}


def _rv_build(sv):
    sv = {k: float(v) for k, v in sv.items()}
    return RailVoltages(by_net=sv, hi=max(sv.values()), lo=min(sv.values()))


def rail_voltages(spec, rails):
    sv = spec.get("supplies_v")
    if sv is None or set(sv) != set(rails.nets):
        raise ValueError("SCHEMA_REJECTED supplies_v %r != supply_nets %r" % (sorted(sv or {}), sorted(rails.nets)))
    return _rv_of(spec)


def _rv_of(spec):
    _RV_CALLS["read"] += 1
    ent = _RV_CACHE.get(id(spec))
    if ent is None or ent[0] is not spec:
        _RV_CALLS["build"] += 1
        ent = (spec, _rv_build(spec["supplies_v"]))
        _RV_CACHE[id(spec)] = ent
    return ent[1]


def _rv_span_or_none(spec):
    return _rv_of(spec).span if spec.get("supplies_v") is not None else None
'''
    wr(SR, t)

def rd_field():
    # x4: 전압을 RailDeclaration 필드로 싣는 판(Phase 3 E5식 '계약값 nets만 보는' 판정기가 놓치는지 대조)
    t = rd(SD)
    t = rep(t, "class RailDeclaration:\n    nets: frozenset\n", "class RailDeclaration:\n    nets: frozenset\n    voltages: object = None\n")
    t = rep(t, "    return RailDeclaration(nets=frozenset(v))\n",
            "    return RailDeclaration(nets=frozenset(v), voltages=(topology.get(\"_declared_target_spec\") or {}).get(\"supplies_v\"))\n")
    wr(SD, t)

def meta_rv():
    t = rd(SD)
    t = rep(t, "        \"rails\": _rails,\n",
            "        \"rails\": _rails,\n        \"rail_voltages\": (data.get(\"_declared_target_spec\") or {}).get(\"supplies_v\"),\n")
    wr(SD, t)

if variant in ("p1", "p20", "p21", "x1", "x2", "x3", "x4"):
    b26_1()
if variant in ("p20", "p21", "x1", "x2", "x3", "x4"):
    cc5_min()
if variant in ("p21", "x2", "x4"):
    mg1()
if variant == "x1":
    mg1(mis_scope_supply_nets=True)
if variant == "x3":
    mg1(descend_vdd=True)
if variant == "x2":
    meta_rv()
if variant == "x4":
    rd_field()
print("patched", root, variant)
