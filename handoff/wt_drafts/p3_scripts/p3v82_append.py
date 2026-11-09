"""v8.2: design 부록 A에 F1v82~F3v82 행·한계 줄 삽입, 부록 J와 revision log 절을 바이너리 append(앞 바이트 불변 단언).
사용: python -B p3v82_append.py <design.md> <revision_log.md> <question.md>"""
import hashlib, sys
DES, LOG, Q = sys.argv[1:4]
D = "D"
rows = (
"| F1v82 | `bash D/p3_scripts/p3v82_out/run_reach.sh`(`$PY -B -P D/p3_scripts/p3v82_relaxed_reach.py C:/g135/iso_r <회로> <out>`, `a796468`, SPECS 4회로) → `p3v82_out/<회로>.json` | "
"파일럿: `run_matching_safety_with_finger_growth` 1회, `relaxed_pairs` = `M4a/M4b` `interdig_ok` True·`M3a/M3b` False, 같은 값이 `save_instance_json`의 `pipeline_result[\"relaxed_pairs\"]`로 넘어감; "
"instance.json(92,573 B)·report.html(77,728 B)·stdout에서 `relaxed` 0·`interdig_ok` 0(`interdig` 48·30회는 전부 `interdigitation` -- audit 3b 체크 이름), instance.json 최상위 키 = "
"`schema_version`·`topology_ref`·`sizing`·`netlist`·`floorplan`·`box_shape`·`audit_row_split`·`coverage`. `folded_cascode`: 호출 1, `relaxed_pairs` 빈 목록, instance.json `relaxed` 0. "
"`two_stage_ota`·`nmcnr_amplifier`: 이 def 전에 하네스가 `ValueError`(KVL 합 불일치)로 멈춤, instance.json 없음(backfill card 초안 'library 회로 적용 여부'와 같음). "
"결론: backfill이 바꾸는 값은 E-INST·보고 산출물에 닿지 않는다(D-28 (e) ③) |\n"
"| F2v82 | `bash D/p3_scripts/p3v82_out/run_elib.sh`(`a796468` 복제본 `C:/g135/el_base`, 사본 sha256: `e_lib.py` `41b72d7d…`, `e_lib_p3.py` `c6b82fc7…`) → `p3v82_out/summary.txt` | "
"`e_lib.py` `hash` `1d2e3bf6…` = `e_lib_p3.py`(인자 없음) = `e_lib_p3.py rails`; 두 `e_lib_p3` 출력에서 `masked_meta_keys`·`circuits.*.masked`를 빼면 `e_lib.py` 출력과 같음(동등), `rails` 실행의 `masked.rails` 9회로 모두 `<ABSENT>` |\n"
"| F3v82 | 같은 실행의 시제품 `C:/g135/el_p1`(`a796468` + SD 끝에 `RailDeclaration(nets: frozenset)`·`rail_declaration(topology)`, `load_topology`가 `meta[\"rails\"] = rail_declaration(data)` -- B26-1 계약 1·2 모양), "
"`el_p2`(nets에서 마지막 넷을 뺌), `el_p3`(p1 + `meta[\"_g135_unexpected\"] = 1`); E-INST는 `el_base`의 `e_inst_df36`·`e_inst_p3`와 `el_p1`의 `e_inst_p3`; "
"`bash D/p3_scripts/p3v82_judge_scenarios.sh D/draft_phase3_design_v8.md C:/g135/out_e C:/g135/js C:/g135/el_p1` → `p3v82_judge_scenarios.out.txt`(§10 E5 판정 python을 design에서 그대로 뽑아 실행 -- sha256 `37fecfea…` = `p3v82_e5_judge.py`) | "
"원래 `e_lib.py` `hash`: p1 `c1213331…`·p2 `e01c7b52…`·p3 `ab5be683…`(base `1d2e3bf6…`와 모두 다름, 9회로 모두 `per_hash.load`만 다르고 V1·V2 같음 -- `run_topology_pipeline` 반환은 meta를 담지 않는다). "
"`e_lib_p3 rails`: p1·p2 `1d2e3bf6…`(base와 같음), p3 `58e3a1e8…`. E-INST: 파일럿 `raw_sha256` `2fc426d9…`·`folded_cascode` `ef3cd996…`가 base df36·base p3·p1 p3 셋에서 같음(`rails`는 instance.json에 닿지 않는다; 값은 F3v8 `0f23786`과도 같음). "
"판정: p1 `E5 E-LIB/E-INST PASS`; p2 `E5 E-LIB rails 계약 FAIL` 9줄 + `FAIL`; p3 `E5 E-LIB(rails 뺀 해시) 다름/실패` + `FAIL E-LIB`; 고장 입력(P2D `e_lib.py` `hash` 한 글자 변경) `E5 INVALID: e_lib_p3(MASK 없음) ≠ e_lib on P2D` + `FAIL`. "
"측정 시간(CPU 경합): E-LIB 4~6초, E-INST `folded_cascode` 53~62초·파일럿 269~388초 |\n")
limit = ("v8.2 추가 한계: F3v82의 HEAD 대용은 B26-1 계약 1·2만 흉내 낸 시제품이다(B26-1 실제 병합본이 아니다 -- SR 소비처·접근자 거부 규칙 없음). 보이는 것은 '판정 python이 계약 모양의 `rails` 추가를 받고, nets가 틀리거나 "
         "다른 meta가 바뀌면 거부하며, 동등 확인이 고장 입력을 INVALID로 낸다'이다. 실제 P2D·HEAD 값은 DoD E5가 잰다. F1v82는 `a796468` 엔진(backfill 수정 전)에서 값이 '저장 함수까지 가고 파일에는 없다'를 보인 것이고, "
         "backfill 뒤에도 `save_instance_json`의 키 집합이 같다는 것은 그 card 초안(엔진 수정 = backfill 호출 줄 삭제뿐)에서 온 추론이다 -- 어긋나면 E5 (ii)가 FAIL로 드러낸다.\n")

