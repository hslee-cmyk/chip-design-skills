# 5차 독립 검토 -- Phase 3 `30-module-split` 초안 v7 (UD-0 승인 요청 전)

검토자: 독립 검토 agent(초안 작성자·이전 검토자 아님). 저장소 읽기 전용, 상태 변경 git 없음.
측정: `C:/g105/repo`(`git clone --no-hardlinks`, `a796468`)와 그 안의 합성 브랜치 `syn`·`syn2`(스크래치 전용). 끝난 뒤 `C:/g105`를 지웠다. Python `C:/Python314/python.exe -B`.

검토 대상 판(sha256 앞 16자리): `draft_phase3_design_v7.md` `40f7447b1c500c1a`(**17:29 판** -- 검토 중에 16:45 판에서 §2.3 M10 생존 표·D-25 정정이 더해졌다. §10 bash 블록 E3·E3b·`import_any`는 두 판이 같다(추출 후 `diff` 동일)),
G1 `b886de51…`, T0 `0f2ca719…`, D0a `c2271dce…`, `p3_doc_amendments.md` `5bbfffbf…`, `phase3_approval_question.md` `7dd1f9fe…`(16:39), `phase3_revision_log.md` `aa747991…`('초안 v6 → v7' 절 있음).

**기준 커밋**: 초안은 `a796468`에서 쟀다. 지금 gate `master` = **`0f23786`**(이동함). `git diff --stat a796468 0f23786` = `.ai/approvals/20261001-p10b-v3-equiv.md`, `.ai/specs/20260930-df23-registry-record.spec.md` 2파일뿐 -- 엔진·`tools/`·계획서·레지스트리 무변경이라 Phase 3 사실 문장에 영향 없다(m6).

## 판정

**고친 뒤 승인 요청 가능(fixable then ask).** 막는 것 2건(둘 다 DoD 판정 명령이라 승인 뒤에 고치면 기준 변경 -- 작다), 고칠 것 6건(그중 승인 질문 문장 3건).

* **B1**: Phase 3 DoD(E4·E5)와 T0 oracle이 `PT` = `--gmid-phase=1`로 돈다. Phase 2에서 승인 `20260930-phase2-e4-phase`로 고친 결함의 재발이다.
* **B2**: E3b의 `pre_existing` 면제가 star import·동적 이름·파싱 오류 표지까지 면제한다. 합성 커밋에서 깨진 추적 파일 2개가 있는데 `E3b PASS`가 나왔다(fail-open).

4차 검토 N1·S1~S5·m1~m6은 문서에 모두 반영됐다. 재측정한 것과 믿고 넘긴 것은 §1에 나눠 적었다.

---

## 1. 4차 검토 항목 재확인

| # | 확인 방법(직접 실행) | 결과 |
|---|---|---|
| N1 E3b | §10의 `E3B_AST`를 문서에서 `awk`로 잘라 실행. (i) `B0 = HEAD = a796468` (ii) 합성 `syn`: SD에서 `find_structural_symmetry_candidates` def를 새 파일로 옮기고 `structural_symmetry_probe.py:10`을 새 모듈로 바꿈 (iii) `syn2`: (ii)에 함수 안 `from stick_diagram import find_structural_symmetry_candidates as g` 파일 추가 | (i) `LIVE moved_out=0 … pre_existing=1` + `INVALID`(거부 확인 동작). (ii) `LIVE moved_out=1 base_files_reading_moved_out=1` + `PASS`(수용). (iii) `E3b FAIL workspaces/zz/infunc.py:2 find_structural_symmetry_candidates`(함수 안 import도 잡는다). **해결. 단 B2** |
| S1 E3 fail-closed | `E3_AST`를 잘라 `a796468`에서 실행 | `stmt` 69줄·`call` 9줄, 제외 집합 안 1(`probe_stage_partition.py`), 밖 66파일. 문서 수치와 같다. 비ASCII 경로 경우는 작성자 자체 시험(`p3v7_sec10_selftest.out.txt`)을 믿었다. 코드상 `-z`·`core.quotepath=off`·`ERROR`+종료 코드 3·`PIPESTATUS` 확인 -- **해결** |
| S2 IMPORT-ANY | `import_any`를 잘라 실행 | 정상 `GC`: `IMPORT-ANY tried=5 expected=5 failed=0` rc 0. 없는 `GC`: `IMPORT-ANY INVALID: 모듈 목록 계산 실패` rc 2. **해결**(환경 주의 m3) |
| S3 M10 생존 | 17:29 판 §2.3 표, `p3v7_m10_summarize.py`·`p3v7_m10_summary.json` 대조, `run()` 422~529행 읽기 | 표 수치 = summary(`survive_T1` 50, `T3` 24 등). `run()`의 `print(` 21개, `if circuit_key not in SPECS: raise`는 유효 키 test로는 지나가지 않는다 -- 생존 모양이 코드와 맞다. 71개 변이는 다시 돌리지 않았다(약 1시간). (v) "D-25는 새 test 회로만, E-INST 집합은 20 §3 그대로"도 더해졌다. **해결. 단 S4**(D-25 본문 규칙이 측정과 어긋남) |
| S4 엔진 card 동결 | §6.4·§8.1·§9.1·D-27, 계획 769·929·936·1001행 원문 | 계획은 B26-1~B26-4를 "Phase 3 착수 전에 해도 된다"고 적는다(허용이지 의무가 아님). 기본 F2 뒤는 원칙 기본값으로 성립한다. **해결. 단 S6**(동결 범위) |
| S5 D-22 전제 | D0a 계약 2 `import_time_high` 정의, 합성 단계 5개 | s = split∩N3.10 최소 번호(지금 SD 7), σ(u) > s 단위가 import 시점에 출처 s ≤ σ(w) < σ(u)를 읽으면 발견. 데코레이터·기본값·(future 없을 때) 주석·클래스 몸체·모듈 문장을 덮는다. 회로 이름 없음(topology 무관). **해결** |
| m1~m6 | 각 문서 grep | m1 반영(그러나 master가 또 움직임 -- m6), m2 반영(그러나 승인 질문 문장은 과장 -- S2), m3·m4·m5·m6 반영 |

