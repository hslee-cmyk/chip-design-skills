# design 40·41 v1.12.9 (B69, 계획 v6.32) 독립 검증 -- 읽기 전용

- 대상: worktree `wt/design-b69`(design/b69), `a2971fb1`(41)·`16bb8067`(40), 부모 master `559f4da2`. 차이 = 두 design 파일만(22+/22-), 계획 파일 불변(`git diff --stat 559f4da2 -- docs/01-plan` 0).
- 정본: 계획 v6.32 N3.3 '실패 평가의 부분 스냅샷'(plan:450), N3.6 4행(plan:523), N6.6 범위 5(plan:1517)·순서(plan:1521)·완료 조건 (11)(e)(plan:1523), U-93(plan:2206).
- 엔진: `wt/integ-it12/.../gmid_engine` head `56080584`(작업 트리 깨끗).
- 검증자는 파일을 하나도 고치지 않았다(이 결과 파일만 씀). 규칙 A 측정은 scratchpad 안에서 메모리 위 변형 소스로만 했다.

## 점수: 90 / 100

G 0건, S 5건, N 6건. 계획 문장 누락 없음, 고친 인용 7곳과 새 인용 전부 엔진에서 맞음, 집합 함수의 층·규칙 A·호출 자리·재연·봉인 위반 경로가 모두 실현 가능하다. 감점은 정의 칸 안에 남은 옛 문장, 소비자 문서 목록 누락, AST 측정의 연산자 범위 미정, 사례 유효 조건 (가)의 관측 수단 미정, card 귀속 표기에서 나왔다.

---

## 1. 완결성·일관성

| 계획 문장 (v6.32) | 41 | 40 | 판정 |
|---|---|---|---|
| N3.3 남기는 writer = base writer ∪ 실패 전에 성공한 블록, 실패 블록과 뒤 블록 제외 | 753 '규칙' | 499 '정의' | 맞음(용어 차이는 N-1) |
| 봉인 위반 = 봉인 보고서 블록 남김 | 753 | 499 | 맞음 |
| writer 집합·지문 = (평가 키, 실패 지점), parent 무관, parent 없는 평가 불변 | 753 | 500 | 맞음 |
| 집합 함수 하나, 부르는 자리 (i) keep (ii) coverage (iii) 부착 넷 | 753 '부르는 자리 셋' | 501·879·880 | 맞음 |
| 재구현 0의 측정 대상·AST 정의·red 변형 (가)(나)·서로소/parent 검사 제외 | 813 (e) | 931 | 맞음(측정 구현 세부는 S-3) |
| derive_child 구조 공유, 새 필드·cache·사본·writer·블록 호출 없음, 계수 변화 0 | 753 | 501 | 맞음 |
| ss 단계 이미 충족, code 변경 없음 | 753 | 499 | 맞음 |
| 범위 밖 `passive_values`·`metrics_dc` | 753 | 499 | 맞음 |
| N3.6 4행 coverage 집합은 그 함수에서 읽음 | 756 | 879 | 맞음 |
| N6.6 범위 5 착수 실측(IT-2d 병합 head 재측정, parent 없는 기존 test 지문 불변) | 753·813 | 931 | 맞음 |
| 순서(IT-2d 뒤, master 병합 전, 착수 조건 사슬) | 834 | 2092(요약) | 맞음, plan:1521 문언과 같음 |
| (11)(e) 사례 유효 조건 (가)(나)·변성 관계·봉인 위반+parent·재구현 0·계수 0·감사 변화표·NFR-4 기준선 주체 | 813 | 931 | 맞음(`nfr4_run_dump.py:425-426` 줄 번호만 생략 -- 엔진에서 425-426 evals 걷기 확인) |
| 변경 종류(O-34)·SPICE 다리 '대상 없음' (ii)·git grep 증거 | 817 | -- | 맞음 |
| U-93 필드 범위 | 753 머리 | 499 | 맞음 |

