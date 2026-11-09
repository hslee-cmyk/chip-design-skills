"""card 35 모의 도구(리허설 전용 -- 역할 산출물 아님, 판정 근거 아님).

    python -B p35_sim35.py <tools/gates 디렉터리> <scope_proto.py가 든 디렉터리>

<tools/gates>/mutate_changed.py(묶기 card 34 병합본 = 4a286f0 판)를 card 35 계약 4·5 모양으로 고친다:
  * 대상 판정 = 이전 키트의 독립 프로토타입 `v3scope_kit/scope_proto.py` select(…, "N2w")(card 35 계약 1을 문장만 보고 쓴 것 -- 재사용, 새로 쓰지 않음).
    새 def(base에 같은 qualname 없음)는 전부 대상.
  * 처리 순서: ① 대상 판정 → 대상 밖이면 `--out`에 {"id","result":"not_targeted"}(생성 순서대로, 대상 레코드와 섞여) 쓰고 continue
    ② 면제 판정(묶기 card 그대로) ③ 실행. `mutants` = len(results) = 대상 변이 수(그대로).
  * 출력: 묶기 card 키 뒤에 "not_targeted"(수), "targets_by_def"({"<경로>::<qualname>": {"targeted","not_targeted","deleted_statements","def_header_changed"}}).
    모의 한계: deleted_statements·def_header_changed는 null(측정 항목이 쓰지 않는다), 계약 9(데코레이터 변이 적용)는 넣지 않았다.
이미 targets_by_def가 있으면(진짜 35 병합본) 아무것도 쓰지 않고 exit 3. 앵커가 1개가 아니면 exit 1, 쓰지 않는다.
"""
import os
import sys

G, PROTO = sys.argv[1], sys.argv[2]
P = os.path.join(G, "mutate_changed.py")
with open(P, encoding="utf-8", newline="") as fh:
    t = fh.read()
crlf = "\r\n" in t
t = t.replace("\r\n", "\n")
if "targets_by_def" in t:
    print("sim35: 이미 targets_by_def가 있다(card 35 병합본) -- 모의 불필요")
    sys.exit(3)


def sub(text, old, new, label):
    n = text.count(old)
    if n != 1:
        print("sim35 앵커 %s: %d개(1개여야 한다)" % (label, n))
        sys.exit(1)
    return text.replace(old, new)


t = sub(t, """        survivor_bindings, exempt_ignored = [], []
""", """        survivor_bindings, exempt_ignored = [], []
        not_targeted, targets_by_def = 0, {}          # [sim35]
        sys.path.insert(0, %r)                        # [sim35]
        import scope_proto as _SP35                   # [sim35] v3scope_kit 독립 프로토타입(card 35 계약 1)
""" % PROTO, "init")
t = sub(t, """            modname = rch.module_name(path)
""", """            modname = rch.module_name(path)
            _b35 = dict(rch.iter_defs(ast.parse(base_src))) if base_src is not None else {}   # [sim35]
""", "base defs")
t = sub(t, """                fn_bind = bind_hash(fn)   # def마다 한 번
""", """                fn_bind = bind_hash(fn)   # def마다 한 번
                _k35 = "%s::%s" % (path, q)                                                     # [sim35]
                _sel35 = _SP35.select(_b35[q], fn, list(mutants(fn, head_src)), "N2w") if q in _b35 else None
                targets_by_def[_k35] = {"targeted": 0, "not_targeted": 0, "deleted_statements": None, "def_header_changed": None}
""", "per def")
t = sub(t, """                for opname, npath, mfn in mutants(fn, head_src):
                    mid = "%s:%s:%s:%s" % (modname, q, opname, npath)
""", """                for _i35, (opname, npath, mfn) in enumerate(mutants(fn, head_src)):
                    mid = "%s:%s:%s:%s" % (modname, q, opname, npath)
                    if _sel35 is not None and not _sel35[_i35]:                                 # [sim35] ① 대상 밖
                        not_targeted += 1
                        targets_by_def[_k35]["not_targeted"] += 1
                        if ns.out:
                            with open(ns.out, "a", encoding="utf-8") as fh:
                                fh.write(json.dumps({"id": mid, "result": "not_targeted"}, ensure_ascii=False) + "\\n")
                        continue
                    targets_by_def[_k35]["targeted"] += 1                                      # [sim35]
""", "mutant loop")
t = sub(t, """                      "survivor_bindings": survivor_bindings, "exempt_ignored": exempt_ignored},
""", """                      "survivor_bindings": survivor_bindings, "exempt_ignored": exempt_ignored,
                      "not_targeted": not_targeted, "targets_by_def": targets_by_def},
""", "print")
compile(t, P, "exec")
with open(P, "w", encoding="utf-8", newline="") as fh:
    fh.write(t.replace("\n", "\r\n") if crlf else t)
print("sim35 installed:", P)
