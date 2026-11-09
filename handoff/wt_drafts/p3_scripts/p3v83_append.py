# v8.3 바이너리 삽입·append(앞 바이트 불변 단언). 사용:
#   python -B p3v83_append.py design <draft_phase3_design_v8.md>             -- 부록 A F4v83 행 삽입(F3v82 행 바로 뒤) + 부록 K append
#   python -B p3v83_append.py logs <_drafts 디렉터리>                         -- phase3_revision_log.md 절 + pending_questions.md Q-B34-PHASE 닫음 append
import hashlib, os, sys
mode, P = sys.argv[1], sys.argv[2]

def append(path, text):
    b0 = open(path, "rb").read()
    add = text.encode("utf-8")
    if not b0.endswith(b"\n"):
        add = b"\n" + add
    with open(path, "ab") as f:
        f.write(add)
    b1 = open(path, "rb").read()
    assert b1[:len(b0)] == b0 and len(b1) == len(b0) + len(add), path
    print("appended", path, len(b0), "->", len(b1))

F4 = ("| F4v83 | `a796468` 복제본 `C:/g149/el_base`와 시제품 `C:/g149/el_p1`~`el_p5`(`p3_scripts/p3v83_mkproto.py`, 실행 명령 `p3v83_out/run_elib.sh`·`run_einst.sh`, 로그 `p3v83_out/log_*.txt`: p1 = SD 끝에 frozen `RailDeclaration(nets: frozenset)`·`rail_declaration(topology)`, `load_topology`가 `meta[\"rails\"] = rail_declaration(data)`; "
      "p2 = nets에서 마지막 넷을 뺌; p3 = p1 + `meta[\"_g149_unexpected\"] = 1`; p4 = p1 + `RailDeclaration`에 계약 밖 필드 `polarity: str = 'junk-g149'`(7차 검토 S1); p5 = p1 + `two_stage_ota` library `supply_nets`에 `agnd`(7차 검토 m1)), "
      "사본 sha256 `e_lib.py` `41b72d7d…`·`e_lib_p3.py` `c6b82fc7…`·`e_inst_df36.py` `6cc48495…`·`e_inst_p3.py` `7d26134a…`; E-INST는 `el_base`의 df36·p3와 `el_p1`의 p3; "
      "`bash D/p3_scripts/p3v83_judge_scenarios.sh D/draft_phase3_design_v8.md D/draft_phase3_design_v8.v8.2.md C:/g149/out_e C:/g149/js C:/g149/el_base a796468 C:/g149/el_` → `p3_scripts/p3v83_judge_scenarios.out.txt`(v8.3 판정 python을 design에서 그대로 뽑아 실행 -- sha256 `ae6422d6…`; 대조로 v8.2 사본의 판정 python `37fecfea…`도 같은 입력에) "
      "| 원래 `e_lib.py` `hash`: base `1d2e3bf6…`, p1 `c1213331…`·p2 `e01c7b52…`(F3v82와 같음), p3 `e044f286…`, p4 `1ee707d2…`, p5 `9812155e…`(7차 검토 재현과 같음). `e_lib_p3 rails`: base·p1·p2·p4·p5 `1d2e3bf6…`, p3 `36d01e94…`. "
      "E-INST raw: 파일럿 `2fc426d9…`·`folded_cascode` `ef3cd996…`가 base df36·base p3·p1 p3에서 같음(F3v82와 같음). "
      "v8.3 판정: p1 `E5 E-LIB/E-INST PASS`; p2 `E5 E-LIB rails 계약 FAIL` 9줄 + `FAIL`; p3 `E5 E-LIB(rails 뺀 해시) 다름/실패` + `FAIL E-LIB`; **p4 `E5 E-LIB rails 계약 FAIL` 9줄 + `FAIL`(v8.2 판정 = `PASS`)**; **p5 `E5 E-LIB rails 계약 FAIL two_stage_ota` + `FAIL rails:two_stage_ota`(v8.2 판정 = `PASS`)**; "
      "고장 입력(P2D `e_lib.py` `hash` 한 글자) `E5 INVALID: e_lib_p3(MASK 없음) ≠ e_lib on P2D` + `FAIL`; 없는 P2D 커밋(`git show` 실패) 9회로 모두 `rails 계약 FAIL`(기대 nets `None`, fail-closed). "
      "측정 시간: E-LIB 4~6초, E-INST `folded_cascode` 55~59초·파일럿 417~480초 |\n")

