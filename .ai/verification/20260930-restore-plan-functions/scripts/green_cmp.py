"""red 26건이 병합본 green 실행(-rA)에서 PASSED인지, T·병합본 수집 id 집합이 같은지.
사용: python -P green_cmp.py <red_T.jsonl> <green -rA 출력> <T 수집> <M 수집>"""
import json, sys
red_f, green_f, ct, cm = sys.argv[1:5]
red = [json.loads(l)["test_id"] for l in open(red_f, encoding="utf-8") if '"builtins.AttributeError"' in l]
passed = set()
for l in open(green_f, encoding="utf-8", errors="replace"):
    if l.startswith("PASSED "):
        x = l[7:].strip()
        f, sep, rest = x.partition("::")
        x = f.replace("\\", "/") + sep + rest   # 경로 부분만 슬래시로(매개변수 id의 역슬래시는 그대로)
        passed.add(x[x.find("skills/"):])
def ids(f):
    return {l.strip() for l in open(f, encoding="utf-8", errors="replace") if "::" in l}
a, b = ids(ct), ids(cm)
print("red", len(red), "passed_in_green", sum(r in passed for r in red), "missing", [r for r in red if r not in passed])
print("collect T", len(a), "M", len(b), "sym_diff", len(a ^ b))
