"""병합 선행 그래프와 'LA-1 → OP-5' 추가 시 순환 판정 (icmr4 C4-Q6 G-1 (ii′) 실측).

입력(읽기만, git show): plan/v6386 `65377396`
  gain-budget-gmid-sizing.plan.md : N6.1 card 순서 표('화살표는 먼저 병합'), 병합 순서 규칙 표 #1~#21, N6.3 (iii) 'EO-1 선행의 뜻'
  oracle-portability / headroom-chain / graph-consumption / offset-trim / offset-strategy : card 표 '선행' 칸
규칙(N6.3 (iii), gain-budget P:1439): 'SPICE 다리 선행'·'oracle 다리 선행'·'완료 판정 선행'은 병합 선행이 아니다.

방법 두 단계:
  A. 자동 추출(참고) -- 선행 칸의 괄호 밖 문장을 쉼표·쌍반점으로 나눠 card id를 뽑는다. 선행 칸에는 뒤따름·파일 겹침·다른 쌍의
     근거가 섞여 있어 자동 결과에는 가짜 간선이 생긴다(아래 '자동 추출의 가짜 순환'으로 기록).
  B. 판정용 그래프 -- 순환 질문에 닿는 card(LA-1·OP-5의 조상 후보 전부)마다 선행 칸을 사람이 읽은 간선 목록.
     각 간선은 계획 원문 조각(verbatim)을 단언해 원문에 묶는다(조각이 그 줄에 없으면 실행 실패 = fail-closed).
판정: LA-1 → OP-5를 더해 순환이 생기는가 ⇔ 판정용 그래프에서 OP-5가 LA-1의 병합 조상인가(전이 폐포).
출력: merge_order_cycle.txt
"""
import re, subprocess, sys
from collections import defaultdict, deque

REPO = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6387"
REV = "65377396"
OUT = __file__.replace(".py", ".txt")
log = []


def out(*a):
    log.append(" ".join(str(x) for x in a))


def get(name):
    raw = subprocess.run(["git", "-C", REPO, "show", f"{REV}:docs/01-plan/features/{name}.plan.md"], capture_output=True).stdout
    return raw.decode("utf-8").split("\n")


P = {n: get(n) for n in ("gain-budget-gmid-sizing", "oracle-portability", "headroom-chain", "graph-consumption", "offset-trim", "offset-strategy")}
ABBR = {"gb": "gain-budget-gmid-sizing", "op": "oracle-portability", "hc": "headroom-chain", "gc": "graph-consumption"}

