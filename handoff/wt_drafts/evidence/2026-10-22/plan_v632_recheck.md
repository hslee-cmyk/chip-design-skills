# 계획 v6.32 둘째 커밋 재검증

- 대상: `wt/plan-b69` plan/b69 `2998ddd8`(앞 커밋 `65e65e41`). `git -C <wt> diff 65e65e41 2998ddd8` -- 계획 6+/6-, history 1+/0-
- 엔진 실물: `wt/integ-it12`(엔진 코드 = `0c048327`)
- 읽기 전용. git은 `git -C`와 `set -e`로만 썼고, 쓴 파일은 이 보고서 하나다.

## 점수: 93/100 (앞 검증 87)

앞 발견 12건이 모두 의도대로 반영됐다. 새로 찾은 것은 S 하나(AST 측정 정의가 coverage의 연쇄 차집합 꼴을 못 잡는다)와 N 둘이다.

## 1. 앞 발견 대조

| 발견 | 반영 위치 | 판정 |
|---|---|---|
| G-1 | plan (11)(e): '사례 유효 조건 둘' (가) k 입력 버전 ≠ parent, (나) 평가 키 캐시를 거치지 않는 대조(`size_and_seal` 직접 또는 별도 커널 컨텍스트) + 같은 캐시 객체 아님 확인, 어기면 무효(통과로 세지 않음) | 반영됨 |
| S-1 | N3.3 '재구현 0의 측정 대상'(합집합식 + coverage 차집합 꼴, AST, 서로소 단언·parent 검사의 base 단독 읽기 제외), (11)(e) 인용 | 반영됨. 다만 AST 문언에 새 결함이 있다(R-S1) |
| S-2 | 범위 5: 바뀐 줄 수 = 감사가 변화표에서 셈. (11)(e): base↔head evals 실패 줄 차이, NFR-4 덤프(`nfr4_run_dump.py:425-426`) 기준선 갱신 = 작성자 아닌 주체 | 반영됨 |
| S-3 | 범위 5·순서 착수 조건: IT-2d 병합 head에서 착수 사실 재측정. (11)(e): '커널 블록(steps·later 구성원)과 봉인 항목 블록 각각 -- 구성은 IT-2d head 실측' | 반영됨 |
| S-4 | (11)(e): '지문 = 동작 변경, 지문 밖 결과 = 순수 리팩터링(필드별, NFR-4), 결정성 비트 동일', '엔진 소비자 0' | 반영됨 |
| N-1 | (11) 머리말 '(범위 4·5)' | 반영됨 |
| N-2 | N3.3 '(평가 키, 실패 지점)' | 반영됨 |
| N-3 | N3.3에서 커밋 해시를 지우고 history 둘째 커밋 행으로 옮김 | 반영됨 |
| N-4 | N3.3·범위 5: ss 단계 = '규칙 충족, 변경 없음', 백로그는 `passive_values`·`metrics_dc` 하나 | 반영됨. 엔진 근거는 3절 |
| N-5 | (11)(e): `block_versions` 키 =, 필드 writer ⊆ | 반영됨 |
| N-6 | (11)(e): '판정 = 변성 관계(기대값은 축소가 no-op인 parent 없는 경로)' | 반영됨 |
| N-7 | U-93 행 '…을 따른다' | 반영됨 |

## 2. (11)(e) 조건 (가) 주입 가능성 -- 12블록

조건 (가)는 θ를 바꿔 블록 k의 입력 버전을 parent와 다르게 만들 수 있는가이다. 입력 버전은 `fp_of(이름, code_hash, 투영 fp)`이고, 투영에는 READS 열과 extras가 들어간다(`core/compute_block.py:129-136`). 각 블록의 READS(`sizing/*.py`의 `READS =`)와 extras(`kernel_run.py:83-99`, `seal.py:51-60`)를 하나씩 확인했다.

| 블록 | θ 의존 경로 | 바꾸는 θ 성분 | 판정 |
|---|---|---|---|
| `dc_currents` | extras `theta_currents` | 전류 성분 | 가능 |
| `dc_lengths` | extras `theta_lengths`(+ L 동치 멤버) | L 성분 | 가능 |
| `dc_columns` | extras `column_items`(ln IDu·y·resistance) + READS `dc_L`·`dc_drop_current` | ln IDu·y·R 또는 L. MOS 전류만 바꾸면 reuse된다(`block_currents.py:7-9`의 설계 의도) | 가능(성분 선택 필요) |
| `dc_widths` | READS `dc_v`·`dc_current`·`dc_L`·`dc_ln_idu` | 아무 성분(앞 블록 출력이 바뀌면) | 가능 |
| `dc_tolerances` | READS `dc_op` | 위와 같음 | 가능 |
| `dc_seal_node_conflict` | READS `dc_path_values`·`dc_v`·`dc_tol_v` | 노드전압이 바뀌는 성분(ln IDu·y·R·L) | 가능 |
| `dc_seal_vgs_match`·`dc_seal_bulk_reverse`·`dc_seal_saturation`·`dc_seal_kvl_branch`·`dc_seal_conduction` | READS `dc_op`(+`dc_tol_v`) | 아무 성분 | 가능 |
| `dc_seal_kcl` | READS `dc_op`·`dc_current`·`dc_v`… + extras `resistances`(θ R 포함) | 아무 성분 | 가능 |