41:753·756·813·817·834와 40:499-501·879·880·931·2092 사이에 서로 어긋나는 서술은 없다. 다만 40:501 안에 고치지 않은 옛 문장이 남아 같은 칸의 새 문장과 충돌한다(S-1).

## 2. 사실 (엔진 `56080584` 재측정)

고친 인용 7곳:

| 인용 | 엔진 실측 | 판정 |
|---|---|---|
| 41:705 `block_columns.py:223-224` | 218 `def saturation_rows` 안 223 `if m in self.linear:` 224 `continue` | 맞음 |
| 41:719 `writer_plan.py:95` | 95 `def _edges(...)` | 맞음 |
| 41:719 `s2_values.py:143` | 143 `DC_WRITER_PLAN_WRITER` 행 | 맞음 |
| 41:721 `_TIE` 'IT-1 전 `writer_plan.py:104-105` -- IT-1에서 삭제' | head에 `_TIE` 0건, `14e0ca2a^`(IT-1 직전) 104-105 = `_TIE` 엣지 루프 | 맞음 |
| 41:721 `writer_plan.py:162-165` | 162 `if rank == _RES:` ~165 `BRANCH_RESISTOR_CYCLE` 정지(`= "dc_resistor_cycle"`, s2_values:93) | 맞음 |
| 41:812 `writer_plan.py:117-118` | 117 `@compute_block(...)` 118 `def dc_writer_plan` | 맞음 |
| 41:812 `seal.py:48` | 48 `def seal_dc(...)` | 맞음 |

새로 인용한 줄:

| 인용 | 실측 | 판정 |
|---|---|---|
| `compute_block.py:143` reuse 판정 | 143 `if snapshot.block_version(name) == version:` | 맞음 |
| `compute_block.py:150-156` 재연 `from_record` | 150 `find_failure` ~156 `raise entry.exc.from_record(failure)` | 맞음 |
| `kernel_run.py:56-62` `_call_block` | 56-62 | 맞음 |
| `kernel_run.py:73-74` parent 일치 검사 | 73-74 | 맞음 |
| `kernel_run.py:86-87` keep 인라인 식 | 86-87 | 맞음 |
| `seal.py:66-70`·`:71`·`:74-78`·`:87` | 봉인 항목 try/attach, `calls +=`, 보고서 try/attach, 위반 attach | 맞음 |
| `seal_versions.py:32-36` coverage 인라인 식 | 32 base_writers ~ 36 foreign | 맞음 |
| `ss_evaluate.py:113-115` | 113 except ~115 raise | 맞음 |
| `search/kernel.py:142-147` 봉인 아닌 점 | 142 `else:` ~147 | 맞음 |
| `graph_snapshot.py:39`·`:46` | docstring `block_versions`·필드 선언 | 맞음 |
| `kernel_run.py:83-97`(옛 인용, 이번에 안 고침) | steps 83·later_blocks 84, `later` 조립은 98-99 | 대체로 맞음(끝 줄이 2줄 짧음, N 수준도 아님) |

## 3. 집합 함수 `writers_in_scope(base, blocks) -> frozenset` 실현 가능성

