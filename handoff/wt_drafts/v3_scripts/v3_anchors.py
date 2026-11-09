"""승인 기록·def 해시 앵커 재측정(검토 S2·S11·M1). 저장소는 git show/ls-tree로만 읽는다.
결과: C:/g60/out/v3_anchors.txt"""
import ast, hashlib, re, subprocess, sys

R = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
sys.path.insert(0, R + "/tools/gates")
import mutate_changed as mc   # noqa: E402
import reachability as rch     # noqa: E402

SD = "skills/analog-gmid-design/assets/stick_diagram.py"
OUT = open("C:/g60/out/v3_anchors.txt", "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")


def git(*a):
    return subprocess.run(["git", "-C", R] + list(a), capture_output=True, check=True).stdout.decode("utf-8")


def bind_hash(fn):
    return hashlib.sha256(ast.dump(fn, annotate_fields=True, include_attributes=False, indent=None,
                                   show_empty=False).encode("utf-8")).hexdigest()


# M1: HEAD decision 기록 수와 _approved_ids 원소
names = [l for l in git("ls-tree", "--name-only", "7535799", ".ai/approvals/").splitlines() if l.endswith(".md")]
dec = []
for n in names:
    if n.split("/")[-1].startswith("_"):
        continue
    t = git("show", "7535799:" + n)
    if t.startswith("---\n") and "\ntarget_kind: decision\n" in t:
        dec.append(n.split("/")[-1][:-3])
log("decision 기록(7535799):", len(dec), dec)
ids = rch._approved_ids(R, "7535799")
log("_approved_ids(7535799):", len(ids))
v3like = sorted(i for i in ids if re.match(r"^[\w.]+:[\w.]+:(cmp_flip|arith|const\+|const-|stmt_delete|early_return|except_body_delete):", i))
log("V3 모양 원소:", len(v3like))

# 해시 앵커: ① def_hash(docstring 제외)와 묶기 해시(docstring 포함)
revs = ["58e954c", "6fe9cff", "070cf69", "b29be01", "cd64170", "7535799", "b7765b0"]
for q in ("load_topology", "save_instance_json"):
    for r in revs:
        try:
            src = git("show", "%s:%s" % (r, SD))
        except subprocess.CalledProcessError:
            log(q, r, "no-file"); continue
        d = dict(rch.iter_defs(ast.parse(src)))
        if q not in d:
            log(q, r, "no-def"); continue
        log("%-20s %-8s def_hash %s  bind %s" % (q, r, mc.def_hash(d[q])[:16], bind_hash(d[q])[:16]))

# DF-36(070cf69 -> b29be01): save_instance_json 면제 id 4개가 head에서 가리키는 문장
src_b = git("show", "070cf69:" + SD)
src_h = git("show", "b29be01:" + SD)
fb = dict(rch.iter_defs(ast.parse(src_b)))["save_instance_json"]
fh = dict(rch.iter_defs(ast.parse(src_h)))["save_instance_json"]
log("DF-36 save_instance_json def_hash base %s head %s changed=%s" % (mc.def_hash(fb)[:16], mc.def_hash(fh)[:16], mc.def_hash(fb) != mc.def_hash(fh)))
for i in v3like:
    if ":save_instance_json:" not in i:
        continue
    op, p = i.split(":")[2], i.split(":", 3)[3]
    node_p = re.sub(r"\.ops\[\d+\]$", "", p)
    for lab, fn in (("base", fb), ("head", fh)):
        try:
            nd = mc._get(fn, node_p)
            log("   %s | %s | %s" % (i, lab, ast.unparse(nd).split("\n")[0][:90]))
        except Exception as e:
            log("   %s | %s | (없음 %s)" % (i, lab, e))
OUT.close()
