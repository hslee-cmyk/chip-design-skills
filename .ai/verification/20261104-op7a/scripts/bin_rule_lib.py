"""card 20261104-op7a: bin 경계 규칙 선언(lut_bin_rule/1) 순수 함수 모음.

interface card 20261104-op7a.interface.md 3절 시그니처. 표준 라이브러리만 쓴다. 엔진·오라클·LUT를 import하지 않는다.
소속 비교는 격자 정수(round(x/grid))끼리만 한다. 판정을 못 내면 BinRuleStop으로 멈춘다(fail-closed).
"""
import hashlib
import math

SCHEMA = "lut_bin_rule/1"
SOURCE_BASIS = "generator_record"
_RULES = ("lower", "upper")
_SHOWMOD_KEYS = ("lmin", "lmax", "wmin", "wmax")
_HEX = frozenset("0123456789abcdef")


class BinRuleStop(Exception):
    def __init__(self, reason, detail=None):
        super().__init__(reason, detail)
        self.reason = reason
        self.detail = detail


def grid_index(x_m, grid_m):
    return round(x_m / grid_m)


def _span(b, grid_m):
    return (grid_index(b["lmin"], grid_m), grid_index(b["lmax"], grid_m),
            grid_index(b["wmin"], grid_m), grid_index(b["wmax"], grid_m))


def anchor_set(axes, grid_m):
    seen = {}
    for ax in axes:
        for x in ax:
            seen.setdefault(grid_index(x, grid_m), x)
    return tuple(seen[k] for k in sorted(seen))


def tie_axes(l_m, w_m, bins, grid_m):
    li, wi = grid_index(l_m, grid_m), grid_index(w_m, grid_m)
    sp = [_span(b, grid_m) for b in bins]
    out = []
    # L 동률: W를 품는 두 bin a, b가 a.lmax = b.lmin = l
    lo_w = [s for s in sp if s[2] <= wi <= s[3]]
    if any(a[1] == li for a in lo_w) and any(b[0] == li for b in lo_w):
        out.append("L")
    lo_l = [s for s in sp if s[0] <= li <= s[1]]
    if any(a[3] == wi for a in lo_l) and any(b[2] == wi for b in lo_l):
        out.append("W")
    return tuple(sorted(out))


def point_direction(l_m, w_m, chosen, bins, grid_m):
    li, wi = grid_index(l_m, grid_m), grid_index(w_m, grid_m)
    c = _span(chosen, grid_m)
    if not (c[0] <= li <= c[1] and c[2] <= wi <= c[3]):
        raise BinRuleStop("bin_outside", chosen.get("model"))
    res = {}
    for ax in tie_axes(l_m, w_m, bins, grid_m):
        lo, hi, x = (c[0], c[1], li) if ax == "L" else (c[2], c[3], wi)
        if lo == hi == x:
            raise BinRuleStop("tie_interior", chosen.get("model"))
        if hi == x:
            res[ax] = "lower"
        elif lo == x:
            res[ax] = "upper"
        else:
            raise BinRuleStop("tie_interior", chosen.get("model"))
    return res


def derive_rule(directions):
    vals = {v for d in directions for v in d.values()}
    if not vals:
        return None, "no_tie_point"
    if len(vals) == 1:
        return next(iter(vals)), None
    return None, "mixed_direction"


def union_model_sha(records, read_bytes):
    lf_vals, machine = set(), set()
    for path, rec in records:
        try:
            b = read_bytes(path)
        except FileNotFoundError:
            raise BinRuleStop("record_file_missing", path)
        lf = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()
        raw = hashlib.sha256(b).hexdigest()
        if rec == lf:
            pass
        elif rec == raw:
            machine.add(path)
        else:
            raise BinRuleStop("record_sha_mismatch", path)
        lf_vals.add(lf)
    return sorted(lf_vals), sorted(machine)


def split_version(text):
    name, sep, ver = text.rpartition("-")
    if not sep or not name or not ver:
        raise BinRuleStop("simulator_version_unparsed", text)
    return name, ver


def set_versions(by_set):
    vers = {split_version(v) for v in by_set.values() if v is not None}
    unrecorded = tuple(sorted(k for k, v in by_set.items() if v is None))
    if not vers:
        raise BinRuleStop("simulator_version_unrecorded")
    if len(vers) > 1:
        raise BinRuleStop("simulator_version_mixed", sorted(vers))
    return next(iter(vers)), unrecorded


def spiceinit_sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_decl(model_files_sha256, simulator, mode, spiceinit_text, rule, points, date):
    return {
        "schema": SCHEMA,
        "model_files_sha256": list(model_files_sha256),
        "simulator": {"name": simulator[0], "version": simulator[1]},
        "compat": {"mode": mode, "spiceinit_text": spiceinit_text,
                   "spiceinit_sha256": spiceinit_sha(spiceinit_text)},
        "rule": rule,
        "evidence": {"points": [{"L": l, "W": w, "chosen_bin": m} for l, w, m in points],
                     "mode": mode, "source_basis": SOURCE_BASIS, "measured_by": "verifier", "date": date},
    }


