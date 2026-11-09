"""C4-Q6 G-1 (i) OP-5 → LA-1 대 (ii′) LA-1 → OP-5 -- 병합 DAG 두 개 비교(검증 55 A-4 실측).

판정용 간선 = merge_order_cycle.py 의 MANUAL(원문 조각 단언 통과분) + 아래 COMPLETION(LA-1 '완료' 경로와 OP-5 뒤 card,
역시 계획 65377396 원문 조각 단언). 시간 단위가 계획에 없으므로 '병합 사슬 길이(card 수)'와 집합 크기로 잰다.
지표:
 (a) LA-1 병합까지·LA-1 완료(CL-1 -- P:1306 '완료는 card CL-1 뒤에만')까지 가장 긴 선행 사슬
 (b) OP-5 병합이 기다리는 card(OP-5의 병합 조상)
 (c) SPICE 다리 보류 card: 'EO-1 뒤 OP-5 전 기간'(P:2165)에 병합이 강제되는 다리 card = EO-1 후손 ∩ OP-5 조상 ∩ 다리 card
     + ASAP 일정(가장 긴 사슬 깊이)에서 그 기간에 놓이는 다리 card
 (d) 임계 경로 길이(card 수): LA-1 병합, CL-1(LA-1 완료 관문), OP-5 병합, offset-strategy OS-V·offset-trim TR-7(OP-5 선행 card)
출력: merge_order_compare.txt
"""
import importlib.util, sys
from collections import defaultdict

HERE = __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0]
spec = importlib.util.spec_from_file_location("moc", HERE + "/merge_order_cycle.py")
moc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(moc)  # 원문 조각 단언 실행(실패 시 종료), 파일 쓰기는 __main__ 아님이라 안 함
OUT = __file__.replace(".py", ".txt")
log = []
sys.stdout.reconfigure(encoding="utf-8")


def out(*a):
    log.append(" ".join(str(x) for x in a))


COMPLETION = [
    ("CL-1", "LA-1#done", "gb:1306", "**완료는 card CL-1(oracle 닫기", "LA-1 완료 관문"),
    ("LA-1", "LA-1#done", "gb:1306", "**완료는 card CL-1(oracle 닫기", "완료는 병합 뒤"),
    ("OP-5", "CL-1", "gb:1312", "oracle OP-3·OP-5·OP-10·OP-11, 엔진 EO-1·PW-1a·VB-1", "CL-1 선행"),
    ("OP-10", "CL-1", "gb:1312", "oracle OP-3·OP-5·OP-10·OP-11", "CL-1 선행"),
    ("OP-11", "CL-1", "gb:1312", "oracle OP-3·OP-5·OP-10·OP-11", "CL-1 선행"),
    ("EO-1", "CL-1", "gb:1312", "엔진 EO-1·PW-1a·VB-1", "CL-1 선행"),
    ("PW-1a", "CL-1", "gb:1312", "엔진 EO-1·PW-1a·VB-1", "CL-1 선행"),
    ("VB-1", "CL-1", "gb:1312", "엔진 EO-1·PW-1a·VB-1", "CL-1 선행"),
    ("DE-1", "CL-1", "gb:1312", "metric 코드를 바꾸는 DE-1·NL-1·UB-1·IT-2", "CL-1 선행"),
    ("OP-5", "VB-1", "gb:2139", "oracle OP-5·OP-10 승인·병합", "VB-1 착수 조건"),
    ("OP-10", "VB-1", "gb:2139", "oracle OP-5·OP-10 승인·병합", "VB-1 착수 조건"),
    ("SF-1", "VB-1", "gb:2139", "선행 = card SF-1", "VB-1 선행"),
    ("IT-1+IT-2", "VB-1", "gb:1311", "IT-1 + IT-2 통합 병합(IT-2d `offset_sys_mv` 영역 칸", "VB-1 선행"),
    ("OP-3", "OP-11", "op:515", "OP-3(compare 코어 이동 뒤", "선행"),
    ("OP-11", "PW-1a", "gb:1309", "oracle-portability OP-11", "선행"),
    ("OP-4", "OP-10", "op:514", "OP-4(과도 코어·어댑터), OP-5(정의 일반형 입력 선언)", "선행"),
    ("OP-5", "OP-10", "op:514", "OP-4(과도 코어·어댑터), OP-5(정의 일반형 입력 선언)", "선행"),
    ("EO-1", "OP-10", "op:514", "**EO-1**(v0.6.10, O-50 O3", "선행"),
    ("LA-1", "DE-1", "gb:1347", "-- LA-1 → DE-1, 생산 LA-1(O-183)", "표 #2"),
    ("WB-1", "DE-1", "gb:1300", "순서 WB-1 → DE-1 고정", "선행"),
    ("SF-1", "DE-1", "gb:1300", "순서 SF-1 → DE-1", "선행(J4)"),
    ("EO-1", "DE-1", "gb:1300", "병합 선행 EO-1(v6.33 기본안", "병합 선행"),
    ("OP-5", "OS-V", "os:577", "오라클 쪽 선행 = oracle-portability OP-3·gain-budget EO-1·oracle-portability OP-5", "OS-V 선행"),
    ("LA-1", "OS-2", "gb:1347", "-- LA-1 → offset-strategy OS-2, 생산 LA-1(O-183)", "표 #8"),
    ("OS-2", "OS-V", "os:577", "OS-V card, OS-2 뒤", "OS-V 선행"),
]
P = moc.P
P["offset-strategy"] = moc.get("offset-strategy")
ABBR = dict(moc.ABBR, os="offset-strategy")
for a, b, tag, frag, why in COMPLETION:
    ab, ln = tag.split(":")
    assert frag in P[ABBR[ab]][int(ln) - 1], (tag, frag)

