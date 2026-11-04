# -*- coding: utf-8 -*-
"""core/descriptor.py -- 오라클 PDK 기술자 `oracle_pdk_descriptor/1` 읽기·검사·지문(design §10, card 20261104-op23 OP-2).

규칙
  * PDK 값은 기술자 파일과 그것이 가리키는 엔진 선언에만 있다. 이 모듈은 PDK 이름·값을 갖지 않는다(O-197).
  * 엔진을 import하지 않는다(오라클 C1). 엔진 선언 식 형식(`E/core/CONTRACT.md` §9)의 읽기를 새로 쓰되 기술자가 가리키는
    키만 푼다. 값은 사본으로 두지 않고 `quantity()`가 부를 때마다 원본 파일에서 푼다.
  * sha256 정의: 기술자 칸 = LF 정규화 값(규칙 (i)), 엔진 `sources` 기록 = LF 또는 raw(규칙 (ii), raw만이면 기계 의존 표시),
    중복 검사 = 파일 바이트를 다시 잰 LF 값끼리(규칙 (iii)).
  * 검사 순서(처음 걸린 하나만): 입력이 준 기술자 sha -> 스키마 -> 참조 sha -> 중복 -> 참조 파일 형식. 모두 stage "2".
  * 시뮬레이터 호출 0, os.environ 직접 읽기 0(env 는 인자).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from typing import Mapping

from core.results import OracleError

STAGE = "2"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


# ---------------------------------------------------------------- 해시 정의
def lf_sha256(b: bytes) -> str:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def raw_sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_sha256(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def match_recorded(recorded: str, data: bytes):
    """기록값이 LF 값과 같으면 'lf', 아니고 raw 와 같으면 'raw', 둘 다 아니면 None(계획 N3.4 규칙 (ii))."""
    if recorded == lf_sha256(data):
        return "lf"
    if recorded == raw_sha256(data):
        return "raw"
    return None


# ---------------------------------------------------------------- 위치 선언(E/lut/CONTRACT.md 1.8)
def resolve_location(doc: dict, key: str, env: Mapping):
    """위치 선언 doc[key] = {env?, default?} -> (abspath, 'env:<이름>' | 'config_default'). 칸 없음·형식 오류는 거부(LUT meta 로 돌아가지 않음)."""
    if not isinstance(doc, dict) or key not in doc:
        raise OracleError("lut_location_decl_invalid", {"item": key, "why": "missing"}, STAGE)
    ent = doc[key]
    if not isinstance(ent, dict) or not (set(ent) & {"env", "default"}) or not set(ent) <= {"env", "default"}:
        raise OracleError("lut_location_decl_invalid", {"item": key, "why": "shape"}, STAGE)
    name, default = ent.get("env"), ent.get("default")
    if (name is not None and (not isinstance(name, str) or not name)) or \
            (default is not None and (not isinstance(default, str) or not default)):
        raise OracleError("lut_location_decl_invalid", {"item": key, "why": "shape"}, STAGE)
    if name is not None and env.get(name):
        return os.path.abspath(env[name]), f"env:{name}"
    if default is None:
        raise OracleError("lut_location_decl_invalid", {"item": key, "why": "no_value"}, STAGE)
    return os.path.abspath(default), "config_default"


# ---------------------------------------------------------------- 스키마(코드 안 검사, design §10.2·J-1)
def _is_sha(v):
    return isinstance(v, str) and _HEX64.match(v) is not None


def _closed(node, ptr, required, optional, errs):
    """객체의 닫힌 키 집합 검사. 객체면 True."""
    if not isinstance(node, dict):
        errs.append({"pointer": ptr, "rule": "type"})
        return False
    for k in required:
        if k not in node:
            errs.append({"pointer": f"{ptr}/{k}", "rule": "required"})
    for k in node:
        if k not in required and k not in optional:
            errs.append({"pointer": f"{ptr}/{k}", "rule": "additionalProperties"})
    return True


def _ref(node, ptr, errs):
    if _closed(node, ptr, ("path", "sha256"), (), errs):
        if "path" in node and not (isinstance(node["path"], str) and node["path"]):
            errs.append({"pointer": f"{ptr}/path", "rule": "minLength"})
        if "sha256" in node and not _is_sha(node["sha256"]):
            errs.append({"pointer": f"{ptr}/sha256", "rule": "pattern"})


def _text_spec(node, ptr, errs, nullable=False):
    """{"value": 문자열} | {"expr": {source, regex}} (nullable 이면 None 도)."""
    if node is None and nullable:
        return
    if not isinstance(node, dict) or len(node) != 1 or not (set(node) & {"value", "expr"}):
        errs.append({"pointer": ptr, "rule": "type"})
        return
    if "value" in node:
        if not (isinstance(node["value"], str) and node["value"]):
            errs.append({"pointer": f"{ptr}/value", "rule": "minLength"})
    else:
        e = node["expr"]
        if _closed(e, f"{ptr}/expr", ("source", "regex"), (), errs):
            for k in ("source", "regex"):
                if k in e and not (isinstance(e[k], str) and e[k]):
                    errs.append({"pointer": f"{ptr}/expr/{k}", "rule": "minLength"})


def _schema_errors(doc) -> list:
    errs: list = []
    if not _closed(doc, "", ("schema", "engine_decl", "lut_record_root", "model_family", "kinds", "corners", "temperature",
                             "diffusion"), ("extra_engine_decls", "extra_sources", "lut_file_roles"), errs):
        return errs
    if doc.get("schema") != "oracle_pdk_descriptor/1":
        errs.append({"pointer": "/schema", "rule": "const"})
    if "engine_decl" in doc:
        _ref(doc["engine_decl"], "/engine_decl", errs)
    for k, v in (doc.get("extra_engine_decls") or {}).items() if isinstance(doc.get("extra_engine_decls", {}), dict) else ():
        _ref(v, f"/extra_engine_decls/{k}", errs)
    if "extra_engine_decls" in doc and not isinstance(doc["extra_engine_decls"], dict):
        errs.append({"pointer": "/extra_engine_decls", "rule": "type"})
    xs = doc.get("extra_sources", {})
    if not isinstance(xs, dict):
        errs.append({"pointer": "/extra_sources", "rule": "type"})
    else:
        for k, v in xs.items():
            p = f"/extra_sources/{k}"
            if _closed(v, p, ("path", "sha256", "base", "provenance"), (), errs):
                if "path" in v and not (isinstance(v["path"], str) and v["path"]):
                    errs.append({"pointer": f"{p}/path", "rule": "minLength"})
                if "sha256" in v and not _is_sha(v["sha256"]):
                    errs.append({"pointer": f"{p}/sha256", "rule": "pattern"})
                if "base" in v and v["base"] != "pdk_root":
                    errs.append({"pointer": f"{p}/base", "rule": "enum"})
                if "provenance" in v and not (isinstance(v["provenance"], str) and v["provenance"].strip()):
                    errs.append({"pointer": f"{p}/provenance", "rule": "minLength"})
    lr = doc.get("lut_record_root")
    if "lut_record_root" in doc and _closed(lr, "/lut_record_root", ("location_decl", "key"), (), errs):
        if "location_decl" in lr:
            _ref(lr["location_decl"], "/lut_record_root/location_decl", errs)
        if "key" in lr and not (isinstance(lr["key"], str) and lr["key"]):
            errs.append({"pointer": "/lut_record_root/key", "rule": "minLength"})
    roles = doc.get("lut_file_roles", [])
    if not isinstance(roles, list):
        errs.append({"pointer": "/lut_file_roles", "rule": "type"})
    else:
        for i, r in enumerate(roles):
            _ref(r, f"/lut_file_roles/{i}", errs)
    if "model_family" in doc and not (isinstance(doc["model_family"], str) and doc["model_family"]):
        errs.append({"pointer": "/model_family", "rule": "minLength"})
    kinds = doc.get("kinds")
    if "kinds" in doc:
        if not isinstance(kinds, dict) or not kinds:
            errs.append({"pointer": "/kinds", "rule": "minProperties"})
        else:
            for k, v in kinds.items():
                p = f"/kinds/{k}"
                if not _closed(v, p, ("call_form", "name", "inner_device", "includes", "polarity"),
                               ("geometry_unit", "parallel_multiplier"), errs):
                    continue
                if v.get("call_form") not in ("subckt_wrapper", "model_direct") and "call_form" in v:
                    errs.append({"pointer": f"{p}/call_form", "rule": "enum"})
                if "name" in v:
                    _text_spec(v["name"], f"{p}/name", errs)
                if "inner_device" in v:
                    _text_spec(v["inner_device"], f"{p}/inner_device", errs, nullable=True)
                if "polarity" in v and v["polarity"] not in ("n", "p"):
                    errs.append({"pointer": f"{p}/polarity", "rule": "enum"})
                inc = v.get("includes")
                if "includes" in v:
                    if not isinstance(inc, list) or not inc:
                        errs.append({"pointer": f"{p}/includes", "rule": "minItems"})
                    else:
                        for j, it in enumerate(inc):
                            if _closed(it, f"{p}/includes/{j}", ("source",), ("corner_section",), errs):
                                if "source" in it and not (isinstance(it["source"], str) and it["source"]):
                                    errs.append({"pointer": f"{p}/includes/{j}/source", "rule": "minLength"})
                gu = v.get("geometry_unit")
                if "geometry_unit" in v and gu != "si":
                    if _closed(gu, f"{p}/geometry_unit", ("source",), (), errs) and \
                            not (isinstance(gu.get("source"), str) and gu.get("source")):
                        errs.append({"pointer": f"{p}/geometry_unit/source", "rule": "minLength"})
                pm = v.get("parallel_multiplier")
                if "parallel_multiplier" in v and _closed(pm, f"{p}/parallel_multiplier", ("to", "source"), (), errs):
                    to = pm.get("to")
                    if not isinstance(to, list) or not to:
                        errs.append({"pointer": f"{p}/parallel_multiplier/to", "rule": "minItems"})
                    else:
                        for j, t in enumerate(to):
                            tp = f"{p}/parallel_multiplier/to/{j}"
                            if not isinstance(t, dict) or t.get("target") not in ("instance_multiplier", "model_param"):
                                errs.append({"pointer": tp, "rule": "enum"})
                            elif t["target"] == "instance_multiplier":
                                _closed(t, tp, ("target",), (), errs)
                            elif _closed(t, tp, ("target", "name"), (), errs) and "name" in t:
                                _text_spec(t["name"], f"{tp}/name", errs)
                    if "source" in pm and not isinstance(pm["source"], dict):
                        errs.append({"pointer": f"{p}/parallel_multiplier/source", "rule": "type"})
    cn = doc.get("corners")
    if "corners" in doc and _closed(cn, "/corners", ("names", "select"), (), errs):
        nm = cn.get("names")
        if "names" in cn and not (isinstance(nm, list) and nm and all(isinstance(x, str) and x for x in nm)):
            errs.append({"pointer": "/corners/names", "rule": "minItems"})
        sel = cn.get("select")
        if "select" in cn and _closed(sel, "/corners/select", ("how",), ("section",), errs) and \
                sel.get("how") not in ("include_path", "lib_section") and "how" in sel:
            errs.append({"pointer": "/corners/select/how", "rule": "enum"})
    tp = doc.get("temperature")
    if "temperature" in doc and _closed(tp, "/temperature", ("range_source",), ("tnom",), errs):
        if "range_source" in tp and tp["range_source"] != "spec":
            errs.append({"pointer": "/temperature/range_source", "rule": "const"})
        tn = tp.get("tnom")
        if "tnom" in tp:
            if not isinstance(tn, dict):
                errs.append({"pointer": "/temperature/tnom", "rule": "type"})
            else:
                for k, v in tn.items():
                    if _closed(v, f"/temperature/tnom/{k}", ("source",), (), errs) and \
                            not (isinstance(v.get("source"), str) and v.get("source")):
                        errs.append({"pointer": f"/temperature/tnom/{k}/source", "rule": "minLength"})
    df = doc.get("diffusion")
    if "diffusion" in doc and _closed(df, "/diffusion", ("decl", "ad_per_w", "as_per_w", "pd_extra", "ps_extra"), (), errs):
        for k, v in df.items():
            if not (isinstance(v, str) and v):
                errs.append({"pointer": f"/diffusion/{k}", "rule": "minLength"})
    return sorted(errs, key=lambda e: (e["pointer"], e["rule"]))


def _roles_errors(doc) -> list:
    """lut_file_roles/1 형식(design §12.5): 닫힌 키, 역할 값, evidence 일관, 생성기 근거는 commit 또는 data_path 중 하나."""
    errs: list = []
    if not _closed(doc, "", ("schema", "generator_sha256", "roles", "evidence"), (), errs):
        return errs
    if doc.get("schema") != "lut_file_roles/1":
        errs.append({"pointer": "/schema", "rule": "const"})
    if "generator_sha256" in doc and not _is_sha(doc["generator_sha256"]):
        errs.append({"pointer": "/generator_sha256", "rule": "pattern"})
    roles = doc.get("roles")
    if "roles" in doc:
        if not isinstance(roles, dict):
            errs.append({"pointer": "/roles", "rule": "type"})
        else:
            for k, v in roles.items():
                if _closed(v, f"/roles/{k}", ("sha256", "role"), (), errs):
                    if "sha256" in v and not _is_sha(v["sha256"]):
                        errs.append({"pointer": f"/roles/{k}/sha256", "rule": "pattern"})
                    if v.get("role") not in ("model_file", "generation_aux_input") and "role" in v:
                        errs.append({"pointer": f"/roles/{k}/role", "rule": "enum"})
    ev = doc.get("evidence")
    if "evidence" in doc and _closed(ev, "/evidence", ("generator", "include_graph", "measured_by", "date"), (), errs):
        g = ev.get("generator")
        if "generator" in ev and _closed(g, "/evidence/generator", ("path", "file_sha256", "matched"),
                                        ("commit", "data_path", "aux_append_lines"), errs):
            if not (g.get("commit") or g.get("data_path")):
                errs.append({"pointer": "/evidence/generator", "rule": "commit_or_data_path"})
            if "file_sha256" in g and g["file_sha256"] != doc.get("generator_sha256"):
                errs.append({"pointer": "/evidence/generator/file_sha256", "rule": "equals_generator_sha256"})
            if "matched" in g and g["matched"] not in ("lf", "raw"):
                errs.append({"pointer": "/evidence/generator/matched", "rule": "enum"})
        ig = ev.get("include_graph")
        if "include_graph" in ev:
            _closed(ig, "/evidence/include_graph", ("start", "files"), (), errs)
    return sorted(errs, key=lambda e: (e["pointer"], e["rule"]))


# ---------------------------------------------------------------- 엔진 선언 읽기(필요한 키만)
def _read(path: str):
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return None


def _decl_doc(path: str, ref: str):
    b = _read(path)
    try:
        d = json.loads(b.decode("utf-8")) if b is not None else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        d = None
    if not isinstance(d, dict) or not isinstance(d.get("sources"), dict) or not isinstance(d.get("quantities"), dict) \
            or not isinstance(d.get("pdk_root"), str):
        raise OracleError("descriptor_schema_invalid", [{"pointer": ref, "rule": "engine_decl_shape"}], STAGE)
    return d


class _Decl:
    """엔진 선언 하나(파일 + 폴더). 원본 경로·읽기·quantity 식 풀이."""

    def __init__(self, path: str, doc: dict):
        self.path, self.dir, self.doc = path, os.path.dirname(path), doc

    def src_path(self, key: str) -> str:
        s = self.doc["sources"][key]
        base = self.dir if s.get("base") == "decl_dir" else self.doc["pdk_root"]
        return os.path.abspath(os.path.join(base, s["path"]))

    def src_text(self, key: str):
        b = _read(self.src_path(key))
        if b is None:
            return None
        s = self.doc["sources"][key]
        if s.get("newline") == "lf":
            b = b.replace(b"\r\n", b"\n")
        return b.decode(s.get("encoding", "utf-8"), errors="replace")


_NAME = r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*"
_PAIR = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\{[^}]*\}|'[^']*'|[^\s(){}=']+)")
_VAL = re.compile(r"^([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)([A-Za-z]*)$")


def _instance_line_rules(decl: _Decl, src_key: str) -> dict:
    """format = spice_instance_line: 규칙 이름(소문자) -> [(값 글자, 단위 글자)]. 이 card 가 쓰는 형식은 이것 하나다."""
    s = decl.doc["sources"][src_key]
    if s.get("format") != "spice_instance_line":
        raise OracleError("descriptor_schema_invalid", [{"pointer": f"/sources/{src_key}", "rule": "quantity_format_unsupported"}], STAGE)
    text = decl.src_text(src_key)
    if text is None:
        raise OracleError("pdk_descriptor_stale", {"ref": f"engine_source:{src_key}", "path": decl.src_path(src_key),
                                                   "expected_sha256": s.get("sha256"), "actual_sha256": "missing"}, STAGE)
    pat = re.compile(s["line_pattern"])
    out: dict = {}
    for line in text.splitlines():
        m = pat.search(line)
        if not m:
            continue
        body = m.group(1) if m.groups() else m.group(0)
        for k, v in _PAIR.findall(body):
            vm = _VAL.match(v)
            out.setdefault(k.lower(), []).append((vm.group(1), vm.group(2).lower()) if vm else (v, ""))
    return out


def _eval_expr(expr: str, rules: dict, units: dict, where: str) -> float:
    """quantity 식: 수, + - * /, 단항 -, 괄호, max/min, 규칙 이름."""
    toks = re.findall(rf"\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+|{_NAME}|[-+*/(),]", expr)
    pos = [0]

    def bad(why):
        raise OracleError("descriptor_schema_invalid", [{"pointer": where, "rule": why}], STAGE)

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def eat(t=None):
        x = peek()
        if x is None or (t is not None and x != t):
            bad("expression_invalid")
        pos[0] += 1
        return x

    def atom():
        t = eat()
        if t == "(":
            v = add()
            eat(")")
            return v
        if t == "-":
            return -atom()
        if t in ("max", "min"):
            eat("(")
            args = [add()]
            while peek() == ",":
                eat(",")
                args.append(add())
            eat(")")
            return max(args) if t == "max" else min(args)
        if re.fullmatch(r"\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+", t):
            return float(t)
        hits = rules.get(t.lower())
        if not hits:
            bad("rule_missing")
        if len(set(hits)) != 1:
            bad("rule_ambiguous")
        txt, unit = hits[0]
        if unit not in units:
            bad("rule_unit_unknown")
        try:
            return float(txt) * float(units[unit])
        except ValueError:
            bad("rule_not_numeric")

    def mul():
        v = atom()
        while peek() in ("*", "/"):
            op = eat()
            r = atom()
            if op == "/" and r == 0:
                bad("expression_invalid")
            v = v * r if op == "*" else v / r
        return v

    def add():
        v = mul()
        while peek() in ("+", "-"):
            op = eat()
            r = mul()
            v = v + r if op == "+" else v - r
        return v

    v = add()
    if peek() is not None:
        bad("expression_invalid")
    return v


# ---------------------------------------------------------------- Descriptor
@dataclass(frozen=True)
class Descriptor:
    path: str
    doc: dict
    fp: str
    record_root: str
    record_root_source: str
    machine_dependent_refs: tuple
    roles_docs: tuple = ()
    _decls: dict = field(default_factory=dict, repr=False, compare=False)       # {"main": _Decl, "extra": {key: _Decl}}
    _extra_src: dict = field(default_factory=dict, repr=False, compare=False)   # {key: 절대 경로}

    def source_path(self, key: str) -> str:
        """엔진 `sources` 키 또는 `extra_sources` 키의 원본 절대 경로."""
        if key in self._extra_src:
            return self._extra_src[key]
        main = self._decls["main"]
        if key in main.doc["sources"]:
            return main.src_path(key)
        raise OracleError("descriptor_schema_invalid", [{"pointer": f"/sources/{key}", "rule": "source_undeclared"}], STAGE)

    def source_text(self, key: str) -> str:
        b = _read(self.source_path(key))
        if b is None:
            raise OracleError("sim_model_not_found", {"source": key, "path": self.source_path(key)}, STAGE)
        main = self._decls["main"]
        enc = main.doc["sources"].get(key, {}).get("encoding", "utf-8")
        return b.replace(b"\r\n", b"\n").decode(enc, errors="replace")

    def quantity(self, key: str) -> float:
        """엔진 선언 quantity 를 원본에서 푼다(사본 없음). 주 선언을 먼저, 없으면 extra 선언."""
        decls = [self._decls["main"], *self._decls["extra"].values()]
        for d in decls:
            q = d.doc["quantities"].get(key)
            if q is None:
                continue
            rules = _instance_line_rules(d, q["source"])
            return _eval_expr(q["expression"], rules, d.doc["sources"][q["source"]].get("units_m", {}), f"/quantities/{key}")
        raise OracleError("descriptor_schema_invalid", [{"pointer": f"/quantities/{key}", "rule": "quantity_undeclared"}], STAGE)

    def text(self, spec: dict) -> str:
        """{"value": s} 또는 {"expr": {source, regex}} -> 문자열(식은 원본 파일에서 풀고, 못 찾으면 거부)."""
        if "value" in spec:
            return spec["value"]
        e = spec["expr"]
        body = self.source_text(e["source"])
        m = re.search(e["regex"], body, re.M | re.I)
        if m is None:
            raise OracleError("descriptor_schema_invalid", [{"pointer": f"expr:{e['source']}", "rule": "expr_unmatched"}], STAGE)
        return m.group(1) if m.groups() else m.group(0)


def _resolve(base_dir: str, p: str) -> str:
    return os.path.abspath(p if os.path.isabs(p) else os.path.join(base_dir, p))


def _stale(ref, path, expected, actual):
    return OracleError("pdk_descriptor_stale", {"ref": ref, "path": path, "expected_sha256": expected, "actual_sha256": actual}, STAGE)


def _used_engine_sources(doc: dict, main: _Decl) -> list:
    """기술자가 쓰는 엔진 `sources` 키(규칙 (ii) 대상). includes·식 source·quantity 가 가리키는 source."""
    keys: list = []

    def add(k):
        if k in main.doc["sources"] and k not in keys:
            keys.append(k)
    for kd in doc["kinds"].values():
        for s in (kd["name"], kd.get("inner_device")):
            if s and "expr" in s:
                add(s["expr"]["source"])
        for t in (kd.get("parallel_multiplier") or {}).get("to", []):
            if isinstance(t.get("name"), dict) and "expr" in t["name"]:
                add(t["name"]["expr"]["source"])
        pms = (kd.get("parallel_multiplier") or {}).get("source") or {}
        if isinstance(pms.get("expr"), dict):
            add(pms["expr"].get("source"))
        for it in kd["includes"]:
            add(it["source"])
        gu = kd.get("geometry_unit")
        if isinstance(gu, dict) and gu["source"] in main.doc["quantities"]:
            add(main.doc["quantities"][gu["source"]]["source"])
    for t in (doc["temperature"].get("tnom") or {}).values():
        if t["source"] in main.doc["quantities"]:
            add(main.doc["quantities"][t["source"]]["source"])
    return keys


def load_descriptor(path, *, env: Mapping, expected_lf_sha256: str | None = None) -> Descriptor:
    path = os.path.abspath(str(path))
    base = os.path.dirname(path)
    raw = _read(path)
    if raw is None:
        raise OracleError("descriptor_schema_invalid", [{"pointer": "", "rule": "file_missing"}], STAGE)
    me = lf_sha256(raw)
    # 0. 입력이 준 기술자 sha
    if expected_lf_sha256 is not None and expected_lf_sha256 != me:
        raise _stale("input_descriptor", path, expected_lf_sha256, me)
    # 1. 스키마
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise OracleError("descriptor_schema_invalid", [{"pointer": "", "rule": "json_parse"}], STAGE)
    errs = _schema_errors(doc)
    if errs:
        raise OracleError("descriptor_schema_invalid", errs, STAGE)

    # 2. 참조 sha(규칙 (i): LF 값만) -- 기술자가 가리키는 파일을 한 번에 대조한다
    def check_ref(ref_name, ent):
        p = _resolve(base, ent["path"])
        b = _read(p)
        actual = "missing" if b is None else lf_sha256(b)
        if actual != ent["sha256"]:
            raise _stale(ref_name, p, ent["sha256"], actual)
        return p, b

    ep, eb = check_ref("engine_decl", doc["engine_decl"])
    decls_lf = [lf_sha256(eb)]
    extra_paths = {}
    for k, ent in (doc.get("extra_engine_decls") or {}).items():
        p, b = check_ref(f"extra_engine_decl:{k}", ent)
        extra_paths[k] = p
        decls_lf.append(lf_sha256(b))
    main = _Decl(ep, _decl_doc(ep, "/engine_decl"))
    extras = {k: _Decl(p, _decl_doc(p, f"/extra_engine_decls/{k}")) for k, p in extra_paths.items()}
    # 엔진 `sources` 가운데 기술자가 쓰는 키(규칙 (ii): LF 또는 raw, newline=lf 항목은 LF 만)
    mdep: list = []
    for k in _used_engine_sources(doc, main):
        s = main.doc["sources"][k]
        p = main.src_path(k)
        b = _read(p)
        if b is None:
            raise _stale(f"engine_source:{k}", p, s["sha256"], "missing")
        if s.get("newline") == "lf":
            got = "lf" if lf_sha256(b) == s["sha256"] else None
        else:
            got = match_recorded(s["sha256"], b)
        if got is None:
            raise _stale(f"engine_source:{k}", p, s["sha256"], {"lf": lf_sha256(b), "raw": raw_sha256(b)})
        if got == "raw":
            mdep.append({"ref": f"engine_source:{k}", "path": p, "recorded_sha256": s["sha256"], "matched": "raw"})
    extra_lf: dict = {}
    extra_src: dict = {}
    for k, ent in (doc.get("extra_sources") or {}).items():
        p = os.path.abspath(os.path.join(main.doc["pdk_root"], ent["path"]))
        b = _read(p)
        actual = "missing" if b is None else lf_sha256(b)
        if actual != ent["sha256"]:
            raise _stale(f"extra_source:{k}", p, ent["sha256"], actual)
        extra_lf[k], extra_src[k] = actual, p
    lp, lb = check_ref("lut_location_decl", doc["lut_record_root"]["location_decl"])
    roles_files = []
    for i, ent in enumerate(doc.get("lut_file_roles") or []):
        roles_files.append(check_ref(f"lut_file_roles[{i}]", ent))

    # 3. 중복(규칙 (iii)): 경로, 그리고 파일 바이트를 다시 잰 LF 값. 엔진 `sources` 는 기술자가 안 쓰는 것까지 전부
    norm = lambda p: os.path.normcase(os.path.abspath(p))   # noqa: E731
    eng_paths = {k: main.src_path(k) for k in main.doc["sources"]}
    seen_paths = {norm(p): ("engine", k) for k, p in eng_paths.items()}
    for k, p in extra_src.items():
        if norm(p) in seen_paths:
            raise OracleError("descriptor_source_duplicated", {"why": "path", "path": p, "engine_source_key": seen_paths[norm(p)][1],
                                                              "extra_source_key": k}, STAGE)
        seen_paths[norm(p)] = ("extra", k)
    lf_owner: dict = {}
    for k, p in eng_paths.items():
        b = _read(p)
        if b is None:
            raise OracleError("descriptor_source_duplicated", {"why": "file_missing", "engine_source_key": k, "path": p}, STAGE)
        lf_owner.setdefault(lf_sha256(b), ("engine", k))
    for k, h in extra_lf.items():
        if h in lf_owner:
            raise OracleError("descriptor_source_duplicated", {"why": "sha", "lf_sha256": h, "owner": list(lf_owner[h]),
                                                              "extra_source_key": k}, STAGE)
        lf_owner[h] = ("extra", k)

    # 4. 참조 파일 형식
    try:
        locdoc = json.loads(lb.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise OracleError("lut_location_decl_invalid", {"item": "file", "why": "json_parse"}, STAGE)
    if not isinstance(locdoc, dict) or locdoc.get("schema") != "gmid_lut_location/1":
        raise OracleError("lut_location_decl_invalid", {"item": "schema", "why": "not_gmid_lut_location/1"}, STAGE)
    rroot, rsrc = resolve_location(locdoc, doc["lut_record_root"]["key"], env)
    roles_docs = []
    for i, (p, b) in enumerate(roles_files):
        try:
            rd = json.loads(b.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise OracleError("lut_file_roles_invalid", [{"pointer": f"lut_file_roles[{i}]", "rule": "json_parse"}], STAGE)
        e2 = _roles_errors(rd)
        if e2:
            raise OracleError("lut_file_roles_invalid", e2, STAGE)
        roles_docs.append(rd)
    _check_cross(doc, main, extras, extra_src)
    desc = Descriptor(path=path, doc=doc, fp="", record_root=rroot, record_root_source=rsrc,
                      machine_dependent_refs=tuple(mdep), roles_docs=tuple(roles_docs),
                      _decls={"main": main, "extra": extras}, _extra_src=extra_src)
    for kd in doc["kinds"].values():           # 식은 원본에서 풀려야 한다(못 풀면 형식 오류)
        for spec in (kd["name"], kd.get("inner_device")):
            if spec:
                desc.text(spec)
        pms = (kd.get("parallel_multiplier") or {}).get("source") or {}
        if "expr" in pms:
            if re.search(pms["expr"]["regex"], desc.source_text(pms["expr"]["source"]), re.M | re.I) is None:
                raise OracleError("descriptor_schema_invalid", [{"pointer": f"expr:{pms['expr']['source']}", "rule": "expr_unmatched"}], STAGE)
        for t in (kd.get("parallel_multiplier") or {}).get("to", []):
            if isinstance(t.get("name"), dict):
                desc.text(t["name"])
    fp = canonical_sha256({"descriptor": me, "engine_decls": sorted(decls_lf), "extra_files": sorted(extra_lf.values())})
    return Descriptor(path=path, doc=doc, fp=fp, record_root=rroot, record_root_source=rsrc,
                      machine_dependent_refs=tuple(mdep), roles_docs=tuple(roles_docs),
                      _decls={"main": main, "extra": extras}, _extra_src=extra_src)


def _check_cross(doc, main: _Decl, extras: dict, extra_src: dict):
    """칸끼리의 교차 참조(includes 키·quantity 키·diffusion.decl)가 실제로 있는지."""
    errs = []
    all_q = set(main.doc["quantities"])
    for d in extras.values():
        all_q |= set(d.doc["quantities"])
    for kn, kd in doc["kinds"].items():
        for j, it in enumerate(kd["includes"]):
            if it["source"] not in main.doc["sources"] and it["source"] not in extra_src:
                errs.append({"pointer": f"/kinds/{kn}/includes/{j}/source", "rule": "source_undeclared"})
        gu = kd.get("geometry_unit")
        if isinstance(gu, dict) and gu["source"] not in all_q:
            errs.append({"pointer": f"/kinds/{kn}/geometry_unit/source", "rule": "quantity_undeclared"})
    for kn, t in (doc["temperature"].get("tnom") or {}).items():
        if kn not in doc["kinds"]:
            errs.append({"pointer": f"/temperature/tnom/{kn}", "rule": "kind_undeclared"})
        if t["source"] not in all_q:
            errs.append({"pointer": f"/temperature/tnom/{kn}/source", "rule": "quantity_undeclared"})
    df = doc["diffusion"]
    if df["decl"] not in extras:
        errs.append({"pointer": "/diffusion/decl", "rule": "extra_engine_decl_undeclared"})
    else:
        for k in ("ad_per_w", "as_per_w", "pd_extra", "ps_extra"):
            if df[k] not in extras[df["decl"]].doc["quantities"]:
                errs.append({"pointer": f"/diffusion/{k}", "rule": "quantity_undeclared"})
    if errs:
        raise OracleError("descriptor_schema_invalid", sorted(errs, key=lambda e: (e["pointer"], e["rule"])), STAGE)
