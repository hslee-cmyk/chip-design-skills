"""P10 `20260930-p10-df23-inventory` 문서 커밋 내용을 작업 트리에 적용한다 (오케스트레이터 준비 도구, 커밋하지 않음).

근거: `_drafts/draft_p10_b22.reviewed.spec.md` '순서'·'결정 필요 항목'·계약 5, `_drafts/draft_p10b.reviewed.spec.md` '결정 필요 항목'
둘째 점(design §8 P10b 행 문안), `p10_prep/b22_lines.md`(19줄 문안).

하는 일 (모두 작업 트리 파일만 바꾼다 -- git add/commit은 하지 않는다):
  1. 목록 재생성: `regen_df23.py --repo <R> --commit C --prev-measured-at 1e2e243` (소스는 C의 blob만 읽는다) ->
     `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json` (`measured_at` = C 확인)
  1b. 생성기를 같은 폴더에 `mk_df23_inventory.py`로 복사(바이트 동일, sha256 고정 -- spec '결정 필요 항목' 둘째 점)
  2. 참조 문서 19줄 표시(`b22_lines.md` 문안 그대로)
  3. `probe-df23-summary.md` §B 제목 아래 표지 한 줄
  4. design 20 §8 P10 행 정정 + P10b 행 추가, §11-1 정정

성질:
  * 결정론·멱등: 이미 적용된 편집은 '적용됨'으로 건너뛴다. 편집마다 옛 줄(전체 문자열)이 파일에 정확히 1번이고 새 줄이 0번이면 적용,
    옛 줄 0번·새 줄 1번이면 적용됨, 그 밖은 오류(exit 2). 기본으로 줄 번호도 C 실측값과 같아야 한다(`--allow-line-shift`로 완화).
  * 줄 끝·인코딩 보존: 바이트로 읽어 UTF-8(strict)로 풀고, 줄마다 원래 줄 끝(`\\r\\n`/`\\n`/없음)을 그대로 붙인다.
    새로 넣는 줄은 그 파일의 우세 줄 끝을 쓴다. BOM이 있으면 보존. 목록 JSON은 기존 작업 트리 파일의 줄 끝 방식으로 쓴다.
  * `--dry-run`: 쓰지 않고 unified diff(목록 JSON은 요약 + `--json-diff`일 때만 전체)와 통계를 출력.

사용:
  python -B apply_p10_doc_commit.py --repo <작업 트리> --commit <C> [--dry-run] [--json-diff] [--allow-line-shift]
         [--prep-dir <p10_prep>] [--allow-head-mismatch]
exit: 0 = 성공(적용 또는 이미 적용), 2 = 전제·대조 실패(아무것도 쓰지 않는다 -- 모든 편집을 메모리에서 먼저 계산한다).
"""
import argparse
import difflib
import hashlib
import json
import os
import subprocess
import sys
import tempfile

A = "skills/analog-gmid-design/assets"
INV_DIR = "docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup"
INV_PATH = INV_DIR + "/df23_inventory.json"
GEN_DST = INV_DIR + "/mk_df23_inventory.py"
SUMMARY = INV_DIR + "/probe-df23-summary.md"
DESIGN = "docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md"
REF = "skills/analog-gmid-design/references/"
SKILL = "skills/analog-gmid-design/SKILL.md"
PREV_MEASURED_AT = "1e2e243"
GEN_SHA256 = "b4a75e92551da35503e048ec1abc5f9195c282cd769fd4496ac932b34b284e27"  # p10_reconcile_log.md §7
ENGINE_PATHS = [A + "/*.py", "workspaces/run_harness.py", A + "/library"]

MOVED = "Phase 2에서 tests/tools/interleave_splits.py로 이동"
DELETED = "Phase 2에서 삭제"