def _is_hex64(s):
    return isinstance(s, str) and len(s) == 64 and set(s) <= _HEX


def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _keys(d, expected):
    return isinstance(d, dict) and set(d) == set(expected)


def validate_decl(d):
    if not isinstance(d, dict):
        return [""]
    bad = set()
    top = ("schema", "model_files_sha256", "simulator", "compat", "rule", "evidence")
    for k in d:
        if k not in top:
            bad.add("/" + str(k))
    for k in top:
        if k not in d:
            bad.add("/" + k)
    if "schema" in d and d["schema"] != SCHEMA:
        bad.add("/schema")
    if "model_files_sha256" in d:
        m = d["model_files_sha256"]
        if not (isinstance(m, list) and m and all(_is_hex64(s) for s in m)
                and all(m[i] < m[i + 1] for i in range(len(m) - 1))):
            bad.add("/model_files_sha256")
    if "simulator" in d:
        s = d["simulator"]
        if not (_keys(s, ("name", "version")) and all(isinstance(s[k], str) and s[k] for k in s)):
            bad.add("/simulator")
    cmode = None
    if "compat" in d:
        c = d["compat"]
        if not _keys(c, ("mode", "spiceinit_text", "spiceinit_sha256")):
            bad.add("/compat")
        else:
            if not (isinstance(c["mode"], str) and c["mode"]):
                bad.add("/compat/mode")
            else:
                cmode = c["mode"]
            if not isinstance(c["spiceinit_text"], str):
                bad.add("/compat/spiceinit_text")
            elif c["spiceinit_sha256"] != spiceinit_sha(c["spiceinit_text"]):
                bad.add("/compat/spiceinit_sha256")
    if "rule" in d and d["rule"] not in _RULES:
        bad.add("/rule")
    if "evidence" in d:
        e = d["evidence"]
        if not (isinstance(e, dict) and set(e) - {"source_basis"} == {"points", "mode", "measured_by", "date"}):
            bad.add("/evidence")
        else:
            if e.get("source_basis") != SOURCE_BASIS:
                bad.add("/evidence/source_basis")
            p = e["points"]
            if not (isinstance(p, list) and p):
                bad.add("/evidence/points")
            else:
                for i, pt in enumerate(p):
                    if not (_keys(pt, ("L", "W", "chosen_bin")) and _is_num(pt["L"]) and _is_num(pt["W"])
                            and isinstance(pt["chosen_bin"], str) and pt["chosen_bin"]):
                        bad.add(f"/evidence/points/{i}")
            if e["mode"] != cmode or cmode is None:
                bad.add("/evidence/mode")
            if e["measured_by"] != "verifier":
                bad.add("/evidence/measured_by")
            if not (isinstance(e["date"], str) and e["date"]):
                bad.add("/evidence/date")
    return sorted(bad)


def isolated_env(env, home_dir):
    out = dict(env)
    for k in ("HOMEDRIVE", "HOMEPATH", "SPICE_USERINIT_DIR"):
        out.pop(k, None)
    out["HOME"] = home_dir
    out["USERPROFILE"] = home_dir
    return out


def judge_controls(default_rule, cwd_rule, home_rule):
    if default_rule is None:
        return "stop", "default_undetermined"
    if cwd_rule is None or home_rule is None:
        return "stop", "control_undetermined"
    if cwd_rule == default_rule:
        return "stop", "control_not_discriminating"
    if home_rule == default_rule:
        return "ok", "home_not_read"
    if home_rule == cwd_rule:
        return "ok", "home_read_isolated"
    return "stop", "control_undetermined"


def judge_empty_init(default_bins, empty_bins):
    if default_bins == empty_bins:
        return "ok", None
    return "stop", "control_undetermined"


def w_boundary_points(bins, grid_m):
    found = {}
    sp = [(b, _span(b, grid_m)) for b in bins]
    for a, sa in sp:
        for b, sb in sp:
            if a is b or sa[3] != sb[2]:
                continue
            if sa[0] == sb[0] and sa[1] == sb[1]:
                l_idx = round((a["lmin"] + a["lmax"]) / (2 * grid_m))
                if l_idx == sa[0] or l_idx == sa[1]:
                    raise BinRuleStop("w_boundary_no_interior", (a["model"], b["model"]))
                found[(sa[3], l_idx)] = (l_idx * grid_m, a["wmax"])
            elif min(sa[1], sb[1]) - max(sa[0], sb[0]) > 0:
                raise BinRuleStop("w_boundary_not_product", (a["model"], b["model"]))
    return tuple(found[k] for k in sorted(found))


def _parse_um_key(k):
    try:
        v = float(k)
    except (TypeError, ValueError):
        raise BinRuleStop("source_record_missing", k)
    if not math.isfinite(v):
        raise BinRuleStop("source_record_missing", k)
    return v * 1e-6


