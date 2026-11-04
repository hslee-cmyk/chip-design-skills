"""Hand mutants for V3 (GL-1). usage: python -I mutants.py <throwaway clone root> <out jsonl>
Applies one replacement, runs the matching new test files, restores original bytes, appends one JSON line per mutant."""
import json, os, subprocess, sys, time
from pathlib import Path

root, outp = Path(sys.argv[1]), Path(sys.argv[2])
S = "skills/analog-gmid-design/gmid_engine/tests/structure/"
CH = root / (S + "structure_checks.py")
TOOL = root / "tools/audit/scan_shared_calls.py"
LINT = [S + "test_g8_lint.py", S + "test_value_types_lint.py", S + "test_g8_baseline.py"]
SCAN = [S + "test_scan_shared_calls_tool.py"]
M = [
 # checker: G8
 ("C01_attr_off", CH, 'elif sc.kind == "func" and sc.mparam is not None and _mutable_value(value):', 'elif False:'),
 ("C02_attr_self_only", CH, 'isinstance(t.value, ast.Name) and t.value.id == sc.mparam:\n                        out.append(Violation("g8_attr', 'isinstance(t.value, ast.Name) and t.value.id == "self":\n                        out.append(Violation("g8_attr'),
 ("C03_class_off", CH, 'if _mutable_value(value):\n                            out.append(Violation("g8_class_container"', 'if False:\n                            out.append(Violation("g8_class_container"'),
 ("C04_factory_no_set", CH, 'G8_FACTORY_CONTAINERS = ("dict", "list", "set")', 'G8_FACTORY_CONTAINERS = ("dict", "list")'),
 ("C05_factory_double", CH, 'handled.add(id(value))', 'pass'),
 ("C06_cached_off", CH, 'if _decorator_name(d) == "cached_property":', 'if False:'),
 ("C07_deco_not_excluded", CH, 'if id(node) not in deco_calls and (', 'if ('),
 ("C08_obj_cache_counted", CH, 'and isinstance(f.value, ast.Name) and f.value.id == "functools")', ')'),
 ("C09_id_off", CH, 'if isinstance(f, ast.Name) and f.id == "id":', 'if False:'),
 ("C10_memo_local_ok", CH, 'return not isinstance(root, ast.Name) or root.id in local', 'return not isinstance(root, ast.Name)'),
 ("C11_memo_noarg_ok", CH, 'if not n.args:\n        return True', 'if not n.args:\n        return False'),
 ("C12_memo_lambda_ok", CH, 'if not isinstance(a, (ast.Name, ast.Attribute)):\n        return True', 'if not isinstance(a, (ast.Name, ast.Attribute)):\n        return False'),
 ("C13_no_lookup_persistent", CH, 'G8_MEMO_LOOKUPS = ("lookup", "lookup_persistent")', 'G8_MEMO_LOOKUPS = ("lookup",)'),
 ("C14_memo_attr_recv_off", CH, 'return (isinstance(e, ast.Name) and e.id == "memo") or (isinstance(e, ast.Attribute) and e.attr == "memo")', 'return (isinstance(e, ast.Name) and e.id == "memo")'),
 ("C15_allow_drop_one", CH, '"search/s3_index.py", "core/run_counters.py",\n)', '"search/s3_index.py",\n)'),
 ("C16_allow_basename", CH, 'if r in G8_ALLOWED_MODULES:\n            continue\n        out.extend(_g8_file', 'if Path(r).name in {Path(x).name for x in G8_ALLOWED_MODULES}:\n            continue\n        out.extend(_g8_file'),
 ("C17_modcache_top_only", CH, 'for s in _module_level(tree.body):\n        parts = _assign_parts(s)', 'for s in tree.body:\n        parts = _assign_parts(s)'),
 ("C18_modcache_drop_weak", CH, 'G8_MODULE_CACHE_CLASSES = ("BoundedLRU", "LutMemo", "OrderedDict", "WeakValueDictionary")', 'G8_MODULE_CACHE_CLASSES = ("BoundedLRU", "LutMemo", "OrderedDict")'),
 ("C19_g8_unsorted", CH, 'out.extend(_g8_file(parse(p), r))\n    return len(targets), sorted(out)', 'out.extend(_g8_file(parse(p), r))\n    return len(targets), list(reversed(sorted(out)))'),
 ("C20_targets_excl_allowed", CH, 'out.extend(_g8_file(parse(p), r))\n    return len(targets), sorted(out)', 'out.extend(_g8_file(parse(p), r))\n    return len(targets) - 1, sorted(out)'),
 # checker: value types
 ("V01_frozen_any_dataclass", CH, 'if k.arg == "frozen" and isinstance(k.value, ast.Constant) and k.value.value is True:\n                    return True', 'return True'),
 ("V02_ann_no_string", CH, 'elif isinstance(n, ast.Constant) and isinstance(n.value, str):', 'elif False:'),
 ("V03_ann_no_attr", CH, 'elif isinstance(n, ast.Attribute) and n.attr in types:', 'elif False:'),
 ("V04_max_type", CH, 'min(found)', 'max(found)'),
 ("V05_frozen_class_flagged", CH, 'elif sc.kind == "class" and not sc.cls_frozen and isinstance(t, ast.Name):', 'elif sc.kind == "class" and isinstance(t, ast.Name):'),
 ("V06_frozen_method_flagged", CH, 'sc.mparam is not None and not sc.mfrozen and isinstance(t, ast.Attribute)', 'sc.mparam is not None and isinstance(t, ast.Attribute)'),
 ("V07_vt_allow_off", CH, 'for r, tree in trees:\n        if r in G8_ALLOWED_MODULES:\n            continue\n', 'for r, tree in trees:\n'),
 ("V08_wrap_drop_set", CH, 'G8_LIST_CONTAINER_CALLS = ("tuple", "list", "set", "frozenset", "dict", "MappingProxyType")', 'G8_LIST_CONTAINER_CALLS = ("tuple", "list", "frozenset", "dict", "MappingProxyType")'),
 ("V09_wrap_drop_dict", CH, 'G8_LIST_CONTAINER_CALLS = ("tuple", "list", "set", "frozenset", "dict", "MappingProxyType")', 'G8_LIST_CONTAINER_CALLS = ("tuple", "list", "set", "frozenset", "MappingProxyType")'),
 ("V10_wrap_drop_mapping", CH, 'G8_LIST_CONTAINER_CALLS = ("tuple", "list", "set", "frozenset", "dict", "MappingProxyType")', 'G8_LIST_CONTAINER_CALLS = ("tuple", "list", "set", "frozenset", "dict")'),
 ("V11_wrap_drop_tuple", CH, 'G8_LIST_CONTAINER_CALLS = ("tuple", "list", "set", "frozenset", "dict", "MappingProxyType")', 'G8_LIST_CONTAINER_CALLS = ("list", "set", "frozenset", "dict", "MappingProxyType")'),
 ("V12_dict_keys_off", CH, 'subs = [k for k in v.keys if k is not None] + list(v.values)', 'subs = list(v.values)'),
 ("V13_comp_off", CH, 'elif isinstance(v, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):\n        subs = [v.elt]', 'elif False:\n        subs = []'),
 ("V14_dictcomp_off", CH, 'elif isinstance(v, ast.DictComp):\n        subs = [v.key, v.value]', 'elif False:\n        subs = []'),
 ("V15_ann_preference_off", CH, 'kind, found = "vt_annotation", ann', 'kind, found = "vt_assign", ann'),
 # checker: ratchet
 ("R01_new_full_count", CH, 'new = tuple((k[0], k[1], k[2], now[k] - base.get(k, 0))', 'new = tuple((k[0], k[1], k[2], now[k])'),
 ("R02_stale_full_count", CH, 'stale = tuple((k[0], k[1], k[2], base[k] - now.get(k, 0))', 'stale = tuple((k[0], k[1], k[2], base[k])'),
 ("R03_stale_is_new", CH, 'return RatchetResult(new=new, stale=stale)', 'return RatchetResult(new=new + stale, stale=())'),
 ("R04_line_in_key", CH, 'return (v.kind, v.path, v.detail)', 'return (v.kind, v.path, "%s@%d" % (v.detail, v.line))'),
 ("R05_bool_count_ok", CH, 'if isinstance(c, bool) or not isinstance(c, int) or c < 1:', 'if not isinstance(c, int) or c < 1:'),
 ("R06_dup_ok", CH, 'if key in seen:', 'if False:'),
 ("R07_sha_unanchored", CH, 'BASELINE_SHA = re.compile(r"^[0-9a-f]{40}$")', 'BASELINE_SHA = re.compile(r"^[0-9a-f]{40}")'),
 ("R08_unsorted_keys", CH, 'json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2)', 'json.dumps(doc, ensure_ascii=False, sort_keys=False, indent=2)'),
 ("R09_no_trailing_nl", CH, 'sort_keys=True, indent=2) + "\\n").encode("utf-8")', 'sort_keys=True, indent=2)).encode("utf-8")'),
 ("R10_missing_returns_empty", CH, 'raw = Path(path).read_bytes()                 # 파일 없음', 'raw = Path(path).read_bytes() if Path(path).exists() else b\'{"id":"x","base_commit":"\' + b"a"*40 + b\'","rows":[]}\'  # 파일 없음'),
 # tool
 ("T01_value_leaf_off", TOOL, 'if f.attr == "value" and len(e.args) >= 3 and _str_const(e.args[0]) and _str_const(e.args[2]):', 'if False:'),
 ("T02_column_leaf_off", TOOL, 'if f.attr == "column" and len(e.args) >= 2 and _str_const(e.args[0]) and _str_const(e.args[1]):', 'if False:'),
 ("T03_import_as_off", TOOL, 'if a.asname:\n                        if a.name in self.mods:\n                            aliases[a.asname] = a.name', 'if False:\n                        pass'),
 ("T04_for_comp_assign_off", TOOL, 'elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)):\n            add(_target_names(n.target), n.iter)', 'elif False:\n            pass'),
 ("T05_local_trace_off", TOOL, 'if use is not None:\n                if marker in seen:', 'if False:\n                if marker in seen:'),
 ("T06_reexport_off", TOOL, 'if r:\n                            return r\n        return None', 'if r:\n                            return (mod, name)\n        return None'),
 ("T07_param_subst_off", TOOL, 'if len(callers) == 1:', 'if False:'),
 ("T08_param_subst_many", TOOL, 'if len(callers) == 1:', 'if len(callers) >= 1:'),
 ("T09_B_no_field_req", TOOL, 'if a["arg_keys"] == b["arg_keys"] and _field_leaves(a) >= 1 and _field_leaves(b) >= 1:', 'if a["arg_keys"] == b["arg_keys"]:'),
 ("T10_notB_param_ok", TOOL, 'and _param_leaves(a) == 0 and _param_leaves(b) == 0):', '):'),
 ("T11_class_priority", TOOL, 'cls = "B" if counts["B"] else ("D" if counts["D"] else "not_B")', 'cls = "D" if counts["D"] else ("B" if counts["B"] else "not_B")'),
 ("T12_touching_off", TOOL, 'if touched and not any(c["_rel"] in touched for c in cs):', 'if False:'),
 ("T13_touching_bad_ok", TOOL, 'raise InputError("--touching 경로가 대상 파일에 없다: %s" % t)', 'return p'),
 ("T14_same_module_counted", TOOL, 'if tgt[0] == mname:\n                continue', 'if False:\n                continue'),
 ("T15_calls_unsorted", TOOL, 'calls.sort(key=lambda c: (c["callee_mod"], c["callee"], c["caller_mod"], c["line"], c["_col"], c["caller_fn"], c["text"]))', 'calls.reverse()'),
 ("T16_stale_b_kept", TOOL, 'if stale.is_file():\n            stale.unlink()', 'pass'),
 ("T17_method_count_off", TOOL, 'if isinstance(call.func, ast.Attribute):\n                    method_unresolved += 1', 'pass'),
 ("T18_param_leaf_count_off", TOOL, '"sites_with_param_leaf": sum(1 for c in calls if _param_leaves(c) >= 1)', '"sites_with_param_leaf": 0'),
 ("T19_tests_scanned", TOOL, 'if parts[0] == "tests" or any(', 'if any('),
 ("T20_literal_leaf_off", TOOL, 's = repr(e.value)\n            leaves.append(s)', 's = "L"\n            leaves.append(s)'),
 ("T21_global_as_param", TOOL, 'leaf = "G[%s]" % nm', 'leaf = "P[%s]" % nm'),
 ("T22_name_check_off", TOOL, 'if engine_dir.name != PKG:', 'if False:'),
 ("T23_nopy_ok", TOOL, 'if not self.mods:\n            raise InputError(".py 파일이 없다")', 'pass'),
 ("T24_syntax_skip", TOOL, 'raise InputError("구문 오류·읽기 실패: %s (%s)" % (rel, e))', 'continue'),
]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", OPENBLAS_NUM_THREADS="1")
done = set()
if outp.exists():
    done = {json.loads(l)["id"] for l in outp.read_text(encoding="utf-8").splitlines() if l.strip()}
for mid, path, old, new in M:
    if mid in done:
        continue
    orig = path.read_bytes()
    # git autocrlf can leave CRLF in the clone; mutants are written with LF, so normalise for the search and keep LF while testing
    txt = orig.decode("utf-8").replace("\r\n", "\n")
    n = txt.count(old)
    rec = {"id": mid, "file": path.name, "matches": n}
    if n < 1:
        rec["status"] = "NOT_APPLIED"
    else:
        path.write_bytes(txt.replace(old, new).encode("utf-8"))
        t0 = time.time()
        files = SCAN if path == TOOL else LINT
        x = subprocess.run([sys.executable, "-P", "-m", "pytest", *files, "-q", "-p", "no:cacheprovider", "--tb=no", "-x"],
                           cwd=str(root), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        rec.update(rc=x.returncode, sec=round(time.time() - t0), tail=x.stdout.strip().splitlines()[-1:] or [""],
                   first_fail=[l for l in x.stdout.splitlines() if l.startswith(("FAILED", "ERROR"))][:2],
                   status="killed" if x.returncode == 1 else ("SURVIVED" if x.returncode == 0 else "RC%d" % x.returncode))
    path.write_bytes(orig)
    with open(outp, "ab") as f:
        f.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))
print("done")