---

## 2. Blocking

### B1. Phase 3 DoD E4·E5와 T0 oracle이 `--gmid-phase=1`로 돈다

* design §10 머리: "`PT`는 `10-test-separation` §10 정의를 그대로 쓴다". 그 정의(10 design 525행) = `… pytest … <iso>/…/tests --gmid-phase=1`.
  E4 `PT "$ISO/…/test_p3_registry_dest.py"`, E5 "`PT` 전체", T0 spec 99행 "base 트리 전체 `PT`(`10-test-separation` §10)"가 모두 이것을 쓴다.
* 실측(`a796468` `tests/conftest.py:103-126`): 표식 Phase가 현재 Phase보다 뒤인 케이스는 `xfail(strict=False)`로 바뀐다. `--gmid-dod`가 없으면 현재 Phase 케이스도 `--gmid-strict` 목록에 없으면 xfail이다.
  그래서 `--gmid-phase=1`로 돌리면 phase 2·3 표식 케이스가 실패해도 PASS로 지나간다. 지금 표식 분포는 1:6, 4:2, 6a:4, 6b:4, 6c:7(`git grep gmid_ic(`)이라 당장 차이는 0이다. 하지만 Phase 3 card가 phase 3 표식을 더하면 DoD가 그것을 보지 않는다.
* 선례: 같은 결함을 Phase 2에서 승인 `20260930-phase2-e4-phase`(17행: "--gmid-phase=1이 박혀 있지만 … --gmid-phase=2로 읽고 --gmid-dod 실행을 하나 더하는 것이 기본안")로 고쳤다. card V1은 게이트가 card phase를 강제한다(`merge_gate.py:1008-1010`). 그런데 DoD 명령은 게이트를 거치지 않는다.
* 고칠 것: §10 머리에 `PT3` = `PT`에서 `--gmid-phase=1`만 `--gmid-phase=3`으로 바꾼 것을 정의한다. E4와 E5는 `PT3` 전체 + `PT3 --gmid-dod` 전체(둘 다 실패 0)로 둔다. T0 oracle의 `PT`는 card V1과 같은 `--gmid-phase=3`으로 둔다. 기준을 더하는 쪽이다.

### B2. E3b `pre_existing`이 star·동적 이름·파싱 오류 표지까지 면제한다(fail-open)

* 코드(§10 `E3B_AST`): `pre = {(p, n) for p, s in br.items() for _, n in s if n not in bd | bi | IMPL}`.
  표지 이름 `"*"`(star import), `"<동적 이름>"`, `"<PARSE-ERROR>"`는 base SD에서 절대 해석되지 않는다. 그래서 base에 있으면 언제나 `pre`에 들어가 판정에서 빠진다.
  design §3 SD-NAMES·D-24·D-26의 "star import·동적 이름·파싱 오류는 … FAIL"과 어긋난다.