- 결론: 12블록 모두 입력 버전에 θ 의존 경로가 있다. 코드로 확인한 범위에서 조건 (가)는 주입 가능하다.
- 실제로 실패를 일으키는 주입 수단(블록 함수를 바꿔 끼우는지, 후보 실패를 내는 θ를 고르는지)과 각 회로·toy에서 입력 버전이 달라지는지 직접 실행해 보지는 않았다. **미확인**(test 역할 몫).

## 3. N-4 근거 (엔진 코드)

- `metrics/ss_evaluate.py:98`: `snapshot = sealed.snapshot`
- `:99-115`: ss 블록 실패 시 그때까지 쓴 스냅샷을 붙인다
- `search/kernel.py:126`·`:136`: `sealed`는 같은 평가의 `size_and_seal` 결과다
- parent가 있으면 `kernel_run.py:85-87` keep(base ∪ 커널 4 ∪ 봉인 항목 8)으로 파생된다. 그래서 ss writer와 `dc_seal_report`의 parent 필드는 지워진 상태에서 시작한다. 이어서 12블록과 보고서(`seal.py:75`)를 이번 평가가 모두 부른 뒤에야 `sealed`가 된다(`seal.py:89`). 낡은 DC 필드는 없다.
- 결론: ss 단계 실패 스냅샷 = base ∪ DC 12 ∪ 보고서 ∪ 실패 전에 성공한 ss 블록이다. 이미 규칙을 충족한다. 계획 문언과 history 근거는 사실과 같다.

## 4. history 삭제 0

- `git diff --numstat 65e65e41 2998ddd8` → history `1 0`
- `b4bdc125..2998ddd8` → history `2 0`
- 삭제 0이다.

## 5. 남은 발견

### S

**R-S1 AST 측정 정의가 coverage의 연쇄 차집합 꼴을 잡지 못한다**
- 위치: `plan.md:450` N3.3 "측정 = AST 검사(합집합·차집합 연산의 한쪽 피연산자가 base writer 집합이고 다른 쪽이 블록 이름 집합인 식)"
- 근거:
  - 지금 coverage 식은 `used - base_writers - called`다(`seal_versions.py:36`). AST로는 `(used - base_writers) - called`다. 어느 이항 연산도 '한쪽이 base, 다른 쪽이 블록 이름'이 아니다. 앞 연산은 used·base, 뒤 연산은 (결과)·called다.
  - 같은 문장이 "coverage의 차집합 꼴"을 측정 대상이라고 적었는데 판정 규칙은 그 꼴을 놓친다. 재구현 0이 거짓 통과할 수 있다.
  - 또 '집합이 base writer 집합인지'는 변수 이름이 아니라 출처(`base.block_versions`)로 판정해야 한다. 이 점이 적혀 있지 않다.
- 수정 제안: 측정 정의를 다음과 같이 바꾼다. "합집합·차집합 연산 사슬(괄호·연쇄 포함, 한 식 트리)의 피연산자에 base writer 집합(출처 `….block_versions` -- 대입을 거쳐도 추적)과 블록 이름 집합(`.name` 모음)이 함께 나타나는 식. red 변형 둘: (가) `used - set(base.block_versions) - {b.name …}` 연쇄 꼴 (나) 변수에 담았다가 쓰는 꼴. 넣으면 FAIL해야 한다(O-92 M1 선례)."
- 원칙 적합: 적합. 측정을 강화하는 쪽이고, graph 규칙 1·3을 실제로 지키게 한다.

### N

- **R-N1** `history.md:1421` v6.32 둘째 커밋 행의 `` `set(base_writers) | {이름}` ``에 이스케이프하지 않은 `|`가 있다. GFM 표는 코드 스팬 안의 파이프에서도 칸을 나눈다. 이 행은 칸이 6개로 갈라진다(파이프 5개, 표는 3열). `\|`로 바꾼다. 적합.
- **R-N2** (11)(e) 조건 (가)는 parent reuse만 막는다. 같은 실행의 S3 색인에 그 (k, 입력 버전)의 성공 기록이 있으면 k는 실패하지 않고 graft된다(`compute_block.py:146-149`). 예를 들어 주입 없이 같은 θ를 먼저 평가한 경우다. 블록 함수를 바꿔 끼워 주입하면 `code_hash`가 생성 때 고정이라(`compute_block.py:126`) 입력 버전도 같다. (가)를 "k가 reuse·graft되지 않고 compute 또는 실패 재연으로 실패한다"로 넓히거나, 무효 판정 문언을 '부분 스냅샷이 없으면 무효'로 덧붙인다. 적합(판정 강화, 새 저장 없음).

## 6. 미확인

- 12블록마다 실제 주입 수단과 대표 toy에서 입력 버전이 달라지는지(실행하지 않음)
- 행을 하나도 쓰지 않는 블록이 있는지(N-5 관련. ⊆로 바꿔 판정 위험은 사라짐)
- IT-2b~IT-2d가 부착 자리·커널 구성을 바꾸는지(착수 때 재측정하도록 조건이 들어갔음)
