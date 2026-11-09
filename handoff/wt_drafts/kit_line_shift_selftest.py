#!/usr/bin/env python3
"""kit_line_shift.py 자기 시험 -- 검토 review_kit_line_shift.md의 최소 재현(S1·S2·S3·m1~m9)을 합성 저장소에서 돌린다.

r2: 재검토 review_kit_line_shift_r1.md의 S-A(measured 표지 -> anchored)·S-B(절 표지 번짐·병기 -> ambiguous)·
m1(범위 사이 덩어리)·m2(두 자리·문장 끝 마침표)·m3(줄에 의심 인용)·m5(`SR·SD n`)·m6(옛 b1 대입) 재현을 더했다.

모래상자 KLS_SB(기본 C:/g340/st, TMP/TEMP도 그 아래). 현재 디렉터리(".")는 쓰지 않는다. 끝나면 모래상자를 지운다.
결과는 KLS_OUT(기본 _drafts/kit_line_shift_selftest.out.txt)에 케이스마다 덧붙인다. 하나라도 FAIL이면 rc 1.
다른 판 도구를 시험하려면 KLS_TOOL=<경로>(예 kit_line_shift.py.pre-r2.bak -- 새 시험이 옛 판에서 FAIL하는지 확인).
실행: python kit_line_shift_selftest.py
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SB = os.environ.get("KLS_SB", "C:/g340/st")
TMP = SB + "/tmp"
OUT = os.environ.get("KLS_OUT", os.path.join(HERE, "kit_line_shift_selftest.out.txt"))
TOOL = os.environ.get("KLS_TOOL", os.path.join(HERE, "kit_line_shift.py"))
GITC = ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false",
        "-c", "core.hooksPath=" + SB + "/nohooks", "-c", "commit.gpgsign=false"]
SR, SD = "skills/a/sizing_recipe.py", "skills/a/stick_diagram.py"

from importlib.machinery import SourceFileLoader  # noqa: E402  (.bak 확장자도 읽게)
spec = importlib.util.spec_from_file_location("kls", TOOL, loader=SourceFileLoader("kls", TOOL))
kls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kls)

RESULTS = []


def log(msg):
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(msg + "\n")
    print(msg)


def check(name, cond, detail=""):
    RESULTS.append(cond)
    log("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))


def git(repo, *args):
    p = subprocess.run(["git", *GITC, "-C", repo, *args], capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("git %s: %s" % (args, p.stderr.decode("utf-8", "replace")))
    return p.stdout.decode().strip()


def engine_text(prefix, n=3000, nl="\n", common=True, big=False):
    out = []
    for i in range(1, n + 1):
        if common and i == 500:
            out.append("common = 1")
        elif big and i == 2500:
            out.append("def big_func():")
        elif big and 2501 <= i <= 2600:
            out.append("    %s_line_%d = %d" % (prefix, i, i))
        else:
            out.append("%s_line_%d = %d" % (prefix, i, i))
    return nl.join(out) + nl


def insert_after(text, after, k, nl="\n"):
    ls = text.split(nl)
    return nl.join(ls[:after] + ["ins_%d = %d" % (j, j) for j in range(k)] + ls[after:])


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))


def make_repo(name, nl="\n", attrs=None, nul=False, rename=False, sr_mod=None):
    """old = SR·SD 3000줄, new = 40행 뒤 5줄 삽입(sr_mod가 있으면 SR new = sr_mod(old 글)). 반환 (repo, old_sha, new_sha)."""
    repo = SB + "/" + name
    os.makedirs(repo)
    git(repo, "init", "-q")
    sr, sd = engine_text("sr", nl=nl, big=True), engine_text("sd", nl=nl)
    if nul:
        sr = sr.replace("sr_line_10 = 10", "sr_line_10 = '\x00'")
    write(repo + "/" + SR, sr)
    write(repo + "/" + SD, sd)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "old")
    old = git(repo, "rev-parse", "HEAD")
    write(repo + "/" + SR, sr_mod(sr) if sr_mod else insert_after(sr, 40, 5, nl))
    write(repo + "/" + SD, insert_after(sd, 40, 5, nl))
    if attrs:
        write(repo + "/.gitattributes", attrs)
    if rename:
        git(repo, "mv", SR, "skills/a/sizing_recipe2.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "new")
    return repo, old, git(repo, "rev-parse", "HEAD")


def run(repo, old, new, drafts_root, drafts, out, bases=(), extra=()):
    argv = ["--repo", repo, "--old", old, "--new", new, "--engine", "SR=" + SR, "--engine", "SD=" + SD,
            "--drafts-root", drafts_root, "--out-dir", out, *extra]
    for b in bases:
        argv += ["--base", b]
    for d in drafts:
        argv += ["--draft", d]
    kls.main(argv)
    with open(out + "/kit_line_shift.json", encoding="utf-8") as fh:
        return json.load(fh)["records"]


def rmtree(path):
    """git 객체 파일(읽기 전용)도 지운다."""
    def onerr(func, p, _exc):
        os.chmod(p, 0o700)
        func(p)
    if os.path.exists(path):
        shutil.rmtree(path, onexc=onerr)


def main():
    rmtree(SB)
    os.makedirs(TMP)
    os.makedirs(SB + "/nohooks")
    os.environ["TMP"] = os.environ["TEMP"] = TMP
    tempfile.tempdir = TMP
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("kit_line_shift selftest\n")
    try:
        cases()
    finally:
        rmtree(SB)
        log("sandbox removed: %s" % (not os.path.exists(SB)))
    n_fail = RESULTS.count(False)
    log("TOTAL %d, FAIL %d" % (len(RESULTS), n_fail))
    return 1 if n_fail else 0


def cases():
    repo, old, new = make_repo("r1")
    # 모의 base b1 = 로컬 파일(old SD 사본)
    b1f = SB + "/g83/b1/" + SD
    write(b1f, engine_text("sd"))
    drafts = SB + "/drafts"
    # (줄, 기대: {old: new} 패치되는 것, 패치되면 안 되는 수 목록, 신뢰도 점검 {old: conf})
    L = [
        ("SR 1200", {1200: 1205}, [], {1200: "medium"}),
        ("`sr_line_1200 = 1200` sizing_recipe.py:1200", {1200: 1205}, [], {1200: "high"}),
        ("SR 1200 `sr_line_1200`", {1200: 1205}, [], {1200: "medium"}),                 # 식별자 하나는 high 근거 아님
        ("SR 2550 big_func", {2550: 2555}, [], {2550: "medium"}),                       # def-ok만으로는 high 아님
        ("* `sr_line_1200` 근처, sizing_recipe.py:1205", {}, [1205], {1205: "already-new"}),
        ("* 주석, sizing_recipe.py:1205~1206:", {}, [1205, 1206], {1205: "already-new", 1206: "already-new"}),
        ("  > `sr_line_1200 = 1200`", {}, [], {}),
        ("  > `sr_line_1201 = 1201`", {}, [], {}),
        ("* 주석, sizing_recipe.py:1200~1201:", {1200: 1205, 1201: 1206}, [], {1200: "high", 1201: "high"}),
        ("  > `sr_line_1200 = 1200`", {}, [], {}),
        ("  > `sr_line_1201 = 1201`", {}, [], {}),
        ("exp = {1205: b'sr_line_1200 = 1200'}", {}, [1205], {1205: "already-new"}),
        ("", {}, [], {}),                                                               # 바로 옆 줄이면 옛·새 쌍으로 본다
        ("exp = {1200: b'sr_line_1200 = 1200'}", {1200: 1205}, [], {1200: "high"}),
        ("exp = {500: b'common = 1'}", {}, [500], {500: "ambiguous"}),                 # m2 두 엔진 모두
        ("SR 130줄을 고쳤다", {}, [130], {}),
        ("SR 2026년 10월 6일", {}, [2026], {}),
        ("SR 2026/10/06", {}, [2026], {}),
        ("SR 2026", {}, [2026], {}),
        ("SR 1200 2026년", {1200: 1205}, [2026], {}),
        ("SR 1200 / 2026", {1200: 1205}, [2026], {}),
        ("SD 512 MB", {}, [512], {}),
        ("SR 100% 통과", {}, [100], {}),
        ("SR 300 tests passed", {}, [300], {}),
        ("SR: 300 passed", {}, [300], {}),
        ("SR 1200·133개", {1200: 1205}, [133], {}),
        ("sizing_recipe.py 3000줄 중 1200", {}, [3000, 1200], {}),
        ("SR 1200 → 1205(이미 옮긴 값)", {}, [1200, 1205], {1200: "ambiguous", 1205: "ambiguous"}),
        ("SR 1200->1205", {}, [1200, 1205], {}),
        ("`C:/g83/b1/skills/a/stick_diagram.py:1200`", {}, [1200], {1200: "ambiguous"}),   # m3
        ("SR 9024→9016줄", {}, [9024, 9016], {}),
        ("SR 12345", {}, [12345], {}),
        ("SR 2026-10-06", {}, [2026], {}),
        ("SR v1.2.300", {}, [300], {}),
        ("SR 0x1234", {}, [1234], {}),
        ("SR 3.14159", {}, [14159], {}),
        ("SR 1,200줄", {}, [200], {}),
        ("SR 1234567", {}, [], {}),
        ("SR 래치 1200", {}, [1200], {}),
        ("SR latch 1200", {}, [1200], {}),
        ("| SR | 1200 | 1300 |", {}, [1200, 1300], {}),
        ("PR #1234, SR", {}, [1234], {}),
        ("SR 1200 (a1b2c3d)", {}, [1200], {}),
        ("SD 1567(b34 1563)", {}, [1567, 1563], {}),
        ("SR 1200(B34 사본 1195)", {}, [1200, 1195], {}),
        ("sizing_recipe.py:1200, test_sizing_recipe.py:1300", {1200: 1205}, [1300], {}),
        ("SR 1200-1210", {}, [1200, 1210], {1200: "ambiguous", 1210: "ambiguous"}),   # m4 시작 수도 보고
        ("SR 01200", {}, [1200], {}),                                                   # m8
        ("SR 3000", {3000: 3005}, [], {}),
        ("SR 3001", {}, [3001], {3001: "low"}),                                         # m6 길이+1
        ("SR 1195 이전", {1195: 1200}, [], {}),
        # 절 표지: new rev 줄 번호라고 적힌 절 -- 아래 인용은 이미 옮긴 것
        ("## 근거(gate `master` `%s` 줄 번호)" % new[:7], {}, [], {}),
        # r2 S-B: 위 줄에서 이어 온 new 표지는 already-new가 아니라 ambiguous(section-inherited) -- 패치 밖은 같다
        ("* SR 1205, SD 1210", {}, [1205, 1210], {1205: "ambiguous", 1210: "ambiguous"}),
        ("SITE_SD = [1014, 1571]", {}, [1014, 1571], {1014: "ambiguous"}),
        # 다음 절 표지(old) -- 다시 옮긴다
        ("## 옛 절(줄 번호는 `%s`)" % old[:7], {}, [], {}),
        ("* SR 1205", {1205: 1210}, [], {1205: "medium"}),
        # 줄에 인용 여럿 + 조각이 new 같은 번호 줄과 맞음 -> ambiguous, 범위 짝도 함께 패치 밖
        ("sizing_recipe.py 1201~1205, `sr_line_1200 = 1200`", {}, [1201, 1205], {1201: "ambiguous", 1205: "ambiguous"}),
        # 한 줄에 표지 둘: measured rev가 이긴다. r2 S-A: measured rev ≡ base -> 측정 기록이라 anchored(패치 밖)
        ("(gate master `%s` 재측정 -- measured rev는 `%s` 그대로)" % (new[:7], old[:7]), {}, [], {}),
        ("* SR 1200", {}, [1200], {1200: "anchored"}),
        # 새 값이 곁에 이미 있다: 옛·새 판 리터럴을 나란히 둔 조건식, `SD 1210(b34 1215)`
        ("exp = ({1205: b'sr_line_1200 = 1200'} if new_rev else", {}, [1205], {1205: "already-new"}),
        ("       {1200: b'sr_line_1200 = 1200'})", {}, [1200], {1200: "ambiguous"}),
        ("| x | `sd_line_1210 = 1210` | SD 1210(b34 1215) |", {}, [1210, 1215], {1210: "ambiguous"}),
    ]
    text = "\n".join(t for t, *_ in L) + "\n"
    write(drafts + "/d.md", text)
    # m5: U+2028 / \x0c 가 있는 초안 -- 줄 번호는 \n 기준
    write(drafts + "/u.md", "x\u2028y\nSR 1200\n\x0cz\x85w\nSR 1300")
    recs = run(repo, old, new, drafts, ["d.md", "u.md"], SB + "/out1", bases=["b1=SD:" + b1f])
    by = {}
    for r in recs:
        by.setdefault((r["file"], r["line"]), []).append(r)
    for i, (t, want_p, not_p, confs) in enumerate(L, 1):
        rs = by.get(("d.md", i), [])
        got_p = {r["old"]: r["new"] for r in rs if r.get("patched")}
        ok = got_p == want_p and not any(n in got_p for n in not_p)
        for n, c in confs.items():
            cc = [r["confidence"] for r in rs if r["old"] == n and r["how"] not in ("bare", "untied")]
            ok = ok and cc and all(x == c for x in cc)
        check("d.md:%d %r" % (i, t), ok, "patched=%s conf=%s" % (got_p, {r["old"]: r["confidence"] for r in rs}))
    u = {(r["line"], r["old"]): r for r in recs if r["file"] == "u.md"}
    check("m5 U+2028/\\x0c 줄 번호", (2, 1200) in u and (4, 1300) in u and u[(2, 1200)].get("patched")
          and u[(4, 1300)].get("patched"), str(sorted(u)))
    # patch가 초안에 그대로 적용되는가(m5, CRLF·끝 개행 없음 포함)
    p = subprocess.run(["git", "-C", drafts, "apply", "--check", "-p1", SB + "/out1/kit_line_shift.patch"], capture_output=True)
    check("patch git apply --check", p.returncode == 0, p.stderr.decode("utf-8", "replace"))

    # m1: CRLF 엔진에서 리터럴 대조
    repo2, old2, new2 = make_repo("r2", nl="\r\n")
    write(SB + "/drafts2/c.py", "exp = {1200: b'sr_line_1200 = 1200'}\n")
    rs = [r for r in run(repo2, old2, new2, SB + "/drafts2", ["c.py"], SB + "/out2") if r["how"] == "literal"]
    check("m1 CRLF 엔진 리터럴", len(rs) == 1 and rs[0]["confidence"] == "high" and rs[0]["new"] == 1205 and rs[0]["patched"],
          str([(r["confidence"], r["new"]) for r in rs]))

    # S3: 바이너리 판정(.gitattributes -diff, NUL 바이트)에도 덩어리를 읽는다
    write(SB + "/drafts3/s.md", "SR 1200\n")
    for nm, kw in (("r3", {"attrs": "*.py -diff\n"}), ("r4", {"nul": True})):
        r, o, n = make_repo(nm, **kw)
        rs = run(r, o, n, SB + "/drafts3", ["s.md"], SB + "/out_" + nm)
        check("S3 %s %s" % (nm, kw), len(rs) == 1 and rs[0]["new"] == 1205 and rs[0]["patched"],
              str([(x["confidence"], x["new"]) for x in rs]))
    # S3 단언: 덩어리를 빠뜨리면 멈춘다
    orig = kls.parse_hunks
    kls.parse_hunks = lambda d: []
    try:
        run(repo, old, new, SB + "/drafts3", ["s.md"], SB + "/out5")
        check("S3 Σ 단언(덩어리 빠짐 -> 멈춤)", False, "멈추지 않음")
    except SystemExit as e:
        check("S3 Σ 단언(덩어리 빠짐 -> 멈춤)", "Σ" in str(e), str(e)[:120])
    finally:
        kls.parse_hunks = orig
    # m9: 이름 바뀐 엔진은 지원 밖 -- 조용히 틀리지 않고 멈춘다
    r6, o6, n6 = make_repo("r6", rename=True)
    try:
        run(r6, o6, n6, SB + "/drafts3", ["s.md"], SB + "/out6")
        check("m9 이름 바뀐 엔진 -> 멈춤", False, "멈추지 않음")
    except SystemExit as e:
        check("m9 이름 바뀐 엔진 -> 멈춤", "git show" in str(e), str(e)[:120])
    # S1 재실행: 패치를 적용한 사본 + 절 표지(new)면 다시 옮기지 않는다
    shutil.copytree(SB + "/drafts3", SB + "/drafts7")
    write(SB + "/drafts7/s.md", "줄 번호는 `%s`\nSR 1205\n" % new[:7])
    rs = run(repo, old, new, SB + "/drafts7", ["s.md"], SB + "/out7")
    # r2: 위 줄 표지는 이어 온 것이라 ambiguous(section-inherited) -- 이중 이동 0은 같다
    check("S1 재실행 절 표지 -> 이중 이동 0", not any(r.get("patched") for r in rs) and
          any(r["confidence"] in ("already-new", "ambiguous") and
              any(ev.startswith(("section-rev", "section-inherited")) for ev in r["evidence"]) for r in rs),
          str([(r["old"], r["confidence"], r["evidence"]) for r in rs]))
    cases_r2(repo, old, new, b1f)


def cases_r2(repo, old, new, b1f):
    """재검토 r1(review_kit_line_shift_r1.md) S-A·S-B·m1·m2·m3·m5·m6 재현. repo: old -> new = SR·SD 40행 뒤 5줄 삽입."""
    o, n = old[:7], new[:7]
    root = SB + "/drafts_r2"

    def go(name, lines, tag, bases=(), extra=(), draft=None):
        write(root + "/" + name, "\n".join(lines) + "\n")
        recs = run(repo, old, new, root, [draft or name], SB + "/out_r2_" + tag, bases=bases, extra=extra)
        return {(r["line"], r["old"]): r for r in recs if r["file"] == name}

    def want(name, got, key, conf=None, patched=None, new_v=None, ev=None):
        r = got.get(key)
        ok = r is not None
        if ok and conf is not None:
            ok = r["confidence"] == conf
        if ok and patched is not None:
            ok = bool(r.get("patched")) == patched
        if ok and new_v is not None:
            ok = r["new"] == new_v
        if ok and ev is not None:
            ok = any(e.startswith(ev) for e in r["evidence"])
        check("r2 %s L%d %d" % (name, key[0], key[1]), ok,
              "" if r is None else "conf=%s patched=%s new=%s ev=%s" % (r["confidence"], r.get("patched"), r["new"], r["evidence"]))

    # S-A (1): 문서 전체 measured 선언('이 card의'와 같은 줄) -- 앞·뒤 줄의 base 인용 모두 anchored, 패치 밖
    sa = ["* SR 1200 앞 절 인용",
          "**measured at `%s`** -- 이 card의 줄 인용은 그대로다." % o,
          "* SR 1300",
          "(재측정 gate master `%s` -- measured rev는 `%s` 그대로)" % (n, o),
          "* SD 1210"]
    g = go("sa.md", sa, "sa")
    want("sa.md", g, (1, 1200), "anchored", False, 1205, "measured-rev")
    want("sa.md", g, (3, 1300), "anchored", False, 1305, "measured-rev")
    want("sa.md", g, (5, 1210), "anchored", False, 1215, "measured-rev")
    # --include-anchored면 옮긴다(측정 rev를 새로 앵커할 때)
    g = go("sa.md", sa, "sa_inc", extra=["--include-anchored"])
    want("sa.md(--include-anchored)", g, (1, 1200), "anchored", True, 1205)
    # S-A (2): '이 card의' 없는 measured 표지 -- 그 아래만 anchored, 앞 줄은 그대로 옮긴다
    g = go("sa2.md", ["* SR 1200", "measured rev는 `%s`" % o, "* SR 1200"], "sa2")
    want("sa2.md", g, (1, 1200), "medium", True, 1205)
    want("sa2.md", g, (3, 1200), "anchored", False, 1205)
    # S-A (3): measured 표지 아래라도 이미 다른 이유로 강등된 인용은 그 근거를 잃지 않는다(new-value-present)
    g = go("sa3.md", ["measured rev는 `%s`" % o, "| x | `sd_line_1210 = 1210` | SD 1210(b34 1215) |"], "sa3")
    want("sa3.md", g, (2, 1210), "ambiguous", False)

    # S-B (1): 두 줄에 걸친 병기('줄 번호는 <old>와' / '<new>') -- 아래 문단의 낡은 인용을 already-new라 하지 않는다
    sb = ["줄 번호는 gate `master` `%s`(병합 전)와" % o,
          "실제 병합본 gate `master` `%s`(병합 뒤):" % n,
          "",
          "| 9 | f | 1200 / 1205 | x |",
          "",
          "**범위 밖**: SR 1300·1301, SD 1222"]
    g = go("sb.md", sb, "sb")
    want("sb.md", g, (6, 1300), "ambiguous", False, 1305, "section-inherited")
    want("sb.md", g, (6, 1301), "ambiguous", False, 1306, "section-inherited")
    want("sb.md", g, (6, 1222), "ambiguous", False, 1227, "section-inherited")
    # S-B (2): 한 줄 병기 -- 두 rev의 엔진 상태가 갈리면 mixed(그 줄과 아래 줄)
    g = go("sb2.md", ["줄 번호는 `%s` / `%s`: SR 1200·1205" % (o, n), "* SR 1300"], "sb2")
    want("sb2.md", g, (1, 1200), "ambiguous", False, None, "section-mixed")
    want("sb2.md", g, (2, 1300), "ambiguous", False, 1305, "section-mixed")
    # S-B (2b): 숫자만인 짧은 해시 표지(draft_b26_1 35행 `7535799`)와 표 머리 병기 `줄(A / B)`를 읽는다(순수 함수)
    fs1 = sorted({x[1] for x in kls.find_sections("줄 번호는 gate `master` `7535799`(B34·P9 병합 전 HEAD)와")})
    fs2 = sorted({x[1] for x in kls.find_sections("| # | 함수 | 줄(7535799 / 2183f2e) | 바꾸는 것 |")})
    check("r2 find_sections 숫자만 해시·표 머리 병기", fs1 == ["7535799"] and fs2 == ["2183f2e", "7535799"], "%s %s" % (fs1, fs2))
    # S-B (3): 출처 설명 문장 아래의 낡은 인용(review adv L22·L24)
    g = go("sb3.md", ["모의 base는 gate master `%s` archive에서 가져왔다." % n, "옛 인용 SR 1300"], "sb3")
    want("sb3.md", g, (2, 1300), "ambiguous", False, 1305, "section-inherited")
    # S-B (4): 같은 줄 표지는 그대로 already-new
    g = go("sb4.md", ["* SR 1205 (줄 번호는 `%s`)" % n], "sb4")
    want("sb4.md", g, (1, 1205), "already-new", False)

    # m1: 범위 사이에 바뀐 덩어리(40행 뒤 삽입)를 품은 범위 -> ambiguous(span-hunk). 품지 않는 범위는 옮긴다
    g = go("m1.md", ["SR 30~50", "SR 1195~1210"], "m1")
    want("m1.md", g, (1, 30), "ambiguous", False, None, "span-hunk")
    want("m1.md", g, (1, 50), "ambiguous", False, 55, "span-hunk")
    want("m1.md", g, (2, 1195), "medium", True, 1200)
    want("m1.md", g, (2, 1210), "medium", True, 1215)
    # m1: 같은 크기 교체(1000행) + 처음 3줄 삽입 -- 995~1005는 끝점만 옮기면 틀린다
    def mod(t):
        ls = t.split("\n")
        ls[999] = "replaced_1000 = 0"
        return "\n".join(["top_%d = 0" % j for j in range(3)] + ls)
    r7, o7, n7 = make_repo("r7", sr_mod=mod)
    write(SB + "/drafts_m1b/x.md", "SR 995~1005\nSR 1001~1005\n")
    rs = {(r["line"], r["old"]): r for r in run(r7, o7, n7, SB + "/drafts_m1b", ["x.md"], SB + "/out_m1b")}
    want("m1b x.md", rs, (1, 995), "ambiguous", False, 998, "span-hunk")
    want("m1b x.md", rs, (1, 1005), "ambiguous", False, 1008, "span-hunk")
    want("m1b x.md", rs, (2, 1001), "medium", True, 1004)

    # m2: 두 자리(묶였으면 보고, 글 근거 없으면 패치 밖) / 리터럴 두 자리(글 대조 high) / 문장 끝 마침표 / 소수·확장자 아님
    g = go("m2.md", ["SR 42", "exp = {42: b'sr_line_42 = 42'}", "내용은 SR 1300.", "SR 1300.5 와 SR 1300.py", "SR 12개, SR 18, SD 2"],
           "m2")
    want("m2.md", g, (1, 42), "ambiguous", False, 47, "two-digit")
    want("m2.md", g, (2, 42), "high", True, 47)
    want("m2.md", g, (3, 1300), "medium", True, 1305)
    check("r2 m2.md L4 소수·확장자 아님", not any(k[0] == 4 and k[1] == 1300 for k in g), str(sorted(k for k in g if k[0] == 4)))
    check("r2 m2.md L5 두 자리+단위·개수 패치 0", not any(k[0] == 5 and g[k].get("patched") for k in g) and (5, 12) not in g,
          str({k: g[k]["confidence"] for k in g if k[0] == 5}))

    # m3: 줄에 이미 옮긴 것으로 의심되는 인용(조각이 new 1205 줄)이 있으면 같은 줄의 다른 인용도 패치하지 않는다
    g = go("m3.md", ["sizing_recipe.py 1205~1207, 1300행(`sr_line_1200 = 1200`)"], "m3")
    want("m3.md", g, (1, 1300), "ambiguous", False, 1305, "line-suspect")
    want("m3.md", g, (1, 1205), "ambiguous", False)

    # m5: 표지가 연달아 오면(`SR·SD 1300`) 엔진을 모른다 -> ambiguous(multi-engine). 따로 묶인 인용은 그대로
    g = go("m5.md", ["SR·SD 1300", "SR 1300, SD 1300"], "m5")
    want("m5.md", g, (1, 1300), "ambiguous", False, None, "multi-engine")
    with open(SB + "/out_r2_m5/kit_line_shift.json", encoding="utf-8") as fh:
        l2 = [r for r in json.load(fh)["records"] if r["line"] == 2]
    check("r2 m5.md L2 각 엔진 패치", sorted((r["engine"], r["new"]) for r in l2 if r.get("patched")) == [("SD", 1305), ("SR", 1305)],
          str([(r["engine"], r["new"], r.get("patched")) for r in l2]))

    # m6: 옛 b1 번호를 일부러 남긴 대입(SITE_SD_B1_MOCK)이 위 줄 new 표지 아래에 있어도 already-new라 하지 않는다
    g = go("m6.py", ["# 사이트 줄(줄 번호는 gate master `%s`)" % n, "SITE_SD_B1 = [1014, 1576]",
                     "SITE_SD_B1_MOCK = [1014, 1571]  # 옛 b1"], "m6", bases=["b1=SD:" + b1f], draft="m6.py@b1")
    want("m6.py", g, (3, 1571), "ambiguous", False, 1576, "section-inherited")
    want("m6.py", g, (2, 1576), "ambiguous", False)


if __name__ == "__main__":
    sys.exit(main())