# ---------------------------------------------------------------- 편집 표
# kind "sub": 줄 `old`(전체)에서 `a`(줄 안 1번)를 `b`로. kind "line": 줄 `old`를 `new`(전체)로.
# kind "insert_after": 줄 `old`(전체) 바로 다음에 `new` 줄이 없으면 넣는다. line = C(7535799/8790b24) 실측 줄 번호.
EDITS = [
    # ---- 2. 참조 문서 19줄 (b22_lines.md 1~19)
    dict(n=1, path=REF + "function-selection-map.md", line=35, kind="sub",
         old="| 단일 소자, 기생 커패시턴스까지 반복 수렴시켜 사이징 | `converge_with_parasitics(fT, C_external, gm_id, L, lut, ...)` | §1 스텝 3~5를 자동 반복 |",
         a="`converge_with_parasitics(fT, C_external, gm_id, L, lut, ...)` |",
         b="`converge_with_parasitics(fT, C_external, gm_id, L, lut, ...)` (" + DELETED + ") |"),
    dict(n=2, path=REF + "function-selection-map.md", line=38, kind="sub",
         old="| slew-rate 계산 | `slew_rate(ID, C)` | |",
         a="`slew_rate(ID, C)` |", b="`slew_rate(ID, C)` (" + DELETED + ") |"),
    dict(n=3, path=REF + "function-selection-map.md", line=80, kind="sub",
         old="| PDF 스타일 텍스트 렌더링(터미널 확인용, **리포트의 시각 자료 아님**) | `render_stick_diagram(result)` | ⚠️ 이 함수의 출력 문자열을 리포트 HTML에 그대로 붙여넣지 말 것 — 리포트 시각화는 항상 `assets/report_template.html`의 `renderStack()`(SVG) 재사용 |",
         a="`render_stick_diagram(result)` |", b="`render_stick_diagram(result)` (" + DELETED + ") |"),
    dict(n=4, path=REF + "function-selection-map.md", line=99, kind="sub",
         old="| 매칭쌍 개수가 홀수라 단독 좌우 분할이 안 될 때 | `find_interleaved_symmetric_splits(count_a, count_b)` | §2.5.4 |",
         a="`find_interleaved_symmetric_splits(count_a, count_b)` |",
         b="`find_interleaved_symmetric_splits(count_a, count_b)` (" + MOVED + ") |"),
    dict(n=5, path=REF + "sky130-worked-example.md", line=256, kind="sub",
         old="**부수적으로 발견한 버그**: 이 최적화기를 만들다가 `converge_with_parasitics()`의",
         a="`converge_with_parasitics()`의", b="`converge_with_parasitics()`(" + DELETED + ")의"),
    dict(n=6, path=REF + "sky130-worked-example.md", line=262, kind="sub",
         old="`converge_with_parasitics()`는 수정 완료(현재 커밋에 반영됨).",
         a="(현재 커밋에 반영됨).", b="(현재 커밋에 반영됨) -- 이 함수는 " + DELETED + "."),
    dict(n=7, path=REF + "stick-diagram-euler-layout.md", line=113, kind="sub",
         old="> `find_interleaved_symmetric_splits()`(§2.5.4, 개수가 안 맞는 매칭쌍도 다른 소자와 섞어",
         a="`find_interleaved_symmetric_splits()`(§2.5.4,", b="`find_interleaved_symmetric_splits()`(" + MOVED + ", §2.5.4,"),
    dict(n=8, path=REF + "stick-diagram-euler-layout.md", line=215, kind="sub",
         old="**구현**: `find_interleaved_symmetric_splits(count_a, count_b)`가 이 조건(count_a==count_b)을",
         a="`find_interleaved_symmetric_splits(count_a, count_b)`가",
         b="`find_interleaved_symmetric_splits(count_a, count_b)`(" + MOVED + ")가"),
    dict(n=9, path=REF + "stick-diagram-euler-layout.md", line=464, kind="sub",
         old="잡아 `find_interleaved_symmetric_splits(10,10)`의 최선 분할 `(5,5,5,5)`로 diffpair의",
         a="`find_interleaved_symmetric_splits(10,10)`의", b="`find_interleaved_symmetric_splits(10,10)`(" + MOVED + ")의"),
    dict(n=10, path=REF + "stick-diagram-euler-layout.md", line=1065, kind="line",
         old="    Transistor, build_stick_diagram, render_stick_diagram,",
         new="    Transistor, build_stick_diagram,  # render_stick_diagram: " + DELETED),
    dict(n=11, path=REF + "stick-diagram-euler-layout.md", line=1102, kind="line",
         old="    print(render_stick_diagram(result))",
         new="    # print(render_stick_diagram(result))  -- " + DELETED),
    dict(n=12, path=REF + "stick-diagram-euler-layout.md", line=1223, kind="sub",
         old="      구성했는가 — `build_mirror_symmetric_pattern()`/`find_interleaved_symmetric_splits()`",
         a="/`find_interleaved_symmetric_splits()`", b="/`find_interleaved_symmetric_splits()`(" + MOVED + ")"),
    dict(n=13, path=REF + "design-report-spec.md", line=92, kind="sub",
         old="19. **증상**: 18번의 재구성 중 `find_interleaved_symmetric_splits()`가 반환한 모든 후보로",
         a="`find_interleaved_symmetric_splits()`가", b="`find_interleaved_symmetric_splits()`(" + MOVED + ")가"),
    dict(n=14, path=REF + "design-report-spec.md", line=308, kind="sub",
         old="   `find_interleaved_symmetric_splits()`로 홀수 조합의 불균등 분할을 구하고), 각 소자를",
         a="`find_interleaved_symmetric_splits()`로", b="`find_interleaved_symmetric_splits()`(" + MOVED + ")로"),
    dict(n=15, path=REF + "consistency-map.md", line=207, kind="sub",
         old="     않음): `fT_dev = lut.fT(gm_id, L, VDS, vs); fnqs_ok = fT <= quasi_static_margin * fT_dev`로",
         a="* fT_dev`로", b="* fT_dev`(`lut.fT()`는 " + DELETED + ")로"),
    dict(n=16, path=REF + "consistency-map.md", line=209, kind="sub",
         old="     있었다 — element 함수를 호출하는 대신 그 안의 공식을 그대로 베껴 쓴 것. `lut.fT()`가",
         a="`lut.fT()`가", b="`lut.fT()`(" + DELETED + ")가"),
    dict(n=17, path=REF + "known-incidents.md", line=104, kind="sub",
         old="`telescopic_class_ab` CMRR 폐형식(`_cmrr_telescopic_class_ab`)의 self-test를 작성하며,",
         a="(`_cmrr_telescopic_class_ab`)의", b="(`_cmrr_telescopic_class_ab`, 둘 다 " + DELETED + ")의"),
    dict(n=18, path=REF + "known-incidents.md", line=125, kind="sub",
         old="구현 예시: `sizing_recipe.py`의 `telescopic_class_ab` self-test(2026-07-31, `_crt_by_name`",
         a="self-test(2026-07-31,", b="self-test(" + DELETED + ", 2026-07-31,"),
    dict(n=19, path=SKILL, line=74, kind="sub",
         old="| 6 | 순수 수식 함수의 self-test라는 이유로, 실제 `library/*.topology.json`에 존재하는 소자 이름을 그 회로에서의 kind/connectivity를 확인하지 않고 논문/기억만으로 역할 배정해서 씀(2026-07-31, `telescopic_class_ab` CMRR 계기) | 그 이름을 값에 채워 넣기 전에 `load_topology(그 실제 파일)`로 kind/connectivity(같은 노드 공유 등)를 먼저 assert — \"수식 검증\"과 \"역할 배정 검증\"을 별도 블록으로 분리 |",
         a="`telescopic_class_ab` CMRR 계기)", b="`telescopic_class_ab` CMRR 계기 -- " + DELETED + ")"),
    # ---- 3. probe-df23-summary.md §B 표지 한 줄 (spec '결정 필요 항목' 셋째 점 문안 그대로)
    dict(n=20, path=SUMMARY, line=157, kind="insert_after",
         old="## B. DF-23 전수 -- 엔진 소스의 소자·넷·회로 이름과 topology 경로 리터럴",
         new="이 절의 수는 1e2e243 측정 기록이다. 현재 목록은 `df23_inventory.json`(`measured_at`, 항목마다 `phase`)."),
    # ---- 4. design 20 §8 P10 행 정정 (spec '결정 필요 항목' 넷째 점)
    dict(n=21, path=DESIGN, line=194, kind="line",
         old="| P10 | `df23-inventory` | DF-23 전수 목록 문서화(`df23_inventory.json` 기준 266건)와 레지스트리 기록, 신규 148건의 담당 Phase 배정 | test-only(문서) | (d) 실측 원자료 | 목록 |",
         new="| P10 | `df23-inventory` | DF-23 전수 목록 문서화(card base 재측정(`measured_at`))와 항목마다 담당 Phase 배정, 참조 문서의 Phase 2 삭제·이동 이름 표시(문서 백로그 B22 (b)). 레지스트리 기록은 별도 card(code 경로 -- 아래 행) (2026-09-30 정정, spec card `20260930-p10-df23-inventory`) | test-only(문서) | (d) 실측 원자료 | 목록 |"),
    # ---- 4b. P10b 행 추가 (draft_p10b.reviewed.spec.md '결정 필요 항목' 둘째 점 문안 그대로)
    dict(n=22, path=DESIGN, line=194, kind="insert_after",
         old="| P10 | `df23-inventory` | DF-23 전수 목록 문서화(card base 재측정(`measured_at`))와 항목마다 담당 Phase 배정, 참조 문서의 Phase 2 삭제·이동 이름 표시(문서 백로그 B22 (b)). 레지스트리 기록은 별도 card(code 경로 -- 아래 행) (2026-09-30 정정, spec card `20260930-p10-df23-inventory`) | test-only(문서) | (d) 실측 원자료 | 목록 |",
         new="| P10b | `df23-registry-record` | 레지스트리 §8에 DF-23 목록 기록(목록 경로·`measured_at`·총계·함수별 행)과 `reg_check.py --df23-inventory` 대조 규칙 | red-green(레지스트리·도구 code 커밋) | (a) 도구 합성 입력, (d) card base 목록 | 레지스트리 기록 |"),
    # ---- 4c. design 20 §11-1 정정 (spec: "63건에 DF 번호가 없다" -> "DF-19·DF-26(`수정 Phase` 4)이 이미 덮는다 -- 목록에서 두 행에 묶는다")
    dict(n=23, path=DESIGN, line=230, kind="line",
         old="1. **레일 넷 이름 리터럴 63건에 DF 번호가 없다**(`vdd` 49·`gnd` 25·`vss` 4 중). `supply_nets`가 topology.json에 선언돼 있는데 코드가 이름을 직접 쓰고, 같은 레일 집합이 최소 세 곳에 따로 선언돼 있다(`sizing_recipe:3893-3894`, `sizing_recipe:8592`, `stick_diagram:3167`). `_metric_supply_current`는 `'vdd'`만 보는데 세 회로는 `vss`·`agnd`를 쓴다. → DF 신설 요청(담당 Phase 4, MG1 레일 이름 변경과 같은 자리).",
         new="1. **레일 넷 이름 리터럴은 DF-19·DF-26(`수정 Phase` 4)이 이미 덮는다 -- 목록에서 두 행에 묶는다**(2026-09-30 정정, spec card `20260930-p10-df23-inventory`. 처음 기록 \"레일 넷 이름 리터럴 63건에 DF 번호가 없다(`vdd` 49·`gnd` 25·`vss` 4 중) → DF 신설 요청\"은 틀렸다 -- DF-19·DF-26 두 행이 이미 레일 이름 집합 하드코딩을 적고 있다). `supply_nets`가 topology.json에 선언돼 있는데 코드가 이름을 직접 쓰고, 같은 레일 집합이 최소 세 곳에 따로 선언돼 있다(`sizing_recipe:3893-3894`, `sizing_recipe:8592`, `stick_diagram:3167`). `_metric_supply_current`는 `'vdd'`만 보는데 세 회로는 `vss`·`agnd`를 쓴다. → 새 DF 없이 DF-19·DF-26 교체(담당 Phase 4, MG1 레일 이름 변경과 같은 자리)에서 다룬다."),
]


