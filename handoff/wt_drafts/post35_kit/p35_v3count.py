"""post-35 재측정 -- V3 대상 수를 **도구 자신**(병합본 mutate_changed.py, 리허설에서는 p35_sim35 모의)으로 잰다.

    python -B p35_v3count.py --tool-dir <tools/gates> --root <복제본> --base <rev> --head <rev> --label <이름>
                             --work <scratch 폴더> --proto-dir <scope_proto.py 폴더> [--def-key <경로::qualname>]
                             [--carry <b26_1_carry.sh>] [--ids <id 목록 json>]

방법(v3scope_kit/probe_selection.py와 같은 원리 -- 재사용): PYTHONPATH 앞에 가짜 `pytest`(sys.exit(0))를 둬 도구 `main`을 실제 경로 그대로
돌린다(판정 아님 -- 선택 집합만 본다). 실행된 변이는 전부 '생존', 인벤토리 없음도 '생존'. pytest를 돌리지 않으므로 '죽임' 수는 재지 않는다.
결과(JSON 한 줄, <work>/v3_<label>.json에도):
  tool_exit, has35(출력에 targets_by_def), mutants(= 대상), not_targeted(출력), out_records, out_not_targeted, targets_by_def(요약),
  proto_targeted(scope_proto N2w 독립 계산 -- 도구가 만든 변이 목록에 적용), sym_diff(도구 대상 id vs proto 대상 id),
  carry_subset(b26_1_carry.sh의 '범위 card 35 계약 5' 단정 블록을 그대로 뽑아 이 출력에 실행 -- ok / 실패 문장),
  ids_check(--ids가 주면 각 id가 targeted / not_targeted / absent 중 무엇인지)
"""
import argparse
import ast
import json
import os
import re
import subprocess
import sys


