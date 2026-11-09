"""PDK 선언(sky130_pdk_decl.json)이 정한 역할 양을 원본 파일에서 직접 계산한다(엔진 reader 미사용).

선언의 expression(규칙 번호 식)을 그대로 쓰고, 값은 원본(periphery.csv, tlef, 모델 카드 .param)에서 읽는다.
PDK가 바뀌면 선언만 바뀌면 된다(O-197) -- 이 파일에는 PDK 값이 없다.
"""
import csv, json, math, re

DECL = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/sky130_pdk_decl.json"


def _rules(src, root):
    path = root + "/" + src["path"]
    sec_re = re.compile(src["section_pattern"])
    vals = {}
    prefix = None
    with open(path, encoding=src.get("encoding", "utf-8"), errors="replace") as f:
        for row in csv.reader(f):
            if not row:
                continue
            c0 = row[src["section_column"]].strip()
            m = sec_re.match(c0)
            if m:
                prefix = m.group(1)
                continue
            if prefix and c0 and len(row) > src["value_column"]:
                v = row[src["value_column"]].strip()
                u = row[src["unit_column"]].strip() if len(row) > src["unit_column"] else ""
                try:
                    x = float(v)
                except ValueError:
                    continue
                vals["%s.%s" % (prefix, c0)] = x * src["units_m"].get(u, src["units_m"].get("", 1.0))
    return vals


def _lef(src, root, name):
    with open(root + "/" + src["path"], encoding=src.get("encoding", "utf-8")) as f:
        for line in f:
            t = line.split()
            if t and t[0] == name:
                return float(t[1]) * src["units_m"][""]
    raise KeyError(name)


def _param_line(src, root):
    pat = re.compile(src["line_pattern"])
    out = {}
    with open(root + "/" + src["path"], encoding=src.get("encoding", "utf-8"), errors="replace") as f:
        for line in f:
            m = pat.match(line.strip()) or pat.match(line)
            if m:
                for kv in re.findall(r"([A-Za-z_][\w]*)\s*=\s*([-+0-9.eE]+)", m.group(1)):
                    out[kv[0]] = float(kv[1])
    return out


def quantities(names):
    d = json.load(open(DECL, encoding="utf-8"))
    root = d["pdk_root"]
    cache = {}
    res = {}
    for n in names:
        q = d["quantities"][n]
        sname = q["source"]
        src = d["sources"][sname]
        expr = q["expression"]
        if src["format"] == "rule_table_csv":
            if sname not in cache:
                cache[sname] = _rules(src, root)
            env = {k.replace(".", "_"): v for k, v in cache[sname].items()}
            e = re.sub(r"\b([a-z]+)\.(\w+)\b", lambda m: m.group(1) + "_" + m.group(2), expr)
            res[n] = eval(e, {"max": max, "min": min, "__builtins__": {}}, env)
        elif src["format"] == "lef_statement":
            res[n] = _lef(src, root, expr)
        elif src["format"] == "spice_instance_line":
            if sname not in cache:
                cache[sname] = _param_line(src, root)
            unit = src["units_m"].get("", 1.0)
            res[n] = eval(expr, {"__builtins__": {}}, cache[sname]) * unit
        else:
            raise ValueError(src["format"])
    return res


if __name__ == "__main__":
    import sys
    names = ["min_finger_w_m", "manufacturing_grid_m", "finger_pitch_overhead_m", "row_gap_m", "dummy_w_m",
             "tap_w_m", "well_spacing_m", "mim_cap_density_f_per_m2"]
    q = quantities(names)
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        for k in names:
            f.write("%s = %.6g\n" % (k, q[k]))