# ---------------- B. 판정용 그래프(사람이 읽은 간선 + 원문 조각 단언) ----------------
# (먼저, 나중, 계획:줄, 원문 조각, 판단)
MANUAL = [
    # LA-1 선행(gb:1306)
    ("cardB", "LA-1", "gb:1306", "XRUN-F1 card B(병합됨)", "병합 선행"),
    ("WB-1", "LA-1", "gb:1306", "card WB-1(v6.38.2 -- LA-0 base에 포함)", "병합 선행"),
    ("IT-1+IT-2", "LA-1", "gb:1306", "IT-1 + IT-2 통합 병합(IT-2a~IT-2e)", "병합 선행"),
    ("UB-1", "LA-1", "gb:1306", "UB-1(블록 국소 모델 통합, O-38 (2)) + NL-1(같은 통합 병합)", "병합 선행(UB-1·NL-1 한 병합)"),
    ("HC-S", "LA-1", "gb:1306", "headroom-chain HC-S(`sat_threshold` 정본)", "병합 선행"),
    ("TB-1", "LA-1", "gb:1306", "card TB-1(θ 기저 S/B/F 분류 필드", "병합 선행"),
    ("HC-1", "LA-1", "gb:1306", "headroom-chain HC-1(R-1′ 묶음 -- 병합 순서 규칙 표 #16", "병합 선행(표 #16)"),
    ("EO-1", "LA-1", "gb:1306", "코드 의존이라 병합 선행", "병합 선행(N6.3 (iii) 예외)"),
    ("SF-1", "LA-1", "gb:1306", "card SF-1(범위 9 -- N6.1 병합 순서 규칙 표 #12", "병합 선행(표 #12)"),
    # WB-1(gb:1296)
    ("cardB", "WB-1", "gb:1296", "XRUN-F1 card B(병합됨)", "병합 선행"),
    ("HC-S", "WB-1", "gb:1296", "headroom-chain HC-S 뒤(순서 HC-S → WB-1", "병합 선행(표 #6·#11)"),
    ("OP-7", "WB-1", "gb:1296", "oracle-portability OP-7(bin 경계 선언 기록 -- 범위 0 D1이 읽음", "병합 선행(코드가 읽음)"),
    ("IT-1+IT-2", "WB-1", "gb:1296", "Q-W1 승인 시 card IT-1 + IT-2 통합 병합 선행 추가", "조건부 병합 선행 -- 보수적으로 넣음"),
    # IT-1 + IT-2(gb:1285), SF-1(gb:1299), EO-1(gb:1284 + 표 #13)
    ("cardB", "IT-1+IT-2", "gb:1285", "XRUN-F1 card B; SPICE 다리 선행 EO-1", "card B만 병합 선행(EO-1은 다리)"),
    ("IT-1+IT-2", "SF-1", "gb:1299", "IT-1 + IT-2 통합 병합(데이터 변경을 IT-0 기준선", "병합 선행"),
    ("OP-3", "EO-1", "gb:1284", "oracle-portability OP-3 | design 개정", "병합 선행(착수 조건 'OP-3 병합')"),
    ("IT-1+IT-2", "EO-1", "gb:1284", "EO-1 병합은 IT-1 + IT-2 통합 병합 뒤", "병합 선행(표 #13)"),
    # UB-1·NL-1, TB-1
    ("NL-1", "UB-1", "gb:1307", "NL-1과 같은 통합 병합", "같은 병합(순서 동등) -- 조상 계산에 NL-1 조상 포함용"),
    # NL-1(gb:1302): 'SPICE 다리 선행 EO-1' -- 병합 선행 없음
    # TB-1(gb:1293): 'EO-1(SPICE 다리)' -- 병합 선행 없음
    # headroom-chain
    ("HC-D", "HC-S", "hc:515", "HC-D, XRUN-F1 card C 병합, card IT-1 병합", "병합 선행"),
    ("cardC", "HC-S", "hc:515", "XRUN-F1 card C 병합", "병합 선행"),
    ("IT-1+IT-2", "HC-S", "hc:515", "card IT-1 병합", "병합 선행"),
    ("EO-1", "HC-S", "hc:515", "**상위 card EO-1**(병합 선행", "병합 선행(표 #7)"),
    ("HC-0", "HC-D", "hc:514", "HC-0", "병합(문서) 선행"),
    ("HC-D", "HC-1", "hc:516", "HC-D, XRUN-F1 card C 병합, **card IT-1 병합**", "병합 선행"),
    ("cardC", "HC-1", "hc:516", "XRUN-F1 card C 병합", "병합 선행"),
    ("IT-1+IT-2", "HC-1", "hc:516", "**card IT-1 병합**", "병합 선행"),
    ("HC-S", "HC-1", "hc:516", "**HC-S 병합**", "병합 선행"),
    ("TB-1", "HC-1", "hc:516", "**상위 card TB-1 병합**", "병합 선행"),
    ("GC-1", "HC-1", "hc:516", "graph-consumption GC-D design 승인·GC-1", "병합 선행(통합 병합 짝 GC-8의 선행)"),
    # graph-consumption
    ("GC-D", "GC-1", "gc:638", "GC-D", "선행"),
    ("GC-0a", "GC-D", "gc:637", "GC-0a(GC-0b 결과가 필요한 design 항목은 GC-0b 뒤)", "선행"),
    ("GC-0b", "GC-D", "gc:637", "GC-0b 뒤", "선행(일부 항목) -- 보수적으로 넣음"),
    ("GC-1", "GC-8", "gc:644", "GC-1, headroom-chain HC-1과 같은 통합 병합", "선행"),
    ("HC-S", "GC-8", "gc:644", "순서: HC-S → [HC-1 + GC-8 통합 병합] → 상위 LA-1", "선행"),
    ("GC-8", "LA-1", "gc:644", "순서: HC-S → [HC-1 + GC-8 통합 병합] → 상위 LA-1", "병합 선행(HC-1과 같은 병합)"),
    # oracle-portability(op card 표)
    ("OP-2", "OP-3", "op:508", "OP-2(따로 검토, 함께 병합), OP-1b", "선행"),
    ("OP-1b", "OP-3", "op:508", "OP-1b(병합 조건 (b)의 비교 상대", "선행"),
    ("OP-0", "OP-2", "op:507", "OP-0, OP-1", "선행"),
    ("OP-1", "OP-2", "op:507", "OP-0, OP-1", "선행"),
    ("OP-1a", "OP-1b", "op:506", "OP-1a(보관 규칙·변환 스크립트)", "선행"),
    ("OP-0", "OP-1b", "op:506", "OP-0 필드 대응표", "선행"),
    ("OP-1", "OP-1a", "op:505", "OP-1", "선행"),
    ("OP-3", "OP-7", "op:512", "OP-3(어댑터가 생긴 뒤", "선행"),
    ("OP-3", "OP-4", "op:509", "OP-3", "선행"),
    ("OP-4", "OP-5", "op:510", "OP-4, EO-1(생산자 갱신", "선행"),
    ("EO-1", "OP-5", "op:510", "OP-4, EO-1(생산자 갱신", "병합 선행(G-18 생산자 갱신 -- gb N6.3 (iii) 예외)"),
    ("OP-1b", "OP-5", "op:510", "OP-1b(noise·MC (가-2) 동일성의 비교 상대", "선행"),
]
# 병합 선행이 아니라고 읽은 언급(조상 계산에서 뺌) -- 원문 조각과 판단
NOT_MERGE = [
    ("DE-1", "LA-1", "gb:1306", "DE-1·FX-1·GC-9는 선행 아님", "명시적 '선행 아님'; 뒤따름 = DE-1(표 #2)"),
    ("OS-2", "LA-1", "gb:1306", "뒤따름 = DE-1(표 #2)·offset-strategy OS-2(표 #8·#9)", "LA-1 뒤따름(역방향)"),
    ("EO-1", "IT-1+IT-2", "gb:1285", "SPICE 다리 선행 EO-1", "다리 선행(N6.3 (iii))"),
    ("EO-1", "SF-1", "gb:1299", "SPICE 다리 선행 EO-1(범위 9", "다리 선행 -- EO-1 ↔ SF-1 병합 선후 미고정"),
    ("EO-1", "TB-1", "gb:1293", "EO-1(SPICE 다리)", "다리 선행"),
    ("EO-1", "NL-1", "gb:1302", "SPICE 다리 선행 EO-1", "다리 선행"),
    ("EO-1", "WB-1", "gb:1296", "SPICE 다리 선행 EO-1", "다리 선행"),
    ("EO-1", "HC-1", "hc:516", "완료 판정 선행 -- SPICE 다리. 병합 선행 아님", "다리 선행"),
    ("OP-5", "DE-1", "gb:1300", "oracle 다리 선행 EO-1, oracle-portability OP-5·OP-10", "oracle 다리 선행(질문 검증 A (a))"),
    ("OS-2", "WB-1", "gb:1296", "파일 겹침만(선후 고정 없음", "파일 겹침만"),
    ("HC-1", "WB-1", "gb:1296", "파일 겹침만(선후 고정 없음", "파일 겹침만"),
    ("SF-1", "DE-1", "gb:1299", "DE-1보다 먼저", "SF-1 → DE-1(정방향, 순환 질문과 무관)"),
    ("SF-1", "VB-1", "gb:1299", "VB-1보다 먼저", "SF-1 → VB-1(정방향, 무관)"),
    ("GC-9", "LA-1", "gb:1306", "DE-1·FX-1·GC-9는 선행 아님", "명시적 '선행 아님'"),
    ("FX-1", "LA-1", "gb:1306", "DE-1·FX-1·GC-9는 선행 아님", "명시적 '선행 아님'"),
]


