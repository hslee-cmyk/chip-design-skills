# Consistency Map

## 사용법

SKILL.md 원칙 수정 시:
1. 아래 맵에서 해당 원칙의 반영 위치 확인
2. 모든 반영 위치를 함께 업데이트
3. SKILL.md 내부 요약 (섹션 10 체크리스트)도 확인
4. **수정 후: `../skill-validation-prompt.md` 절차로 일관성 검증**

## 원칙별 반영 위치

| 원칙 | SKILL.md 섹션 | SKILL.md 내부 요약 | reference 반영 위치 |
|------|--------------|-------------------|-------------------|
| **필수 규칙 테이블** | 1. Design Rules | 섹션10 합성 | review-checklist > 필수/권장, synthesis-check > 체크리스트 |
| Always 블록 유연성 | 2. 분리 체계 | 섹션10 코딩스타일 | review-checklist > Always 블록 분리, always-block-patterns > 전체 |
| CDC 방향 구분 (Slow→Fast: 2FF/Pulse, Fast→Slow: Handshake 또는 2FF 장기유지) | 1. CDC 테이블+유지조건 | 섹션10 합성 | review-checklist > CDC, cdc-patterns > 핵심원칙/체크리스트, synthesis-check > 체크리스트 |
| 리셋 정책 | 1. Reset 패턴 | 섹션10 합성/타이밍 | review-checklist > 리셋 정책/Data-Valid, synthesis-check > 리셋 정책/체크리스트, cycle-analysis > 체크리스트 |
| Latch 방지 (기본값 할당 또는 if/case 완전성) | 1. 필수 규칙, 7. FSM | 섹션10 합성 | review-checklist > Latch(체크리스트+포인터), synthesis-check > Latch/체크리스트(상세 원본), fsm-patterns > 체크리스트 |
| Blocking 규칙 (ff: <=, comb: =) | 1. 필수 규칙, 2. 분리 원칙 ✓ | 섹션10 합성 | review-checklist > Blocking, synthesis-check > Blocking |
| 단일 할당 원칙 (동일 신호 여러 always 금지) | 1. 필수 규칙, 2. 분리 원칙 ✓ | 섹션10 코딩스타일 | review-checklist > Always 필수, synthesis-check > 멀티드라이버 |
| 네이밍 (Prefix) | 4. Signal Naming | 섹션10 코딩스타일 | review-checklist > 네이밍, naming-examples > 전체/체크리스트 |
| 네이밍 (Top Wire) | 6. Top Integration | - | review-checklist > 네이밍, naming-examples > Top Integration/체크리스트 |
| 네이밍 (BSC) | 4. BSC Naming | - | review-checklist > 네이밍, naming-examples > BSC 예시/체크리스트 |
| 네이밍 (Clock/Reset) | 4. Clock/Reset | - | review-checklist > 네이밍, naming-examples > 체크리스트 |
| 모듈 코드 구조 (3영역 분리, 선언-Body 대응) | 4. 모듈 코드 구조 | 섹션10 코딩스타일 | — |
| FSM 작성 규칙 | 7. FSM(규칙표+bullet+포인터) | 섹션10 기능 | review-checklist > FSM, fsm-patterns > 전체/체크리스트/사이클 다이어그램/비교 테이블(상세 원본) |
| FSM 기본값 | 7. FSM | - | review-checklist > FSM, fsm-patterns > 체크리스트, synthesis-check > Latch |
| 사이클 분석 | 3. Cycle Analysis | 섹션10 타이밍 | review-checklist > 사이클/Data-Valid, cycle-analysis > 전체 |
| Coverage 목표 | 8. Verification | - | review-checklist > 시뮬레이션 |
| Coverage 분류 (Code/Functional/Assertion) | 8. Verification > Coverage 분류 | - | methodology §1, §2, §3 |
| Observation 기반 coverage | - | - | methodology §6 |
| Check 통과 시 유효 | - | - | methodology §6 |
| Code ≠ Functional 상호보완 | - | - | methodology §1, §2 |
| 명시적 bin 설계 | - | - | covergroup-patterns §6, §7 |
| Cross ignore_bins | - | - | covergroup-patterns §3.2 |
| Spec → Testplan → Coverage | - | - | methodology §4, §5, §6 |
| Coverage Closure | - | - | methodology §7 |
| Covergroup 문법 패턴 | 8. Verification (포인터만) | - | covergroup-patterns 전체 |
| Assertion Coverage 패턴 | 8. Verification > SVA | - | covergroup-patterns §5 |
| Coverage Options | - | - | covergroup-patterns §4 |
| Coverage 실전 예제 | - | - | coverage-examples 전체 |
| Coverage Space 2×2 분류 | - | - | methodology §1 > Coverage Space |
| Bit-Width Safety (unsized localparam, max value 검증) | 1. Design Rules > Bit-Width(rules box+포인터) | 섹션10 합성 | synthesis-check > Bit-Width Safety(상세 원본) |
| $clog2 vs custom log2 | 1. Design Rules > Bit-Width(포인터만) | - | synthesis-check > $clog2 vs custom log2(상세 원본) |
| 코드 생성 Bit-Width 검증 단계 | 9. 코드 생성 워크플로우 Step 4.5 | - | synthesis-check > 검증 체크리스트 |
| Verilator Lint (OSS CAD Suite, verilator 5.047, Warning 유형, 억제) | 11. Verilator Lint | - | verilator-guide > 전체 |
| H/W 리소스 최소화 (인스턴스 재사용, FSM 최소 상태) | 1. Design Rules > Resource | 섹션10 합성 | review-checklist > 리소스, synthesis-check > 체크리스트 |
| Combinational Depth 최적화 (타이밍) | 1. Design Rules > Timing | 섹션10 타이밍 | review-checklist > 타이밍, synthesis-check > 체크리스트 |
| 래칭 데이터 보존 (Data Lifecycle) | 1. Design Rules > DataLife | 섹션10 기능 | review-checklist > 래칭 보존, §12 D항 래칭 수명 |
| 정의-구현 대조 (FSM state별 설계 정의 1:1 대조) | 1. Design Rules > DefImpl | 섹션10 기능 | — |
| Module Analysis (수정 전 필수 분석) | 12. Module Analysis | 섹션9 Step 0, Step 6 | .ai/analysis/*.analysis.md (프로젝트별 생성) |
| 파일 헤더 주석 (신규 생성/수정 이력 업데이트) | 13. File Header Comment | 섹션9 Step 0.5, 섹션10 코딩스타일 | — |

## Cross-Skill 참조

| 원칙 | 본 skill | 참조 skill |
|------|---------|-----------|
| UVM Coverage Subscriber | 8. Verification | uvm-verification > coverage-guide.md |
| UVM Register Coverage (UVM_CVR_*) | 8. Verification | uvm-verification > ral-guide.md §11 |

## 마커 규약

- **형식**: `[→§X]` — X는 SKILL.md 내 섹션 번호
- **서브토픽**: `[→§X.Topic]` — 섹션 내 특정 주제 (예: `[→§1.CDC]`, `[→§1.Reset]`)
- **용도**: 요약 Zone의 항목이 어느 상세 섹션에서 유래했는지 추적
- **수정 시**: 상세 섹션 변경 → 마커가 가리키는 요약 항목도 반드시 동기화

## 변경 이력

- 2026-03-30 (20차): 파일 헤더 주석 규칙 추가 (§13) — 프로젝트 실제 파일 스타일 기반 doxygen 템플릿. 신규 파일 생성/기존 수정 시 @history 갱신 규칙. §9 Step 0.5, §10 코딩스타일 체크리스트 항목 추가. frontmatter description (9)항목 + 트리거 키워드 추가
- 2026-03-23 (19차): 모듈 코드 구조 규칙 추가 (§4) — 3영역 분리(포트/선언/Body), 기존 코드 수정 시 관련 신호 근처 배치, 선언-Body 순서 대응
- 2026-04-17 (21차): Verilator Lint 원칙 설명 MSYS2→OSS CAD Suite 수정 (line 47) — consistency-map 텍스트 동기화
- 2026-04-17 (20차): 6-Check FAIL 수정 — review-checklist.md에 리소스/Combinational Depth/래칭 보존 섹션 추가; synthesis-check.md 체크리스트에 2항목 추가 (15~16차에서 consistency-map 기재 후 파일 미반영 보완)
- 2026-03-20 (18차): CDC 테이블 Fast→Slow 2FF 장기유지 레벨 조건 추가. 필수규칙/§10 CDC 요약 동기화. §12 A항 클럭 주파수 확인 규칙, F항 2FF 유지 검증 규칙 추가
- 2026-03-20 (17차): 정의-구현 대조(§1.DefImpl) 추가 — FSM state 구현 후 설계 정의와 1:1 대조 규칙. Best Practices Check 6에 "압축 vs 명확성 균형" 항목 추가 (skill-validation-prompt.md). consistency-map 원칙 1개 추가
- 2026-03-20 (16차): 래칭 데이터 보존(§1.DataLife) 추가 — Proactive Dispatch에서 pending 레지스터 덮어쓰기 버그 기반. §1 필수규칙+상세, §10 체크리스트, §12 D항 래칭 수명. consistency-map 원칙 1개 추가
- 2026-03-18 (15차): H/W 리소스 최소화(§1.Resource) + Combinational Depth 최적화(§1.Timing) 추가 — 범용 H/W 설계 원칙. 필수규칙 테이블에 2개 항목 추가. consistency-map 원칙 2개 추가
- 2026-03-18 (14차): Module Analysis §12 추가 — RTL 수정 전 모듈 전체 분석서 필수 작성 규칙. §9 Step 0/6에 분석서 확인/갱신 단계 추가. description에 (8) 항목 및 트리거 키워드 추가. consistency-map 원칙 1개 추가
- 2026-03-09 (13차): Coverage 원칙 SKILL.md 섹션 컬럼 정정 — 2026-02-09 (8차) §8 리팩토링 시 미갱신된 항목 수정. 핵심 원칙 #1~#5, 워크플로우, Coverage Space 2×2 → "-", Covergroup 문법 → "포인터만"으로 갱신
- 2026-03-09 (12차): Verilator Lint 원칙 추가 — §11 내용을 verilator-guide.md로 추출한 것 반영. consistency-map 원칙 항목 추가
- 2026-02-20 (11차): Best Practices 적용 — P1: ASCII box→markdown 변환(8개), Quick Reference 섹션 전체 삭제(44줄). SKILL.md 597줄→452줄. 전 원칙의 "SKILL.md 내부 요약" 열에서 QR 참조 제거
- 2026-02-19 (10차): 중복 정리 D1-D6 — D1+D2: review-checklist Latch 상세→synthesis-check 포인터(-47줄), D3: always-block-patterns 가이드테이블→§2 포인터, D4: §1 $clog2 테이블→synthesis-check 포인터, D5: §1 Bit-Width BAD/GOOD 코드→synthesis-check 포인터(-15줄), D6: §7 2-proc/3-proc 비교테이블→fsm-patterns 포인터(-6줄). 원칙 반영위치 갱신(Latch, $clog2, Bit-Width, FSM)
- 2026-02-19 (9차): Bit-Width Safety 규칙 추가 — FIFO pointer truncation 실제 버그 기반. §1 필수규칙+상세 섹션, §9 Step 4.5, §10 체크리스트, QR 추가. synthesis-check > Bit-Width Safety 섹션 신규. 원칙 3개 추가 (Bit-Width Safety, $clog2 vs custom log2, 코드생성 Bit-Width 검증)
- 2026-02-09 (8차): SKILL.md 2단계 확장 패턴 적용 (889줄→570줄, -36%). §1 CDC 선택트리→포인터, §2 코드5개→always-block-patterns.md(신규), §3 notation/다이어그램→포인터, §7 2-proc코드+cycle다이어그램→fsm-patterns.md, §8 covergroup예제→포인터, §9 FIFO prose 삭제, §11 lint 3예시→1예시. 중복체크 R1-R8 전 PASS
- 2026-02-09 (7차): coverage skill 통합 — coverage-methodology/covergroup-patterns/coverage-examples 이관, 원칙 13개 추가, Cross-Skill 참조 추가
- 2026-02-09 (6차): Context 최적화 — SKILL.md 코드 예제 중복 제거 (CDC 2FF/Handshake, 스타일 비교, Pipeline 전체 모듈+다이어그램, BSC 코드+다이어그램, Top Integration 코드, FSM 2-proc/3-proc/출력 레지스터링). 긴 코드는 reference 포인터로 교체, 규칙/테이블/짧은 예제는 유지. 1,224줄 → ~855줄 (30% 감소)
- 2026-02-06 (5차): BSC _a/_z postfix 설명 수정 — "Actual/Zero-delay" → "primitive cell 관행 (a=입력, z=출력)". 검증 5/5 PASS
- 2026-02-06 (4차): Step 6 초기 검증 완료 (5/5 PASS), 변경 사항 없음
- 2026-02-06 (3차): [→§X] 참조 마커 시스템 도입, skill-validation-prompt.md 연동
- 2026-02-06 (2차): 필수 규칙 테이블 재구성 — Always블록분리/단일출력 제거, Blocking/단일할당 승격. No Latches·CDC 문구 수정. CDC guide box Pulse Sync 위치 교정(Fast→Slow → Slow→Fast)
- 2026-02-06 (1차): 전체 점검 완료 (SKILL.md ↔ 6개 reference 파일 일관성 확보)
