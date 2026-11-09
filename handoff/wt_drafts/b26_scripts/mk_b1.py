"""모의 base b1 = gate master HEAD(2d58fd8, 엔진 = 7535799 + P9 b7765b0) archive + B34 코드 변경(build_b34: 사이트 1·2·3·11·11b).
전제: C:/g83/base = `git archive HEAD`, C:/g83/b1 = base 사본(cp -r). 이 스크립트는 b1의 SD만 B34판으로 바꾼다."""
import sys
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_scripts")
import v3_scope_classify as V  # noqa: E402  (sim_head가 C:/g83/b1을 읽는다 -- 이 시점 b1 = base)

S = V.S
src0 = S.BASEF[S.SD]
head = V.build_b34(S.BASEF)
assert head[S.SD] != src0
with open("C:/g83/b1/" + S.SD, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(head[S.SD])
print("b1 SD written; lines", src0.count("\n"), "->", head[S.SD].count("\n"))
