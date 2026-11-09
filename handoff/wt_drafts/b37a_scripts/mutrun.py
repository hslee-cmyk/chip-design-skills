"""B37a N2 대상 변이를 하나씩 모의 head에 넣고, 모의 계약 판정(contracts.py 출력)과 folded_cascode 평가 1회가
head와 달라지는지 본다(관찰이 달라짐 = 계약 test가 죽일 수 있는 근사. 예외·시간 초과도 죽음으로 센다).
도구 함수(mutate_changed.changed_defs·mutants·_replace_def)만 읽기 전용 import. 결과는 케이스마다 append.
사용: python -B mutrun.py <base 사본> <head 사본> <mut 작업 사본> <out.txt>
"""
import ast, json, os, shutil, subprocess, sys, types

BASE, HEAD, MUT, OUT = sys.argv[1:5]
ONLY = None
if len(sys.argv) > 5:   # 선택: 'def op path' 줄 목록 파일 -- 그 변이만 다시 돈다
    ONLY = {tuple(l.split()[:3]) for l in open(sys.argv[5], encoding="utf-8") if l.strip()}
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE + "/tools/gates")
import mutate_changed as mc  # noqa: E402
import reachability as rch  # noqa: E402
fake = types.ModuleType("sim_head"); fake.mc, fake.rch = mc, rch
sys.modules["sim_head"] = fake
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3_scripts")
import v3_scope_classify as V  # noqa: E402

A = "skills/analog-gmid-design/assets/"
FILES = [A + "stick_diagram.py", A + "sizing_recipe.py"]
PY = "C:/Python314/python.exe"
EVAL = r'''
import sys, os, json, hashlib
R = sys.argv[1]
sys.path.insert(0, os.path.join(R, "skills/analog-gmid-design/assets/tests/unit"))
import _library_sized_contexts as L
cfg = L.H.SPECS["folded_cascode"]
sc = L._evaluate_once("folded_cascode", cfg)
if sc.refusal is not None:
    print("REFUSAL", type(sc.refusal).__name__, str(sc.refusal)[:200])
else:
    print("OK", hashlib.sha256(json.dumps({k: float.hex(v) if isinstance(v, float) else repr(v) for k, v in sorted(sc.metrics.items())}).encode()).hexdigest()[:16])
'''


def rd(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8", newline="") as fh:
        return fh.read()


def run(root, tag):
    env = dict(os.environ, PYTHONHASHSEED="0")
    out = os.path.join("C:/g68/out", "mut_%s.json" % tag)
    try:
        r = subprocess.run([PY, "-B", os.path.join(S, "contracts.py"), root, out], capture_output=True, timeout=600, env=env)
        c = open(out, encoding="utf-8").read() if r.returncode == 0 and os.path.exists(out) else "CRASH rc=%d %s" % (r.returncode, r.stderr[-300:])
    except subprocess.TimeoutExpired:
        c = "TIMEOUT"
    try:
        r2 = subprocess.run([PY, "-B", "-c", EVAL, root], capture_output=True, timeout=600, env=env, cwd=root)
        e = (r2.stdout.decode("utf-8", "replace").strip().splitlines() or ["CRASH " + r2.stderr.decode("utf-8", "replace")[-200:]])[-1]
    except subprocess.TimeoutExpired:
        e = "TIMEOUT"
    return c, e


if os.path.exists(MUT):
    shutil.rmtree(MUT)
shutil.copytree(HEAD, MUT)
ref_c, ref_e = run(HEAD, "ref")
fh = open(OUT, "w", encoding="utf-8")
fh.write("ref eval: %s\n" % ref_e); fh.flush()
killed = surv = 0
for rel in FILES:
    bsrc_raw, hsrc_raw = rd(BASE, rel), rd(HEAD, rel)
    crlf = "\r\n" in hsrc_raw
    bsrc, hsrc = bsrc_raw.replace("\r\n", "\n"), hsrc_raw.replace("\r\n", "\n")
    bdefs = dict(rch.iter_defs(ast.parse(bsrc)))
    for q, hfn in mc.changed_defs(bsrc, hsrc):
        allm = {(op, p): f for op, p, f in mc.mutants(hfn, hsrc)}
        if q in bdefs:
            rows, _ = V.classify(bdefs[q], hfn, hsrc)
            sel = [(t["op"], t["path"]) for t in rows if V.DEFS["N2b"](t)]
        else:
            sel = list(allm)
        for op, p in sel:
            if ONLY is not None and (q, op, p) not in ONLY:
                continue
            new = mc._replace_def(hsrc, hfn, allm[(op, p)])
            if crlf:
                new = new.replace("\n", "\r\n")
            with open(os.path.join(MUT, rel), "w", encoding="utf-8", newline="") as w:
                w.write(new)
            c, e = run(MUT, "m")
            k_c, k_e = c != ref_c, e != ref_e
            dead = k_c or k_e
            killed += dead; surv += (not dead)
            fh.write("%s %s::%s %s %s contracts=%s eval=%s\n" % ("KILLED " if dead else "SURVIVE", rel.split("/")[-1], q, op, p,
                                                                   "diff" if k_c else "same", "diff" if k_e else "same"))
            fh.flush()
        with open(os.path.join(MUT, rel), "w", encoding="utf-8", newline="") as w:
            w.write(hsrc_raw)
fh.write("TOTAL killed=%d survived=%d\n" % (killed, surv))
fh.close()
shutil.rmtree(MUT, ignore_errors=True)
