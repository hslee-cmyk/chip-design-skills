"""generality 하류 단계(sizing·metrics·search·layout) 공용 -- 회로 변형 -> spec -> S1 -> sizing ctx -> search ctx 를 **공개 API 로만**
만든다(입력 생성용; 기대값은 각 test 가 '원래 결과에 변형 표를 적용한 것'으로 만든다).

- LUT = 실데이터 LUT v2(`assets/lut_v2_location.json`, lut CONTRACT 1.8 `resolve_lut_location`) -- tests/sizing conftest `real_lut_v2`
  와 같은 구성(격자 = PDK tlef MANUFACTURINGGRID, kind 별 최소 finger = 슬라이스 최소 W). 데이터가 없으면 `RuntimeError`(fixture 가
  skip 이 아니라 FAIL 로 바꾼다).
- PDK 선언 = `assets/sky130_pdk_decl.json`, LUT 규칙 선언 = `assets/sky130_lut_rule_decl.json`(core 9절, search r6
  `build_search_context`, metrics 7.6 `JunctionSource`).
- metric 이름표 = metrics `metric_catalog()` + library spec 이 쓰는 레지스트리 밖 이름 3개(SPEC_CONTRACT 7절 S2 -- tests/sizing
  conftest `spec_catalog` 와 같은 보충).
- 변형 = "orig" / ("ren", seed) 이름 치환 / ("shuf", seed) 순서 섞기 + 태그 잡음 / "pol" 극성 뒤집기. spec 은 같은 표로 옮긴다
  (`topogen.rename_spec`, 합성 회로는 `topogen.synthetic_spec`).
- library spec 에는 소신호 metric 판정 제약(유도 뷰)을 이름표에 없는 metric 만 더한다(값은 test 가 정한 입력 -- 통과 여부가 아니라
  변형 전후 같은 값인지를 본다). 같은 (metric, op) 가 이미 있으면 더하지 않는다(SPEC_CONTRACT 2절 `constraint_duplicate`).
- 탐색 설정: θ 저항 상자 (1e2, 1e5) Ω·θ 커패시터 상자 (1e-13, 1e-10) F 는 search CONTRACT 10절 시연 상자(사용자 선언 대기 S-3 --
  변형 전후 같은 입력이면 충분), 평가 예산 `EVAL_BUDGET`(결정론 -- 벽시계 정지 없음, search 7절).
"""
from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path

import numpy as np

from gmid_engine.authoring import load_sizing_spec, load_topology
from gmid_engine.core import BoundedLRU, MetricSignature, SchemaRejectedError, read_pdk_decl
from gmid_engine.graph import build_s1
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.metrics import JunctionSource, metric_catalog
from gmid_engine.search import SearchSettings, build_search_context, layer0_start
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access

from .topogen import add_tag_noise, flip_polarity, random_renaming, rename, rename_spec, shuffle_order, synthetic_spec
from .topogen import synthetic_topologies

SKILL_DIR = Path(__file__).resolve().parents[3]
LIBRARY = SKILL_DIR / "assets" / "library"
LOCATION_CONFIG = SKILL_DIR / "assets" / "lut_v2_location.json"
PDK_DECL = SKILL_DIR / "assets" / "sky130_pdk_decl.json"
LUT_RULE_DECL = SKILL_DIR / "assets" / "sky130_lut_rule_decl.json"
DEFAULT_TLEF = "C:/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef"
REAL_DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
REAL_CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
MEMO_POINT, MEMO_CURVE, MEMO_ROOT = 1 << 16, 1 << 14, 1 << 16
SYNTH_SUPPLIES = (("qp_hi", 1.8), ("qp_lo", 0.0))       # 합성 회로 레일(topogen circuits.py) 전위 -- test 입력
SS_CONSTRAINTS = (("gain_ss_db", ">=", 0.0), ("ugf_ss_hz", ">=", 1.0), ("gbw_ss_hz", ">=", 1.0), ("pm_ss_deg", ">=", 0.0),
                  ("parasitic_pm_ss_deg", ">=", 0.0), ("rout_ss_ohm", "<=", 1e12))
SS_SOURCE = {"kind": "user_spec", "record": "generality test fixture (metric request)", "decided": "2026-10-08"}
SINGLE_ENDED_INPUT = "single_ended_input"
DIFF_INPUT_ROLES = ("differential_input_p", "differential_input_n")
RESISTANCE_BOX = (1e2, 1e5)
CAPACITANCE_BOX = (1e-13, 1e-10)
FRONT_BUDGET_S = 60.0
EVAL_BUDGET = 40
CATALOG_GAPS = (("mismatch_sigma_mv", ("mv", "dc")), ("mirror_ratio_error_mv", ("mv", "dc")),
                ("area_layout_m2", ("m2", "geom", None, "area")))