t = open(DES, "rb").read()
anchor = "| F5v8 |".encode("utf-8")
assert t.count(anchor) == 1
i = t.index(anchor); j = t.index(b"\n", i) + 1
t = t[:j] + rows.encode("utf-8") + t[j:]
anchor2 = "v8 추가 한계: F1v8·F3v8".encode("utf-8")
assert t.count(anchor2) == 1
k = t.index(anchor2); k2 = t.index(b"\n", k) + 1
t = t[:k2] + limit.encode("utf-8") + t[k2:]
open(DES, "wb").write(t)

appJ = ("\n## 부록 J. 초안 v8.1 대비 정정(오케스트레이터 결정 -- 대응표는 `phase3_revision_log.md` '초안 v8.1 → v8.2' 절)\n\n"
"| # | v8.1 | v8.2 |\n|---|---|---|\n"
"| 1 | UD-0 (c) 기본안 = B0 비교(선례에서 고르지 않은 대안 모양), 대안 = 선례 모양(측정 명령 없음) | 기본안 = 선례 `20260930-phase2-e4-baseline` 모양(P2D = Phase 2 DoD 대상 커밋과 비교, 사이 card가 의도적으로 바꾼 필드만 그 card 계약값으로 따로 판정, 나머지 해시 같음), 대안 = B0 비교(같은 블록에서 `P2D=`만 B0로). 원칙: 같은 상황의 사용자 선택(\"둘다 기본안으로 진행해\")을 따른다 |\n"
"| 2 | 빼는 필드 미정('B26-1 `meta[\"rails\"]` 등', backfill `interdig_ok` 도달 미측정) | card 초안 계약에서 유도 + 실측: E-INST 없음(B34 계약 7, b26pre test-only, backfill `interdig_ok`는 instance.json·report에 0 -- F1v82, B26-1 계약 8), E-LIB `meta[\"rails\"]` 하나(B26-1 계약 2·8, 계약값 `RailDeclaration(nets = supply_nets)`) -- D-28 (e), 판정 python `EXCL_INST`·`MASK_META` |\n"
"| 3 | E-LIB 측정 = `e_lib.py` 사본(키를 뺄 수 없음) | DoD E5용 `e_lib_p3.py`(`e_lib.py` + meta 키 빼기 인자 한 곳, design 커밋에 함께 -- 문서 개정 §8). 인자 없으면 `e_lib.py`와 같음(F2v82), E5 (i)이 P2D에서 먼저 잰다. M card는 `e_lib.py` 그대로 |\n"
"| 4 | §10 E5 블록 = B0 대 HEAD | P2D 대 HEAD, E-INST 키별 `field_sha256`·raw·without_topology_ref, E-LIB `rails` 뺀 해시 + 회로별 `rails` 계약값 판정(A2-③ (나)면 P2D에도 같은 값 허용). 판정 python을 design에서 뽑아 시제품 4입력에 실행(F3v82: PASS·계약 FAIL·해시 FAIL·INVALID) |\n"
"| 5 | §9.2 UD-0·승인 질문 UD-0 (c) | 기본안(Recommended)·대안 교체, 선례 인용, 새 스크립트 문서 개정 목록에 추가, '수정 요청' 예시 (c)를 B0로 |\n")
t = open(DES, "rb").read(); h0 = hashlib.sha256(t).hexdigest()
open(DES, "ab").write(appJ.encode("utf-8"))
t2 = open(DES, "rb").read(); assert hashlib.sha256(t2[:len(t)]).hexdigest() == h0

sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
import os
base = os.path.dirname(DES)
logsec = ("\n---\n\n# 초안 v8.1 → v8.2 (오케스트레이터 결정 -- UD-0 (c) 기본안을 선례 모양으로, 2026-10-01)\n\n"
"입력: 오케스트레이터 결정(원칙: 같은 상황에서 사용자가 고른 쪽을 따른다 -- 승인 `.ai/approvals/20260930-phase2-e4-baseline.md`, 사용자 원문 \"둘다 기본안으로 진행해\"; 그 질문의 기본안 = da03c0e와 Phase 2 마지막 병합본을 같은 경로에서 비교하고 `topology_ref`만 DF-36 계약값으로 판정, 대안 = card별 판정 기록 사슬). "
"개정 전 사본: `draft_phase3_design_v8.1.md`, `phase3_approval_question.v8.1.md`, `p3_doc_amendments.v8.1.md`. 측정: `a796468` 복제본(`C:/g135`, 끝나면 삭제), 엔진은 gate `master` `0f23786`과 같다.\n\n"
"| # | 대상 | 대응 |\n|---|---|---|\n"
"| 1 | UD-0 (c) 기본안 | B0 비교 → 선례 모양(P2D 비교 + 의도된 필드만 계약값으로 따로 판정). B0는 대안(같은 블록에서 `P2D=`만 바꿈). design 머리·D-28 가운데·(e)·§9.2 UD-0 행·§10 E5 블록·행, 승인 질문 (c)·'수정 요청' 예시·머리 |\n"
"| 2 | 빼는 필드 목록 | 초안 계약에서 유도: B34(`draft_b34.final.spec.md` 계약 7) 없음, b26pre 없음, backfill(`draft_b26_backfill_audit.spec.md` 계약 1·2) 값은 `pipeline_result`까지만 -- 실측 F1v82로 instance.json·report 0 확인 -- 없음, B26-1(`draft_b26_1.spec.md` 계약 2·8) E-LIB `meta[\"rails\"]` 하나. E-INST 빼는 키 없음 |\n"
"| 3 | 계산 가능성 | E-INST: 기존 `e_inst_p3.py` 출력(`field_sha256`·raw)으로 충분. E-LIB: `e_lib.py`는 해시만 내므로 확장 `e_lib_p3.py`(meta 키 빼기 인자) -- F1 전 트리(`a796468`)에서 인자 없음·`rails` 모두 `e_lib.py`와 같은 `hash` `1d2e3bf6…`(F2v82) |\n"
"| 4 | 거부 확인 | 판정 python을 design에서 그대로 뽑아(sha256 `37fecfea…`) 시제품에 실행: 계약 모양 p1 PASS, nets 틀림 p2 FAIL(9줄), meta 키 하나 더 p3 FAIL, 동등 고장 INVALID(F3v82). 원래 `e_lib.py`는 p1에서 해시가 달라 raw 비교 불성립을 재현 |\n"
"| 5 | 문서 개정 | `p3_doc_amendments.md` 머리 `diff_path` 문장에 `e_lib_p3.py`, §7 동등 확인 판 문장(B0 → P2D), 새 §8(`e_lib_p3.py` sha256) |\n\n"
"## 대상 판 해시(v8.2, sha256 앞 16자리 -- 승인 질문 끝 목록과 같음)\n\n"
"* design `draft_phase3_design_v8.md` `%s`(v8.1 `7da84c9a0237b604`), 승인 질문 `phase3_approval_question.md` `%s`(v8.1 `dcb20e72f4e94885`), 문서 개정 `p3_doc_amendments.md` `%s`(v8.1 `c775320e6c2b7e1a`).\n"
"* 새 파일: `p3_scripts/e_lib_p3_proposed/e_lib_p3.py` `%s`. 바뀌지 않음: G1 `3a99df21414d6e99`, T0 `35f7e3e7850a2847`, D0a `1f9592d491303132`, `e_inst_p3.py` `7d26134ad00ec504`.\n"
"* 도구: `p3_scripts/p3v82_patch.py`(design 본문 교체, '현재' 문자열 1회 단언), `p3v82_patch_question.py`(승인 질문·문서 개정), `p3v82_append.py`(부록 A 행 삽입, 부록 J·이 절 바이너리 append -- 앞 바이트 불변 단언), "
"`p3v82_e5_judge.py`(§10 E5 판정 python 원본), `p3v82_relaxed_reach.py`, `p3v82_judge_scenarios.sh` → `p3v82_judge_scenarios.out.txt`, 실행 스크립트·요약 `p3v82_out/`.\n")
qt = open(Q, encoding="utf-8", newline="").read()
qa = "## 대상 판 해시(v8.1 작성 완료 시점"
assert qt.count(qa) == 1
qt = qt[:qt.index(qa)] + ("## 대상 판 해시(v8.2 작성 완료 시점, sha256 앞 16자리 -- 질문 때 다시 계산해 승인 기록에 적는다. v8.2에서 바뀐 것은 design·문서 개정·새 `e_lib_p3.py`, 나머지는 v8.1과 같다)\n\n"
    "* `draft_phase3_design_v8.md` `%s`(v8.1: `7da84c9a0237b604`)\n"
    "* `draft_p3_g1.spec.md` `%s`\n* `draft_p3_t0.spec.md` `%s`\n* `draft_p3_d0a.spec.md` `%s`\n"
    "* `p3_doc_amendments.md` `%s`(v8.1: `c775320e6c2b7e1a`)\n"
    "* `p3_scripts/e_inst_p3_proposed/e_inst_p3.py` `%s`\n"
    "* `p3_scripts/e_lib_p3_proposed/e_lib_p3.py` `%s`(v8.2 새 파일)\n") % (
    sha(DES), sha(os.path.join(base, "draft_p3_g1.spec.md")), sha(os.path.join(base, "draft_p3_t0.spec.md")), sha(os.path.join(base, "draft_p3_d0a.spec.md")),
    sha(os.path.join(base, "p3_doc_amendments.md")), sha(os.path.join(base, "p3_scripts", "e_inst_p3_proposed", "e_inst_p3.py")),
    sha(os.path.join(base, "p3_scripts", "e_lib_p3_proposed", "e_lib_p3.py")))
open(Q, "w", encoding="utf-8", newline="").write(qt)
return_vals = (sha(DES), sha(Q), sha(os.path.join(base, "p3_doc_amendments.md")), sha(os.path.join(base, "p3_scripts", "e_lib_p3_proposed", "e_lib_p3.py")))
t = open(LOG, "rb").read(); h0 = hashlib.sha256(t).hexdigest()
open(LOG, "ab").write((logsec % return_vals).encode("utf-8"))
t2 = open(LOG, "rb").read(); assert hashlib.sha256(t2[:len(t)]).hexdigest() == h0
print("ok", return_vals)
