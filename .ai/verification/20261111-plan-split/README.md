# 20261111-plan-split -- 계획서 기계적 분할 (내용 변경 0)

대상 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(분할 전 2,134,522 B, sha256 `f0b451f22a1586171b741dbb86f340e748b8145fd102f920f08f4739d0f6a7a7`, 커밋 `a6c7791b`)를 `gain-budget-gmid-sizing.parts/` 조각과 줄어든 계획서(1,097,083 B, 51%)로 나눴다. 사용자 지시(2026-11-11: 계획서 분할을 먼저, "권고대로 ... 분할해")에 따른 계획 **구조** 변경이며 규칙·정의·결정 문언은 바꾸지 않았다.

## 분할 기준
| 대상 | 조각 | 수 |
|---|---|---|
| N6 card 절(`### N6.n card <ID>`) | `parts/cards/<ID>.md` | 41 (N6.4~N6.47 중 card ID가 있는 절) |
| 제목이 `-- **철회**`·`-- **삭제**`인 card(PR-1, NB-1)와 폐기 절 N3.12 | `parts/archive/` | 3 |
| N2.1 표 행 중 3,000 B 초과(DEC 행) | `parts/decisions/<ID>.md` | 25 |
| Status 줄 | `parts/status/` | 1 |

(앞서 제안서에 적은 "삭제·폐기 표지 card 7개"는 틀렸다 -- LT-1·IT-1·PW-1a·LG-1·JC-1은 무언가를 지우는 일을 하는 살아 있는 card다. 아카이브는 제목에 `**철회**`·`**삭제**` 표지가 있는 2개와 N3.12뿐이다.)

## 검사 (`scripts/check_split.py`, 결과 `result.txt` -- 전부 PASS)
1. 분할본에서 복원한 계획서가 분할 전과 **바이트 단위로 같다**.
2. 표지(`<!-- split:... -->`) 70개와 조각 파일 70개가 일대일이다. 링크 대상이 모두 있다.
3. `##`·`###` 제목 97개가 모두 계획서에 남았다. N2.1 표 행 ID는 card·archive 조각 밖에서 모두 남았다(card 본문 안의 행 `G-2` 하나는 LT-1 조각과 함께 이동).
4. 요약 행의 표 칸 수가 4다.

## 한계
- 증거 문서·승인 기록이 쓰는 **줄 번호 인용**(예: `:1857`)은 분할 전 기준이라 어긋난다. 코드·test는 계획서 줄을 읽지 않는다(grep 확인).
- 최대 줄은 아직 76,806 B(N3.8 등). 이번 범위(분할)에서 줄 길이는 건드리지 않았다.
- 계획 v6.39.6(브랜치 `plan/v6396-fs1`, 분할 전 기준)은 이 구조 위에 `scripts/split_plan.py`를 두 판에 똑같이 적용해 얻은 조각별 차이로 다시 얹는다.

## 재현
```
python scripts/split_plan.py split <plan.md>                  # 제자리 분할
python scripts/split_plan.py rebuild <plan.md> <복원 출력>      # 되돌리기
python scripts/check_split.py <분할 전 plan.md> <분할된 plan.md>
```
