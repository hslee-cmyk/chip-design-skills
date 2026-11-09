"""2차 검토 적대 21건(+ 이 키트가 더한 경계 사례)에 독립 프로토타입(scope_proto, 계약 1)을 적용해
지금 규칙 / N2b(승인 당시) / N2w(이 card)의 대상 수·weak 판정·변경 고유 변이를 잰다. 기존 분류기(v3_scope_widen.classify_w)와 변이별로 대조한다.

사례 소스는 _drafts/v3_scripts/v3_adv21.py(2차 검토 표 설명대로 다시 쓴 판)의 CASES를 그대로 읽는다(그 파일의 경로만 C:/g109로 바꿔 exec).
결과: <KIT>/out/adv21_proto.txt
"""
import ast, os, sys

G = "C:/g109"
KIT = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3scope_kit"
sys.path.insert(0, KIT)
sys.path.insert(0, G + "/scripts")
import scope_proto as SP   # noqa: E402

OUT = KIT + "/out/adv21_proto.txt"
src = open("C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3_scripts/v3_adv21.py", encoding="utf-8").read()
src = src.replace("C:/g69/scripts", G + "/scripts").replace("C:/g69/out/v3_adv21.txt", G + "/out/v3_adv21_unused.txt")
src = src.split('\nif __name__ == "__main__":')[0]
A = {"__name__": "adv21src"}
exec(compile(src, "v3_adv21.py", "exec"), A)
W, V, mc, rch = A["W"], A["V"], A["mc"], A["rch"]

# 키트 추가 경계 사례(spec card 계약 8 (i)·(j)·(k) 꼴과 '두 단계'·'블록 끝 삭제' 경계)
EXTRA = []


def extra(cid, desc, base, head, weak, strong):
    EXTRA.append((cid, desc, A["mod"](base), A["mod"](head), weak, strong))


def _t(cond):
    if not cond:
        raise AssertionError()
    return True


extra("K1", "for 본문 뒤쪽 acc 변경 -> 앞쪽 out.append(acc - 1)(반복문 규칙, 계약 8 (j) 꼴)",
      "def f(xs):\n    out = []\n    acc = 0\n    for x in xs:\n        out.append(acc - 1)\n        acc = x + 1\n    return out\n",
      "def f(xs):\n    out = []\n    acc = 0\n    for x in xs:\n        out.append(acc - 1)\n        acc = x + 2\n    return out\n",
      lambda m: _t(len(m["f"]([1, 2])) == 2),
      lambda m: _t(m["f"]([1, 2]) == [-1, 2]))
extra("K2", "if 안 y 변경 -> 바깥 블록 return y + 1(다른 블록, 계약 8 (k) 꼴)",
      "def f(x):\n    y = 0\n    if x > 0:\n        y = x * 2\n    return y + 1\n",
      "def f(x):\n    y = 0\n    if x > 0:\n        y = x * 3\n    return y + 1\n",
      lambda m: _t(m["f"](-1) == 1),
      lambda m: _t(m["f"](1) == 4))
extra("K3", "a 변경 -> b = a -> if b > 1(두 단계)",
      "def f(x):\n    a = x + 1\n    b = a\n    LOG.append(b)\n    if b > 1:\n        return 1\n    return 0\n",
      "def f(x):\n    a = x + 2\n    b = a\n    LOG.append(b)\n    if b > 1:\n        return 1\n    return 0\n",
      lambda m: _t(m["f"](5) == 1),
      lambda m: _t(m["f"](0) == 1))


def run(cid, desc, bsrc, hsrc, weak, strong):
    P = A["passes"]
    assert P(bsrc, weak) and P(hsrc, weak) and not P(bsrc, strong) and P(hsrc, strong), ("sanity", cid)
    bdefs = dict(rch.iter_defs(ast.parse(bsrc)))
    res = {k: [0, 0, 0] for k in ("now", "N2b", "N2w")}
    disagree = []
    for q, hfn in mc.changed_defs(bsrc, hsrc):
        ms = mc.mutants(hfn, hsrc)
        if q in bdefs:
            sw = SP.select(bdefs[q], hfn, ms, "N2w")
            sb = SP.select(bdefs[q], hfn, ms, "N2b")
            rows, _ = W.classify_w(bdefs[q], hfn, hsrc)
            ow = [bool(V.DEFS["N2w"](t)) for t in rows]
            ob = [bool(V.DEFS["N2b"](t)) for t in rows]
            for (o, p, _), a1, a2, b1, b2 in zip(ms, sw, ow, sb, ob):
                if a1 != a2 or b1 != b2:
                    disagree.append("%s:%s proto(N2w=%s,N2b=%s) old(N2w=%s,N2b=%s)" % (o, p, a1, b1, a2, b2))
        else:
            sw = sb = [True] * len(ms)
        for (o, p, mfn), w, b in zip(ms, sw, sb):
            msrc = A["replace_def_with_deco"](hsrc, hfn, mfn)
            wk = not P(msrc, weak)
            sk = not P(msrc, strong)
            for k, s in (("now", True), ("N2b", b), ("N2w", w)):
                if s:
                    res[k][0] += 1
                    res[k][1] += (not wk)
                    res[k][2] += (sk and not wk)
    cell = lambda k: "%d / %s / %d" % (res[k][0], "PASS" if res[k][1] == 0 else "FAIL(weak 생존 %d)" % res[k][1], res[k][2])
    line = "| %s | %s | %s | %s | %s |" % (cid, desc, cell("now"), cell("N2b"), cell("N2w"))
    return res, line, disagree


if __name__ == "__main__":
    os.makedirs(KIT + "/out", exist_ok=True)
    lines = ["| # | 동작 변경 | 지금(def 전체) 대상 / weak 판정 / 변경 고유 | N2b(승인 당시) | N2w(이 card) |", "|---|---|---|---|---|"]
    tot = {k: 0 for k in ("now", "N2b", "N2w")}
    dis_all = []
    for c in A["CASES"] + EXTRA:
        r, line, dis = run(*c)
        lines.append(line)
        if c in A["CASES"]:
            for k in tot:
                tot[k] += r[k][0]
        dis_all += ["%s %s" % (c[0], d) for d in dis]
        print(line, flush=True)
    lines.append("합계 대상(21건): " + ", ".join("%s=%d" % kv for kv in tot.items()))
    lines.append("기존 분류기(v3_scope_widen)와 변이별 불일치: %d" % len(dis_all))
    lines += ["  " + d for d in dis_all]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[-2 - len(dis_all):]))