- **층 규칙**: `_module_map.LAYERS` sizing = [0] bracket_root…, [1] …`seal_versions.py`…, [2] block_columns…, [3] `seal.py`, [4] `kernel_run.py`. 앞 층 import만 허용이므로 seal(3)·kernel_run(4) → seal_versions(1) 가능, 순환 없음. 맞음.
- **구조 규칙 A**: `structure_checks.entry_points`는 같은 파일 다른 최상위 문장이 이름을 참조하면 독립 진입점에서 뺀다. `seal_versions.py`에 `writers_in_scope`를 두고 `seal_versions`의 coverage가 부르는 변형 소스를 메모리 위에서 만들어 측정한 결과: 원본 `(['seal_versions'], [('def','seal_versions')])`, 변형도 같음. 진입점 개념 1 유지 -- **실측 확인**. 규칙 B(비공개 import)는 공개 이름이라 해당 없음.
- **blocks 입력 형태**: (i) keep = `tuple(b for b, _ in steps) + later_blocks + SEAL_ITEM_BLOCKS`(블록 객체), (ii) coverage = `(b for b, _ in calls)`, (iii) 부착 = 블록 객체 slice. 부르는 쪽에서 이름 집합을 만들 필요가 없다. 단 `seal_versions`의 서로소 (4)는 지금처럼 `called` 이름 집합을 지역에서 만든다 -- 계획이 측정 대상 밖이라 한 교집합이고 위반 아님.
- **`_call_block`의 `before`**: `_call_block`은 비공개이고 호출 자리는 `kernel_run.py:89`·`:101` 둘뿐(엔진 전체 grep). 두 루프에 인덱스를 더해 slice를 넘기면 된다. 다른 호출자 없음. 실현 가능.
- **재연 예외**: 재연은 `ComputeBlock.__call__` 안에서 `from_record`로 새 예외를 내므로(`partial` None) `_call_block`·`seal_dc`의 except가 같은 축소를 한다. 첫 부착 유지 규칙(`failure_partial.py:19`)과 충돌 없음. 실현 가능.
- **봉인 위반 경로**: `seal.py:87`의 `snapshot`은 75에서 `dc_seal_report`까지 쓴 것이고 `calls`에는 보고서 블록이 없으므로 `calls`의 블록 + `dc_seal_report`를 넘겨야 한다 -- design 41:753·40:501·880 모두 그렇게 적었다. 맞음.
- **base None**: `writers_in_scope`의 `TypeError`는 design이 정했고 `seal_versions.py:17-18`과 같은 형태다. `_call_block`은 `ctx.base`(None일 수 없음)를 넘긴다. 맞음.
- **parent 없는 경우 불변의 근거**: 축소가 no-op이려면 `ctx.base`의 모든 필드 writer가 `ctx.base.block_versions` 키여야 한다. parent 없는 평가가 봉인 4 coverage를 통과한다는 기존 단언(L11 (a))이 이를 보장한다. fp는 내용 지문이라(`graph_snapshot.py:40-41`) 새 객체여도 같다. B-T19 (4)의 `r.partial.fp == entered[0].fp` 단언(`tests/search/test_kernel.py`)은 parent 없는 경로라 그대로 성립한다.
- **레지스트리**: §2에 같은 개념 행 없음, 엔진 `def` grep에도 같은 집합을 내는 함수 없음. 맞음.

## 4. (11)(e)·L11 (e) 판정 가능성

- **실패 주입**: 기존 B-T19 (4)가 `ComputeBlock.__call__`을 클래스 수준에서 감싸 대상 블록에서 `SealViolationError.from_record(rec)`를 내는 방식을 이미 쓴다. 커널 블록·봉인 항목 블록 각각에 똑같이 쓸 수 있다.
- **(가)**: 블록 k가 reuse·graft되지 않아야 한다. parent는 θ0, 실패 평가는 θ1(k의 입력이 바뀌는 θ)로 두면 만족한다. 다만 `__call__`을 감싸는 주입은 reuse 판정 앞에서 예외를 내므로 '주입이 없었다면 reuse·graft였는가'를 계수로 볼 수 없다(S-4).
- **(나)**: `size_and_seal`을 직접 부르면 평가 키 캐시를 거치지 않는다. 같은 `KernelContext`면 앞 블록은 graft, k는 실패 색인 재연(`from_record`)으로 들어오는데, 둘 다 같은 축소 자리를 지나므로 대조로 유효하다.
- **변성 관계**: fp는 내용 지문이다. parent 경로의 축소 결과는 base 필드(parent 검사로 같은 버전)와 앞 블록 필드(reuse·graft·compute 모두 같은 입력 버전 → 같은 값)뿐이다. 그래서 대조 fp와 같아야 한다는 관계가 성립한다. 실패 줄 `snapshot_fp`는 `search/kernel.py:89-90`이 `partial.fp`로 쓴다.
- **AST red 변형 둘**: `ast`로 함수 안 대입을 따라가며 `block_versions` 출처를 추적하면 (가) `(used - bw) - called`, (나) `bw = set(s.block_versions); bw | names` 모두 잡을 수 있다. 지금 엔진에서 `block_versions`를 집합 연산에 쓰는 곳은 `seal_versions.py:32-36`·`kernel_run.py:86` 두 곳뿐이다(`kernel_run.py:72`는 `any` 비교, `layout/run.py:103-104`는 dict 필터라 대상 밖). 변경 뒤 오탐 없이 0을 셀 수 있다. 연산자 범위만 정하면 된다(S-3).
- **계수 변화 0**: 축소는 `derive_child`뿐이고 블록 호출이 없으므로 G-10 계수에 영향이 없다.

