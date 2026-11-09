# P10b spec card 최종화 기록 (20260930-df23-registry-record)

- 입력: `draft_p10b.reviewed.spec.md`(사본 `draft_p10b.reviewed.v1.spec.md`) → 출력 `draft_p10b.final.spec.md`.
- 기준: gate `master` 2d58fd8(P10 문서 커밋 0fa6ca2, measured_at 766b5c2, P10 spec card b8d4c4d가 gate에 있음). 저장소 읽기 전용, scratch C:/g79(측정 끝에 삭제).
- 커밋 시점: P10 판정 기록이 gate에 들어간 직후. 그때 작성 전 실측 1·5·7을 다시 잴 것(P10 test 커밋은 새 contracts 파일 둘뿐이라 값은 바뀌지 않을 것으로 보지만 잰다).

## 다시 잰 사실(커밋된 목록·HEAD 기준)

| 항목 | 리뷰본 | 실측(2d58fd8) | 처리 |
|---|---|---|---|
| 목록 | 1e2e243 목록(590)·후보(515) 비교 수 | 커밋본 515항목, measured_at 766b5c2…, role 302/213, phase 해당 없음 317·4 63·3 61·7b 46·7a 27·6b 1, 묶음 52, 빈 function 0, 파일 이름 8개 고유 | 재현할 수치를 커밋본 값으로 바꿈(비교용, 판정 수치 아님 -- 영구 test는 쓰지 않음을 명시) |
| 목록 항목 필드 | file·function·role·phase·plan_mapping | 515개 전부 가짐(공통 키 15개 기록) | 계약 표 열과 일치 확인 |
| 동작 항목 plan_mapping | "맞지 않으면 신규" | 비DF 76개 전부 `신규(계획 …`로 시작 | 계약 3에 ValueError (v) 추가(조용한 신규 묶기 금지, P10 계약 3과 짝) |
| 레지스트리 | §0~§7 줄 번호·524줄 | 같음, CRLF 524/524, 끝 `|\r\n\r\n`, 마지막 변경 a410f31 | "도구가 `\r`을 뗀다" → "`splitlines()`로 나눠 줄 끝 문자는 판정에 들지 않음"으로 정정(도구는 `read_text`·`splitlines` 사용) |
| reg_check.py | 192-194 argparse | 191-194행(try/parse/except SystemExit/return 2), `--df23-inventory x` → unrecognized arguments, exit 2 실측 | 줄 번호 정정, 실측 명시 |
| test_reg_check.py | sys.path 44-61행 | 51-59행(경로 상수·sys.path 삽입), 61행 `import reg_check` | 줄 번호 정정 |
| design 20 | E-filters 218·221행, P10b 행은 "P10 문서 커밋에서 더한다" | E0 218·E1 219·E3 221·E5 222행, §8 195행에 P10b 행 이미 있음(0fa6ca2) | 결정 필요 항목의 P10b 행 문안 → "반영됨"으로, 의도 절 순서 문장 갱신 |
| 1e2e243..HEAD | 101 | 116 | 해당 문장 삭제(필요 없는 이력 수) |

## 내용 정정

