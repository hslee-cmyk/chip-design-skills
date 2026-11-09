"""검증 9: Q-KV1 (다) 6고리 선택 재현 -- current_reuse 4고리(버퍼 2고리는 J12-f ratified 먼저라 생략).
B 판정 = S1v 셀 kind ∈ {diode_load, load, mirror, tail_source}(pass·cs·input = 신호), diode = gate == drain(topology),
B 안 순위 = diode → (대칭 궤도 대표: 여기서는 동률) → 이름. 입력: topology.json, stage_a.json(읽기만)."""
import json, pathlib
TOP = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json")
SA = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/classab_battery/_stage_a/current_reuse_telescopic_ota.stage_a.json")
net = {d["name"]: d for d in json.loads(TOP.read_text(encoding="utf-8"))["netlist"]}
cells = {c["dev"]: c for c in json.loads(SA.read_text(encoding="utf-8"))["tables"]["views"][0]["cells"]}
loops = [("M11a", "M11b", "M15", "M9a"), ("M14a", "M14b", "M16", "M9b"), ("M18a", "M20a", "M20b", "M25"), ("M18b", "M23a", "M24b", "M26")]
B_KINDS = {"diode_load", "load", "mirror", "tail_source"}
out = []
for lp in loops:
    rows = []
    for m in lp:
        k = cells.get(m, {}).get("kind")
        diode = net[m]["gate"] == net[m]["drain"]
        rows.append((m, k, "B" if k in B_KINDS else "S/F", diode))
    B = [r for r in rows if r[2] == "B"]
    pick = sorted(B, key=lambda r: (not r[3], r[0]))[0][0] if B else None
    out.append(f"{lp}: {rows} -> 종속 = {pick}")
pathlib.Path(__file__).with_suffix(".txt").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