def line_of(tag):
    ab, ln = tag.split(":")
    return P[ABBR[ab]][int(ln) - 1]


bad = []
for a, b, tag, frag, why in MANUAL + NOT_MERGE:
    if frag not in line_of(tag):
        bad.append((a, b, tag, frag))
if bad:
    for x in bad:
        out("원문 조각 불일치(fail-closed):", x)
    open(OUT, "w", encoding="utf-8").write("\n".join(log) + "\n")
    sys.exit(1)

E = defaultdict(set)
for a, b, *_ in MANUAL:
    E[a].add(b)
# UB-1 = NL-1 같은 병합: NL-1의 조상도 UB-1의 조상(양방향 넣지 않고 NL-1 -> UB-1 하나로 충분)


def anc(n, edges):
    rev = defaultdict(set)
    for a, bs in edges.items():
        for b in bs:
            rev[b].add(a)
    seen, par, q = set(), {}, deque([n])
    while q:
        x = q.popleft()
        for p in sorted(rev[x]):
            if p not in seen:
                seen.add(p); par[p] = x; q.append(p)
    return seen, par


def chain(par, s, g):
    p = [s]
    while p[-1] != g:
        p.append(par[p[-1]])
    return " → ".join(p)


a_la1, p1 = anc("LA-1", E)
a_op5, p2 = anc("OP-5", E)
out(f"# merge_order_cycle -- plan/v6386 {REV}")
out("## B. 판정용 그래프(사람이 읽은 간선, 원문 조각 단언 통과):", sum(len(v) for v in E.values()), "간선")
out("LA-1의 병합 조상", len(a_la1), ":", ", ".join(sorted(a_la1)))
out("OP-5의 병합 조상", len(a_op5), ":", ", ".join(sorted(a_op5)))
c1 = "OP-5" in a_la1
out("판정 (ii′) LA-1 → OP-5 추가 시 순환:", "있음 -- " + chain(p1, "OP-5", "LA-1") if c1 else "없음 (OP-5는 LA-1의 병합 조상이 아님)")
c2 = "LA-1" in a_op5
out("참고 (i) OP-5 → LA-1 추가 시 순환:", "있음 -- " + chain(p2, "LA-1", "OP-5") if c2 else "없음 (LA-1은 OP-5의 병합 조상이 아님)")
out("두 card의 기존 선후:", "LA-1이 OP-5 조상" if c2 else ("OP-5가 LA-1 조상" if c1 else "미고정(서로 조상 아님) -- P:1439 사실과 일치"))
out("공통 조상(둘 다 기다리는 card):", ", ".join(sorted(a_la1 & a_op5)))
out("")
out("## 간선 근거(먼저 → 나중 :: 계획:줄 :: 원문 조각 :: 판단)")
for a, b, tag, frag, why in MANUAL:
    out(f"{a} → {b} :: {tag} :: '{frag}' :: {why}")