class Fail(Exception):
    pass


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True)
    if p.returncode != 0:
        raise Fail("git %s 실패: %s" % (" ".join(args), p.stderr.decode("utf-8", "replace").strip()))
    return p.stdout.decode("utf-8")


# ---------------------------------------------------------------- 바이트 보존 텍스트
class TextFile:
    def __init__(self, raw):
        self.bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw[3:] if self.bom else raw
        try:
            text = body.decode("utf-8")  # strict
        except UnicodeDecodeError as ex:
            raise Fail("UTF-8이 아니다: %s" % ex)
        self.lines, self.eols = [], []
        for seg in text.splitlines(keepends=True):
            if seg.endswith("\r\n"):
                self.lines.append(seg[:-2]); self.eols.append("\r\n")
            elif seg.endswith("\n"):
                self.lines.append(seg[:-1]); self.eols.append("\n")
            elif seg.endswith("\r") or any(c in seg for c in "\x0b\x0c\x1c\x1d\x1e\x85  "):
                raise Fail("표준 밖 줄 끝 문자가 있다 -- 이 도구는 \\n/\\r\\n만 다룬다")
            else:
                self.lines.append(seg); self.eols.append("")
        n_crlf = self.eols.count("\r\n")
        n_lf = self.eols.count("\n")
        self.dominant = "\r\n" if n_crlf > n_lf else "\n"
        self.eol_desc = "CRLF" if n_crlf and not n_lf else ("LF" if n_lf and not n_crlf else "혼합(CRLF %d, LF %d)" % (n_crlf, n_lf))

    def to_bytes(self):
        out = "".join(l + e for l, e in zip(self.lines, self.eols))
        return (b"\xef\xbb\xbf" if self.bom else b"") + out.encode("utf-8")


