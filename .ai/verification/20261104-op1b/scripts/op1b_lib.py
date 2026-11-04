# -*- coding: utf-8 -*-
"""card 20261104-op1b 판정 도구 라이브러리(표준 라이브러리만, 엔진·오라클·LUT import 없음).

계약 = docs/02-design/specs/20261104-op1b.interface.md 2절. 판정용 독립 구현이며 운영 경로에서 부르지 않는다.
실행 스크립트(run_op1b.py, vos_recompute.py)가 이 함수들을 부른다.
"""
import copy
import hashlib
import json
import math
import posixpath
import re


class Op1bStop(Exception):
    """멈춤 신호. reason = 사유 이름, detail = 선택 상세."""

    def __init__(self, reason, detail=None):
        super().__init__(reason, detail)
        self.reason = reason
        self.detail = detail


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _lf(b):
    return b.replace(b"\r\n", b"\n")


# ---------------------------------------------------------------- 입력 사본
def rewrite_lut_ref(old, lut_path):
    proc = old.get("process") if isinstance(old, dict) else None
    if not isinstance(proc, dict) or "lut_npz" not in proc:
        raise Op1bStop("lut_npz_absent")
    new = copy.deepcopy(old)
    new["process"]["lut_npz"] = lut_path
    return new


def provenance_shape(meta_json_text):
    if meta_json_text is None:
        return "missing"
    m = json.loads(meta_json_text).get("model_files_sha256")
    if not m:
        return "missing"
    if not isinstance(m, dict):
        return "unknown"
    vals = list(m.values())
    if all(isinstance(v, str) for v in vals):
        return "flat"
    if all(isinstance(v, dict) for v in vals):
        return "nested"
    return "unknown"


# ---------------------------------------------------------------- include 묶음
_INC_RE = re.compile(r"""^\s*\.(include|lib)\s+(?:"([^"]*)"|'([^']*)'|(\S+))(?:\s+(\S+))?""", re.I)


def _targets(text):
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("*"):
            continue
        m = _INC_RE.match(line)
        if not m:
            continue
        quoted = m.group(2) if m.group(2) is not None else m.group(3)
        path = quoted if quoted is not None else m.group(4)
        if m.group(1).lower() == "lib" and quoted is None and m.group(5) is None:
            continue  # `.lib sect` = 같은 파일 안 구획 정의, 포함 아님
        out.append(path)
    return out


def _norm(p):
    return posixpath.normpath(p.replace("\\", "/"))


def include_bundle(entries, read_bytes):
    bundle = {}
    stack = [_norm(e) for e in entries]
    stack.reverse()
    while stack:
        path = stack.pop()
        if path in bundle:
            continue
        try:
            data = read_bytes(path)
        except FileNotFoundError:
            raise Op1bStop("include_missing", path)
        bundle[path] = (_sha(_lf(data)), _sha(data))
        base = posixpath.dirname(path)
        for t in reversed(_targets(data.decode("utf-8", errors="replace"))):
            t = t.replace("\\", "/")
            stack.append(_norm(t if posixpath.isabs(t) or re.match(r"^[A-Za-z]:/", t) else posixpath.join(base, t)))
    return bundle


# ---------------------------------------------------------------- 묶음 규칙(§12.5)
def bundle_rules(records, roles, bundle, texts, model_name, aux_read):
    if not records:
        return ["lut_model_provenance_missing"], []
    reasons, raw_only = set(), []
    model_rec, aux_rec = {}, {}
    for p, s in records.items():
        role = roles.get(p, "model_file")
        if role == "model_file":
            model_rec[p] = s
        elif role == "generation_aux_input":
            aux_rec[p] = s
        else:
            raise Op1bStop("role_unknown", p)
    lf_vals = {v[0] for v in bundle.values()}
    raw_vals = {v[1] for v in bundle.values()}
    for p, s in sorted(model_rec.items()):  # (i)
        if s in lf_vals:
            continue
        if s in raw_vals:
            raw_only.append(p)
        else:
            reasons.add("model_bundle_mismatch")
    rec_vals = set(model_rec.values())
    pat = re.compile(r"^\s*\.(?:subckt|model)\s+" + re.escape(model_name) + r"(?!\w)", re.I | re.M)
    defining = [k for k, t in texts.items() if pat.search(t)]
    if not defining:  # (ii)
        reasons.add("model_bundle_mismatch")
    for k in defining:
        if k not in bundle or not (set(bundle[k]) & rec_vals):
            reasons.add("model_bundle_mismatch")
    for p, s in sorted(aux_rec.items()):  # (iii)
        data = aux_read(p)
        if data is None or s not in (_sha(data), _sha(_lf(data))):
            reasons.add("lut_aux_input_mismatch")
    return sorted(reasons), raw_only


# ---------------------------------------------------------------- 두 실행 비교
_EXCLUDED = ("cache", "stability_cache")


