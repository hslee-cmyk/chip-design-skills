"""G1 시제품 설치(측정 전용): 격리 복제본의 tools/gates/{reachability,mutate_changed,source_lint}.py와 redteam/lib/rt.py를
spec card 20260930-p3-gate-move-aware 계약 0~6·12(관찰)대로 고친다. 역할 산출물이 아니다(작성자 != 검증자 -- test·code 열람 금지).

    python -B install_proto.py <복제본 루트>          # 앵커가 하나라도 없으면 exit 1, 아무것도 쓰지 않는다

* reachability.py 끝에 g1_core.py 본문을 붙이고 main의 new_defs에서 옮긴 def를 뺀다(+ moved·move_rejected).
* mutate_changed.py: _strip_doc·def_hash를 reachability 것으로(계약 8), 대상 선택 앞에서 옮긴 def 제외(계약 4), 출력 defs·moved·move_rejected.
  **앵커 판 = card 35(20260930-v3-changed-stmt-scope) 병합본 a17b8bd**(2026-10-02 재앵커): 범위 정책이 도구 안에 있으므로
  (_Scope·targets_by_def·not_targeted·데코레이터 포함 치환) 옛 G1_SCOPE=1 근사(_drafts/v3scope_kit/scope_proto)는 뺐다 -- G1_SCOPE는 무시된다.
  옮긴 def 제외는 card 35의 targets_by_def 기록·_Scope 생성보다 앞이라 옮긴 def는 not_targeted·targets_by_def에 들지 않는다(계약 4).
  잘못된 구현 변형 G1_VARIANT=scope_from_origin: 같은 경로 base def가 없을 때 base 전체에서 같은 qualname 하나를 찾아 _Scope로 맞춘다(D-20 위반 판별용).
  36e170e·4a286f0(card 35 병합 전) 판에는 설치하지 않는다(exit 1) -- 그 판은 install_proto.py.pre-35.bak.
* source_lint.py: 계약 5(옮긴 def 단위 이전 항목 수 = 원본 맥락, <module> += 옮긴 문장 원본 맥락 항목) + moved·move_rejected.
* rt.py vcase: "observe": "moved" 관찰(계약 12).
"""
import os
import sys

KIT = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1]
G = os.path.join(ROOT, "tools", "gates")


