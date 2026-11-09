"""V3 범위 card 문서 커밋 시퀀스 모의(격리 복제본 C:/g109/seq, origin 없음, 빈 hooksPath -- 저장소 쓰기 없음).

순서(v3_cards_commit_plan.md §4.1·§4.2 + 키트 개정):
  0. 범위 card 패치를 묶기 card 전에 --check -> 거부(exit 2, 선행 문구 없음) 확인
  1. 묶기 card A(문서)·B(spec+interface)·C(승인) -- 범위 card의 전제 상태(묶기 card 코드 병합은 모의하지 않는다: 범위 card 문서 패치의 앵커와
     승인·게이트 판정에 닿지 않는다 -- 키트 §0.4)
  2. 범위 card A(patch_v3_scope_docs --check -> 적용 -> 커밋), B(spec 사본 + interface_card.py 절대 경로 호출), C(fill_v3_approval)
  3. 확인: gate_change_ok(HEAD) True / (HEAD~1) False, weakening_diff.diff_hash == compute_diff_hash == 기록 target, approved_hashes(HEAD) 포함,
     parse_spec_card, parse_approval_header, _approved_ids 수 불변, plan_tables_hash 불변, card 계약 10 인용문 ⊂ 패치된 줄
  4. EL4: merge_gate.py receive --git-dir seq/.git (old=P0,new=묶기 C), (old=묶기 C,new=범위 C) exit 0. 대조: 트레일러 없는 커밋 -> exit 1
결과: <KIT>/out/sim_sequence.txt
"""
import hashlib, json, os, re, shutil, subprocess, sys

REPO = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
DR = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts"
KIT = DR + "/v3scope_kit"
G = "C:/g109"
SEQ = G + "/seq"
PY = "C:/Python314/python.exe"
REV = sys.argv[1] if len(sys.argv) > 1 else "0f23786"
OUT = KIT + "/out/sim_sequence.txt"
BID, SID = "20260930-v3-exempt-binding", "20260930-v3-changed-stmt-scope"
PLAN = "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
D05 = "docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md"
D10 = "docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md"
FAIL = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def check(cond, msg):
    log(("  OK  " if cond else "  NG  ") + msg)
    if not cond:
        FAIL.append(msg)


def run(args, ok=(0,)):
    r = subprocess.run(args, capture_output=True)
    out = (r.stdout + r.stderr).decode("utf-8", "replace").strip()
    if r.returncode not in ok:
        raise SystemExit("명령 실패(exit %d): %s\n%s" % (r.returncode, args, out))
    return r.returncode, out


def git(*a, ok=(0,)):
    return run(["git", "-C", SEQ] + list(a), ok)[1]


def commit(paths, msg, trailer=True):
    git("add", "--", *paths)
    args = ["commit", "--quiet", "-m", msg] + (["--trailer", "Role: doc"] if trailer else [])
    git(*args)
    return git("rev-parse", "HEAD")


def pyc(code):
    return run([PY, "-B", "-P", "-c", "import sys;sys.path.insert(0,%r);" % (SEQ + "/tools/gates") + code])[1]


