"""LUT 단일 정본 재발 방지 (사용자 결정 O-180: "lut v2만 남기고 다른 lut는 지워. 같은 잘못된 사용이 안 생기도록").

정본 = `assets/lut_v2_location.json` 이 sha256 으로 고정한 묶음(엔진은 `resolve_lut_location` 으로만 찾는다).
- (1) git 이 추적하는 LUT npz 파일(이름에 'lut' 이 든 *.npz)은 저장소에 없다. 이력 기록 폴더(.ai/.bkit/docs/wt)의 test 산출물은 제외.
- (2) skills/analog-gmid-design 아래 .py 가 'sky130' 로 시작하는 LUT npz 파일 이름(sky130*lut*.npz)을 문자열로 적었다면
  그 이름은 위치 선언의 files 에 있는 이름이어야 한다(옛 sample·r1 이름을 다시 가리키면 실패).
oracle: git ls-files 와 위치 선언 JSON 을 직접 읽는다(피검 코드 미사용).
"""
import json
import re
import subprocess
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[3]
LOCATION_CONFIG = SKILL_DIR / "assets" / "lut_v2_location.json"
REPO_ROOT = Path(subprocess.run(["git", "-C", str(SKILL_DIR), "rev-parse", "--show-toplevel"], capture_output=True,
                                text=True, check=True).stdout.strip())
HISTORY_DIRS = (".ai/", ".bkit/", "docs/", "wt/")
NAME_RE = re.compile(r"sky130[A-Za-z0-9_.\-]*lut[A-Za-z0-9_.\-]*\.npz")


def _tracked():
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files"], capture_output=True, text=True, check=True,
                         encoding="utf-8").stdout
    return [p for p in out.splitlines() if p]


def _declared_names():
    cfg = json.loads(LOCATION_CONFIG.read_text(encoding="utf-8"))
    return {ent["path"] for ent in cfg["files"].values()}


def test_no_tracked_lut_npz_outside_history():
    bad = [p for p in _tracked()
           if p.lower().endswith(".npz") and "lut" in Path(p).name.lower() and not p.startswith(HISTORY_DIRS)]
    assert bad == [], "위치 선언 밖 LUT npz 가 git 에 있다(정본은 lut_v2_location.json 뿐): %s" % bad


def test_py_files_reference_only_declared_lut_npz_names():
    declared = _declared_names()
    this = Path(__file__).resolve()
    hits = []
    for rel in _tracked():
        if not rel.endswith(".py") or rel.startswith(HISTORY_DIRS):
            continue
        p = REPO_ROOT / rel
        if p.resolve() == this or not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in NAME_RE.finditer(text):
            if m.group(0) not in declared:
                hits.append("%s: %s" % (rel, m.group(0)))
    assert hits == [], "위치 선언에 없는 LUT npz 이름을 적은 .py: %s" % hits[:20]


DRAFT_RE = re.compile(r"_drafts/engine|lut_slices|lut_v2/", re.I)
SLICE_RE = re.compile(r"sky130_fd_pr__\w*\.npz")
# 허용 리터럴 한 개: tests/lut/test_tolerance.py 의 `_GEN_SEARCH` -- LUT 데이터가 아니라 슬라이스 생성기 소스 파일의 검색 폴더다
# (git 밖 한 곳에만 있고 manifest 의 generator_sha256 이 같은 파일만 쓴다). 데이터(npz·manifest)는 이 폴더에서 읽지 않는다.
ALLOWED_LITERALS = {"C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/verification/slices_vdsat"}
ALLOWED_PAIRS = {("skills/analog-gmid-design/gmid_engine/tests/lut/test_tolerance.py", lit) for lit in ALLOWED_LITERALS}


def _scan_source(source, rel):
    try:
        return _literal_violations(source, rel)
    except SyntaxError as e:   # 원칙 10: 못 읽은 파일을 통과로 치지 않는다
        raise AssertionError("구문 오류로 검사하지 못한 .py: %s (%s)" % (rel, e))


