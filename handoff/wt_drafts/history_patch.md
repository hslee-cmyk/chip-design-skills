# history 추가 초안 -- 2026-09-30 ~ 2026-10-01 (070cf69 이후)

대상 파일(유일한 계획 이력 문서): `docs/01-plan/features/gain-budget-gmid-sizing.history.md`
(gate `master` `7535799`와 메인 `master`의 이 파일은 같다. 마지막 이력 커밋은 `1e2e243` "history H1에 Phase 1 완료 기록", 2026-09-23 -- Phase 2 card(P1~P8·복원·DF-35)는 이 문서에 행이 없고 `.ai/context.md`에만 있다. 아래는 오케스트레이터 지정 범위 070cf69 이후만 다룬다.)

## 0. 문서 구조와 넣을 자리 (7535799 기준 줄 번호)

| 절 | 형식 | 넣을 자리 |
|---|---|---|
| 머리 서술 절(`### 제목 (날짜)` + 문단·글머리) | 최신이 위. 마지막 서술 절은 2026-09-18(05 v3.6 마감) | 22행 `### 05 v3.6 마감 …` **앞**(찾아보기 표 뒤) |
| `## H1. 결정 경위` 둘째 표 | `\| 사건·U ID \| 날짜 \| 사용자 원문·경위 \|` -- 마지막 행 326행 `\| Phase 1 완료 \| 2026-09-23 \| …` | 326행 **뒤**(표 끝, 327행 빈 줄 앞) |
| `## H2. 정정·폐기 이력` 첫 표 | `\| 항목 \| 무엇이 어떻게 틀렸나 / 무엇이 폐기됐나 \| 언제·무엇으로 대체 \| 현행 위치 \|` | 376행 **뒤**(표 끝) |
| `## H4. 측정 근거표` | `\| 수치 \| 측정 조건 \| 원자료 \| 계획서에서 쓰는 곳 \|` | 525행 **뒤**(표 끝, 원자료 목록 문단 앞) |

규칙: 셀 안에 `|`를 쓰지 않는다(아래 행은 확인함). 반영은 Edit/Write 또는 Python 바이너리 쓰기만(heredoc append 금지). 반영 뒤 `git diff --numstat`에서 삭제 0줄 확인.

## 1. 반영 시점 표 (오케스트레이터용)

| 묶음 | 항목 | 반영 가능 시점 |
|---|---|---|
| A | DF-36 완료(1차 V3 FAIL·재시도·cherry-pick 교훈), B28 완료, E1 정정, E4 기준값 정정(D1), D2, topology 주석 보류 | **지금**(근거 커밋 전부 gate `master`에 있음: `148bd6d`·`8790b24`·`6398a28`·`ab90ec5`·`2140da8`·`b7d2570`) |
| B | P9 | P9 판정 기록(`role/audit/20260930-p9-kcl-edges`, 병합 `b7765b0`) push 뒤 -- 판정 수치는 판정 기록에서 채운다(자리표시 `<…>`) |
| C | A1-a(면제 묶기), A1-b(+정정), V3 면제 누수(H2), 본문 전체 V3 비용(H4), V3 card 검토 2회 | 승인 기록 `20260930-v3-exempt-binding`·`20260930-v3-changed-stmt-scope` + 두 spec card·interface card·design 05/10·계획 N4.2 문서 커밋 push 뒤(커밋 id 자리표시) |
| D | A2(B26-1·B34 Phase 3 전), B26-1·B34 검토 | 계획 정정 + 승인 기록 `20260930-b26-before-phase3` push 뒤 |
| E | A3(E4 PT phase=2 + dod) | 승인 기록 `20260930-phase2-e4-phase`(target_kind diff) + design 20 §10 E4 절차 보강 커밋 push 뒤 |
| F | Phase 3 G1 검토 2회, B33 검토, B37a 검토 | 각 design/spec card 커밋 push 뒤(아직 초안) |
| G | Phase 4 design 검토 2회, F26·F27, UD-17 | Phase 4 design(v0.4) 커밋 push 뒤. UD-17은 **결정 대기**로 적는다(사용자 공동분석 후 결과 행 추가) |

