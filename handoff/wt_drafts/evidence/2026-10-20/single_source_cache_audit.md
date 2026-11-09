# graph 단일 정본 위반 감사 -- 새 캐시·사본·두 번째 생산자 (읽기 전용, 2026-10-20)

계기: design 40/41 v1.12 초안(design/it12-window `1beeef51`)이 다듬은 결과용 새 칸 `sctx.front_cache`를 만들었고, 사용자가 "cache는 graph정본인데 새로 cache를 왜 만들지?"라고 지적했다.
기준 규칙: 계획 NFR-2·DEC-83·WP-23 (1)(2)·N3.3 정본 원칙·N3.5 '캐시 위치와 상한'(master `2e707d5d` plan 186·282·352·419·473행), design 40 §2.4.
graph 밖에 둘 수 있는 것은 셋뿐이다: (a) LUT memo(+LUT 파생표 디스크 캐시) (b) S3 기록과 실행 수명 메모리 색인(평가 키·실패 캐시·블록 결과 색인 (블록, 분할, 입력 버전)) (c) 실행 계수.

## 0. 감사한 판(읽는 동안 브랜치 머리가 움직였다)

| ref | 머리 | 비고 |
|---|---|---|
| master | `2e707d5d` | plan 6건, design 00/40/41/42·oracle·offset-trim·offset-strategy |
| design/it12-window | `1beeef51` → **`112e9fc1`**(감사 중 새 커밋 "W4 front_cache 철회") | 판정은 `112e9fc1` 기준 |
| design/oracle-eo1 | `5d6e7073` → `4d003b33`(v0.3.2 Status 줄만) | |
| plan/gb-v621 | `bb545b92` | |
| plan/oracle-v0611 | `ade94756` | |

방법: 각 ref를 `git -C … show`로 꺼내 캐시·memo·보관·사본·재계산 어휘를 grep한 뒤 문맥을 읽었다. 엔진 코드는 `git grep`만 했다. 저장소 상태는 바꾸지 않았다.

## 1. 발견 사항

### F1 [차단] plan/gb-v621 -- "컨덕턴스 조립·인수분해 캐시 공유"(새 graph 밖 캐시, `front_cache`와 같은 종류)