out("")
out("## 병합 선행이 아니라고 읽은 언급(수작업 판정 근거)")
for a, b, tag, frag, why in NOT_MERGE:
    out(f"{a} ? {b} :: {tag} :: '{frag}' :: {why}")
out("")
out("## 조상 계산에서 열지 않은 card(그 조상이 OP-5인지 영향 없음 근거)")
out("cardB·cardC(XRUN-F1, 이 계획들 밖 -- 병합됨/별도 계획, oracle card 선행 문언 없음), HC-0·GC-0a·GC-0b(검증자 측정 -- '이 계획 승인'·'K-3 구현 card 병합' 선행), OP-0·OP-1(oracle 계획 승인)")

# ---------------- A. 자동 추출(참고) ----------------
ID = r"(?:IT-1 \+ IT-2|XRUN-F1 card [BC]|(?:OP|HC|GC|TR|OS|EO|IT|SF|DE|LA|TB|WB|UB|NL|FX|SB|CL|VB|PW|RS|CPG|CMP|DR|PD|LI|SD|AP|NU|RB|TN|GV|SH|DT|LT|GL|ME|PR)-[0-9]+[A-Za-z]*|(?:OP|HC|GC|TR|OS)-[A-Z]+[0-9]*)"
IDRE = re.compile(ID)


def norm(x):
    if x.startswith("IT-1 + IT-2") or re.fullmatch(r"IT-[12][a-e]?", x):
        return "IT-1+IT-2"
    return {"XRUN-F1 card B": "cardB", "XRUN-F1 card C": "cardC"}.get(x, x)


def strip_paren(t):
    o, d = [], 0
    for ch in t:
        if ch in "([":
            d += 1
        elif ch in ")]":
            d = max(0, d - 1)
        elif d == 0:
            o.append(ch)
    return "".join(o)


