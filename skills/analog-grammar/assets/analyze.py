#!/usr/bin/env python3
"""
analyze.py — Stage 1~6 파이프라인 러너

    python3 analyze.py netlist.json
    python3 analyze.py netlist.json --inputs Vip,Vim --feedback Vcmfb
    python3 analyze.py netlist.json --json out.json

입력 netlist 형식 (schematic_extract.py 출력과 동일):
    {"devices":[{"name":"M1a","type":"PMOS","D":"n1","G":"Vip","S":"Vx"}, ...]}

출력 원칙
---------
확정 사실(구조에서 결정론적으로 나온 것)과 가정/추론을 항상 분리해 표시한다.
가정 절(ASSUMPTIONS)이 비어 있지 않으면 그 아래 결과는 전부 그 가정에
조건부다. 사용자가 --inputs 등으로 선언하면 가정이 사실로 승격된다.
"""
import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from netclass import classify_nets, assign_roles, stack_edges
from idioms import match_all, resolve_overlaps, contract
from sfg import build_sfg, structural_signature, hypothesise


def csv(s): return [x for x in (s or '').split(',') if x]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('netlist')
    ap.add_argument('--inputs', default='');   ap.add_argument('--outputs', default='')
    ap.add_argument('--bias', default='');     ap.add_argument('--feedback', default='')
    ap.add_argument('--clocks', default='');   ap.add_argument('--json')
    a = ap.parse_args()

    doc = json.load(open(a.netlist))
    devs = doc['devices'] if isinstance(doc, dict) else doc
    devs = [d for d in devs if d.get('type') in ('PMOS', 'NMOS')]
    if not devs: sys.exit("MOS 소자가 없습니다.")

    # ── Stage 1 ────────────────────────────────────────────────────────
    cls, imp, assume = classify_nets(devs, csv(a.inputs), csv(a.outputs),
                                     csv(a.bias), csv(a.feedback), csv(a.clocks))
    print("=" * 66); print("ASSUMPTIONS  (아래 모든 결과는 이 가정에 조건부)"); print("=" * 66)
    if assume:
        for s in assume: print("  " + s)
        if not csv(a.inputs):
            print("\n  ! 잘린 도면에서 INPUT 과 BIAS 는 구조적으로 구별되지 않습니다.")
            print("    --inputs / --bias 로 선언하면 이 가정이 사실로 승격됩니다.")
    else:
        print("  (없음 — 전부 사용자 선언 또는 구조 결정)")

    print("\n" + "=" * 66); print("STAGE 1 — net classification"); print("=" * 66)
    print(f"  {'net':<10}{'class':<12}{'impedance':<10}")
    print("  " + "-" * 32)
    for n in sorted(cls, key=lambda n: (cls[n], n)):
        print(f"  {n:<10}{cls[n]:<12}{imp.get(n,''):<10}")

    # ── Stage 2 ────────────────────────────────────────────────────────
    role = assign_roles(devs, cls, imp)
    print("\n" + "=" * 66); print("STAGE 2 — device roles  (net class 주어지면 결정론적)"); print("=" * 66)
    print(f"  {'dev':<7}{'type':<7}{'role':<26}{'D':<9}{'G':<9}{'S':<9}")
    print("  " + "-" * 66)
    for d in devs:
        print(f"  {d['name']:<7}{d['type']:<7}{role[d['name']]:<26}"
              f"{d['D']:<9}{d['G']:<9}{d['S']:<9}")
    un = [n for n, r in role.items() if r == 'UNRESOLVED']
    if un: print(f"\n  WARN  role 미해결: {un}  <= net 분류를 먼저 확인하세요")

    st = stack_edges(devs)
    if st:
        print("\n  직렬 적층 (lower -> upper via node):")
        for lo, up, nd in st: print(f"    {lo} -> {up}  via {nd}")

    # ── Stage 3 / 4 ────────────────────────────────────────────────────
    matches = match_all(devs, cls, imp, role)
    kept, used = resolve_overlaps(matches)
    sup, leftover = contract(devs, kept)
    print("\n" + "=" * 66); print("STAGE 3 — L1 idiom matching"); print("=" * 66)
    for m in sorted(kept, key=lambda m: (-m.priority, m.kind)):
        p = ' '.join(f"{k}={v}" for k, v in m.ports.items())
        print(f"  [{m.priority}] {m.kind:<24} {'+'.join(m.devices):<18} {p}")
        if m.note: print(f"       {m.note}")
    dropped = [m for m in matches if m not in kept]
    if dropped:
        print(f"\n  겹침으로 탈락한 매칭 {len(dropped)}개: "
              f"{', '.join(sorted({str(m) for m in dropped}))[:200]}")

    print("\n" + "=" * 66); print("STAGE 4 — hierarchy contraction"); print("=" * 66)
    for s in sup: print(f"  {s['id']:<4}{s['kind']:<24}{'+'.join(s['members'])}")
    if leftover: print(f"  미축약 소자: {leftover}")
    cov = 1 - len(leftover) / len(devs)
    print(f"  coverage = {cov:.2f}")

    # ── Stage 5 / 6 ────────────────────────────────────────────────────
    E = build_sfg(devs, cls, imp, role)
    sig = structural_signature(devs, cls, imp, role, kept, sup, E)
    print("\n" + "=" * 66); print("STAGE 5 — signal flow graph"); print("=" * 66)
    print(f"  gain nodes    : {sig['gain_nodes']}")
    print(f"  gain stages   : {sig['gain_stages']}")
    print(f"  output Z      : {sig['output_impedance']}")
    if sig['forward_paths']:
        print("  forward paths :")
        for p, k in sig['forward_paths']: print(f"      {p}   ({k})")
    if sig['loops']:
        print("  loops         :")
        for p, k in sig['loops']: print(f"      {p}   ({k})")
    else:
        print("  loops         : (이 도면 범위에서 검출 없음)")

    H, evid = hypothesise(sig)
    print("\n" + "=" * 66); print("STAGE 6 — functional hypothesis"); print("=" * 66)
    print("  [확정 — 구조에서 결정론적으로 도출]")
    for h in H: print(f"    - {h}")
    print("  [근거]")
    for e in evid: print(f"    - {e}")
    print("\n  [LLM 에게 남기는 것]")
    print("    - 위 시그니처에 해당하는 문헌상의 정확한 topology 명칭")
    print("    - 라이브러리에 없는 신규 idiom 의 명명 및 등록 제안")
    print("    - 겹쳐 탈락한 매칭 중 '의도된 해석'이 무엇인지 판단")
    print("    - 미축약 소자가 왜 남았는지 설명")

    if a.json:
        json.dump(dict(assumptions=assume, netclass=cls, impedance=imp,
                       roles=role, idioms=[dict(kind=m.kind, devices=list(m.devices),
                                                ports=m.ports, note=m.note)
                                           for m in kept],
                       supernodes=sup, signature=sig, hypothesis=H),
                  open(a.json, 'w'), indent=2, ensure_ascii=False)
        print(f"\n-> {a.json}")


if __name__ == '__main__':
    main()
