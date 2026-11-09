# GC-B7 착수 실측: library 13에서 θ 전류 기저 저항 수와 그중 양 끝이 레일이 아닌 넷 수 (평가 0, LUT 0).
# 사용: python measure_gcb7.py <engine_skill_root> <out.jsonl>. 저장소 쓰기 0(바이트코드 없음).
# 엔진 인용 용도 = 엔진 밖 사실 측정 도구(원칙 8). 필드 = graph.dc_current_basis.free(= θ `current` 성분, theta_schema).
import json, os, pathlib, sys, traceback
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
SKILL = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(SKILL))
import gmid_engine.search  # noqa
import gmid_engine.pipeline  # noqa
from gmid_engine.authoring import load_topology, load_sizing_spec
from gmid_engine.core import GraphSnapshot, SchemaRejectedError
from gmid_engine.graph import build_s1, s1_symmetry, load_structure_facts, structure_rule_fp, supplies_declaration, ELEMENT_PASSIVE, ELEMENT_SOURCE, NO_MARKS
from gmid_engine.search import open_run
from gmid_engine.sizing import dc_inputs_from_spec, symmetry_marks
sa = sys.modules["gmid_engine.pipeline.stage_a"]
ck = sys.modules["gmid_engine.sizing.kernel_context"]
LIB = SKILL / "assets" / "library"
names = sorted(p.name[:-len(".topology.json")] for p in LIB.glob("*.topology.json") if not p.name.startswith("_"))
OUT.write_text("", encoding="utf-8")


def app(row):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