* 실증(`C:/g105`, 합성 커밋):
  * B0' = `a796468` + `workspaces/zz/star_reader.py`(`from stick_diagram import *` 뒤 `find_structural_symmetry_candidates` 사용) + `workspaces/zz/dyn_reader.py`(`getattr(sd, name)`)
  * H = B0' + SD에서 그 def를 새 파일로 옮김(재수출 없음) + `structural_symmetry_probe.py`만 새 모듈로 갱신

  결과는 `E3b LIVE moved_out=1 base_files_reading_moved_out=1 pre_existing=3` / **`E3b PASS`** / rc 0이었다.
  같은 트리에서 두 파일을 실제로 실행하면 `NameError: name 'find_structural_symmetry_candidates' is not defined`, `AttributeError: module 'stick_diagram' has no attribute …`가 난다.
* 지금 저장소에서 이 모양은 0건이다(`from (stick_diagram|sizing_recipe|…) import \*` 0, `getattr(sd, 변수)` 0 -- 작성자 F5v7과 일치). 그러나 B0은 M1 판정 기록의 base라서, 그 사이 card가 이런 파일을 더하면 영구 면제된다.
* 고칠 것(한 줄): `pre` 계산에서 `n.startswith("<")`와 `n == "*"`를 뺀다. 표지 이름은 base·head 어디서든 FAIL이다. 표지별 합성 단계(base에 있던 star reader → FAIL)를 F2v7 자체 시험에 더한다.

---

## 3. Should-fix

