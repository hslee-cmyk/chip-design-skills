# gcb7_*.jsonl 요약 출력(읽기 전용). 사용: python show_gcb7.py <jsonl>
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
for l in open(sys.argv[1], encoding="utf-8"):
    r = json.loads(l)
    if "total" in r:
        print(r); continue
    if "error" in r:
        print(r["circuit"], "ERR", r["error"][-400:]); continue
    print(r["circuit"], "spec_rej" if r.get("spec_rejected") else "", "R", r["theta_R"], "both", r["both_nonrail"],
          ("STOP " + r["writer_plan_stop"][:260]) if "writer_plan_stop" in r else "")
    print("   dep", [(a, b) for a, b, _c in r.get("dependents", [])][:40])
    print("   ties", r.get("tie_breaks"))
    if r["circuit"] == "erfc_ota":
        for n, d in r["detail"].items():
            print("   ", n, d)