def comparable(sim):
    def strip(x):
        if isinstance(x, dict):
            return {k: strip(v) for k, v in x.items() if k not in _EXCLUDED}
        if isinstance(x, list):
            return [strip(v) for v in x]
        return x
    return strip(copy.deepcopy(sim))


def _esc(k):
    return str(k).replace("~", "~0").replace("/", "~1")


def _walk(a, b, ptr, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(ptr + "/" + _esc(k))
            else:
                _walk(a[k], b[k], ptr + "/" + _esc(k), out)
    elif isinstance(a, list) and isinstance(b, list):
        for i in range(max(len(a), len(b))):
            if i >= len(a) or i >= len(b):
                out.append(ptr + "/" + str(i))
            else:
                _walk(a[i], b[i], ptr + "/" + str(i), out)
    elif type(a) is not type(b):
        out.append(ptr)
    elif isinstance(a, float):
        if not (a.hex() == b.hex()):
            out.append(ptr)
    elif a != b:
        out.append(ptr)


def compare_runs(a, b):
    out = []
    _walk(comparable(a), comparable(b), "", out)
    return sorted(out)


# ---------------------------------------------------------------- 범주
def _stab(sim):
    ac = sim.get("ac")
    st = ac.get("stability") if isinstance(ac, dict) else None
    return st if isinstance(st, dict) else None


def category_present(sim, category):
    def nonempty(key):
        return bool(sim.get(key))
    if category == "op":
        return sim.get("op_ok") is True
    if category == "ac":
        ac = sim.get("ac")
        return isinstance(ac, dict) and ac.get("dc_gain_db") is not None
    if category == "rail":
        return nonempty("rail_current_A")
    if category in ("ratio", "rout"):
        return nonempty(category)
    if category == "beta_loop":
        st = _stab(sim)
        return isinstance(sim.get("loop"), dict) and st is not None and st.get("loop") == "beta_loop"
    if category == "stability":
        return _stab(sim) is not None
    if category in ("stable", "unstable"):
        st = _stab(sim)
        return st is not None and st.get("verdict") == category
    if category == "noise":
        n = sim.get("noise")
        return isinstance(n, dict) and n.get("status") != "unavailable"
    if category == "mc":
        m = sim.get("offset_mc")
        return isinstance(m, dict) and m.get("n_requested") is not None
    raise Op1bStop("category_unknown", category)


# ---------------------------------------------------------------- MC
def vos_samples(v_id, v_out, a):
    """계획 N0.1: V_os[k] = (v_out[k]-v_out[0])/a - (v_id[k]-v_id[0]), k >= 1."""
    return [(v_out[k] - v_out[0]) / a - (v_id[k] - v_id[0]) for k in range(1, len(v_out))]


# ---------------------------------------------------------------- 변환(§11.5)
def lut_files_row(old, lut_sha256, shape, meta_keys):
    if shape not in ("nested", "flat", "missing"):
        raise Op1bStop("lut_shape_unknown", shape)
    proc = old["process"]
    kinds = sorted({d["kind"] for d in old["devices"]})
    out = {}
    for kind in kinds:
        if shape != "nested":
            out[kind] = None
            continue
        sub = proc.get("models", {}).get(kind, {}).get("subckt")
        hit = [k for k in meta_keys if sub is not None and sub.endswith(k)]
        if len(hit) != 1:
            raise Op1bStop("lut_kind_key_unresolved", kind)
        out[kind] = hit[0]
    return [{"path": proc["lut_npz"], "sha256": lut_sha256, "kinds": out}]


_PROCESS_MAPPED = {"lut_npz", "models", "ngspice_exe", "diffusion", "lut_reference_width_m", "provenance"}


def convert_input(old, *, lut_files, descriptor, adapter, exe=None):
    proc = old.get("process", {})
    for k in proc:
        if k not in _PROCESS_MAPPED:
            raise Op1bStop("process_key_unmapped", k)
    exe_absent = "ngspice_exe" not in proc
    use_exe = proc.get("ngspice_exe") if not exe_absent else exe
    if use_exe is None:
        raise Op1bStop("exe_unresolved")
    tb = copy.deepcopy(old.get("testbench", {}))
    options_absent = "options" not in tb
    sim = {"exe": use_exe}
    if not options_absent:
        sim["options"] = tb.pop("options")
    sim["adapter"] = adapter
    new = copy.deepcopy(old)
    new["schema"] = "spice_oracle_input/2"
    new["process"] = {"lut_files": copy.deepcopy(lut_files), "descriptor": copy.deepcopy(descriptor)}
    new["simulator"] = sim
    new["testbench"] = tb
    record = {
        "schema": old.get("schema"),
        "diffusion": copy.deepcopy(proc.get("diffusion")),
        "lut_reference_width_m": proc.get("lut_reference_width_m"),
        "provenance": copy.deepcopy(proc.get("provenance")),
        "exe_absent": exe_absent,
        "options_absent": options_absent,
        "draft": descriptor is None,
    }
    return new, record