K = """
## 부록 K. 초안 v8.2 대비 정정(7차 검토 `review7_phase3_v82.md`와 B26 묶음 답 반영 -- 대응표는 `phase3_revision_log.md` '초안 v8.2 → v8.3' 절)

| # | v8.2 | v8.3 |
|---|---|---|
| 1 | §10 E5 판정 python `rails` 계약 판정이 `__dc__`와 `nets` 성분만 봄(계약 밖 필드가 끼어도 PASS -- S1) | `hv == {"__dc__": "RailDeclaration", "nets": want}` 정확 일치. E5 행 (iv)·D-28 (e) 문장. F4v83 p4: v8.2 PASS → v8.3 FAIL |
| 2 | 계약값 `supply_nets`를 HEAD library에서 읽음(P2D~HEAD 사이 선언 변경이 안 보임 -- m1) | `git -C "$ISO" show "$P2D:…/library/<회로>.topology.json"`(판정 python 인자에 `$P2D`). F4v83 p5: v8.2 PASS → v8.3 FAIL, 없는 P2D는 fail-closed |
| 3 | 승인 질문 UD-0 (c) 기본안에 비용 문장 없음, '실측으로 확인'(m2) | 기본안 비용(빼는 필드 목록이 design 상수 -- 사이 card 계약이 바뀌면 design 개정 승인), '계약 모양 시제품으로 실측' |
| 4 | A2-③ 미결(승인 질문 다섯 번째 항목, §9.2 행·§11-11·§6.4 인계, D-28 (e) (나) 분기 -- S2) | **결정됨**(사용자 답 2026-10-01 B26 묶음 [card phase] "phase 3 + 정정 기록 (Recommended)", decision 기록 `20261001-b26-phase3-cards`): 승인 질문 네 항목, §9.2 A2-③ 행·§11-11 = 결정 사실(V1 `--gmid-phase=3`, strict 집합 빈 집합), §6.4 인계 문장 정정, D-28 (e) (나) 분기 삭제(`bv == hv` 허용은 대안 (c-2) B0 몫으로 남김) |
| 5 | 네 card가 어느 DoD 목록에 드는지 없음 | 네 card `phase: 3` → Phase 3 DoD N6.3 목록(`^phase: 3$`)에 든다, 기록 그대로 세고 다시 판정하지 않는다(§9.1), §8.1 표 행·D-23(design 30 승인은 기다리지 않음 -- 그 기록) |
| 6 | §6.4 '바뀌는 def'에 B40·C1·C2 없음, U3 면제와 M card 이동 관계 없음 | B40 반환 키 삭제(U4)·정리 C1·C2(U3) 추가. 면제 id의 모듈 접두 `stick_diagram:`은 M card 이동을 따라가지 않지만 옮길 필요 없음 -- B26-1 V3에서 쓰이고 끝나며(M1 전 병합), M card에서 그 def는 변이 대상이 아니고(E2 ① `mutants` = 0), DoD E2는 M card만 다시 돈다. 그 def를 바꾸는 뒤 card는 해시가 달라져 어차피 새 승인 |
"""

if mode == "design":
    s = open(P, "rb").read().decode("utf-8")
    i = s.index("| F3v82 |"); j = s.index("\n", i) + 1
    assert s.count("| F3v82 |") == 1 and "| F4v83 |" not in s
    s2 = s[:j] + F4 + s[j:]
    b0 = s.encode("utf-8"); b1 = s2.encode("utf-8")
    assert b1[:len(s[:j].encode("utf-8"))] == b0[:len(s[:j].encode("utf-8"))] and b1.endswith(b0[len(s[:j].encode("utf-8")):])
    open(P, "wb").write(b1)
    print("inserted F4v83")
    append(P, K)
