"""순서 3 판별력·red 원인·@bindhash 독립 대조 (auditor, 20260930-v3-exempt-binding).
사용: python -B disc.py <v.json> <base 게이트 디렉터리> <T 하네스 lib 디렉터리> <작업 디렉터리> <출력 json>
각 단계마다 (1) rt.py 둘째 단계 결과(T 하네스 _vrepo_contents)의 승인 기록 원소 해시와 auditor 독립 계산 묶기 해시 대조,
(2) 'with' = 그 단계 그대로(승인 기록 포함, 자리표시자 치환본) 합성 저장소에서 base 도구 실행(red 원인),
(3) 'without' = 승인 기록을 뺀 같은 저장소에서 base 도구 실행 -> survivors == [X] 인지(판별력),
(4) (e) 전제: base 도구 def_hash(Dk) == def_hash(head rt_scale), 묶기 해시 다름, Dk != D0.
합성 저장소는 rt.py와 독립으로 git으로 직접 만든다(base 커밋 -> head 커밋, 승인 기록은 v.json이 둔 쪽 사전에)."""
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

vjson, gate, tlib, work, outp = sys.argv[1:6]
PY = sys.executable
X = "rt_engine:rt_scale:stmt_delete:body[1]"


def my_bind(src, qualname):
    """계약 머리 정의를 스택으로 따로 구현(rt.py 코드와 무관): FunctionDef/AsyncFunctionDef만, 클래스·def 이름만 qualname에 든다."""
    tree = ast.parse(src)
    hits = []
    stack = [(tree, "")]
    while stack:
        node, pre = stack.pop()
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = ch.name if not pre else pre + "." + ch.name
                if q == qualname and not isinstance(ch, ast.ClassDef):
                    hits.append(ch)
                stack.append((ch, q))
            else:
                stack.append((ch, pre))
    assert len(hits) == 1, (qualname, len(hits))
    d = ast.dump(hits[0], annotate_fields=True, include_attributes=False, indent=None, show_empty=False)
    return hashlib.sha256(d.encode("utf-8")).hexdigest()


def git(cwd, *a):
    r = subprocess.run(["git", "-C", cwd, *a], capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace"))
    return r.stdout.decode("utf-8").strip()


def mkrepo(path, base, head):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    git(path, "init", "-q", "-b", "master")
    for k, v in (("user.name", "audit"), ("user.email", "audit@example.invalid"), ("core.autocrlf", "false"),
                 ("commit.gpgsign", "false"), ("core.hooksPath", path + "/.nohooks")):
        git(path, "config", k, v)
    def put(files):
        for p, data in files.items():
            fp = os.path.join(path, p)
            if data is None:
                git(path, "rm", "-q", p)
                continue
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "wb") as f:
                f.write(data)
    put(base)
    git(path, "add", "-A")
    git(path, "commit", "-q", "--allow-empty", "-m", "base")
    b = git(path, "rev-parse", "HEAD")
    put(head)
    git(path, "add", "-A")
    git(path, "commit", "-q", "--allow-empty", "-m", "head")
    return b, git(path, "rev-parse", "HEAD")


def run_tool(path, b, h, tag):
    out = os.path.join(work, tag + ".jsonl")
    if os.path.exists(out):
        os.remove(out)
    cmd = [PY, os.path.join(gate, "mutate_changed.py"), "--root", path, "--base", b, "--head", h,
           "--pytest-ini", os.path.join(gate, "pytest_gate.ini"), "--out", out]
    r = subprocess.run(cmd, capture_output=True)
    stdout = r.stdout.decode("utf-8", "replace")
    first = next((ln for ln in stdout.splitlines() if ln.strip().startswith("{")), None)
    obj = json.loads(first) if first else None
    recs = [json.loads(l) for l in open(out, encoding="utf-8")] if os.path.exists(out) else []
    return {"exit": r.returncode, "stdout": stdout.strip(), "stderr_tail": r.stderr.decode("utf-8", "replace")[-400:],
            "survivors": obj and obj.get("survivors"), "mutants": obj and obj.get("mutants"),
            "killed": obj and obj.get("killed"), "keys": obj and list(obj),
            "out_records": [(x.get("id"), x.get("result")) for x in recs]}


