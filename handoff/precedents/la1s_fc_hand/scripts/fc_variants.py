"""x0 에서 출발해 헤드룸·가드를 보는 변형들을 차례로 손계산(결과는 design_log.txt 에 append)."""
import copy, json, subprocess, sys
base = json.load(open("x0.json", encoding="utf-8"))
var = {
    "x1": {"g": {"M9": 18, "M10": 18, "M7": 22, "M8": 22, "M3": 7, "M4": 7, "MP": 7}, "r_cas": 0.5},
    "x2": {"g": {"M9": 16, "M10": 16, "M7": 22, "M8": 22, "M3": 6, "M4": 6, "MP": 6}, "r_cas": 0.4},
    "x3": {"g": {"M9": 18, "M10": 18, "M7": 22, "M8": 22, "M3": 6, "M4": 6, "MP": 6, "M1": 20, "M2": 20}, "r_cas": 0.4},
    "x4": {"g": {"M9": 14, "M10": 14, "M7": 22, "M8": 22, "M3": 6, "M4": 6, "MP": 6, "M1": 20, "M2": 20}, "r_cas": 0.4,
           "L": {"M9": 2.0e-6, "M10": 2.0e-6, "M3": 2.0e-6, "M4": 2.0e-6, "MP": 2.0e-6}},
}
for tag, v in var.items():
    x = copy.deepcopy(base)
    x["tag"] = tag
    for k, val in v.items():
        if isinstance(val, dict):
            x[k].update(val)
        else:
            x[k] = val
    json.dump(x, open(tag + ".json", "w", encoding="utf-8"))
    r = subprocess.run([sys.executable, "fc_design.py", tag + ".json", "../out/d_%s.json" % tag, "../out/design_log.txt"],
                       capture_output=True, text=True)
    if r.returncode:
        open("../out/design_log.txt", "a", encoding="utf-8").write("%s | 실패: %s\n" % (tag, r.stderr.strip().splitlines()[-1]))