- 문서: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` @ `plan/gb-v621` `bb545b92`. master에는 이 문장이 없다(`캐시 하나를 공유` master 0건, v6.21 1건). v6.21에서 새로 들어왔다.
- N3.8 '엔진 쪽 계산 자리' 565행: "봉인점 컨덕턴스 계의 조립·인수분해는 기존 조립 자리(`E/metrics/offset_analysis.py:69`·`E/metrics/offset_systematic.py:46`·`E/metrics/block_residual.py:73` -- 모두 `nodal_factor(conductance_matrix(ss.circuit, size), fixed)`)와 **캐시 하나를 공유한다**(넷째 조립 금지 -- 재계산 원칙)."
- 1476행 IT-2 범위 1: "컨덕턴스 조립·인수분해 캐시는 N3.8 '엔진 쪽 계산 자리'의 기존 조립 자리와 공유한다".
- 1484행 완료 조건 (c): "같은 평가에서 기존 조립 자리와 캐시를 공유(G-10 계수·WP-10 중복 인자 계측)".
- 318행 O-58 행 요약: "컨덕턴스 인수분해 캐시 공유".
- 어기는 규칙: NFR-2·N3.3 정본 원칙 "graph 밖에 두는 것은 셋뿐", WP-23 (1)(2)(모듈 수준 dict·인스턴스 속성 캐시 금지, graph 밖은 DEC-83의 셋만), DEC-83 "별도 캐시 레지스트리에 설계 값을 두지 않는다". 봉인점 컨덕턴스 계와 그 LU 분해는 봉인 스냅샷(`ss.circuit`)에서 나오는 설계 값이다. LUT memo(LUT와 숫자 인자만의 순수 함수)도 S3 색인도 실행 계수도 아니다. 계획이 저장 자리를 graph 필드로 정하지 않고 '캐시'라고만 적었으므로, design·구현은 `sctx.front_cache` 같은 새 칸으로 갈 수밖에 없다.
- 함께 드러난 as-built 사실(두 번째·세 번째 생산자): 계획 문장 그대로라면 엔진은 지금 같은 계를 세 자리에서 따로 조립·분해한다(위 세 파일:줄. 이 감사는 `E/metrics/_helpers_nodal.py:36-46` `nodal_factor`(`scipy.linalg.lu_factor`)까지만 grep으로 확인했고, 세 호출 자리 줄 번호는 계획 문장을 인용한 것이다).
- 원칙에 맞는 최소 수정(계획 변경 필요 -- S-7, IT-2 design 전에): N3.3 `ss` 층에 필드 하나를 둔다(가칭 `graph/ss: nodal_factor` = 봉인점 컨덕턴스 계 + 분해, writer 블록 하나, 입력 버전 = 그 `ss` 필드). 측정 구성 블록과 기존 세 자리는 그 필드를 READS로 읽고 직접 조립하지 않는다. 재사용은 graph 규칙(같은 스냅샷이면 reuse, 다른 lineage면 S3 블록 결과 색인 graft)만 쓴다. 완료 조건 (c)는 "그 필드 writer 하나(`git grep nodal_factor(conductance_matrix` = writer 파일 1곳) + 같은 입력 버전 재계산 0(G-10)"으로 바꾼다. 세 기존 자리의 읽기 전환은 같은 변경에서 한다(만들면 배선). 필드 형식(LU 튜플을 frozen 값으로 담을지)은 design 몫이다.

### F2 [해소 확인 + 중간 1건] design/it12-window -- `sctx.front_cache` 철회 뒤 남은 것

- `112e9fc1`에서 `sctx.front_cache`는 지워졌다(41 본문 남은 언급은 761행 K3 (d) "`git grep` -- `front_cache` 0" 하나뿐). 41 §4.7-4 5(729행)는 "재사용 = graph 규칙 하나, 새 캐시 없음 … 재사용 자리는 실행 수명 S3 색인(`S3Index(Donors)`, 키 = (writer, part, input_version)) 하나"로 바뀌었고, 40 553행도 "새 캐시 없음"이다. 규칙에 맞다.
- 공백 처리도 원칙에 맞다(41 730행): 커널 밖 writer 필드(`dc_window_refine`·`metrics_icm_front`)가 parent 스냅샷에 실리면 봉인 4(`E/sizing/seal_versions.py:14-27`)가 잡지 못한다는 공백을 "계획 먼저, S-7"로 올렸다. **계획 쪽 후속이 필요하다**: v6.21에는 이 항목이 없다. 사용자 결정 대상으로 올려야 한다(봉인 4 범위를 스냅샷의 모든 writer로 넓히기, 또는 parent 재사용 때 커널 writer 밖 필드 제거).
- [중간] 41 761행 K3 (b) "`sctx.cache`의 모든 값의 스냅샷에도 그 필드가 없음"과 729·730행 "`sctx.cache`(… as-built 그대로)에는 넣지 않는다": 단언이 없어질 칸에 묶여 있다. 그 칸은 40 §2.4.5가 S3 메모리 색인으로 바꾸기로 한 as-built 칸이다(40 370·523·573행, 42 D-GR5 DEV). 그 칸을 이름으로 묶은 test는 U17 ② 때 대상 소멸이나 test 재작성을 부른다. 원칙상 위반은 아니다(새 칸을 만들지 않음). 수정: K3 (b)를 "커널 평가 결과(S3 색인 평가 키 부분 -- U17 ② 전까지 as-built `sctx.cache`)"로 적는다.

### F3 [중간] offset-strategy design -- `EvalResult`에 새 값 칸

- 문서: `docs/02-design/features/offset-strategy.design.md` @ master, 123행(합성 행 표): "보고 칸 | 행과 함께 (v, L)을 `EvalResult`의 합성 행 보고 칸에 둔다(결과 JSON이 옮겨 쓴다, §8. 다시 계산하지 않는다, OB-13)".
- 어기는 규칙: design 40 §2.4.7·42 D-GR9 "값 사본 제거(`SsEvaluation`·`EvalResult`·`LayoutResult`)". 40 2086행 지울 것 목록에 "`EvalResult`의 값 칸"이 있다. DEC-83에 따르면 metric·제약 값은 graph 필드다. 결과 객체에 값 칸을 새로 두면 graph 밖에 사본이 하나 더 생긴다(그 값이 graph 행에서 나온 것이면 사본이고, 행 계산 중에만 생긴 것이면 graph에 없는 설계 값이다).
- 최소 수정(design만 고치면 된다. 계획 변경 없음): (v, L)을 합성 행을 쓰는 블록의 graph 필드(봉인 스냅샷의 제약 행 필드, writer 하나)로 둔다. 결과 JSON은 그 스냅샷 필드를 읽는다(재계산 0은 그대로). (v, L)이 이미 제약 행 필드 안에 있다면 '보고 칸' 행은 지우고 참조로 적는다.

### F4 [중간] as-built graph 밖 저장소를 사실로 인용하는 새 design·계획 문장(부채는 이미 등록됨)

as-built 칸(master 엔진 코드, grep):
- `sctx.cache` = `{}` `E/search/search_context.py:58`, `computed_keys` `:59`·`E/search/kernel.py:114-116`
- `sctx.cell_floors` `E/search/search_context.py:67`("[r8] `cell_floor`의 (kind, w_key, L 칸) -> 칸 정점 하한 등")
- `sctx.ach`·`sctx.start`·`sctx.structure`·`sctx.noise_decl` 객체 사본(40 163·537-544행 DEV)
- `sctx.spec_passive_values`, 그리고 `kernel.py:146-150` 수동소자 규칙 사본(40 493행, 42 D-GR8 MISS)

이 칸들은 모두 지울 대상으로 이미 등록돼 있다(U17 ② = 40 2086행, GC-7 = graph-consumption 769·795행 "`sctx.cell_floors` 캐시는 허용 저장소가 아니라 지운다"). 그래서 위반 건수로 세지 않는다. 다만 다음 새 문장은 그 칸을 정본처럼 읽는 경로로 적었다.
- offset-strategy design 100·371행, offset-strategy plan 469행: `sctx.cache.values()`·`sctx.cache`를 읽는 경로(`nfr4_run_dump.py:401-421`)를 실행 계획 결과의 읽기 경로로 인용한다. 괄호 안에 "card B 뒤 `S3Index` 평가 키 부분"이 있어 정합은 유지된다. [낮음] 표기만 "S3 색인 평가 키 부분(as-built `sctx.cache`)" 순서로 바꾸기를 권한다.
- [낮음, 낡은 인용] 40 370행 "`local_seal_memo`(:88, …)"와 42 267행 "`search_context.py:65-89`(cache·cell_floors·local_seal_memo 등)": master 코드에서 `search_context.py`·`kernel.py`에 `local_seal_memo`가 0건이고 `cache`는 :58에 있다. 줄 번호와 대상이 master와 맞지 않는다. 다음 design 개정 때 다시 재서 고친다.

### F5 [낮음] 레이아웃 READS 정정 문구의 LUT memo 인자

40 v1.11.2 머리말(16행)의 `ly_slice_density` "추가 인자 LUT memo만 `_LutHandle(memo)`"는 LUT memo 예외(a) 안이다. 위반이 아니다. 기록만 남긴다.

## 2. 확인했고 위반이 아닌 것(같은 종류로 의심했던 곳)

- design 41 v1.12 `WindowEnd(x, v, reason)`의 `v`("끝 풀이 해의 그 포트 전압 보관"): 끝 풀이라는 다른 풀이의 값을 graph 필드(`node.dc_window_def_refined`)에 담은 것이다. `node.dc_v`의 사본이 아니다. 뿌리 아닌 포트 창은 같은 `input_windows` 해의 감도로 옮기고 κ·별도 노드 풀이를 하지 않는다(M3, 766행).
- plan v6.21 O-58 S-1의 창 필드 셋(θ 프레임 `node.dc_window`, 측정 구성 판정 창, 다듬은 창 `node.dc_window_def_refined`): 정의·판정 여유·정밀도가 다른 양이다. 같은 양을 두 칸에 담은 것이 아니다(N3.8 '창 필드는 정의와 판정 여유로 나눈다'). writer는 각각 하나다(1484행 (b)).
- plan v6.21 1572행 출력 스윙 KVL 고정 = "IT-2 측정 구성 블록의 KCL 1차 감도 연립 재사용 -- 사본 금지": 단일 생산자 규칙에 맞다. 다만 F1이 고쳐지기 전에는 그 연립의 분해도 '캐시 공유'에 기대게 된다.
- headroom-chain plan 262행·G-4(672행): 층 0 거르기 판정을 "기존 S3 평가 기록의 항목"에 싣는다("새 캐시 아님"). 실행 수명 S3 메모리 색인(b) 안이다. design G-4가 그 자리를 평가 키 색인 항목으로 정하면 규칙에 맞다.
- headroom-chain 361·533행, graph-consumption 494행, offset-strategy design 332·735행(OB-30 "pipeline 수준 캐시 없이 블록 결과 색인만"): 모두 "새 캐시는 만들지 않는다"고 적었고 규칙에 맞다.
- offset-trim plan 122·454행, D-24 안 B: 반복을 실행 계획 안의 변형으로 두고 단계 A·S0·블록 결과 색인을 공유한다. 실행 수명 색인이고 실행 사이 재사용이 아니다(T-35).
- offset-strategy S-14 DS-1 (다): `S3Index` 하나를 공유하고 평가 키에 `constraint_set_fp`(문턱 값 지문)를 넣는다. 두 번째 색인을 만들지 않는다.
- oracle design v0.3.2: DV-6 (가) I_off 보간 사본 기각(O-50 G5, 1545·1574행 삭제). `ZOOM_ROUNDS` 정본 한 곳("2단계는 사본을 두지 않음", 1022행). `--cache-dir`·캐시 키(§9, B-35)는 오라클 자기 시뮬레이션 결과 캐시라 엔진 graph 범위 밖이다. `power_dc_w` "엔진 `supply.py:69`와 같은 값"(1760행)은 독립 측정이다(아래 예외 3).
- plan/oracle-v0611: T-1 triode 경계 여유 = gain-budget N3.8 인용, "이 계획은 따로 정하지 않는다"(421행). 정의 사본이 없다.

## 3. 승인된 예외(위반으로 세지 않음)

| 예외 | 결정 | 이 감사에서 본 자리 | 승인 넘어섬 |
|---|---|---|---|
| LUT memo·LUT 파생표 디스크 캐시 | U-87(2026-10-15), NFR-2 (a), N3.5 | 40 §2.4.6, `_LutHandle(memo)` | 없음 |
| `ly_point` = `dc_op` 사본 부채 | O-27, card LI-1 | 40 v1.11.2 머리말 | 없음 |
| 엔진·오라클 독립(오라클의 자기 기록은 사본 아님) | oracle NFR-P3, X-D5(O-11) | oracle `pdk_root` 해석 따로 구현, `power_dc_w` | 없음(G5로 LUT 보간 사본은 오히려 없앰) |
| 블록 안 local memo(수명 = 블록 호출 하나, 상한 있음, 블록 밖으로 안 나감) | O-15 (E) | graph-consumption plan 132행 | 없음 |
| S3 메모리 색인(평가 키·실패 캐시·블록 결과 색인), 실행 계수 | 2026-10-12 G, 2026-10-15 X-1 | 41 §4.7-4 5 graft | 없음 |
| `LocalSeal.snapshot_fragment` `DeviceOp` 사본 부채 | O-36 (1), card LA-1, GC-1 부채 목록 | graph-consumption 274·519행 | 없음(부채 목록 증가 금지 조건 있음) |
| S1 관계 사본(`rel_equal_vgs`·`rel_l_class`·`rel_matching_ratio`·`rel_vds_eq_vgs`) | GC-7, 항목별 삭제 승인 대기(U-G3) | graph-consumption 320-324행 | 없음 |

## 4. 요약

| # | 등급 | 자리 | 처리 |
|---|---|---|---|
| F1 | 차단 | plan/gb-v621 565·1476·1484(c)·318행 "인수분해 캐시 공유" | 계획 개정(S-7): `ss` 층 필드 하나 + writer 하나, 기존 세 자리 읽기 전환 |
| F2 | 해소 + 중간 | it12-window `112e9fc1` 41 761행 K3 (b) `sctx.cache` 결속; parent 무효화 공백의 계획 항목 없음 | K3 (b) 문구 수정; 공백을 계획 결정 항목으로 올림 |
| F3 | 중간 | offset-strategy design 123행 `EvalResult` 합성 행 보고 칸 | graph 필드로 두고 결과 JSON이 스냅샷을 읽음 |
| F4 | 낮음 | `sctx.cache` 인용 표기(OS design 100·371, OS plan 469); 40 370·42 267 낡은 줄 번호 | 표기·재측정 |
| F5 | 기록 | 40 머리말 LUT memo 인자 | 예외 (a) 안 |

새 graph 밖 캐시가 남아 있는 곳은 F1 하나다(`front_cache`는 철회됐다). F1이 `front_cache`와 같은 종류다. IT-2 design이 그 문장을 따르면 같은 지적이 다시 나온다. 그러니 v6.21 독립 검증·승인 전에 고쳐야 한다.