| # | 위치 | 발견(근거) | 고칠 것 |
|---|---|---|---|
| S1 | §10 E5 "E-LIB·E-INST 재측정이 Phase 2 DoD와 같은 해시", §3 E-LIB/E-INST 행 | **F1부터 Phase 2의 E-INST 측정 스크립트를 쓸 수 없는데 대체 명령이 없다.** Phase 2 DoD 정본 E-INST 스크립트 `.ai/verification/20260930-df36-instance-relpath/scripts/e_inst_df36.py` 33~35행은 `for m in ("sizing_recipe", "stick_diagram", "design_report"): … sys.modules[m].__file__`이다. 지금 하네스는 40·42·43행에서 셋을 import한다. F1이 하네스 import를 MOD로 바꾸면 SR·DR이 `sys.modules`에 없어 `KeyError`가 난다. 이 스크립트는 D-9 제외 집합이라 고치지 않는다. E-LIB `e_lib.py`는 `sd.load_topology`·`sd.run_topology_pipeline`만 읽는다. `run_topology_pipeline`은 레지스트리 목적지가 `stick_diagram`(MOD7)이고 `load_topology`를 읽으므로(SD AST 실측) SD에 import가 남아 살아남을 것으로 본다(D0b 배정에 달림) | E5와 F1·F2 card의 E-INST 명령을 정한다. 같은 해시 정의(`without_topology_ref_sha256`, design 20 E4)를 Phase 2 DoD 트리와 Phase 3 트리 양쪽에서 계산하는 Phase 3 auditor 스크립트 사본을 두 판에 쓴다(design 20 E4 '같은 사본' 절차 선례). E-LIB도 F2 뒤 `sd.` 경유가 풀리는지 E3b 결과와 묶어 한 줄로 적는다 |
| S2 | 승인 질문 UD-0 (a), design §9.2 UD-0·D-9 | **"판정 기록 스크립트 8개가 … 읽는 이름"이 깨진다는 문장은 재지 않은 사실이다.** 8파일이 SD에서 읽는 이름(E3b `file_reads`로 실측): 6개 `e_lib.py`는 `__file__`·`load_topology`·`run_topology_pipeline`뿐이다. 레지스트리상 `run_topology_pipeline`은 SD에 남고 `load_topology`를 읽으므로 SD import가 남는다. 깨질 후보는 `df36…/e_lib_inst.py`(`save_instance_json` → MOD9, SD 사용처 0)와 `p9-kcl-edges/scripts/diff_dup.py`(`_kcl_and_matching_edges` → MOD3, `_import_analog_grammar` → MOD2) 2개다. 질문은 사실을 그대로 인용해야 한다 | "판정 기록 스크립트 8개 중 F2 뒤 SD에 남지 않는 이름을 읽는 것(근사 배정 기준 2개 -- 정확한 수는 D0b 뒤)"로 고친다. design D-9의 "깨질 수 있다"는 맞다 |
| S3 | §6.4·§11-11, 승인 질문 | **사용자 승인 기록의 범위가 바뀌는데 사용자에게 보이지 않는다.** `.ai/approvals/20260930-b26-before-phase3.md` 27·28행 ③: "Phase 2 진행 중에 병합하는 것(card `phase: 2`)". v7 확정 순서는 둘을 Phase 2 DoD **뒤**에 둔다. 확정 순서의 근거로 든 사용자 지시 원문("P10b 끝나면 push하고 Phase 2 완료 판정 진행해")은 P10b → Phase 2 DoD만 정한다. 34 → 35 → B34 → B26-1 → B33은 오케스트레이터 배열이다(design 머리·§8.1이 "오케스트레이터 결정이자 사용자 지시"라고 묶어 적었다). design은 이것을 인계(§11-11)로만 둔다 | 승인 기록 문장 변경은 사용자 몫이다. 이번 승인 묶음에 한 줄을 넣거나(예: "A2 ③의 'Phase 2 진행 중'을 'Phase 2 DoD 뒤·Phase 3 M card 전'으로 정정, card `phase` 값은 계획 1001행대로") 별도 정정 승인으로 받는다. design 머리의 '사용자 지시' 귀속은 원문 범위로 좁힌다 |
| S4 | D-25(17:29 판 674행), §2.3 '회로' 글머리 | **규칙 문장이 새 측정과 어긋난다.** D-25 = "네 library 회로 중 E-INST 한 판이 가장 짧은 것". §2.3에는 아직 "`two_stage_ota`·`nmcnr_amplifier`는 기록 없음 → 네 회로를 한 판씩 재고 가장 짧은 것을 고른다"가 남아 있다. 그런데 v7 측정(`p3v7_m10_trace.{two_stage_ota,nmcnr_amplifier}.json`)에서 두 회로는 `inst_sha: null`, `fail_in_stdout: true`, 31.4·33.9초이고, 같은 경합 조건의 `folded_cascode` 기준 실행(56.6초)보다 짧다. 규칙을 문언대로 적용하면 instance.json을 만들지 않는 회로가 뽑힌다. design 20 §3 E-INST(57행)도 "파일럿·`folded_cascode`"뿐이다 | D-25와 §2.3을 "instance.json을 만드는 회로(E-INST 회로 집합) 중 가장 짧은 것 = `folded_cascode`"로 고친다. 실패 경로 회로는 §2.3 (ii)의 보조 회로로만 둔다. 옛 '기록 없음' 문장을 지운다 |
| S5 | 승인 질문 UD-1, design §7.2·§9.2 UD-1 | **경로가 틀렸다.** 질문은 "`workspaces/smoke_run_harness_session18_save.py`"라고 적는다. 실제 경로는 `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py`다(`git status --porcelain --untracked-files=all -- '*.py'`: 추적 안 된 `.py`는 이것과 `.claude/hooks/*` 4개뿐). 9·10행 import 내용은 맞다 | 전체 경로로 고친다 |
| S6 | D-27·§9.1, §10 `GC` 주석 | **동결 범위가 엔진 파일뿐이다.** §10 `GC` 주석은 "M card는 tools/** 변경 0(D-16)이라 마지막 병합본의 tools/gates가 그 판이다"라고 적는다. 이 문장은 M1~F2 사이에 **다른** card가 `tools/gates`를 바꾸지 않을 때만 참이다. B35의 착수 조건인 게이트 변경 card B36은 순서에 없다(§8.1). 레지스트리 '이관 목적지' 열을 바꾸는 문서 card도 D0b 계약 test(`reg_mismatch`)를 이후 모든 card V1에서 깨뜨린다. 크게 깨지므로 약화는 아니다 | D-27에 `tools/gates/**`·`tools/migrate/**`와 레지스트리 목적지 열을 더한다. 또는 E2가 05 §4.4의 '판정 시점 gate master 판'으로 다시 돈다는 것을 의도로 적고 주석을 사실에 맞춘다. 참고: E6 MOVE-TOTAL(base = M1 base)은 M1~F2 사이의 엔진 변경을 DoD에서 잡는다. D-27의 사후 강제 수단으로 한 줄 적어 둘 만하다(D0b~M1 구간은 덮지 않는다) |

---

## 4. Minor

