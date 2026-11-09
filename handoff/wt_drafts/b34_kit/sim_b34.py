"""B34 착수 문서 시퀀스 모의 -- 격리 복제본 + 가짜 bare gate(pre-receive = old 판 merge_gate receive). 저장소 쓰기 없음.

  C:/Python314/python.exe -B sim_b34.py [REV]     (기본 REV = 0f23786, scratch = C:/g123 -- 다른 C:/g* 안 건드림)

변형 두 가지(Q-B34-PHASE 답에 따라 갈리는 부분만 다르다):
  P2 = spec card 초안 그대로(phase: 2, approval 1줄)
  P3 = phase: 3 + approval 2줄(20260930-b26-before-phase3 + 모의 decision 기록 id 20261001-sim-b34-phase -- 내용은 자리표시자,
       실제 기록 문안·id는 사용자 답 뒤 오케스트레이터가 정한다)
단계(변형마다 새 복제본·새 gate):
  0 착수 전 확인(커밋 계획 §4.0)  1 (P3만) 모의 decision 승인 기록 커밋  2 spec card + interface card(절대 경로 호출) 커밋
  3 references 문서 패치(patch_b34_refs.py --check -> 적용 -> 재실행 멱등) 커밋 + test_phase2_stale_refs 실행
  4 가짜 gate에 push(단독) -> accept-log 줄 확인  5 대조: 트레일러 없는 커밋 push -> 거부
  6 phase 판정 지점 비교(merge_gate.rule10_phase·v1_command_check·strict_set, 병합된 phase 2 판정 기록 하나를 재료로)
결과: <KIT>/out/sim_b34.txt (줄마다 append)
"""
import json, os, shutil, subprocess, sys

REPO = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
DR = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts"
KIT = DR + "/b34_kit"
G = "C:/g123"
PY = "C:/Python314/python.exe"
REV = sys.argv[1] if len(sys.argv) > 1 else "0f23786"
OUT = KIT + "/out/sim_b34.txt"
ID = "20260930-b34-grammar-explicit"
SIMAPP = "20261001-sim-b34-phase"
FAIL = []
ENV = dict(os.environ, TMP=G + "/tmp", TEMP=G + "/tmp", PYTHONDONTWRITEBYTECODE="1")

RUNNER = r'''import os, shutil, subprocess, sys, tempfile, datetime
ZERO = "0" * 40
gate = os.path.abspath(os.environ.get("GIT_DIR") or ".")
def git(a):
    return subprocess.run(["git", "--git-dir", gate] + a, capture_output=True, check=True).stdout
lines = [l.split() for l in sys.stdin.read().splitlines() if l.strip()]
for old, new, ref in lines:
    if ref != "refs/heads/master" or new == ZERO or old == ZERO:
        print("[fake gate 거부] ref/생성/삭제", file=sys.stderr); sys.exit(1)
    if subprocess.run(["git", "--git-dir", gate, "merge-base", "--is-ancestor", old, new]).returncode:
        print("[fake gate 거부] non-ff", file=sys.stderr); sys.exit(1)
    tmp = tempfile.mkdtemp(prefix="fakegate-", dir="C:/g123/tmp")
    try:
        for ent in git(["ls-tree", "-r", "-z", "--full-tree", old, "--", "tools/gates/"]).decode("utf-8").split("\0"):
            if not ent:
                continue
            meta, path = ent.split("\t", 1)
            if meta.split()[1] != "blob" or path.startswith("tools/gates/redteam/"):
                continue
            p = os.path.join(tmp, *path[len("tools/gates/"):].split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(git(["cat-file", "blob", meta.split()[2]]))
        # 무결성 대조(integrity.py --scope gate)는 모의하지 않는다(설치된 hook·workspace 대조라 격리 복제본에 없음)
        mg = subprocess.run([sys.executable, os.path.join(tmp, "merge_gate.py"), "receive", "--old", old, "--new", new,
                             "--git-dir", gate], capture_output=True, cwd=tmp)
        sys.stderr.write(mg.stderr.decode("utf-8", "replace"))
        if mg.returncode:
            print("[fake gate 거부] merge_gate receive exit %d" % mg.returncode, file=sys.stderr); sys.exit(1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    open(os.path.join(gate, "gmid-accept-log"), "a").write("%s %s %s\n" % (old, new, datetime.datetime.now().isoformat()))
'''


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def check(cond, msg):
    log(("  OK  " if cond else "  NG  ") + msg)
    if not cond:
        FAIL.append(msg)


