# -*- coding: utf-8 -*-
"""find_structural_symmetry_candidates()(2026-08 세션6 신설, stick_diagram.py)를
current_reuse_telescopic_ota에 실제로 돌려보는 검증 스크립트 -- mirror(좌우)/dual(상하)
둘 다, 오늘 손으로 재발견한 대응관계(M8<->M17, M13<->M22, M11a-chain<->M20a-chain 등)를
자동으로 재현하는지 확인한다."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")

from stick_diagram import load_topology, find_structural_symmetry_candidates

JSON_PATH = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json"

transistors, meta = load_topology(JSON_PATH)
by_name = {t.name: t for t in transistors}

print("=" * 78)
print("MIRROR(좌우, Vom블록<->Vop블록) transform")
print("=" * 78)
mirror_seed = {
    "vdd": "vdd", "gnd": "gnd",
    "Vbias1": "Vbias1", "Vbias2": "Vbias2", "Vbias3": "Vbias3", "Vbias4": "Vbias4",
    "Vcmfb": "Vcmfb",
    "Vip": "Vim", "Vim": "Vip",
    "Vop": "Vom", "Vom": "Vop",
}
mv = find_structural_symmetry_candidates(transistors, mirror_seed, transform="mirror")
device_pairs = sorted({frozenset((a, b)) for a, b in mv.device_map.items() if a != b},
                       key=lambda fs: sorted(fs))
print(f"device_map 쌍 개수: {len(device_pairs)}")
for fs in device_pairs:
    a, b = sorted(fs)
    print(f"  {a} <-> {b}")
self_paired = sorted(a for a, b in mv.device_map.items() if a == b)
print(f"자기-대칭(self-paired): {self_paired}")
print(f"conflicts: {mv.conflicts}")
print(f"unresolved({len(mv.unresolved)}): {mv.unresolved}")
print(f"low_confidence_pairs: {mv.low_confidence_pairs}")

print()
print("--- 오늘 손으로 확인한 대응관계와 대조 ---")
expected_mirror_pairs = [
    ("M8", "M17"), ("M13", "M22"), ("M9a", "M18a"), ("M9b", "M18b"),
    ("M10", "M19"), ("M11a", "M20a"), ("M11b", "M20b"), ("M12", "M21"),
    ("M14a", "M23a"), ("M14b", "M24b"), ("M15", "M25"), ("M16", "M26"),
    ("M1a", "M1b"), ("M2a", "M2b"), ("M3a", "M3b"), ("M4a", "M4b"),
]
found_pairs = {frozenset(p) for p in mv.device_map.items() if p[0] != p[1]}
for a, b in expected_mirror_pairs:
    ok = frozenset((a, b)) in found_pairs
    print(f"  {'OK ' if ok else 'MISS'}  {a} <-> {b}")

print()
print("=" * 78)
print("DUAL(상하/극성, PMOS망<->NMOS망) transform")
print("=" * 78)
dual_seed = {
    "vdd": "gnd", "gnd": "vdd",
    "Vip": "Vip", "Vim": "Vim",
}
dv = find_structural_symmetry_candidates(transistors, dual_seed, transform="dual")
device_pairs_d = sorted({frozenset((a, b)) for a, b in dv.device_map.items() if a != b},
                         key=lambda fs: sorted(fs))
print(f"device_map 쌍 개수: {len(device_pairs_d)}")
for fs in device_pairs_d:
    a, b = sorted(fs)
    print(f"  {a} <-> {b}")
print(f"conflicts: {dv.conflicts}")
print(f"unresolved({len(dv.unresolved)}): {dv.unresolved}")
print(f"low_confidence_pairs: {dv.low_confidence_pairs}")
