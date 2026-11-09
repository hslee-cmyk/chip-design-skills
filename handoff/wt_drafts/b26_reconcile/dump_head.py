"""v4 모의 head의 SD·SR을 C:/g103/head_v4/에 쓰고 b1과의 unified diff를 C:/g103/out/head_v4.diff에 쓴다."""
import difflib, os, sys
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile")
import b26v4_head as H  # noqa: E402

head, _ = H.build_head("v4")
S = H.S
os.makedirs("C:/g103/head_v4", exist_ok=True)
out = []
for p in (S.SD, S.SR):
    with open("C:/g103/head_v4/" + p.split("/")[-1], "w", encoding="utf-8", newline="\n") as fh:
        fh.write(head[p])
    out += difflib.unified_diff(S.BASEF[p].split("\n"), head[p].split("\n"), "b1/" + p, "head/" + p, n=2, lineterm="")
with open("C:/g103/out/head_v4.diff", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) + "\n")
print(len(out))
