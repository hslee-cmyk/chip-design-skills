"""20260930-v3-changed-stmt-scope 순서 7 probe p1~p7·p9 (auditor). 기대값은 spec card 계약 문장을 구성에 손으로 적용해 이 파일에 적었다
(피검 도구 출력에서 만들지 않는다). 교차 확인으로 순서 3 auditor 분류기(disc35.py classify -- 계약 1 auditor 구현)도 같은 입력에 돌린다.
사용: python -B probes35.py <병합본 mutate_changed.py> <base 판 게이트 디렉터리> <disc35.py> <작업 디렉터리> <출력 json>
"""
import ast
import copy
import difflib
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys

MT, BG, DISC, WORK, OUTP = sys.argv[1:6]
BT = os.path.join(BG, "mutate_changed.py")
INI = os.path.join(BG, "pytest_gate.ini")
PY = sys.executable
A = "skills/analog-gmid-design/assets"
MOD = A + "/m.py"
RES = {}
NG = []


def save():
    RES["NG"] = NG
    with open(OUTP, "w", encoding="utf-8") as f:
        json.dump(RES, f, ensure_ascii=False, indent=1)


def check(name, cond, detail=None):
    if not cond:
        NG.append({"probe": name, "detail": detail})
    return bool(cond)


# ---- 순서 3 auditor 분류기(disc35.py의 계약 1 부분만 -- argv 줄 제거, '합성 저장소' 절 앞까지)
_src = open(DISC, encoding="utf-8").read()
_src = _src.split("# ---------------------------------------------------------------- 합성 저장소")[0]
_src = _src.replace("vjson, gate, work, outp = sys.argv[1:5]", "")
DC = {}
exec(compile(_src, DISC, "exec"), DC)


def load(path, name):
    sys.path.insert(0, os.path.dirname(path))
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    sys.path.pop(0)
    return m


MM = load(MT, "mc_merged")
MB = load(BT, "mc_base")


def my_bind(fn):
    # 묶기 card 계약 머리 정의(auditor 구현)
    return hashlib.sha256(ast.dump(fn, annotate_fields=True, include_attributes=False, indent=None,
                                   show_empty=False).encode("utf-8")).hexdigest()


def defs(src):
    out = {}

    def rec(nodes, pre):
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[pre + n.name] = n
                rec(n.body, pre + n.name + ".")
            elif isinstance(n, ast.ClassDef):
                rec(n.body, pre + n.name + ".")
    rec(ast.parse(src).body, "")
    return out


def git(cwd, *a):
    r = subprocess.run(["git", "-C", cwd, *a], capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace"))
    return r.stdout.decode("utf-8").strip()


def mkrepo(name, base, head):
    path = os.path.join(WORK, name)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    git(path, "init", "-q", "-b", "master")
    for k, v in (("user.name", "audit"), ("user.email", "audit@example.invalid"), ("core.autocrlf", "false"),
                 ("commit.gpgsign", "false"), ("core.hooksPath", path + "/.nohooks")):
        git(path, "config", k, v)
    ids = []
    for files, msg in ((base, "base"), (head, "head")):
        for p, data in files.items():
            fp = os.path.join(path, p)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "w", encoding="utf-8", newline="\n") as f:
                f.write(data)
        git(path, "add", "-A")
        git(path, "commit", "-q", "--allow-empty", "-m", msg)
        ids.append(git(path, "rev-parse", "HEAD"))
    return path, ids[0], ids[1]