# 다리 card(동작 변경 -- SPICE 다리 선행 EO-1)
BRIDGE = [
    ("IT-1+IT-2", "gb:2165", "IT-1·IT-2, DE-1, FX-1, NL-1, LI-1, LA-1, CL-1"),
    ("DE-1", "gb:2165", "IT-1·IT-2, DE-1, FX-1, NL-1, LI-1, LA-1, CL-1"),
    ("NL-1", "gb:2165", "IT-1·IT-2, DE-1, FX-1, NL-1, LI-1, LA-1, CL-1"),
    ("LA-1", "gb:2165", "IT-1·IT-2, DE-1, FX-1, NL-1, LI-1, LA-1, CL-1"),
    ("SF-1", "gb:1299", "SPICE 다리 선행 EO-1(범위 9"),
    ("TB-1", "gb:1293", "EO-1(SPICE 다리)"),
    ("WB-1", "gb:1296", "SPICE 다리 선행 EO-1"),
    ("HC-S", "hc:515", "완료 판정 선행이기도 함 -- SPICE 다리"),
    ("HC-1", "hc:516", "완료 판정 선행 -- SPICE 다리"),
    ("GC-8", "gc:644", "**완료 판정 선행**: gain-budget card EO-1(SPICE 다리"),
]
for n, tag, frag in BRIDGE:
    ab, ln = tag.split(":")
    assert frag in P[ABBR[ab]][int(ln) - 1], (tag, frag)
BR = {n for n, *_ in BRIDGE}


def build(extra):
    E = defaultdict(set)
    for a, b, *_ in moc.MANUAL + COMPLETION:
        E[a].add(b)
    a, b = extra
    E[a].add(b)
    return E


def depth(E):
    nodes = set(E) | {b for v in E.values() for b in v}
    rev = defaultdict(set)
    for a, bs in E.items():
        for b in bs:
            rev[b].add(a)
    memo, path = {}, {}
    sys.setrecursionlimit(10000)
    def d(n):
        if n in memo:
            return memo[n]
        best, bp = 1, None
        for p in sorted(rev[n]):
            v = d(p) + 1
            if v > best:
                best, bp = v, p
        memo[n], path[n] = best, bp
        return best
    for n in sorted(nodes):
        d(n)
    def chain(n):
        c = [n]
        while path.get(c[-1]):
            c.append(path[c[-1]])
        return " → ".join(reversed(c))
    return memo, chain, rev


def anc(rev, n):
    seen, st = set(), [n]
    while st:
        x = st.pop()
        for p in rev[x]:
            if p not in seen:
                seen.add(p); st.append(p)
    return seen


def desc(E, n):
    seen, st = set(), [n]
    while st:
        x = st.pop()
        for c in E.get(x, ()):
            if c not in seen:
                seen.add(c); st.append(c)
    return seen


res = {}
for name, extra in (("(i) OP-5 → LA-1", ("OP-5", "LA-1")), ("(ii′) LA-1 → OP-5", ("LA-1", "OP-5"))):
    E = build(extra)
    D, chain, rev = depth(E)
    aOP5 = anc(rev, "OP-5")
    forced = sorted(desc(E, "EO-1") & aOP5 & BR)
    asap = sorted(n for n in BR if D["EO-1"] < D[n] < D["OP-5"])
    res[name] = dict(D=D)
    out("##", name)
    out("(a) LA-1 병합 사슬", D["LA-1"], ":", chain("LA-1"))
    out("(a) LA-1 완료(CL-1 뒤) 사슬", D["LA-1#done"], ":", chain("LA-1#done"))
    out("(b) OP-5가 기다리는 card", len(aOP5), ":", ", ".join(sorted(aOP5)))
    out("(c) EO-1 뒤 OP-5 전 기간에 병합이 강제되는 다리 card", len(forced), ":", ", ".join(forced) or "없음")
    out("(c) ASAP 깊이로 그 기간에 놓이는 다리 card", len(asap), ":", ", ".join(asap) or "없음", f"(깊이 EO-1 {D['EO-1']}, OP-5 {D['OP-5']})")
    out("(d) 임계 경로 길이(card 수): LA-1 병합", D["LA-1"], "/ CL-1", D["CL-1"], "/ LA-1 완료", D["LA-1#done"], "/ OP-5", D["OP-5"], "/ VB-1", D["VB-1"], "/ DE-1", D["DE-1"], "/ OS-V", D["OS-V"])
    out("")
a, b = res["(i) OP-5 → LA-1"]["D"], res["(ii′) LA-1 → OP-5"]["D"]
out("## 차(ii′ − i)")
for k in ("LA-1", "OP-5", "VB-1", "DE-1", "CL-1", "LA-1#done", "OS-V"):
    out(f"{k}: {a[k]} → {b[k]} (차 {b[k] - a[k]:+d})")
open(OUT, "w", encoding="utf-8").write("\n".join(log) + "\n")
print("\n".join(log))