---

## 2. 머리 서술 절 (22행 앞에 넣음 -- 묶음 C·D 반영 때, 그 전에 넣으면 커밋 id 자리표시를 남기지 말 것)

```markdown
### V3 대상 범위 -- B28 뒤 '본문 전체 변이'가 실제로 돌기 시작했다 (2026-09-30 ~ 2026-10-01)

B28(`20260930-v3-history-clone`, gate `8790b24`)로 V3 도구가 `--head` 격리 복제본(이력 포함)에서 실제로 돌고 기준 실행 실패가 `ERROR`가 되자, 그 전까지 "도구가 못 돌아 auditor가 사이트만 대체 측정"하던 경로(P8·DF-36)가 없어졌다. 그런데 V3는 AST가 바뀐 def의 **본문 전체**를 변이한다. B26-1 사전 측정(gate `cd64170`, 시뮬레이션 head)에서 바뀐 def 31개의 변이 2,472개, 그중 diff가 닿은 것은 106개, 현실 하한 약 19 h·상한 약 122 h였다(H4). 기존 문장의 생존 변이를 넘기는 길은 변이 id 면제(`target_kind: decision`)뿐인데, 그 면제가 def가 바뀐 뒤에도 그대로 적용되는 누수가 실제 판정에서 나왔다(DF-36, H2).

사용자 결정(2026-10-01, H1 A1-a·A1-b): (1) 면제를 '변이 id@함수 원본 해시'에 묶는 게이트 변경(강화), (2) V3 대상을 '바뀐 문장 + 감싸는 제어문 + 삭제 지점 바로 뒤 + 바뀐 이름을 같은 블록 뒤쪽에서 읽는 문장 + 새 def 전체 + 항상 `early_return`'으로 좁히는 범위 정책(N2, **판정 약화 승인**). 놓치는 것: ① 다른 블록에서의 사용 ② 두 단계 이상 흐름 ③ 바뀌지 않은 문장의 기존 test 강도. 두 card 모두 독립 검토 2회를 거쳤고 1차 검토가 묶기 해시의 docstring 결함(B1)과 머리만 바꾼 변경의 대상 0(B2)을, 2차 검토가 승인 문안보다 실제 공백이 넓다는 것(사례 11·14)을 잡았다 -- 앞의 둘은 card 개정으로, 뒤의 것은 사용자 정정(T6 넓힘)으로 닫았다. 같은 측정에서 계획서 533행 이동 규칙("해시가 같은 함수는 V3 대상에서 뺀다")이 도구에 구현돼 있지 않다는 것도 드러났다(H2) -- 구현은 Phase 3 G1 card 몫. 승인 기록 `20260930-v3-exempt-binding`·`20260930-v3-changed-stmt-scope`, 커밋 `<묶음 C 문서 커밋>`.
```

---

## 3. H1 둘째 표 행 (326행 뒤)

### 묶음 A -- 지금 반영 가능

