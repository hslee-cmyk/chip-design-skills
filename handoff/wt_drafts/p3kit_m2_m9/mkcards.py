"""measure only: render draft spec cards M2..M9 from C:/g226/out/cards_data.json (all numbers = this scratch measurement).
Writes <drafts>/draft_p3_m<k>.spec.md. M1 draft is NOT touched."""
import json
import re
import sys

D = json.load(open("C:/g226/out/cards_data.json", encoding="utf-8"))
OUTDIR = sys.argv[1]
PLAN_LINES = {}
for i, l in enumerate(open("C:/g226/tmp/plan_4a286f0.md", encoding="utf-8").read().split("\n"), 1):
    m = re.match(r"\| (MOD\d+) \|", l)
    if m:
        PLAN_LINES[m.group(1)] = (i, l)
B0 = "1a18416"
CHAIN = "`4a286f0` → `9659236` FU 대역(DR 28행·ACF 38행 앞 `from __future__ import annotations`, `fu_standin.py`) → `9a24b34` T0 W-1 대역(unit selftest 3파일 24행의 비엔진 7이름을 출처 import로, `t0w1_standin.py` -- W-1 (가)의 T0 몫만) → `b6c35d5` G1 시제품(`g1_kit/install_proto.py`·`g1_core.py`, gate master 판 `mutate_changed.py`·`rt.py`에 그대로 설치) → `744d0fe` D-11 (가) 대역(N3.10 MOD1 '대표 대상'에 `_QUERY_CACHE_MAX` 토큰, `p3fq_kit/variant.py qtok` -- p3_followup §1.4 새 문안과 같은 바이트) → `1c19dd4` D0a 대역(`p3kit_m1/move_plan_sim.py`를 `tools/migrate/move_plan.py`로, **문장 키 = 바인딩 이름(D0a 계약 2 문언, `MP_STMT_KEY=names`)**) → `1a18416` D0b 재생성 대역(`regen_registry.py --write` one 354·nested 7·nounit 18, `보류(Phase 3)` → `보류(Phase 4)`) = **M1 base 대역**"
CARDS = [
    ("topology_authoring", 2, "topology-authoring", "gmid_lut", "M1"),
    ("circuit_state_graph", 3, "circuit-state-graph", "topology_authoring", "M2"),
    ("gmid_sizing_engine", 4, "gmid-sizing-engine", "circuit_state_graph", "M3"),
    ("circuit_metrics", 5, "circuit-metrics", "gmid_sizing_engine", "M4"),
    ("theta_search", 6, "theta-search", "circuit_metrics", "M5"),
    ("sizing_layout_convergence", 8, "sizing-layout-convergence", "theta_search", "M6"),
    ("instance_report_builder", 9, "instance-report-builder", "sizing_layout_convergence", "M8"),
]
AB = {"sizing_recipe.py": "SR", "stick_diagram.py": "SD", "topology_library.py": "TL", "design_report.py": "DR", "audit_current_forced.py": "ACF"}
ORDER_SRC = ["topology_library.py", "stick_diagram.py", "sizing_recipe.py", "design_report.py", "audit_current_forced.py"]
T0_FAIL = {  # T0 A-group tests that the scratch PT3 shows failing at this head (no T0 in the chain) -- filled from data
}


def bt(x):
    return "`%s`" % x


def fmt_findings(f):
    if not f:
        return "발견 0"
    return "·".join("`%s` %d" % (k, v) for k, v in f.items())


def neg_rows(c, d):
    rows = []
    for n in d["neg"]:
        v = n["variant"]
        f = n.get("check_findings") or {}
        v3 = n.get("v3_static_g1") or {}
        ia = (n.get("import_any") or [""])
        ia_fail = [x for x in ia if x.startswith("IMPORT-ANY FAIL")]
        if n.get("ERROR"):
            if "no candidate" in n["ERROR"]:
                rows.append((v, "", "후보 없음 -- 이 card base의 split 파일(SR·SD·TL)에 남은 단위 중 이 card MOD도 현재 파일도 아닌 MOD에 배정된 것이 0(SR·TL은 완전 shim, SD 잔류 단위는 SD 배정). 변형을 만들 수 없어 판정 대상 아님"))
            else:
                rows.append((v, n.get("what") or "", "변형 생성 실패(%s) -- 판정 대상 아님" % n["ERROR"][:80]))
            continue
        bits = ["`check` exit %s %s" % (n.get("check_exit"), fmt_findings(f))]
        bits.append("G1 정적 V3 대상 def %s·변이 %s·거부 %s" % (v3.get("n_defs"), v3.get("mutants"), v3.get("n_rejected")))
        bits.append("IMPORT-ANY " + ("FAIL(" + ", ".join(x.split(": ", 1)[1] for x in ia_fail) + ")" if ia_fail else "통과"))
        if n.get("w2_foreign_load") is not None:
            bits.append("ACF 밖 cwd 로드 " + ("성공" if n["w2_foreign_load"] == "ok" else "`%s`" % re.sub(r"\x1b\[[0-9;]*m", "", n["w2_foreign_load"])[:90]))
        rows.append((v, n.get("what") or "", "; ".join(bits)))
    return rows


def expect_of(v, n):
    """judge that must reject (contract numbers) -- derived from what the measured judges actually caught."""
    f = n.get("check_findings") or {}
    ia_fail = any(x.startswith("IMPORT-ANY FAIL") for x in (n.get("import_any") or []))
    w2bad = n.get("w2_foreign_load") not in (None, "ok")
    parts = []
    if f:
        parts.append("계약 2 `check` " + "·".join("`%s`" % k for k in f))
    if (n.get("v3_static_g1") or {}).get("n_defs"):
        parts.append("계약 4 V3 `defs` 비지 않음")
    if ia_fail:
        parts.append("계약 5 IMPORT-ANY FAIL")
    if w2bad:
        parts.append("계약 10 ACF 밖 cwd 로드 실패")
    if v.startswith("R-1") or v.startswith("R-6") or v.startswith("R-7"):
        parts.append("계약 3 (a)")
    if v.startswith("R-2"):
        parts.append("계약 3 (b)")
    if v.startswith("R-D22"):
        parts.append("계약 3 (a)(끝 import 문장이 단위 뒤에 와야 한다)")
    if v.startswith("R-W2"):
        parts.append("계약 3 (b)(재수출 위치)")
    if v.startswith("R-SHIM"):
        parts.append("계약 7 완전 shim")
    return " + ".join(parts) if parts else "**측정한 판정기 중 어느 것도 거부하지 않음**"


