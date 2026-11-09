"""v6.38.4 스물한째 커밋 -- 분량 정리(이력성 서술 → history). 규칙 문언 불변."""
import re, json
B = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6384/docs/01-plan/features/"
S = "C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/"
T = "v6.38.4 스물한째 커밋 분량 정리"
REF = "history H2 'v6.38.4 스물한째 커밋 분량 정리' 행"


def load(f):
    return open(B + f, "rb").read().decode("utf-8").replace("\r\n", "\n")


def save(f, s):
    open(B + f, "wb").write(s.replace("\n", "\r\n").encode("utf-8"))


def esc(t):
    return t.replace("|", "\\|").replace("\\\\|", "\\|")


F = "gain-budget-gmid-sizing.plan.md"
g0 = load(F)
g = g0
L = g.split("\n")
MOVED = []

# 1. Status 이전 판 사슬
s = L[10]
i = s.index(" 이전 판: ")
chain = s[i + 1:]
L[10] = s[:i] + " 이전 판 Status 사슬(v6.38.3 이하) = history H1 '이전 판 Status 사슬' 절(" + T + ")."
MOVED.append(("Status 이전 판 사슬", "H1 절"))
# 2. 553 문단
p553 = L[552]
assert p553.startswith("**배정할 card가 없던 사안 -- 배정 기본안**")
L[552] = "**배정할 card가 없던 사안**: 배정 결과는 위 배정 표의 card 칸이 정본이다(B4 → IT-1 범위 6 (b), B12 → DT-1, B13 → SF-1 범위 6 (e) -- 승인 대기 P9-M1a; IT-1·DT-1·SF-1 성격 확장은 원래 취지와 다름). `graph/coupling`은 엔진 소비자가 0이라 LA-1 design이 GB3 y를 쓰지 않으면 `coupling_vars`를 삭제 대상으로 올린다(O-169, LA-1 design 착수 확인 항목). 블록 안 반복(감사 §2.3 E)은 이 규칙 밖이고 O-15 (E) 블록 안 local 범위(NFR-2 점검 대상)다. 배정 근거·대안 비교 = " + REF + "."
MOVED.append(("N3.3 '배정할 card가 없던 사안' 문단", p553))
p555 = L[554]
assert p555.startswith("**v6.38.4 P9 계열 승인 질문 대안 비교**")
L[554] = "**P9 계열 승인 질문 대안 비교**: " + REF + "(승인 전 참고)."
MOVED.append(("N3.3 'P9 계열 승인 질문 대안 비교' 문단", p555))
# 3. DR-1 근거·사실
k = [j for j, l in enumerate(L) if l.startswith("### N6.36 card DR-1")][0]
assert L[k + 2].startswith("**근거**:") and L[k + 4].startswith("**사실**(")
MOVED.append(("N6.36 DR-1 근거 문단", L[k + 2]))
MOVED.append(("N6.36 DR-1 사실 문단", L[k + 4]))
L[k + 2] = "**근거·사실**: " + REF + "(사용자 지시 2026-10-29 백로그 재검증 → card 분배, 재감사 B_N53 I-H1 행; heldout `cnr_ota` 저항 분압 사슬과 `dc_resistor_cycle` 정지 실측 -- 착수 때 다시 잰다)."
del L[k + 3:k + 5]
# 4. DEC-105 실측 문장 둘
s = L[303]
a = s.index("**9회로 재측정**(")
b = s.index("대안: (A) 옛 반복", a)
MOVED.append(("DEC-105 (2) '9회로 재측정' 문장", s[a:b]))
s = s[:a] + "9회로 재측정 기록 = " + REF + ". " + s[b:]
a = s.index("실측(`wt/_drafts/evidence/2026-10-29/handcalc_principle_audit/p8_exact_slice.summary.json`")
b = s.index("점별 실측은 card WB-1 착수 실측).", a) + len("점별 실측은 card WB-1 착수 실측).")
MOVED.append(("DEC-105 (2) Q-P8 (A) 실측 문장", s[a:b]))
s = s[:a] + "(A) 잔차 실측은 N5.3 Q-P8 행과 " + REF + "." + s[b:]
L[303] = s
g = "\n".join(L)

# 5. 커밋별 괄호 표지 제거(규칙 문언 불변 -- 표지 낱말만)
ID = r"(?:[A-Za-z]{1,3}\d*-[A-Za-z]?\d+′?|n-\d+|m\d+-\d+|[A-Z]{1,2}\d+′?|m\d+)"
TOK = re.compile(r"(?:상위 )?v6\.38\.4 [가-힣]+째 커밋(?: 계획 검증 \d+)?(?: 단순화| 백로그 재감사| 정정| P9 검증)?(?: " + ID + r"(?:·" + ID + r")*)?(?:으로|로)?")
TOK2 = re.compile(r"계획 검증 \d+ " + ID + r"(?:·(?:검증 \d+ )?" + ID + r")*(?:으로|로)?")
removed = []