def rd(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return fh.read().replace(chr(13) + chr(10), chr(10))   # core.autocrlf=true 체크아웃은 CRLF -- LF로 맞춰 고치고 LF로 쓴다


def sub(text, old, new, label):
    if text.count(old) != 1:
        raise SystemExit("앵커 %s: %d개(1개여야 한다)" % (label, text.count(old)))
    return text.replace(old, new)


out = {}
# ---------------------------------------------------------------- reachability.py
p = os.path.join(G, "reachability.py")
t = rd(p)
if "G1 시제품" in t:
    print("already installed")
    sys.exit(0)
t = sub(t, """        new_defs = sorted(n for n in nodes if _is_source(n.split("::")[0]) and not n.endswith(("::<module>", "::__main__"))
                          and n not in base_defs)
""", """        _H = SourceIndex({k: v for k, v in head.items() if _is_source(k)})
        _B = SourceIndex({k: v for k, v in base.items() if _is_source(k)})
        moved = moved_defs(_B, _H)
        _hfn = {}
        for _p in _H.paths():
            for _q, _fn in iter_defs(_H.mod(_p).tree):
                _hfn.setdefault("%s::%s" % (_p, _q), _fn)
        new_defs = sorted(n for n in nodes if _is_source(n.split("::")[0]) and not n.endswith(("::<module>", "::__main__"))
                          and n not in base_defs
                          and not (n in _hfn and g1_excluded(moved, n.split("::")[0], n.split("::", 1)[1], _hfn[n])))
""", "rch new_defs")
t = sub(t, """                      "unreached_without_approval": unexempt}, ensure_ascii=False))""",
        """                      "unreached_without_approval": unexempt, "moved": g1_moved_list(moved),
                      "move_rejected": moved["rejected"]}, ensure_ascii=False))""", "rch print")
t = sub(t, """\n\nif __name__ == "__main__":""", "\n\n" + rd(os.path.join(KIT, "g1_core.py")) + """\n\nif __name__ == "__main__":""", "rch main")
out[p] = t

# ---------------------------------------------------------------- mutate_changed.py
p = os.path.join(G, "mutate_changed.py")
t = rd(p)
if "class _Scope:" not in t or '"targets_by_def": targets_by_def' not in t:
    raise SystemExit("mutate_changed.py가 card 35(20260930-v3-changed-stmt-scope) 병합 전 판이다 -- 이 키트는 a17b8bd 앵커"
                     "(36e170e·4a286f0 판은 install_proto.py.pre-35.bak)")
# 36e170e 재앵커: 옛 판은 'def _strip_doc' ~ 'def changed_defs' 구간을 잘라 냈다 -- 34(dd01d1d)가 그 사이에 bind_hash·_HASH_RE·
# approved_index·exempt_decision을 넣어 조용히 지워졌다. 두 def 본문만 정확히 앵커로 바꾼다(0f23786·36e170e·a17b8bd 모두 같은 텍스트).
t = sub(t, """def _strip_doc(fn):
    f = copy.deepcopy(fn)
    for n in ast.walk(f):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)) and n.body \\
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) \\
                and isinstance(n.body[0].value.value, str):
            n.body = n.body[1:] or [ast.Pass()]
    return f


def def_hash(fn):
    return hashlib.sha256(ast.dump(_strip_doc(fn), include_attributes=False).encode("utf-8")).hexdigest()
""", """_strip_doc = rch._strip_doc
def_hash = rch.def_hash
""", "mc strip_doc def_hash")
t = sub(t, """        head_files = rch.read_tree(root, ns.head, rch.GRAPH_PREFIXES)
""", """        head_files = rch.read_tree(root, ns.head, rch.GRAPH_PREFIXES)
        base_files = rch.read_tree(root, ns.base, rch.GRAPH_PREFIXES)
        moved = rch.moved_defs({k: v for k, v in base_files.items() if rch._is_source(k)},
                               {k: v for k, v in head_files.items() if rch._is_source(k)})
        defs_out = []
        _g1_origin_by_q = None        # 변형 scope_from_origin 전용(한 번만 만든다)
""", "mc read_tree")
# a17b8bd 재앵커: 옮긴 def 제외는 card 35의 _Scope 생성·targets_by_def 기록보다 앞(계약 4 -- 옮긴 def는 not_targeted·targets_by_def에 들지 않는다)
t = sub(t, """            for q, fn in changed_defs(base_src, head_src):
                inv = inventory(edges, "%s::%s" % (path, q), test_nodes)
""", """            for q, fn in changed_defs(base_src, head_src):
                if rch.g1_excluded(moved, path, q, fn):
                    continue
                defs_out.append("%s::%s" % (path, q))
                inv = inventory(edges, "%s::%s" % (path, q), test_nodes)
""", "mc loop")
t = sub(t, """                scope = _Scope(base_defs[q], fn) if q in base_defs else None
""", """                scope = _Scope(base_defs[q], fn) if q in base_defs else None
                if scope is None and "scope_from_origin" in os.environ.get("G1_VARIANT", "").split(","):
                    # 잘못된 구현 변형(D-20 위반): 같은 경로 base def가 없으면 base 전체에서 같은 qualname 하나와 문장 단위로 맞춘다
                    if _g1_origin_by_q is None:
                        _g1_origin_by_q = {}
                        for _pp, _ss in base_files.items():
                            if rch._is_source(_pp):
                                for _qq, _n in rch.iter_defs(ast.parse(_ss)):
                                    _g1_origin_by_q.setdefault(_qq, []).append(_n)
                    _c = _g1_origin_by_q.get(q, [])
                    scope = _Scope(_c[0], fn) if len(_c) == 1 else None
""", "mc scope")
# a17b8bd 재앵커: card 35가 출력에 not_targeted·targets_by_def를 더했다 -- 그 키는 그대로 두고 G1 키를 뒤에 덧붙인다
t = sub(t, """                      "survivor_bindings": survivor_bindings, "exempt_ignored": exempt_ignored,
                      "not_targeted": not_targeted_n, "targets_by_def": targets_by_def},
                     ensure_ascii=False))""",
        """                      "survivor_bindings": survivor_bindings, "exempt_ignored": exempt_ignored,
                      "not_targeted": not_targeted_n, "targets_by_def": targets_by_def, "defs": defs_out,
                      "moved": rch.g1_moved_list(moved), "move_rejected": moved["rejected"]},
                     ensure_ascii=False))""", "mc print")
out[p] = t

# ---------------------------------------------------------------- source_lint.py
p = os.path.join(G, "source_lint.py")
t = rd(p)
t = sub(t, """import sys
""", """import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reachability as rch  # noqa: E402
""", "sl import")
t = sub(t, """def compare(path, base_src, head_src, kd):""", """def _g1_before(path, moved, base_t, kd, _cache={}):
    \"\"\"계약 5: {단위: {검사: 이전 항목 수}} 덧셈분 -- 옮긴 def 단위 = 원본 파일 맥락의 원본 단위, <module> += 옮긴 문장(원본 맥락, 줄 범위).\"\"\"
    def feats(pb):
        if pb not in _cache:
            src = base_t[pb]
            tr = ast.parse(src)
            f = unit_features(tr, src, kd)
            for u, lines in decorator_caches(tr).items():
                f.setdefault(u, {}).setdefault("unbounded_cache", []).extend(lines)
            _cache[pb] = (tr, f)
        return _cache[pb]
    over, extra = {}, {}
    for to, frm in moved["defs"].items():
        if to.split("::")[0] != path:
            continue
        pb, q = frm.split("::", 1)
        over[to.split("::", 1)[1]] = {k: len(v) for k, v in feats(pb)[1].get(q, {}).items()}
    if "v6_no_module_extra" not in os.environ.get("G1_VARIANT", "").split(","):
        for to, frm in moved["units"].items():
            if to.split("::")[0] != path or "::<stmt:" not in to:
                continue
            pb = frm.split("::")[0]
            h = to.split("<stmt:")[1][:-1]
            tr, f = feats(pb)
            for n in tr.body:
                if rch.def_hash(n)[:12] == h:
                    lo, hi = n.lineno, getattr(n, "end_lineno", n.lineno)
                    for k, items in f.get("<module>", {}).items():
                        extra[k] = extra.get(k, 0) + len([x for x in items if lo <= (x[0] if isinstance(x, tuple) else x) <= hi])
    return over, extra


def compare(path, base_src, head_src, kd, g1=None):""", "sl compare def")
t = sub(t, """    for unit, feats in hf.items():
        for k, items in feats.items():
            before = bf.get(unit, {}).get(k, [])
""", """    over, extra = g1 if g1 else ({}, {})
    for unit, feats in hf.items():
        for k, items in feats.items():
            before = bf.get(unit, {}).get(k, [])
            if unit in over:
                before = [None] * over[unit].get(k, 0)
            elif unit == "<module>" and extra.get(k):
                before = list(before) + [None] * extra[k]
""", "sl before")
t = sub(t, """        findings = []
        for p in targets:
            findings += compare(p, _src(ns.root, ns.base, p), _src(ns.root, ns.head, p), kd)
""", """        findings = []
        base_t = rch.read_tree(ns.root, ns.base, rch.SOURCE_GLOBS)
        head_t = rch.read_tree(ns.root, ns.head, rch.SOURCE_GLOBS)
        moved = rch.moved_defs({k: v for k, v in base_t.items() if rch._is_source(k)},
                               {k: v for k, v in head_t.items() if rch._is_source(k)})
        for p in targets:
            findings += compare(p, _src(ns.root, ns.base, p), _src(ns.root, ns.head, p), kd,
                                _g1_before(p, moved, base_t, kd))
""", "sl main")
t = sub(t, """    print(json.dumps({"tool": "V6", "verdict": "FAIL" if findings else "PASS", "targets": targets, "findings": findings},
                     ensure_ascii=False))""", """    print(json.dumps({"tool": "V6", "verdict": "FAIL" if findings else "PASS", "targets": targets, "findings": findings,
                      "moved": rch.g1_moved_list(moved), "move_rejected": moved["rejected"]}, ensure_ascii=False))""", "sl print")
out[p] = t

# ---------------------------------------------------------------- rt.py (관찰 "moved")
p = os.path.join(G, "redteam", "lib", "rt.py")
t = rd(p)
t = sub(t, """        if case.get("observe") == "v4_first":
            stm = iface.v4_statements(obj)
            observed = stm[0][1] if stm else None
""", """        if case.get("observe") == "v4_first":
            stm = iface.v4_statements(obj)
            observed = stm[0][1] if stm else None
        elif case.get("observe") == "moved":
            o = obj or {}
            observed = {"moved": sorted(x["to"] for x in o["moved"]) if isinstance(o.get("moved"), list) else None,
                        "move_rejected": {k: v.get("rule") for k, v in o["move_rejected"].items()}
                        if isinstance(o.get("move_rejected"), dict) else None}
            if tool == "V3":
                observed["defs"] = sorted(o["defs"]) if isinstance(o.get("defs"), list) else None
                if case.get("observe_scope"):
                    observed["not_targeted"] = o.get("not_targeted")
""", "rt observe")
out[p] = t

for p, t in out.items():
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(t)
print("installed", len(out))
