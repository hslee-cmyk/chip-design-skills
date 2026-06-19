---
kind: pattern
domain: rtl
scope: global
tags: [width-truncation, fifo, clog2, software-queue, occupancy-counter, verifier-routing]
---

# RTL 일반 패턴 (전 프로젝트 적용) — 장기 지식

> 특정 프로젝트의 버그 instance가 아니라, **여러 프로젝트에 일반화되는 원칙**.
> 프로젝트별 구체 사례는 각 프로젝트의 `docs/solutions/`(단기·graphify) 참조.
> 승격 규칙: 프로젝트 패턴이 3건+ 또는 명백한 일반 원칙이면 여기로 격상.

## P-WIDTH · sized 변수 폭 truncation (T9)

**증상**: 카운터/포인터가 기대 범위를 못 담아 wrap·오판. sized `localparam`/`reg`에
`max(value) >= 2^width` 값을 대입하면 silent truncation.

**원칙**:
- sized 변수 폭은 항상 `$clog2`로 산정하고 `max(value) < 2^width` 를 검증.
- `localparam`은 unsized가 기본 안전. 굳이 `[N-1:0]`로 좁히지 말 것.
- depth N FIFO의 포인터 폭은 `$clog2(N)`, 최대 인덱스는 `N-1` (off-by-one 주의).

**❌ WRONG** `localparam [PTR_W-1:0] MAX_PTR = SIZE-1;`  (PTR_W가 좁으면 truncation)
**✅ CORRECT** `localparam PTR_W = $clog2(SIZE); localparam MAX_PTR = SIZE-1;`

**검증 owner**: static (lint/elaboration).

---

## P-FIFOSW · FIFO/메모리를 소프트웨어 자료구조처럼 모델링 (T4/T6/T9 메타패턴)

**증상**: FIFO 경계(single-entry, wrap, full, zero-duration)에서 오동작 — read 불안정,
off-by-one, 영구 hang, 폭 truncation. 표면 증상은 다양하나 근원 동일.

**원칙**:
- 동기-read는 같은 사이클에 데이터 샘플 금지 → registered-read 대기 또는 holding latch.
  블록 간 read는 고정 cycle count가 아니라 data-valid/ack로 캡처(CDC면 ack도 동기화).
- "N칸 앞 entry 존재"는 **occupancy counter**(`count>=N`)로 판단, raw 포인터 magnitude 비교 금지.
  비교 offset 더하기 전 포인터를 1비트 zero-extend.
- write-enable은 `~full` AND 없이 절대 assert 금지.
- single-entry / `ptr==MAX` / wr-wraps-to-0 / `count==0` 경계를 명시적 directed-test.

**검증 owner**: static(폭·zero-ext smell) → formal(경계 반례) → sim(타이밍/래칭).

---

## P-VERIFY · 버그 클래스별 검증 owner 라우팅 (방법론)

**원칙**: 발견된 위험은 "test 요구"에 그치지 말고 가장 싼 신뢰 owner로 라우팅.
- self-contained 논리/타이밍 (off-by-one, deadlock corner, sync-read latency) → **formal**(sby).
- cross-domain CDC 타이밍 → **directed sim**.
- protocol-relational dead-code/도달성 → **static reachability** 또는 directed sim.
- 비합성/구조/폭 → **static**(lint, `default_nettype none`, elaboration).

상세 실패 분류는 `ai-verilog-failure-taxonomy.md` (T1..T9) 참조.