def main(argv):
    ap = argparse.ArgumentParser()
    for k in ("--tool-dir", "--root", "--base", "--head", "--label", "--work", "--proto-dir"):
        ap.add_argument(k, required=True)
    ap.add_argument("--def-key", default=None)
    ap.add_argument("--carry", default=None)
    ap.add_argument("--ids", default=None)
    ap.add_argument("--survive-re", default=None, help="이 정규식이 --survive-file에 있는 변이만 생존(나머지 실행 변이는 죽음, 기준 실행 = git diff 없음 = 통과)")
    ap.add_argument("--survive-file", default=None)
    ap.add_argument("--carry-full", default=None, help="b26_1_carry.sh -- check 단계 V3 heredoc 전체를 이 출력에 실행")
    ns = ap.parse_args(argv)
    os.makedirs(ns.work, exist_ok=True)
    fdir = "fakepytest_" + ns.label if ns.survive_re else "fakepytest"
    fake = os.path.join(ns.work, fdir, "pytest")
    os.makedirs(fake, exist_ok=True)
    open(os.path.join(fake, "__init__.py"), "w").close()
    with open(os.path.join(fake, "__main__.py"), "w", encoding="utf-8") as fh:
        if ns.survive_re:
            fh.write("import re, subprocess, sys\n"
                     "if subprocess.run(['git', 'diff', '--quiet']).returncode == 0:\n    sys.exit(0)\n"
                     "t = open(%r, encoding='utf-8').read()\nsys.exit(0 if re.search(%r, t) else 1)\n" % (ns.survive_file, ns.survive_re))
        else:
            fh.write("import sys\nsys.exit(0)\n")
    out = os.path.join(ns.work, "v3_%s.out.jsonl" % ns.label)
    if os.path.exists(out):
        os.remove(out)
    env = dict(os.environ, PYTHONPATH=os.path.join(ns.work, fdir))
    tool = os.path.join(ns.tool_dir, "mutate_changed.py")
    r = subprocess.run([sys.executable, "-B", tool, "--root", ns.root, "--base", ns.base, "--head", ns.head,
                        "--pytest-ini", os.path.join(ns.work, "none.ini"), "--out", out], capture_output=True, env=env)
    stdout = r.stdout.decode("utf-8", "replace").strip()
    res = {"label": ns.label, "base": ns.base[:10], "head": ns.head[:10], "tool_exit": r.returncode}
    if r.returncode not in (0, 1):
        res["error"] = "도구 exit %d: %s | %s" % (r.returncode, stdout[-400:], r.stderr.decode("utf-8", "replace")[-400:])
        return finish(ns, res, 2)
    v = json.loads([l for l in stdout.splitlines() if l.strip().startswith("{")][-1])
    recs = [json.loads(l) for l in open(out, encoding="utf-8")] if os.path.exists(out) else []
    tg = [x["id"] for x in recs if x["result"] != "not_targeted"]
    nt = [x["id"] for x in recs if x["result"] == "not_targeted"]
    res.update({"has35": "targets_by_def" in v, "keys": list(v), "mutants": v.get("mutants"), "not_targeted": v.get("not_targeted"),
                "out_records": len(recs), "out_targeted": len(tg), "out_not_targeted": len(nt), "targets": v.get("targets")})
    tb = v.get("targets_by_def")
    if tb is not None:
        res["targets_by_def"] = {k: [d.get("targeted"), d.get("not_targeted")] for k, d in tb.items()}
        res["defs"] = len(tb)
        if ns.def_key:
            res["def_key_targeted"] = tb.get(ns.def_key, {}).get("targeted")
            res["def_keys"] = list(tb)
    # proto 독립 계산(도구 변이 목록에 scope_proto N2w 적용) -- 도구가 만든 id 순서와 대조
    sys.path.insert(0, ns.proto_dir)
    sys.path.insert(0, ns.tool_dir)
    import mutate_changed as mc   # noqa: E402
    import reachability as rch     # noqa: E402
    import scope_proto as SP       # noqa: E402

    def gitb(*a):
        q = subprocess.run(["git", "-C", ns.root] + list(a), capture_output=True)
        return q.returncode, q.stdout
    _, diff = gitb("diff", "--name-only", "--no-renames", "--diff-filter=AM", ns.base, ns.head)
    paths = [p for p in diff.decode("utf-8").splitlines() if p.endswith(".py") and rch._is_source(p)]
    p_all, p_tg = [], []
    for path in paths:
        _, hsrc = gitb("show", "%s:%s" % (ns.head, path))
        hsrc = hsrc.decode("utf-8")
        rc, bsrc = gitb("show", "%s:%s" % (ns.base, path))
        bsrc = bsrc.decode("utf-8") if rc == 0 else None
        bdefs = dict(rch.iter_defs(ast.parse(bsrc))) if bsrc else {}
        mod = rch.module_name(path)
        for q, hfn in mc.changed_defs(bsrc, hsrc):
            ms = mc.mutants(hfn, hsrc)
            sel = SP.select(bdefs[q], hfn, ms, "N2w") if q in bdefs else [True] * len(ms)
            ids = ["%s:%s:%s:%s" % (mod, q, o, p) for o, p, _ in ms]
            p_all += ids
            p_tg += [i for i, s in zip(ids, sel) if s]
    res["proto_all"] = len(p_all)
    res["proto_targeted"] = len(p_tg)
    res["proto_not_targeted"] = len(p_all) - len(p_tg)
    if res["has35"]:
        a, b = set(tg), set(p_tg)
        res["sym_diff"] = len(a ^ b)
        res["sym_diff_ids"] = sorted(a ^ b)[:20]
        res["order_ok"] = [x["id"] for x in recs] == p_all
    if ns.ids:
        want = json.load(open(ns.ids, encoding="utf-8"))
        st = {i: ("targeted" if i in set(tg) else "not_targeted" if i in set(nt) else "absent") for i in want}
        res["ids_check"] = st
        res["ids_targeted"] = sum(1 for s in st.values() if s == "targeted")
        res["ids_total"] = len(want)
    if ns.carry and res["has35"]:
        res["carry_subset"] = carry_subset(ns.carry, v, recs)
    res["survivors"] = v.get("survivors", [])[:5]
    res["n_survivors"] = len(v.get("survivors", []))
    if ns.carry_full:
        res["carry_full"] = carry_full(ns, v, out)
    return finish(ns, res, 0)