sys.path.insert(0, tlib)
os.environ.setdefault("WORK", work)
import rt  # T 하네스 (피검 도구 import 없음 -- grep 확인)
sys.path.insert(0, gate)
import mutate_changed as mc  # base 판 (전제 측정용 def_hash만)

spec = json.load(open(vjson, encoding="utf-8"))
res = {"X": X, "steps": {}}
for case in spec["cases"]:
    step = case["step"]
    contents = rt._vrepo_contents(None, case)  # 모두 {"text"} 명세라 S 불필요
    raw = {s: {p: v["text"].encode("utf-8") for p, v in case.get(s, {}).items()} for s in ("base", "head")}
    st = {"kind": case["kind"]}
    # (1) 자리표시자 독립 대조
    checks = []
    for s in ("base", "head"):
        for p, data in raw[s].items():
            for m in re.finditer(r"@bindhash\(([^()]*)\)", data.decode("utf-8")):
                side, _, rest = m.group(1).partition(":")
                rp, _, q = rest.rpartition(":")
                mine = my_bind(raw[side][rp].decode("utf-8"), q)
                tline = [l for l in contents[s][p].decode("utf-8").splitlines() if l.startswith("target: ")][0]
                checks.append({"in": f"{s}:{p}", "ref": m.group(1), "auditor": mine,
                               "rt_target_line": tline, "match": tline == "target: " + X + "@" + mine})
    st["bindhash_checks"] = checks
    tl = [l for s in ("base", "head") for p, d in contents[s].items() if p.startswith(".ai/approvals/")
          for l in d.decode("utf-8").splitlines() if l.startswith("target: ")]
    st["target_lines"] = tl
    st["no_placeholder_bytes_equal"] = all(contents[s][p] == raw[s][p] for s in raw for p in raw[s]
                                           if b"@bindhash(" not in raw[s][p])
    # (2) with
    b, h = mkrepo(os.path.join(work, step + "-with"), contents["base"], contents["head"])
    st["with"] = run_tool(os.path.join(work, step + "-with"), b, h, step + "-with")
    # (3) without approvals
    nb = {p: d for p, d in contents["base"].items() if not p.startswith(".ai/approvals/")}
    nh = {p: d for p, d in contents["head"].items() if not p.startswith(".ai/approvals/")}
    b, h = mkrepo(os.path.join(work, step + "-without"), nb, nh)
    w = run_tool(os.path.join(work, step + "-without"), b, h, step + "-without")
    st["without"] = w
    st["X_sole_survivor"] = w["survivors"] == [X]
    # (4) (e) 전제
    if "notes/attempt_k.py" in raw["head"]:
        dk = raw["head"]["notes/attempt_k.py"].decode("utf-8")
        hd = raw["head"]["skills/analog-gmid-design/assets/rt_engine.py"].decode("utf-8")
        d0 = raw["base"]["skills/analog-gmid-design/assets/rt_engine.py"].decode("utf-8")
        def fn(src):
            return [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "rt_scale"][0]
        st["e_premise"] = {"def_hash_Dk_eq_head": mc.def_hash(fn(dk)) == mc.def_hash(fn(hd)),
                           "bind_Dk_ne_head": my_bind(dk, "rt_scale") != my_bind(hd, "rt_scale"),
                           "def_hash_Dk_ne_D0": mc.def_hash(fn(dk)) != mc.def_hash(fn(d0)),
                           "Dk_body1": ast.unparse(fn(dk).body[1]), "head_body1": ast.unparse(fn(hd).body[1])}
    res["steps"][step] = st
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
print(json.dumps({k: {"with_exit": v["with"]["exit"], "without_surv": v["without"]["survivors"],
                      "sole": v["X_sole_survivor"], "hash_ok": all(c["match"] for c in v["bindhash_checks"])}
                  for k, v in res["steps"].items()}, ensure_ascii=False, indent=1))