```markdown
| DF-36 완료 | 2026-09-30 | `20260930-df36-instance-relpath`(red-green): `save_instance_json`의 `topology_ref`를 저장소 루트 기준 `/` 상대 경로로(비공개 헬퍼 `_topology_ref_relpath`, 루트는 `__file__` 유도), 저장소 밖·다른 드라이브 topology는 파일 쓰기 전 `ValueError`. 1차 시도는 V3 FAIL -- 다른 드라이브 분기 변이가 생존(test 공백, 1차 test `2c61257`). 2차는 test에 다른 드라이브 2건 추가(`6444a03`)하고 코드는 1차와 같게(`ed98d35`), 병합 `b29be01`, 판정 `148bd6d`(red 21, 798 passed·15 xfailed, V3 대체 측정 26 중 killed 22·면제 4·생존 0, E-INST·E-LIB·E-LIB-INST 판정값 base와 같음). **재시도 절차 교훈**: 오케스트레이터가 code-author에게 1차 커밋 `git cherry-pick`을 지시했고 EL1이 hook 없는 커밋 생성으로 거부했다(agent의 `git apply` 시도도 거부). 이후 1차 구현 재사용은 `git show`로 읽고 Edit로 옮겨 일반 commit, `git diff <1차> HEAD -- <파일>` 빈 출력 확인으로 지시한다. 면제 4는 뒤에 누수로 판명(H2 'DF-36 V3 면제 4') |
| B28 완료 | 2026-09-30 | 게이트 변경 `20260930-v3-history-clone`(red-green, 승인 `ab90ec5`): V3 사본 = `--head` 격리 복제본(이력 포함, origin 없음), 기준 실행 실패·복제 실패 = `ERROR` exit 2, 임시 복제본 강제 삭제. 원인은 P8 1차 시도에서 드러난 결함 -- `.git` 없는 사본에서 `test_ts6_probe_relocate`의 `git show`가 기준 실행을 실패시켜 변이 2,060개가 전부 '생존'으로 셌다. spec card `d99919c`(design 05 §10 V3 행 ④ 개정), test `b93c1e4`(redteam 공격 31, `rt.py` 선택 키 `tool_tmpdir`·`root_state`), code `dee338d`, 병합 `2b41e79`, 판정 `8790b24`(공격 31 FAIL→PASS, redteam 병합본 PASS 52·SKIPPED 7·FAIL 0, pytest 795 passed·15 xfailed·3 xpassed, DF-36 범위 재실행 killed 22·면제 4·생존 0). 사전 실측: clone 6.5 s·54 MB(copytree 8.9 s·231 MB). 이 card 뒤 V3가 실제로 돌면서 본문 전체 변이 비용이 표면화됐다(머리 서술 절, H4) |
| P9 설계 E1 정정 | 2026-09-30 | 사용자 "E1 문구 정정 승인하고 topology.json주석은 보류해." design 20 E1·§6.2·§8 P9 행·196행 정정(`6398a28`): P9는 `kcl_series_union` 본문의 중복 엣지 정의만 정본 `_kcl_and_matching_edges` 호출로, `_metric_kcl_residual`은 P9 대상 아님, 차등 test 경로 `tests/contracts`, 다선형 보간은 DUP 대상 아님. 승인 기록 `20260930-p9-e1-correction`(`ab90ec5`) |
| topology.json 주석 정리 보류 | 2026-09-30 | 같은 답의 뒷부분. `current_reuse_telescopic_ota.topology.json` 1250·1281(`suggest_headroom_stack_groups`)·1872(`_metrics_comment`), `nmcnr_amplifier.topology.json` 74(`slew_rate()`)의 삭제된 이름 안내는 P10 범위 밖 백로그 B29. 고칠 때 승인 기록(쓰기 경로표·U-16), 주석 필드만·connectivity 불변, auditor가 주석 외 필드·E-LIB 동일 확인 |
| Phase 2 DoD D1 -- E4 기준값 정정 | 2026-09-30 | 사용자 "둘다 기본안으로 진행해". E4 원문 "Phase 1 DoD와 같은 값(회로 9/9 로드, instance.json 해시 동일)"은 Phase 1 기록에 값이 없고 DF-36이 `topology_ref`를 의도 변경해 그대로 잴 수 없었다. 기본안: `da03c0e`(Phase 1 마지막 병합본)와 Phase 2 마지막 병합본을 같은 경로에서 비교 -- E-LIB 9/9 로드·`run_topology_pipeline` 출력 동일, E-INST(파일럿·folded_cascode)는 `topology_ref`를 뺀 해시 동일 + `topology_ref` = DF-36 계약 1 값, `da03c0e` 쪽 하네스는 DF-35 base 모드(경로 리터럴 치환). design 20 §10 E4 정정 `2140da8`, 승인 기록 `20260930-phase2-e4-baseline`(`b7d2570`, target_kind diff) |
| Phase 2 DoD D2 -- 남은 probe | 2026-09-30 | 같은 답. P3c 보류분 `tests/probe_physical_consistency.py`는 추가 card 없이 E2 문구(`tests/probes/**`)대로 판정하고 DoD 기록 '남긴 관찰'에 "P3c 보류(B21, Phase 4), 스캐너 범위 밖 rail-set 재구현 1건"을 적는다. 기준 변경 아님(승인 기록 없음) |
```

### 묶음 B -- P9 판정 기록 push 뒤

```markdown
| P9 완료 | 2026-10-01 | `20260930-p9-kcl-edges`(equivalence, 승인 `20260923-20-dead-code-dup-design` + `20260930-p9-e1-correction`): `kcl_series_union` 본문의 엣지 정의를 `_kcl_and_matching_edges` 호출로 통합, 함수·시그니처 유지. spec card·interface card `7535799`, test `c8d55db`(계약 2 그룹·대표·키 순서, 계약 3(b) 정본 엣지 집합, 합성 넷리스트 11개), code `16a71fa`(경로 압축 제거, 레지스트리 정정), 병합 `b7765b0`, 판정 `<판정 커밋>`(<V1 수치>, V3 <대상·killed·생존>). spec card 단계 독립 검토(`review_p9.md`) blocking 1: 경로 압축 줄 삭제가 어떤 test로도 죽지 않는 등가 변이라 V3 FAIL 확정 -- 경로 압축 자체를 지워 대상에서 없앴다. should-fix 4(`Transistor`를 interface card에, 줄 수 판정을 AST `Name` 참조 수 19→18로, V3 실행 조건·timeout 명시, DIFF-DUP 입력 고정) 반영 |
```

### 묶음 C -- V3 두 card 문서·승인 기록 push 뒤

```markdown
| A1-a V3 면제 묶기 | 2026-10-01 | AskUserQuestion 답 "승인 (Recommended)". 게이트 변경 `20260930-v3-exempt-binding`(강화): 면제 원소 = `변이 id@함수 원본 해시`(docstring·데코레이터 포함 원본 def의 `ast.dump(annotate_fields=True, include_attributes=False, indent=None, show_empty=False)` sha256), 해시가 같을 때만 적용, 원소 형식 오류 = `malformed`, exempt도 `--out`에 기록, 데코레이터 변이 NOOP 수정(`_replace_def`를 첫 데코레이터 줄부터). 근거 = DF-36 면제 누수(H2). 순서 P9·P10·P10b 뒤, B26-1 전. 승인 기록 `20260930-v3-exempt-binding`(target_kind diff, diff_path 계획·design 05·design 10·interface·spec), redteam 34. 커밋 `<…>` |
| A1-b V3 범위 정책 | 2026-10-01 | AskUserQuestion 답 "② N2 (Recommended)". `20260930-v3-changed-stmt-scope`: V3 대상 = 바뀐 문장 + 감싸는 제어문 + 삭제 지점 주변 + 새 함수 전체 + 항상 `early_return`, def 머리 변경은 좁은 판 (b)(def 자기 필드 + 바뀐 매개변수를 읽는 문장). 계획 문구 기준 **판정 약화** -- 승인 기록 범위 설명에 "약화 승인" 명시. 승인 당시 근거 수치 B26-1: 변이 2,472 → 228, 현실 하한 19 h → 0.6 h, 미실행 줄 변이 306 → 6 |
| A1-b 정정 -- T6 넓힘 | 2026-10-01 | 2차 검토(`review2_v3_cards.md`) 적대 사례 21건 중 N2가 현행보다 더 놓치는 4건, 그중 2건(사례 11·14: 같은 블록·바로 다음이 아닌 문장)이 승인 안내에 없었다. AskUserQuestion 답 "규칙을 안내에 맞게 넓힘 (Recommended)" -- T6 = 삭제 지점 바로 뒤 문장 + 바뀐 영역이 바꾸는 이름을 같은 블록 뒤쪽에서 읽는 문장, 반복문 본문이면 위치 무관(사용자 문장보다 한 걸음 넓힌 강화 쪽 판단, 보고에 명시). 놓치는 것을 승인 때 안내한 대로 ① 다른 블록 ② 두 단계 이상 ③ 기존 test 강도로 한정. 재측정: B26-1 228 → **294**(현실 하한 0.88 h, 미실행 줄 변이 9), P9 12, B34 10 그대로. redteam 35 (i)(j) attack·(k) control |
```

### 묶음 D -- 계획 정정 + `20260930-b26-before-phase3` push 뒤

```markdown
| A2 B26-1·B34 Phase 3 전 착수 | 2026-10-01 | AskUserQuestion(2026-09-30) 답 "승인 (Recommended)": ① DEC-60 넷 이름 전원 판정 전환기 종료(`supply_nets` 선언만, 없으면 `load_topology` 거부) ② DF-19·DF-26 전원 넷 판정 몫을 MG1에서 분리(B26-1~B26-4) ③ B26-1(`20260930-b26-rail-accessor-set`)·B34(`20260930-b34-grammar-explicit`, analog-grammar 부재 시 조용한 폴백 → `ImportError`)를 Phase 3 모듈 분할보다 먼저. 승인 기록 `20260930-b26-before-phase3`(decision) 하나가 두 card를 덮는다 -- 첫 초안은 B26-1만 적어 B34 card의 approval이 덮지 않는 기록을 가리킬 뻔했다(review2_b34 B1). 별도 B34 기록 초안 `20260930-b34-before-phase3`은 폐기. Phase 4 design UD-14가 이 결정으로 닫혔다. 커밋 `<…>` |
```

### 묶음 E -- A3 승인 기록 push 뒤

```markdown
| A3 E4 PT 실행 | 2026-10-01 | AskUserQuestion 답 "phase=2 + dod 실행 (Recommended)". 드라이런(`dryrun_phase2_e4.md`)에서 E4가 design 10 §10 PT 정의(`--gmid-phase=1`)를 "그대로" 쓰는 것이 Phase 2 DoD와 어긋남을 발견 -- PT를 `--gmid-phase=2`와 `--gmid-dod` 두 실행으로 고정, 같은 커밋에서 스크립트 출처(Phase 2 마지막 병합본 판을 복제본 밖으로 복사해 두 판에 같은 사본)·`python -B -P` 절차 보강. 승인 기록 `20260930-phase2-e4-phase`(target_kind diff). 드라이런 값(증거 아님): E-LIB 해시 동일, E-INST `topology_ref` 제외 두 회로 동일, 두 실행 모두 798 passed·15 xfailed. 커밋 `<…>` |
```

### 묶음 F·G -- 각 문서 push 뒤

```markdown
| 독립 검토가 막은 약화 구멍 (2026-09-30 ~ 10-01) | 2026-10-01 | 초안마다 작성 agent와 다른 검토 agent를 두었고, 아래 blocking은 모두 판정을 약하게 만들거나 test가 dispute로 멈출 결함이었다. (1) **Phase 3 G1** 1차(`review_phase3_drafts.md`, B6·S13·m8): 덮어쓰기·자유 이름 재바인딩·`__file__` 변경·클래스가 '이동'으로 분류돼 V3 대상에서 빠짐, `plan`의 이동 중 동작 미정, E2가 엉뚱한 필드를 잼 → v3에서 M-0~M-4·클래스 골격 단위·규칙 A-0. 2차(`review2_phase3_v3.md`, B2·S8): 옮긴 def를 qualname 키로만 빼서 같은 키의 해시 다른 def(조건부 재정의·property setter)가 V3·V7에서 빠짐 → v4. (2) **V3 두 card** 1차(`review_v3_cards.md`): 묶기 해시가 docstring을 빼 같은 해시에서 id가 다른 문장을 가리킴(B1), 머리만 바꾼 변경 → 대상 0 → PASS(B2) → v2. 2차(`review2_v3_cards.md`): 승인 문안이 놓치는 범위를 실제보다 좁게 적음(B1) → A1-b 정정. (3) **B33**(`review_b33.md`, V7 호출 그래프 간선): R2가 `super().__init__` 속성 폴백을 깨워 모든 새 `__init__`이 도달, R1 재수출 폴백이 외부 모듈 속성에도 걸림, 17단계가 해석 형식을 고정 못 함(blocking 3). (4) **B34**(`review_b34.md`): approval 줄이 동작 변경을 덮지 않는 design 20 승인, `idioms.Match`에 `__eq__`가 없어 `==` 판정 불가, parametrize 문자열 진입점이 V3 인벤토리에 안 잡힘(blocking 3) → 범위 13 → 5 def, V3 1,139 → 118(base) → 102(head). 2차(`review2_b34.md`): A2 승인 기록 초안에 B34가 없음(B1). (5) **B26-1**(`review_b26_1.md`): 본문 전체 V3 약 2,465 변이에 계획 없음(B1 -- A1의 계기), 계약 7 '역방향'이 `netclass.RAILS` 대소문자 무관 집합 때문에 병합본에서도 거짓(B2). (6) **B37a**(`review_b37a.md`): 불변 범위 문장이 병합본에서 거짓·oracle이 엔진 정규식 import, 픽스처 선언에 따라 DEC-40 여부가 갈림, `try/except Exception: pytest.fail`이 `KeyError`·`TypeError`를 허용 red로 세탁(blocking 3) → v2. (7) **Phase 4 design** 1차(`review_phase4_design.md`, blocking 4): UD-3 nmcnr ±0.9 전환이 DF-24 수정 전, IC11 rail2 oracle·선행이 계획과 다름, 열린 항목 잔존, B35 어댑터를 근거 없이 원칙 기본안으로 → v0.3. 2차(`review2_phase4_v03.md`, blocking 2): V3 범위를 사용자 결정 없이 게이트 변경 승인만으로 선행에 넣음, #50 red 형태 근거 없음(실측 F25 -- rail2는 처음부터 PASS) → v0.4, #50 폐지. 원자료 `wt/_drafts/review_*.md`·`*_revision_log.md` -- 커밋 때 `docs/03-analysis/…`로 옮길 경로 `<…>` |
| UD-17 (결정 대기) | 2026-10-01 제기 | Phase 4 design v0.4 실측 F27(H4): HEAD θ*에서 `propagate_node_voltages` conflicts -- folded 4개(M4@Y·M1@X 1.6 V, M9@Vg9 1.1 V, M8@out 1.0 V), current_reuse 4개(각 0.22272 V). #23(conflicts > tol_V → SEAL_VIOLATION)이 병합되면 두 정본 회로의 θ* 평가가 실패로 바뀐다. 기본안: #23은 계획대로 진행하고 E-INST 변화는 기대 차이표 + DEC-40, 충돌 원인은 회로별 사용자 공동분석(connectivity 표·도달 경로 표, 자료 `ud17_scripts/out/report.txt`). 회로 해석이라 오케스트레이터 단독 판단 금지 -- 결과는 이 표에 새 행으로 |
```

---

## 4. H2 첫 표 행 (376행 뒤)

```markdown
| **DF-36 V3 면제 4**(판정 `148bd6d`, B28 재실행 `8790b24`도 같음) | 면제 4개는 C8 승인 `20260922-ic3-v3-exempt`의 변이 id였다. 그 승인은 옛 `save_instance_json`(def 해시 `9cb09766…`)에 대해 받은 것인데 DF-36이 함수를 바꾼 뒤(`11a55c19…`) 같은 id가 그대로 적용됐다 -- 면제 원소가 id뿐이라 함수가 바뀌어도 승인이 따라왔다(승인 범위 밖 누수). auditor는 4개가 같은 문장을 가리키는지 손으로 확인했지만 승인 범위로 보면 V3 PASS는 누수에 기댄 판정이다. 자동 번복 경로는 없다(`integrity.py` 행 3(나) 재판정은 `merge_gate.py`만 돌리고 V3를 부르지 않는다) | 2026-10-01, 게이트 변경 `20260930-v3-exempt-binding`(면제 = id@원본 def 해시, A1-a). 백로그 B41: 필요하면 4개를 실제로 돌려 DF-36 V3 재측정 | 계획 N4.2 V3 행, design 05 §10 V3 ⑤ |
| "Phase 3 이동 card는 계획 규칙(해시가 같은 함수는 V3 대상에서 뺀다, 계획 533행)으로 V3 비용 문제가 없다"(`v3_scope_systemic.md` 초판) | 거짓. `mutate_changed.main`은 같은 경로의 base만 비교하고 새 파일이면 그 파일의 def가 전부 대상이다(359~364행) -- 계획서 이동 규칙은 도구에 구현돼 있지 않다. G1 초안 실측: 엔진 4파일 상한 V3 대상 def 473·변이 15,677 | 2026-10-01 `review_v3_cards` S8로 정정. 구현은 Phase 3 G1 card | 계획 533행, Phase 3 design §3 MOVED |
| B26-1·B34 spec card 초안의 `approval: 20260923-20-dead-code-dup-design` | 그 승인은 "동작이 바뀌는 수정"을 명시적으로 뺀다. Phase 범위 밖을 당기거나 동작을 바꾸는 card를 덮지 못한다 -- review_b26_1 S3, review_b34 B1이 같은 결함을 두 번 잡았다 | 2026-10-01, 사용자 decision 기록 `20260930-b26-before-phase3`(A2)로 교체. B37a도 같은 이유로 자기 decision 기록 `20260930-b37a-ports-roles` | 두 spec card 머리 |
| P8 spec card 계약 6 괄호 문장 "옛 목록 3개 함수는 현 소스와 맞지 않음"(design 20 §6.1 원문 인용) | 사실과 반대 -- 세 함수는 18곳 사이트에 포함됐다. P8 1차 시도가 이 문장 때문에 V2 FAIL | 2026-09-30, design·spec 정정 후 2차 PASS(`54dec6a`). 교훈 = 설계서 사실 문장을 spec card로 옮길 때 그 자리에서 재측정, `_TEMPLATE.spec.md` '작성 전 실측' 절 | design 20 §6.1 |
```

(P8 행은 070cf69 이전 사건이다. history에 Phase 2 card 행이 없어서 넣었다 -- 범위를 070cf69 이후로 엄격히 지키려면 이 행은 빼도 된다.)

---

## 5. H4 측정 근거표 행 (525행 뒤)

```markdown
| V3 본문 전체 변이 비용: B26-1 변이 2,472(diff가 닿은 것 106), 하한 약 3.4 h·상한 약 122 h / P9 24 / B34 직접 폴백 def 1,130·전파 def 265 | gate `cd64170` `git archive` 사본(`C:/g39`), `mutate_changed.changed_defs`·`mutants`·`inventory`, `reachability.build_graph`만 읽기 전용 import(도구 `main` 미실행), B26-1·P9는 시뮬레이션 head. 사본 전체 test 813건 272 s, 엔진 def 하나의 인벤토리 60~159개·177~192 s(느린 test 4개가 거의 모든 인벤토리에 듦), pytest 기동 4.7~7.1 s/회, 직렬. 하한 = 변이마다 기동만, 상한 = 변이 × 인벤토리 시간 | `v3_scope_systemic.md`, `b26_v3_measure.py`·`.out.txt` | 머리 서술 절 'V3 대상 범위', A1 결정 근거 |
| V3 범위 정의별 대상 변이 수: B26-1 지금 2,472 / 옛 N2 176 / N2(b) 228 / 넓힌 T6 294 / N2a 1,309 / D1 399; P9 실제(`7535799→b7765b0`) 28 / 12 / 12; B34 좁힌 초안 55 / 10 / 10. 현실 하한 B26-1 지금 19.2 h → N2 0.63 h → 넓힌 T6 0.88 h, 미실행 줄 대상 변이 306 → 6 → 9 | gate `7535799` archive 사본(`C:/g60`, `C:/g69`), `$PY` 3.14.2 `-B`, 분류기 시뮬레이션(옛 N1 139·옛 N2 176 재현으로 교정). 미실행 줄 = head 줄 → base 줄 대응(새 줄 119개는 판정 불가). 적대 동작 변경 21건: 지금 179 / 승인 당시 87 / 넓힌 98 대상, 넓힌 T6가 지금보다 더 놓치는 것 1c·4b(두 단계)·15(다른 블록) | `v3_cards_revision_log.md` §2·§6, `v3_scripts/out/v3_scope_classify.txt`·`v3_scope_widen.txt`·`v3_adv21.txt` | 승인 기록 `20260930-v3-changed-stmt-scope` 범위 설명 |
| F26 LUT VS 축 밖 조회(지금 조용히 클램프, DF-27): folded θ* 조회 403,847 중 436(vsb M7 −0.65, M1·M2 1.6, M5 1.8 -- 축 [0, 0.8]), 하네스 전체 실행 1,137; current_reuse θ* 533,469 중 3,537(0.8125 ~ 1.5 대, 음수 없음). L·VGS·VDS 축 밖 0. 거부로 바꾸면 folded θ* = `InfeasibleSizingError`(M7), 전체 실행 400 격자점 전부 infeasible | HEAD `7535799` 사본(`C:/g61`), 보간 함수를 계수 래퍼로 바꿔 끼운 `b2_axes.py`(축 L·VGS·VDS·VS), `b2_run_axis.sh` | Phase 4 design v0.4 §2 F26·부록 C4·C6 | 계획 DF-27·U-27 행, Phase 4 #22 → #25, #25·#26·#27 연속 병합(P-24) |
| F27 노드전압 경로 충돌(DF-02, 지금 엔진 미소비): folded conflicts 4(M4@Y 1.6, M1@X 1.6, M9@Vg9 1.1, M8@out 1.0 V), current_reuse 4(M5@Vy, M64@Vbias3, M1a@N1a2a, M1b@N1b2b 각 0.22272 V), unresolved 0 | θ* 평가 뒤 `propagate_node_voltages(by_name, sized, vdd)`(`b2_nodes.py`), 같은 사본. 도달 경로 추적(엔진 경로와 일치 확인) `ud17_scripts`. 한 점 평가 current_reuse 약 15~23 s, folded 약 14~17 s | Phase 4 design v0.4 §2 F27·부록 C7, `ud17_scripts/out/report.txt` | 계획 DF-02 행, Phase 4 #23, UD-17 |
```

---

## 6. 확인한 것·남긴 것

* 대상 파일 구조는 7535799에서 확인했다. 마지막 이력 커밋 `1e2e243`(H1 둘째 표에 'Phase 1 완료' 행)이 현행 기록 형식이다 -- 그래서 사건은 H1 행으로, 정정은 H2, 수치는 H4로 나눴다.
* `b33_revision_log.md`는 `_drafts`에 없다(B33은 `review_b33.md` + `draft_b33.spec.md`·`.v1.spec.md`만). B37a의 `b37a_revision_log.md`도 card가 가리키지만 파일이 없다 -- 검토 결과는 검토 파일에서 옮겼다.
* `.ai/context.md` 마지막 기록은 B28·E4·백로그 B29~B37까지다. P9 진행, A1·A2·A3, 백로그 B39~B46은 아직 없다(`backlog_additions.md`가 다음 문서 커밋 때 바이너리 append 대상).
* P9 판정 기록은 아직 없다(`role/audit/20260930-p9-kcl-edges`에 병합 `b7765b0`만) -- 묶음 B의 `<…>`는 판정 기록에서 채운다.
