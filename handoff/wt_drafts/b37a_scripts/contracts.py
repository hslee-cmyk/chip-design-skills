"""B37a 개정 card 계약 모의 판정(관찰 기록). 사본 하나에서 새 프로세스로 실행, 결과는 <out.json>.
사용: python -B contracts.py <사본 루트> <out.json>
계약 3(library: 레일 밖 넷 전부 / 합성: 포트 넷만), 4, 5, 6(거부·수용), 7, 8(orig = M.port_declaration 모양),
계약 3 반례(B1: 비포트 게이트 전용 넷만 바꾸기 -- 계약이 아님을 확인하는 참고 관찰).
합성 topology 기본형에는 `direction`이 없다(S6). 예외는 타입 이름으로 기록한다.
"""
import copy, dataclasses, glob, inspect, json, os, shutil, sys, tempfile

ROOT = sys.argv[1]
OUT = sys.argv[2]
ASSETS = os.path.join(ROOT, "skills/analog-gmid-design/assets")
sys.path.insert(0, ASSETS)
import stick_diagram as SD  # noqa: E402
import sizing_recipe as SR  # noqa: E402
for m in (SD, SR):
    assert os.path.abspath(m.__file__).replace("\\", "/").startswith(os.path.abspath(ROOT).replace("\\", "/")), m.__file__
LIB = os.path.join(ASSETS, "library")
TMP = tempfile.mkdtemp(prefix="b37a_", dir="C:/g68")
res = {}


def exc(e):
    s = str(e).replace(TMP, "<TMP>").replace(TMP.replace("/", "\\"), "<TMP>")
    return "%s: %s" % (type(e).__name__, s[:160])


