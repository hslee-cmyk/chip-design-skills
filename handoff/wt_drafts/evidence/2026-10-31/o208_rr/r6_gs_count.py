# R6 실측 -- library(·heldout 있으면) topology.json netlist 연결만으로 gate 넷 = source 넷인 MOS 수(g = s 소자, VGS = 0 KVL 고정).
# 태그(device_roles 등) 미사용 -- 연결 필드 kind·drain·gate·source·bulk 만 읽는다. 결과 = r6_gs_count.txt(덮어씀, 결정적).
import json, glob, pathlib
HERE = pathlib.Path(__file__).parent
A = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets")
out = ["# R6 g = s MOS 수 (topology.json netlist 연결 필드만)"]
tot_c = hit_c = 0
for grp in ("library", "heldout"):
    files = sorted(f for f in glob.glob(str(A / grp / "*.topology.json")) if not f.endswith("_TEMPLATE.topology.json"))
    out.append(f"## {grp}: 파일 {len(files)}개" + ("" if files else f" (폴더 {A / grp} 없음 또는 비어 있음)"))
    for f in files:
        d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        mos = [e for e in d.get("netlist", []) if e.get("kind") in ("nmos", "pmos")]
        gs = [e for e in mos if e.get("gate") == e.get("source")]
        gd = [e for e in mos if e.get("gate") == e.get("drain")]
        tot_c += 1; hit_c += bool(gs)
        out.append(f"{pathlib.Path(f).name} | MOS {len(mos)} | g = s {len(gs)} {[(e['name'], e['kind'], e['gate']) for e in gs]} | (참고) g = d diode {len(gd)}")
out.append(f"g = s 소자가 있는 회로 {hit_c}/{tot_c}")
(HERE / "r6_gs_count.txt").write_bytes(("\n".join(out) + "\n").encode("utf-8"))
print("\n".join(out))
