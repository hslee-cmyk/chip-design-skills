"""stub 어댑터(test 작성자 소유, D §3.3). 이 card 몫은 op·ac 뿐이다(interface §1 'stub').

코어 interface(D §4~§8)만 보고 쓴다. MOS 는 생성자에 준 `devices = {이름: {gm, gds}}` 로 선형 스탬프하고(입력
`predictions.devices` 와 같은 값을 test 가 준다), 나머지는 MNA 해석해다. 기대값의 정본은 test 의 손 유도이지 이 파일이 아니다.

해석(interface 가 모호해 정함):
  * S-1 `fingerprint()` 는 키 `name`·`code_sha256`·`exe_sha256`·`sim_version` 을 가진 사전(속성 접근도 됨).
  * S-2 결과 `values` 의 키는 `core.requests.expr_key(expr)` 가 있으면 그것, 없으면 `repr(expr)`.
  * S-3 캐시: 디스크 `cache_dir/<core.cache.cache_key(...)>.pkl`. 첫 실행 'miss', 다음 'hit', `cache_dir=None` 이면 None,
    시간 초과 실행은 저장하지 않는다(D §9).
"""
from __future__ import annotations

import hashlib
import pickle
from pathlib import Path

import numpy as np

GROUND = ("0", "gnd")
CAP_KEYS = ("op", "ac", "noise", "noise_device_contrib", "tran", "tran_early_stop", "pz", "op_sweep", "temperature", "tf",
            "tran_large_signal", "tran_ic_bias_only", "mc_native", "mc_keep_identity", "mc_diagnostic",
            "instance_geometry_readback", "case_insensitive_names")