def render(c, k, slug, prev, prevM):
    d = D[c]
    mod = "MOD%d" % k
    ln, row = PLAN_LINES[mod]
    Mk = "M%d" % k
    mf = c + ".py"
    units = d["unit_rows"]
    src_counts = d["src_counts"]
    src_txt = "·".join("%s %d" % (AB[f], src_counts[f]) for f in ORDER_SRC if f in src_counts)
    rule_txt = "·".join("%s %d" % (r, n) for r, n in sorted(d["rule_counts"].items(), key=lambda x: (-x[1], x[0])))
    reexp = d["gen"]["reexports"]
    complete = [f for f, v in reexp.items() if "complete shim" in v]
    exporting = list(reexp)
    head = d["gen"]["mod_imports_head"]
    tail = d["gen"]["mod_imports_tail"]
    pos = d["reexport_pos"]
    ia_line = [x for x in d["import_any"] if x.startswith("IMPORT-ANY tried")][0]
    m_ia = re.search(r"tried=(\d+)", ia_line)
    ia_n = int(m_ia.group(1))
    layer_n = d["import_layering"]["n_findings"]
    subj = d["V4"]["subjects"]
    cache_names = {"gmid_sizing_engine": [("_KNEE_L_CACHE", "knee_L_for_kind"), ("_FEASIBLE_L_WINDOW_CACHE", "feasible_L_window")],
                   "sizing_layout_convergence": [("_ACHIEVABLE_BOUND_CACHE", "achievable_metric_bound")]}.get(c, [])
    pt3 = d.get("pt3") or {}
    t0fails = [re.sub(r"^FAILED .*?tests[/\\]", "", x).replace("\\", "/") for x in ((pt3.get("head") or {}).get("failed") or [])]
    t0fails_base = [re.sub(r"^FAILED .*?tests[/\\]", "", x).replace("\\", "/") for x in ((pt3.get("base") or {}).get("failed") or [])]
    ei = d["einst"]
    out = []
    w = out.append
    # ---------------- header
    w("---")
    w("id: 20261002-p3-move-mod%d-%s" % (k, slug))
    w("phase: 3")
    w("evidence_type: equivalence")
    w("gate_change: no")
    w("approval: 20260930-30-module-split-design")
    w("---")
    # ---------------- 의도
    w("## 의도")
    w("")
    w("design `30-module-split` **v8.5**(사용자 승인 UD-0 `20260930-30-module-split-design`) §8 M행·§8.1·§2.2·§3·§10, card **%s**. 틀과 판정 문언은 M1 초안(`_drafts/draft_p3_m1.spec.md`)을 그대로 따르고, 이 card에서 다른 것만 적는다." % Mk)
    w("A = `skills/analog-gmid-design/assets`, SR = `A/sizing_recipe.py`, SD = `A/stick_diagram.py`, TL = `A/topology_library.py`, DR = `A/design_report.py`, ACF = `A/audit_current_forced.py`, %s = `A/%s`(계획 N3.10 %d행 `%s`)." % (mod, mf, ln, row.split(" | ")[0] + " | " + row.split(" | ")[1] + " | " + row.split(" | ")[2] + " |"))
    w("")
    w("**무엇을 하는가**: D0b가 다시 쓴 레지스트리 '이관 목적지' 열과 N3.10 표로 `move_plan plan`이 **%s(`%s`)에 배정한 최상위 단위 전부**를 split 파일(모의 base: %s)에서 새 파일 `A/%s`로 **바이트 그대로** 옮기고," % (mod, mf, src_txt, mf))
    w("단위를 내보낸 split 파일마다 그 이름들의 명시 재수출 줄 하나를 남긴다(design §2.2: `from %s import a, b, _c`(design §2.2의 형태 예 -- 실제 이름 순서는 아래 계약 3 (b)), `import *` 금지, def 래퍼 금지). 함수 몸체·클래스·문장은 한 토큰도 바꾸지 않는다(계획 533행). 배정 집합은 card base에서 도구가 낸다 --" % c)
    w("이 card는 단위 목록을 손으로 정하지 않는다(작성 전 실측 2의 %d단위는 모의 base의 관찰)." % d["assigned"])
    w("")
    w("**MOD 파일 머리(design D-30)**: `%s`의 import 줄 = card base `plan`의 `mod_imports[\"%s\"]` **그대로**(이름마다 import 한 번). 모의 base에서 %d줄이었다(재현할 수치)." % (mf, mf, len(head) + len(tail)))
    if k >= 8:
        w("%s는 번호 %d라 **D-22 (2)**: N3.10 번호 7 이상 모듈(SD·MOD8)을 가리키는 줄은 **파일 끝**(모든 단위 뒤), 나머지와 `from __future__`는 머리 -- 모의 머리 %d줄·끝 %d줄(끝 줄 = %s). 함수 안 지연 import로 바꾸지 않는다(F3)." % (mod, k, len(head), len(tail), "; ".join(bt(x[:80] + ("…" if len(x) > 80 else "")) for x in tail)))
    else:
        w("%s는 번호 %d라 D-22의 '파일 끝 import'(MOD8·MOD9 몫)는 해당 없다 -- 모든 줄이 머리다. 가리키는 트리 모듈은 번호가 작은 MOD뿐이다(ORDER, 계약 7)." % (mod, k))
    w("")
    w("**재수출 줄 위치(design §2.2·D-22, W-2 구체화)**: 재수출 줄 = 그 split 파일 앞머리 묶음(docstring 뒤 연속한 `import`·`from … import`·`sys.path` 조작 식 문장) 중 **마지막 import 문 바로 뒤**(앞 card의 재수출 줄도 import라 그 뒤에 쌓인다).")
    for f in exporting:
        p = pos.get(f, {})
        if f in complete:
            w("* %s: **완전 shim**이 된다(아래 '완전 shim'). 모의 병합본 %s는 %d줄, 이 card 재수출 줄 %d행." % (AB[f], AB[f], p.get("n_lines", 0), p.get("line", 0)))
        elif f == "stick_diagram.py" and k >= 8:
            w("* SD: **SD 파일 끝**(D-22 (1) -- SD의 MOD 8·9 재수출). 모의 병합본 SD %d줄 중 %d행(앞 비어 있지 않은 줄 `%s`, 뒤 `%s`)." % (p.get("n_lines", 0), p.get("line", 0), p.get("prev", "")[:60], p.get("next", "")[:20]))
        elif f == "audit_current_forced.py":
            w("* ACF: `from stick_diagram import load_topology  # noqa: E402` **뒤**%s, 재수출 줄에도 `# noqa: E402`(W-2 -- `p3_followup_questions.md` §3.3 문안 그대로: \"split 파일의 재수출 줄 = 파일 앞머리 묶음(docstring 뒤 연속한 `import`·`from … import`·`sys.path` 조작 식 문장) 중 마지막 import 문 바로 뒤. ACF에서는 `from stick_diagram import load_topology  # noqa: E402` 뒤(재수출 줄에도 `# noqa: E402`).\"). 모의 병합본 ACF %d행(앞 줄 `%s`)." % ("(M2가 더한 `from topology_authoring import _as_set  # noqa: E402` 뒤에 쌓임)" if k == 9 else "", p.get("line", 0), p.get("prev", "")[:70]))
        else:
            w("* %s: import 머리 바로 뒤 -- 모의 병합본 %d행(앞 줄 `%s`)." % (AB[f], p.get("line", 0), p.get("prev", "")[:90] + ("…" if len(p.get("prev", "")) > 90 else "")))
    w("")
    if complete:
        w("**완전 shim(design §3 SHIM (b)(c), %s)**: %s는 이 card에서 배정 단위가 0개가 되어 최상위 문장이 **docstring·`from __future__ import annotations`·재수출 줄뿐**이다. 재수출 줄 = 앞 card들이 더한 `from <MOD> import …` 줄 전부 + 이 card 줄" % (
            "W-1·SHIM (c) 반영", "·".join(AB[f] for f in complete)))
        if any(f in ("sizing_recipe.py", "design_report.py") for f in complete):
            w("+ **base에 있던 `from stick_diagram import …` 줄(SHIM (c) '(base 재수출)' -- SD = MOD7, N3.10 파일이라 D0a 계약 4가 재수출 줄로 센다)**. 그 줄은 지우지 않는다: SD 경유 이름을 이 파일에서 읽는 추적 파일이 있고(F1 초안 `draft_p3_f1.spec.md` '결정 필요 항목' 5 -- 모의 생성기가 그 줄을 지워 F1 모의 base를 정정한 사례), SHIM (c) 이름 집합 = (base 재수출) ∪ (옮긴 이름)이다.")
        w("그 밖의 import 줄(표준 라이브러리·서드파티·N3.10 밖 split 파일 import -- 예 `import math`, `from topology_library import …`)은 **지운다**(SHIM (b) 문언 그대로 -- '남은 일반 import 줄 포함, 그 card가 지운다'). **사용자 결정 W-1 (가)**(2026-10-02 \"(가) T0에서 test import 수정 (Recommended)\"): 그 이름들을 이 파일 경유로 읽던 unit selftest 3줄은 **T0가 이미 출처 import로 바꿨다** -- 그래서 이 card의 완전 shim은 추가 import 없는 완전 shim이고, SHIM (b) 문언을 바꾸지 않는다(작성 전 실측 7·9).")
        w("")
    if c in ("topology_authoring", "instance_report_builder"):
        w("**`__future__`(W-6)**: ACF%s는 FU(card `20261002-p3-future-annotations`)가 docstring 뒤에 `from __future__ import annotations`를 더한 파일이다 -- FU 병합이 착수 조건(FU 없으면 G1 M-4가 그 단위를 거부하고 D0b `import_conflicts`가 %s를 잡는다, design §6.5). 모의는 FU 대역 위에서 `import_conflicts` 0·`move-rejected` 0." % ("·DR" if k == 9 else "", mod))
        w("")
    tmods = ", ".join(sorted({x.split()[1] for x in head + tail if x.startswith("from ") and x.split()[1] in ("gmid_lut", "topology_authoring", "circuit_state_graph", "gmid_sizing_engine", "circuit_metrics", "theta_search", "stick_diagram", "sizing_layout_convergence")}))
    if tmods:
        w("**왜 이 순서인가(design §8.1)**: ORDER(작은 번호부터). %s 병합 뒤라 `%s`의 `mod_imports`가 가리키는 트리 모듈(%s)은 이미 있는 번호 < %d 파일이다 -- 잔여 shim·split 파일 import 0(계약 7)." % (prevM, mf, tmods, k))
    else:
        w("**왜 이 순서인가(design §8.1)**: ORDER(작은 번호부터). 모의 `mod_imports[\"%s\"]`는 트리 모듈을 하나도 가리키지 않는다(표준 라이브러리만 -- MOD2 단위의 트리 안 참조는 MOD2 단위뿐, `upward` 0). 잔여 shim·split 파일 import 0(계약 7). 실제 base에서 B26-1·B34 뒤 `mod_imports`가 바뀌면 같은 조건(번호 < %d)으로 다시 본다." % (mf, k))
    w("")
    w("**착수 조건**: M1과 같음(Phase 2 DoD PASS, B34 → b26pre → backfill → B26-1 → B33 → T0·FU·G1 → D0a → D0b 병합, 면제 묶기(34)·범위 정책(35), D-27 동결 중) + **앞 card %s(`p3-move-mod%s`) 판정 기록**이 gate `master`에 있음. G1이 없으면 V3 대상 def %d·변이 %d(작성 전 실측 8 -- design §4 F5), T0가 없으면 계약 test 위치 가정(F6 -- 작성 전 실측 7)." % (
        prevM, {"M1": "1-gmid-lut", "M2": "2-topology-authoring", "M3": "3-circuit-state-graph", "M4": "4-gmid-sizing-engine", "M5": "5-circuit-metrics", "M6": "6-theta-search", "M8": "8-sizing-layout-convergence"}[prevM],
        d["v3_static"]["pre_g1_defs"], d["v3_static"]["pre_g1_mutants"]))
    w("")
    w("**만들면 배선**: 새 def가 없다(옮긴 정의만). 새 파일 `%s`의 소비자는 split 파일의 재수출 줄(그리고 그것을 거쳐 옮긴 이름을 읽는 추적 파일 -- 작성 전 실측 9)과 뒤 MOD의 `mod_imports`다. 판정 도구 `move_plan check`는 이 card의 `equivalence.commands`에 들어간다(design §2.4 (ii))." % mf)
    w("")
    # ---------------- 계약
    w("## 관찰 가능한 계약")
    w("")
    files_changed = ["`A/%s`(추가)" % mf] + ["`A/%s`(수정)" % f for f in ORDER_SRC if f in exporting]
    w("1. **범위(diff, auditor)**: 이 card `Change-Id` 커밋들의 diff = %s %d파일뿐이다. `git diff --name-only <base> <code_commit> -- tools` 빈 출력(D-16), test·문서·레지스트리·library·`A/` 밖 0. test 커밋 0." % (" + ".join(files_changed), len(files_changed)))
    w("2. **MOVE-AST -- `move_plan check` 발견 0(auditor)**: M1 계약 2와 같은 명령(`MPC` = `tools/migrate/move_plan.py`를 마지막으로 바꾼 판정 기록의 `code_commit` 사본), `--card %s` → exit 0, 11종(`move-set`·`move-rejected`·`changed`·`lost`·`rebind`·`future`·`import-dup`·`stmt-order`·`order`·`shim`·`cache`) 모두 빈 목록." % mf)
    w("   일관성 점검(증거로 세지 않음): `assigned` 수 = `moved_units` 수, `moved_units` 목적지 모두 `A/%s`, `moved_defs` 키 집합 = 계약 4 V3 JSON `moved`의 `to` 집합." % mf)
    w("3. **바이트 이동(auditor, 독립 측정)**: (a) `%s` 최상위 문장 = `mod_imports[\"%s\"]` 줄을 차례로 파싱한 import 문장들 + 옮긴 단위들%s. 옮긴 단위마다 `ast.dump(node)`(docstring 포함, `include_attributes=False`)가 base의 같은 단위와 같다. 모듈 docstring·그 밖의 새 문장 0(M1-1 기본안)." % (
        mf, mf, (" + (끝) D-22 끝 import 문장들" if tail else "")))
    bparts = []
    for f in exporting:
        if f in complete:
            bparts.append("%s = docstring + `from __future__` + base의 N3.10 모듈 재수출 줄들(앞 card 것%s) + 이 card 재수출 `ImportFrom(module='%s', level=0)` 하나 -- 그 밖 문장 0" % (AB[f], " + `from stick_diagram import …`" if f in ("sizing_recipe.py", "design_report.py") else "", c))
        elif f == "stick_diagram.py" and k >= 8:
            bparts.append("SD = base 열 − 옮긴 단위 + 파일 **끝**에 재수출 하나")
        else:
            bparts.append("%s = base 열 − 옮긴 단위 + 재수출 하나를 앞머리 묶음의 마지막 import 뒤에" % AB[f])
    w("   (b) 병합본 split 파일 최상위 문장 열(`ast.dump` 열 비교): %s. 재수출 이름 집합 = 그 파일에서 옮긴 단위가 바인딩하는 이름 전부(`_` 접두 포함, `as` 없음; 이름 순서 = card base `plan` `reexports[\"<그 split 파일>\"]`의 이 MOD 줄 그대로 -- D0a 계약 2 결정성 문단의 코드 포인트 순, 예: 첫 글자 기준 대문자 → `_` 접두 → 소문자). (c) `from __future__ import annotations`가 `%s`의 첫 문장이다." % ("; ".join(bparts), mf))
    w("4. **게이트(auditor, 판정 때 gate `master` 판 도구 -- G1·면제 묶기·범위 정책 병합본)**: V3 exit 0, JSON `defs` = `[]`, `mutants` = 0, `survivors` = `[]`, `move_rejected` = `{}`, `not_targeted` = 0, `targets_by_def` = `{}`; `moved`는 비지 않는다. V6 exit 0, `findings` `[]`, `move_rejected` `{}`. V7 exit 0, `new_defs` `[]`, `move_rejected` `{}`. V5 `diff_paths` `[]`.")
    w("   V4는 FU·M1 선례대로 card가 옮기는 대표 심볼을 subject로 준다(%s → `PASS`, `files` `[]`). V8·V9 N/A." % " ".join("`--subject %s`" % s for s in subj))
    w("5. **IMPORT-ANY(design §10 `import_any` 그대로)**: 병합본에서 `IMPORT-ANY tried=<n> expected=<n> failed=0` 한 줄, `FAIL`·`INVALID` 없음, 종료 코드 0. 기대 수 = `import_layering` `present` ∪ 트리에 있는 `--split` 파일(모의 병합본 %d)." % ia_n)
    w("6. **동작 보존(auditor, base·병합본 같은 조건)**: (a) **PT3 전체** base·병합본 test id 집합 같고 id별 결과 같음, 실패 0(T0 병합 뒤 -- 작성 전 실측 7). (b) **E-LIB**(`e_lib.py` 사본) 출력 JSON 전체가 base와 같다. (c) **E-INST**(`e_inst_p3.py`) 파일럿·`folded_cascode`: `engine_origin`을 뺀 키 전부가 base와 같고, 병합본 `engine_origin`의 모든 경로가 `<iso>` 안이며 `%s`를 포함한다. stdout 사본은 `elapsed=<초>s`를 가리면 같다. base·병합본은 같은 체크아웃 경로에서 차례로 잰다." % c)
    sev = "`order`·`cache`·`shim` 발견 0이 판정이다. 풀어 쓰면 -- `%s`의 import가 가리키는 트리 파일은 N3.10 번호 < %d 파일%s뿐(split 파일 import 0)" % (mf, k, "(끝 import의 SD = MOD7 포함)" if tail else "")
    if cache_names:
        sev += "; 모듈 최상위 빈 dict 캐시 %s는 그것을 읽고 쓰는 %s와 **같은 card에서 같은 파일 `%s`로** 옮긴다(CACHE-ID -- design §2.2; V6 `unbounded_cache`는 주석 대입이라 보지 않는다)" % ("·".join(bt(a) for a, b in cache_names), "·".join(bt(b) for a, b in cache_names), mf)
    else:
        sev += "; 이 card 단위에 모듈 최상위 빈 dict 캐시 없음(CACHE-ID 대상 셋은 M4·M8 몫)"
    sev += "; split 파일의 새 최상위 문장은 재수출 줄뿐이고 재수출 이름마다 바인딩 출처 = `(\"def\", A/%s, 이름)`." % mf
    w("7. **ORDER·CACHE-ID·SHIM**: 계약 2의 " + sev)
    if complete:
        w("   **완전 shim(%s)**: SHIM (b) -- 최상위 문장이 docstring·재수출 줄·`from __future__`뿐(그 밖 import 줄 0, 로직 0); SHIM (c) -- 재수출 이름 집합 = (base 재수출) ∪ (이 card가 옮긴 이름), base에 있던 `if __name__ == \"__main__\"` 블록 불변." % "·".join(AB[f] for f in complete))
    e3b_parts = []
    for m, v in d["e3b"].items():
        e3b_parts.append(m)
    if d["e3"]["same_outside"]:
        e3a = "(a) E3 식(§10 `E3_AST`) base·병합본 D-9 제외 집합 밖 파일 목록 같음, 두 판 모두 `stmt`·`call` 줄 0 아님."
    else:
        e3a = ("(a) E3 식(§10 `E3_AST`) 병합본 D-9 제외 집합 밖 파일 목록 = base 목록 − {완전 shim이 된 split 파일 자신}(SHIM (b)가 그 파일의 N3.10 밖 import 줄 -- 여기서는 SR의 "
               "`from topology_library import …`, 모의 base SR 140행 -- 를 지우므로 그 파일이 TL importer에서 빠진다; 그 밖 차이 0), 두 판 모두 `stmt`·`call` 줄 0 아님.")
    acf_inv = " `base_files_reading_moved_out` = 0이라 `INVALID`인 사본(ACF -- 추적 파일이 ACF에서 옮긴 이름을 import하지 않음)은 기록만 한다(정의상 대상 없음)." if "audit_current_forced.py" in exporting else ""
    w("8. **중간 상태 이름 해석(M1-3 기본안 -- 강화)**: %s (b) E3b 식에서 `stick_diagram`을 이 card가 단위를 내보내는 split 파일 줄기(%s)로 바꾼 사본마다 `<base> <merge>`의 `E3b FAIL` 줄 집합 = `<base> <base>` 사본의 `E3b FAIL` 줄 집합(새 FAIL 0), `ERROR` 없음, `LIVE moved_out=<m>`(m > 0).%s" % (e3a, ", ".join(bt(x) for x in e3b_parts), acf_inv))
    w("9. **레지스트리 정합(REG-DEST 유지)**: 병합본 `plan`(같은 `MPC`, `--rev <merge>`) exit 0, 판정 목록 일곱 0, (단위 키 → MOD) 사상이 base `plan`과 같다(옮긴 단위는 규칙 `A-0`).")
    extra = 10
    if "audit_current_forced.py" in exporting:
        w("%d. **ACF 재수출 위치(W-2)**: 병합본 ACF의 `from %s import …` 줄이 `from stick_diagram import load_topology  # noqa: E402` 뒤에 있고, 저장소 밖 cwd의 새 프로세스에서 `importlib.util.spec_from_file_location`으로 ACF를 로드하면 성공한다(auditor 명령 -- `equivalence.commands`에 추가). 어느 기존 판정도 위치를 보지 않으므로(p3_followup §3.1) 이 계약이 맡는다." % (extra, c))
        extra += 1
    if k >= 8:
        judge = ("배치는 IMPORT-ANY(계약 5 -- 머리로 올리면 `instance_report_builder` 단독 import가 FAIL, 작성 전 실측 10 R-D22)와 계약 3 (a)가 판정하고"
                 if k == 9 else
                 "배치는 **계약 3 (a)의 문장 열 비교가 판정**하고(이 card 병합본에서는 머리로 올려도 순환이 없어 `check`·G1·IMPORT-ANY가 통과한다 -- 작성 전 실측 10 R-D22, open items O-8)")
        w("%d. **D-22 배치와 LAYER(design §2.2 (1)~(4))**: `%s`의 SD%s import 줄은 파일 끝, 그 밖 import는 머리. %s %s, `import_layering --root <iso>`는 %s(LAYER는 F2 뒤 판정 -- 중간 상태 판정 아님, 기록만)." % (
            extra, mf, "·MOD8" if k == 9 else "", "SD의 MOD9 재수출 줄은 SD 파일 끝(계약 3 (b))." if k == 9 else "", judge,
            "발견 %d(큰 번호로의 import `MOD7 stick_diagram → MOD9 instance_report_builder` 1 + 순환 `instance_report_builder ↔ stick_diagram` 1 -- design D-22 (4) 예상, M9~F1 동안 이 둘만 허용)" % layer_n if k == 9 else "발견 %d" % layer_n))
        extra += 1
    w("")
    # ---------------- 신규 시그니처
    w("## 신규 시그니처")
    w("")
    w("| 모듈 | 심볼 | 시그니처 |")
    w("|---|---|---|")
    w("")
    # ---------------- 판정 유형 근거
    w("## 판정 유형 근거")
    w("")
    w("**equivalence, test 커밋 0.** 근거는 M1 초안 '판정 유형 근거'와 같다(계획 N3.12.3 686행 'Phase 3 이동은 `equivalence`', design §8 M행 'test 커밋 0 가능 -- 05 §9.2 289행', FU spec 선례). 브랜치 `role/test/<id>`는 커밋 0으로 만들어 둔다.")
    w("")
    w("**신규 시그니처가 비는 이유**: 옮긴 심볼은 새 심볼이 아니다 -- G1 `moved_defs`가 %d def 전부를 '옮긴 정의'로 인정하고(계약 4 `moved`), 같은 이름이 split 파일 재수출로 계속 import된다." % d["moved_defs"])
    w("")
    w("**계획 838행(V2) 'Phase 3 AST 해시 동일'을 대신하는 것**: 계약 2(`check`)와 계약 3(독립 `ast.dump` 열 비교, docstring 포함). red-green으로 하지 않는 이유는 M1 초안과 같다(위치 단언 영구 test = T0가 없앤 '정의 파일 가정'의 재도입, 위치의 영구 판정은 D0b 계약 test).")
    w("")
    w("**V3 규모(작성 전 실측 8)**: G1 시제품 판 V3 대상 def 0·변이 0. G1이 없으면(gate master 판 대상 선택 식) 새 파일 `%s`와 바뀐 split 파일의 def %d개 전부가 대상, 변이 %d개." % (mf, d["v3_static"]["pre_g1_defs"], d["v3_static"]["pre_g1_mutants"]))
    w("")
    # ---------------- oracle
    w("## oracle 종류와 출처")
    w("")
    w("(c) 동작 보존: PT3 test id별 결과, E-LIB·E-INST 출력 -- 기대값 = base 실행 결과(auditor가 격리 복제본에서 같은 명령으로). (a) 구성: 계약 3의 기대 모양은 계획 533·534행과 design §2.2·§3에서 손으로 정하고, 배정 집합은 card base의 `plan` 출력(D0b 레지스트리 -- 이 card가 바꾸지 않는 입력)이다.")
    w("판정 도구 `move_plan check`는 D0a `code_commit` 사본이고 code-author가 같은 card에서 바꿀 수 없다(D-16). 모의 스크립트(`_drafts/p3kit_m2_m9/`)는 작성 전 실측용 시제품이고 판정 도구가 아니다(작성자≠검증자 -- test-author·code-author·auditor에게 건네지 않는다).")
    w("")
    # ---------------- 거부해야 할 입력
    w("## 거부해야 할 입력")
    w("")
    w("auditor 판정기 자기 점검(병합본 사본에 하나씩 커밋해 판정기가 실제로 거부하는지 먼저 확인 -- 모의 실측은 작성 전 실측 10, 변형은 생성기 `neg226.py`가 card마다 같은 규칙으로 고른 것):")
    w("| ID | 변형(병합본 기준) | 거부해야 할 판정 |")
    w("|---|---|---|")
    for n in d["neg"]:
        if n.get("ERROR"):
            continue
        v = n["variant"]
        desc = {"R-1": "옮긴 def 하나의 몸체 정수 상수 하나 +1 (%s)", "R-2": "재수출 줄에서 이름 하나를 뺌 (%s)", "R-3": "`%s`에 `import sizing_recipe` 한 줄" % mf,
                "R-4": "`%s` import 한 줄을 두 번 (%%s)" % mf, "R-5": "`%s`의 `from __future__ import annotations` 줄을 뺌" % mf,
                "R-6": "다른 MOD 배정 단위를 함께 옮김 (%s)", "R-7": "`%s` 머리에 모듈 docstring 한 줄" % mf,
                "R-W2": "ACF 재수출 줄을 `sys.path.insert` 앞에 둠", "R-SHIM": "완전 shim에 로직 문장 하나 (%s)",
                "R-D22": "끝에 둔 SD/MOD8 import를 머리로 올림 (%s)", "R-CACHE": "캐시 dict만 SR에 남기고 사용 함수는 옮김 (%s)"}[v.split()[0]]
        if "%s" in desc:
            desc = desc % (n.get("what") or "")[:110]
        exp = expect_of(v, n)
        note = ""
        if v.startswith("R-2") and not (n.get("check_findings") or {}).get("rebind"):
            note = " (뺀 이름을 그 파일의 남은 단위가 읽지 않아 `rebind` 0 -- `shim` (c)가 맡는다)"
        if v.startswith("R-5"):
            note = " (`future` 발견 자체는 0 -- W-11: 옮긴 단위가 0이 되어 목적 파일 집합이 빈다, 거부는 `move-rejected`)"
        if v.startswith("R-6") and not (n.get("check_findings") or {}).get("move-set"):
            note = " (그 단위는 G1 M-4로 옮긴 단위가 되지 못해 `move-set`이 아니라 `move-rejected`·`changed`·`lost`로 잡힌다)"
        if v.startswith("R-CACHE") and not (n.get("check_findings") or {}).get("cache"):
            note = " (**`cache` 발견 자체는 0** -- 사용 함수가 캐시 이름을 MOD 파일에서 묶지 못해 G1 M-4로 거부되어 '옮긴 단위'가 아니므로 `cache` 검사 대상이 되지 않는다. 거부는 `move-rejected`·`rebind`가 한다 -- W-11과 같은 모양)"
        if v.startswith("R-W2"):
            note = " (`check`·G1·IMPORT-ANY(cwd = A)는 거부하지 않는다 -- 계약 %d 몫)" % (10)
        if v.startswith("R-D22") and not (n.get("check_findings") or {}) and not any("FAIL" in x for x in (n.get("import_any") or [])):
            note = " (**모의에서 `check`·G1·IMPORT-ANY 모두 통과** -- 이 card 병합본에서는 SD가 MOD8을 import하지 않아 순환이 없다. D-22 (2) 배치는 계약 3 (a)의 문장 열 비교만 본다)"
        if v.startswith("R-6") and (n.get("check_findings") or {}).get("move-rejected") and not (n.get("check_findings") or {}).get("move-set"):
            note = " (그 단위가 MOD 파일에 없는 모듈 전역을 읽어 G1 M-4로 거부된다 -- '옮긴 단위'가 되지 못해 `move-set`이 아니라 `move-rejected`·`changed`·`lost`로 잡힌다)"
        w("| %s | %s | %s%s |" % (v.split()[0], desc, exp, note))
    w("")
    # ---------------- library
    w("## library 회로 적용 여부")
    w("")
    w("적용 -- E-LIB 9회로(`load_topology`·`run_topology_pipeline` 경로), E-INST 파일럿·`folded_cascode`(하네스 `run()`이 엔진 전 경로를 지난다). 회로·넷·소자 이름은 이 card의 도구·판정식에 없다(topology 무관 -- 배정은 레지스트리·N3.10·소스 구조에서만).")
    w("")
    w("## 무동작 판정 입력(무발동 값)")
    w("")
    w("새 산출물 필드 없음. library 회로 전부·기존 test 전부의 판정·산출물이 base와 같다(계약 6). 발동 계수 ID 없음.")
    w("")
    # ---------------- 재현할 수치
    w("## 재현할 수치")
    w("")
    w("(모의 base = `%s`(M1~%s 모의 병합 뒤), 모의 head = `%s`, 스크래치 `C:/g226`, 2026-10-02 -- **전부 관찰**: 사슬은 '작성 전 실측' 머리. 실제 base(B34·B26-1·B33 등 병합 뒤)에서 auditor가 다시 잰다.)" % (d["base"][:7], prevM, d["head"][:7]))
    by_src = {}
    for u in units:
        f, key = u["uid"].split("::", 1)
        a, b2 = u["span"].split(" ")[0].split(":")[1].split("-")
        by_src.setdefault(f, []).append("`%s`(%s~%s, %s)" % (key, a, b2, u["rule"]))
    w("* 배정 %s %d단위(%s), 규칙 %s, 단위 안 def %d. 줄은 card base(모의) 파일 기준:" % (mod, d["assigned"], src_txt, rule_txt, d["gen"]["n_defs_in_units"]))
    for f in ORDER_SRC:
        if f in by_src:
            w("  * %s: %s" % (AB[f], "·".join(by_src[f])))
    w("* `mod_imports[\"%s\"]`(머리 %d줄): %s." % (mf, len(head), " / ".join(bt(x) for x in head)))
    if tail:
        w("  끝(D-22 (2)) %d줄: %s." % (len(tail), " / ".join(bt(x) for x in tail)))
    for f in exporting:
        line = reexp[f].replace("  (complete shim)", "")
        w("* %s 재수출(%s): `%s`." % (AB[f], "완전 shim" if f in complete else ("파일 끝" if (f == "stick_diagram.py" and k >= 8) else "머리"), line))
    w("* `check` exit 0, 발견 11종 모두 0, `assigned` %d·`moved_units` %d·`moved_defs` %d (`check` %.0f s)." % (d["assigned"], d["moved_units"], d["moved_defs"], d["t_check"]))
    v3 = d["V3"]
    w("* V3(G1 시제품, 실행) %s `defs` %s·`mutants` %s·`move_rejected` %s·`moved` %s; V6 %s `findings` %s; V7 %s `new_defs` %s. G1 없는 대상 선택 식: def %d·변이 %d." % (
        v3.get("verdict"), json.dumps(v3.get("defs")), v3.get("mutants"), json.dumps(v3.get("move_rejected")), v3.get("moved_n"),
        d["V6"].get("verdict"), json.dumps(d["V6"].get("findings")), d["V7"].get("verdict"), json.dumps(d["V7"].get("new_defs")),
        d["v3_static"]["pre_g1_defs"], d["v3_static"]["pre_g1_mutants"]))
    w("* V4 %s → exit %s `%s`; V5 exit %s `%s`." % (" ".join("`--subject %s`" % s for s in subj), d["V4"]["exit"], d["V4"]["out"][:120], d["V5"]["exit"], d["V5"]["out"][:120]))
    w("* IMPORT-ANY 병합본 `%s`. `import_layering` 발견 %d%s." % (ia_line, layer_n, " (큰 번호 import 1·순환 1 -- D-22 (4) 예상)" if k == 9 else ""))
    if pt3:
        hs = (pt3.get("head") or {}).get("summary") or [""]
        bs = (pt3.get("base") or {}).get("summary") or [""]
        w("* PT3 base `%s` / 병합본 `%s`, test id %d = %d, id별 결과 차이 %d%s." % (bs[0], hs[0], pt3["ids_base"], pt3["ids_head"], len(pt3["diff"]),
                                                                   (" -- " + "; ".join(bt(x) for x in pt3["diff"])) if pt3["diff"] else ""))
        if t0fails:
            w("  병합본 실패는 전부 T0 몫 A군(모의에 T0의 R-DEF 수정이 없음 -- design §7.1, m_cards_plan W-8): %s." % ", ".join(bt(x) for x in t0fails))
    w("* E-LIB `hash` `%s`(base = 병합본 JSON 전체 같음: %s). E-INST(`e_inst_p3.py` `7d26134a…`): 파일럿 키 %d 중 다른 키 %s, `raw_sha256` `%s`, `without_topology_ref_sha256` `%s`; `folded_cascode` 다른 키 %s, `raw_sha256` `%s`; 병합본 `engine_origin`에 `%s` 포함 %s·전부 `<iso>` 안 %s." % (
        ei.get("elib_hash"), ei.get("elib_equal"), ei["current_reuse_telescopic_ota"]["n_keys"], json.dumps(ei["current_reuse_telescopic_ota"]["diff_keys"]),
        ei["current_reuse_telescopic_ota"]["raw_sha256"], ei["current_reuse_telescopic_ota"]["without_topology_ref_sha256"],
        json.dumps(ei["folded_cascode"]["diff_keys"]), ei["folded_cascode"]["raw_sha256"], c,
        ei["current_reuse_telescopic_ota"]["origin_has_mod"], ei["current_reuse_telescopic_ota"]["origin_in_iso"]))
    e3 = d["e3"]
    w("* E3 식 base `stmt` %d·`call` %d / 병합본 `stmt` %d·`call` %d, 병합본 제외 밖 %d파일(base 목록과 같음: %s%s)." % (
        e3["base"]["stmt"], e3["base"]["call"], e3["head"]["stmt"], e3["head"]["call"], e3["n_outside"], "예" if e3["same_outside"] else "아니오",
        "" if e3["same_outside"] else " -- 차이 = `stmt skills/analog-gmid-design/assets/sizing_recipe.py:140` 한 줄(완전 shim SR이 `from topology_library import …`를 지움, 계약 8 (a))"))
    for m, v in d["e3b"].items():
        w("* E3b 식(%s 사본) `%s`, FAIL %d줄 = base 자기 대조 %d줄, 새 FAIL %d%s." % (m, (v["live"] or [""])[0], v["fail_head"], v["fail_bb"], len(v["new_fail"]),
                                                             " -- 끝 줄 `INVALID`(옮긴 이름을 그 모듈에서 읽는 추적 파일 0)" if (v["last"] and "INVALID" in v["last"][-1]) else ""))
    ph = d["plan_head"]
    w("* `plan`(병합본) 일곱 목록 %s, 사상 차이 %d, 옮긴 단위 규칙 %s." % (json.dumps(ph["lists"]), ph["map_diff"], json.dumps(ph["moved_rule"])))
    if d["w2_acf_foreign_load"] is not None:
        w("* ACF 밖 cwd 로드(계약 10): `%s`." % d["w2_acf_foreign_load"])
    w("")
    return out, d, mod, mf, Mk, complete, exporting, tail, t0fails, t0fails_base, cache_names, ia_n, layer_n