def _literal_violations(source, rel=None):
    """.py 소스의 문자열 리터럴 가운데 위치 선언 밖 LUT 를 가리키는 것: 옛 초안 LUT 폴더 조각(_drafts/engine·lut_slices·lut_v2/),
    폴더가 붙은 lut manifest.json 경로, 폭 슬라이스 npz 이름(선언을 거치지 않고 직접 np.load 하는 꼴).
    이름 없는 상대 'manifest.json' 은 toy 입력 파일이라 통과."""
    import ast
    found = []
    tree = ast.parse(source)
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body \
                and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            docs.add(id(node.body[0].value))   # docstring 은 설명이라 경로로 쓰이지 않는다
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):   # 허용 폴더라도 거기서 manifest·npz 를 join 해 읽는 꼴은 거부
            strs = [a.value.replace("\\", "/") for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if any(s in ALLOWED_LITERALS for s in strs) and any(s.endswith(("manifest.json", ".npz")) for s in strs):
                found.append("join(%s, ...)" % strs[0][:80])
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            s = node.value.replace("\\", "/")
            if (rel, s) in ALLOWED_PAIRS:
                continue
            if DRAFT_RE.search(s) or SLICE_RE.search(s) or ("/" in s and s.endswith("manifest.json") and "lut" in s.lower()):
                found.append(s[:100])
    return found


def test_no_py_literal_points_at_lut_outside_declaration():
    this = Path(__file__).resolve()
    hits = []
    for rel in _tracked():
        if not rel.endswith(".py") or rel.startswith(HISTORY_DIRS):
            continue
        p = REPO_ROOT / rel
        if p.resolve() == this or not p.is_file():
            continue
        for s in _scan_source(p.read_text(encoding="utf-8", errors="replace"), rel):
            hits.append("%s: %s" % (rel, s))
    assert hits == [], "위치 선언 밖 LUT 경로·슬라이스 npz 리터럴: %s" % hits[:20]


def test_literal_guard_rejects_mutations():
    """거부 확인: 옛 오용 꼴 두 가지(초안 폴더 manifest 경로, 슬라이스 npz 직접 np.load)를 거부하고 toy 상대 manifest 는 통과."""
    m1 = 'M = r"C:\\Users\\x\\wt\\_drafts\\engine\\lut_slices\\manifest.json"\nN = "C:/a/_drafts/engine/lut_v2/manifest.json"\n'
    m4 = 'import numpy as np\nz = np.load("C:/a/_drafts/engine/lut_v2/sky130_fd_pr__nfet_01v8__tt__W5p0000um_dc.npz")\n'
    m4b = 'import numpy as np\nz = np.load(r"D:\\data\\sky130_fd_pr__nfet_01v8__tt__W5p0000um_dc.npz")\n'
    m5 = 'P = "C:/data/lut_xyz/manifest.json"\n'
    assert len(_literal_violations(m1)) == 2
    assert _literal_violations(m4) and _literal_violations(m4b) and _literal_violations(m5)
    assert _literal_violations('p = root / "manifest.json"\nq = "cap_ref.npz"\n') == []


def test_allowed_literal_is_pinned_to_one_file():
    """r-1: 허용 리터럴은 (파일, 리터럴) 쌍 하나뿐 -- 다른 파일이 같은 폴더 리터럴을 쓰거나 그 폴더에서 manifest·npz 를 join 하면 거부."""
    lit = next(iter(ALLOWED_LITERALS))
    owner, _ = next(iter(ALLOWED_PAIRS))
    src_dir = '_GEN = (r"%s",)\n' % lit.replace("/", "\\")
    assert _literal_violations(src_dir, owner) == []                      # 지정한 파일의 지정한 리터럴은 통과
    assert _literal_violations(src_dir, "skills/other/elsewhere.py")      # 같은 리터럴이라도 다른 파일은 거부
    assert _literal_violations(src_dir)                                   # 파일 미지정도 거부
    joined = 'import os\nm = os.path.join(r"%s", "manifest.json")\n' % lit.replace("/", "\\")
    assert _literal_violations(joined, owner)                             # 지정 파일이라도 그 폴더의 manifest join 은 거부
    assert _literal_violations(joined, "skills/other/elsewhere.py")


def test_unparsable_py_fails_closed():
    """r-2: 구문 오류 .py 는 건너뛰지 않고 실패(파일 경로를 담는다)."""
    import pytest
    with pytest.raises(AssertionError, match="bad.py"):
        _scan_source("def (:\n", "bad.py")


ENV_RE = re.compile(r"GMID_LUT_[A-Z0-9_]+")
# 허용: 위치 선언 파일이 쓰는 env(데이터 루트·파생표 캐시 폴더 -- 루트 env 는 sha256 이 같은 파일만 받는다) +
# 슬라이스 생성기를 manifest 의 generator_sha256 으로 찾는 폴더(LUT 가 아님).
ALLOWED_ENV_EXTRA = {"GMID_LUT_GENERATOR_DIR"}


def _declared_envs():
    cfg = json.loads(LOCATION_CONFIG.read_text(encoding="utf-8"))
    return {v["env"] for v in cfg.values() if isinstance(v, dict) and "env" in v}


def test_no_env_override_reads_lut_outside_declaration():
    """환경변수로 위치 선언 밖 LUT(manifest·cap npz 등)를 가리키는 경로 0: 추적 .py 의 `GMID_LUT_*` 이름은 선언의 env 이거나 허용 목록뿐."""
    allowed = {e for e in _declared_envs() if e.startswith("GMID_LUT_")} | ALLOWED_ENV_EXTRA
    this = Path(__file__).resolve()
    hits = []
    for rel in _tracked():
        if not rel.endswith(".py") or rel.startswith(HISTORY_DIRS):
            continue
        p = REPO_ROOT / rel
        if p.resolve() == this or not p.is_file():
            continue
        for m in ENV_RE.finditer(p.read_text(encoding="utf-8", errors="replace")):
            if m.group(0) not in allowed:
                hits.append("%s: %s" % (rel, m.group(0)))
    assert hits == [], "위치 선언 밖 LUT 를 가리키는 환경 덮어쓰기: %s" % hits[:20]
    assert "GMID_LUT_V2_ROOT" in allowed


def test_root_env_still_sha256_checked(tmp_path):
    """GMID_LUT_V2_ROOT 로 다른 폴더를 줘도 sha256 이 다르면 실제로 거부한다(루트 env 는 같은 파일의 위치 이동 용도뿐)."""
    import sys
    sys.path.insert(0, str(SKILL_DIR))
    from gmid_engine.core import SchemaRejectedError
    from gmid_engine.lut import resolve_lut_location
    cfg = json.loads(LOCATION_CONFIG.read_text(encoding="utf-8"))
    for ent in cfg["files"].values():
        (tmp_path / ent["path"]).write_bytes(b"not the pinned lut")
    env = {cfg["root"]["env"]: str(tmp_path)}
    try:
        resolve_lut_location(str(LOCATION_CONFIG), env)
    except SchemaRejectedError as e:
        assert "lut_location_sha256_mismatch" in repr(e.record)
    else:
        raise AssertionError("다른 내용의 파일을 가진 루트를 받아들였다")


def test_checks_actually_reject(tmp_path):
    """거부 능력 확인: 정규식이 옛 이름(sample)과 r1 이름을 잡고, 선언 이름은 통과시킨다."""
    declared = _declared_names()
    for old in ("sky130_nfet_pfet_lut_sample.npz", "sky130_nfet_pfet_lut_v2.npz"):
        assert NAME_RE.search("x = '%s'" % old).group(0) not in declared
    for ok in declared:
        if ok.endswith(".npz"):
            assert NAME_RE.search(ok).group(0) in declared
