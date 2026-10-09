"""gmid_engine.layout test 공용 fixture -- 옛 엔진 오라클 적재, 결과 직렬화, PYTHONHASHSEED 별도 프로세스 실행.

- 오라클(SD) = `legacy/stick_diagram.py`(CONTRACT.md 머리 '옛 원본'). 피검이 아니라 기준선이다. `sys.path` 를 건드리지 않고
  파일 경로로 고유 모듈 이름 `_sd_oracle_stick_diagram` 에 적재한다.
- 직렬화(CONTRACT 1 불변식 6): dataclass 는 (클래스 이름, 필드 dict), dict 는 삽입 순서 그대로의 (키, 값) 목록, set 은 정렬 목록,
  float 는 repr 정확값. 순서까지 같아야 '같은 출력'이다.
"""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[3]          # tests/layout -> tests -> gmid_engine -> analog-gmid-design
SD_PATH = SKILL_DIR / "legacy" / "stick_diagram.py"
SD_MODULE_NAME = "_sd_oracle_stick_diagram"


def load_sd():
    if SD_MODULE_NAME in sys.modules:
        return sys.modules[SD_MODULE_NAME]
    if not SD_PATH.is_file():
        pytest.skip("옛 원본 stick_diagram.py 가 저장소에 없다(SD 삭제 뒤) -- 오라클 대조 불가")
    spec = importlib.util.spec_from_file_location(SD_MODULE_NAME, SD_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[SD_MODULE_NAME] = mod
    spec.loader.exec_module(mod)
    return mod


def ser(x):
    """비교용 정규 표현(순서 보존). dataclass 클래스는 이름으로만 비교 -- 옛/새 모듈의 같은 이름 클래스를 같게 본다."""
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return ("dc", type(x).__name__, tuple((f.name, ser(getattr(x, f.name))) for f in dataclasses.fields(x)))
    if isinstance(x, dict):
        return ("dict", tuple((ser(k), ser(v)) for k, v in x.items()))
    if isinstance(x, (set, frozenset)):
        return ("set", tuple(sorted(repr(ser(v)) for v in x)))
    if isinstance(x, list):
        return ("list", tuple(ser(v) for v in x))
    if isinstance(x, tuple):
        return ("tuple", tuple(ser(v) for v in x))
    if isinstance(x, float):
        return ("float", repr(x))
    return (type(x).__name__, x)


@pytest.fixture(scope="session")
def sd():
    return load_sd()


@pytest.fixture(scope="session")
def serialize():
    return ser


def run_with_seed(code: str, seed: int) -> object:
    """`code` 를 PYTHONHASHSEED=seed 별도 프로세스에서 실행. code 는 마지막에 `RESULT` 를 JSON 직렬화 가능한 값으로 둔다."""
    prelude = (
        "import sys, json\n"
        f"sys.path.insert(0, {str(SKILL_DIR)!r})\n"
        f"sys.path.insert(0, {str(Path(__file__).resolve().parent)!r})\n"
        "from conftest import load_sd, ser\n"
    )
    epilogue = "\nprint('@@RESULT@@' + json.dumps(RESULT))\n"
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = str(seed)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([sys.executable, "-c", prelude + code + epilogue], cwd=str(SKILL_DIR), env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=600)
    assert proc.returncode == 0, "seed=%d 하위 프로세스 실패:\n%s\n%s" % (seed, proc.stdout, proc.stderr)
    line = [ln for ln in proc.stdout.splitlines() if ln.startswith("@@RESULT@@")]
    assert len(line) == 1, proc.stdout
    return json.loads(line[0][len("@@RESULT@@"):])


@pytest.fixture(scope="session")
def seed_runner():
    return run_with_seed


# ---------------------------------------------------------------------------
# 2단계(CONTRACT 4절) 공용 -- toy LUT(4.15 = lut 계약 7.1 r5 toy, 최소 finger 1e-6), 입력 생성기, 독립 계산
# 피검(layout 계산) 함수는 여기서 부르지 않는다. 기대값은 계약 손계산 또는 이 파일의 독립 계산에서 나온다.
# ---------------------------------------------------------------------------

import hashlib  # noqa: E402
from fractions import Fraction  # noqa: E402

import numpy as np  # noqa: E402

TOY_L = (1e-6, 2e-6, 3e-6)
TOY_VGS = (0.0, 0.5, 1.0)
TOY_VDS = (0.5, 1.0)
TOY_VS = (0.0, 0.5)
TOY_VS_FACTOR = (1.0, 0.5)
GRID = 1e-8
# [r5] lut 계약 7.1 r5 toy 닫힌 식: ln ID = ln(1e-7·(1e-6/L)) + 20v − 6v² + 0.1d + ln(0.5)·s/0.5, gm/ID = 20 − 12v, GDS = 0.1·ID
TOY_GM_ID = 14.0                              # layout 4.15 소자 공통 gm/ID -> 20 − 12v = 14 의 근 v = 0.5 (격자점)
TOY_VGS_ROOT = (20.0 - TOY_GM_ID) / 12.0
TOY_VDS_OP = 0.5


def toy_ln_id(v, d, L=1e-6, s_factor=1.0):
    return math.log(1e-7 * (1e-6 / L) * s_factor) + 20.0 * v - 6.0 * v * v + 0.1 * d


# I1 = 키 100 슬라이스(W 1e-6) 의 동작점(v 0.5, d 0.5, vsb 0, L 1e-6) ID = 1e-7·e^8.55 (layout 4.2), J0 = I1 / 1e-6 A/m
I1 = math.exp(toy_ln_id(TOY_VGS_ROOT, TOY_VDS_OP))
J0 = I1 / 1e-6


def _toy_slice_r4(W, scale):
    """lut r4 toy(FC 위반 예시) -- 4.2 의 거부 경로 확인용. [r7 2026-10-09] lut CONTRACT 1.4 기울기 열 단위 검사(현 기울기가 두 끝
    기울기 사이)와 맞는 판(lut tests conftest 의 R4_* 와 같은 구성·손계산): ID 마디 (1e-7, 1e-6, 1e-6·e^1.5)[VGS]·exp((0, 0.01)[VDS]),
    GM/ID = (20, 4, 1.5), GDS/ID = (0.1, 0.01) -- VGS 칸 0 과 VDS 칸은 FC 위반, VGS 칸 1 은 단조(옛 판 GM/ID (20, 10, 4)·GDS = ID/10 은
    VDS 칸 모두 단위 검사 위반이라 로드 거부). toy 동작점 gm/ID 14 는 VGS 칸 0(20 > 14 > 4) 이라 거부 경로 그대로."""
    ID = np.empty((3, 3, 2, 2))
    for iL, L in enumerate(TOY_L):
        for iG in range(3):
            for k in range(2):
                for s in range(2):
                    ID[iL, iG, k, s] = ((1e-6 / L) * (1e-7, 1e-6, 1e-6 * math.exp(1.5))[iG] * math.exp((0.0, 0.01)[k])
                                        * TOY_VS_FACTOR[s])
    ID = ID * scale
    GM = ID * np.asarray((20.0, 4.0, 1.5))[None, :, None, None]
    return {
        "W": np.float64(W), "L": np.asarray(TOY_L), "VGS": np.asarray(TOY_VGS), "VDS": np.asarray(TOY_VDS),
        "VS": np.asarray(TOY_VS), "ID": ID, "GM": GM, "GDS": ID * np.asarray((0.1, 0.01))[None, None, :, None],
        "VTH": np.full(ID.shape, 0.4),
        "meta_json": np.str_('{"model_files_sha256": {}}'), "corner": np.str_("tt"), "temp_c": np.float64(27.0),
    }


def _toy_slice(W, scale):
    ID = np.empty((3, 3, 2, 2))
    for iL, L in enumerate(TOY_L):
        for iG, v in enumerate(TOY_VGS):
            for k, d in enumerate(TOY_VDS):
                for s in range(2):
                    ID[iL, iG, k, s] = math.exp(toy_ln_id(v, d, L, TOY_VS_FACTOR[s]))
    ID = ID * scale
    GM = ID * (20.0 - 12.0 * np.asarray(TOY_VGS))[None, :, None, None]
    return {
        "W": np.float64(W), "L": np.asarray(TOY_L), "VGS": np.asarray(TOY_VGS), "VDS": np.asarray(TOY_VDS),
        "VS": np.asarray(TOY_VS), "ID": ID, "GM": GM, "GDS": ID * 0.1, "VTH": np.full(ID.shape, 0.4),
        "meta_json": np.str_('{"model_files_sha256": {}}'), "corner": np.str_("tt"), "temp_c": np.float64(27.0),
    }


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build_toy_lut(root, id_scale=1.0, variant="r5"):
    """CONTRACT 4.15 [r5] toy(lut 계약 7.1 r5 toy 슬라이스 2장 + 기준 LUT, LutSpec 최소 finger 1e-6). id_scale != 1 이면 내용이 다른 LUT(다른 fp)."""
    from gmid_engine.lut import LutSpec, load_lut_set
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for fname, W, scale in (("toy_w100.npz", 1e-6, 1.0), ("toy_w200.npz", 2e-6, 2.0)):
        p = root / fname
        np.savez(p, **(_toy_slice if variant == "r5" else _toy_slice_r4)(W, scale * id_scale))
        entries.append({"device": "toyn", "file": fname, "sha256": _sha(p)})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    shp = (3, 3, 2, 2)
    np.savez(root / "cap_ref.npz", L=np.asarray(TOY_L), VGS=np.asarray(TOY_VGS), VDS=np.asarray(TOY_VDS),
             VS=np.asarray(TOY_VS), CGG_n=np.full(shp, 1e-15), CGD_n=np.full(shp, 2e-16), w_ref_m=np.float64(1e-6),
             corner=np.str_("tt"), temp_c=np.float64(27.0))
    spec = LutSpec(GRID, (("nmos", 1e-6),), (("toyn", "nmos"),), (("nmos", "_n"),))
    return load_lut_set(str(root / "manifest.json"), str(root / "cap_ref.npz"), spec)


def new_memo(lut, n=4096):
    from gmid_engine.lut import LutMemo
    return LutMemo(lut, point=n, curve=n, root=n)


def rule_ids():
    from gmid_engine.layout.contract_input import PDK_RULE_QUANTITIES
    return tuple((q, "RULE." + q) for q in PDK_RULE_QUANTITIES)


def toy_pdk(lut, overhead=0.0, gap=0.0, dummy=0.0, tap=0.0, well=0.0, rules=None):
    from gmid_engine.layout import LayoutPdk
    return LayoutPdk.from_lut(lut, overhead, gap, dummy, tap, well, rule_ids() if rules is None else rules)


def dev(name, s, d, w_need, gate="g", W=4e-6, L=1e-6, gm_id=TOY_GM_ID, vds=TOY_VDS_OP, vsb=0.0, diode=False, adj=True,
        kind="nmos", body="sub", ID_A=None):
    """4.15 소자 공통값(kind nmos, body sub, L 1e-6, gm/ID 14, vds 0.5, vsb 0, W_m 4e-6 참고).

    [r5] 넷째 인자 `w_need` = toy 동작점에서의 W_need(m). 계약 4.15 의 'ID_A = c x I1 -> W_need = c x 1e-6' 그대로
    ID_A = w_need x J0 (J0 = I1 / 1e-6). 실 LUT 등 다른 조건은 `ID_A=` 로 전류를 직접 준다.
    """
    from gmid_engine.layout import LayoutDevice
    current = w_need * J0 if ID_A is None else ID_A
    return LayoutDevice(name, kind, d, gate, s, body, W, L, current, gm_id, vds, vsb, diode, adj)


def make_input(devices, groups, row_groups, pdk, rejected=(), passives=()):
    from gmid_engine.layout import LayoutInput
    return LayoutInput(tuple(devices), tuple(groups), tuple(row_groups), pdk, tuple(rejected), tuple(passives))


def rg(rid, members, kind="nmos", body="sub"):
    from gmid_engine.layout import RowGroup
    return RowGroup(rid, kind, body, tuple(members))


def mg(gid, members, role, hub=None, patterns=("common_centroid", "interdigitation")):
    from gmid_engine.layout import MatchingGroup
    return MatchingGroup(gid, tuple(members), role, hub, tuple(patterns))


def centroid_offsets(rows, members):
    """CONTRACT 4.5 4 의 dx·dy 독립 계산(정확한 유리수). rows = 소자 이름 열들."""
    R = len(rows)
    xs = {m: [] for m in members}
    ys = {m: [] for m in members}
    for r, seq in enumerate(rows):
        n = len(seq)
        for i, name in enumerate(seq):
            if name in xs:
                xs[name].append(Fraction(2 * i - (n - 1), 2))
                ys[name].append(Fraction(2 * r - (R - 1), 2))
    cx = [sum(v, Fraction(0)) / len(v) for v in xs.values() if v]
    cy = [sum(v, Fraction(0)) / len(v) for v in ys.values() if v]
    return max(cx) - min(cx), max(cy) - min(cy)


def strip_volatile(result):
    """결과 비교용: computed_blocks·snapshot 제외(4.13 9·10)."""
    return ser(tuple((f.name, getattr(result, f.name)) for f in dataclasses.fields(result)
                     if f.name not in ("computed_blocks", "snapshot")))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "layout_realdata: 실 LUT(폭 슬라이스 manifest·기준 LUT·tlef) 레이아웃 test -- 경로가 없으면 FAIL(skip 아님), 슬라이스 2장 tol_V 표 "
        "계산 때문에 수십 초. 빼려면 -m \"not layout_realdata\"",
    )