def slice_tie_cells(l_axis_m, w_m, per_l, measured, bins, grid_m):
    if not isinstance(per_l, dict):
        raise BinRuleStop("source_record_missing", "model_bin_per_L")
    by_idx = {}
    for k, v in per_l.items():
        if not isinstance(v, str):
            raise BinRuleStop("source_record_missing", k)
        i = grid_index(_parse_um_key(k), grid_m)
        if i in by_idx:
            raise BinRuleStop("source_record_missing", k)
        by_idx[i] = v
    wi = grid_index(w_m, grid_m)
    out = []
    for l in l_axis_m:
        if not tie_axes(l, w_m, bins, grid_m):
            continue
        li = grid_index(l, grid_m)
        d, h = measured.get((li, wi), (None, None))
        out.append({"l_m": l, "w_m": w_m, "recorded": by_idx.get(li), "default": d, "hsa": h})
    return out


def record_source_mode(cells, declared):
    if not cells:
        raise BinRuleStop("source_no_tie_cell")
    modes = set()
    for c in cells:
        r, d, h = c["recorded"], c["default"], c["hsa"]
        if r is None:
            raise BinRuleStop("source_record_missing", c)
        if d is None or h is None:
            raise BinRuleStop("source_cell_unmeasured", c)
        if r == d == h:
            raise BinRuleStop("source_record_both_modes", c)
        if r == d:
            modes.add("default")
        elif r == h:
            modes.add("hsa")
        else:
            raise BinRuleStop("source_record_no_mode", c)
    if len(modes) > 1:
        raise BinRuleStop("source_record_mixed", sorted(modes))
    mode = next(iter(modes))
    if mode != declared:
        raise BinRuleStop("source_mode_differs", (mode, declared))
    return mode


def combined_bin_check(recorded, measured):
    if not isinstance(recorded, dict) or not recorded:
        raise BinRuleStop("combined_bin_missing")
    for k, cell in recorded.items():
        if not isinstance(cell, dict) or not isinstance(cell.get("model"), str):
            raise BinRuleStop("combined_bin_unparsed", k)
        if k not in measured:
            raise BinRuleStop("combined_bin_unmeasured", k)
        if cell["model"] != measured[k]:
            raise BinRuleStop("combined_bin_differs", (k, cell["model"], measured[k]))


def cap_bind_check(recorded, pinned):
    if recorded is None or pinned is None:
        raise BinRuleStop("cap_bind_missing")
    if recorded != pinned:
        raise BinRuleStop("cap_bind_differs", (recorded, pinned))


def record_only_files(reached, recorded):
    if not reached or not isinstance(recorded, dict) or not recorded:
        raise BinRuleStop("include_not_recorded")
    rec_vals = set(recorded.values())
    reached_vals = set()
    for path, (lf, raw) in reached.items():
        if lf not in rec_vals and raw not in rec_vals:
            raise BinRuleStop("include_not_recorded", path)
        reached_vals.update((lf, raw))
    return tuple(sorted(p for p, v in recorded.items() if v not in reached_vals))


def netlist_lines(subckt, includes, points):
    out = [f"* bin probe {subckt}", *includes,
           "vgs g 0 dc 0", "vds d 0 dc 0", "vsrc s 0 dc 0", "vb b 0 dc 0"]
    for i, (l_um, w_um) in enumerate(points):
        out.append(f"xp{i} d g s b {subckt} l={l_um:g}u w={w_um:g}u")
    out += [".control", "op"]
    for i in range(len(points)):
        out += [f"echo SHOWMOD p{i}", f"showmod m.xp{i}.m{subckt} : " + " ".join(_SHOWMOD_KEYS)]
    out += ["quit", ".endc", ".end"]
    return out


def parse_probe_log(text, bins, grid_m):
    spans = [(b["model"], _span(b, grid_m)) for b in bins]
    out, tag, cur = {}, None, {}

    def close():
        if len(cur) != len(_SHOWMOD_KEYS):
            raise BinRuleStop("showmod_incomplete", tag)
        key = tuple(grid_index(cur[k], grid_m) for k in _SHOWMOD_KEYS)
        hit = [m for m, s in spans if s == key]
        if not hit:
            raise BinRuleStop("showmod_bin_unmatched", (tag, key))
        if len(hit) > 1:
            raise BinRuleStop("showmod_bin_ambiguous", (tag, hit))
        out[tag] = hit[0]

    for ln in text.splitlines():
        s = ln.split()
        if len(s) == 2 and s[0] == "SHOWMOD":
            if tag is not None:
                close()
            tag, cur = s[1], {}
        elif tag is not None and len(s) == 2 and s[0] in _SHOWMOD_KEYS:
            try:
                cur[s[0]] = float(s[1])
            except ValueError:
                raise BinRuleStop("showmod_incomplete", tag)
    if tag is not None:
        close()
    return out