def card_flow(cid, patch, spec_src, approval_draft):
    base = git("rev-parse", "HEAD")
    rc, o = run([PY, "-B", patch, "--root", SEQ, "--check"])
    log("  %s --check:" % os.path.basename(patch), o.replace("\n", " ")[:400])
    run([PY, "-B", patch, "--root", SEQ])
    num = git("diff", "--numstat")
    log("  numstat:", num.replace("\n", " | "))
    changed = [l.split("\t")[2] for l in num.splitlines()]
    check(all(l.split("\t")[:2] == ["1", "1"] for l in num.splitlines()), "%s 문서 패치: 파일마다 1줄 바꿈" % cid)
    a = commit(changed, "docs: %s 문서 커밋(모의)" % cid)
    rc, o = run([PY, "-B", patch, "--root", SEQ])
    check("already" in o or "applied" in o, "%s 패치 재실행 멱등: %s" % (cid, o.replace("\n", " ")[:120]))
    spec = "docs/02-design/specs/%s.spec.md" % cid
    iface = "docs/02-design/specs/%s.interface.md" % cid
    shutil.copyfile(spec_src, os.path.join(SEQ, *spec.split("/")))
    run([PY, "-B", SEQ + "/tools/gates/interface_card.py", SEQ + "/" + spec, "--root", SEQ, "--out", SEQ + "/" + iface])
    log("  interface card %d줄" % open(SEQ + "/" + iface, encoding="utf-8").read().count("\n"))
    b = commit([spec, iface], "docs: 게이트 변경 spec card %s + interface card(모의)" % cid)
    rc, o = run([PY, "-B", DR + "/fill_v3_approval.py", "--root", SEQ, "--draft", approval_draft, "--base", base, "--head", b])
    log("  fill_v3_approval:", o.replace("\n", " ")[:300])
    c = commit([".ai/approvals/%s.md" % cid], "docs: 승인 기록 %s(모의)" % cid)
    # 확인
    ok_h = pyc("import merge_gate as mg;print(mg.gate_change_ok(mg.TreeView(['-C',%r],'HEAD'),%r))" % (SEQ, cid))
    ok_p = pyc("import merge_gate as mg;print(mg.gate_change_ok(mg.TreeView(['-C',%r],'HEAD~1'),%r))" % (SEQ, cid))
    check(ok_h == "True" and ok_p == "False", "%s gate_change_ok HEAD=%s, HEAD~1=%s" % (cid, ok_h, ok_p))
    rec = json.loads(pyc("import merge_gate as mg,json;print(json.dumps(mg.parse_approval_header(open(%r,'rb').read(),%r),ensure_ascii=False,default=list))"
                         % (SEQ + "/.ai/approvals/%s.md" % cid, cid + ".md")))
    paths = rec.get("diff_path") or rec.get("diff_paths")
    h1 = pyc("import weakening_diff as wd;print(wd.diff_hash(%r,%r,%r,%r))" % (SEQ, base, b, paths))
    h2 = pyc("import merge_gate as mg;print(mg.compute_diff_hash(mg.TreeView(['-C',%r],%r),mg.TreeView(['-C',%r],%r),%r))" % (SEQ, base, SEQ, b, paths))
    check(h1 == h2 == rec["target"], "%s target == diff_hash == compute_diff_hash (%s…)" % (cid, rec["target"][:16]))
    ah = pyc("import weakening_diff as wd;print(%r in wd.approved_hashes(%r,'HEAD'))" % (rec["target"], SEQ))
    check(ah == "True", "%s approved_hashes(HEAD)에 target" % cid)
    sc = pyc("import role_paths as rp,json;c=rp.parse_spec_card(open(%r,encoding='utf-8').read(),%r);print(json.dumps({k:c[k] for k in ('phase','evidence_type','gate_change','approval')},default=list))"
             % (SEQ + "/" + spec, cid))
    log("  parse_spec_card:", sc)
    blob = git("cat-file", "-p", "HEAD:.ai/approvals/%s.md" % cid)
    check("<!--" not in blob and "\r" not in blob, "%s 승인 기록 blob: HTML 주석 없음, CR 없음" % cid)
    log("  diff_path %d개: %s" % (len(paths), paths))
    return base, a, b, c


def contract10_quotes(spec_path):
    t = open(spec_path, encoding="utf-8").read()
    m = re.search(r"\n10\. \*\*문서\*\*: (.*?)\n\n", t, re.S)
    para = m.group(1)
    ls = [l.strip() for l in para.split("\n")]
    joined = ls[0]
    for l in ls[1:]:
        joined += ("" if joined.endswith("·") or l.startswith("(") else " ") + l
    return re.findall(r'"(① 대상 =.*?\(판정 제외\))"', joined) + re.findall(r'"(대상 = diff가 닿은 def 중 AST 해시가 바뀐 것의.*?\(대상 밖 변이는 실행하지 않고 id를 출력\))"', joined)


