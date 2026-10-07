# -*- coding: utf-8 -*-
"""세션16 논의 검증용 격리 스크립트 (프로덕션 코드 변경 없음).

질문: find_min_crossover_layout()이 이미 계산한 segments(transistor_sequence 포함)를
버리고, stack_id만 재배정해서 build_stick_diagram()이 나중에 다시 계산하게 하면
(C-1 설계 그대로) 실제로 무슨 일이 일어나는가?

- M6 그룹(current_reuse_telescopic_ota, 8소자, crossover=1)을 실제 사례로 사용.
- find_min_crossover_layout()의 segments를 먼저 확인.
- 그 segments대로 stack_id를 M6_seg0/M6_seg1로 재배정.
- build_stick_diagram()을 그 재배정된 리스트로 호출해서(=C-1이 다음 라운드에 할 일을
  그대로 재현) 각 세그먼트가 독립적으로 다시 계산됐을 때 어떻게 되는지 확인.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "..", "skills", "analog-gmid-design", "assets"))

from stick_diagram import (  # noqa: E402
    load_topology, geometry_colocation_union, find_min_crossover_layout,
    build_stick_diagram, check_walk_sequence, _dc_replace, audit_row_split,
)

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..", "skills", "analog-gmid-design", "assets", "library")

trs, meta = load_topology(os.path.join(LIB, "current_reuse_telescopic_ota.topology.json"))
pairs_meta = meta["symmetry"]["matching_pairs"]
forced = [tuple(p["names"]) for p in pairs_meta if p.get("current_forced")]
groups = geometry_colocation_union(trs, forced)
m6_names = groups["M6"]
by_name = {t.name: t for t in trs}
m6_trs = [_dc_replace(by_name[n], stack_id="M6") for n in m6_names]
inside_pairs = [tuple(p["names"]) for p in pairs_meta if set(p["names"]) <= set(m6_names)]

print("=== 1) find_min_crossover_layout() 원본 결과 ===")
result = find_min_crossover_layout(m6_trs, inside_pairs)
print(f"crossover_count={result['crossover_count']}  "
      f"node_pairing_fallback_used={result['node_pairing_fallback_used']}")
for i, seg in enumerate(result["segments"]):
    names_in_seg = sorted(set(seg["transistor_sequence"]))
    print(f"  segment{i}: devices={names_in_seg}")
    print(f"    transistor_sequence={seg['transistor_sequence']}")
    print(f"    node_sequence      ={seg['node_sequence']}")

print()
print("=== 2) inside_pairs 중 세그먼트 경계를 가로지르는 쌍이 있는가? ===")
seg_of = {}
for i, seg in enumerate(result["segments"]):
    for n in set(seg["transistor_sequence"]):
        seg_of[n] = i
for a, b in inside_pairs:
    same = seg_of.get(a) == seg_of.get(b)
    print(f"  ({a},{b}): seg[{a}]={seg_of.get(a)}  seg[{b}]={seg_of.get(b)}  "
          f"{'같은 세그먼트' if same else '★세그먼트 경계를 가로지름'}")

print()
print("=== 3) C-1 설계 재현: stack_id를 M6_seg{i}로 재배정 후 build_stick_diagram() 재실행 ===")
reassigned = []
for i, seg in enumerate(result["segments"]):
    seg_names = set(seg["transistor_sequence"])
    for n in seg_names:
        reassigned.append(_dc_replace(by_name[n], stack_id=f"M6_seg{i}"))

rebuilt = build_stick_diagram(reassigned, matching_pairs=inside_pairs)
for stack_id, r in sorted(rebuilt.items(), key=lambda kv: str(kv[0])):
    print(f"  stack={stack_id}  status={r.status}  method={r.method}")
    if r.status == "ok":
        print(f"    transistor_sequence={r.transistor_sequence}")
        wv = check_walk_sequence(r.transistor_sequence, [t for t in reassigned if t.stack_id == stack_id])
        print(f"    check_walk_sequence.ok={wv.ok}  (독립 재검증)")
    else:
        print(f"    odd_nodes={r.odd_nodes}  connected={r.connected}")

print()
print("=== 4) 재계산된 시퀀스가 원본 find_min_crossover_layout() 시퀀스와 같은가? ===")
for i, seg in enumerate(result["segments"]):
    stack_id = f"M6_seg{i}"
    orig = seg["transistor_sequence"]
    new = rebuilt[stack_id].transistor_sequence if rebuilt[stack_id].status == "ok" else None
    same = (orig == new)
    print(f"  {stack_id}: 원본={orig}")
    print(f"           재계산={new}")
    print(f"           동일={'YES' if same else 'NO(다른 유효 오일러 경로)'}")

print()
print("=== 5) 사용자 질문 검증: 그룹분할 결과가 3c(common-centroid) 게이트를 통과하는가? ===")
print("  M1a/M1b(offset), M2a/M2b(topology.json 선언값 그대로)는 select_layout_tool()상")
print("  common-centroid가 필수 게이트 -- 이게 '한 행에 같이' 요구가 아니라 '여러 행에 걸쳐")
print("  분배돼도 되지만 전체 무게중심(x,y)이 맞아야' 요구라는 걸 실제로 계산해서 확인.")
pair_sensitivity = {tuple(p["names"]): p["matching_sensitivity"] for p in pairs_meta
                    if set(p["names"]) <= set(m6_names)}
print(f"  pair_sensitivity={pair_sensitivity}")

rows = {}
for t in reassigned:
    rows.setdefault(t.stack_id, []).append(t)

audit = audit_row_split(rows, matching_pairs=inside_pairs, pair_sensitivity=pair_sensitivity)
print(f"  전체 audit.ok={audit.ok}")
for check in audit.checks:
    if check.name.startswith("3") or check.name.startswith("1."):
        print(f"    [{'PASS' if check.ok else 'FAIL'}] {check.name}: {check.detail}")
