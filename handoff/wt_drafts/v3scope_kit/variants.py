"""계약 1 문장이 정하지 않은 해석 자리(키트 §모호점)가 수치를 바꾸는지 -- measure_b26.py가 만든 모의 커밋(sim-b1, sim-h4, sim-h2, sim-ho)에서
scope_proto의 해석 스위치만 바꿔 다시 센다. 결과: C:/g109/out/variants.txt"""
import sys

KIT = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3scope_kit"
sys.path.insert(0, KIT)
import measure_b26 as M   # noqa: E402
import scope_proto as SP   # noqa: E402

M.TXT = "C:/g109/out/variants.txt"
open(M.TXT, "w").close()
sys.path.insert(0, "C:/g109/scripts")
import sim_head as S       # noqa: E402
M.DUR = S.durations()
pairs = (("b26_v4", "sim-b1", "sim-h4"), ("b26_review2", "sim-b1", "sim-h2"), ("b26_oldsim", "7535799", "sim-ho"))
for ncn, pp in (("own", "kind_index"), ("subtree", "flat_index")):
    SP.NEW_COMPOUND_NAMES, SP.PARAM_POS = ncn, pp
    for label, b, h in pairs:
        M.measure("%s__names-%s__pos-%s" % (label, ncn, pp), M.git("rev-parse", b).decode().strip(), M.git("rev-parse", h).decode().strip())
