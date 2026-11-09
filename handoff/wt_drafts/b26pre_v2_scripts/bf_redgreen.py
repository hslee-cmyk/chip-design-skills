"""B26 backfill 결함 card 초안 red-green 사전 측정.
C:/g106/w_base0(base 사본)에 proto_bf_test.py를 넣고 (1) base에서 실행(red 기대) (2) 수정 후보
'루프 안·루프 뒤의 사전 backfill 두 줄(base SR 11800·11879) 삭제'를 적용해 실행(green 기대)
(3) 같은 수정 사본에서 기존 test 중 run_matching_safety_with_finger_growth를 부르는 파일과 b26pre 시제품을 실행.
결과: C:/g106/out/bf_redgreen.txt"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_proto as RP  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = open("C:/g106/out/bf_redgreen.txt", "a", encoding="utf-8")
root = "C:/g106/w_base0"
A = root + "/skills/analog-gmid-design/assets/"


def log(s):
    OUT.write(s + "\n"); OUT.flush(); print(s, flush=True)


def summary(txt):
    ls = [l for l in txt.splitlines() if l.startswith("FAILED") or ((" passed" in l or " failed" in l) and " in " in l)]
    return ls[-6:]


RP.PROTO = os.path.join(HERE, "proto_bf_test.py")
RP.REL = "skills/analog-gmid-design/assets/tests/contracts/test_b26bf_proto.py"
RP.place(root)
fp = A + "sizing_recipe.py"
orig = open(fp, "rb").read()
try:
    for seed in ("0", "1"):
        rc, dt, txt = RP.run(root, seed)
        log("BASE seed=%s rc=%s %s" % (seed, rc, summary(txt)))
    src = open(fp, encoding="utf-8").read().split("\n")
    assert src[11799].strip() == "_backfill_interdig_ok(result)" and src[11878].strip() == "_backfill_interdig_ok(result)"
    del src[11878]
    del src[11799]
    with open(fp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(src))
    for seed in ("0", "1", "7"):
        rc, dt, txt = RP.run(root, seed)
        log("FIX seed=%s rc=%s %s" % (seed, rc, summary(txt)))
    # 기존 test 중 이 함수를 쓰는 파일 + b26pre 시제품(같은 수정 사본)
    RP.PROTO = os.path.join(HERE, "proto_v2_test_b26pre.py")
    RP.REL = "skills/analog-gmid-design/assets/tests/contracts/test_b26pre_proto.py"
    RP.place(root)
    targets = ["skills/analog-gmid-design/assets/tests/contracts/test_b26pre_proto.py"]
    for dp, _dn, fns in os.walk(A + "tests"):
        for fn in fns:
            if fn.endswith(".py") and fn.startswith("test_"):
                p = os.path.join(dp, fn)
                if "run_matching_safety_with_finger_growth" in open(p, encoding="utf-8").read() or "optimize_full_circuit_budget" in open(p, encoding="utf-8").read():
                    targets.append(os.path.relpath(p, root).replace("\\", "/"))
    log("FIX regression targets: %s" % targets)
    for t in targets:
        RP.REL = t
        rc, dt, txt = RP.run(root, "1", timeout=3000)
        log("FIX %s rc=%s %.0fs %s" % (t.split("/")[-1], rc, dt, summary(txt)))
finally:
    with open(fp, "wb") as fh:
        fh.write(orig)
    log("restored")
