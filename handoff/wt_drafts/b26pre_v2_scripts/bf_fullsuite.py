"""B26 backfill 결함 card 사전 측정 -- 수정 후보(SR 11800·11879 삭제) 사본과 base 사본에서 assets/tests 전체를 돌려 결과를 비교한다.
w_base1 = 수정 후보, w_base2 = base. 두 사본 모두 contracts/에 시제품 두 파일(b26pre 17, b26bf 2)이 들어 있다.
결과: C:/g106/out/bf_fullsuite_<name>.txt (pytest -rA 출력 꼬리 + 요약)."""
import os, sys, threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_proto as RP  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = "skills/analog-gmid-design/assets/tests"


def go(name, root, fix):
    fp = root + "/skills/analog-gmid-design/assets/sizing_recipe.py"
    orig = open(fp, "rb").read()
    for proto, rel in (("proto_v2_test_b26pre.py", "test_b26pre_proto.py"), ("proto_bf_test.py", "test_b26bf_proto.py")):
        RP.PROTO = os.path.join(HERE, proto)
        RP.REL = TESTS + "/contracts/" + rel
        RP.place(root)
    try:
        if fix:
            src = open(fp, encoding="utf-8").read().split("\n")
            assert src[11799].strip() == "_backfill_interdig_ok(result)" and src[11878].strip() == "_backfill_interdig_ok(result)"
            del src[11878]
            del src[11799]
            with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(src))
        RP.REL = TESTS
        rc, dt, txt = RP.run(root, "1", timeout=5400)
    finally:
        with open(fp, "wb") as fh:
            fh.write(orig)
    lines = txt.splitlines()
    keep = [l for l in lines if l.startswith(("FAILED", "ERROR", "XFAIL"))] + lines[-3:]
    with open("C:/g106/out/bf_fullsuite_%s.txt" % name, "w", encoding="utf-8") as fh:
        fh.write("rc=%s %.0fs\n%s\n" % (rc, dt, "\n".join(keep)))
    print(name, rc, round(dt), lines[-1:] if lines else "", flush=True)


ts = [threading.Thread(target=go, args=("fix", "C:/g106/w_base1", True)),
      threading.Thread(target=go, args=("base", "C:/g106/w_base2", False))]
for t in ts:
    t.start()
for t in ts:
    t.join()
