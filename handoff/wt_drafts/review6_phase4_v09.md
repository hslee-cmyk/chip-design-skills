# 6차 독립 검토: `draft_phase4_design.md` v0.9 (Phase 4 `40-defect-fixes`) -- 변경분(delta) 검토

검토자: 독립 검토(작성자 아님). 범위는 **변경분만** 본다: `draft_phase4_design.v08.md` 대 `draft_phase4_design.md`(v0.9), `phase4_approval_question.v08.md` 대 `phase4_approval_question.md`, 기준 `review5_phase4_v08.md`, `phase4_revision_log.md` v0.8 → v0.9 절(333행~).
종료 규칙: (a) v0.9 변경이 새로 만든 결함과 (b) 5차 지적 중 실제로 풀리지 않은 것만 적는다. 이미 닫힌 앞 차수 항목은 다시 열지 않는다.
측정: gate `master` = **`0f23786`**(시작·끝 같음). `git status --short` md5 `168fd530…`(시작·끝 같음). 저장소 쓰기 0, git 상태 변경 0. 실험은 모두 `C:/g118`(HEAD `git archive` 복제본 `iso`, DAG 사본, probe 3개, 출력)에서 했고 끝에 지웠다.

---

## 0. 판정

**blocking 0, should-fix 1(R6-S1), minor 2, 정보 1. R6-S1 문안을 반영하면 Phase 3 DoD 뒤에 질문해도 된다.**