def carry_full(ns, v, out):
    """b26_1_carry.sh check 단계의 `local v3; v3=$("$PY" -B - "$WT_A/$AUD/attempt1_v3.json" …) <<'EOF'` heredoc 전체(= b26_1_kit_selftest/out_check_test.sh의 피검)를
    이 실제 도구 출력에 그대로 돌린다. 인자 = (판정 JSON, --out, K1 SD = head 판 stick_diagram.py, V3_RE, SD 경로) -- carry 스크립트와 같은 순서."""
    L = open(ns.carry_full, "rb").read().split(b"\n")
    s = [i for i, l in enumerate(L) if l.startswith(b'  local v3; v3=$("$PY" -B - "$WT_A/$AUD/attempt1_v3.json"')]
    if len(s) != 1:
        return "anchor 없음(heredoc 시작 줄 %d개)" % len(s)
    e = s[0] + 1 + L[s[0] + 1:].index(b"EOF")
    body = b"\n".join(L[s[0] + 1:e]) + b"\n"
    vre = [l for l in L if l.startswith(b"V3_RE='")]
    if len(vre) != 1:
        return "V3_RE 줄 %d개" % len(vre)
    v3_re = vre[0].split(b"'")[1].decode()
    sd = "skills/analog-gmid-design/assets/stick_diagram.py"
    hp = os.path.join(ns.work, "carry_full_%s.py" % ns.label)
    open(hp, "wb").write(body)
    vp = os.path.join(ns.work, "carry_full_%s.v.json" % ns.label)
    json.dump(v, open(vp, "w", encoding="utf-8"), ensure_ascii=False)
    kp = os.path.join(ns.work, "carry_full_%s.K1_SD.py" % ns.label)
    k = subprocess.run(["git", "-C", ns.root, "show", "%s:%s" % (ns.head, sd)], capture_output=True).stdout
    open(kp, "wb").write(k)
    q = subprocess.run([sys.executable, "-B", hp, vp, out, kp, v3_re, sd], capture_output=True)
    msg = (q.stderr.decode("utf-8", "replace").strip().splitlines() or [""])[-1][:300]
    return ("PASS: " + q.stdout.decode("utf-8", "replace").strip()[:120]) if q.returncode == 0 else ("FAIL exit %d: %s" % (q.returncode, msg))


def carry_subset(path, v, recs):
    """b26_1_carry.sh의 '범위 card 35(…) 계약 5' 주석부터 `assert v["killed"]` 줄까지를 그대로 뽑아 실행한다(`== [mid]` 줄만 뺀다 --
    가짜 pytest라 생존이 전부여서 U3 하나 단정은 실제 1차 출력에서만 뜻이 있다)."""
    lines = open(path, encoding="utf-8").read().split("\n")
    a = [i for i, l in enumerate(lines) if l.startswith("# 범위 card 35(")]
    b = [i for i, l in enumerate(lines) if l.startswith('assert v["killed"] == ')]
    if len(a) != 1 or len(b) != 1 or b[0] < a[0]:
        return "anchor 없음(carry 스크립트 구조가 바뀜): %d %d" % (len(a), len(b))
    block = [l for l in lines[a[0]:b[0] + 1] if "== [mid]" not in l]
    try:
        exec(compile("\n".join(block), "b26_1_carry.sh(발췌)", "exec"), {"v": v, "recs": recs})
    except AssertionError as e:
        return "FAIL %s" % (e,)
    return "ok(%d줄)" % len(block)


def finish(ns, res, code):
    with open(os.path.join(ns.work, "v3_%s.json" % ns.label), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
