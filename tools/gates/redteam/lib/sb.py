"""임시 sandbox: 작업 저장소·gate 저장소·역할 worktree·변경 한 건 흐름·판정 기록을 %TEMP% 아래에 새로 만든다.

안전 규칙(검증 agent 브리핑의 git 가드):
* 모든 git 쓰기는 `git -C <절대 경로>`이고 그 경로는 반드시 이 실행의 임시 루트 아래다(`_assert_temp`).
* 실제 저장소(시험 대상 worktree 포함)에는 읽기 명령(`show`, `cat-file`, `rev-parse`, `ls-tree`)만 쓴다.
* `config` 쓰기·`update-index`·`commit-tree`·`reset` 같은 명령은 임시 저장소에만 쓴다.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

REDTEAM = Path(__file__).resolve().parents[1]
REPO = Path(os.environ.get("RT_REPO") or REDTEAM.parents[2]).resolve()
TEMP_ROOT = Path(tempfile.gettempdir()).resolve()
HISTORY = Path(os.environ.get("RT_HISTORY_REPO") or REPO).resolve()   # git show로 원천 blob을 읽는 저장소
PLAN_REL = "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
SPEC_DIR = "docs/02-design/specs"
PINNED_PROBE_COMMIT = "4fd0fd8"   # v4_rule_probe가 있는 커밋(부트스트랩 ①이 probe를 지워도 재생이 원천을 잃지 않게)
EMPTY_GIT_ENV_KEYS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                      "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_PREFIX",
                      "GIT_QUARANTINE_PATH", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT")


class Missing(Exception):
    """게이트 코드(작성본)가 없어 이 단계를 실행할 수 없다."""

    def __init__(self, paths):
        super().__init__(", ".join(paths))
        self.paths = list(paths)


def posix(p) -> str:
    return str(Path(p)).replace("\\", "/")


def win(p) -> str:
    return str(Path(p)).replace("/", "\\")


def clean_env(extra: dict | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in EMPTY_GIT_ENV_KEYS and not k.startswith("GIT_CONFIG_KEY_")
           and not k.startswith("GIT_CONFIG_VALUE_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    if extra:
        env.update(extra)
    return env


def _assert_temp(path) -> None:
    p = Path(path).resolve()
    if TEMP_ROOT not in p.parents:
        raise RuntimeError(f"git 쓰기 경로가 임시 루트 밖이다: {p}")
    if p == REPO or REPO in p.parents or p in REPO.parents:
        raise RuntimeError(f"git 쓰기 경로가 시험 대상 저장소와 겹친다: {p}")


def git(cwd, *args, check=True, env=None, input_bytes=None) -> subprocess.CompletedProcess:
    _assert_temp(cwd)
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, env=clean_env(env), input=input_bytes)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} (in {cwd}) 실패 {r.returncode}: "
                           f"{r.stderr.decode('utf-8', 'replace')[:800]}")
    return r


def gout(cwd, *args, env=None) -> str:
    return git(cwd, *args, env=env).stdout.decode("utf-8").strip()


READ_ONLY = {"show", "cat-file", "rev-parse", "ls-tree"}


def repo_read(*args) -> bytes:
    """시험 대상 저장소 읽기 전용."""
    if args[0] not in READ_ONLY:
        raise RuntimeError(f"실제 저장소에는 읽기 명령만 쓴다: {args[0]}")
    r = subprocess.run(["git", "-C", str(HISTORY), *args], capture_output=True, env=clean_env())
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 실패: {r.stderr.decode('utf-8', 'replace')[:400]}")
    return r.stdout


def gate_path(key: str) -> Path:
    from iface import GATE_FILES
    return REPO / GATE_FILES[key]


def require(*keys) -> None:
    from iface import GATE_FILES
    miss = [GATE_FILES[k] for k in keys if not (REPO / GATE_FILES[k]).is_file()]
    if miss:
        raise Missing(miss)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def write(path, content, *, binary=False):
    path = Path(path)
    _assert_temp(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        path.write_bytes(content)
    else:
        path.write_bytes(content.encode("utf-8"))


# --------------------------------------------------------------------------------------------------------------
# 상태 파일
# --------------------------------------------------------------------------------------------------------------
class State:
    def __init__(self, work: Path):
        self.work = work
        self.file = work / "state.json"
        self.vars: dict = json.loads(self.file.read_text(encoding="utf-8")) if self.file.exists() else {}

    def save(self):
        self.file.write_text(json.dumps(self.vars, ensure_ascii=False, indent=1), encoding="utf-8")

    def __getitem__(self, k):
        return self.vars[k]

    def __setitem__(self, k, v):
        self.vars[k] = v
        self.save()

    def get(self, k, d=None):
        return self.vars.get(k, d)


# --------------------------------------------------------------------------------------------------------------
# sandbox 파일 내용
# --------------------------------------------------------------------------------------------------------------
ENGINE_B0 = '''"""redteam 합성 엔진 모듈 -- 공격 재생용이다(실제 엔진이 아니다)."""


def rt_gain(gm, ro):
    """소신호 이득 gm*ro."""
    return gm * ro
'''

TEST_B0 = '''from rt_engine import rt_gain


def test_rt_gain():
    assert rt_gain(2e-3, 50e3) == 100.0
'''


def spec_card(cid: str, phase: str = "1", evidence_type: str = "red-green", gate_change: str = "no",
              contracts: list[str] | None = None) -> str:
    contract_lines = "\n".join(f"- `{c}`" for c in (contracts or ["rt_engine.rt_gain"]))
    return (f"---\nid: {cid}\nphase: {phase}\nevidence_type: {evidence_type}\ngate_change: {gate_change}\n---\n"
            f"## 의도\nredteam 합성 변경 {cid}\n## 관찰 가능한 계약\n{contract_lines}\n## 신규 시그니처\n"
            f"## 판정 유형 근거\n합성\n## oracle 종류와 출처\n(a) 구성으로 정답이 정해진 합성 입력\n"
            f"## 거부해야 할 입력\n없음\n## library 회로 적용 여부\n아님\n## 무동작 판정 입력(무발동 값)\n없음\n"
            f"## 재현할 수치\n없음\n## 결정 필요 항목\n없음\n")


def approval_text(header: list[tuple[str, str]], *, eol="\n", bom=b"") -> bytes:
    lines = ["---"] + [f"{k}: {v}" if v is not None else k for k, v in header] + ["---", "",
             "## 사용자 원문", "", "> redteam 합성 기록(실제 사용자 승인이 아니다)", "", "## 범위 설명", "", "redteam", ""]
    return bom + eol.join(lines).encode("utf-8")


FLOW_IDS = {"rg": ("20260921-rt-rg", "red-green"), "eq": ("20260921-rt-eq", "equivalence"),
            "to": ("20260921-rt-to", "test-only"), "rg2": ("20260921-rt-rg2", "red-green")}


# --------------------------------------------------------------------------------------------------------------
# sandbox 만들기
# --------------------------------------------------------------------------------------------------------------
def init_repo(path: Path, *, bare=False):
    path.mkdir(parents=True, exist_ok=True)
    _assert_temp(path)
    if bare:
        git(path, "init", "--bare", "-b", "master", str(path))
        hooks = path / "hooks"
        for f in hooks.glob("*.sample"):   # §13.1 ④(b): 샘플 hook 삭제
            f.unlink()
        return
    git(path, "init", "-b", "master", str(path))
    for k, v in (("user.name", "redteam"), ("user.email", "redteam@example.invalid"), ("core.autocrlf", "false"),
                 ("commit.gpgsign", "false"), ("core.hooksPath", posix(path / ".githooks")),
                 ("core.quotepath", "false")):
        git(path, "config", k, v)


def copy_gate_tree(dst_root: Path):
    """시험 대상의 게이트 코드(tools/gates/** -- redteam 제외, hooks/role_*)를 sandbox 트리로."""
    src = REPO / "tools" / "gates"
    for p in src.rglob("*"):
        rel = p.relative_to(REPO)
        parts = rel.parts
        if "redteam" in parts[:3] or "__pycache__" in parts or p.suffix == ".pyc" or not p.is_file():
            continue
        d = dst_root / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, d)
    for p in (REPO / "hooks").glob("role_*"):
        if p.is_file():
            d = dst_root / "hooks" / p.name
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, d)
    for rel in (".ai/verification/_schema.json", ".ai/approvals/_TEMPLATE.md", "docs/02-design/specs/_TEMPLATE.spec.md",
                "docs/02-design/disputes/_TEMPLATE.md"):
        if (REPO / rel).is_file():
            d = dst_root / rel
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / rel, d)
    for p in (REPO / "agents").glob("gmid-*.md"):
        d = dst_root / "agents" / p.name
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, d)


def run_py(args, cwd, env=None, stdin: bytes | None = None, timeout=600) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, env=clean_env(env), input=stdin, timeout=timeout)


def make_sandbox(st: State, *, extra_specs: dict | None = None):
    """부트스트랩 ④(b) 뒤·(c) 전과 같은 상태(gate 있음, pre-receive 설치 안 함 -- direct는 게이트 함수를 직접 부른다,
    완료 표지 없음). 기준 커밋 B0에는 계획서, 게이트 코드, 판정 표 승인 기록, 흐름용 spec card가 있다."""
    require("CONFIG", "EL4")
    root = st.work / "sb"
    work, gate, wtroot = root / "work", root / "gate.git", root / "wt"
    wtroot.mkdir(parents=True, exist_ok=True)
    init_repo(work)
    # 파일
    plan = (REPO / PLAN_REL).read_bytes()
    write(work / PLAN_REL, plan, binary=True)
    copy_gate_tree(work)
    cfg_path = work / "tools/gates/gate_config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg.update({"gate_path": posix(gate), "workspace_path": posix(work), "python_path": posix(os.sys.executable)})
    cfg.pop("bootstrapped", None)
    cfg.pop("baseline_commit", None)
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write(work / "skills/analog-gmid-design/SKILL.md", "# analog-gmid-design (redteam sandbox)\n")
    write(work / "skills/analog-gmid-design/assets/rt_engine.py", ENGINE_B0)
    write(work / "skills/analog-gmid-design/assets/tests/test_rt_engine.py", TEST_B0)
    write(work / "skills/analog-gmid-design/assets/library/rt_demo.topology.json", '{"devices": []}\n')
    write(work / "skills/analog-gmid-design/assets/library/rt_demo.structure.json", '{"status": "draft", "nodes": []}\n')
    write(work / "rtl/core.v", "module core;\nendmodule\n")
    write(work / "skills/verilog-rtl/notes.md", "# notes\n")
    write(work / "docs/02-design/rt-notes.md", "# redteam notes\n")
    write(work / ".gitignore", "__pycache__/\n.pytest_cache/\nruns/\n")
    specs = {cid: (et, "1") for cid, et in FLOW_IDS.values()}
    specs.update(extra_specs or {})
    for cid, (et, phase) in specs.items():
        write(work / SPEC_DIR / f"{cid}.spec.md", spec_card(cid, phase, et))
    # 최초 판정 표 승인(§9.2-2 상태 기반 검사가 old에서 찾는다) -- 해시는 §15.2 CLI
    from iface import plan_tables_hash_command
    r = run_py(plan_tables_hash_command(os.sys.executable, str(work / "tools/gates/merge_gate.py"), str(work / PLAN_REL)),
               cwd=work)
    h = r.stdout.decode("utf-8", "replace").strip().splitlines()[-1].strip() if r.returncode == 0 and r.stdout.strip() else ""
    if r.returncode != 0 or len(h) != 64:
        raise RuntimeError(f"plan-tables-hash 실패(exit {r.returncode}): {r.stdout!r} {r.stderr[:600]!r}")
    write(work / ".ai/approvals/20260921-rt-plan-tables.md", approval_text(
        [("id", "20260921-rt-plan-tables"), ("date", "2026-09-21"), ("target_kind", "plan_tables"), ("target", h),
         ("scope", "redteam sandbox 최초 판정 표")]), binary=True)
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "redteam baseline", "--trailer", "Role: user")
    b0 = gout(work, "rev-parse", "HEAD")
    # gate
    init_repo(gate, bare=True)
    git(work, "remote", "add", "gate", posix(gate))
    git(work, "push", "-q", "gate", "master:master")
    (gate / "gmid-accept-log").write_text(f"{b0} {b0} {time.strftime('%Y-%m-%dT%H:%M:%S')}\n", encoding="utf-8")
    git(work, "fetch", "-q", "gate")
    common = gout(work, "rev-parse", "--git-common-dir")
    common = (work / common).resolve() if not Path(common).is_absolute() else Path(common)
    st.vars.update({"SB": posix(root), "WORK": posix(work), "GATE": posix(gate), "W": posix(wtroot), "B0": b0,
                    "GITDIR": posix(common), "CACHE": posix(common / "gmid-gate-cache" / b0),
                    "TEMPDIR": posix(TEMP_ROOT), "PY": posix(os.sys.executable), "PLAN_HASH": h, "SIDE": 0})
    st.save()


def side_ref(st: State) -> str:
    n = st.get("SIDE", 0) + 1
    st["SIDE"] = n
    return f"refs/redteam/c{n}"


def push_side(st: State, rev: str) -> str:
    """판정 대상 커밋을 gate에 데이터로 넣는다(pre-receive 없음 -- 판정은 merge_gate를 직접 부른다)."""
    ref = side_ref(st)
    git(st["WORK"], "push", "-q", "gate", f"{rev}:{ref}")
    return ref


def advance_gate_master(st: State, rev: str):
    """흐름 밖 준비 단계(판정 대상이 아님): gate master를 옮기고 작업 저장소가 받는다."""
    git(st["WORK"], "push", "-q", "-f", "gate", f"{rev}:refs/heads/master")
    git(st["WORK"], "fetch", "-q", "gate")


# --------------------------------------------------------------------------------------------------------------
# 변경 한 건 흐름(§12) -- 훅 없이 만든다(판정 대상은 결과 커밋이다)
# --------------------------------------------------------------------------------------------------------------
def wt(st: State, cid: str, role: str) -> Path:
    return Path(st["W"]) / f"{cid}-{role}"


def commit(cwd, msg: str, role: str | None = None, change_id: str | None = None, *, allow_empty=False):
    args = ["commit", "-q", "-m", msg]
    if role:
        args += ["--trailer", f"Role: {role}"]
    if change_id:
        args += ["--trailer", f"Change-Id: {change_id}"]
    if allow_empty:
        args.append("--allow-empty")
    git(cwd, *args)
    return gout(cwd, "rev-parse", "HEAD")


def flow_start(st: State, cid: str, base: str = "gate/master"):
    work = st["WORK"]
    old = gout(work, "rev-parse", base)
    git(work, "worktree", "add", "-q", posix(wt(st, cid, "test")), "-b", f"role/test/{cid}", old)
    st[f"{cid}.OLD"] = old
    st[f"{cid}.T"] = old


def flow_test(st: State, cid: str, *, n: int = 1, role: str = "test", change_id: str | None = None,
              extra_files: dict | None = None):
    t = wt(st, cid, "test")
    slug = cid.split("-", 1)[1].replace("-", "_")
    for i in range(n):
        name = f"skills/analog-gmid-design/assets/tests/test_{slug}_{i}.py"
        write(t / name, f"from rt_engine import rt_scale\n\n\ndef test_rt_scale_{i}():\n    assert rt_scale(2.0) == 6.0\n")
        for p, c in (extra_files or {}).items():
            write(t / p, c)
        git(t, "add", "-A")
        st[f"{cid}.T"] = commit(t, f"test {cid} #{i}", role, change_id or cid)


def ensure_audit_code(st: State, cid: str):
    work = st["WORK"]
    if not wt(st, cid, "audit").exists():
        git(work, "worktree", "add", "-q", posix(wt(st, cid, "audit")), "-b", f"role/audit/{cid}", f"role/test/{cid}")
    if not wt(st, cid, "code").exists():
        git(work, "worktree", "add", "-q", posix(wt(st, cid, "code")), "-b", f"role/code/{cid}", f"role/test/{cid}")


def flow_code(st: State, cid: str, *, role: str = "code", change_id: str | None = None, also_test=False,
              extra_role_test=False, equivalence=False, extra_files: dict | None = None):
    ensure_audit_code(st, cid)
    c = wt(st, cid, "code")
    if extra_role_test:          # 공격 20 (d): code 쪽에 끼운 Role: test 커밋 T'
        write(c / "skills/analog-gmid-design/assets/tests/test_rt_tprime.py",
              "def test_tprime():\n    assert True\n")
        git(c, "add", "-A")
        commit(c, f"T' {cid}", "test", cid)
    eng = c / "skills/analog-gmid-design/assets/rt_engine.py"
    src = eng.read_text(encoding="utf-8")
    if equivalence:
        src = src.replace("return gm * ro", "return ro * gm")
    else:
        src += '\n\ndef rt_scale(x):\n    """3배."""\n    return 3.0 * x\n'
    write(eng, src)
    if also_test:                # 공격 3: 소스와 tests를 한 커밋에
        tp = c / "skills/analog-gmid-design/assets/tests/test_rt_engine.py"
        write(tp, tp.read_text(encoding="utf-8").replace("== 100.0", "== pytest.approx(100.0, rel=0.5)"))
    for p, cont in (extra_files or {}).items():
        write(c / p, cont)
    git(c, "add", "-A")
    st[f"{cid}.K"] = commit(c, f"code {cid}", role, change_id or cid)


def flow_merge(st: State, cid: str, *, no_commit=False):
    a = wt(st, cid, "audit")
    msg2 = f"Role: doc\nChange-Id: {cid}"
    if no_commit:
        git(a, "merge", "--no-ff", "--no-commit", f"role/code/{cid}")
        return None
    git(a, "merge", "-q", "--no-ff", f"role/code/{cid}", "-m", f"merge {cid}", "-m", msg2)
    st[f"{cid}.M"] = gout(a, "rev-parse", "HEAD")
    return st[f"{cid}.M"]


def red_failure_hash(test_id: str, exc="builtins.AssertionError") -> str:
    """00-common §8.1: sha256(UTF-8(f"{test_id}\\n{module}.{qualname}"))."""
    return sha256_text(f"{test_id}\n{exc}")


def valid_record(st: State, cid: str, evidence_type: str) -> dict:
    old = st[f"{cid}.OLD"]
    t = st[f"{cid}.T"]
    k = st.get(f"{cid}.K")
    iso = posix(TEMP_ROOT / f"{cid}-iso")
    cache = f"{st['GITDIR']}/gmid-gate-cache/{old}"
    v1 = (f"V1: PYTHONPATH={cache} PYTHONPYCACHEPREFIX={posix(TEMP_ROOT)}/{cid}-pyc $PY -P -m pytest "
          f"-c {cache}/pytest_gate.ini --rootdir={iso} --confcutdir={iso} {iso}/skills/analog-gmid-design/assets/tests")
    na = {"V7": "도입 2: Phase 1 변경이라 V7(배선) 도입 전", "V8": "도입 4: Phase 1 변경이라 V8 도입 전",
          "V9": "도입 6b: Phase 1 변경이라 V9 도입 전"}
    checks = {}
    for i in range(1, 11):
        n = f"V{i}"
        if n in na:
            checks[n] = {"verdict": "N/A", "basis": na[n]}
        elif n == "V4":
            checks[n] = {"verdict": "PASS", "basis": "test_lint.py exit 0\noracle 대조: test_rt_scale 기대값 6.0 -- spec card (a) 구성으로 정한 합성 입력(3배)"}
        else:
            checks[n] = {"verdict": "PASS", "basis": f"{n} 격리 복제본 실행 결과 PASS"}
    rec = {
        "id": cid,
        "spec_card": f"{SPEC_DIR}/{cid}.spec.md",
        "evidence_type": evidence_type,
        "base_commit": old,
        "test_commit": t,
        "code_commit": k if evidence_type != "test-only" else None,
        "checks": checks,
        "reproduced_numbers": [{"name": "rt_gain_demo", "value": 1.5, "command": "$PY -c \"print(1.5)\""}],
        "approvals": [],
        "auditor_run": {"time": "2026-09-21T10:00:00+09:00", "worktree": posix(wt(st, cid, "audit")),
                        "commands": [v1, f"iso: git clone --no-hardlinks --no-local {posix(wt(st, cid, 'audit'))} {iso}"]},
    }
    if evidence_type == "red-green":
        tid = "skills/analog-gmid-design/assets/tests/test_%s_0.py::test_rt_scale_0" % cid.split("-", 1)[1].replace("-", "_")
        rec["red"] = {"test_ids": [tid], "failure_hashes": [red_failure_hash(tid)]}
    elif evidence_type == "equivalence":
        rec["equivalence"] = {"commands": ["$PY skills/analog-gmid-design/assets/rt_engine.py"],
                              "outputs_hash": sha256_text("")}
    else:
        checks["V2"]["basis"] = "섹션->test 매핑표의 모든 섹션이 변경 후 test에서 PASS"
    return rec


def _get_parent(obj, path):
    for k in path[:-1]:
        obj = obj[k]
    return obj


def render_record(st: State, rec: dict, ops: list, subst) -> bytes:
    """케이스 연산: set/del(객체), text_replace(직렬화 텍스트), prefix_hex·encoding·replace_bytes(바이트)."""
    for op in ops:
        kind = op["op"]
        if kind == "set":
            _get_parent(rec, op["path"])[op["path"][-1]] = subst(op["value"])
        elif kind == "del":
            del _get_parent(rec, op["path"])[op["path"][-1]]
        elif kind == "upper":
            parent = _get_parent(rec, op["path"])
            parent[op["path"][-1]] = parent[op["path"][-1]].upper()
        elif kind == "replace_record":
            rec = subst(op["value"])
    text = json.dumps(rec, ensure_ascii=False, indent=1)
    for op in ops:
        if op["op"] == "text_replace":
            old, new = subst(op["old"]), subst(op["new"])
            if old not in text:
                raise RuntimeError(f"text_replace 대상 없음: {old!r}")
            text = text.replace(old, new, op.get("count", 1))
    data = text.encode("utf-8")
    for op in ops:
        if op["op"] == "encoding":
            data = bytes.fromhex(op.get("bom_hex", "")) + text.encode(op["name"])
        elif op["op"] == "prefix_hex":
            data = bytes.fromhex(op["hex"]) + data
        elif op["op"] == "replace_bytes":
            data = data.replace(bytes.fromhex(op["old_hex"]), bytes.fromhex(op["new_hex"]), 1)
    return data


def audit_commit_plumbing(st: State, cid: str, parent: str, rec_bytes: bytes, *, role="audit", change_id=None,
                          rec_name: str | None = None, extra: dict | None = None) -> str:
    """판정 기록 한 파일을 parent 트리에 더한 커밋을 작업 트리를 건드리지 않고 만든다(임시 index + commit-tree)."""
    work = st["WORK"]
    idx = Path(st["SB"]) / f"idx-{time.time_ns()}"
    env = {"GIT_INDEX_FILE": str(idx)}
    git(work, "read-tree", parent, env=env)
    blobs = {f".ai/verification/{rec_name or cid}.json": rec_bytes}
    blobs.update(extra or {})
    for path, data in blobs.items():
        h = git(work, "hash-object", "-w", "--stdin", input_bytes=data).stdout.decode().strip()
        git(work, "update-index", "--add", "--cacheinfo", f"100644,{h},{path}", env=env)
    tree = git(work, "write-tree", env=env).stdout.decode().strip()
    idx.unlink(missing_ok=True)
    msg = f"audit {cid}\n\nRole: {role}\nChange-Id: {change_id or cid}\n"
    return git(work, "commit-tree", tree, "-p", parent, input_bytes=msg.encode("utf-8")).stdout.decode().strip()


def flow_audit(st: State, cid: str, evidence_type: str) -> str:
    a = wt(st, cid, "audit")
    rec = valid_record(st, cid, evidence_type)
    write(a / f".ai/verification/{cid}.json", json.dumps(rec, ensure_ascii=False, indent=1))
    git(a, "add", "--", f".ai/verification/{cid}.json")
    st[f"{cid}.NEW"] = commit(a, f"audit {cid}", "audit", cid)
    return st[f"{cid}.NEW"]


def flow_full(st: State, key: str, *, cid: str | None = None, evidence_type: str | None = None, base="gate/master",
              audit=True, **kw):
    cid0, et0 = FLOW_IDS.get(key, (None, None))
    cid, et = cid or cid0, evidence_type or et0
    flow_start(st, cid, base)
    if et in ("red-green", "test-only"):
        flow_test(st, cid, role=kw.get("test_role", "test"))
    if et == "test-only":
        git(st["WORK"], "worktree", "add", "-q", posix(wt(st, cid, "audit")), "-b", f"role/audit/{cid}", f"role/test/{cid}")
    else:
        flow_code(st, cid, role=kw.get("code_role", "code"), change_id=kw.get("code_change_id"),
                  also_test=kw.get("also_test", False), extra_role_test=kw.get("extra_role_test", False),
                  equivalence=(et == "equivalence"), extra_files=kw.get("code_extra_files"))
        flow_merge(st, cid)
    if audit:
        flow_audit(st, cid, et)
    return cid, et


def diff_hash(repo, base: str, head_blobs: dict[str, str | None], paths: list[str]) -> str:
    """00-common §8.2 diff 해시(blob 기반): sha256("".join(f"{path}\\t{base_blob}\\t{head_blob}\\n" ...))."""
    out = []
    for p in sorted(paths):
        r = git(repo, "rev-parse", "--verify", "--quiet", f"{base}:{p}", check=False)
        bb = r.stdout.decode().strip() if r.returncode == 0 else "-"
        hb = head_blobs.get(p) or "-"
        out.append(f"{p}\t{bb}\t{hb}\n")
    return sha256_text("".join(out))


def blob_of(repo, data: bytes) -> str:
    return git(repo, "hash-object", "--stdin", input_bytes=data).stdout.decode().strip()
