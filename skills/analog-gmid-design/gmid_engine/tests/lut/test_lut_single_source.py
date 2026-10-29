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


def test_checks_actually_reject(tmp_path):
    """거부 능력 확인: 정규식이 옛 이름(sample)과 r1 이름을 잡고, 선언 이름은 통과시킨다."""
    declared = _declared_names()
    for old in ("sky130_nfet_pfet_lut_sample.npz", "sky130_nfet_pfet_lut_v2.npz"):
        assert NAME_RE.search("x = '%s'" % old).group(0) not in declared
    for ok in declared:
        if ok.endswith(".npz"):
            assert NAME_RE.search(ok).group(0) in declared
