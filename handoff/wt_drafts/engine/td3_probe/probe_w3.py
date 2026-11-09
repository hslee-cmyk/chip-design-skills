"""읽기 전용 probe: 출력 넷 W3 목표 유무에 따른 쓰기 계획 비교 (저장소 파일 수정 없음)."""
import sys, dataclasses, traceback
sys.path.insert(0, '.')
from gmid_engine.authoring import load_topology, load_sizing_spec
from gmid_engine.metrics import metric_catalog
from gmid_engine.graph import build_s1, s1_symmetry, supplies_declaration
from gmid_engine.sizing import dc_inputs_from_spec
from gmid_engine.sizing.s2_lift import lift_s1
from gmid_engine.sizing.w0_rails import dc_rails
from gmid_engine.sizing.symmetry_marks import symmetry_marks
from gmid_engine.sizing.current_basis import dc_current_basis
from gmid_engine.sizing.writer_plan import dc_writer_plan
from gmid_engine.sizing.scc_order import dc_scc_order
from gmid_engine.graph import ELEMENT_SOURCE
OUT = {'folded_cascode':'out','ngcc_3stage_ff':'Vout','nmcnr_amplifier':'Vout','sf_pushpull_output_opamp':'vout','two_stage_ota':'OUT','two_stage_ota_sf':'vout'}
res = open(sys.argv[1], 'w', encoding='utf-8')
for c, out in OUT.items():
    try:
        topo = load_topology(f'assets/library/{c}.topology.json')
        spec = load_sizing_spec(f'assets/library/{c}.sizing_spec.json', topo, metric_catalog())
        inp = dc_inputs_from_spec(spec)
        s1 = build_s1(topo, dict(inp.supplies_v))
        rails = frozenset(n for n, r in s1.column('node','is_rail') if r)
        sup = supplies_declaration(dict(inp.supplies_v), rails)
        classes = dict(s1.column('device','element_class')); kinds = dict(s1.column('device','kind'))
        vals = dict(inp.element_values)
        sources = tuple((n, vals.get(n)) for n in sorted(classes) if classes[n] == ELEMENT_SOURCE and kinds[n] == 'current_source')
        for label, targets in (('none', ()), ('W3', ((out, 0.9),))):
            inp2 = dataclasses.replace(inp, node_targets=targets)
            b = lift_s1(s1); b = dc_rails(b, sup); b = s1_symmetry(b, sup, symmetry_marks(inp2)); b = dc_current_basis(b, sources)
            b = dc_writer_plan(b, tuple(sorted(n for n, _ in targets)), inp2.input_dc_v is not None)
            b = dc_scc_order(b)
            w = dict(b.column('node','dc_writer')); coords = dict(b.column('device','dc_coord'))
            dep = sorted(n for n, cd in coords.items() if cd is not None and getattr(cd,'role',None) != 'writer' and str(cd).find('writer')<0)
            w4 = sorted(n for n, x in w.items() if 'W4' in str(x))
            res.write(f'{c} [{label}] out writer={w.get(out)}\n   W4 nodes={w4}\n   dependent={[(n, str(coords[n])) for n in dep]}\n')
    except Exception as e:
        res.write(f'{c} ERROR {type(e).__name__}: {e}\n{traceback.format_exc()[-1500:]}\n')
    res.flush()