1. **담당 Phase 순서**: "N6.1 순서 목록(3,4,…,해당 없음)" → **문자열 오름차순**. 도구에 N6.1 순서 상수를 박지 않기 위함(상수 금지 원칙). 닫힌 집합에서 sorted == N6.1 순서 실측(True). 거부 입력 "N6.1 순서 아님" → "오름차순 아님(`7b, 4`)".
2. **DF 칸 순서**: "DF 번호 오름차순" → "정수 오름차순"으로 명확화(`DF-4, DF-19`), 거부 입력에 문자열 순 예 추가.
3. **발견 `name` 형식 고정**: df23-section(빠진 것: title·목록·measured_at·8.1·8.2, 제목 없으면 그 하나만), path·measured-at(레지스트리 쪽 값), total(`<축>:<값>`), function(`<파일>::<함수>`). 같은 키의 두 번째 행도 발견. 행 순서는 판정하지 않음(거부 안 함 목록에 "행 순서만 다른 레지스트리" 추가).
4. **ValueError 조건 번호화** (i)~(v), 계약 5 (d) 보충 뮤테이션 대상에 (v)·루트 밖 분기·발견 합치기 추가.
5. **CLI 경로(realpath+normcase)**: `inventory_rel` = realpath 기준 relpath를 `/`로, 루트 안 판정은 normcase(realpath) commonpath. 최상위 dict 아님도 exit 2.
6. **red 근거 검증**: `merge_gate.py` 588-603행(_ALWAYS_RED, _NEW_SYMBOL_TYPES, new_symbol_pair), 수집 오류 `__cause__` 경로, 00-common §8.1 302·303행 인용. Python 3.14 실측 `from <모듈> import check_df23` → ImportError name/name_from. P7(ModuleNotFoundError, (reg_check, *))과 다른 점 명시. "reg_check를 가리키는 첫 import 문"으로 규칙화.
7. **test-author 입력 정정**: 리뷰본 "interface card(계약 문장 포함)만으로"는 사실과 다름 -- 생성기 출력은 표뿐이고 test-author는 spec card 네 절도 읽음(agent 정의 21-22행). import 위치·exit 2 짝 규칙을 oracle 절에도 복사.
8. **test 작성 규칙 추가**: helper `_p10b_`, test `test_p10b_` 접두사(P10 test가 `_p10_` 사용 -- P10 test worktree 실측), 피검 직접 호출(getattr·parametrize 이름 문자열 금지), 경로 비교 normcase(realpath), 합성 이름이 엔진 def 이름과 같은 문자열 금지(reachability 문자열 레지스트리 간선).
9. **V3 규칙(base에서 적용되는 것)**: 순서 P10 → P10b → 면제 묶기(A1-a "P9·P10·P10b 뒤") → 범위 정책(A1-b N2 (b)+넓힌 T6). P10b base에서는 현행 `mutate_changed.py`; `reachability._is_source`(175-177행)가 `A/` 바로 아래 *.py·run_harness만 대상이라 targets 0(P7 V3 기록 `targets []` 확인). 두 V3 card는 `_is_source`를 바꾸지 않으므로(초안 grep) 순서가 바뀌어도 같은 결론 → auditor 보충 뮤테이션 유지.
10. **미배선 절 보강**: P7과 달리 실제 저장소 `main` 호출이 영구 test가 아니라는 점과 실제 호출 증거(계약 5 (a)·(b) 실행 기록) 명시.

## 검증

- `role_paths.parse_spec_card` 통과, 절 11개 양식 순서.
- `interface_card.build`(HEAD 엔진) → 기존 함수 0행, 신규 시그니처 1행. `merge_gate.read_new_symbols`·`test_lint.read_card_symbols` → {(reg_check, check_df23)}.
- scratch: `C:/g79/m1.py`(목록·묶음 표 계산), `C:/g79/v.py`(머리·interface card) -- 작업 끝에 C:/g79 삭제.

## 남은 것(커밋 때)

- (완료, 아래) P10 판정 기록 병합 뒤 실측 1·5·7 재측정. 남은 일: interface card를 `docs/02-design/specs/20260930-df23-registry-record.interface.md`로 생성(생성기 기본 경로).

## 62ae24f 재측정 (P10 판정 기록 병합 뒤)

- 2d58fd8..62ae24f = 56b86c6(P10 test 2파일) + 62ae24f(판정 기록 2파일). 레지스트리·목록·plan·design·tests/tools·엔진·tools 변경 없음 -> 실측 1·5·7 변화 없음.
- E0 exit 0, --df23-inventory x exit 2, test_reg_check 381·424·432·444행 그대로.
- 실측 2만 갱신: P10 test 두 파일이 gate에 있음. reg_check import 없음, helper _p10_, 새 glob *.topology.json(library)·references rglob *.md -- test_reg_check_df23.py와 충돌 없음.
- 순서 문장에 base = 62ae24f 또는 그 후손 명시.
- 머리 검증·interface card 재생성 통과(기존 함수 0행, 신규 (reg_check, check_df23)). C:/g79 삭제.