def locate(tf, s):
    return [i for i, l in enumerate(tf.lines) if l == s]


def apply_edit(tf, e, allow_shift, offset=0):
    """적용하면 'applied', 이미 적용이면 'already'. 실패는 Fail. offset = 같은 파일 앞 편집이 넣은 줄 수(C 줄 번호 보정)."""
    tag = "편집 %d (%s:%d)" % (e["n"], e["path"], e["line"])
    want = e["line"] + offset
    old = e["old"]
    if e["kind"] == "sub":
        if old.count(e["a"]) != 1:
            raise Fail("%s: 표 오류 -- 앵커가 옛 줄에 %d번" % (tag, old.count(e["a"])))
        new = old.replace(e["a"], e["b"], 1)
    elif e["kind"] in ("line", "insert_after"):
        new = e["new"]
    else:
        raise Fail("%s: 모르는 kind" % tag)

    if e["kind"] == "insert_after":
        io_ = locate(tf, old)
        if len(io_) != 1:
            raise Fail("%s: 기준 줄이 %d번 있다(1번이어야 한다)" % (tag, len(io_)))
        i = io_[0]
        if i + 1 != want and not allow_shift:
            raise Fail("%s: 기준 줄이 %d행에 있다(기대 %d행, --allow-line-shift로 완화)" % (tag, i + 1, want))
        cnt_new = len(locate(tf, new))
        if cnt_new == 1 and i + 1 < len(tf.lines) and tf.lines[i + 1] == new:
            return "already", i + 2
        if cnt_new != 0:
            raise Fail("%s: 넣을 줄이 이미 다른 자리에 %d번 있다" % (tag, cnt_new))
        ins_eol = tf.eols[i] if tf.eols[i] else ""   # 파일 끝 줄 뒤에 넣으면 "끝 줄 바꿈 없음" 상태를 넣은 줄이 물려받는다
        if tf.eols[i] == "":
            tf.eols[i] = tf.dominant
        tf.lines.insert(i + 1, new)
        tf.eols.insert(i + 1, ins_eol)
        return "applied", i + 2

    io_, in_ = locate(tf, old), locate(tf, new)
    if len(io_) == 1 and len(in_) == 0:
        i = io_[0]
        if i + 1 != want and not allow_shift:
            raise Fail("%s: 옛 줄이 %d행에 있다(기대 %d행, --allow-line-shift로 완화)" % (tag, i + 1, want))
        tf.lines[i] = new
        return "applied", i + 1
    if len(io_) == 0 and len(in_) == 1:
        return "already", in_[0] + 1
    raise Fail("%s: 옛 줄 %d번·새 줄 %d번 -- (1,0) 또는 (0,1)이어야 한다" % (tag, len(io_), len(in_)))


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def main(argv=None):
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", required=True, help="작업 트리(문서 커밋을 만들 worktree)")
    ap.add_argument("--commit", required=True, help="C = card base가 될 gate master 머리(문서 커밋의 부모 = measured_at)")
    ap.add_argument("--prep-dir", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json-diff", action="store_true", help="dry-run에서 목록 JSON 전체 diff도 출력")
    ap.add_argument("--allow-line-shift", action="store_true")
    ap.add_argument("--allow-head-mismatch", action="store_true", help="HEAD != C 허용(시험용 -- 실제 문서 커밋에는 쓰지 말 것)")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)
    try:
        return run(a, repo)
    except Fail as ex:
        print("[apply_p10] 실패: %s" % ex)
        print("[apply_p10] 아무 파일도 쓰지 않았다(모든 편집을 메모리에서 먼저 계산하고 대조가 끝난 뒤에만 쓴다).")
        return 2


