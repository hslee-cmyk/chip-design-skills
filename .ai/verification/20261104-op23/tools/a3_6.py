# -*- coding: utf-8 -*-
"""A3-6: 새 소자 줄 표기(dialect.device_line, 기술자 선언)로 lut_v2_bin_rule.json 점 전부의 showmod bin = 선언 chosen_bin, 격리 환경 모드 = 선언 compat.
인스턴스 보고 l,w,m,ad,pd 원값 = 입력에서 따로 계산한 SI 기대값. 사용: a3_6.py <iso_v> <work> <exe> <out.json>
"""
import json, os, re, shutil, subprocess, sys

ISO, WORK, EXE, OUT = sys.argv[1:5]
S = os.path.join(ISO, "skills/analog-gmid-design")
O = os.path.join(S, "tools/spice_oracle")
sys.path.insert(0, O)
from adapters.ngspice import dialect  # noqa: E402
from core.descriptor import load_descriptor  # noqa: E402
from core.ir import Diffusion, Mos  # noqa: E402

D = load_descriptor(os.path.join(O, "descriptors/sky130.oracle_descriptor.json"), env=os.environ)
rule = json.load(open(os.path.join(S, "assets/lut_v2_bin_rule.json"), encoding="utf-8"))
os.makedirs(WORK, exist_ok=True)
home = os.path.join(WORK, "home")
os.makedirs(home, exist_ok=True)
env = dict(os.environ)
env["HOME"] = env["USERPROFILE"] = home
for k in ("HOMEDRIVE", "HOMEPATH", "SPICE_USERINIT_DIR"):
    env.pop(k, None)
KIND = {"nmos": "nfet", "pmos": "pfet"}
res = {"compat_decl": {k: rule["compat"][k] for k in ("mode", "spiceinit_sha256")}, "kinds": {}, "readback": {}}
logs_compat = set()


def tab(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    r = {}
    for m in re.finditer(r"\.model\s+(\S+)\s+\w+\s*\n(.*?)(?=\n\.model|\Z)", t, re.S | re.I):
        b = m.group(2)
        g = lambda k: float(re.search(rf"\b{k}\s*=\s*([-+0-9.eE]+)", b).group(1))  # noqa: E731
        r[(g("lmin"), g("lmax"), g("wmin"), g("wmax"))] = m.group(1)
    return r


for kind, tag in KIND.items():
    kd = D.doc["kinds"][kind]
    sub = D.text(kd["name"])
    inner = D.text(kd["inner_device"])
    u = D.quantity(kd["geometry_unit"]["source"])
    to = [dict(t, name=D.text(t["name"])) if "name" in t else dict(t) for t in kd["parallel_multiplier"]["to"]]
    incs = [D.source_path(i["source"]) for i in kd["includes"]]
    T = tab(D.source_path(kd["name"]["expr"]["source"]))
    pts = [p for p in rule["evidence"]["points"] if tag in p["chosen_bin"]]
    tot, diff, unmatched, gbad = 0, [], 0, []
    for s in range(0, len(pts), 60):
        ch = pts[s:s + 60]
        L = ["* a3_6"] + [f'.include "{p.replace(chr(92), "/")}"' for p in incs] + [f".option scale={dialect.fmt(u)}", "vg g 0 dc 0", "vd d 0 dc 0", "vs s 0 dc 0", "vb b 0 dc 0"]
        for i, p in enumerate(ch):
            m = Mos(f"p{i}", kind, "d", "g", "s", "b", p["L"], p["W"], 1, None, None)
            L.append(dialect.device_line(m, sub, u, to))
        L += [".control", "op"]
        for i in range(len(ch)):
            L += [f"echo SHOWMOD p{i}", f"showmod m.xp{i}.{inner} : lmin lmax wmin wmax", f"print @m.xp{i}.{inner}[l]", f"print @m.xp{i}.{inner}[w]"]
        L += ["quit", ".endc", ".end"]
        d = os.path.join(WORK, f"{kind}_{s}")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "t.cir"), "w", newline="\n").write("\n".join(L) + "\n")
        r = subprocess.run([EXE, "-b", "t.cir"], cwd=d, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        txt = r.stdout + r.stderr
        for ln in txt.splitlines():
            if "compatibility mode" in ln.lower():
                logs_compat.add(ln.strip())
        blks = re.split(r"SHOWMOD ", txt)[1:]
        for blk in blks:
            i = int(blk.split()[0][1:])
            vals = []
            for key in ("lmin", "lmax", "wmin", "wmax"):
                m = re.search(rf"^\s*{key}\s+([-+0-9.eE]+)", blk, re.M)
                vals.append(float(m.group(1)) if m else None)
            p = ch[i]
            tot += 1
            b = T.get(tuple(vals))
            if b is None:
                unmatched += 1
            elif b.lower() != p["chosen_bin"].lower():
                diff.append({"L": p["L"], "W": p["W"], "decl": p["chosen_bin"], "got": b})
            ml = re.search(r"\[l\]\s*=\s*([-+0-9.eE]+)", blk)
            mw = re.search(r"\[w\]\s*=\s*([-+0-9.eE]+)", blk)
            gl, gw = float(ml.group(1)) if ml else None, float(mw.group(1)) if mw else None
            if gl is None or gw is None or abs(gl - p["L"]) > 1e-6 * p["L"] or abs(gw - p["W"]) > 1e-6 * p["W"]:
                gbad.append({"L": p["L"], "W": p["W"], "gl": gl, "gw": gw})
        shutil.rmtree(d, ignore_errors=True)
    res["kinds"][kind] = {"points": tot, "declared_points": len(pts), "differ": len(diff), "unmatched": unmatched, "geometry_bad": len(gbad), "ex": diff[:10], "gex": gbad[:10]}
    # 보고 원값: 배수·확산 포함 한 소자
    m = Mos("g1", kind, "d", "g", "s", "b", 5e-7, 2e-6, 3, Diffusion(1e-12, 1e-12, 4e-6, 4e-6), None)
    L = ["* readback"] + [f'.include "{p.replace(chr(92), "/")}"' for p in incs] + [f".option scale={dialect.fmt(u)}", "vg g 0 dc 0.7", "vd d 0 dc 0.9", "vs s 0 dc 0", "vb b 0 dc 0",
                                                                                  dialect.device_line(m, sub, u, to), ".control", "op"]
    L += [f"print @m.xg1.{inner}[{q}]" for q in ("l", "w", "m", "ad", "as", "pd", "ps")] + ["quit", ".endc", ".end"]
    d = os.path.join(WORK, f"rb_{kind}")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "t.cir"), "w", newline="\n").write("\n".join(L) + "\n")
    r = subprocess.run([EXE, "-b", "t.cir"], cwd=d, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    res["readback"][kind] = {"line": dialect.device_line(m, sub, u, to), "values": re.findall(r"\[(\w+)\]\s*=\s*([-+0-9.eE]+)", r.stdout),
                             "expected_SI": {"l": 5e-7, "w": 2e-6, "m": 3, "ad": 1e-12, "as": 1e-12, "pd": 4e-6, "ps": 4e-6}}
    shutil.rmtree(d, ignore_errors=True)
res["log_compat_lines"] = sorted(logs_compat)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=0))