| 5차 | v0.9 반영 | 재측정 | 판정 |
|---|---|---|---|
| N-S1 | (가) 앞당김 경로 삭제(P-35), 승인 시점 간선 | `p4v09_dag.py`를 사본에서 다시 돌렸다. 기록된 `out/p4v09_dag.out.txt`와 `diff` 0, `SUMMARY scenarios=23 unexpected=0`. S0~S9 비순환, RC1·RC8·RC9·C1~C7 순환, N1 비순환. 스크립트 안 `assert` 3개(#6·#25 → #10, #17 → #18, UD-0 → #2 / P3DoD → UD-0)가 통과했다. 줄 끝 주석에 `add(`가 숨은 줄은 0이다. design §5 `P3?` 칸(#2·#3·#4·#17·#18 = 'F2 뒤 단일 경로')과 승인 질문 21행에 '앞당길 때는 D0b 전에만' 문장이 남아 있지 않다 | 해소 |
| N-S2 | #23 범위 확장(P-36): `node_tol` 명시 전달, vsb `tol` 삭제(비트 동일) | 호출부 목록은 맞다(§1). **비트 동일이 '무동작'은 아니다**: current_reuse 정본 실행의 θ*와 metrics가 바뀐다(§2, R6-S1) | 부분 해소 → R6-S1 |
| N-S3 | 계획 1158·1159행 추가, 1002행 변경 없음 | HEAD 계획 원문을 다시 확인했다. 1159행 = `50-failure-cache` 행 "`00-common` CC-9(`normalized_margin`), …"(N9.1, 1147행 절 아래), 1158행 = `40-defect-fixes` 행 "… `00-common` CC-4(실패 규약 …", 1002행 = N6.1(989행 절) Phase 5 행 "실패 캐시, 시작점 선택(S3 레코드 v1: θ*·start별 결과·실패), margin 반환". 698행 EL3의 입력 목록(N4.1 `담당 Phase`·`강제 test`, N4.2 `도입`, N6.1 `Phase` 열, N3.12.2)에 N9.1은 없다. 인용이 모두 맞다. design §7 요약(631행)만 '1159행'이라 적고 1158행을 빠뜨렸다(m-1) | 해소(m-1) |
| N-S4 | 간선 복원, `assert` | 위 N-S1 행 | 해소 |
| m-3 | 새 grep 명령 | HEAD `sky130_lut_sweep.py`에서 `grep -n -e 'VS.iVS.' -e SID_1F -e xdut -e VS_GRID -e OUTPUT_DIR` = **33줄**. 그 안에 73·75·108·150·267·270·275·276이 있다 | 해소 |
| m-1·m-2·m-4~m-9, 정보 1~3 | 반영 | 해당 줄을 확인했다. m-8 반영 문장 하나에 사실 누락이 있다(m-2) | 해소(m-2) |

---

## 1. N-S2 호출부 목록(gate master `0f23786`)

`git -C R grep -n -w -e propagate_node_voltages -e reconcile_vsb_from_nodes -e audit_vsb_consistency HEAD -- '*.py'`로 정의와 docstring을 빼고 센 실제 호출은 다음이 전부다.
* SR 3831: `reconcile` → `propagate`, tol을 넘기지 않는다.
* SR 3863: `audit` → `propagate(**kw)`.
* SR 7294·7449: `_hr_resolve_vertical_group` 안이다. 각각 `except Exception`(7297·7451)으로 감싸져 있다.
* SR 8658: `reconcile`.
* SR 8892: `audit`. 결과가 있으면 `ValueError`를 낸다.
* `tests/probes/probe_full_research.py:142`. 이 파일은 pytest가 수집하지 않는다. 저장소에 `python_files`·`collect_ignore` 설정이 없고, 기본 패턴은 `probe_*.py`를 잡지 않는다.

`test_ic5.py:51`은 표 문자열이고, `test_ts6_dead_probes.py`에 나오는 것은 합성 소스 문자열·상수다. 둘 다 호출이 아니다. ts6 (c)는 운영 호출이 있는지만 세고 인자 모양은 보지 않으므로 `node_tol` 키워드를 더해도 깨지지 않는다.

design F36·§5.5 #23·부록 A H2의 목록이 위와 정확히 같다.

추가로 실측한 것(정보, `C:/g118/hr_probe.py`, 정본 하네스 인자): 7294·7449 호출에서는 예외가 0건이었다. 그 호출 시점에 `vds`가 있는 소자는 모두 `L`도 갖고 있었다. current_reuse에서 7294는 3,376회 호출됐고 `vds`가 있는 소자는 140,104개였다. 7449는 25,320회, 724,152개였다. 두 경우 모두 `L`이 없는 소자는 0개다. folded에서는 이 두 지점이 호출되지 않는다. 따라서 #23이 7294·7449에 tol_V로 `node_tol`을 넘겨도 입력(kind·L·VDS)이 없어서 `except Exception`이 오류를 삼키는 새 경로가 생길 근거는 정본 실행에서 보이지 않는다.

## 2. R6-S1 (should-fix): vsb 비트 동일은 '엄격해질 뿐'이 아니다. current_reuse 정본 실행 결과가 바뀐다

**측정**: `C:/g118/vsb_probe.py`. HEAD 복제본에서 `reconcile_vsb_from_nodes`·`audit_vsb_consistency`를 같은 본문의 계수 래퍼로 바꿨다. 모드 `head`는 `tol=1e-6`이고, 모드 `proto`는 v0.9 P-36대로 `reconcile`은 `old != exp`이면 덮어쓰고 `audit`은 `d != 0`이면 보고한다. 하네스 4회로 정본 인자로 `optimize_full_circuit_budget`를 실행했다.

| 회로 | head | proto | 차이 |
|---|---|---|---|
| two_stage_ota | `ValueError` 'stage1_out' KVL(F15 기준선) -- reconcile/audit에 도달 안 함 | 같음 | 없음 |
| nmcnr_amplifier | `ValueError` 모든 θ infeasible(F15) -- 도달 안 함 | 같음 | 없음 |
| folded_cascode | reconcile 400회: 5,200건 전부 `old is None`. audit 400회: 5,200건 전부 `d == 0` | θ*·metrics 해시 같음 | **없음(무동작)** |
| current_reuse_telescopic_ota | reconcile 54회 중 **호출마다 1건 `0 < |old−exp| ≤ 1e-6`**(최대 1.11e-16), audit 53회 중 **호출마다 1건 `0 < |d| ≤ 1e-6`**(1.11e-16) | reconcile이 그 1건을 덮어쓰고 audit은 2,703건 전부 `d == 0`이다(게이트 발동 0). 그러나 **θ*가 바뀐다**: `L_class__M68` `0x1.124b078d0db2dp-21` → `0x1.124b078cff54cp-21`, `L_class__M8` `0x1.fcd9f04470762p-22` → `0x1.fcd9f044663dep-22`. metrics 해시 `5ff39866…` → `8b171811…`. SLSQP 경로가 갈렸다 | **동작 변경** |

**원인**: `C:/g118/who_probe.py`로 첫 reconcile 호출을 봤다. 해당 소자는 **M58**(pmos, source `Vx`)이고 저장된 vsb는 `0x1.0000000000002p-2`, 전체 그래프에서 다시 계산한 값은 `0x1.0000000000004p-2`다(2 ulp 차이, `_vsb_source` 없음). M58의 vsb는 SR 7294가 쓴다. 7294는 `_bn_pair`, 곧 **부분 그래프**로 `propagate_node_voltages`를 돌린다(7286~7289행 주석 "M58의 소스 Vx는 diffpair_branch_a가 정한다"). 같은 노드라도 도달 경로가 다르면 부동소수 합의 순서가 달라져서 마지막 비트가 다르다.

**결함(v0.9 신규)**:
1. **P-36의 근거 문장이 사실과 다르다.** design 14행, §5.5 #23 (3), §7.2 P-36, 승인 질문 UD-0은 vsb 비교를 "같은 식으로 **같은 노드전압**에서 다시 계산한 값의 일치"라고 쓴다. 그러나 정본 실행에서는 7294·7449의 부분 그래프 노드전압으로 쓴 vsb가 reconcile 시점까지 남아 있다. 결론(두 함수 모두 비트 동일)은 실측으로 성립한다. proto에서 audit 게이트 발동은 0이고, reconcile은 그대로 두고 audit만 비트 동일로 바꾸면 audit이 53회 모두 발동한다(head 모드 계수 `aud_small` = 호출마다 1건에서 추론한 것이고, 따로 실행하지는 않았다). 그러니 '두 함수가 같은 규칙이어야 정합'이라는 문장은 맞다. 틀린 것은 전제다.
2. **'무동작' 기대가 틀렸고, 승인 질문이 결과 변경을 알리지 않는다.** §5.5 #23은 이 경우를 조건부로 이미 적어 두었다('reconcile 쪽 > 0이면 … E-INST가 달라질 수 있고(기대 차이표 + DEC-40)'). 실측하면 그 갈래가 실제로 일어난다. 그런데 승인 질문 UD-0은 "기준이 엄격해지는 쪽이고 새 상수를 만들지 않습니다"라고만 쓴다. 'reconcile이 2 ulp 차이까지 덮어써서 current_reuse 정본 θ*·metrics가 바뀐다'는 사실이 빠져 있다. 새 상수가 없다는 것은 맞다. 엄격해진다는 것은 audit에만 맞다.

**고칠 것(문안. 새 사용자 결정은 아니다. DEC-40은 §7.4의 '발생 시 건별' 경로를 그대로 쓴다)**:
* §5.5 #23 (3)·P-36·14행의 근거를 고친다. 예: "vsb 비교는 `derive_vsb_from_nodes` 재계산과의 일치다. 정본 실행에서 7294·7449가 부분 그래프로 쓴 vsb는 ulp 단위로 다를 수 있지만(실측 current_reuse M58 2 ulp), reconcile이 비트 동일로 덮어쓰므로 audit에는 차이가 남지 않는다."
* §5.5 #23의 [미측정] 무동작 항목을 사실로 바꾼다. 이 검토의 수치는 검토자 측정이므로 #23 작성 전 실측이 다시 재되, 기대는 'current_reuse reconcile > 0, θ* 비트 변경'으로 적는다. §7.4 DEC-40 예상 목록에 'current_reuse θ*·metrics(#23 vsb 비트 동일)'을 한 줄 더한다. #23의 기대 차이표에서는 노드 충돌 거부(F27)로 생기는 차이와 이 차이를 따로 적어 원인을 가를 수 있게 한다.
* 승인 질문 UD-0의 '근거 없는 기본값 제거' 글머리에 한 문장을 더한다. 예: "그 결과 current_reuse 정본 실행의 θ*가 마지막 자리에서 바뀝니다(소자 하나의 vsb가 2 ulp 다르게 저장돼 있던 것을 다시 맞추기 때문). 기준선 변경은 #23 병합 때 건별로 승인받습니다."

## 3. minor

* **m-1** design §7 결정 상태 요약(631행)은 "계획 N9.1 **1159행**"만 적는다. §9-22·승인 질문·개정 기록은 1158·1159 두 행을 적는다. 631행에 1158행을 더한다.
* **m-2** m-8 반영 문장 621행과 부록 A H6의 사실이 불완전하다. 문장은 "`merge_gate.rule10_phase`는 card phase를 … V 검사 N/A 허용에만 쓴다"인데, `rule10_phase`(532~549행)만 보면 맞다. 그러나 `merge_gate.py`는 card `phase`를 다른 곳에도 쓴다. 1213행·1009~1010행은 V1 명령의 `--gmid-phase=<card phase>`를 강제하고, 1042행은 같은 Phase의 기록된 card끼리 `activated_ic_case`를 합쳐 엄격 집합을 만든다. 그래서 Q-B34-PHASE의 답에 따라 **B34·B26-1의 V1 명령과 엄격 집합**이 바뀐다. 이 문서의 결론('이 문서의 간선·판정은 어느 답이든 같다')은 그대로 성립한다. Phase 4 card의 엄격 집합은 phase "4" card끼리만 합치기 때문이다. 다만 '바뀌는 것은 phase 2 표기 문장뿐'은 과하다. H6에 두 사용처를 적고, 결론은 '이 문서 card의 판정은 같다'로 좁힌다.

## 4. 정보 (결함 아님. 닫힌 항목은 다시 열지 않음)

* 7294·7449의 부분 그래프 전파에서는 다중 도달 차이가 1e-6을 넘는 사건이 정본 실행 current_reuse에서 7294에 10,128건, 7449에 47,264건 있었다(위 probe에서 `tol < 0`으로 모든 다중 도달을 셌다). 이 지점들이 헤드룸 중에 vsb를 유도하므로, P-27('충돌 노드로 vsb 유도 금지')을 #23이 적용하면 이 두 지점도 대상이 된다. 이것은 v0.5 이래의 #23 범위(F27)이고 v0.9 변경이 아니다. #23 작성 전 실측이 정본 θ*(전체 그래프)뿐 아니라 이 두 부분 그래프 지점의 충돌 규모도 재야 한다는 점만 적어 둔다.

## 5. 증거 명령(요지)

```
R=…/chip-design-skills; set -e
git -C $R rev-parse --short HEAD                       # 0f23786 (시작·끝)
git -C $R status --short | md5sum                      # 168fd530… (시작·끝)
git -C $R archive HEAD | tar -x -C C:/g118/iso
python -B C:/g118/dag/p4v09_dag.py                     # 23 시나리오 unexpected=0, 기록과 diff 0
git -C $R grep -n -w -e propagate_node_voltages -e reconcile_vsb_from_nodes -e audit_vsb_consistency HEAD -- '*.py'
bash C:/g118/run_vsb.sh                                # 4회로 × {head, proto} -> out/vsb.jsonl (§2 표)
python -B C:/g118/who_probe.py C:/g118/iso …          # M58, 0x1.0000000000002p-2 vs 0x1.0000000000004p-2
bash C:/g118/run_hr.sh                                 # 7294·7449 호출·예외·L 유무·다중 도달 (§1, §4)
git -C $R show HEAD:docs/01-plan/features/gain-budget-gmid-sizing.plan.md | sed -n '698p;1002p;1158p;1159p'
git -C $R show HEAD:…/sky130_lut_sweep.py | grep -n -e 'VS.iVS.' -e SID_1F -e xdut -e VS_GRID -e OUTPUT_DIR | wc -l   # 33
git -C $R show HEAD:tools/gates/merge_gate.py | sed -n '532,549p;1034,1048p;1186,1216p'   # m-2
```

## 산출물·정리

* 쓴 파일은 이 파일뿐이다. 저장소·worktree 쓰기 0, git 상태 변경 0. 다른 `_drafts` 파일은 수정하지 않았다.
* 스크래치 `C:/g118`(복제본, probe, 출력)은 검토 끝에 지웠다.