def run(a, repo):
    C = git(repo, "rev-parse", a.commit + "^{commit}").strip()
    head = git(repo, "rev-parse", "HEAD").strip()
    print("[apply_p10] repo=%s  C=%s  HEAD=%s  모드=%s" % (repo, C, head, "dry-run" if a.dry_run else "적용"))
    if head != C and not a.allow_head_mismatch:
        raise Fail("HEAD(%s) != C(%s): 문서 커밋의 부모가 measured_at(C)이어야 한다(계약 8)" % (head[:12], C[:12]))
    # 엔진·library 경로가 C와 같아야 한다(작업 트리 포함) -- 계약 7 (e)의 전제
    changed = git(repo, "diff", "--name-only", C, "--", *ENGINE_PATHS).split()
    if changed:
        raise Fail("작업 트리의 엔진·library 경로가 C와 다르다: %s" % changed)
    # 이 도구가 쓰는 경로 밖의 변경이 있으면 멈춘다(문서 커밋에 섞이지 않게)
    ours = {INV_PATH, GEN_DST, SUMMARY, DESIGN} | {e["path"] for e in EDITS}
    dirty = []
    for ln in git(repo, "status", "--porcelain", "--untracked-files=all").splitlines():
        p = ln[3:].strip().strip('"')
        if p not in ours:
            dirty.append(ln)
    if dirty:
        print("[apply_p10] 경고: 이 도구 밖의 변경/미추적 파일이 있다(문서 커밋에 넣지 말 것):")
        for d in dirty[:20]:
            print("    " + d)

    gen_src = os.path.join(a.prep_dir, "regen_df23.py")
    gen_bytes = open(gen_src, "rb").read()
    if sha256(gen_bytes) != GEN_SHA256:
        raise Fail("생성기 sha256 %s != 고정값 %s (reconcile 판이 아니다)" % (sha256(gen_bytes), GEN_SHA256))

    plan = {}  # path -> (old_bytes or None, new_bytes)
    report = []

    # ---- 1. 목록 재생성
    with tempfile.TemporaryDirectory(prefix="p10inv_") as td:
        out = os.path.join(td, "df23_inventory.json")
        p = subprocess.run([sys.executable, "-B", gen_src, "--repo", repo, "--commit", C,
                            "--prev-measured-at", PREV_MEASURED_AT, "--out", out], capture_output=True)
        if p.returncode != 0:
            raise Fail("생성기 실패(%d): %s" % (p.returncode, p.stderr.decode("utf-8", "replace")[-2000:]))
        gen_json = open(out, "rb").read()
    inv = json.loads(gen_json.decode("utf-8"))
    if inv.get("measured_at") != C:
        raise Fail("생성 목록 measured_at %s != C %s" % (inv.get("measured_at"), C))
    inv_abs = os.path.join(repo, INV_PATH)
    old_inv = open(inv_abs, "rb").read() if os.path.exists(inv_abs) else None
    new_inv = gen_json
    if old_inv is not None:
        eol = "\r\n" if old_inv.count(b"\r\n") and old_inv.count(b"\r\n") == old_inv.count(b"\n") else "\n"
        if eol == "\r\n":
            new_inv = gen_json.replace(b"\n", b"\r\n")
    plan[INV_PATH] = (old_inv, new_inv)
    t = inv["totals"]
    report.append("목록: measured_at=%s n_items=%d by_role=%s by_phase=%s sha256(LF)=%s" % (
        C, t["n_items"], json.dumps(t["by_role"], ensure_ascii=False), json.dumps(t["by_phase"], ensure_ascii=False),
        sha256(gen_json)))

    # ---- 1b. 생성기 복사
    gd = os.path.join(repo, GEN_DST)
    plan[GEN_DST] = (open(gd, "rb").read() if os.path.exists(gd) else None, gen_bytes)

    # ---- 2~4. 텍스트 편집
    files = {}
    for e in EDITS:
        if e["path"] not in files:
            raw = open(os.path.join(repo, e["path"]), "rb").read()
            files[e["path"]] = (raw, TextFile(raw))
    offset = {}
    for e in EDITS:
        status, at = apply_edit(files[e["path"]][1], e, a.allow_line_shift, offset.get(e["path"], 0))
        if e["kind"] == "insert_after":
            offset[e["path"]] = offset.get(e["path"], 0) + 1
        report.append("편집 %2d %-8s %s:%d" % (e["n"], status, e["path"], at))
    for path, (raw, tf) in files.items():
        nb = tf.to_bytes()
        # 되돌림 확인: 바뀐 줄 말고는 바이트 동일(줄 끝 포함)
        plan[path] = (raw, nb)
        report.append("파일 %s 줄 끝=%s BOM=%s" % (path, tf.eol_desc, tf.bom))

    # ---- 출력/쓰기
    n_changed = 0
    for path, (ob, nb) in plan.items():
        if ob == nb:
            continue
        n_changed += 1
        if a.dry_run:
            ot = (ob or b"").decode("utf-8").replace("\r\n", "\n").splitlines(keepends=True)
            nt = nb.decode("utf-8").replace("\r\n", "\n").splitlines(keepends=True)
            d = list(difflib.unified_diff(ot, nt, "a/" + path, "b/" + path, n=0))
            plus = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
            minus = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
            print("=== %s  (+%d -%d)" % (path, plus, minus))
            if path in (INV_PATH, GEN_DST) and not a.json_diff:
                print("    (전체 diff 생략 -- --json-diff)")
            else:
                sys.stdout.writelines(d)
    for r in report:
        print("[apply_p10] " + r)
    if a.dry_run:
        print("[apply_p10] dry-run: 바뀔 파일 %d개, 아무것도 쓰지 않았다." % n_changed)
        return 0
    for path, (ob, nb) in plan.items():
        if ob != nb:
            dst = os.path.join(repo, path)
            with open(dst, "wb") as fh:
                fh.write(nb)
    print("[apply_p10] 적용: 바뀐 파일 %d개 (0이면 이미 적용된 상태)." % n_changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