| # | 내용 |
|---|---|
| m1 | v7 design이 검토 요청 뒤 16:45 → 17:29에 바뀌었다(§2.3 표, D-25, 부록 A F6v7). 16:45 판의 부록 G 4행이 가리키던 `p3v7_m10_mutants.folded_cascode.json`·summary는 17:27에야 생겼다. 승인 요청 때 기준 판의 해시를 승인 기록에 적는다 |
| m2 | E3b가 SD 최상위 바인딩을 `symtable`로 따로 정의한다(§2.4 '정의 하나'는 `reachability.SourceIndex`). DoD 시점에는 G1이 있으므로 그것을 쓸 수 있다. symtable은 `try/except ImportError`·`if TYPE_CHECKING:` 안의 바인딩도 '있음'으로 센다. 한계 문장으로 남기거나 SourceIndex로 바꾼다 |
| m3 | 이 환경에서 bash를 한 번 더 띄우면 `APPDATA`가 빠진다(`bash -c 'echo $APPDATA'` 빈 값). 그러면 사용자 site의 numpy를 못 찾아 `import_any`가 `IMPORT-ANY FAIL: sizing_recipe`를 낸다(실측. fail-closed지만 거짓 FAIL). §10 공통 블록에 `export APPDATA=…`를 둔다(pytest 메모와 같음) |
| m4 | 승인 질문 '뒤에 올 승인'에 "M10 V3 생존이 남으면 면제 승인"(§2.3 "면제는 사용자 승인")을 한 줄 더한다 |
| m5 | D-19 (가)의 "다음 card B37a의 같은 성격 접근자도 같은 곳에 둡니다"에서 B37a는 미승인 card다. "둘 예정"으로 고친다 |
| m6 | 기준 문장: gate `master`가 `0f23786`으로 움직였다(docs 2파일, Phase 3 영향 0). 승인 질문 머리의 "`a796468`에서 다시 확인"에 "`0f23786`까지 엔진·tools·계획 무변경"을 더한다 |
| m7 | D-24 한계 목록에 '경로로 로드한 엔진 모듈'(`importlib.util.spec_from_file_location`·`runpy.run_path`)을 더한다. 실측 `a796468`: 엔진 4파일을 이 방식으로 로드하는 추적 파일 0(나오는 것은 `run_harness.py`·review 스크립트·`w_sites.py`뿐) |

---

## 5. 중점 점검 요약

* **약화 구멍**: B1(DoD phase 1, 선례 있음), B2(E3b 표지 면제, 실증). E3·IMPORT-ANY는 고장 입력에서 FAIL/INVALID로 떨어진다(재실행 확인).
* **측정 없이 적은 사실**: S2(8개 깨짐), S5(경로), m1(16:45 판의 F6v7 인용). 17:29 판의 M10 수치는 summary와 맞는다.
* **D-27 순서**: 엔진 동결 구간(D0b~F2)과 B26-2~4·B35 기본 위치는 계획 허용 문구와 맞다. 범위 보강은 S6. E6가 사후 강제 수단이다.
* **D-22 import 순환 규칙**: `import_time_high`가 전제를 단언하고(D0a 계약 2·합성 단계 5개), 위반 처리(D0b 정지·배정 변경·D-11)도 정해져 있다. 새 결함 없음.
* **M10 인벤토리**: `a796468`에서 다시 쟀다. `run` 인벤토리 60(`test_extract_selftest` 24, `test_selftest_sizing_recipe` 22, …)으로 문서와 같다. 생존 표·(i)~(v)로 S3는 닫혔다. 남은 것은 D-25 문장(S4)이다.
* **승인 질문**: 진짜 사용자 결정은 UD-0·D-19·UD-5·UD-1 넷이고, 숨은 회로 해석 결정은 없다. 고칠 것은 S2·S5·m4·m5·m6, 그리고 S3(A2 ③ 정정을 같은 묶음에 넣을지)다.

## 6. 정리

B1·B2(§10 블록 몇 줄, T0 한 줄)와 S2·S4·S5(문장)를 고치면 승인 질문을 올릴 수 있다. S1(F1 뒤 E-INST 명령)과 S3(A2 ③ 정정 경로)도 같은 개정에서 정하기를 권한다. S1은 E5 판정을 실행할 수 없게 만들고, S3은 사용자 승인 문장에 닿기 때문이다. S6·minor는 문장 보강이다.
재현: `C:/g105`(삭제함). 브랜치 `syn`(B0' = star·dyn reader, H = def 이동 + probe 갱신), `syn2`(+ 함수 안 import reader). §10 블록은 design 파일에서 `awk`로 잘라 그대로 실행했다.
