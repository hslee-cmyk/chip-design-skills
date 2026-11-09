import re, pathlib, sys, collections
roots = [pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386/docs/01-plan/features"),
         pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features")]
pats = {k: re.compile(v) for k, v in {
 "tolV": r"tol_V|tol_VDsat|dc_tol_v|tol_v",
 "eps": r"ε|epsilon",
 "res": r"분해능",
 "allow": r"허용오차|허용 오차",
 "inv": r"반전 수준|반전 계수|ln IC|약반전|강반전|IC =",
 "off": r"꺼짐|I_off|전도 여유|누설",
 "dom": r"정의역|탐색 개방|S_d",
 "sat": r"VDsat|VDSAT|포화 기준|포화 여유",
}.items()}
out = open("grep_hits.txt", "w", encoding="utf-8")
cnt = collections.Counter()
for r in roots:
    for f in sorted(r.glob("*.md")):
        if "history" in f.name or "verilog" in f.name: continue
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            keys = [k for k, p in pats.items() if p.search(line)]
            if not keys: continue
            if not ({"tolV","eps","res","allow"} & set(keys)): continue   # 수치 양이 낀 줄만
            if not ({"inv","off","dom","sat"} & set(keys)): continue      # 물리 경계·정의역이 낀 줄만
            cnt[f.name] += 1
            # 수치 양 키워드 주변 스니펫
            snips = []
            for m in re.finditer(r"tol_V|tol_VDsat|ε|분해능|허용오차", line):
                s = max(0, m.start()-120); e = min(len(line), m.end()+120)
                snips.append(line[s:e].replace("\n"," "))
                if len(snips) >= 4: break
            out.write(f"### {f.name}:{i} {keys}\n" + "\n  ~ ".join(snips) + "\n")
print(cnt)