## 5. 원칙 점검

| 원칙 | 판정 |
|---|---|
| graph 단일 정본(새 cache·memo·sctx 슬롯·EvalResult 칸·값 사본) | 위반 없음. 반환 frozenset은 호출마다 만들고 버리는 메타데이터라 저장되지 않는다. `partial` 칸은 기존 칸이고 축소본은 구조 공유다 |
| 둘째 writer·둘째 생산자 | 없음. 인라인 식 둘을 함수 하나로 모으고 셋째 사본을 막는다 |
| 이름 집합 사본 | 없음. 블록 객체를 넘기고 `.name`은 함수 안에서 읽는다 |
| fail-closed | base None `TypeError`, 낡은 필드 제거('없음'이 '낡은 값'보다 안전) |
| 상수 발명 | 없음 |
| 회로 이름 | 없음 |
| as-built 결정 | 없음. design이 정한 것은 계획이 design에 맡긴 이름·자리·서명과 `before` 전달 방식, base None 형태뿐이다 |
| 만들면 배선 | 됨. 옛 인라인 식 둘의 삭제가 명시됨(41:753 '두 인라인 식을 같은 변경에서 지우며', 40:879 '옛 인라인 차집합식 삭제', 40:880 '옛 인라인 합집합식 삭제'), 부르는 자리 넷이 모두 지정됨 |
| 원래 취지와 다름 표시 | v1.12.8의 '원래 취지와 다름(작음)·B69'를 해소로 표시했다(41:753). 새 이탈 없음 |

---

## G (결함)

없음.

## S (권고)

**S-1. 40:501 '전달' 칸 안에 옛 문장이 남아 새 규칙과 충돌**
- 위치: 40:501 "재연한 예외(§2.4.4 '실패 재연')는 … 바깥 `run_kernel`이 그 블록에 들어간 스냅샷을 붙인다(계산했을 때와 같은 부분 스냅샷)". 같은 칸 앞부분 "`seal_dc`는 스스로 내는 `SealViolationError`에 보고서를 쓴 스냅샷을 붙인 뒤 낸다"와 "스냅샷을 쥔 쪽 -- … `seal_dc`(보고서를 쓴 스냅샷)"도 같은 문제다(봉인 항목 블록 실패 부착이 빠져 있다).
- 근거: 같은 칸 뒤의 **줄인 뒤 붙임**은 "들어간 스냅샷을 그대로 붙이지 않고"라고 정한다. 이 칸이 §2.4.7 전달의 정본인데 한 칸 안에 반대 서술이 둘 있다.
- 수정 제안: 옛 문장을 그 자리에서 고친다. "…바깥 `run_kernel`이 그 블록에 들어간 스냅샷을 줄여(아래 '줄인 뒤 붙임') 붙인다", "`seal_dc`(봉인 항목 블록·보고서 블록 실패, 위반)". 줄 수는 늘지 않는다. [원칙 적합: 정의 하나·문서 단일 정본]

