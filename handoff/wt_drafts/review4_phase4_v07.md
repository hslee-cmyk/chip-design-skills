# 4차 독립 검토: `draft_phase4_design.md` v0.7 (Phase 4 `40-defect-fixes`) -- 승인 전 검토

검토자: 독립 검토(작성자 아님, 1~3차 검토자 아님). 대상: `_drafts/draft_phase4_design.md`(v0.7, mtime 2026-10-01 16:32:08), `_drafts/phase4_revision_log.md`(v0.6 → v0.7 절), `_drafts/p4_scripts/p4v07_dag.py`.
입력: `review_phase4_design.md`, `review2_phase4_v03.md`, `review3_phase4_v06.md`, `user_decisions.md`(16:10), `draft_b26pre.spec.md`, `draft_phase3_design_v6.md`·`draft_phase3_design_v7.md`(16:34, 작성 중), `phase3_approval_question.md`.
측정: gate `master` HEAD = **`a796468`**(`git rev-parse --short HEAD`, 시작·끝 같음). 저장소·worktree 쓰기 0, git 상태 변경 0(`rev-parse`·`show`·`archive`·`status`만; `status --short`는 시작 스냅숏과 같음). 스크래치 `C:/g100`만 사용(HEAD `git archive` 복제본 `iso`, DAG 사본·추가 시나리오 `extra.py`, 결과 파일) -- 끝에 삭제.

---

## 0. 판정

**수정 후 승인 질문 가능 -- blocking 1, should-fix 9, minor 6.**

