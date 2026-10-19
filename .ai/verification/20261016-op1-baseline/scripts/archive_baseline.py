# -*- coding: utf-8 -*-
"""OP-1a 기준선 보관(검증자 gmid-verification-auditor 작성·소유).

입력: 원자료 루트 RAW(= wt/_scratch_op1/baseline, 5,133 파일), base 판 오라클 test 소스(격리 복제본 ISO, base 5fea301).
출력(DST = <audit worktree>/.ai/verification/<id>/baseline):
  files/<rel>            판정용 텍스트(규칙 SELECT) 복사본 -- 바이트 그대로(같은 폴더 .gitattributes `* -text`)
  _sha256_all.tsv        원자료 전 파일: rel, size, sha256, class, committed(1/0)
  _external.json         저장소 밖에 두는 파일 묶음별 수·바이트, PDK 모델 사본의 원본 대응
  _log_excerpt.jsonl     기준선 로그(.log) 줄 발췌: 줄 번호(1부터) + 줄 텍스트(OP-1 m8 정규식 + stepping/note 줄)
  _test_tmp_map.json     junit test -> tmp 폴더 대응(tmp_path 이름 규칙 + mktemp 이름 AST 대응)
분류 규칙(SELECT): 확장자 json·md·cir·xml·npz, 이름 console.txt·oracle_run.stdout.txt, 이름 끝 .mc.log(DV-5 표본별 op 값),
  MC 로그와 같은 폴더·같은 stem의 .ac.txt(DV-5 A 원천), .spice 중 PDK 원본(C:/pdk/sky130_fd_pr 아래 같은 이름 파일)과 sha256이 다른 것(test가 만든 래퍼·변형 -- 텍스트 입력).
  나머지(.txt 데이터·.log·PDK 동일 사본·캐시 슬롯 done/rc)는 저장소 밖, 목록에 경로·sha256만.
"""
import ast
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET

RAW, ISO, DST, PDK = sys.argv[1:5]
O_TESTS = os.path.join(ISO, "skills/analog-gmid-design/tools/spice_oracle/tests")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# PDK 원본 이름 -> [(경로, sha256)]
pdk_by_name = {}
for p in glob.glob(PDK + "/**/*.spice", recursive=True):
    pdk_by_name.setdefault(os.path.basename(p), []).append(p.replace("\\", "/"))
pdk_sha_cache = {}


def pdk_match(rel, s):
    for p in pdk_by_name.get(os.path.basename(rel), []):
        if p not in pdk_sha_cache:
            pdk_sha_cache[p] = sha(p)
        if pdk_sha_cache[p] == s:
            return p
    return None


rows, ext_groups, pdk_copies = [], {}, []
files = sorted(os.path.relpath(p, RAW).replace("\\", "/") for p in glob.glob(RAW + "/**/*", recursive=True) if os.path.isfile(p))
MC_AC = {f[:-len(".mc.log")] + ".ac.txt" for f in files if f.endswith(".mc.log")}   # DV-5 차동 이득 A 원천(.ac 첫 점)
for rel in files:
    p = os.path.join(RAW, rel)
    s, n = sha(p), os.path.getsize(p)
    base = os.path.basename(rel)
    ext = base.rsplit(".", 1)[1].lower() if "." in base else ""
    if ext in ("json", "md", "cir", "xml", "npz"):
        cls, keep = ext, True
    elif base in ("console.txt", "oracle_run.stdout.txt"):
        cls, keep = "console", True
    elif base.endswith(".mc.log"):
        cls, keep = "mc_log", True
    elif rel in MC_AC:
        cls, keep = "mc_ac", True
    elif ext == "spice":
        m = pdk_match(rel, s)
        if m:
            cls, keep = "pdk_model_copy", False
            pdk_copies.append({"rel": rel, "sha256": s, "pdk_original": m})
        else:
            cls, keep = "spice_test_made", True
    elif ext == "":
        cls, keep = "cache_slot", False
    elif ext == "txt":
        cls, keep = "sim_data_txt", False
    elif ext == "log":
        cls, keep = "sim_log", False
    else:
        cls, keep = "other_" + ext, False
    rows.append((rel, n, s, cls, keep))
    if keep:
        q = os.path.join(DST, "files", rel)
        os.makedirs(os.path.dirname(q), exist_ok=True)
        shutil.copyfile(p, q)
    else:
        g = ext_groups.setdefault(cls, {"n": 0, "bytes": 0})
        g["n"] += 1
        g["bytes"] += n