BLOCK_ORDER = ("finger_candidates","pattern_select", "finger_geometry", "compose_rows")


def block_objects():
    """계산 블록 4개(4.0 표의 파일·진입점 이름) -- 블록 단위 test 가 run_layout 없이 부른다."""
    from gmid_engine.layout.finger_candidates import finger_candidates
    from gmid_engine.layout.pattern_select import pattern_select
    from gmid_engine.layout.finger_geometry import finger_geometry
    from gmid_engine.layout.rows import compose_rows
    return {"finger_candidates": finger_candidates, "pattern_select": pattern_select,
            "finger_geometry": finger_geometry, "compose_rows": compose_rows}


def staged_snapshot(inp, memo, upto=None):
    """4.12 2·3 의 입력 필드·슬라이스 필드를 직접 쓴 스냅샷(writer = `_ly_fields` 표) + `upto` 블록까지 차례로 적용.

    슬라이스 값은 `slice_density`(4.2, 따로 test) 결과. `upto=None` 이면 블록을 하나도 부르지 않는다.
    """
    from gmid_engine.core import GraphSnapshot
    from gmid_engine.layout import _ly_fields as lf
    from gmid_engine.layout.slice_density import slice_density
    pdk = inp.pdk
    keys = dict(pdk.slice_width_keys)
    snap = GraphSnapshot.empty(lf.LY_WRITERS)
    snap = snap.write(lf.WRITER_INPUT, "test-input", {
        (lf.DEVICE, lf.F_DEVICE): {d.name: d for d in inp.devices},
        (lf.GRAPH, lf.F_PDK): {lf.GRAPH_KEY: pdk},
        (lf.GRAPH, lf.F_GROUPS_IN): {lf.GRAPH_KEY: inp.matching_groups},
        (lf.GRAPH, lf.F_ROW_GROUPS): {lf.GRAPH_KEY: inp.row_groups},
        (lf.GRAPH, lf.F_REJECTED): {lf.GRAPH_KEY: tuple(sorted(inp.rejected_requests))},
        # [U12] CONTRACT 4.12 2: 입력 필드 `ly_passives` = 이름순 `LayoutPassive` tuple(_ly_fields.INPUT_FIELDS 에 추가된 필드)
        (lf.GRAPH, lf.F_PASSIVES): {lf.GRAPH_KEY: tuple(sorted(inp.passives, key=lambda p: p.name))},
    })
    snap = snap.write(lf.WRITER_SLICES, "test-slices", {
        (lf.DEVICE, lf.F_SLICES): {d.name: slice_density(memo, d, keys[d.kind]) for d in inp.devices},
    })
    if upto is None:
        return snap
    blocks = block_objects()
    for name in BLOCK_ORDER[:BLOCK_ORDER.index(upto) + 1]:
        snap = blocks[name](snap)
    return snap


def graph_value(snap, field):
    from gmid_engine.layout import _ly_fields as lf
    return snap.value(lf.GRAPH, lf.GRAPH_KEY, field)


def device_column(snap, field):
    from gmid_engine.layout import _ly_fields as lf
    return dict(snap.column(lf.DEVICE, field))


@pytest.fixture(scope="session")
def toy_lut(tmp_path_factory):
    return build_toy_lut(tmp_path_factory.mktemp("layout_toy"))


@pytest.fixture
def toy_memo(toy_lut):
    return new_memo(toy_lut)