* 3차 검토 지적(B1, S1~S7, m1~m7)은 전부 반영됐고 DAG 재실행 결과가 기록과 한 줄도 다르지 않다(§1).
* blocking은 DoD 하나다: **E3(IC11 rail2)의 명령이 `--gmid-dod` 없이 rail2를 비엄격 xfail로 돌려 판정 기준을 잴 수 없다**(HEAD 복제본 실측, §2 B1). 같은 종류로 E4의 `-k "legacy"`는 HEAD에서 이미 무관한 test 1개를 골라 MG1 test 없이도 PASS가 된다(S1).
* v0.7이 새로 연 margin 문제(§9-22)는 승인 전에 기본안으로 닫아야 한다. 계획 749행 "`null` ≠ 빠뜨림"과 어긋나는 처리를 '오케스트레이터 정정 요청'으로 남겨 두면 #23 계약과 E2 비교 단위가 승인 시점에 정해지지 않는다. 그리고 문서가 인용한 IC9는 계획 원문(827행)과 뜻이 다르다(S2).
* v0.7의 S7 처리(#53 (i) '노드 고정 값 출처 하나 -- `supplies_v`와 한 스키마일 수 있음')가 **갈래 안에 잠재 순환**을 만든다(R3·R4 실측, S3).
* Phase 3 초안이 v0.7 작성 **뒤** v7로 바뀌었다(`cmp` 다름, D-27 엔진 card 동결). v0.7 머리의 "v7 = v6 바이트 동일"은 지금 거짓이다(S4).
* 새 상수: 엔진 규칙에는 없다. 다만 #53·#54 oracle의 'conflicts 0'이 HEAD 기본 인자 `tol=1e-6`에 기대고, #23이 그 기본값 제거를 범위에 적지 않았다(S6).
* topology 무관: #55가 엔진 몫을 맡는 갈래의 oracle에 합성 topology·무동작이 빠졌다(S5). 그 밖의 엔진 규칙은 이름 없는 규칙으로 적혀 있다(§5).

---

## 1. 3차 검토 지적의 처리 확인 (검사 1)

DAG: `p4v07_dag.py` 사본을 `C:/g100`에서 다시 실행(출력은 사본 쪽 `out/`). S0~S8·C1~C4 13줄이 `_drafts/p4_scripts/out/p4v07_dag.out.txt` 끝 13줄과 `diff` 0(`SAME_AS_RECORDED`).

| 3차 | 지적 | v0.7 | 판정 |
|---|---|---|---|
| B1 | 확정 순서와 반대 읽기 | §3.2 #1 (0)·B26pre 행·#45 행, §3.3 도식, §9-19 결정됨, DAG `P2DoD ← P10b`만 + 하드 사슬 | 해소. S0 비순환, C1(옛 읽기 (가)) 순환 재현 |
| B1-4·5 | Phase 3 묶음 문구, E5 기준 해시 | §9-23·§9-24 | 해소. C2 순환 재현. `user_decisions.md` 원문 자체가 "실제 순서는 Phase 3 design"이라 적어 §9-23은 사실상 닫혀 있다(m6) |
| S1 | #43 margin 분모 | margin `null`, P-23 정정, §11.2 | 해소. 단 새 항목 §9-22가 열려 있다 → **S2** |
| S2 | #10·#25 X 핸들러 반대 동작 | P-34 한 규칙, #10·#25 oracle 갱신, §10.7 | 해소. 혼합 사유·실행 수준 보존이 남음 → **S9** |
| S3 | #54 엔진 갈래 권고 간선 | §3.3·#54 선행 | 해소. S5 비순환·C3 순환 재현. 추가로 R6(엔진 갈래 + #21이 #54를 하드로 기다림) 비순환 확인 |
| S4 | UD-17e (ii)가 #22 뒤 | #55 엔진 몫, 권고 UD-17e → #22 | 해소(S6·S7 비순환). oracle 공백 → **S5** |
| S5 | #54 포화 기준 상수 | 포화 = 기록 항목, F33 [미측정] | 해소 |
| S6 | 결정 목록 | 확정 순서 결정됨, B26pre U1·U2 | 해소. `draft_b26pre.spec.md` U1~U3 문구와 일치 |
| S7 | #53 엔진 몫 | §3.4 행, `#6 → #53`, 출처 하나 문장 | 반영. 그 문장이 새 잠재 순환을 만든다 → **S3** |
| m1~m7 | 낡은 문장 등 | 반영 | 해소. 단 m1 (a)의 'v7 = v6' 근거가 무너짐 → **S4** |

---

## 2. blocking

### B1. E3 명령이 rail2 판정을 잴 수 없다 -- `--gmid-dod`(또는 `--gmid-strict=IC11:rail2`)가 빠졌다

**근거(실측, `C:/g100/iso` = HEAD `git archive` 복제본, `PT` = `10-test-separation` §10 형식에서 `--gmid-phase=4`)**
* HEAD의 `test_ic11.py` rail2 본문은 `pytest.fail()` 한 줄(F13)이다. 같은 파일을 세 방식으로 돌렸다.

| 옵션 | rail2 | 요약 |
|---|---|---|
| (없음) -- E3 명령 그대로 | **XFAIL**(reason "IC11 -- 담당 Phase 4 -- 만료: 4 DoD") | 3 xfailed |
| `--gmid-dod` | **FAILED** | 1 failed, 2 xfailed |
| `--gmid-strict=IC11:rail2` | **FAILED** | 1 failed, 2 xfailed |

* 곧 E3 명령 그대로면 망가진 rail2는 XFAIL, 맞는 rail2는 XPASS로 보인다. 통과 기준 "rail2 PASS(xfail 표식 없음)"은 이 명령으로 성립할 수 없다. `00-common` §9.3: "`--gmid-dod`: 그 Phase DoD 판정 실행 -- 표식 Phase가 현재 Phase인 케이스 전부"(엄격).
* 선례: 사용자 결정 A3(2026-10-01, "E4 PT를 `--gmid-phase=2`와 `--gmid-dod` 두 실행으로 고정"), design 10 §10 D6(`PT --gmid-dod -rA …/contracts`), design 20 E4(`PT2` 전체와 `PT2 --gmid-dod` 전체).

**고칠 것**
* E3 명령 = `PT --gmid-dod -rA <iso>/…/tests/contracts/test_ic11.py`.
* E11 = `PT` 전체와 `PT --gmid-dod` 전체 **두 실행**(A3과 같은 형식). 통과 기준에 "두 실행 모두 실패 0".
* 정보: `PT`는 이미 `<iso>/…/tests` 전체를 경로로 갖는다. 파일 경로를 더해도 전체 suite가 돈다(design 10 D4와 같은 관례). 실행 범위가 전체라는 것을 E3 칸에 한 줄로 적는다(m4).

---

## 3. should-fix

### S1. E4·E5의 `-k` 선택이 엉뚱한 test를 잡거나 0개를 잡는다

* 실측(HEAD 복제본, `--collect-only`): `-k legacy` → **1/886**: `contracts/test_ts3_no_print_verdicts.py::test_target_set_includes_legacy_scripts`(MG1과 무관, HEAD에서 PASS). E4 명령은 MG1 옛 키 test가 하나도 없어도 PASS다. `-k lut_axis` → 0개(지금은 수집 없음 exit 5. 나중에 이름이 겹치는 test가 생기면 같은 문제).
* design 20 E1이 같은 함정을 이미 겪었다("`-k "dup_"`는 P4의 `test_probe_dup_scan.py`까지 잡는다", 기준에 "수집 1개 이상").
* **고칠 것**: E4·E5 명령을 test node id 목록으로 바꾼다(#20·#21·#25 interface card가 id를 정하고, 이 표는 "그 card의 id 목록"을 가리킨다). 통과 기준에 "수집 수 = 목록 수, 전부 PASS". E10도 같은 형식(파일 이름이 초안이므로 card가 확정).

### S2. §9-22 margin을 승인 전에 기본안으로 닫는다. IC9 인용을 고친다

**근거**
* 계획 749행: "분모가 0이거나 정의되지 않으면 margin은 `null`로 기록하고 비교·정렬에 쓰지 않는다(**빠뜨린 것과 구분된다**)". #23 conflicts(봉인 항목 1, 분모 tol_V)는 분모가 **정의된다**. v0.7 기본안("위반 크기·분모 기록 + margin `null`")은 그 레코드에서 `null`을 '아직 계산 안 함'의 뜻으로 쓴다. 계획이 구분하라고 한 두 뜻을 섞는 것이다.
* 계획 IC9(827행) 원문: "| IC9 | 중복 복붙 | 레지스트리 정본 하나, 타입 setter만 | `test_no_raw_duplicated_writes` … | 6b |". IC9는 margin 전용 규칙이 아니고 6b에 활성화된다. "margin을 계산하는 곳은 이 함수 하나"는 `00-common` §7.2가 IC9를 근거로 든 문장이다. "첫 소비자는 실패 캐시 정렬(N3.5, Phase 5)이라 그 변경 단위에서 만든다(WP-01)". 그래서 v0.7 §10.6-0의 "IC9 때문에 Phase 4 card는 margin 수를 따로 계산하지 않는다"는 근거를 잘못 짚었다. 맞는 근거는 "근거 하나(두 번째 margin 식 금지) + `00-common` §7.2의 CC-9 시점"이다.
* 영향: Phase 4의 모든 margin이 `null`이면 §10.6-0 실패 단위 판정(실패 클래스·margin·setup 양)과 E2의 margin 열은 Phase 4 안에서 아무것도 가르지 못한다. #21 '조건부' 실측(실패 단위 판정기가 S2·S3을 가르는가)은 margin 차원 없이 재야 한다. 지금 문서는 그것을 적지 않았다.
* 반대로 #43 `null`은 계획과 맞는다. 계획 396행: "'기둥 VDS 합 ≠ 레일 전압차'는 표현할 수 없다(**검사 대상이 아니다**) … 층 0의 기둥 KVL은 … 새 검사 항목이 아니다" -- 허용오차를 가진 봉인 항목이 아니므로 분모가 없다. §11.2 근거에 이 줄을 더하면 단단해진다(m6).

**고칠 것**(원칙 기본안으로 정하고 UD-0이 덮게 한다 -- 사용자 별도 질문 아님)
* **권고 기본안 = (나) CC-9를 #23으로 앞당긴다**: `normalized_margin`은 한 줄 함수(MOD2)이고, 첫 **생산자**(#23의 실패 레코드)가 부르면 배선된다(만들면 배선). 계획 749행 의미가 그대로 지켜지고(정의되면 수, 아니면 `null`), Phase 4의 실패 단위 판정과 E2가 margin 차원을 갖는다. 변경 = `00-common` §14 CC-9 행·§7.2 둘째 줄(WP-01 근거 '첫 소비자' → '첫 생산자')을 #23 card 커밋에서 고친다.
* 대안 (가)(계획 749행에 'CC-9 전에는 `null` + 위반 크기·분모 기록' 한 줄)을 택하면 계획 정정 커밋이 #23 병합 **전**이어야 한다(간선 `계획 정정 → #23`). 그리고 #21 조건부 실측에서 margin 차원을 빼고 잰다고 적는다.
* §10.6-0·§9-22·P-23의 IC9 문장을 위 근거로 바꾼다. 둘 중 하나를 문서에 확정하고 §9-22를 '결정됨(UD-0)'으로 옮긴다.

### S3. #53 (i) '출처 하나' 문장이 갈래 안 잠재 순환을 만든다

* v0.7 #53 (i): 고정 노드 전위 선언을 "`supplies_v`와 한 스키마로 둘지 … card가 정하되, 엔진이 노드 고정 값을 읽는 경로는 하나". 그리고 (i)에는 권고 `#53 → #23`이 유지된다.
* `supplies_v`는 #21이 만들고, 선언 레일을 그 전위로 고정하는 엔진 경로는 #22가 만든다. 둘 다 #23 뒤다(#21 ← #23, #22 ← #21·#23).
* 실측(`C:/g100/extra.py`, v0.7 그래프 + 권고 간선):
  * R3 (i) + `supplies_v` 같은 스키마(`#21 → #53`) + 권고 `#53 → #23` 유지: **순환**.
  * R4 (i) + 읽기 경로를 #22의 것으로 하나(`#22 → #53`) + 권고 유지: **순환**.
  * R5 R3에서 권고 `#53 → #23` 제거: 비순환.
* **고칠 것**: §3.3 갈래 문장과 §5.10 #53 선행에 "(i)에서 `supplies_v`와 한 스키마로 두거나 #22의 고정 경로를 쓰면 **하드 `#21`(또는 `#22`) → #53, 권고 #53 → #23은 없다**. 따로 두면(#53이 먼저 읽기 경로를 만들면) 권고는 유지하고, #22가 그 경로를 재사용한다는 계약을 #22에 적는다"를 #53 (ii)·#54 엔진 갈래와 같은 형태로 적는다. DAG 스크립트에 R3~R5를 더한다.

### S4. Phase 3 v7과 다시 맞춘다 -- 'v7 = v6' 근거가 무너졌고 D-27이 새로 생겼다

* 실측: `cmp draft_phase3_design_v6.md draft_phase3_design_v7.md` → **다름**(byte 77, line 3). v7 mtime 16:34:38(이 검토 중에도 159,444 → 160,900 바이트로 바뀜) > v0.7 16:32:08. v0.7 머리 35행의 "`draft_phase3_design_v7.md`는 v6과 바이트 동일, `cmp`"와 부록 A F3는 지금 거짓이다.
* v7이 더한 것 중 이 문서에 닿는 것:
  * **D-27 엔진 card 동결**: "D0b 병합 → F2 병합까지 … 엔진 파일(`A/*.py`, `workspaces/run_harness.py`)을 바꾸는 Phase 3 밖 card를 병합하지 않는다".
  * "B26-2~B26-4·B35의 자리 … 위 확정 순서에는 없으므로 **기본값 = F2 뒤** … Phase 3 전에 넣으려면 **D0b 전**에 병합해야 하고, 그러면 §9.1 재측정 (1)에 그 card가 들어간다". B35는 F2 뒤.
  * D-26(E3b, `stick_diagram` 임시 재수출 삭제 뒤 이름 해석).
* v0.7과 어긋나는 곳: §3.3 "d4-delete-unwired(#2)·#3·#4 -- 확정 순서 밖(**Phase 3 전 아무 때나**)", §3.2 "B26-2·B26-3도 UD-1이 일찍 결정되면 Phase 3 전에 할 수 있다", #17·#18 `P3?` '조건부 pre'. #2~#4는 엔진 정의를 지우거나 옮기는 card라 D-27 구간에 병합할 수 없다.
* 순서 영향 실측: R1(`#2·#3·#4 → D0b`)·R2(#2를 Phase 4로)·R8(`#17 → D0b`) 모두 비순환. 그래서 고칠 것은 문장과 조건뿐이다.
* **고칠 것**: 머리 35행·부록 A F3를 "v7(작성 중, mtime …) 기준 재확인"으로 바꾼다. #2~#4·#17·#18의 "Phase 3 전"을 "**D0b 전에만**(그때 Phase 3 §9.1 재측정 (1)에 포함), 아니면 F2 뒤 = Phase 4"로 고친다. §9-11 요청 문구도 v7 §9.1에 맞춘다. 승인 질문은 Phase 3 v7 확정본 기준으로 다시 확인한 뒤 올린다.

### S5. #55가 엔진 몫을 맡는 갈래의 oracle에 topology 무관 판정이 없다

* #55 oracle은 (d) 공동분석 확인표, (c) 해당 소자 θ* vsb = 0뿐이다. v0.7 S4 기본안에서 #55는 "데이터 + 엔진 card"(`bulk` 거부 해제 + `derive_vsb_from_nodes`의 선언 bulk 읽기, P3? = Y)가 될 수 있다. 그때 §4.1(합성 topology, 역방향, 무동작)이 빠진다. #22 (ii)에는 같은 몫의 계약(`bulk` 넷이 netlist 넷에 있음, 그 밖 거부)이 있다.
* **고칠 것**: #55 oracle에 "(엔진 몫을 맡을 때) (a) 합성 topology -- 선언 `bulk`가 source 넷인 소자와 아닌 소자(이름 무관)의 vsb, `bulk`가 netlist 밖이면 `SchemaRejectedError`, (c) `bulk`를 선언하지 않은 library 회로 무동작(CC-8 noop)"을 #22 (ii)와 같은 문장으로 넣는다.

### S6. 'conflicts 0' 판정이 HEAD 기본 인자 `tol=1e-6`에 기대고, #23이 그 기본값 제거를 적지 않았다

* 실측(HEAD SR): `def propagate_node_voltages(by_name, sized, vdd, rail_hi=_DEFAULT_RAIL_HI, rail_lo=_DEFAULT_RAIL_LO, tol: float = 1e-6, max_passes: int = 50)`(3727~3729행). 호출부 3831·3863·7294·7449는 `tol`을 넘기지 않는다. 그래서 지금의 `conflicts`는 1e-6 기준이다.
* #53·#54 oracle의 "conflicts 0"은 어느 tol 기준인지 적지 않았다. 권고 간선(데이터 갈래)대로 #23 **전**에 병합되면 판정 기준은 이 근거 없는 기본값이다. #23 대상 칸은 "conflicts → SEAL_VIOLATION + tol_V 함수"만 적고 `tol=1e-6` 기본 인자 제거를 적지 않았다(§4.2 '기본값 없는 인자' 위반이 남는다). `max_passes=50`도 근거 없는 상수다. 계획 N3.6은 반복 상한을 `K_max = ceil(log2(구간폭 / tol_V))`로 유도하고 "창 크기·연속 횟수 상수는 두지 않는다"고 적는데, 이것은 6b 몫이다.
* **고칠 것**: #23 대상에 "`tol` 기본 인자 제거, 호출부는 tol_V를 넘김"을 더한다(`rail_hi/lo` 기본 인자는 #17이 맡고, 같은 함수라 순차 병합). #53·#54 oracle은 "최대 충돌 차를 기록하고, #23 병합본이면 tol_V로, 그 전이면 HEAD 기준(1e-6 -- 더 엄격한 쪽, 기존 값이라 새 상수 아님)으로 판정하고 #23 병합 때 다시 잰다"로 적는다. `max_passes`는 §1.4 '다른 Phase'(6b 반복 상한)에 한 줄로 둔다.

### S7. #13(`fallback_events` 키)·#14(θ* 기록)가 E-INST 기대 해시를 바꾸는데 §7.4에 없다

* §10.1-2: 성공 실행은 `instance.json` **최상위 키** `fallback_events`. #14: "실행 산출물에 θ* 기록"(위치 미정). §10.5 정규화는 design 20 §3 E-INST 제외 규칙을 그대로 쓰므로, 새 최상위 키는 4회로 E-INST 해시와 Phase 3 D-25(M10 진입점 E-INST test, 기록상 folded) 기대 해시를 #13에서 바꾼다. §7.4·§3.1-5는 #23·#25·#53·#54·#55만 적는다.
* **고칠 것**: §7.4에 "#13(`fallback_events` 키 추가)·#14(θ* 기록이 `instance.json`에 들어가면)의 E-INST·D-25 기대 해시 변경 -- 기대 차이표 + DEC-40"을 더한다. #14의 기록 위치(`instance.json` 안/밖)를 대상 칸에 정한다. 두 card의 '관찰 가능한 계약'에 "바뀌는 것은 그 키뿐(나머지 정규화 해시 동일)"을 둔다.

### S8. 규칙 일부가 이 문서 밖(v0.2 사본·`_drafts` 자료)에만 있다

* #26 "U-27 도구 결함 **G1~G6(v0.2와 같다)**": 내용은 `draft_phase4_design.v02.md` 354행에만 있다(VS 값 기반 체크포인트 이름, 재사용 조건 = 필요 열 전체, CGS·CGB 추출, npz 메타 `w_ref_m`·PDK 커밋·ngspice 버전·스크립트 해시, VS 상한을 `supplies_v` 최대 차에서 인자로, 출력 경로 인자). 정식 경로로 커밋될 design이 `_drafts` 사본을 가리킬 수 없다. 같은 종류: §2 F8 "v0.2 표 그대로", §8.4 "v0.2와 같다"(사실 문장이라 영향은 작다).
* oracle (d) 출처: #53·#54·#55의 "(d) 공동분석 확인표([pack] §3·§5)", #23 "(d) B21 (c) 재현 입력 [prep]". `00-common` §9.3: "oracle (d): spec card '오라클 출처'에 사용자가 승인한 계획서 절과 그 판의 커밋 해시". `_drafts` 문서는 커밋 해시가 없다.
* **고칠 것**: G1~G6을 #26 칸에 그대로 옮긴다. #53~#55의 (d)는 "topology 수정 승인 기록(WP-07, §7.3)에 붙인 공동분석 확인표(커밋됨)"로, #23의 (d)는 "card '작성 전 실측'에서 커밋하는 재현 입력"으로 출처를 바꾼다.

### S9. P-34의 사유 보존이 한 단계 위(실행 수준)와 혼합 사유에서 정해지지 않았다

* F29의 증상은 **실행 수준**이다: "SLSQP 3회 전부 infeasible → `ValueError` … 어느 메시지에도 축 밖이 없다". P-34는 후보 집계 지점까지만 정한다. 그 `SealViolationError`는 `CANDIDATE_FAILURE_CLASSES`로 θ 후보 실패가 되고, 모든 시작점이 실패하면 `SearchFailedError`(exit 6)가 된다. 이 문서는 `SearchFailedError` 레코드가 하위 실패 클래스를 싣는다고 적지 않았다(grep: `SearchFailedError` 3곳 모두 #43·§11.2). 그래서 F29가 한 층 위에서 되풀이될 수 있다.
* 혼합(일부 후보는 축 밖, 나머지는 역산 실패 등)일 때 집계 지점이 무엇을 올리는지도 적지 않았다.
* **고칠 것**: P-34에 두 줄. (1) 혼합이면 기존 클래스를 쓰되 `detail`에 배제 사유를 클래스별 계수로 싣는다(원인 바꿔 보고 금지 -- P-28). (2) `SearchFailedError.record.detail`은 시작점별 마지막 실패 클래스와 계수를 싣는다. #25 oracle에 "하네스 실행 수준에서 축 밖 원인이 보임"(F29 재현 입력의 실행 판) 한 줄을 더한다.

---

## 4. minor

* **m1** §10.6-0 "둘 다 수이면 차가 허용오차 안": margin 차의 허용오차가 정의돼 있지 않다. S2 (나)를 택하면 "같은 클래스 margin은 비트 동일, 아니면 차를 기록하고 원인 card"로, (가)면 "Phase 4에서는 생기지 않음"으로 적는다.
* **m2** §10.7 `LutDomainError(ValueError)` 기본안: 계획은 `SchemaRejectedError`를 "`Exception` 직접 하위 -- 기존 `except ValueError`와 후보 실패 처리가 삼키지 않게"로 정했다(N3.14 표). 반대 선택의 근거 중 "I-C11 xfail `raises=ValueError`"는 KVL 실패라 LUT 정의역 오류와 무관하다. 기본안은 유지해도 되지만 #25 작성 전 실측 표가 X 15곳뿐 아니라 **MOD1 raise 지점부터 집계 지점까지 경로 위의 모든 `except ValueError`/`Exception`**(F5: SR 26·6)을 다루게 적는다. #25가 #10보다 먼저 병합되므로 그 사이에는 #10의 좁히기가 없다.
* **m3** §8.4 "사본 전체 test 1회 813건 272 s"(cd64170)는 HEAD `a796468`에서 수집 886건(실측 `--collect-only`, `--gmid-phase=4`). [prep] 표기를 붙이거나 갱신한다.
* **m4** E3 칸에 "PT가 tests 전체를 포함하므로 실행 범위 = 전체 suite"(B1 참고).
* **m5** §3.2 #1 행 (5)의 "B26-1 card의 'V3 계획'·U1 대기 문장과 수치 228은 … 아직 미반영"은 B26-1 v4와 B26pre 뒤 상태로 갱신한다.
* **m6** §11.2 #43 margin `null` 근거에 계획 396행(기둥 VDS 합 검사는 봉인 검사 대상 아님)을 더한다. §9-23은 `user_decisions.md` 원문이 이미 "실제 순서는 Phase 3 design"이라 적어 확인이 끝났다 -- '결정됨(기록 원문)'으로 닫는다.

---

## 5. 검사 3·4·5 결론

### 5.1 §9-22·§10.7과 `00-common` §7·계획 IC9 (검사 3)
* `00-common` §7.2 원문: "`normalized_margin(magnitude, tol)` (MOD2) … 분모의 선택은 N3.14 정규화식이 정본이고, 부르는 쪽이 그 클래스의 분모를 넘긴다. margin을 계산하는 곳은 이 함수 하나다(IC9). 첫 소비자는 실패 캐시 정렬(N3.5, Phase 5)이라 그 변경 단위(`50-failure-cache`)에서 만든다(WP-01)." -- v0.7 인용과 같다.
* 계획 IC9(827행) 원문: "중복 복붙 | 레지스트리 정본 하나, 타입 setter만 | `test_no_raw_duplicated_writes`: 원시 대입·중복 상수 grep 0 | 6b" -- v0.7과 개정 기록의 "IC9(margin 함수 하나)"는 계획 원문이 아니라 `00-common`의 적용 문장이다(S2).
* 계획 749행 원문: "SEAL_VIOLATION·`local_infeasible` = 위반 크기 / 그 봉인 항목의 허용오차 … 분모가 0이거나 정의되지 않으면 margin은 `null`로 기록하고 비교·정렬에 쓰지 않는다(빠뜨린 것과 구분된다)". #43 `null`은 맞고(계획 396행이 뒷받침), #23 `null`은 이 문장과 어긋난다(S2).
* `00-common` §7.1 원문: "**raise 위치 규칙**: N3.14 예외는 MOD4 이상에서만 raise한다. MOD3(구조 유도)은 `status`를 돌려주고, 그것을 소비하는 MOD4·MOD6이 `StructureUnresolvedError`로 바꾼다". `FailureRecord.margin: float | None`. §10.7(MOD1 정의역 오류 → 집계 지점(MOD4 이상)에서 `SealViolationError`)은 이 규칙과 같은 모양이다. 변환되지 않고 새어 나가면 `exit_code_for`가 1(예상 밖)을 주므로 조용하지 않다. 일치. 남는 것은 m2(기반 클래스 근거)와 S9(실행 수준 보존).

### 5.2 새 상수 (검사 4) -- 규칙·oracle의 수치 리터럴 추적

| 수치 | 위치 | 출처 | 판정 |
|---|---|---|---|
| `1e-9 × max(span, 1)` | #43 경계 | HEAD SR 7068~7069 실측(`1e-9 * max(vdd, 1.0)`) | 동작 보존, 새 상수 아님 |
| Δ = −span/2, τ = max tol_V, ±τ | §10.6 | 계획 IC11 예 (1.8, 0)/(0.9, −0.9), N3.6 `tol_I` 최댓값 형태 | 유도 |
| 판정 한 번 6회 평가 | §10.6-0 | 2 + 2·레일 수 | 계수 |
| `min_finger_w` 0.42e-6, `l_min` 0.15e-6, `l_grid_step` 0.005e-6 | §10.2 | difftap.2·poly.1a·`MANUFACTURINGGRID`(출처 열 있음) | PDK 출처 |
| VS 상한 1.8, 간격 0.2 | P-5·P-30 | `supplies_v` 최대 차 / 기존 격자 | 유도·기존 값 |
| `min(high) > max(mid) > max(low)` | §10.3 | 극성 정의 | 유도 |
| 닫힌 role 어휘 6개 | #47 | F21 실측(인용 card) | 스키마 데이터 |
| 0.0273, 0.9227, 0.2227, 1.6 … | F·UD 칸 | [pack]·[ud17]·F25~F27 실측 | 기록값(판정 경계 아님) |
| **`tol=1e-6`, `max_passes=50`** | `propagate_node_voltages` 기본 인자 | 근거 없음 | **S6** -- 'conflicts 0' oracle이 기댄다 |
| 0.2(`min_vds_by_role`) | #54 | DF-20 폴백 | v0.7에서 쓰지 않음(해소) |

### 5.3 topology 무관 (검사 5) -- 엔진 규칙별

| card | 규칙 | 판정 |
|---|---|---|
| #22 | DEC-61 vsb 식, bulk 미선언이면 극성별 최저/최고 전위 넷 | 이름 없음, 합성 red |
| #23 | 충돌 > tol_V 거부, 첫 소비자 앞 검사(P-27) | 이름 없음, 합성 + 계수 래퍼 |
| #25·#10 P-34 | 정의역 오류 → 후보 배제 → 집계 지점 변환 | 이름 없음(S9 보완) |
| #53 (i)·(ii) | 선언 고정 노드 읽기 / 컬럼 KVL 일반 규칙 | 이름 없음, 합성 + 다른 회로 무동작 명시 |
| #54 엔진 갈래 | 교차 그룹 노드 구속 | "(a) 합성 회로 + 무동작" 명시 |
| #55 엔진 몫 | 선언 bulk 읽기 | **oracle에 합성·무동작 없음 → S5** |
| #19 lint | 어휘 = 선언에서 실행 시점 읽기 | 이름 없음 |
| #21 `rail_voltages`·IC11 | `supply_nets`만, 전위형 metric = type 단위 | 이름 없음. 대상 회로 선택(P-32)은 test 입력 규칙이고 엔진 규칙이 아님 |
| #54 (i) `budget_reference_device` | 메타데이터 | HEAD SR에 키 있음(28곳, 1778행 읽기) -- 데이터 갈래 주장 맞음 |

---

## 6. 의존 그래프 재실행 (`C:/g100`)

| 시나리오 | 결과 |
|---|---|
| 원 스크립트 S0~S8, C1~C4 | 기록과 동일(S 전부 비순환, C 전부 순환) |
| R1 D-27: #2·#3·#4 → D0b | 비순환 |
| R2 #2를 Phase 4로(P3DoD ← #2 제거) | 비순환 |
| R3 #53 (i) `supplies_v` 같은 스키마(#21 → #53) + 권고 #53 → #23 | **순환 → S3** |
| R4 #53 (i) #22 고정 경로 재사용(#22 → #53) + 권고 | **순환 → S3** |
| R5 R3에서 권고 제거 | 비순환 |
| R6 #54 엔진 갈래 + #21이 #54를 하드로 기다림 | 비순환 |
| R7 #54 데이터 갈래 + #21 ← #54 하드 | 비순환 |
| R8 #17 → D0b | 비순환 |

## 7. 승인 질문

`_drafts/phase4_approval_question.md`에 썼다. 승인과 함께 묻는 것 = UD-0(원칙 기본안 P-1~P-34 + §9 정정 요청 + S2 margin 기본안), UD-6(U-09), UD-1, UD-15, 그리고 계획 지정 확인 한 묶음(U-04·U-05·U-26 (a)). card 착수 때로 미루는 것 = UD-7·UD-9(#19 전), UD-17a~e(공동분석, 권고 #23 착수 전), UD-18(#47), #46 게이트 승인, #21 V4 면제, §7.4 DEC-40 건별. 이미 따로 대기 중인 것 = B26pre U1·U2, B26-1 U4·U5, Phase 3 D-19.
**선결 조건**: B1·S1~S4는 질문을 올리기 전에 문서에 반영한다(S2는 기본안을 문서에 확정해야 UD-0 문안이 성립한다).

## 산출물·정리

* 쓴 파일: 이 파일, `_drafts/phase4_approval_question.md`. 저장소·worktree 쓰기 0, git 상태 변경 0(`git status --short`가 시작 스냅숏과 같고 HEAD `a796468` 그대로).
* 스크래치 `C:/g100`(HEAD 복제본 `iso`, `p4v07_dag.py` 사본·출력, `extra.py`·`extra.out.txt`, `SR.py`)은 검토 끝에 삭제했다.