**S-2. 부분 스냅샷 정의를 옮겨 적은 엔진 문서·docstring 소비자가 변경 목록에 없음**
- 위치: 40:880 IT-2e 추가, 41:753, 41 §4.7-6.
- 근거(엔진 grep): `E/search/CONTRACT.md:458` "DC 블록 실패 = 그 블록에 들어간 스냅샷", `E/search/search_values.py:163-164` `EvalResult.partial` docstring(같은 문언), `E/sizing/CONTRACT.md:117-119`(run_kernel·seal_dc 부착 문언), `E/sizing/kernel_run.py:10-11` 머리 설명, `seal.py:69` 주석. 바뀐 뒤에는 parent 경로에서 이 문언들이 거짓이 된다. 계획 쪽 '삭제 전 계획서 소비자 grep' 원칙과 같은 성격이다.
- 수정 제안: 40:880 또는 41:753 끝에 "같은 변경에서 고치는 문서 자리: search CONTRACT 3.10 `partial` 문언·`search_values.EvalResult` docstring·sizing CONTRACT 부분 스냅샷 문단·`kernel_run`/`seal` 머리 설명"을 한 구절로 더한다(줄 추가 없이 기존 칸 끝에 붙임). [원칙 적합: 단일 정본, 소비자 전수]

**S-3. AST '재구현 0' 검사의 연산자 범위와 '블록 이름 집합' 인식 규칙이 정해지지 않음**
- 위치: 41:813 (e) '재구현 0', 40:931.
- 근거: 계획과 design 모두 "합집합·차집합 연산 사슬"이라고만 적었다. `BinOp`(`|`, `-`) 말고 `|=`/`-=`(AugAssign), `.union()`/`.difference()`/`.update()` 메서드 호출, `set(a) | …` 같은 꼴을 세는지 정해지지 않아 우회가 열려 있다. '블록 이름 집합'을 어떻게 알아보는지(`.name` comprehension인지, 그 변수인지)도 없다.
- 수정 제안: design에 측정 구현을 한 구절로 정한다. "대상 연산 = BinOp `|`·`-`, AugAssign `|=`·`-=`, set 메서드 `union`·`difference`·`update`·`difference_update`; 한 피연산자의 출처가 `block_versions`(함수 안 대입 추적)이면 다른 피연산자 종류와 상관없이 정의 자리 밖은 위반". 이것은 계획 정의를 넓힌 상위 집합이다. 계획이 센 위반을 모두 잡고 오탐은 지금 엔진에서 0이다(§4 실측). [원칙 적합: fail-closed. 계획 정의보다 넓으므로 '계획과 다름' 여부를 오케스트레이터가 판단해야 한다. 계획 문언 '함께 나타나는 식'의 구현 세부로 보면 design 몫이다]

**S-4. 사례 유효 조건 (가)를 무엇으로 관측하는지 없음**
- 위치: 41:813 (e) (가), 40:931.
- 근거: 기존 주입 방식(B-T19 (4), `ComputeBlock.__call__` 감쌈)은 reuse·graft 판정 앞에서 예외를 내므로 계수(`RunCounters`)에 k의 outcome이 남지 않는다. 그러면 '주입한 θ에서 k가 reuse·graft가 아님'을 직접 보일 수 없다.
- 수정 제안: (가)의 관측을 정한다. 예: "k에 들어간 스냅샷에서 `k.input_version(snapshot, *extras) != parent.snapshot.block_version(k.name)`이고 그 실행 색인 `donors.find(k.name, '*', 그 버전)`이 None". 또는 주입 자리를 `block.fn`(계산 직전, 계수 'compute' 기록 뒤)으로 두어 outcome을 계수로 읽는다. [원칙 적합: 게이트가 실제로 거부함을 먼저 확인. test 주체의 독립성은 그대로]

