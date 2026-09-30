"""w_sites.py compare 모드의 판별력 확인용 합성 병합본(auditor). 병합본이 아니다 -- 스크래치 복제본 C:/g12/synth에만 쓴다.
사용: python -P synth_merge.py <w_sites_base.json> <synth 루트> <variant>
variant: ok      -- 18곳을 width_from_id_density(Lop, IDop, IDuop)로 바꾸고 size_transistor 앞에 def 추가
         swap    -- ok + 한 곳(첫 사이트)의 인자 순서를 (IDop, Lop, IDuop)로
         context -- ok + 한 사이트 문장의 다른 부분 변경(사이트 3456 줄에서 치환 뒤 ' * 1.0' 덧붙임은 모양이 바뀜 -> 대신 대상 문장 앞줄에 무관 문장 추가 없이
                    같은 줄 좌변 이름 변경은 위험하므로, 호출 뒤에 '+ 0.0'을 붙인다)
"""
import json, sys
base_f, root, variant = sys.argv[1:4]
sites = json.load(open(base_f, encoding="utf-8"))["sites"]
path = root + "/skills/analog-gmid-design/assets/sizing_recipe.py"
src = open(path, encoding="utf-8", newline="").read()
lines = src.split("\n")
# 뒤에서부터 바꿔 줄·열이 흔들리지 않게
for i, s in enumerate(sorted(sites, key=lambda s: (s["line"], s["col"]), reverse=True)):
    assert s["line"] == s["end_line"], s
    ln = lines[s["line"] - 1]
    seg = s["expr_src"]
    # col은 UTF-8 바이트 오프셋
    b = ln.encode("utf-8")
    col = s["col"]
    assert b[col:col + len(seg.encode("utf-8"))].decode("utf-8") == seg, (s["line"], seg)
    Lop, IDop, IDuop = s["operands_src"]
    args = (IDop, Lop, IDuop) if (variant == "swap" and s is sites[0]) else (Lop, IDop, IDuop)
    call = "width_from_id_density(%s, %s, %s)" % args
    if variant == "context" and s["line"] == 3456:
        call += " + 0.0"
    lines[s["line"] - 1] = (b[:col] + call.encode("utf-8") + b[col + len(seg.encode("utf-8")):]).decode("utf-8")
out = "\n".join(lines)
anchor = "\ndef size_transistor("
assert out.count(anchor) == 1
out = out.replace(anchor, "\ndef width_from_id_density(L: float, ID: float, IDu: float) -> float:\n    return L * ID / IDu\n\n" + anchor, 1)
open(path, "w", encoding="utf-8", newline="").write(out)
print("written", variant)