def strip(line):
    out = TOK.sub(lambda m: (removed.append(m.group(0)) or ""), line)
    out = TOK2.sub(lambda m: (removed.append(m.group(0)) or ""), out)
    for _ in range(3):
        for a_, b_ in [("( -- ", "("), ("(; ", "("), ("(, ", "("), ("( ", "("), (" -- )", ")"), ("; )", ")"), (", )", ")"), (" )", ")"), ("()", ""), (" -- , ", " -- "), (" -- ; ", " -- "), ("→  -- ", "→ "), (" -- -- ", " -- "), ("(+ : ", "(+ "), ("(: ", "("), ("(:", "("), ("·)", ")"), ("(·", "("), ("  ", " ")]:
            out = out.replace(a_, b_)
    return out


L = g.split("\n")
for j in range(len(L)):
    if j == 10:
        continue
    if TOK.search(L[j]) or TOK2.search(L[j]):
        L[j] = strip(L[j])
# Status 안 표지는 승인 항목 이름이라 그대로 둔다
L[11] = L[11] if not L[11].startswith("> **이력**") else L[11] + " v6.38.4 판의 커밋별 괄호 표지(커밋·검증 번호)는 " + REF + "로 옮겼다(" + T + ")."
g = "\n".join(L)
save(F, g)

# 검증: 지운 낱말이 표지 어휘뿐인지
w0 = re.findall(r"\S+", g0)
w1 = re.findall(r"\S+", g)
json.dump({"removed_tokens": removed}, open(S + "v12_removed.json", "w", encoding="utf-8"), ensure_ascii=False)
print("markers removed", len(removed), "bytes", len(g0.encode("utf-8")), "->", len(g.encode("utf-8")))

# history
GH = "gain-budget-gmid-sizing.history.md"
h = load(GH)
HL = h.split("\n")
i = [k for k, l in enumerate(HL) if l.startswith("| **v6.38.4 스무째 커밋**")][0]
HL.insert(i + 1, "| **v6.38.4 스물한째 커밋** 분량 정리(계획 v6.38.4, 검증 대기) | 2026-10-29 | 근거: 사용자 원칙 '계획서는 규칙·정의·게이트·완료 조건만, 경위·정정 이력·측정 조건·판 이력은 history'(계획 검증 8 §4 권고, 오케스트레이터 지시). 옮긴 것: Status 이전 판 사슬(아래 H1 '이전 판 Status 사슬' 절), N3.3 배정 근거 문단·P9 대안 비교 문단, N6.36 DR-1 근거·사실 문단, DEC-105 (2) 9회로 재측정·Q-P8 (A) 실측 문장(아래 H2 행), 계획 본문의 커밋별 괄호 표지 %d개('v6.38.4 N째 커밋 …'·'계획 검증 N …' 낱말 -- 목록은 H2 행). 규칙 문언 불변(표지 낱말 제거와 정리 기호만 -- 검증 스크립트 `v12_removed.json`). |" % len(removed))
h = "\n".join(HL)
HL = h.split("\n")
# H1 끝(## H2 앞)에 이전 판 사슬 절
k = [j for j, l in enumerate(HL) if l.startswith("## H2.")][0]
HL[k:k] = ["### 이전 판 Status 사슬 (" + T + "로 계획서 Status에서 옮김)", "", chain, ""]
h = "\n".join(HL)
HL = h.split("\n")
last = max(j for j, l in enumerate(HL) if l.startswith("|") and "v6.38.4 스무째 커밋 계획 검증 8" in l and "원문:" in l)
rows = ["| **%s** | 원문: «%s» | 2026-10-29 %s | 계획 같은 자리(참조 한 줄) |" % (esc(a), esc(b), T) for a, b in MOVED if b != "H1 절"]
from collections import Counter
cnt = Counter(removed)
rows.append("| **계획 본문 커밋별 괄호 표지 %d개** | 지운 표지 낱말(빈도): %s | 2026-10-29 %s | 계획 본문 각 자리 |" % (len(removed), esc("; ".join("%s ×%d" % (k_, v_) if v_ > 1 else k_ for k_, v_ in cnt.items())), T))
HL[last + 1:last + 1] = rows
save(GH, "\n".join(HL))
print("history rows", len(rows))
