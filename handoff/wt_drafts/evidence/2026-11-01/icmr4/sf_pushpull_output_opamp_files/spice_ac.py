"""설계점(v2) 개루프 AC(servo: 큰 L DC 되먹임 + 큰 C 입력 결합) -- DC 이득·GBW·PM·Rout(출력 테스트 전류원) 측정. jsonl append."""
import json, math, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spice_icmr as S

case = sys.argv[1] if len(sys.argv) > 1 else "v2"
d = [json.loads(l) for l in open(HERE / "spice_icmr.jsonl", encoding="utf-8")]
des = [r for r in d if r.get("case") == case and r["step"] == "design"][-1]
sz = {k: tuple(v) for k, v in des["size"].items()}
R, Cc = des["R"], des["Cc"]
deck = "\n".join([S.header(), S.body(sz, R, Cc),
                  "Vinp vin_p 0 DC 0.9 AC 1", "Lfb vout vfb 1e9", "Vofs vin_n vfb DC 0", "Cfb vin_n 0 1e3",
                  "Iout vout 0 DC 0 AC 0",
                  ".control", "set numdgt=8", "op", "print v(vout) v(vin_n)",
                  "ac dec 40 1 1e10",
                  "let A=v(vout)/(v(vin_p)-v(vin_n))",
                  "let Adb=db(A)", "let ph=180/PI*cph(A)",
                  "meas ac a0 find Adb at=10",
                  "meas ac ugf when Adb=0",
                  "meas ac phu find ph when Adb=0",
                  "quit", ".endc", ".end"])
out = S.run(deck, f"ac_{case}")
v = {}
for line in out.splitlines():
    m = re.match(r"^\s*(a0|ugf|phu)\s*=\s*([-+0-9.eE]+)", line)
    if m:
        v[m.group(1)] = float(m.group(2))
# Rout: 출력에 AC 전류 1 A, 입력 AC 0, DC 되먹임만(L) -- 개루프 출력 저항(DC servo는 저주파에서 루프를 닫으므로 L 차단 위 주파수에서 읽음)
deck2 = "\n".join([S.header(), S.body(sz, R, Cc).replace("CCL vout agnd 1e-12", "* CL removed for Rout"),
                   "Vinp vin_p 0 DC 0.9", "Lfb vout vfb 1e9", "Vofs vin_n vfb DC 0", "Cfb vin_n 0 1e3",
                   "Ix 0 vout DC 0 AC 1",
                   ".control", "set numdgt=8", "op", "ac dec 10 1e3 1e6",
                   "meas ac zout find vm(vout) at=1e4",
                   "quit", ".endc", ".end"])
out2 = S.run(deck2, f"rout_{case}")
for line in out2.splitlines():
    m = re.match(r"^\s*(zout)\s*=\s*([-+0-9.eE]+)", line)
    if m:
        v[m.group(1)] = float(m.group(2))
pm = 180 + v["phu"] if "phu" in v else None
rec = {"case": case, "step": "ac", "a0_db": v.get("a0"), "ugf_hz": v.get("ugf"), "phase_at_ugf_deg": v.get("phu"), "pm_deg": pm,
       "zout_ohm_10k": v.get("zout"), "tail": out[-600:] if not v else None}
with open(HERE / "spice_icmr.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(rec)
