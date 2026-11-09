# O-200 v3 전수 grep (검증 42 Major B) -- 수치 양과 같은 줄 한정이 아니라 전도·꺼짐 개념어 전수.
# 대상: 계획 wt/plan-v6386 a4d87f1a 의 *.plan.md, design wt/design-v115 e957ba44 의 *.design.md (history·verilog 제외), user_decisions.md.
# 패턴: dc_conduction_floor | conduction | 전도 | I_off | off_current | 꺼짐 | `off` | V_on | intended_region
# 출력: grep_conduction_hits.txt (파일:행 + 패턴 주변 260자 창, 창마다 한 줄), grep_conduction_counts.txt (파일·패턴별 행 수)
import re, pathlib, collections
ROOTS = [pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386/docs/01-plan/features"),
         pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features")]
UD = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md")
PATS = {"floor": r"dc_conduction_floor|conduction_floor", "conduction": r"conduction", "전도": r"전도", "I_off": r"I_off|off_current",
        "꺼짐": r"꺼짐|꺼지", "off": r"`off`|off 선언|off 소자|off 유지", "V_on": r"V_on", "region": r"intended_region"}
RX = {k: re.compile(v) for k, v in PATS.items()}
HERE = pathlib.Path(__file__).parent
files = [f for r in ROOTS for f in sorted(r.glob("*.md")) if "history" not in f.name and "verilog" not in f.name] + [UD]
hits = open(HERE / "grep_conduction_hits.txt", "w", encoding="utf-8")
cnt = collections.Counter()
for f in files:
    for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        ks = [k for k, rx in RX.items() if rx.search(line)]
        if not ks:
            continue
        for k in ks:
            cnt[(f.name, k)] += 1
        seen = set()
        for k in ks:
            for m in RX[k].finditer(line):
                b = m.start() // 400
                if b in seen:
                    continue
                seen.add(b)
                s = max(0, m.start() - 130); e = min(len(line), m.end() + 130)
                hits.write(f"[{f.name}:{i}] {{{k}}} ...{line[s:e]}...\n")
with open(HERE / "grep_conduction_counts.txt", "w", encoding="utf-8") as fh:
    for (fn, k), n in sorted(cnt.items()):
        fh.write(f"{fn}\t{k}\t{n}\n")
print(sum(cnt.values()), "line-pattern hits")