if __name__ == "__main__":
    os.makedirs(KIT + "/out", exist_ok=True)
    open(OUT, "w").close()
    assert not os.path.exists(SEQ)
    run(["git", "clone", "-c", "core.autocrlf=false", "--quiet", "--no-hardlinks", "--no-local", "-c", "core.longpaths=true", REPO, SEQ])
    git("remote", "remove", "origin")
    git("config", "core.hooksPath", G + "/emptyhooks")
    git("config", "user.name", "sim")
    git("config", "user.email", "sim@example.invalid")
    git("checkout", "--quiet", "-B", "master", REV)
    P0 = git("rev-parse", "HEAD")
    log("== seq base", P0, "autocrlf=%s" % run(["git", "-C", SEQ, "config", "core.autocrlf"], ok=(0, 1))[1])
    ptab0 = pyc("import merge_gate as mg;print(mg.plan_tables_hash(open(%r,'rb').read().decode('utf-8')))" % (SEQ + "/" + PLAN))
    ids0 = pyc("import reachability as r;print(len(r._approved_ids(%r,'HEAD')))" % SEQ)
    log("  plan_tables_hash", ptab0, "| _approved_ids", ids0)
    # 0. 범위 패치를 먼저 -> 거부
    rc, o = run([PY, "-B", DR + "/patch_v3_scope_docs.py", "--root", SEQ, "--check"], ok=(0, 2))
    check(rc == 2 and git("status", "--porcelain") == "", "묶기 card 전 범위 패치 --check 거부(exit %d), 무쓰기" % rc)
    # 1. 묶기 card
    log("== 묶기 card", BID)
    bb, ba, bspec, bc = card_flow(BID, DR + "/patch_v3_binding_docs.py", DR + "/draft_v3_exempt_binding.spec.md",
                                  DR + "/approval_%s.md" % BID)
    # 2. 범위 card
    log("== 범위 card", SID)
    sb, sa, sspec, sc_ = card_flow(SID, DR + "/patch_v3_scope_docs.py", DR + "/draft_v3_scope_policy.spec.md",
                                   DR + "/approval_%s.md" % SID)
    ptab1 = pyc("import merge_gate as mg;print(mg.plan_tables_hash(open(%r,'rb').read().decode('utf-8')))" % (SEQ + "/" + PLAN))
    check(ptab1 == ptab0, "plan_tables_hash 불변(%s…)" % ptab1[:16])
    ids1 = pyc("import reachability as r;print(len(r._approved_ids(%r,'HEAD')))" % SEQ)
    check(ids1 == ids0, "_approved_ids 수 불변(%s)" % ids1)
    line05 = [l for l in open(SEQ + "/" + D05, encoding="utf-8").read().split("\n") if "`mutate_changed.py`(V3)" in l][0]
    line_pl = [l for l in open(SEQ + "/" + PLAN, encoding="utf-8").read().split("\n") if l.startswith("| V3 | 뮤테이션 |")][0]
    qs = contract10_quotes(DR + "/draft_v3_scope_policy.spec.md")
    check(len(qs) == 2 and qs[0] in line05 and qs[1] in line_pl, "spec card 계약 10 인용문 2개(%s자·%s자)가 패치된 design 05·계획 V3 행 안에 그대로" % tuple(len(q) for q in qs) if len(qs) == 2 else "인용문 추출 %d개" % len(qs))
    check(line05.count("|") == open(REPO + "/" + D05, encoding="utf-8").read().split("\n")[316].count("|"), "design 05 V3 행 `|` 개수 불변")
    for nm, p in (("plan", PLAN), ("05", D05), ("10", D10)):
        b = open(SEQ + "/" + p, "rb").read().replace(b"\r\n", b"\n")
        log("  LF 정규화 sha256 %s %s" % (nm, hashlib.sha256(b).hexdigest()[:16]))
    # 4. EL4
    gate = SEQ + "/tools/gates/merge_gate.py"
    for old, new, tag in ((P0, bc, "묶기 push"), (bc, sc_, "범위 push")):
        rc, o = run([PY, "-B", gate, "receive", "--git-dir", SEQ + "/.git", "--old", old, "--new", new], ok=(0, 1))
        check(rc == 0, "EL4 receive %s old=%s new=%s exit %d %s" % (tag, old[:7], new[:7], rc, o[:200]))
    negs = []
    for np_ in ("docs/02-design/specs/%s.spec.md" % SID, "tools/gates/mutate_changed.py"):
        git("checkout", "--quiet", "--detach", sc_)
        with open(SEQ + "/" + np_, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n")
        negs.append((np_, commit([np_], "docs: 트레일러 없는 커밋(대조)", trailer=False)))
    for np_, neg in negs[:-1]:
        rc, o = run([PY, "-B", gate, "receive", "--git-dir", SEQ + "/.git", "--old", sc_, "--new", neg], ok=(0, 1))
        log("  참고: 트레일러 없는 커밋(%s) receive exit %d %s" % (np_, rc, o.replace("\n", " ")[:200]))
    np_, neg = negs[-1]
    rc, o = run([PY, "-B", gate, "receive", "--git-dir", SEQ + "/.git", "--old", sc_, "--new", neg], ok=(0, 1))
    check(rc == 1, "EL4 대조(트레일러 없음) exit %d: %s" % (rc, o.replace("\n", " ")[:200]))
    log("== 커밋: 묶기 A %s B %s C %s | 범위 A %s B %s C %s" % (ba[:7], bspec[:7], bc[:7], sa[:7], sspec[:7], sc_[:7]))
    log("== 결과: NG %d" % len(FAIL))
    sys.exit(1 if FAIL else 0)
