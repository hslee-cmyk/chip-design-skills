"""V4 rule (1)/(2) visibility diagnostic for the contract-8 assertion (gate test_lint internals, read-only import)."""
import ast, json, re, sys
sys.path.insert(0, "C:/g136/gates/tools/gates")
import test_lint as tl
iface = open("C:/g136/repo/docs/02-design/specs/20260930-b34-grammar-explicit.interface.md", encoding="utf-8").read()
subjects = {s for _, s in tl.read_card_symbols(iface)}
proto = open("C:/g136/proto/test_b34_grammar_explicit.py", encoding="utf-8").read()
fn = next(f for n, f in tl.find_test_functions(ast.parse(proto)) if n == "test_b34_c8_restored_values_equal_fresh_process")
def report(label, fn):
    for line, a, b, hooked in tl._assert_pairs(fn.body, subjects):
        if a is None:
            print("  %s line %d: no pair (hooked=%s)" % (label, line, hooked)); continue
        ka, kb = tl._call_keys(a, subjects), tl._call_keys(b, subjects)
        print("  %s line %d: subject calls left=%d %s | right=%d %s | shared=%d -> rule(1) %s" % (
            label, line, len(ka), sorted({k[0] for k in ka}), len(kb), sorted({k[0] for k in kb}), len(ka & kb),
            "FAIL" if ka & kb else "no hit"))
print("subjects:", len(subjects))
report("proto c8 (fresh process)", fn)
# variants: same body, expected from (H) helper snapshot, (B) in-process before
src_fn, _ = tl._fn_source(proto, fn)
helper = src_fn.replace("    rc, out, err = _b34_fresh_process(p)\n    assert rc == 0, err\n    expected = json.loads(out)\n    ts, _meta = stick_diagram.load_topology(p)\n",
                        "    ts, _meta = stick_diagram.load_topology(p)\n    expected = _b34_snapshot(p, ts)\n")
helper = re.sub(r"    got = \{.*?\n    \}\n", "    got = _b34_snapshot(p, ts)\n", helper, flags=re.S)
before = src_fn.replace("    rc, out, err = _b34_fresh_process(p)\n    assert rc == 0, err\n    expected = json.loads(out)\n    ts, _meta = stick_diagram.load_topology(p)\n    ov = _b34_overrides(ts)\n",
                        "    ts, _meta = stick_diagram.load_topology(p)\n    ov = _b34_overrides(ts)\n    expected = {\"find_stack_edges\": _b34_normalize(stick_diagram.find_stack_edges(ts))}\n")
before = re.sub(r"    got = \{.*?\n    \}\n", "    got = {\"find_stack_edges\": _b34_normalize(stick_diagram.find_stack_edges(ts))}\n", before, flags=re.S)
assert helper != src_fn and before != src_fn
for label, s in (("helper-snapshot variant", helper), ("in-process-before variant", before)):
    f = next(x for x in ast.parse(s).body if isinstance(x, ast.FunctionDef))
    report(label, f)
    print("  %s lint_function:" % label, [ (r["rule"], r["output"]) for r in tl.lint_function(s, f, {open('C:/g136/repo/skills/analog-gmid-design/assets/stick_diagram.py', encoding='utf-8').read(): subjects}, subjects)])
print("  proto lint_function:", [(r["rule"], r["line"] + 0, r["output"]) for r in tl.lint_function(proto, fn, {open('C:/g136/repo/skills/analog-gmid-design/assets/stick_diagram.py', encoding='utf-8').read(): subjects}, subjects)])