class Env:
    """LUT·memo·레이아웃 전 폭 접근자·PDK 선언·접합 묶음·이름표(프로세스당 1회)."""

    def __init__(self):
        try:
            loc = resolve_lut_location(str(LOCATION_CONFIG), os.environ)
        except SchemaRejectedError as e:
            raise RuntimeError("LUT v2 데이터 위치를 풀지 못함: %r" % (e.record.detail,)) from e
        tlef = os.environ.get("GMID_PDK_TLEF") or DEFAULT_TLEF
        if not Path(tlef).is_file():
            raise RuntimeError("PDK tlef 없음: %s" % tlef)
        m = re.search(r"^\s*MANUFACTURINGGRID\s+([0-9.eE+-]+)\s*;",
                      Path(tlef).read_text(encoding="utf-8", errors="replace"), re.M)
        grid = float(m.group(1)) * 1e-6
        man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
        dk = dict(REAL_DEVICE_KINDS)
        mins = {}
        for s in man["slices"]:
            with np.load(Path(loc.manifest_path).parent / s["file"]) as z:
                w = float(z["W"])
            kind = dk[s["device"]]
            mins[kind] = min(w, mins.get(kind, w))
        decl_memo = BoundedLRU(16)
        self.pdk = read_pdk_decl(str(PDK_DECL), decl_memo)
        # [U8 2026-10-09] search CONTRACT 11절: 값 있는 잡음 제약이 있으면 시작 때 noise_lut_missing 거부 -- 잡음 r1(설정 files.noise)과
        # LutSpec.noise_ef(PDK 선언 noise_ef_<kind>, lut CONTRACT 9 '부르는 쪽이 PDK 선언에서 채운다')를 싣는다
        if not loc.noise_path:
            raise RuntimeError("LUT 위치 설정에 잡음 r1(files.noise) 항목이 없다: %s" % LOCATION_CONFIG)
        q = dict(self.pdk.quantities)
        noise_ef = tuple(sorted((kind, q["noise_ef_%s" % kind].value_m) for kind in mins))
        spec = LutSpec(grid, tuple(sorted(mins.items())), REAL_DEVICE_KINDS, REAL_CAP_SUFFIX, noise_ef=noise_ef)
        self.lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root,
                                verify_midpoints=loc.midpoints_path, noise_npz=loc.noise_path)
        self.memo = LutMemo(self.lut, point=MEMO_POINT, curve=MEMO_CURVE, root=MEMO_ROOT)
        self.access = pre_layout_lut_access(self.memo)
        self.lut_rule = read_pdk_decl(str(LUT_RULE_DECL), decl_memo)
        self.junction = JunctionSource.from_decls(self.pdk, self.lut_rule, self.lut)
        cat = dict(metric_catalog())
        for name, sig in CATALOG_GAPS:
            cat.setdefault(name, MetricSignature(*sig))
        self.catalog = cat


class Case:
    """변형 하나의 공개 API 산출물. mapping = 원래 이름 -> 이 변형 이름(원소·넷), kind_map = MOS kind 치환."""

    def __init__(self, name, variant, mapping, kind_map, doc, td, spec, inputs, s1, ctx):
        self.name, self.variant, self.mapping, self.kind_map = name, variant, mapping, kind_map
        self.doc, self.td, self.spec, self.inputs, self.s1, self.ctx = doc, td, spec, inputs, s1, ctx

    def nm(self, x):
        return self.mapping.get(x, x)


def _with_ss_constraints(spec, ports):
    """library spec 에 SS_CONSTRAINTS 중 (metric, op) 가 없는 것을 유도 뷰로 더한 사본. 유도 뷰 조건(SPEC_CONTRACT 2절
    `view_required`: 입력 = 차동쌍 1개 또는 단일 1개, 출력 1개)에 맞지 않으면 더하지 않는다."""
    roles = sorted(v["role"] for k, v in ports.items() if not k.startswith("_") and v["direction"] == "input")
    outs = [k for k, v in ports.items() if not k.startswith("_") and v["direction"] == "output"]
    if not (roles == [SINGLE_ENDED_INPUT] or tuple(sorted(roles)) == tuple(sorted(DIFF_INPUT_ROLES))) or len(outs) != 1:
        return spec
    out = copy.deepcopy(spec)
    have = {(c.get("metric"), c.get("op")) for c in out["human"]["constraints"] if isinstance(c.get("metric"), str)}
    for metric, op, value in SS_CONSTRAINTS:
        if (metric, op) not in have:
            out["human"]["constraints"].append({"metric": metric, "op": op, "value": value, "source": dict(SS_SOURCE)})
    return out