tot = {"circuits": 0, "theta_R": 0, "both_nonrail": 0, "circuits_nonzero": 0, "errors": 0}
for c in names:
    row = {"circuit": c}
    try:
        topo = load_topology(str(LIB / (c + ".topology.json")))
        try:
            spec = load_sizing_spec(str(LIB / (c + ".sizing_spec.json")), topo, sa.metric_catalog())
            inputs = dc_inputs_from_spec(spec)
            marks = symmetry_marks(inputs)
            supplies = sa._supplies(spec, None)
            values = dict(inputs.element_values)
            inp_sup = dict(inputs.supplies_v)
        except SchemaRejectedError as exc:
            # spec 로더 거부(사실 기록) -- 연결만으로 잰다: 표시 없음, 선언값 없음(값 선언 칸은 미상), 레일 값은 spec 원문.
            row["spec_rejected"] = str(exc)[:300]
            raw = json.loads((LIB / (c + ".sizing_spec.json")).read_text(encoding="utf-8"))
            inp_sup = dict(raw["human"]["supplies_v"]["values"])
            supplies = inp_sup; marks = NO_MARKS; values = {}; inputs = None
        path = LIB / (c + ".structure.json")
        structure = load_structure_facts(path, topo.connectivity_fp, structure_rule_fp(), sa._net_names(topo))
        donors, counters = open_run()
        s1 = build_s1(topo, supplies, previous=GraphSnapshot.empty(sa.S0_WRITERS), structure=structure, marks=marks, donors=donors, counters=counters)
        classes = dict(s1.column("device", "element_class")); kinds = dict(s1.column("device", "kind"))
        rails = {n for n, r in s1.column("node", "is_rail") if r}
        sources = tuple((n, values.get(n)) for n in sorted(classes) if classes[n] == ELEMENT_SOURCE and kinds[n] == ck.CURRENT_SOURCE)
        base = ck.lift_s1(s1)
        sup = supplies_declaration(inp_sup, rails)
        base = ck.dc_rails(base, sup, donors=donors, counters=counters)
        base = s1_symmetry(base, sup, marks, donors=donors, counters=counters)
        base = ck.dc_current_basis(base, sources, donors=donors, counters=counters)
        basis = base.value("graph", "dc", "dc_current_basis")
        pins = dict(s1.column("device", "pins"))
        free = list(basis.free)
        rs = [n for n in free if classes[n] == ELEMENT_PASSIVE and kinds[n] == "resistor"]
        detail = {}
        rows = dict(basis.rows)
        mos = set(basis.mos)
        vmax, vmin = max(inp_sup.values()), min(inp_sup.values())
        for n in rs:
            nets = [net for _t, net in sorted(dict(pins[n]).items())]        # 양의 방향 = t0 -> t1 (dc_current_basis._ends)
            rail_v = {x: inp_sup.get(x) for x in nets if x in rails}
            # 레일 끝이 주는 방향: t0 쪽이 최고 레일이거나 t1 쪽이 최저 레일이면 양(+), 반대면 음(-), 중간 레일이면 미정(0)
            sign = None
            if nets[0] in rail_v:
                sign = 1 if rail_v[nets[0]] == vmax else (-1 if rail_v[nets[0]] == vmin else 0)
            elif nets[1] in rail_v:
                sign = 1 if rail_v[nets[1]] == vmin else (-1 if rail_v[nets[1]] == vmax else 0)
            # 그 전류를 읽는 MOS 행: 단독 항(직렬)이면 전도 방향이 저항 방향을 정한다(계수 부호)
            alone = sorted({(m, t.num / t.den) for m, ts in rows.items() if m in mos for t in ts if t.source == n and len(ts) == 1})
            mixed = sorted({m for m, ts in rows.items() if m in mos and len(ts) > 1 and any(t.source == n for t in ts)})
            others = sorted({m: [(t.source, t.num / t.den) for t in ts] for m, ts in rows.items() if m not in mos and any(t.source == n for t in ts) and m != n}.items())
            detail[n] = {"nets": nets, "n_rail_ends": sum(x in rails for x in nets), "value_declared": values.get(n) is not None,
                         "rail_sign_t0_t1": sign, "mos_series_rows": alone, "mos_mixed_rows": mixed, "other_element_rows": others}
        sym = sys.modules["gmid_engine.search.current_symmetry"].current_symmetry(base, ())
        zero = {k for _c, k in sym.zeros}; neg = {k for _c, k in sym.negated}
        tied = {k: rep[1] for rep, ms in sym.ties for _c, k in ms}
        for n in rs:
            detail[n].update(structural_zero=n in zero, negated=n in neg, tied_to=tied.get(n))
        both = [n for n, d in detail.items() if d["n_rail_ends"] == 0]
        # 쓰기 계획 도달 여부(사실 -- TB-1 변화표 분모). 입력 DC 선언 여부는 spec 로드된 회로만.
        try:
            targets = tuple(sorted(dict(inputs.node_targets))) if inputs is not None else ()
            declared_dc = inputs.input_dc_v is not None if inputs is not None else False
            planned = ck.dc_writer_plan(base, targets, declared_dc, donors=donors, counters=counters)
            coord = dict(planned.column("device", "dc_coord"))
            row["dependents"] = sorted((n, c.relation, c.partner) for n, c in coord.items() if c.role == "dependent")
            row["tie_breaks"] = [(t.decision, list(t.candidates)) for t in planned.value("graph", "dc", "dc_tie_breaks")]
        except Exception as exc:
            row["writer_plan_stop"] = str(exc)[:400]
        row.update(n_free=len(free), theta_R=rs, n_theta_R=len(rs), both_nonrail=both, n_both_nonrail=len(both), detail=detail,
                   dc_resistors=list(basis.resistors), pruned=list(basis.pruned))
        tot["circuits"] += 1; tot["theta_R"] += len(rs); tot["both_nonrail"] += len(both); tot["circuits_nonzero"] += bool(both)
    except Exception:
        row["error"] = traceback.format_exc()[-1500:]
        tot["errors"] += 1
    app(row)
    print(c, row.get("n_theta_R"), row.get("n_both_nonrail"), "ERR" if "error" in row else "", flush=True)
app({"total": tot})
print(tot)
