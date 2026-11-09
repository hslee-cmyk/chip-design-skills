import re, pathlib
roots = [pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386/docs/01-plan/features"),
         pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features")]
NUM = re.compile(r"tol_V(?!Dsat)|tol_VDsat|\(gm/ID\)·tol|ε ?=|ε·|분해능|허용오차|dc_tol_v")
PHY = re.compile(r"꺼짐|전도|I_off|포화|VDsat|VDSAT|반전|정의역|누설|triode|경계|S_d|cut-?off|off")
out = open("grep2_hits.txt", "w", encoding="utf-8")
seen=set(); n=0
for r in roots:
    for f in sorted(r.glob("*.md")):
        if "history" in f.name or "verilog" in f.name: continue
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for m in NUM.finditer(line):
                s = max(0, m.start()-160); e = min(len(line), m.end()+160)
                w = line[s:e]
                if not PHY.search(w): continue
                key=(f.name,i,s//300)
                if key in seen: continue
                seen.add(key); n+=1
                out.write(f"[{f.name}:{i}] ...{w}...\n")
print(n)
