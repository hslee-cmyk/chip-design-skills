"""p7: '@' 원소가 든 승인 기록 저장소(P2)에서 base 판 대 병합본 test_lint.py·reachability.py 출력·exit 대조 +
merge_gate.parse_approval_header·weakening_diff.approved_hashes·reachability._approved_ids 결과(두 판).
사용: python -B p7_other_tools.py <base gate> <병합 gate> <out json>"""
import hashlib
import json
import subprocess
import sys

BG, MG, OUT = sys.argv[1:4]
PY = sys.executable
repos = {"P2": ("C:/g186/o7/pw/P2", "4789c1dc89e41318cbe9e682aef0381292453357", "5a884be2002ed4b76eeae18026aed5e2e49060e3")}
res = {"file_identity_lf": {}}
for f in ("test_lint.py", "reachability.py", "merge_gate.py", "weakening_diff.py", "gate_config.json"):
    a, b = (open(x + "/" + f, "rb").read().replace(b"\r\n", b"\n") for x in (BG, MG))
    res["file_identity_lf"][f] = [hashlib.sha256(a).hexdigest()[:16], hashlib.sha256(b).hexdigest()[:16], a == b]
for name, (r, b, h) in repos.items():
    for tool, extra in (("test_lint.py", ["--subject", "pc:h1"]), ("reachability.py", ["--config", None])):
        outs = []
        for g in (BG, MG):
            ex = [x if x is not None else g + "/gate_config.json" for x in extra]
            p = subprocess.run([PY, g + "/" + tool, "--root", r, "--base", b, "--head", h, *ex], capture_output=True)
            outs.append((p.returncode, p.stdout.decode("utf-8", "replace").strip()))
        res["%s_%s" % (name, tool)] = {"base": outs[0], "merged": outs[1], "same": outs[0] == outs[1]}
    for label, g in (("base", BG), ("merged", MG)):
        code = ("import sys, json; sys.path.insert(0, %r); import merge_gate as m, weakening_diff as w, reachability as rc, subprocess;"
                "t = subprocess.run(['git','-C',%r,'show',%r+':.ai/approvals/p-r3.md'],capture_output=True).stdout.decode('utf-8');"
                "t = t.replace('id: p-r3', 'id: 20261002-p-r3'); hdr = m.parse_approval_header(t, '20261002-p-r3.md');"
                "print(json.dumps({'hdr': repr(hdr)[:900], 'approved_hashes': sorted(w.approved_hashes(%r, %r)), 'approved_ids': sorted(rc._approved_ids(%r, %r))}, ensure_ascii=False))"
                ) % (g, r, h, r, h, r, h)
        p = subprocess.run([PY, "-P", "-c", code], capture_output=True)
        res["%s_lib_%s" % (name, label)] = {"exit": p.returncode, "out": p.stdout.decode("utf-8", "replace").strip(),
                                            "err": p.stderr.decode("utf-8", "replace")[-600:]}
    res["%s_lib_same" % name] = res["%s_lib_base" % name]["out"] == res["%s_lib_merged" % name]["out"]
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