elif mode == "logs":
    D = P
    h = lambda p: hashlib.sha256(open(os.path.join(D, p), "rb").read()).hexdigest()[:16]
    log = f"""
---

# 초안 v8.2 → v8.3 (7차 검토 `review7_phase3_v82.md` + B26 묶음 답 반영, 2026-10-01)

입력: `_drafts/review7_phase3_v82.md`(막는 것 0·고칠 것 2·minor 3, '고친 뒤 승인 요청 가능'), `_drafts/phase3_followups_from_b26.md`(B26 묶음 4문항 답 -- `_drafts/user_decisions.md` 67행 [Q-B34-PHASE]).
개정 전 사본: `draft_phase3_design_v8.v8.2.md`, `phase3_approval_question.v8.2.md`, `p3_doc_amendments.v8.2.md`, `phase3_revision_log.v8.2.md`. 문서 개정 문안·`e_inst_p3.py`·`e_lib_p3.py`·spec card(G1·T0·D0a)는 바꾸지 않았다.

| # | 발견 | 대응 |
|---|---|---|
| S1 | E5 `rails` 계약 판정이 `nets`만 봄(계약 밖 필드 fail-open) | 판정 python `cok`를 `hv == {{"__dc__": "RailDeclaration", "nets": want}}` 정확 일치로. 재측정 F4v83: p4(polarity 필드) v8.2 PASS → v8.3 `rails 계약 FAIL` 9줄 + FAIL. p1 PASS·p2·p3 FAIL·고장 INVALID는 그대로 |
| S2 | 승인 질문에 이미 답한 A2-③ | 질문에서 A2-③ 블록 삭제(네 질문), 머리에 '이미 답함' 한 줄, 승인 기록 목록 문장을 `20261001-b26-phase3-cards` 참조로. design §9.2 머리·A2-③ 행(결정됨), §11-11(해소됨 -- V1 `--gmid-phase=3`, strict 빈 집합), §6.4 인계 괄호, D-28 (e) (나) 분기 삭제, E5 행 (iv) |
| m1 | 계약값 출처가 HEAD library | 판정 python 인자에 `$P2D`, `git -C "$ISO" show "$P2D:…/library/<회로>.topology.json"`에서 `supply_nets`. F4v83 p5(two_stage_ota에 agnd) v8.2 PASS → v8.3 `rails 계약 FAIL two_stage_ota`. 없는 P2D는 9회로 FAIL(fail-closed) |
| m2 | UD-0 (c) 기본안 비용 문장 없음, '실측으로 확인' | 기본안 비용 한 줄(빼는 필드 목록 = design 상수, 사이 card 계약 변경 시 design 개정 승인), '계약 모양 시제품으로 실측' |
| m3 | E5 사본을 P2D 판에서 뜸(기록용) | 변경 없음(D-9로 같은 바이트, sha256 기록) |
| B26-1 | A2-③ 답(phase 3 + 정정 기록) | 위 S2. 네 card가 Phase 3 DoD `^phase: 3$` 목록에 듦(§8.1 표·§9.1·D-23 행·D-23 글머리), design 30 승인은 기다리지 않음(기록 범위 설명) |
| B26-2 | U4(B40) | §6.4 '바뀌는 def'에 `propose_device_roles_gap_fill` `unavailable_reason` 키 삭제 |
| B26-3 | U3(정리 C1·C2 + `range` const− 면제) | §6.4 '바뀌는 def'에 C1·C2, 표 뒤 'B26-1 등가 면제와 M card 이동' 문단 -- 면제 id 모듈 접두는 이동을 따라가지 않지만 B26-1 V3에서 쓰이고 끝남(M1 전 병합), M card에서 그 def는 `mutants` = 0(E2 ①), DoD E2는 M card만 재실행(§10 `cards.txt`), 그 def를 바꾸는 뒤 card는 해시가 달라 어차피 새 승인. 근거: `draft_v3_exempt_binding.spec.md` 14행(id 형식)·묶기 규칙 '해시 바뀌면 자동 무효' |
| B26-4 | U5(P9 시그니처 test) | 이 판 변경 없음 -- `inspect.signature` 단언은 바이트 이동이면 같고, `test_dup_kcl_edges.py`의 F1·T0 호출부 포함 여부는 §9.1 재측정 (1)이 D0b base에서 다시 센다 |

## 대상 판 해시(v8.3, sha256 앞 16자리 -- 승인 질문 끝 목록과 같음)

* design `draft_phase3_design_v8.md` `{h("draft_phase3_design_v8.md")}`(v8.2 `dc2a887b2c11f382`), 승인 질문 `phase3_approval_question.md` `{h("phase3_approval_question.md")}`(v8.2 `d2476b580f548fdf`).
* 판정 python(design에서 추출) `ae6422d680dae2ab`(v8.2 `37fecfeae03308fd`).
* **v8.3 밖 변경**: G1 spec card `draft_p3_g1.spec.md` `{h("draft_p3_g1.spec.md")}`(v8.2 `3a99df21414d6e99` = `draft_p3_g1.spec.pre-kit.md`) -- 이 개정이 아니라 G1 착수 키트 작업(22:40 수정, `_drafts/g1_kit/`)이 바꿨다(V3 변이 15,677 → 15,650·V6 861 → 859를 `0f23786`에서 다시 잼, 합성 단계 `class-method-edited` 추가 등). 질문 전에 G1 card가 확정됐는지 확인하고 해시를 다시 계산한다.
* 바뀌지 않음: 문서 개정 `{h("p3_doc_amendments.md")}`, T0 `{h("draft_p3_t0.spec.md")}`, D0a `{h("draft_p3_d0a.spec.md")}`, `e_inst_p3.py` `{h("p3_scripts/e_inst_p3_proposed/e_inst_p3.py")}`, `e_lib_p3.py` `{h("p3_scripts/e_lib_p3_proposed/e_lib_p3.py")}`.
* 도구: `p3_scripts/p3v83_patch.py`(design 본문 교체, 1회 단언), `p3v83_patch_question.py`(승인 질문, 해시 절 재계산), `p3v83_append.py`(부록 A F4v83 삽입·부록 K·이 절·pending 닫음 -- 앞 바이트 불변 단언), `p3v83_judge_scenarios.sh` `{h("p3_scripts/p3v83_judge_scenarios.sh")}` → `p3v83_judge_scenarios.out.txt` `{h("p3_scripts/p3v83_judge_scenarios.out.txt")}`. 스크래치 `C:/g149`(끝에 삭제).
"""
    append(os.path.join(D, "phase3_revision_log.md"), log)
    pq = """
- **[Q-B34-PHASE 닫음]** (2026-10-01) 답 **"phase 3 + 정정 기록 (Recommended)"**(B26 묶음 4문항 [card phase], 질문 21:10·답 21:14 KST, 세션 jsonl `63c6146a-…` AskUserQuestion `toolu_01KTtsbRiK7S3cv1coUsAyPw`, 요약 `_drafts/user_decisions.md` 67행).
  기록 = decision `20261001-b26-phase3-cards`(문안 `_drafts/approval_20261001-b26-phase3-cards.md`): 네 card(B34·b26pre·backfill·B26-1) `phase: 3`, Phase 2 DoD 뒤·Phase 3 M card 전 순서 유지, A2 ③ 문구 정정(옛 기록 불변), design 30 승인·U-03을 기다리지 않음.
  반영: Phase 3 design v8.3(§9.2 A2-③ 결정됨, §11-11 해소, 네 card가 Phase 3 DoD `^phase: 3$` 목록), 승인 질문 v8.3에서 A2-③ 삭제(네 질문). 이 항목은 더 묻지 않는다.
"""
    append(os.path.join(D, "pending_questions.md"), pq)