def norm(x):
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return {f.name: norm(getattr(x, f.name)) for f in dataclasses.fields(x)}
    if isinstance(x, dict):
        return {str(k): norm(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (set, frozenset)):
        return sorted((norm(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True, default=str))
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x]
    return x


def unmap(x, back):
    """중립 토큰 -> 원래 이름(부분 문자열, 긴 토큰부터)."""
    if isinstance(x, str):
        for tok in sorted(back, key=len, reverse=True):
            x = x.replace(tok, back[tok])
        return x
    if isinstance(x, dict):
        return {unmap(k, back): unmap(v, back) for k, v in x.items()}
    if isinstance(x, list):
        return [unmap(v, back) for v in x]
    return x


def deep_rename(obj, fwd):
    if isinstance(obj, str):
        return fwd.get(obj, obj)
    if isinstance(obj, dict):
        return {fwd.get(k, k): deep_rename(v, fwd) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_rename(v, fwd) for v in obj]
    return obj


def write(d, name):
    p = os.path.join(TMP, name)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(d, fh)
    return p


def meta_cmp(meta):
    m = {k: v for k, v in meta.items() if k != "ports"}
    return norm(m)


# ---------- 계약 3 library: supply_nets 밖의 모든 넷 ----------
def lib_nets(d):
    nets = set()
    for t in d["netlist"]:
        nets |= {t["source"], t["drain"], t["gate"]}
    for e in (d.get("passive_elements") or []) + (d.get("ideal_sources") or []):
        nets |= set(e.get("terminals") or [])
    nets |= {k for k in (d.get("ports") or {}) if not k.startswith("_")}
    return sorted(nets - set(d.get("supply_nets") or []))


c3 = {}
for p in sorted(glob.glob(os.path.join(LIB, "*.topology.json"))):
    name = os.path.basename(p).replace(".topology.json", "")
    if name.startswith("_"):
        continue
    d = json.load(open(p, encoding="utf-8"))
    nets = lib_nets(d)
    fwd = {n: "ZQ%dQ" % i for i, n in enumerate(nets)}
    back = {v: k for k, v in fwd.items()}
    p2 = write(deep_rename(copy.deepcopy(d), fwd), "ren_" + os.path.basename(p))
    try:
        _, m0 = SD.load_topology(p)
        _, m1 = SD.load_topology(p2)
        a, b = meta_cmp(m0), unmap(meta_cmp(m1), back)
        diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        devs = {}
        for k in ("device_roles", "_device_roles_autofilled"):
            if k in diff:
                da, db = a.get(k) or {}, b.get(k) or {}
                devs[k] = sorted(x for x in set(da) | set(db) if da.get(x) != db.get(x))
        c3[name] = {"renamed": len(nets), "same": not diff, "diff_keys": diff, "diff_devices": devs}
    except Exception as e:
        c3[name] = {"exc": exc(e)}
res["c3_library_all_nonrail"] = c3


# ---------- 합성 topology(기본형: direction 없음) ----------
def ota(inp, inn, ports=None):
    d = {"topology_name": "syn_ota", "schema_version": "2.0", "supply_nets": ["vdd", "gnd"],
         "symmetry": {"matching_pairs": [], "dispositions": []},
         "netlist": [
             {"name": "M1", "kind": "nmos", "gate": inp, "drain": "x", "source": "tail"},
             {"name": "M2", "kind": "nmos", "gate": inn, "drain": "out", "source": "tail"},
             {"name": "M3", "kind": "pmos", "gate": "x", "drain": "x", "source": "vdd"},
             {"name": "M4", "kind": "pmos", "gate": "x", "drain": "out", "source": "vdd"},
             {"name": "M5", "kind": "nmos", "gate": "nb", "drain": "tail", "source": "gnd"}]}
    d["ports"] = ports if ports is not None else {
        inp: {"role": "differential_input_p"}, inn: {"role": "differential_input_n"}, "out": {"role": "single_ended_output"}}
    return d


def tele(inp, inn, nc="nc"):
    return {"topology_name": "syn_tele", "schema_version": "2.0", "supply_nets": ["vdd", "gnd"],
            "symmetry": {"matching_pairs": [], "dispositions": []},
            "netlist": [
                {"name": "M0", "kind": "nmos", "gate": "nb", "drain": "t", "source": "gnd"},
                {"name": "M1", "kind": "nmos", "gate": inp, "drain": "x", "source": "t"},
                {"name": "M2", "kind": "nmos", "gate": inn, "drain": "y", "source": "t"},
                {"name": "M3", "kind": "nmos", "gate": nc, "drain": "o1", "source": "x"},
                {"name": "M4", "kind": "nmos", "gate": nc, "drain": "o2", "source": "y"},
                {"name": "M5", "kind": "pmos", "gate": "o1", "drain": "o1", "source": "vdd"},
                {"name": "M6", "kind": "pmos", "gate": "o1", "drain": "o2", "source": "vdd"}],
            "ports": {inp: {"role": "differential_input_p"}, inn: {"role": "differential_input_n"},
                      "o2": {"role": "single_ended_output"}}}


VARS = [("sig_a", "sig_b"), ("Vip", "Vim"), ("vin_p", "vin_n"), ("Vinp", "Vinn")]

# 계약 3 합성: 포트 넷만 바꾼 4변형
c3s = {}
for mk, label in ((ota, "ota"), (tele, "tele")):
    outs = []
    for i, (a, b) in enumerate(VARS):
        p = write(mk(a, b), "c3s_%s_%d.topology.json" % (label, i))
        try:
            _, m = SD.load_topology(p)
            outs.append(json.dumps(unmap(meta_cmp(m), {a: "INP", b: "INN"}), sort_keys=True, default=str))
        except Exception as e:
            outs.append(exc(e))
    c3s[label] = {"all_same": len(set(outs)) == 1, "distinct": len(set(outs))}
res["c3_synthetic_ports_only"] = c3s

# B1 반례(참고 관찰, 계약 아님): 비포트 게이트 전용 넷 nc -> in2 (HINT_INPUT에 걸리는 이름)
try:
    pa = write(tele("sig_a", "sig_b", "nc"), "b1_nc.topology.json")
    pb = write(tele("sig_a", "sig_b", "in2"), "b1_in2.topology.json")
    _, ma = SD.load_topology(pa)
    _, mb = SD.load_topology(pb)
    A_, B_ = meta_cmp(ma), unmap(meta_cmp(mb), {"in2": "nc"})
    res["b1_nonport_gate_rename"] = {"same": A_ == B_, "diff_keys": sorted(k for k in set(A_) | set(B_) if A_.get(k) != B_.get(k))}
except Exception as e:
    res["b1_nonport_gate_rename"] = exc(e)

# 계약 4: tele + M1 vsid S1
c4 = {}
for a, b in VARS[:2]:
    d = tele(a, b)
    d["device_roles"] = {"M1": {"vertical_stack_id": "S1"}}
    p = write(d, "c4_%s.topology.json" % a)
    try:
        _, m = SD.load_topology(p)
        c4[a] = m.get("_vertical_stack_id_autofilled")
        c4[a + "__device_roles_vsid"] = {k: (v or {}).get("vertical_stack_id") for k, v in sorted((m.get("device_roles") or {}).items())}
    except Exception as e:
        c4[a] = exc(e)
res["c4"] = c4

# 계약 5: E3 -- head 시그니처 / base 시그니처(관찰)
HAS_PORTS = "ports" in inspect.signature(SR.resolve_stack_layout).parameters
c5 = {"has_ports_kw": HAS_PORTS}
for a, b in VARS:
    p = write(tele(a, b), "c5_%s.topology.json" % a)
    try:
        t, m = SD.load_topology(p)
        dr = m["device_roles"] or {}
        try:
            g = SR.resolve_stack_layout(t, [], dr, ports=m["ports"])
            c5[a] = sorted(sorted(v) for v in g.values())
        except Exception as e:
            c5[a] = exc(e)
        if not HAS_PORTS:
            g = SR.resolve_stack_layout(t, [], dr)
            c5[a + "__base_sig"] = sorted(sorted(v) for v in g.values())
    except Exception as e:
        c5[a] = exc(e)
res["c5"] = c5

# 계약 6: 거부·수용
base_ok = ota("sig_a", "sig_b")


def variant(f):
    d = copy.deepcopy(base_ok)
    f(d)
    return d


REJECT = {
    "no_key": lambda d: d.pop("ports"),
    "null": lambda d: d.__setitem__("ports", None),
    "list": lambda d: d.__setitem__("ports", ["sig_a"]),
    "item_not_dict": lambda d: d["ports"].__setitem__("sig_a", "input"),
    "no_role": lambda d: d["ports"].__setitem__("sig_a", {"direction": "input"}),
    "role_vocab": lambda d: d["ports"].__setitem__("sig_a", {"role": "differential_input"}),
    "dir_contra_in": lambda d: d["ports"].__setitem__("sig_a", {"role": "differential_input_p", "direction": "output"}),
    "dir_contra_out": lambda d: d["ports"].__setitem__("out", {"role": "single_ended_output", "direction": "input"}),
    "empty_name": lambda d: d["ports"].__setitem__("", {"role": "single_ended_input"}),
    "not_in_netlist": lambda d: d["ports"].__setitem__("zz_absent", {"role": "single_ended_input"}),
    "on_rail": lambda d: d["ports"].__setitem__("vdd", {"role": "single_ended_input"}),
}
ACCEPT = {
    "empty": lambda d: d.__setitem__("ports", {}),
    "comment_only": lambda d: d.__setitem__("ports", {"_comment": "x"}),
    "outputs_only": lambda d: d.__setitem__("ports", {"out": {"role": "single_ended_output"}}),
    "inputs_only": lambda d: d.__setitem__("ports", {"sig_a": {"role": "differential_input_p"}, "sig_b": {"role": "differential_input_n"}}),
    "with_direction_consistent": lambda d: d["ports"].__setitem__("sig_a", {"role": "differential_input_p", "direction": "input"}),
    # v2 추가(mutrun 생존 body[16]): 포트 넷이 수동소자·이상원 단자에만 있음 -> 받는다
    "port_on_passive_only": lambda d: (d.__setitem__("passive_elements", [{"name": "Rs", "kind": "resistor", "terminals": ["src", "sig_a"], "value_ohm": 1e3}]),
                                       d["ports"].__setitem__("src", {"role": "single_ended_input"})),
    "port_on_ideal_only": lambda d: (d.__setitem__("ideal_sources", [{"name": "Vs", "kind": "voltage_source", "terminals": ["vsrc", "gnd"], "value_volt": 0.9, "implementable": False}]),
                                     d["ports"].__setitem__("vsrc", {"role": "single_ended_input"})),
}
c6 = {"reject": {}, "accept": {}, "accessor_direct": {}}
for k, f in REJECT.items():
    p = write(variant(f), "c6r_%s.topology.json" % k)
    try:
        SD.load_topology(p)
        c6["reject"][k] = "ACCEPTED"
    except Exception as e:
        c6["reject"][k] = exc(e)
    if hasattr(SD, "port_declaration"):
        try:
            SD.port_declaration(variant(f))
            c6["accessor_direct"][k] = "ACCEPTED"
        except Exception as e:
            c6["accessor_direct"][k] = exc(e)
for k, f in ACCEPT.items():
    p = write(variant(f), "c6a_%s.topology.json" % k)
    try:
        _, m = SD.load_topology(p)
        c6["accept"][k] = norm(m.get("ports"))
    except Exception as e:
        c6["accept"][k] = exc(e)
# 연결 파일
lk = {}
for k, lp in (("linked_differs", {"sig_a": {"role": "differential_input_p"}}),
              ("linked_vocab", {"sig_a": {"role": "bogus"}}),
              ("linked_absent", None), ("linked_same", "SAME")):
    sub = os.path.join(TMP, "lk_" + k)
    os.makedirs(sub, exist_ok=True)
    A_ = copy.deepcopy(base_ok)
    A_["netlist"] = A_["netlist"][:3]
    B_ = copy.deepcopy(base_ok)
    B_["netlist"] = base_ok["netlist"][3:]
    A_["linked_topology_files"] = ["b.topology.json"]
    B_["linked_topology_files"] = ["a.topology.json"]
    if lp is None:
        B_.pop("ports")
    elif lp == "SAME":
        B_["ports"] = copy.deepcopy(A_["ports"])
    else:
        B_["ports"] = lp
    with open(os.path.join(sub, "a.topology.json"), "w") as fh:
        json.dump(A_, fh)
    with open(os.path.join(sub, "b.topology.json"), "w") as fh:
        json.dump(B_, fh)
    try:
        SD.load_topology(os.path.join(sub, "a.topology.json"))
        lk[k] = "ACCEPTED"
    except Exception as e:
        lk[k] = exc(e)
# v2 추가(mutrun 생존 body[13].body[2]): 연결 파일의 수동소자 단자에만 있는 포트 넷 -> 받는다
sub = os.path.join(TMP, "lk_passive")
os.makedirs(sub, exist_ok=True)
A_ = copy.deepcopy(base_ok); A_["netlist"] = A_["netlist"][:3]; A_["linked_topology_files"] = ["b.topology.json"]
A_["ports"]["src2"] = {"role": "single_ended_input"}
B_ = copy.deepcopy(base_ok); B_["netlist"] = base_ok["netlist"][3:]; B_["linked_topology_files"] = ["a.topology.json"]
B_.pop("ports")
B_["passive_elements"] = [{"name": "Rs2", "kind": "resistor", "terminals": ["src2", "sig_a"], "value_ohm": 1e3}]
with open(os.path.join(sub, "a.topology.json"), "w") as fh:
    json.dump(A_, fh)
with open(os.path.join(sub, "b.topology.json"), "w") as fh:
    json.dump(B_, fh)
try:
    _, m = SD.load_topology(os.path.join(sub, "a.topology.json"))
    lk["linked_passive_port"] = norm(m.get("ports"))
except Exception as e:
    lk["linked_passive_port"] = exc(e)
c6["linked"] = lk
res["c6"] = c6

# 계약 7: offset 쌍
c7 = {}
for k, ports in (("no_direction", None),
                 ("with_direction", {"sig_a": {"role": "differential_input_p", "direction": "input"},
                                     "sig_b": {"role": "differential_input_n", "direction": "input"},
                                     "out": {"role": "single_ended_output", "direction": "output"}}),
                 ("empty_ports_with_offset_pair", {}),
                 ):
    d = ota("sig_a", "sig_b", ports)
    d["symmetry"]["matching_pairs"] = [{"names": ["M1", "M2"], "matching_sensitivity": "offset", "current_forced": True}]
    p = write(d, "c7_%s.topology.json" % k)
    try:
        c7[k] = SR.input_referred_offset_pairs(p)
    except Exception as e:
        c7[k] = exc(e)
d = ota("sig_a", "sig_b", {})
p = write(d, "c7_empty_no_offset.topology.json")
try:
    c7["empty_ports_no_offset_pair"] = SR.input_referred_offset_pairs(p)
except Exception as e:
    c7["empty_ports_no_offset_pair"] = exc(e)
# v2 추가(mutrun 생존 len(names) >= 2): 이름 1개인 offset 항목은 쌍이 아니다
for k, ports in (("single_name_offset_empty_ports", {}), ("single_name_offset_with_inputs", None)):
    d = ota("sig_a", "sig_b", ports)
    d["symmetry"]["matching_pairs"] = [{"names": ["M1"], "matching_sensitivity": "offset", "current_forced": False}]
    p = write(d, "c7_%s.topology.json" % k)
    try:
        c7[k] = SR.input_referred_offset_pairs(p)
    except Exception as e:
        c7[k] = exc(e)
res["c7"] = c7

# 계약 8: 계수 -- orig = M.port_declaration 을 먼저 읽는 모양
c8 = {}
try:
    orig = SD.port_declaration
    n = [0]

    def wrap(t):
        n[0] += 1
        return orig(t)
    SD.port_declaration = wrap
    try:
        d = ota("sig_a", "sig_b")
        d["symmetry"]["matching_pairs"] = [{"names": ["M1", "M2"], "matching_sensitivity": "offset", "current_forced": True}]
        p = write(d, "c8.topology.json")
        seq = []
        SD.load_topology(p); seq.append(n[0])
        SR.input_referred_offset_pairs(p); seq.append(n[0])
        for _ in range(3):
            SR.input_referred_offset_pairs(p)
            SR._topology_meta_cached(p)
        seq.append(n[0])
        c8["seq"] = seq
    finally:
        SD.port_declaration = orig
except Exception as e:
    c8["exc"] = exc(e)
    c8["exc_obj_name"] = [getattr(e, "obj", None) is not None, getattr(e, "name", None)]
res["c8"] = c8

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1, default=str)
shutil.rmtree(TMP, ignore_errors=True)
print("wrote", OUT)