**S-5. IT-2e 내용이 card B 귀속 칸에 들어가 card 표기가 어긋남**
- 위치: 40:879·880(§11 파일 표 card 열 = `B`), 40:931(card B 행 완료 조건·test 칸에 IT-2e test 목록).
- 근거: card B는 병합된 card다. IT-2e 판정 단위는 41:834와 40:2092(IT 행)인데, 40:931의 card B 완료 조건 칸에 IT-2e test가 섞여 있어 감사가 card 귀속을 헷갈릴 수 있다.
- 수정 제안: 879·880 card 열을 `B, IT-2e`로 적는다. 931의 IT-2e 문단은 2092 IT 행 test 칸으로 옮기고 931에는 "IT-2e 추가 test는 IT 행" 지시만 남긴다(줄 수 불변). [원칙 적합: 판정 단위 추적성]

## N (사소)

- **N-1** 용어 차이: 계획은 '실패 전에 **성공한** 블록', design(41:753·40:499)은 '실패 전에 **부른** 블록(reuse·graft·compute 어느 쪽이든)'이라고 적었다. 첫 실패에서 예외로 끝나므로 두 집합은 같다. 41:753에 "(= 계획 '성공한 블록' -- 앞 블록은 모두 성공)"을 덧붙이면 대조가 쉬워진다. [원칙 적합]
- **N-2** `writers_in_scope`가 41 §4.7-7 'test interface' 공개 진입점 목록(41:799)에 없다. 서명은 4.7-3c에만 있다. 또 base None `TypeError` test가 40:931에는 있지만 41 L11 (e)에는 없다. 4.7-7 머리 목록과 L11 (e)에 한 구절씩 더하기를 권한다. [원칙 적합]
- **N-3** 봉인 보고서 블록 실패 + parent 사례는 (11)(e) 사례에 없다. 축소가 no-op인 경로(41:753 '열두 블록을 모두 부른 뒤라 낡은 필드가 없고')라 계획이 요구하지 않았으므로 결함은 아니다. 원하면 같은 변성 관계로 한 건 더한다. [원칙 적합, 선택]
- **N-4** `before` slice를 블록 호출마다 미리 만든다(41:753). 평가당 4회, 원소 5개 이하라 비용은 무시할 만하다. 실패 경로에서만 slice를 만들려면 `_call_block`에 (호출 목록, 인덱스)를 넘기는 방법이 있지만, 지금 설계도 '새 누적 변수·저장 없음'을 지키므로 바꿀 필요는 없다. [선택]
- **N-5** 줄 수 유지 방침의 부작용: 41:753 한 bullet이 약 1만 자다(keep 정의·O-94 정오·부분 스냅샷 사실·규칙·집합 함수·부르는 자리·재연·범위 밖·dc_seal_report·근거·derive_child 메서드). 다른 문서가 '41 §4.7-3c '실패 평가의 부분 스냅샷 파생''으로 가리키는 대상이 긴 문단 안의 굵은 구절이라 앵커가 약하다. 40:501·931도 같다. 줄 추가 금지가 아니라면 '실패 평가의 부분 스냅샷 파생'을 4.7-3c 안의 별도 bullet로 떼기를 권한다. 줄 수 정책이 우선이면 그대로 둔다. [사소]
- **N-6** 41:813 (e) 'AST 검사'의 test 파일 자리(구조 test인지 `tests/sizing`인지)가 정해지지 않았다. 기존 L11 (a)~(d)도 파일을 정하지 않았으므로 관행과는 맞다. 규칙 H 자리는 test 주체가 정한다는 점만 확인해 둔다. [사소]

## 미확인

- IT-2d 병합 head의 커널 블록 구성·줄 번호. design이 착수 실측으로 미뤘고 이 검증은 `56080584`에서만 쟀다.
- design↔계획 gap 분석(계획 순서상 별도 단계)은 이 검증의 범위 밖이다. 위 1절 대조표가 그 일부를 대신하지만 독립 gap 판정은 아니다.
- 실제 test 실행(B-T19 불변 등)은 하지 않았다(읽기 전용). 불변 판단은 코드 읽기와 fp 정의에 근거한다.