os.makedirs(DST, exist_ok=True)
with open(os.path.join(DST, "_sha256_all.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("rel\tsize\tsha256\tclass\tcommitted\n")
    for rel, n, s, cls, keep in rows:
        f.write(f"{rel}\t{n}\t{s}\t{cls}\t{1 if keep else 0}\n")

# 로그 발췌 -- OP-1 m8_errlog.py 정규식 그대로 + 회복 경위 줄(stepping, Note:)
OLD = re.compile(r"error|fatal|singular|abort", re.I)
PZ = re.compile(r"giving up|iteration limit|singular matrix", re.I)
MORE = re.compile(r"timestep too small|no convergence|not converge|gmin step|source step|could not find|unable to find|unknown|"
                  r"cannot|can't|failed|warning", re.I)
CTX = re.compile(r"stepping|^\s*note:", re.I)
n_ex = 0
with open(os.path.join(DST, "_log_excerpt.jsonl"), "w", encoding="utf-8", newline="\n") as f:
    for rel, n, s, cls, keep in rows:
        if not rel.endswith(".log"):
            continue
        with open(os.path.join(RAW, rel), encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        hit = [(i + 1, ln) for i, ln in enumerate(lines) if OLD.search(ln) or PZ.search(ln) or MORE.search(ln) or CTX.search(ln)]
        if hit:
            f.write(json.dumps({"rel": rel, "sha256": s, "n_lines": len(lines),
                                "lines": [[i, ln, bool(OLD.search(ln)), bool(PZ.search(ln))] for i, ln in hit]},
                               ensure_ascii=False) + "\n")
            n_ex += len(hit)

# test -> tmp 폴더 대응
junit = ET.parse(os.path.join(RAW, "pytest/junit.xml")).getroot()
tests = []
for tc in junit.iter("testcase"):
    cn, nm = tc.get("classname"), tc.get("name")
    st = "skipped" if tc.find("skipped") is not None else ("failed" if tc.find("failure") is not None or tc.find("error") is not None
                                                           else "passed")
    tests.append({"classname": cn, "name": nm, "status": st})
tmpdirs = sorted(d for d in os.listdir(os.path.join(RAW, "pytest/tmp")) if os.path.isdir(os.path.join(RAW, "pytest/tmp", d)))
# (1) tmp_path: pytest 9.0.2 TempPathFactory 규칙 -- re.sub(r"[\W]", "_", node.name)[:30] + 번호(실행 순서)
groups = {}
for t in tests:
    groups.setdefault(re.sub(r"[\W]", "_", t["name"])[:30], []).append(t)
assigned = {}
prefixes = sorted(groups, key=len, reverse=True)
for d in tmpdirs:
    for pf in prefixes:
        m = re.fullmatch(re.escape(pf) + r"(\d+)", d)
        if m:
            assigned.setdefault(pf, []).append((int(m.group(1)), d))
            break
tmp_path_map, ambiguous = [], []
for pf, ds in assigned.items():
    ds.sort()
    ts = groups[pf]
    if len(ds) == len(ts) and [k for k, _ in ds] == list(range(len(ds))):
        for t, (_, d) in zip(ts, ds):
            tmp_path_map.append({"dir": d, "test": f"{t['classname']}::{t['name']}", "rule": "tmp_path 이름 규칙, 그룹 크기 일치"})
    else:
        ambiguous.append({"prefix": pf, "dirs": [d for _, d in ds], "tests": [f"{t['classname']}::{t['name']}" for t in ts],
                          "rule": "tmp_path 이름 규칙, 그룹 안 test 일부만 tmp_path 사용 -- 실행 순서 번호만 확정"})
# (2) mktemp("<이름>"): base 판 test 소스 AST
mk = []
for p in sorted(glob.glob(O_TESTS + "/*.py")):
    src = open(p, encoding="utf-8").read()
    tree = ast.parse(src)
    mod = os.path.basename(p)[:-3]
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef):
            continue
        for c in ast.walk(fn):
            if isinstance(c, ast.Call) and getattr(c.func, "attr", None) == "mktemp" and c.args and isinstance(c.args[0], ast.Constant):
                fixture = any("fixture" in ast.unparse(dc) for dc in fn.decorator_list)
                mk.append({"name": c.args[0].value, "file": f"tools/spice_oracle/tests/{mod}.py", "line": c.lineno, "def": fn.name,
                           "is_fixture": fixture, "module": mod})
mk_map = []
for e in mk:
    ds = [d for d in tmpdirs if re.fullmatch(re.escape(e["name"]) + r"\d+", d)]
    users = []
    if e["is_fixture"]:
        for t in tests:
            fmod = t["classname"].rsplit(".", 1)[-1]
            if e["module"] != "conftest" and fmod != e["module"]:
                continue
            p = os.path.join(O_TESTS, fmod + ".py")
            tree = ast.parse(open(p, encoding="utf-8").read())
            fname = t["name"].split("[")[0]
            for fn in ast.walk(tree):
                if isinstance(fn, ast.FunctionDef) and fn.name == fname and e["def"] in [a.arg for a in fn.args.args]:
                    users.append(f"{t['classname']}::{t['name']}")
                    break
    else:
        users = [f"{t['classname']}::{t['name']}" for t in tests if t["name"].split("[")[0] == e["def"]]
    note = None
    if e["is_fixture"] and not users:
        note = "인자로 직접 받는 test 0 -- request.getfixturevalue 간접 사용 등은 AST 대응 밖(원문 확인)" if ds else "기준선 실행에서 폴더 없음(fixture 미사용 또는 skip)"
    mk_map.append(dict(e, dirs=ds, used_by_tests=users, note=note))
mapped = {x["dir"] for x in tmp_path_map} | {d for a in ambiguous for d in a["dirs"]} | {d for e in mk_map for d in e["dirs"]}
json.dump({"junit": "pytest/junit.xml", "n_tests": len(tests), "n_tmp_dirs": len(tmpdirs),
           "status_counts": {k: sum(1 for t in tests if t["status"] == k) for k in ("passed", "skipped", "failed")},
           "tmp_path_map": tmp_path_map, "tmp_path_ambiguous_groups": ambiguous, "mktemp_map": mk_map,
           "unmapped_dirs": [d for d in tmpdirs if d not in mapped]},
          open(os.path.join(DST, "_test_tmp_map.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)

kept = [r for r in rows if r[4]]
json.dump({"raw_root": RAW.replace("\\", "/"), "n_files_total": len(rows), "bytes_total": sum(r[1] for r in rows),
           "n_committed": len(kept), "bytes_committed": sum(r[1] for r in kept),
           "committed_by_class": {c: {"n": sum(1 for r in kept if r[3] == c), "bytes": sum(r[1] for r in kept if r[3] == c)}
                                  for c in sorted({r[3] for r in kept})},
           "external_by_class": ext_groups, "pdk_root": PDK.replace("\\", "/"), "pdk_model_copies": pdk_copies,
           "log_excerpt_lines": n_ex},
          open(os.path.join(DST, "_external.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print(json.dumps({"n": len(rows), "kept": len(kept), "kept_bytes": sum(r[1] for r in kept), "external": ext_groups,
                  "pdk_copies": len(pdk_copies), "excerpt_lines": n_ex, "tmp_path_map": len(tmp_path_map),
                  "ambiguous": len(ambiguous), "mktemp": len(mk_map),
                  "unmapped": [d for d in tmpdirs if d not in mapped]}, ensure_ascii=False))