class _Fp(dict):
    __getattr__ = dict.__getitem__


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class StubAdapter:
    name = "stub"

    def __init__(self, devices=None, *, geometry_application=(), calibration_extra=None, caps_extra=None,
                 case_insensitive=False):
        self.devices = devices or {}
        self.calls = []                 # run 호출 기록(시뮬레이터 호출 0 단언용)
        self.force_timeout = False
        self._geometry_application = list(geometry_application)
        self._calibration_extra = dict(calibration_extra or {})
        self._caps_extra = dict(caps_extra or {})
        self._case_insensitive = case_insensitive

    # ---- 계약
    def capabilities(self) -> dict:
        caps = {k: False for k in CAP_KEYS}
        caps.update({"op": True, "ac": True, "case_insensitive_names": self._case_insensitive,
                     "mc_enable_kinds": {}, "mc_distributions": [],
                     "geometry_unit_application": list(self._geometry_application), "model_families": ["toy"]})
        caps.update(self._caps_extra)
        return caps

    def calibration(self) -> dict:
        c = {"default_tolerances": {k: {"value": v, "source": "stub: 합성 해석해 허용오차(test 작성자 선언)"}
                                    for k, v in (("reltol", 1e-4), ("vntol", 1e-7), ("abstol", 1e-13))},
             "data_digits": {"value": 12, "source": "stub: 해석해라 자릿수 제한 없음(test 선언)"},
             "simulator_version_probe": {"how": "none", "source": "stub"}}
        c.update(self._calibration_extra)
        return c

    def fingerprint(self):
        return _Fp(name="stub", code_sha256=_sha(b"stub-adapter-v1"), exe_sha256=_sha(b"stub-exe"), sim_version="stub-1")

    def model_bundle(self, circuit, descriptor, cond) -> dict:
        kinds = sorted({e.kind for e in circuit.elements if type(e).__name__ == "Mos"})
        out = {}
        for k in kinds:
            for inc in descriptor.doc["kinds"][k]["includes"]:
                p = Path(descriptor.source_path(inc["source"]))
                b = p.read_bytes()
                out[str(p.resolve())] = {"lf": _sha(b.replace(b"\r\n", b"\n")), "raw": _sha(b)}
        return out

    # ---- 실행
    def run(self, circuit, requests, descriptor, work_dir, timeout_s, cache_dir, compat):
        from core import results
        from core.cache import cache_key
        self.calls.append((circuit, requests))
        fp = self.fingerprint()
        bundle = self.model_bundle(circuit, descriptor, requests[0].cond)
        state, by_request, status_kw = None, None, {}
        if cache_dir is not None:
            key = cache_key(fp["code_sha256"], repr((circuit, requests)), sorted(v["lf"] for v in bundle.values()),
                            ("-b",), "")
            slot = Path(cache_dir) / f"{key}.pkl"
            if slot.exists() and not self.force_timeout:
                by_request = pickle.loads(slot.read_bytes())
                state = "hit"
            else:
                state = "miss"
        if self.force_timeout:
            status = results.RunStatus(rc=None, timed_out=True, error="sim_timeout", warnings=(), log_excerpt=(),
                                       log_path=None, cache_state=state)
            return results.ResultBundle(bench_id="stub", adapter_fp=fp["code_sha256"], descriptor_fp=descriptor.fp,
                                        status=status, by_request={}, name_map={}, method="stub", bundle_files=bundle)
        if by_request is None:
            by_request = {r.id: self._solve(r, circuit, results) for r in requests}
            if cache_dir is not None:
                Path(cache_dir).mkdir(parents=True, exist_ok=True)
                slot.write_bytes(pickle.dumps(by_request))
        status = results.RunStatus(rc=0, timed_out=False, error=None, warnings=(), log_excerpt=(), log_path=None,
                                   cache_state=state, **status_kw)
        name_map = {e.name: e.name for e in circuit.elements}
        return results.ResultBundle(bench_id="stub", adapter_fp=fp["code_sha256"], descriptor_fp=descriptor.fp,
                                    status=status, by_request=by_request, name_map=name_map,
                                    method="stub: MNA 해석해(선형 스탬프)", bundle_files=bundle)

    # ---- MNA
    def _solve(self, req, circuit, results):
        kind = type(req).__name__
        over = {(n, f): v for (n, f, v) in getattr(req, "exc", ())}
        res = results.Resolution(reltol=1e-4, abstol={"vntol": 1e-7, "abstol": 1e-13}, data_rel=None,
                                 source="adapter_declared")
        if kind == "Op":
            v, cur = self._mna(circuit, over, 0.0, dc=True)
            devs = {}
            for e in circuit.elements:
                if type(e).__name__ == "Mos":
                    p = self.devices.get(e.name, {})
                    gm, gds = p.get("gm", 0.0), p.get("gds", 0.0)
                    vgs, vds, vbs = v[e.g] - v[e.s], v[e.d] - v[e.s], v[e.b] - v[e.s]
                    devs[e.name] = {"id": gm * vgs + gds * vds, "gm": gm, "gds": gds, "vgs": vgs, "vds": vds,
                                    "vbs": vbs, "vth": None, "vdsat": None}
            return results.OpTable(devices=devs, nodes={k: float(x.real) for k, x in v.items()}, currents=cur,
                                   resolution=res, error=None, instance_geometry_reported=None)
        if kind == "Ac":
            if req.f_list is not None:
                f = np.asarray(req.f_list, dtype=float)
            else:
                n = int(round(np.log10(req.f_stop / req.f_start) * req.points_per_decade)) + 1
                f = req.f_start * 10.0 ** (np.arange(n) / req.points_per_decade)
            cols = {}
            for fk in f:
                v, cur = self._mna(circuit, over, 2 * np.pi * fk, dc=False)
                for ex in req.outputs:
                    cols.setdefault(self._key(ex), []).append(self._eval(ex, v, cur))
            return results.FreqSeries(f=f, values={k: np.asarray(x, dtype=complex) for k, x in cols.items()},
                                      resolution=res, error=None)
        raise AssertionError(f"stub 능력 밖 요청: {kind}")

    @staticmethod
    def _key(ex):
        from core import requests as rq
        return rq.expr_key(ex) if hasattr(rq, "expr_key") else repr(ex)

    def _eval(self, ex, v, cur):
        k = type(ex).__name__
        if k == "NodeV":
            return v[ex.net]
        if k == "DiffV":
            return v[ex.net_p] - v[ex.net_n]
        if k == "BranchI":
            return cur[ex.element]
        if k == "Ratio":
            return self._eval(ex.num, v, cur) / self._eval(ex.den, v, cur)
        raise AssertionError(f"stub 식 밖: {k}")

    def _mna(self, circuit, over, w, dc):
        els = circuit.elements
        nets = sorted({n for e in els for n in self._nets(e)} - set(GROUND))
        idx = {n: i for i, n in enumerate(nets)}
        branches = [e for e in els if type(e).__name__ in ("VSource", "Inductor", "Vcvs", "Probe")]
        bidx = {e.name: len(nets) + i for i, e in enumerate(branches)}
        N = len(nets) + len(branches)
        Y = np.zeros((N, N), dtype=complex)
        rhs = np.zeros(N, dtype=complex)
        for i in range(len(nets)):
            Y[i, i] += 1e-15                       # 부유 노드 방지(상대 영향 ~1e-11)

        def node(n):
            return None if n in GROUND else idx[n]

        def add(r, c, x):
            if r is not None and c is not None:
                Y[r, c] += x

        def two(a, b, y):
            ia, ib = node(a), node(b)
            add(ia, ia, y); add(ib, ib, y); add(ia, ib, -y); add(ib, ia, -y)

        for e in els:
            k = type(e).__name__
            if k == "Resistor":
                two(e.a, e.b, 1.0 / e.value)
            elif k == "Capacitor":
                if not dc:
                    two(e.a, e.b, 1j * w * e.value)
            elif k in ("VSource", "Inductor", "Vcvs", "Probe"):
                bi = bidx[e.name]
                p, n = (e.p, e.n) if k in ("VSource", "Vcvs") else (e.a, e.b)
                add(node(p), bi, 1); add(node(n), bi, -1); add(bi, node(p), 1); add(bi, node(n), -1)
                if k == "VSource":
                    val = over.get((e.name, "dc"), e.dc) if dc else over.get((e.name, "ac_mag"), e.ac_mag)
                    rhs[bi] = val
                elif k == "Inductor" and not dc:
                    Y[bi, bi] -= 1j * w * e.value
                elif k == "Vcvs":
                    add(bi, node(e.cp), -e.gain); add(bi, node(e.cn), e.gain)
            elif k == "ISource":
                val = over.get((e.name, "dc"), e.dc) if dc else over.get((e.name, "ac_mag"), e.ac_mag)
                ip, im = node(e.p), node(e.n)
                if ip is not None:
                    rhs[ip] -= val
                if im is not None:
                    rhs[im] += val
            elif k == "Mos":
                p = self.devices.get(e.name, {})
                gm, gds = p.get("gm", 0.0), p.get("gds", 0.0)
                d, g, s = node(e.d), node(e.g), node(e.s)
                add(d, g, gm); add(d, s, -gm - gds); add(d, d, gds)
                add(s, g, -gm); add(s, s, gm + gds); add(s, d, -gds)
            else:
                raise AssertionError(f"stub 원소 밖: {k}")
        x = np.linalg.solve(Y, rhs)
        v = {n: x[idx[n]] for n in nets}
        v.update({g: 0j for g in GROUND})
        cur = {e.name: x[bidx[e.name]] for e in branches}
        return v, cur

    @staticmethod
    def _nets(e):
        k = type(e).__name__
        if k == "Mos":
            return (e.d, e.g, e.s, e.b)
        if k in ("Resistor", "Capacitor", "Inductor", "Probe"):
            return (e.a, e.b)
        if k in ("VSource", "ISource"):
            return (e.p, e.n)
        if k == "Vcvs":
            return (e.p, e.n, e.cp, e.cn)
        raise AssertionError(f"stub 원소 밖: {k}")