def common_tail(c, k, slug, prev, prevM, rest):
    out, d, mod, mf, Mk, complete, exporting, tail, t0fails, t0fails_base, cache_names, ia_n, layer_n = rest
    w = out.append
    w("## 결정 필요 항목")
    w("")
    w("모두 **기본안이 있다**(원칙 유도 -- 사용자 질문 아님). 사용자 몫일 수 있는 것은 `_drafts/m2_m9_open_items.md`에 모았다(이 card 관련 행: %s)." % OPEN_REF[c])
    for line in CARD_DECISIONS[c]:
        w("* " + line)
    w("* **id 날짜**: 초안 id `20261002-p3-move-mod%d-%s`(slug는 design §8 `p3-move-mod<n>-<이름>`). card 커밋 날짜에 맞춰 바꾼다." % (k, slug))
    w("")
    w("## 작성 전 실측")
    w("")
    w("(재측정 = gate `master` **`4a286f0`**(`git -C <repo> rev-parse gate/master master HEAD` 셋 다 `4a286f0f…`), 2026-10-02. 실제 저장소 쓰기 없음 -- 격리 복제본 `C:/g226/r`(`git clone --no-local`, origin 제거, 빈 hooksPath, TMP/TEMP `C:/g226/tmp`), 작업 끝에 `C:/g226` 삭제, 저장소 `status --porcelain`(37줄)·reflog 시작과 같음.")
    w("B34·b26pre·backfill·B26-1·B33·범위 정책(35)·T0·FU·G1·D0a·D0b는 **모두 미병합**이라 복제본 사슬로 대역했다: %s → M1~M9 이동 생성기 `gen226.py`(M1 키트 `gen_move.py` + 모듈 docstring 없음(M1-1) + W-2 머리 계산) 사슬 `chain226.py`. 원자료·스크립트 `_drafts/p3kit_m2_m9/`." % CHAIN)
    w("M1 수치 재현(사슬 첫 card, M1 초안 '재현할 수치'와 대조): MOD1 8단위·`check` 발견 0·`moved_defs` 22·G1 없는 def 22·변이 590·IMPORT-ANY `tried=6`·PT3 1047 passed·15 xfailed(T0 W-1 대역 포함 판) -- 같은 값. 키 방식을 계약 문언(바인딩 이름)으로 바꾸고 D-11 (가) 토큰을 더한 판이라 M1 초안의 `<stmt:해시>` 판과 MOD4·MOD8·MOD9·SD 수가 다르다(MOD4 104·MOD8 30·MOD9 16·SD 111 -- `p3_followup_questions.md` §1.1 names+① 행과 같음).")
    w("")
    pl = d["plan"]
    w("1. **사실 문장 재측정**: `git show 4a286f0:<plan>` %d행 %s 행 원문(위 '의도'). M1 base 대역 `plan`(재생성 전) exit 1 = `reg_mismatch` 80만(나머지 여섯 0, 배정 403 -- A-4 235·A-1 61·A-5 57·A-2 38·A-6 7·A-7 2·A-K 2·A-3 1), 재생성 뒤 exit 0·일곱 0·사상 차이 0." % (PLAN_LINES[mod][0], mod))
    w("2. **단위 집합(관찰)**: 이 card 모의 base `plan` exit 0, 일곱 목록 %s, %s %d단위(%s). 배정은 앞 card들이 옮긴 단위를 `A-0`으로 같은 MOD에 두므로 사슬 어디서나 같다(card마다 사상 차이 0 -- 계약 9)." % (json.dumps(pl), mod, d["assigned"], ", ".join("%s %d" % (AB[f], n) for f, n in d["src_counts"].items())))
    w("3. **`mod_imports`·PLAN-LAYER**: `mod_imports[\"%s\"]` %d줄(재현할 수치), `import_conflicts` 0, `upward` 0, `import_time_high` 0." % (mf, len(d["gen"]["mod_imports_head"]) + len(tail)))
    w("4. **쓰기 경로(계획 N3.12.2)**: `A/%s`·%s = gmid-code-author(엔진 소스). test-author 산출물 없음. 판정 기록·계약 측정 = auditor. `tools/**`는 누구도 바꾸지 않는다(D-16)." % (mf, "·".join("`A/%s`" % f for f in exporting)))
    w("5. **계획서 소비자·이름 충돌**: 이 card는 이름을 지우거나 바꾸지 않는다(위치만, 재수출로 같은 import 경로 유지). 새 파일 이름 `%s`는 `4a286f0`에 없다(`git ls-tree` 빈 출력)." % mf)
    w("6. **미배선**: 새 def 0. V7 `new_defs` [](G1 시제품) -- 면제 불필요.")
    t0line = "7. **기존 계약 test**: 모의 사슬에는 T0의 R-DEF 수정이 없다(W-1 import 3줄만 대역). 이 card 병합본 PT3 실패 = %s -- 전부 design §7.1 A군(T0 몫, m_cards_plan W-8)%s." % (
        (", ".join("`%s`" % x for x in t0fails) if t0fails else "0"),
        ("; base(앞 card 병합본) 실패 = " + (", ".join("`%s`" % x for x in t0fails_base) if t0fails_base else "0")) if True else "")
    w(t0line)
    for line in CARD_T0[c]:
        w("   " + line)
    w("8. **V3 규모**: G1 시제품 `mutate_changed.py --root C:/g226/r --base %s --head %s … --gmid-phase=3 --gmid-strict=` → 계약 4 값(재현할 수치). G1 없는 판(gate master `changed_defs`·`mutants` 정적 계수): def %d·변이 %d. 범위 정책(35) 시제품은 키트에 없다 -- 대상 def 0이라 `not_targeted`·`targets_by_def`는 0·`{}`일 것으로 본다(판정 때 실측)." % (
        d["base"][:7], d["head"][:7], d["v3_static"]["pre_g1_defs"], d["v3_static"]["pre_g1_mutants"]))
    e3same = "(base와 같음)" if d["e3"]["same_outside"] else "(base − 완전 shim SR 자신 -- 계약 8 (a))"
    w("9. **읽는 쪽 범위**: E3b 식 사본 %s -- 전부 재수출로 계속 해석된다(새 FAIL 0). E3 식 importer 병합본 %d파일%s. W-1 점검(`p3fq_kit/shim_import_reads.py`를 병합본에 돌려 N3.10 모듈 재수출이 아닌 import 바인딩 이름을 TL·SR·DR 경유로 읽는 곳): %d곳%s." % (
        "; ".join("%s `%s`" % (m, (v["live"] or [""])[0].replace("E3b LIVE ", "")) for m, v in d["e3b"].items()), d["e3"]["n_outside"], e3same, d["w1_nonreexport_reads"],
        " -- T0 W-1 대역이 3줄을 고친 상태라 0" if d["w1_nonreexport_reads"] == 0 else " (" + json.dumps(d["w1_sample"], ensure_ascii=False)[:200] + ")"))
    w("10. **거부 입력 실측**(병합본 사본에 하나씩 커밋, 모의 `check` + G1 시제품 정적 V3 + IMPORT-ANY(+ ACF 밖 cwd 로드)): 원자료 `p3kit_m2_m9/out/neg.jsonl`.")
    for v, what, res in neg_rows(c, d):
        w("    * %s `%s`: %s." % (v.split()[0], what[:100], res))
    w("11. **test 이름·모양**: 새 test 없음.")
    w("12. **같음 판정**: 계약 3은 `ast.dump` 문자열 열 비교(순서 포함), 계약 6 (a)는 test id별 결과 문자열, (b)는 JSON 전체, (c)는 `engine_origin`을 뺀 키별 값 비교 + 경로 포함 조건. `set`을 `==`로 비교하는 계약 없음.")
    w("13. **red 모양**: red 없음(equivalence). 거부 확인은 auditor 측정.")
    w("14. **양식**: gate `4a286f0` `tools/gates`(`git archive`)의 `role_paths.parse_spec_card(text, expect_id=\"20261002-p3-move-mod%d-%s\")` → 예외 없음, 머리 `phase` 3·`evidence_type` equivalence·`gate_change` no·`approval` 1, 본문 절 11개(양식 순서 그대로). `interface_card.py <이 spec> --root <모의 base 트리>` → %s." % (k, slug, IFACE.get(c, "(미실행)")))
    w("15. **앞 card 의존 재확인(오케스트레이터, card 커밋 직전)**: (i) gate `master`에 %s 판정 기록 (ii) 그 판정 기록의 `code_commit`(= 이 card base)에서 `plan` 출력의 `%s` 배정 단위 목록·`mod_imports[\"%s\"]` -- '재현할 수치'를 그 값으로 바꾼다 (iii) `git diff --stat <D0b 병합> gate/master -- tools docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` 빈 출력·엔진 diff는 M1~%s card 커밋뿐(D-27 동결)." % (prevM, mf, mf, prevM))
    w("16. **비용(모의)**: card 한 건 사슬(plan + 생성 + check + G1 정적 V3 + IMPORT-ANY + E3b + W-1 점검) %.0f s, `check` %.0f s, PT3 약 5~6분, E-INST 파일럿 약 6~8분(다른 측정과 겹친 시간)." % (d["sec"], d["t_check"]))
    w("")
    return "\n".join(out) + "\n"


OPEN_REF = {}
CARD_DECISIONS = {}
CARD_T0 = {}
IFACE = {}
exec(open("C:/g226/kit/card_notes.py", encoding="utf-8").read())
for c, k, slug, prev, prevM in CARDS:
    rest = render(c, k, slug, prev, prevM)
    text = common_tail(c, k, slug, prev, prevM, rest)
    p = "%s/draft_p3_m%d.spec.md" % (OUTDIR, k)
    open(p, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote", p, len(text))