AE = defaultdict(set)
for name, L in P.items():
    hs = [i for i, l in enumerate(L) if l.startswith("| card |") and "선행" in l]
    for h in hs:
        col = [c.strip() for c in L[h].split("|")].index("선행")
        i = h + 2
        while i < len(L) and L[i].startswith("|"):
            cells = [c.strip() for c in L[i].split("|")]
            m = IDRE.search(cells[1]) if len(cells) > col else None
            if m:
                card = norm(m.group(0))
                for seg in re.split(r"[;,]", strip_paren(cells[col])):
                    if any(k in seg for k in ("다리", "완료 판정", "파일 겹침", "선행 아님")):
                        continue
                    for y in IDRE.finditer(seg):
                        y = norm(y.group(0))
                        if y != card:
                            AE[y].add(card)
            i += 1


def find_cycle(edges):
    color, st = {}, []
    sys.setrecursionlimit(10000)
    def dfs(u):
        color[u] = 1; st.append(u)
        for v in sorted(edges.get(u, ())):
            if color.get(v) == 1:
                return st[st.index(v):] + [v]
            if v not in color:
                r = dfs(v)
                if r:
                    return r
        color[u] = 2; st.pop()
    for n in sorted(edges):
        if n not in color:
            r = dfs(n)
            if r:
                return r


out("")
out("## A. 자동 추출(참고 -- 판정에 쓰지 않음):", sum(len(v) for v in AE.values()), "간선")
cy = find_cycle(AE)
out("자동 추출 그래프 자체의 순환:", " → ".join(cy) if cy else "없음")
out("-> 자동 추출은 선행 칸의 '뒤따름'·'X보다 먼저'·'X 앞' 같은 역방향 문언을 정방향으로 읽어 가짜 순환을 만든다(예: 위 순환). 그래서 순환 판정은 B(원문 조각 단언이 붙은 수작업 간선)로만 한다.")
a2, _ = anc("LA-1", AE)
out("자동 추출에서 OP-5가 LA-1 조상으로 잡히는 경로가 있는가:", "OP-5" in a2, "-- 있으면 그 경로의 간선은 아래 '모호 문장'에서 수작업 판정")
if "OP-5" in a2:
    _, pp = anc("LA-1", AE)
    out("자동 경로:", chain(pp, "OP-5", "LA-1"))
out("")
out("## 파싱이 모호한 문장과 수작업 판정")
out("1. gb:1300 DE-1 선행 칸 'oracle 다리 선행 EO-1, oracle-portability OP-5·OP-10, 엔진 VB-1' -- 쉼표로 나누면 OP-5가 '다리' 문맥을 잃어 OP-5 → DE-1 병합 간선으로 잘못 잡힌다. 판정: oracle 다리 선행(N6.3 (iii) P:1439, 질문 검증 A (a)) -- 병합 간선 아님.")
out("2. gb:1306 LA-1 선행 칸 '뒤따름 = DE-1(표 #2)·offset-strategy OS-2(표 #8·#9)' -- 역방향(LA-1 → DE-1·OS-2). 판정: LA-1의 조상 아님.")
out("3. gb:1299 SF-1 선행 칸 'VB-1보다 먼저'·'DE-1보다 먼저'·'LA-1보다 먼저' -- 역방향. 판정: SF-1 → VB-1·DE-1·LA-1.")
out("4. gb:1296 WB-1 선행 칸 '파일 겹침만(선후 고정 없음, …): … offset-strategy OS-2 … headroom-chain HC-1 + graph-consumption GC-8' -- 순서 간선 아님. 'LA-0 앞'·'DE-1 앞' = 역방향.")
out("5. gb:1347 표 #21 '#8·#9를 OS-2 → LA-1로, 또는 #7을 필드 card → EO-1로 두면 순환 둘' -- 가정 문장. 판정: 간선 아님.")
out("6. gb:1296 'Q-W1 승인 시 card IT-1 + IT-2 통합 병합 선행 추가' -- 조건부. 판정: 보수적으로 병합 간선에 넣음(조상이 늘어도 OP-5는 들지 않음 -- IT-1 + IT-2의 조상은 card B뿐).")
out("7. gc:637 'GC-0b 결과가 필요한 design 항목은 GC-0b 뒤' -- 부분 선행. 판정: 보수적으로 넣음(GC-0b 선행 = '이 계획 승인, K-3 구현 card 병합' -- oracle card 없음).")
if __name__ == "__main__":
    open(OUT, "w", encoding="utf-8").write("\n".join(log) + "\n")
    print("\n".join(log[:9]))
