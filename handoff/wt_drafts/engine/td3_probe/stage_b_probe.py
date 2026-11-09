"""읽기 전용: 6회로 단계 A -> B(진단)를 scratchpad 출력으로 돌려 헤드룸 창 보고를 모은다(저장소 파일 수정 없음)."""
import json, os, sys, traceback
from pathlib import Path
sys.path.insert(0, '.')
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings

SKILL = Path('.').resolve(); LIB = SKILL / 'assets' / 'library'; OUTD = Path(sys.argv[1]); RES = Path(sys.argv[2])
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")); CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
loc = resolve_lut_location(str(SKILL / 'assets' / 'lut_v2_location.json'), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding='utf-8'))
kinds = dict(DEVICE_KINDS); mins = {}
for e in man['slices']:
    mins[kinds[e['device']]] = min(e['w_um'] * 1e-6, mins.get(kinds[e['device']], float('inf')))
pdk = read_pdk_decl(str(SKILL / 'assets' / 'sky130_pdk_decl.json'), BoundedLRU(16)); q = dict(pdk.quantities)
spec = LutSpec(float(man.get('manufacturing_grid_m', 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
               noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
settings = SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "td3 probe"),), (1e-13, 1e-10))
with RES.open('w', encoding='utf-8') as f:
    for c in sys.argv[3:]:
        try:
            a = run_stage_a(LIB / (c + '.topology.json'), LIB / (c + '.sizing_spec.json'), lut, output_dir=OUTD / c)
            memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
            b = run_stage_b(a, memo, pdk, output_dir=OUTD / c, diagnostic=True, settings=settings)
            f.write(f'{c} A={a.status} B={b.status} reports={b.report_paths}\n')
        except Exception as e:
            f.write(f'{c} ERROR {type(e).__name__}: {e}\n{traceback.format_exc()[-800:]}\n')
        f.flush()
