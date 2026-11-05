"""§1 코드 재대조(LUT 없음, u7_ngcc.library_case 합성 값·구조만): 13 library 회로의 뷰·블록마다 U_b·전하 넷·출력 무스탬프·NaN·둘째 C 조립 조건을 잰다.
값은 합성이라 판정 수치가 아니다(13회로 변화표 아님 -- 보류). 결과 jsonl 회로마다 append."""
import json
import math
import pathlib
import sys

skill = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(skill))
sys.path.insert(0, str(skill / "gmid_engine" / "tests"))
out = pathlib.Path(sys.argv[2])
out.write_text("", encoding="utf-8")

from gmid_engine.metrics import block_local_gain
from gmid_engine.metrics import block_model as BM
from gmid_engine.metrics.ss_nodal import nodal_of
from gmid_engine.tests.metrics import u7_ngcc as N

total = dict(circuits=0, blocks=0, charge_blocks=0, full_charge=0, full_floating=0, full_singular=0, gain_zero_or_none=0, nan_zout=0, output_unstamped=0, dead_nets=0)
for name in N.LIBRARY_CIRCUITS if hasattr(N, "LIBRARY_CIRCUITS") else sorted(p.name.removesuffix(".topology.json") for p in (skill / "assets" / "library").glob("*.topology.json") if not p.name.startswith("_")):
    item = {"circuit": name}
    try:
        ss, structs, decls = N.library_case(name)
        nod = nodal_of(ss)
        item.update(full_charge=[ss.nodes[i] for i in nod.factor[5]], full_floating=[ss.nodes[i] for i in nod.factor[4]], full_singular=nod.factor[1] is None)
        total["circuits"] += 1
        total["full_charge"] += bool(item["full_charge"])
        total["full_floating"] += bool(item["full_floating"])
        total["full_singular"] += bool(item["full_singular"])
        rows = []
        for v in structs:
            every = {n for b in v.blocks for n in b.nodes}
            excl = tuple(sorted({m for f in v.ff for m in f.members}))
            for b in v.blocks:
                total["blocks"] += 1
                fixed, unknown, charge, mos_l, res_l, _c = BM._structure(ss, b, BM._unit_drive(b.inputs), every - set(b.nodes), excl, (), v.ac_ground)
                got = block_local_gain(ss, b, None, others=every - set(b.nodes), exclude=excl, ground=v.ac_ground)
                total["charge_blocks"] += bool(charge)
                idx = {n: i for i, n in enumerate(ss.nodes)}
                mos_by = {m.label: m for m in ss.circuit.mos}
                res_by = {r.label: r for r in ss.circuit.resistors}
                conduct = {t for l in mos_l for t in (mos_by[l].d, mos_by[l].s)} | {t for l in res_l for t in (res_by[l].a, res_by[l].b)}
                unst = [o for o in b.outputs if o in idx and idx[o] not in fixed and idx[o] not in conduct and idx[o] not in charge]
                total["output_unstamped"] += bool(unst)
                z = got.zout_ohm
                total["nan_zout"] += bool(z is not None and math.isnan(z))
                total["gain_zero_or_none"] += (got.gain is None or got.gain == 0) and not any(u.code == "composite_paths" for u in got.undefined)
                rows.append(dict(view=v.id, key=b.key, members=len(got.members), unknown=len(unknown), charge=[ss.nodes[i] for i in charge], gain=got.gain, zout=z, undefined=[u.code for u in got.undefined], unstamped_outputs=unst))
        item["rows"] = rows
    except Exception as exc:
        item["error"] = repr(exc)[:400]
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False, default=repr) + "\n")
with out.open("a", encoding="utf-8") as f:
    f.write(json.dumps({"total": total}, ensure_ascii=False) + "\n")
print(total)