def run(args, ok=(0,), cwd=None):
    r = subprocess.run(args, capture_output=True, env=ENV, cwd=cwd)
    out = (r.stdout + r.stderr).decode("utf-8", "replace").strip()
    if r.returncode not in ok:
        raise SystemExit("명령 실패(exit %d): %s\n%s" % (r.returncode, args, out))
    return r.returncode, out


def variant(tag):
    seq, gate = "%s/seq_%s" % (G, tag), "%s/gate_%s.git" % (G, tag)
    for p in (seq, gate):
        assert not os.path.exists(p), p

    def git(*a, ok=(0,)):
        return run(["git", "-C", seq] + list(a), ok)[1]

    def commit(paths, msg, trailers=("Role: doc", "Change-Id: " + ID)):
        git("add", "--", *paths)
        args = ["commit", "--quiet", "-m", msg]
        for t in trailers:
            args += ["--trailer", t]
        git(*args)
        return git("rev-parse", "HEAD")

    def pyc(code):
        return run([PY, "-B", "-P", "-c", "import sys;sys.path.insert(0,%r);" % (seq + "/tools/gates") + code])[1]

    log("==== 변형 %s" % tag)
    run(["git", "clone", "-c", "core.autocrlf=false", "--quiet", "--no-hardlinks", "--no-local", "-c", "core.longpaths=true", REPO, seq])
    git("remote", "remove", "origin")
    git("config", "core.hooksPath", G + "/nohooks")
    git("config", "user.name", "sim"); git("config", "user.email", "sim@example.invalid")
    git("checkout", "--quiet", "-B", "master", REV)
    P0 = git("rev-parse", "HEAD")
    # 가짜 gate: 기준 커밋 push(훅 없음) 뒤 pre-receive 설치
    run(["git", "init", "--quiet", "--bare", gate])
    for f in os.listdir(gate + "/hooks"):
        os.remove(os.path.join(gate, "hooks", f))
    git("remote", "add", "gate", gate)
    git("push", "--quiet", "gate", "master:master")
    with open(G + "/fake_runner.py", "w", encoding="utf-8") as fh:
        fh.write(RUNNER)
    with open(gate + "/hooks/pre-receive", "w", encoding="utf-8", newline="\n") as fh:
        fh.write('#!/bin/sh\nexec "%s" -B "%s/fake_runner.py"\n' % (PY, G))
    log("  P0 %s, gate %s" % (P0[:10], gate))
    # 0 착수 전 확인(§4.0)
    check(git("branch", "--list", "role/*") == "", "role/* 브랜치 0(복제본)")
    check(git("status", "--porcelain", "--", "docs/02-design/specs/", ".ai/approvals/") == "", "specs·approvals 깨끗")
    check(os.path.exists(seq + "/.ai/approvals/20260930-b26-before-phase3.md"), "승인 기록 20260930-b26-before-phase3 있음")
    nt = git("show", "HEAD:tools/gates/mutate_changed.py").count("not_targeted")
    log("  참고: gate 판 mutate_changed.py의 not_targeted 개수 = %d (0 = 범위 card 미병합 -- 착수 조건 미충족 상태의 REV)" % nt)
    check(not os.path.exists(seq + "/docs/02-design/specs/%s.spec.md" % ID), "spec card 아직 없음")
    st = git("diff", "--stat", "2d58fd8", "HEAD", "--", "skills/analog-gmid-design/assets/stick_diagram.py",
             "skills/analog-gmid-design/assets/sizing_recipe.py", "install.py",
             "skills/analog-gmid-design/references/analog-grammar-integration.md")
    check(st == "", "2d58fd8..HEAD SD·SR·install.py·references 차이 0(card 줄 번호 유효)")
    # 1 (P3) 모의 decision 기록
    approvals = ["20260930-b26-before-phase3"]
    if tag == "P3":
        ap = seq + "/.ai/approvals/%s.md" % SIMAPP
        with open(ap, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("---\nid: %s\ndate: 2026-10-01\ntarget_kind: decision\ntarget: SIM-B34-PHASE\n"
                     "scope: 모의 자리표시자 -- B34 card phase 3(Phase 2 DoD 뒤, Phase 3 M card 전) 정정 기록의 형식 확인용\n---\n\n"
                     "## 사용자 원문\n\n> (모의 -- 실제 답 아님)\n" % SIMAPP)
        hdr = pyc("import merge_gate as mg,json;print(json.dumps(mg.parse_approval_header(open(%r,'rb').read(),%r),ensure_ascii=False,default=list))"
                  % (ap, SIMAPP + ".md"))
        log("  parse_approval_header(모의):", hdr[:200])
        commit([".ai/approvals/%s.md" % SIMAPP], "docs: 승인 기록 %s(모의)" % SIMAPP, trailers=("Role: doc",))
        approvals.append(SIMAPP)
    # 2 spec card + interface card
    spec, iface = "docs/02-design/specs/%s.spec.md" % ID, "docs/02-design/specs/%s.interface.md" % ID
    t = open(DR + "/draft_b34.final.spec.md", encoding="utf-8").read()
    if tag == "P3":
        t = t.replace("phase: 2\n", "phase: 3\n", 1).replace("approval: 20260930-b26-before-phase3\n",
                                                               "approval: 20260930-b26-before-phase3\napproval: %s\n" % SIMAPP, 1)
    with open(seq + "/" + spec, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(t)
    sc = json.loads(pyc("import role_paths as rp,json;c=rp.parse_spec_card(open(%r,encoding='utf-8').read(),%r);"
                        "print(json.dumps({k:c[k] for k in ('phase','evidence_type','gate_change','approval','activated_ic_case')}|{'n_sections':len(c['sections'])}))"
                        % (seq + "/" + spec, ID)))
    log("  parse_spec_card:", sc)
    check(sc["phase"] == ("3" if tag == "P3" else "2") and sc["evidence_type"] == "red-green" and sc["gate_change"] == "no"
          and sc["approval"] == approvals and sc["n_sections"] == 12 and sc["activated_ic_case"] == [], "spec card 머리·절 12개")
    rc, o = run([PY, "-B", seq + "/tools/gates/interface_card.py", seq + "/" + spec, "--root", seq, "--out", seq + "/" + iface])
    log("  interface_card.py:", o.replace("\n", " ")[:200])
    rows = [l for l in open(seq + "/" + iface, encoding="utf-8").read().split("\n") if l.startswith("| `")]
    sd_rows = [l for l in rows if l.startswith("| `stick_diagram` |")]
    names = sorted(l.split("|")[2].strip().strip("`") for l in sd_rows)
    log("  interface 표 행 %d, stick_diagram %d: %s" % (len(rows), len(sd_rows), names))
    want = sorted(["load_topology", "run_topology_pipeline", "find_stack_edges", "find_idiom_matches", "find_differential_and_mirror_forks",
                   "suggest_vertical_stack_composites", "find_differential_pair_candidates", "find_verified_differential_and_mirror_relations",
                   "refine_differential_and_mirror_relations", "audit_theta_root_direction", "propose_theta_kcl_gap_fill",
                   "propose_device_roles_gap_fill", "geometry_colocation_union", "propose_vertical_stack_id_gap_fill"])
    check(len(rows) == 14 and names == want, "interface 기존 함수 14개 전부 stick_diagram, 계약 1 진입점과 같음")
    B = commit([spec, iface], "docs: B34 spec card %s + interface card(모의)" % ID)
    # 3 references 문서 패치
    rc, o = run([PY, "-B", KIT + "/patch_b34_refs.py", "--root", seq, "--check"])
    check(o == "pending 5", "patch_b34_refs --check: %s" % o)
    check(git("status", "--porcelain") == "", "--check 무쓰기")
    run([PY, "-B", KIT + "/patch_b34_refs.py", "--root", seq])
    num = git("diff", "--numstat")
    log("  numstat:", num.replace("\t", " "))
    dlines = [l for l in git("diff", "-U0").split("\n") if l.startswith(("-", "+")) and not l.startswith(("---", "+++"))]
    check(not any("if not devs" in l for l in dlines), "gate 소자 없음 줄(if not devs) 미변경")
    A = commit(["skills/analog-gmid-design/references/analog-grammar-integration.md"],
               "docs: B34 references 폴백 서술 정정(모의)")
    rc, o = run([PY, "-B", KIT + "/patch_b34_refs.py", "--root", seq])
    check(o == "already-applied", "패치 재실행 멱등: %s" % o)
    blob = run(["git", "-C", seq, "cat-file", "-p", "HEAD:skills/analog-gmid-design/references/analog-grammar-integration.md"])[1]
    check("\r" not in blob and not blob.startswith("﻿"), "references blob LF·BOM 없음")
    rc, o = run([PY, "-B", "-P", "-m", "pytest", "-c", seq + "/tools/gates/pytest_gate.ini", "--rootdir=" + seq, "--confcutdir=" + seq,
                 "-q", "-p", "no:cacheprovider", "--gmid-phase=" + sc["phase"], "--gmid-strict=",
                 seq + "/skills/analog-gmid-design/assets/tests/contracts/test_phase2_stale_refs.py"], ok=(0, 1, 2, 3, 4, 5), cwd=G)
    check(rc == 0, "test_phase2_stale_refs (--gmid-phase=%s) exit %d: %s" % (sc["phase"], rc, o.splitlines()[-1] if o else ""))
    # 4 push(단독)
    rc, o = run(["git", "-C", seq, "push", "gate", "master:master"], ok=(0, 1))
    check(rc == 0, "가짜 gate push exit %d %s" % (rc, o.replace("\n", " ")[-300:]))
    acc = open(gate + "/gmid-accept-log", encoding="utf-8").read().split("\n") if os.path.exists(gate + "/gmid-accept-log") else []
    check(any(l.startswith("%s %s" % (P0, A)) for l in acc), "accept-log 줄 <P0> <A>")
    gm = run(["git", "--git-dir", gate, "rev-parse", "master"])[1]
    check(gm == A, "gate master == A")
    # 5 대조: 트레일러 없는 커밋
    with open(seq + "/" + spec, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n")
    neg = commit([spec], "docs: 트레일러 없는 커밋(대조)", trailers=())
    rc, o = run(["git", "-C", seq, "push", "gate", "master:master"], ok=(0, 1))
    check(rc == 1 and "EL4 거부" in o, "대조 push 거부 exit %d: %s" % (rc, [l for l in o.split("\n") if "거부" in l][:2]))
    git("reset", "--quiet", "--hard", A)
    # 6 phase 판정 지점(재료: 병합된 phase 2 판정 기록 하나)
    rid = "20260930-dup-w-calc"
    res = pyc("import merge_gate as mg,json\n"
              "t=mg.read_plan_tables_text(open(%r,encoding='utf-8').read())\n"
              "o=json.load(open(%r,encoding='utf-8'))\n"
              "out={}\n"
              "for ph in ('2','3'):\n"
              "    try:\n"
              "        mg.rule10_phase(o,ph,t); out['rule10_'+ph]='pass'\n"
              "    except Exception as e: out['rule10_'+ph]=str(e)[:120]\n"
              "v1=[c for c in o['auditor_run']['commands'] if c.startswith('V1: ')][0][4:]\n"
              "old=o['base_commit']\n"
              "for ph in ('2','3'):\n"
              "    out['v1_'+ph]=[f for f in mg.v1_command_check(v1,python_path='C:/Python314/python.exe',old=old,strict_needed=set(),phase=ph) if 'phase' in f]\n"
              "card={'phase':'3','activated_ic_case':[],'activated_ic_case_rename':[]}\n"
              "out['strict_3']=sorted(mg.strict_set(mg.TreeView(['-C',%r],'HEAD'),card))\n"
              "card['phase']='2'\n"
              "out['strict_2']=sorted(mg.strict_set(mg.TreeView(['-C',%r],'HEAD'),card))\n"
              "out['N/A']={k:v['basis'][:12] for k,v in o['checks'].items() if v['verdict']=='N/A'}\n"
              "print(json.dumps(out,ensure_ascii=False))" % (seq + "/docs/01-plan/features/gain-budget-gmid-sizing.plan.md",
                                                            seq + "/.ai/verification/%s.json" % rid, seq, seq))
    log("  phase 판정 지점(%s 기록):" % rid, res)
    if tag == "P2":
        user_install(seq, git, pyc, gate)
    return P0, A


def user_install(seq, git, pyc, gate):
    """사용자 작업 모의: install.py SKILLS에 "analog-grammar" + staged_diff 승인 기록, `Role: user` 한 커밋(선례 d72475a). 모의 id·사용자 원문은 자리표시자."""
    log("  -- 사용자 작업 모의(install.py)")
    p = seq + "/install.py"
    raw = open(p, "rb").read()
    old = b'"solution-capture", "analog-gmid-design"]'
    check(raw.count(old) == 1, "install.py SKILLS 끝 앵커 1회")
    new = raw.replace(old, b'"solution-capture", "analog-gmid-design", "analog-grammar"]')
    # 대조 먼저: 승인 기록 없이 같은 변경 -> 거부(gate master 그대로)
    open(p, "wb").write(new)
    git("add", "--", "install.py")
    git("commit", "--quiet", "-m", "chore: 승인 기록 없는 install.py(대조)", "--trailer", "Role: user")
    rc2, o2 = run(["git", "-C", seq, "push", "gate", "master:master"], ok=(0, 1))
    check(rc2 == 1 and "staged_diff" in o2, "대조(승인 기록 없음) push 거부 exit %d: %s" % (rc2, [l for l in o2.split("\n") if "거부" in l][:1]))
    git("reset", "--quiet", "--hard", "HEAD~1")
    open(p, "wb").write(new)
    git("add", "--", "install.py")
    tree = git("write-tree")
    base = git("rev-parse", "HEAD")
    h = pyc("import merge_gate as mg;print(mg.compute_diff_hash(mg.TreeView(['-C',%r],%r),mg.TreeView(['-C',%r],%r),['install.py']))"
            % (seq, base, seq, tree))
    aid = "20261001-sim-install-grammar"
    ap = ".ai/approvals/%s.md" % aid
    with open(seq + "/" + ap, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("---\nid: %s\ndate: 2026-10-01\ntarget_kind: staged_diff\ntarget: %s\ndiff_base: %s\ndiff_path: install.py\n"
                 "scope: 모의 -- install.py SKILLS에 analog-grammar 추가(B34 뒤 설치본 ImportError 방지)\n---\n\n## 사용자 원문\n\n> (모의)\n" % (aid, h, base))
    git("add", "--", ap)
    git("commit", "--quiet", "-m", "chore: install.py SKILLS에 analog-grammar(모의)", "--trailer", "Role: user")
    U = git("rev-parse", "HEAD")
    rc, o = run(["git", "-C", seq, "push", "gate", "master:master"], ok=(0, 1))
    check(rc == 0, "Role: user install.py 커밋 가짜 gate push exit %d %s" % (rc, [l for l in o.split("\n") if "거부" in l][:2]))
    gm = run(["git", "--git-dir", gate, "rev-parse", "master"])[1]
    check(gm == U, "gate master == 사용자 커밋")


if __name__ == "__main__":
    os.makedirs(G + "/tmp", exist_ok=True)
    os.makedirs(G + "/nohooks", exist_ok=True)
    os.makedirs(KIT + "/out", exist_ok=True)
    open(OUT, "w").close()
    log("REV", REV)
    for tag in ("P2", "P3"):
        variant(tag)
    log("== 결과: NG %d %s" % (len(FAIL), FAIL))
    sys.exit(1 if FAIL else 0)