def run(tool, repo, b, h, tag):
    out = os.path.join(WORK, tag + ".jsonl")
    if os.path.exists(out):
        os.remove(out)
    r = subprocess.run([PY, tool, "--root", repo, "--base", b, "--head", h, "--pytest-ini", INI, "--out", out],
                       capture_output=True)
    lines = [l for l in r.stdout.decode("utf-8", "replace").splitlines() if l.strip()]
    recs = [json.loads(l) for l in open(out, encoding="utf-8")] if os.path.exists(out) else []
    raw = open(out, "rb").read() if os.path.exists(out) else b""
    return {"exit": r.returncode, "obj": json.loads(lines[-1]) if lines else None, "stdout_lines": len(lines),
            "stdout": lines[-1] if lines else None, "recs": recs, "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "stderr_tail": r.stderr.decode("utf-8", "replace")[-400:]}


def tgt_of(recs, q):
    pre = "m:%s:" % q
    return [x["id"][len(pre):] for x in recs if x["id"].startswith(pre) and x["result"] != "not_targeted"]


def nt_of(recs, q):
    pre = "m:%s:" % q
    return [x["id"][len(pre):] for x in recs if x["id"].startswith(pre) and x["result"] == "not_targeted"]


def disc_targets(bsrc, hsrc, q, variant=frozenset()):
    bf, hf = defs(bsrc)[q], defs(hsrc)[q]
    mids = [("%s:%s" % (op, p), op, p) for op, p, _ in MM.mutants(hf, hsrc)]
    t = DC["classify"](bf, hf, mids, frozenset(variant))
    return sorted(t)


HDR = '"""m."""\nimport functools\n\nLOG = []\n\n\n'

# ================================================================== p1·p2(출력 모양·--out 순서)
P1_BASE = HDR + '''def rt_a(x):
    LOG.append(x - 1)
    y = x + 1
    LOG.append(y * 2)
    z = 3
    return y


def rt_h(x, strict=False):
    if strict:
        return -x
    return x + 1
'''
P1_HEAD = HDR + '''def rt_a(x):
    LOG.append(x - 1)
    y = x + 2
    LOG.append(y * 2)
    return y


def rt_h(x, strict=True):
    if strict:
        return -x
    return x + 1


def rt_new(v):
    return v - 1
'''
N_SRC = '"""n."""\n\n\ndef rt_n(a):\n    return a * 2 + 1\n'

# 손 적용(계약 1): rt_a -- base [S0 LOG.append(x-1), y=x+1, LOG.append(y*2), z=3, return y], head [S0, y=x+2, LOG.append(y*2), return y]
#   difflib: equal[0], replace a[1]->b[1](단순문 -> 새 문장 body[1]), equal a[2]->b[2], delete a[3](z=3, 삭제 지점 j=3), equal
#   T1 body[1] 4, T6 나(y를 읽는 뒤 문장) body[2] 4·body[3] 1, T6 가 body[3](중복), T5 1 => 대상 10. S0(body[0], 앞 문장) 대상 밖 4.
#   지운 문장 2 = replace 구간의 짝 없는 base 원소 `y = x + 1`(계약 1: 짝이 없는 base 원소는 지운 문장, 삭제 지점 j2=2) + delete `z = 3`.
# rt_h -- 머리만(기본값 False->True, bool이라 상수 변이 없음). 바뀐 매개변수 strict -> `if strict:`의 몫(stmt_delete body[0]) + T5 => 2,
#   대상 밖: if 본문 return -x의 stmt_delete, body[1]의 stmt_delete·arith·const+/- => 5.
# rt_new(새 def) 전체 5, rt_n(새 파일) 전체 = stmt_delete·arith(Add)·arith(Mult)·const+/-(2)·const+/-(1)·early_return = 8.
P2_EXPECT_RT_A = [  # (id 꼬리, result 종류) -- 도구가 변이를 만드는 순서(계약 5): def 노드의 body 문장 삭제 -> 문장별 부분 트리 -> early_return
    ("stmt_delete:body[0]", "NT"), ("stmt_delete:body[1]", "T"), ("stmt_delete:body[2]", "T"), ("stmt_delete:body[3]", "T"),
    ("arith:body[0].value.args[0]", "NT"), ("const+:body[0].value.args[0].right", "NT"), ("const-:body[0].value.args[0].right", "NT"),
    ("arith:body[1].value", "T"), ("const+:body[1].value.right", "T"), ("const-:body[1].value.right", "T"),
    ("arith:body[2].value.args[0]", "T"), ("const+:body[2].value.args[0].right", "T"), ("const-:body[2].value.args[0].right", "T"),
    ("early_return:body[0]", "T")]
RT_H_T = ["stmt_delete:body[0]", "early_return:body[0]"]
RT_H_NT = ["stmt_delete:body[0].body[0]", "stmt_delete:body[1]", "arith:body[1].value", "const+:body[1].value.right",
           "const-:body[1].value.right"]


def p1_p2():
    repo, b, h = mkrepo("p1", {MOD: P1_BASE}, {MOD: P1_HEAD, A + "/n.py": N_SRC})
    r = run(MT, repo, b, h, "p1")
    o = r["obj"]
    keys = list(o.keys())
    want_keys = ["tool", "verdict", "targets", "mutants", "killed", "survivors", "survivor_bindings", "exempt_ignored",
                 "not_targeted", "targets_by_def"]
    tbd = o.get("targets_by_def", {})
    want_tbd = {A + "/m.py::rt_a": {"targeted": 10, "not_targeted": 4, "deleted_statements": 2, "def_header_changed": False},
                A + "/m.py::rt_h": {"targeted": 2, "not_targeted": 5, "deleted_statements": 0, "def_header_changed": True},
                A + "/m.py::rt_new": {"targeted": 5, "not_targeted": 0, "deleted_statements": 0, "def_header_changed": False},
                A + "/n.py::rt_n": {"targeted": 8, "not_targeted": 0, "deleted_statements": 0, "def_header_changed": False}}
    res = {"exit": r["exit"], "stdout_lines": r["stdout_lines"], "keys": keys, "targets": o["targets"],
           "mutants": o["mutants"], "not_targeted": o["not_targeted"], "targets_by_def": tbd,
           "tbd_key_order": list(tbd.keys()), "tbd_field_orders": [list(v.keys()) for v in tbd.values()],
           "out_lines": len(r["recs"]), "out_sha256": r["raw_sha256"]}
    check("p1.keys", keys == want_keys, keys)
    check("p1.targets", o["targets"] == [A + "/m.py", A + "/n.py"], o["targets"])
    check("p1.mutants=대상 수", o["mutants"] == 25 and o["mutants"] == sum(1 for x in r["recs"] if x["result"] != "not_targeted"), o["mutants"])
    check("p1.not_targeted", o["not_targeted"] == 9 and o["not_targeted"] == sum(1 for x in r["recs"] if x["result"] == "not_targeted"))
    check("p1.tbd", tbd == want_tbd and list(tbd.keys()) == list(want_tbd.keys()), tbd)
    check("p1.tbd_fields", all(list(v.keys()) == ["targeted", "not_targeted", "deleted_statements", "def_header_changed"] for v in tbd.values()))
    check("p1.rt_h", sorted(tgt_of(r["recs"], "rt_h")) == sorted(RT_H_T) and sorted(nt_of(r["recs"], "rt_h")) == sorted(RT_H_NT),
          [tgt_of(r["recs"], "rt_h"), nt_of(r["recs"], "rt_h")])
    check("p1.nt_record_keys", all(list(x.keys()) == ["id", "result"] for x in r["recs"] if x["result"] == "not_targeted"))
    check("p1.stdout_one_line", r["stdout_lines"] == 1)
    # p2: rt_a 레코드 순서(생성 순서, 대상·대상 밖이 섞임)
    got = [(x["id"][len("m:rt_a:"):], "NT" if x["result"] == "not_targeted" else "T") for x in r["recs"] if x["id"].startswith("m:rt_a:")]
    p2 = {"input": "rt_a: base [LOG.append(x - 1), y = x + 1, LOG.append(y * 2), z = 3, return y] -> head [LOG.append(x - 1), y = x + 2, LOG.append(y * 2), return y]",
          "expected_order": ["%s/%s" % e for e in P2_EXPECT_RT_A], "observed_order": ["%s/%s" % g for g in got],
          "match": got == P2_EXPECT_RT_A,
          "all_records_def_order": [x["id"].split(":")[1] for x in r["recs"]]}
    # 전체 --out이 def 처리 순서대로 이어지는가(rt_a 14 -> rt_h 7 -> rt_new 5 -> rt_n 8)
    seq = []
    for x in r["recs"]:
        d = x["id"].split(":")[1]
        if not seq or seq[-1] != d:
            seq.append(d)
    p2["def_runs"] = seq
    check("p2.order", got == P2_EXPECT_RT_A, got)
    check("p2.def_runs", seq == ["rt_a", "rt_h", "rt_new", "rt_n"], seq)
    # 교차: auditor 분류기
    res["disc_rt_a"] = disc_targets(P1_BASE, P1_HEAD, "rt_a")
    res["disc_rt_h"] = disc_targets(P1_BASE, P1_HEAD, "rt_h")
    check("p1.disc_rt_a", sorted(tgt_of(r["recs"], "rt_a")) == res["disc_rt_a"])
    check("p1.disc_rt_h", sorted(tgt_of(r["recs"], "rt_h")) == res["disc_rt_h"])
    RES["p1"] = res
    RES["p2"] = p2


# ================================================================== p3(면제 x 대상 밖, 계약 4)
def p3():
    hf = defs(P1_HEAD)["rt_a"]
    hh = my_bind(hf)
    X_NT_B = "m:rt_a:stmt_delete:body[0]"            # 대상 밖, 해시 맞음
    X_NT_U = "m:rt_a:arith:body[0].value.args[0]"    # 대상 밖, 해시 없음
    X_T_B = "m:rt_a:stmt_delete:body[1]"             # 대상, 해시 맞음 -> exempt
    X_T_U = "m:rt_a:arith:body[1].value"             # 대상, 해시 없음 -> exempt_ignored unbound
    X_T_W = "m:rt_a:const+:body[1].value.right"      # 대상, 해시 다름 -> exempt_ignored hash_mismatch
    wrong = "0" * 64
    tgt = ", ".join([X_NT_B + "@" + hh, X_NT_U, X_T_B + "@" + hh, X_T_U, X_T_W + "@" + wrong])
    rec = "---\nid: p3\ndate: 2026-10-02\ntarget_kind: decision\ntarget: %s\nscope: auditor probe\n---\n\n## 사용자 원문\n\n> probe\n" % tgt
    repo, b, h = mkrepo("p3", {MOD: P1_BASE}, {MOD: P1_HEAD, ".ai/approvals/p3.md": rec})
    r = run(MT, repo, b, h, "p3")
    o = r["obj"]
    byid = {x["id"]: x for x in r["recs"]}
    want_ign = [{"id": X_T_U, "reason": "unbound"},
                {"id": X_T_W, "reason": "hash_mismatch", "approved_hash": wrong, "head_hash": hh}]
    res = {"exit": r["exit"], "head_hash_auditor": hh, "records": {k: byid.get(k) for k in (X_NT_B, X_NT_U, X_T_B, X_T_U, X_T_W)},
           "exempt_ignored": o["exempt_ignored"], "mutants": o["mutants"], "not_targeted": o["not_targeted"]}
    check("p3.nt_bound", byid[X_NT_B] == {"id": X_NT_B, "result": "not_targeted"}, byid[X_NT_B])
    check("p3.nt_unbound", byid[X_NT_U] == {"id": X_NT_U, "result": "not_targeted"}, byid[X_NT_U])
    check("p3.t_bound_exempt", byid[X_T_B] == {"id": X_T_B, "result": "exempt", "bind_hash": hh}, byid[X_T_B])
    check("p3.exempt_ignored", o["exempt_ignored"] == want_ign, o["exempt_ignored"])
    check("p3.no_nt_in_ignored", not any(e["id"] in (X_NT_B, X_NT_U) for e in o["exempt_ignored"]))
    # p3 저장소 head는 P1_HEAD(rt_a 10/4 + rt_h 2/5 + rt_new 5/0) -> 대상 17(exempt 1 포함), 대상 밖 9
    check("p3.mutants", o["mutants"] == 17 and o["not_targeted"] == 9, (o["mutants"], o["not_targeted"]))
    RES["p3"] = res


# ================================================================== p4(머리 변경, 계약 1 T3)·p5(맞춤 경계)
P45_BASE = HDR + '''def p4a(a, k=1):
    if a > 0:
        y = a + k
    else:
        y = a - 1
    LOG.append(y)
    return y * 3


def p4b(a, b):
    c = a + 1
    d = b * 2
    return c - d


def p4c(a, *, k=1):
    LOG.append(rest)
    y = a + k
    return y - 1


def p4d(a, /, b):
    if b > 1:
        LOG.append(a)
    return a + 2


def p4e(a, *, k=1):
    y = a + k
    return y - 1


def p5a(x):
    print(x + 1)
    y = x * 2
    print(x + 1)
    return y


def p5b(d, k):
    try:
        v = d[k] + 1
    except ValueError:
        v = 0
    return v * 2


def p5c(cmd, x):
    match cmd:
        case "a":
            y = x + 1
        case _:
            y = x - 1
    return y * 2


def p5d(x):
    def inner(v, s=7):
        w = v + 1
        return w
    LOG.append(x * 5)
    return inner(x)


def p5e(x):
    return x + 1
'''
P45_HEAD = (P45_BASE
            .replace("def p4a(a, k=1):", "def p4a(a, k=2):")
            .replace("def p4b(a, b):", "def p4b(b, a):")
            .replace("def p4c(a, *, k=1):", "def p4c(a, *rest, k=1):")
            .replace("def p4d(a, /, b):", "def p4d(a, z, /, b):")
            .replace("def p4e(a, *, k=1):", "def p4e(a, z=0, *, k=1):")
            .replace("def p5a(x):\n    print(x + 1)\n", "def p5a(x):\n    print(x + 1)\n    print(x + 1)\n")
            .replace("except ValueError:", "except KeyError:")
            .replace("            y = x + 1\n        case _:", "            y = x + 3\n        case _:")
            .replace("        w = v + 1\n", "        w = v + 2\n")
            .replace("def p5e(x):\n    return x + 1\n", 'def p5e(x):\n    """doc 더함."""\n    return x + 1\n'))

# 손 적용(계약 1) 기대 대상(대상 밖은 나머지 전부)
P45_T = {
    # 기본값만 변경: 자기 필드(기본값 2의 const+/-) + k를 읽는 문장(다른 블록 if 본문 `y = a + k`) 몫 + T5. if 머리·else·뒤 문장은 대상 밖
    "p4a": ["const+:args.defaults[0]", "const-:args.defaults[0]", "stmt_delete:body[0].body[0]", "arith:body[0].body[0].value",
            "early_return:body[0]"],
    # 순서만 바꿈: a·b 둘 다 위치가 바뀜 -> a·b를 읽는 body[0]·body[1] 몫 + T5. `return c - d`는 대상 밖
    "p4b": ["stmt_delete:body[0]", "stmt_delete:body[1]", "arith:body[0].value", "const+:body[0].value.right", "const-:body[0].value.right",
            "arith:body[1].value", "const+:body[1].value.right", "const-:body[1].value.right", "early_return:body[0]"],
    # *rest 추가(`*` 표시 -> `*rest`): 바뀐 매개변수 = rest(이름 대칭차). k(키워드 전용 순번 0)는 그대로 -> `y = a + k` 대상 밖.
    #   자기 필드 kw_defaults[0] const+/- + rest를 읽는 body[0] 몫 + T5
    "p4c": ["stmt_delete:body[0]", "const+:args.kw_defaults[0]", "const-:args.kw_defaults[0]", "early_return:body[0]"],
    # 위치 전용 경계: z 추가로 b의 위치 인자 순번 1 -> 2(바뀐 매개변수 b, z). b를 읽는 `if b > 1:` 몫 4 + T5. if 본문·return은 대상 밖
    "p4d": ["stmt_delete:body[0]", "cmp_flip:body[0].test.ops[0]", "const+:body[0].test.comparators[0]", "const-:body[0].test.comparators[0]",
            "early_return:body[0]"],
    # 키워드 전용 앞 일반 매개변수 추가: 바뀐 매개변수 = z만(k 순번 0 그대로) -> 자기 필드(defaults[0] z=0, kw_defaults[0] k=1) const+/- 4 + T5
    "p4e": ["const+:args.defaults[0]", "const-:args.defaults[0]", "const+:args.kw_defaults[0]", "const-:args.kw_defaults[0]", "early_return:body[0]"],
    # 같은 지문 반복: base [A, B, A, R] -> head [A, A, B, A, R]. 규범 알고리즘은 equal a[0:4]->b[1:5], insert b[0] -> 새 문장 = head body[0]
    #   (print(x + 1)은 바꾸는 이름 없음 -> T6 나 없음). T1 body[0] 4 + T5
    "p5a": ["stmt_delete:body[0]", "arith:body[0].value.args[0]", "const+:body[0].value.args[0].right", "const-:body[0].value.args[0].right",
            "early_return:body[0]"],
    # except 머리 변경: 처리기 = 머리 변경 복합문(T2) -> 몫 = except_body_delete. 조상 try(T4) -> stmt_delete body[0]. + T5
    "p5b": ["stmt_delete:body[0]", "except_body_delete:body[0].handlers[0]", "early_return:body[0]"],
    # match/case: case "a" 본문 `y = x + 3` 새 문장(T1 4), 조상 match·case(T4 -- match의 stmt_delete), + T5
    "p5c": ["stmt_delete:body[0]", "stmt_delete:body[0].cases[0].body[0]", "arith:body[0].cases[0].body[0].value",
            "const+:body[0].cases[0].body[0].value.right", "const-:body[0].cases[0].body[0].value.right", "early_return:body[0]"],
    # 중첩 def 안 변경(바깥 p5d): 새 문장 body[0].body[0] 4, T6 나 `return w` 1, 조상 중첩 def inner의 자기 필드(s=7 const+/-) 2, T5 1
    "p5d": ["stmt_delete:body[0].body[0]", "stmt_delete:body[0].body[1]", "const+:body[0].args.defaults[0]", "const-:body[0].args.defaults[0]",
            "arith:body[0].body[0].value", "const+:body[0].body[0].value.right", "const-:body[0].body[0].value.right", "early_return:body[0]"],
    # 중첩 def 자신(p5d.inner): 머리 불변 -> 자기 필드(s=7)는 대상 밖. 새 문장 4 + T6 나 1 + T5 1
    "p5d.inner": ["stmt_delete:body[0]", "stmt_delete:body[1]", "arith:body[0].value", "const+:body[0].value.right", "const-:body[0].value.right",
                  "early_return:body[0]"],
}


def p4_p5():
    repo, b, h = mkrepo("p45", {MOD: P45_BASE}, {MOD: P45_HEAD})
    r = run(MT, repo, b, h, "p45")
    o = r["obj"]
    tbd = o["targets_by_def"]
    res = {"exit": r["exit"], "targets_by_def": tbd, "per_def": {}}
    for q, want in P45_T.items():
        got = tgt_of(r["recs"], q)
        allm = ["%s:%s" % (op, p) for op, p, _ in MM.mutants(defs(P45_HEAD)[q], P45_HEAD)]
        nt = nt_of(r["recs"], q)
        dsc = disc_targets(P45_BASE, P45_HEAD, q)
        ok = sorted(got) == sorted(want) and sorted(nt) == sorted(set(allm) - set(want)) and len(got) + len(nt) == len(allm)
        res["per_def"][q] = {"expected": sorted(want), "tool_targeted": sorted(got), "tool_not_targeted_n": len(nt),
                             "all": len(allm), "match": ok, "disc_match": dsc == sorted(want)}
        check("p45." + q, ok, {"got": got, "want": want})
        check("p45.disc." + q, dsc == sorted(want), dsc)
    # p5a 규범 알고리즘 확인(auditor가 difflib를 직접 돌림)
    bf, hf = defs(P45_BASE)["p5a"], defs(P45_HEAD)["p5a"]
    ops = difflib.SequenceMatcher(None, [ast.dump(x, include_attributes=False) for x in bf.body],
                                  [ast.dump(x, include_attributes=False) for x in hf.body], autojunk=False).get_opcodes()
    res["p5a_opcodes"] = ops
    check("p5a.opcodes", ops == [("insert", 0, 0, 0, 1), ("equal", 0, 4, 1, 5)], ops)
    # p5e: docstring만 더한 def -> 대상 def가 아님(변이 0, targets_by_def에 없음)
    res["p5e_in_tbd"] = (A + "/m.py::p5e") in tbd
    res["p5e_records"] = sum(1 for x in r["recs"] if x["id"].startswith("m:p5e:"))
    check("p5e", not res["p5e_in_tbd"] and res["p5e_records"] == 0)
    # 머리 변경 표시
    hdr = {q: tbd[A + "/m.py::" + q]["def_header_changed"] for q in P45_T}
    res["def_header_changed"] = hdr
    check("p45.hdr", hdr == {"p4a": True, "p4b": True, "p4c": True, "p4d": True, "p4e": True, "p5a": False, "p5b": False,
                             "p5c": False, "p5d": False, "p5d.inner": False}, hdr)
    RES["p4_p5"] = res


# ================================================================== p6(데코레이터 치환, 계약 9)
P6_SRC = '''"""p6."""
import functools


def deco2(n):
    def w(f):
        return f
    return w


@functools.lru_cache(
    maxsize=128,
)
def f(x):
    return x + 1


@deco2(3)
@functools.lru_cache(maxsize=64)
def g(x):
    return x * 2


class K:
    @staticmethod
    @deco2(5)
    def m(x):
        return x - 4
'''


def p6():
    out = {}
    tree0 = ast.parse(P6_SRC)
    dump0 = ast.dump(tree0, include_attributes=False)
    for q in ("f", "g", "K.m"):
        fn = defs(P6_SRC)[q]
        rows = []
        for op, path, mfn in MM.mutants(fn, P6_SRC):
            new = MM._replace_def(P6_SRC, fn, mfn)
            old = MB._replace_def(P6_SRC, fn, mfn)
            t = ast.parse(new)   # 들여쓰기가 깨지면 여기서 SyntaxError
            got_def = defs(new)[q]
            row = {"id": "%s:%s" % (op, path),
                   "differs_from_original": ast.dump(t, include_attributes=False) != dump0,
                   "def_equals_mutant": ast.dump(got_def, include_attributes=False) == ast.dump(mfn, include_attributes=False),
                   "outside_unchanged": all(ast.dump(defs(new)[o], include_attributes=False) == ast.dump(defs(P6_SRC)[o], include_attributes=False)
                                            for o in ("deco2", "f", "g", "K.m") if o != q),
                   "base_noop": ast.dump(ast.parse(old), include_attributes=False) == dump0}
            rows.append(row)
            if path.startswith("decorator_list"):
                check("p6.%s.%s" % (q, row["id"]), row["differs_from_original"] and row["def_equals_mutant"] and row["outside_unchanged"], row)
            else:
                check("p6.%s.%s" % (q, row["id"]), row["def_equals_mutant"] and row["outside_unchanged"], row)
        out[q] = rows
    deco = [r for rows in out.values() for r in rows if r["id"].split(":", 1)[1].startswith("decorator_list")]
    out["summary"] = {"decorator_mutants": len(deco), "merged_all_differ": all(r["differs_from_original"] for r in deco),
                      "base_noop_count": sum(r["base_noop"] for r in deco)}
    check("p6.has_deco_mutants", len(deco) >= 6, len(deco))
    RES["p6"] = out


# ================================================================== p7(무기록·새 def만, 계약 7)
P7_BASE = HDR + "def rt_gain(gm, ro):\n    return gm * ro\n"
P7_HEAD = P7_BASE + "\n\ndef rt_scale(x, k=2):\n    if x > 0:\n        return x * k\n    return 0\n"
P7_TEST = ('import sys\nfrom pathlib import Path\n\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n'
           'from m import rt_scale\n\n\ndef test_rt_scale_p7():\n    assert rt_scale(3) == 6\n    assert rt_scale(-1) == 0\n')


def p7():
    repo, b, h = mkrepo("p7", {MOD: P7_BASE}, {MOD: P7_HEAD, A + "/tests/test_p7.py": P7_TEST})
    rm = run(MT, repo, b, h, "p7m")
    rb = run(BT, repo, b, h, "p7b")
    om, ob = dict(rm["obj"]), dict(rb["obj"])
    nt, tbd = om.pop("not_targeted", None), om.pop("targets_by_def", None)
    allm = len(MM.mutants(defs(P7_HEAD)["rt_scale"], P7_HEAD))
    res = {"merged_exit": rm["exit"], "base_exit": rb["exit"], "merged": rm["stdout"], "base": rb["stdout"],
           "same_without_new_keys": om == ob, "not_targeted": nt, "targets_by_def": tbd,
           "out_same": rm["raw_sha256"] == rb["raw_sha256"], "out_sha256": rm["raw_sha256"], "all_mutants": allm}
    check("p7.same", om == ob and rm["exit"] == rb["exit"], (rm["stdout"], rb["stdout"]))
    check("p7.nt0", nt == 0)
    check("p7.tbd", tbd == {A + "/m.py::rt_scale": {"targeted": allm, "not_targeted": 0, "deleted_statements": 0, "def_header_changed": False}}, tbd)
    check("p7.out", rm["raw_sha256"] == rb["raw_sha256"])
    RES["p7"] = res


# ================================================================== p9(T6 가 단독 판별)
P9_BASE = HDR + "def rt_g(x):\n    LOG.append(x)\n    LOG.append(-x)\n    return str(x)\n"
P9_HEAD = HDR + "def rt_g(x):\n    LOG.append(x)\n    return str(x)\n"
P9_TEST = ('import sys\nfrom pathlib import Path\n\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n'
           'import m\nfrom m import rt_g\n\n\ndef test_rt_g_p9():\n    n = len(m.LOG)\n    rt_g(3)\n    assert m.LOG[n:] == [3]\n')
# 손 적용: base [LOG.append(x), LOG.append(-x), return str(x)] -> head [LOG.append(x), return str(x)]: delete a[1](삭제 지점 j=1).
#   T6 가: head body[1] `return str(x)`의 몫(stmt_delete -- 부분 트리에 다른 변이 없음) = X. T6 나: 지운 문장이 바꾸는 이름 = {LOG}(메서드 호출 수신자)
#   -> 뒤(j 이상) 문장 중 LOG를 읽는 문장 없음(return str(x)는 LOG를 읽지 않는다). body[0]은 앞 문장 -> 대상 밖. T5 early_return.
#   대상 = {X, early_return}, 대상 밖 = {stmt_delete:body[0]}. test는 LOG[n:] == [3]만 봄 -> early_return 죽음(LOG 빔), X 생존(반환값 안 봄)
P9_X = "m:rt_g:stmt_delete:body[1]"


def p9():
    repo, b, h = mkrepo("p9", {MOD: P9_BASE}, {MOD: P9_HEAD, A + "/tests/test_p9.py": P9_TEST})
    r = run(MT, repo, b, h, "p9")
    o = r["obj"]
    full = disc_targets(P9_BASE, P9_HEAD, "rt_g")
    no6a = disc_targets(P9_BASE, P9_HEAD, "rt_g", {"T6a"})
    res = {"exit": r["exit"], "stdout": r["stdout"], "records": r["recs"],
           "auditor_full_targets": full, "auditor_without_T6a_targets": no6a,
           "X_target_full": "stmt_delete:body[1]" in full, "X_target_without_T6a": "stmt_delete:body[1]" in no6a}
    check("p9.exit1", r["exit"] == 1 and o["survivors"] == [P9_X], o)
    check("p9.records", [(x["id"], x["result"]) for x in r["recs"]] ==
          [("m:rt_g:stmt_delete:body[0]", "not_targeted"), (P9_X, "survived"), ("m:rt_g:early_return:body[0]", "killed")],
          [(x["id"], x["result"]) for x in r["recs"]])
    check("p9.disc_full", full == ["early_return:body[0]", "stmt_delete:body[1]"], full)
    check("p9.disc_no6a", "stmt_delete:body[1]" not in no6a, no6a)
    RES["p9"] = res


for fn in (p1_p2, p3, p4_p5, p6, p7, p9):
    try:
        fn()
    except Exception as e:   # probe 실행 오류는 NG로 기록(조용히 넘기지 않음)
        NG.append({"probe": fn.__name__, "error": "%s: %s" % (type(e).__name__, e)})
    save()
print(json.dumps({"NG": NG, "done": [k for k in RES if k != "NG"]}, ensure_ascii=False, indent=1))
