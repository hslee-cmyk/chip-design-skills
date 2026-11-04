# -*- coding: utf-8 -*-
"""adapters/ngspice -- 첫 어댑터(design §8, card 20261104-op23). 이 card 몫 능력: op, ac(β 루프·CM 루프·ratio·rout·iso 는 op/ac 요청의 조합).

`tran`, `pz`, `noise`, `op_sweep`, `tf`, `mc_*` 는 선언하지 않는다(기간 동작 D-1, OP-4·OP-5 가 더한다). 어댑터는 판정하지 않는다:
판정에 필요한 분해능은 `Resolution` 으로 넘긴다. 실행 파일 경로는 생성자 인자로만 받는다(코드에 경로 없음).
"""
from __future__ import annotations

import json
import os
import re
import subprocess

from adapters.ngspice import dialect, errors, read, run as runner
from core.cache import cache_key
from core.requests import Ac, Op
from core.results import OracleError, ResultBundle, Resolution, RunStatus, canonical_sha256, lf_sha256, raw_sha256

NAME = "ngspice"
_HERE = os.path.dirname(os.path.abspath(__file__))
CAP_KEYS = ("op", "ac", "noise", "noise_device_contrib", "tran", "tran_early_stop", "pz", "op_sweep", "temperature", "tf",
            "tran_large_signal", "tran_ic_bias_only", "mc_native", "mc_keep_identity", "mc_diagnostic",
            "instance_geometry_readback", "case_insensitive_names")


def _code_fingerprint() -> str:
    """어댑터 패키지 아래 모든 파일의 (상대 POSIX 경로, LF sha256) 묶음 지문. 제외 목록(닫힌): calibration.json 의 키 wall_s_per_window,
    calibration_tools/, __pycache__/. 파일을 못 읽으면 지문 계산을 거부한다."""
    pairs = []
    for root, dirs, files in os.walk(_HERE):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "calibration_tools")]
        for fn in files:
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, _HERE).replace("\\", "/")
            try:
                with open(p, "rb") as f:
                    b = f.read()
                if rel == "calibration.json":
                    obj = json.loads(b.decode("utf-8"))
                    obj.pop("wall_s_per_window", None)
                    pairs.append((rel, canonical_sha256(obj)))
                else:
                    pairs.append((rel, lf_sha256(b)))
            except (OSError, ValueError) as e:
                raise OracleError("adapter_fingerprint_unavailable", {"why": type(e).__name__, "path": p}, "1e")
    return canonical_sha256(sorted(pairs))


class Adapter:
    name = NAME

    def __init__(self, exe, options=None):
        self.exe = str(exe)
        self.options = dict(options or {})

    # ---- 계약
    def capabilities(self) -> dict:
        caps = {k: False for k in CAP_KEYS}
        caps.update({"op": True, "ac": True, "temperature": True, "instance_geometry_readback": True,
                     "case_insensitive_names": True, "mc_enable_kinds": {}, "mc_distributions": [],
                     "geometry_unit_application": ["global_directive"], "model_families": sorted(dialect.OP_PARAM_TABLES)})
        return caps

    def calibration(self) -> dict:
        return dialect.load_calibration()

    def fingerprint(self):
        try:
            with open(self.exe, "rb") as f:
                exe_sha = raw_sha256(f.read())
        except OSError as e:
            raise OracleError("adapter_fingerprint_unavailable", {"why": type(e).__name__, "path": self.exe}, "1e")
        probe = self.calibration()["simulator_version_probe"]
        try:
            out = subprocess.run([self.exe, *probe["args"]], capture_output=True, text=True, timeout=60, errors="replace").stdout
        except (OSError, subprocess.TimeoutExpired) as e:
            raise OracleError("adapter_fingerprint_unavailable", {"why": type(e).__name__, "path": self.exe}, "1e")
        m = re.search(probe["pattern"], out)
        if m is None:
            raise OracleError("adapter_fingerprint_unavailable", {"why": "version_unreadable", "path": self.exe}, "1e")
        return {"name": NAME, "code_sha256": _code_fingerprint(), "exe_sha256": exe_sha, "sim_version": m.group(0)}

    def model_bundle(self, circuit, descriptor, cond) -> dict:
        roots = []
        for k in sorted({e.kind for e in circuit.elements if type(e).__name__ == "Mos"}):
            roots += [descriptor.source_path(inc["source"]) for inc in descriptor.doc["kinds"][k]["includes"]]
        return runner.collect_bundle(roots)

    # ---- 실행
    def _resolution(self, data_rel=None) -> Resolution:
        cal = self.calibration()["default_tolerances"]
        pick = lambda k: (float(self.options[k]), "input_options") if k in self.options else (cal[k]["value"], "adapter_declared")   # noqa: E731
        (rel, s1), (vn, s2), (ab, s3) = pick("reltol"), pick("vntol"), pick("abstol")
        src = "input_options" if s1 == s2 == s3 == "input_options" else "adapter_declared"
        return Resolution(reltol=rel, abstol={"vntol": vn, "abstol": ab}, data_rel=data_rel, source=src)

    def run(self, circuit, requests, descriptor, work_dir, timeout_s, cache_dir, compat):
        bench_id = os.path.basename(os.path.normpath(str(work_dir)))
        cond = requests[0].cond
        if cond.temp_c is None or cond.corner is None:
            raise OracleError("oracle_condition_missing", {"key": "condition"}, "2b")
        text, name_map = dialect.render(circuit, requests, descriptor, cond, self.options)
        bundle = self.model_bundle(circuit, descriptor, cond)
        fp = {"code_sha256": _code_fingerprint(), "exe_sha256": self._exe_sha()}
        adapter_fp = canonical_sha256(fp)
        key = cache_key(adapter_fp, text, [h["lf"] for h in bundle.values()], runner.ARGS, "")
        files = [dialect.data_file(r.id) for r in requests if isinstance(r, Ac)]
        rc, log, state, timed_out = runner.execute(self.exe, text, str(work_dir), files, timeout_s, cache_dir, key)
        by_request, present = {}, False
        digits = self.calibration()["data_digits"]["value"]
        if not timed_out:
            for r in requests:
                if isinstance(r, Op):
                    t = read.parse_op(log, r, circuit, name_map, descriptor, self._resolution())
                    by_request[r.id] = t
                    present = present or any(v.get("id") is not None for v in t.devices.values())
                elif isinstance(r, Ac):
                    path = os.path.join(str(work_dir), dialect.data_file(r.id))
                    fs = read.parse_ac(path, r, lambda p: self._resolution(read.data_rel(p, digits)))
                    if fs is not None:
                        by_request[r.id] = fs
                        present = True
        code, warnings = errors.classify(log, result_present=present)
        if timed_out:
            code = "sim_timeout"
        elif code is None and not present:
            code = "sim_failed_other"
        status = RunStatus(rc=rc, timed_out=timed_out, error=code, warnings=tuple(warnings), log_excerpt=tuple(errors.excerpt(log)),
                           log_path="bench.log", cache_state=state)
        return ResultBundle(bench_id=bench_id, adapter_fp=adapter_fp, descriptor_fp=descriptor.fp, status=status,
                            by_request=by_request, name_map=name_map, method="ngspice 배치 .op/.ac (wrdata 복소 열, 단위 환산은 전역 scale 지시)",
                            bundle_files=bundle)

    def _exe_sha(self) -> str:
        with open(self.exe, "rb") as f:
            return raw_sha256(f.read())