class Pipe:
    """회로 이름 + 변형 -> Case(캐시). 파일은 변형마다 다른 하위 폴더(같은 topology_name 충돌 방지)."""

    def __init__(self, env, root):
        self.env = env
        self.root = Path(root)
        self._cases = {}
        self._sctx = {}
        self._theta0 = {}
        self._n = 0

    # ------------------------------------------------------------------ 입력
    @staticmethod
    def base_doc(name):
        synth = synthetic_topologies()
        if name in synth:
            return synth[name]
        return json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))

    @staticmethod
    def base_spec_fn(name, doc):
        """(변형 doc, 이름 표, topology_fp) -> spec dict 를 만드는 함수."""
        if name in synthetic_topologies():
            ports = doc["ports"]
            outs = [k for k, v in ports.items() if v["direction"] == "output"]
            ins = [v["role"] for v in ports.values() if v["direction"] == "input"]
            cons = SS_CONSTRAINTS if (ins == [SINGLE_ENDED_INPUT] and len(outs) == 1) else ()

            def make(vdoc, mapping, fp):
                return synthetic_spec(vdoc, fp, {mapping.get(k, k): v for k, v in SYNTH_SUPPLIES}, cons)
            return make
        spec = json.loads((LIBRARY / (name + ".sizing_spec.json")).read_text(encoding="utf-8"))
        spec = _with_ss_constraints(spec, doc["ports"])

        def make(vdoc, mapping, fp):
            return rename_spec(spec, mapping, fp)
        return make

    @staticmethod
    def variant_doc(doc, variant):
        """-> (변형 doc, 이름 표, kind 표)."""
        if variant == "orig":
            return doc, {}, {}
        if variant == "pol":
            flipped, swap = flip_polarity(doc)
            return flipped, swap, {"nmos": "pmos", "pmos": "nmos"}
        tag, seed = variant
        if tag == "ren":
            m = random_renaming(doc, seed)
            return rename(doc, m), m, {}
        if tag == "shuf":
            return add_tag_noise(shuffle_order(doc, seed), seed), {}, {}
        raise ValueError(variant)

    def case(self, name, variant="orig"):
        key = (name, variant)
        if key not in self._cases:
            doc = self.base_doc(name)
            vdoc, mapping, kind_map = self.variant_doc(doc, variant)
            self._n += 1
            d = self.root / ("v%03d" % self._n)
            d.mkdir(parents=True, exist_ok=True)
            tname = vdoc["topology_name"]
            tp = d / (tname + ".topology.json")
            tp.write_text(json.dumps(vdoc, indent=1, ensure_ascii=False), encoding="utf-8")
            td = load_topology(str(tp))
            # 레일 이름 표: 극성 뒤집기는 넷 이름을 바꾸지 않는다(같은 레일 이름에 같은 전위) -- spec 은 지문만 바뀐다
            spec_map = {} if variant == "pol" else mapping
            sp = d / (tname + ".sizing_spec.json")
            sp.write_text(json.dumps(self.base_spec_fn(name, doc)(vdoc, spec_map, td.connectivity_fp), indent=1,
                                     ensure_ascii=False), encoding="utf-8")
            spec = load_sizing_spec(str(sp), td, self.env.catalog)
            inputs = dc_inputs_from_spec(spec)
            s1 = build_s1(td, dict(inputs.supplies_v))
            ctx = build_kernel_context(s1, inputs, self.env.access)
            self._cases[key] = Case(name, variant, mapping, kind_map, vdoc, td, spec, inputs, s1, ctx)
        return self._cases[key]

    def settings(self):
        return SearchSettings(FRONT_BUDGET_S, EVAL_BUDGET, RESISTANCE_BOX, (("generality", "test_fixture"),),
                              CAPACITANCE_BOX)

    def sctx(self, case):
        """S0 당 1회(캐시) -- 같은 case 의 평가 캐시를 공유한다."""
        key = (case.name, case.variant)
        if key not in self._sctx:
            self._sctx[key] = build_search_context(case.ctx, case.spec, self.settings(), None, self.env.pdk,
                                                   self.env.lut_rule)
        return self._sctx[key]

    def fresh_sctx(self, case):
        """캐시 없는 새 search 컨텍스트(층 0 비교용 -- 평가 캐시가 결과에 끼지 않게)."""
        return build_search_context(case.ctx, case.spec, self.settings(), None, self.env.pdk, self.env.lut_rule)

    def theta0(self, name):
        """원래 회로의 층 0 시작점 (θ dict, {MOS: L 칸 index}) 또는 None. 변형 비교의 고정 θ 출처(입력)."""
        if name not in self._theta0:
            case = self.case(name)
            sc = self.fresh_sctx(case)
            res = layer0_start(sc)
            if res.start is None:
                self._theta0[name] = (None, res)
            else:
                mos = [m for m, _ in sc.domain.l_cells]
                self._theta0[name] = ((dict(res.start.theta), dict(zip(mos, res.start.cells))), res)
        return self._theta0[name]


def map_theta(theta, case):
    """θ {(종류, 이름): 값} 의 이름을 case 의 표로 옮긴다(y 키 `input_common_mode` 는 이름이 아니라 표 밖 -- 그대로)."""
    return {(k, case.nm(n)): v for (k, n), v in theta.items()}


def map_cells(cells, case, domain):
    """{원래 MOS: 칸} -> 그 case 의 `domain.l_cells` 순서(MOS 이름순) tuple."""
    inv = {case.nm(m): m for m in cells}
    return tuple(cells[inv[m]] for m, _ in domain.l_cells)
