import sys
src = r"C:\Users\HSLEE\AppData\Local\Temp\claude\C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills\63c6146a-ab1d-4035-a169-bae810986922\scratchpad\design30.md"
s = open(src, encoding="utf-8").read()
key = "E3B_AST=$(cat <<'PYEOF'\n"
i = s.index(key) + len(key)
j = s.index("PYEOF\n)", i)
open(r"C:\g347\out\e3b_ast.py", "w", encoding="utf-8", newline="\n").write(s[i:j])
print("extracted", s[i:j].count("\n"), "lines")
