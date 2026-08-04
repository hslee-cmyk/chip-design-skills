# topology.json 대기중 정정 목록 (사용자가 "한꺼번에 반영해" 할 때까지 미반영)

대상 파일: `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json`

**2026-08-03 세션 4 — 아래 전부 일괄 반영 완료.** 실제 netlist가 바뀐 항목은 3건뿐
(M14b.source→gnd, M17/M22 drain 스왑, Vg16/Vg26→Vop1/Vom1 교차결합 병합) — 나머지는 전부
현재 JSON과 이미 일치하는 CONFIRMED NO-OP였다. 상세 diff는 topology.json의
`_correction_log_6` 참고. ⚠️ 후속조치(`symmetry.dispositions` 재생성)는 같은 세션에서
바로 실행 완료(아래 "후속 라운드" 이후 별도 배치, `_correction_log_7` 참고).

**2026-08-03 세션 4, 후속 라운드(bias-gen) — 아래도 전부 일괄 반영 완료.**
M60/M61/M64/M63/M58/M57/M68 7개 소자 재구성 + symmetry.dispositions 즉시 재생성까지
같은 배치에서 완료. 상세 diff는 `_correction_log_7` 참고. 소멸 net: `N60_64`, `N_bg_61`,
`Vbias_p`(3개, 38→35개 net).

## 2026-08-03 (세션 4)

### M14a/M14b — diode 스택 재확정
현재 JSON:
```
M14a: source=Vg16, drain=N14a14b, gate=N14a14b
M14b: source=N14a14b, drain=Vg16, gate=Vg16
```
사용자 지시(논문 원본 기준):
- `M14b.source = gnd`
- `M14a.source = M14b.drain`
- `M14a.gate = M14a.drain`
- `M14b.gate = M14b.drain`

**실제 변경분(값 비교 결과)**: `M14a.source=Vg16`, `M14a.gate=M14a.drain(=N14a14b)`,
`M14b.gate=M14b.drain(=Vg16)`는 이미 현재 JSON과 일치 — 변경 없음.
**유일한 실제 변경**: `M14b.source`: `N14a14b` → `gnd`.

결과 구조(반영 시): `N14a14b`(top, M13.drain/M9b.gate도 물림) — M14a(diode, gate=drain=N14a14b) —
`Vg16`(middle) — M14b(diode, gate=drain=Vg16) — `gnd`(bottom). M11a/M11b, M20a/M20b와 같은
"stacked-diode" 패턴으로 통일됨.

**부수 영향**: `N14a14b` net에서 `M14b.source` 단자가 빠짐(5단자→4단자: M13.drain, M14a.drain,
M14a.gate, M9b.gate). `gnd` net에 `M14b.source` 추가.

상태: **APPLIED** (2026-08-03 세션 4, 일괄 반영 완료 — `_correction_log_6` 참고).

### M18a/M18b(Vop측 Monticelli) — M17/M22 소스 배정 정정
사용자 지시: "Vop가 Vom쪽의 대칭구조야. M18a.source=M17.drain=M18b.drain,
M18a.drain=M18b.source=M19.drain."

현재 JSON:
```
M17: source=vdd, drain=N24b23a, gate=Vbias1
M22: source=vdd, drain=Vg25,    gate=Vbias1
Vg25 net(현재): M18a.source, M18b.drain, M22.drain, M25.gate
Vg26 net(현재): M18a.drain, M18b.source, M19.drain, M23a.drain, M23a.gate, M24b.source, M26.gate
```
- `M18a.drain=M18b.source=M19.drain` 부분은 이미 현재 JSON(Vg26 net)과 일치 — 변경 없음.
- `M18a.source=M18b.drain`도 이미 Vg25 net으로 일치 — 변경 없음.
- **실제 변경**: 사용자는 이 Vg25 net을 먹이는 소자가 `M22.drain`이 아니라 **`M17.drain`**이라고
  했다 — 현재 JSON은 M22.drain=Vg25, M17.drain=N24b23a인데, 이는 정확히 **뒤바뀐 상태**로
  보인다. 즉 Vom측 대응 관계(M8.drain=Vg15→M9a/M9b 공급, M13.drain=N14a14b→M14a/M14b 공급)와
  맞추려면 **M17.drain=Vg25(M18a/M18b 공급), M22.drain=N24b23a(M23a/M24b 공급)**로
  **M17↔M22의 drain 배정을 서로 스왑**해야 함.
- 반영 시 함께 정정 필요: `Vg25` net에서 `M22.drain` 제거하고 `M17.drain` 추가,
  `N24b23a` net에서 `M17.drain` 제거하고 `M22.drain` 추가.
- **사용자 확인 완료(다음 메시지)**: "M17.drain=Vg25" — 스왑 해석 확정. M17.drain=Vg25,
  M22.drain=N24b23a로 반영.

상태: **APPLIED**.

### M26.gate — 확인(변경 없음)
사용자 지시: "M26.gate=M18b.source, M26.gate는 M22.drain과 M20b.drain에 연결 안돼."

현재 JSON 대조 결과: 이미 일치 — **변경 불필요**.
- `M26.gate = Vg26`이고, 현재 Vg26 net = {M18a.drain, M18b.source, M19.drain, M23a.drain,
  M23a.gate, M24b.source, M26.gate} → `M18b.source` 포함, 사용자 지시와 일치.
- `M22.drain`은 (위 M17/M22 스왑 반영 후) `N24b23a`가 됨 — Vg26과 다른 net, 연결 없음. 일치.
- `M20b.drain`은 `N20b` — Vg26과 다른 net, 연결 없음. 일치.

상태: **CONFIRMED, NO-OP** — 일괄 반영 때 그대로 둠(현재 값 유지).

### M18b.gate — 확인(스왑과 일치, 변경 없음)
사용자 지시: "M18b.gate=M22.drain, M18b.gate는 M20b.drain과 연결 안 돼."

현재 JSON: `M18b.gate = N24b23a`. 위 M17/M22 스왑 반영 후 `M22.drain = N24b23a`가 되므로
`M18b.gate = M22.drain`이 정확히 성립 — **스왑 정정과 일치, 별도 변경 불필요**(스왑 자체는
이미 대기열에 있음). `M20b.drain(=N20b)`과는 다른 net이라 연결 없음 — 일치.

상태: **CONFIRMED, NO-OP** (스왑 항목에 포함되어 이미 커버됨).

### M23a/M24b — 확인(변경 없음, M14b.source=gnd 정정과 비대칭 유지)
사용자 지시: "M23a.source=M24b.drain=M24b.gate, M23a.drain=M23a.gate."

현재 JSON: `M23a: source=N24b23a, drain=Vg26, gate=Vg26`, `M24b: source=Vg26, drain=N24b23a,
gate=N24b23a`. 대조 결과 **이미 일치, 변경 불필요**.
- `M23a.source(N24b23a) = M24b.drain(N24b23a) = M24b.gate(N24b23a)` — 일치.
- `M23a.drain(Vg26) = M23a.gate(Vg26)` — 일치.

⚠️ 참고(사람 재확인용 메모, 임의 정정 아님): 이 구조는 **위 M14a/M14b PENDING 정정 이전의
"공유 source 노드" 구조**와 대응된다(M24b가 옛 M14a 패턴, M23a가 옛 M14b 패턴) — 그런데
M14b는 이번 세션에 `source: N14a14b → gnd`로 정정됐지만, 이번 M23a 지시엔 그런 "gnd로
분리" 언급이 없다. 즉 Vom측(M14a/M14b)과 Vop측(M23a/M24b)이 이 지점에서 **비대칭**이 되는
것으로 보인다 — 사용자가 실제로 그렇게 확인한 것으로 그대로 기록하며, 임의로 대칭을 강제해
M23a.source도 gnd로 바꾸지 않는다.

상태: **CONFIRMED, NO-OP**.

### M19.drain / M18b.source — Vg26를 Vom1(?)과 병합
사용자 지시(원문 그대로): "M19.drain=Vom1=M18b.source야."

현재 JSON: `M19.drain = Vg26`, `M18b.source = Vg26` (이미 서로 같은 net, 이 부분은 기존과
일치). 하지만 사용자는 이 net 자체가 **`Vg26`이 아니라 `Vom1`**이라고 했다 — 즉 지금까지
Vop측 2단 내부노드로만 쓰던 `Vg26`이 실제로는 **1단 출력 net(`Vom1` 또는 오타라면
`Vop1`)과 동일한 물리 노드**라는 뜻으로 읽힌다.

⚠️ **일괄 반영 전 반드시 확인**: 문자 그대로는 `Vom1`(Vom측 1단 출력, 현재 M2a.drain=M3a.drain)
인데, 이 소자들(M19/M18b)은 전부 **Vop측** 블록이라 대칭상 `Vop1`(M2b.drain=M3b.drain)이
더 자연스럽다 -- 그런데 이 회로가 Class-AB 단에서 반대쪽 1단 출력을 끌어쓰는 교차 결선일
가능성도 있어(과거 correction_log들에서도 Vom1 관련 오독이 여러 번 있었음) 임의로 오타
정정하지 않고 원문 그대로 보관한다. 반영 시 (1) `Vom1`이 맞다면 `Vom1`/`Vg26`이 병합되며
Vom1 net에 M2a.drain,M3a.drain,M19.drain,M18b.source(+ 위 스왑/기존 정정 반영되면 M23a
관련 단자도) 전부 물리고 `Vg26`이라는 net 이름 자체가 없어짐. (2) `Vop1`이 맞다면 대신
`Vop1`/`Vg26`이 병합. 둘 중 어느 쪽인지, 혹은 `Vg26`을 그대로 두고 `Vom1`/`Vop1`과는
별개 노드인지 사용자 확인 필요.

**업데이트(다음 메시지로 해소)**: 사용자가 바로 다음에 "M10.drain=M9b.source=Vop1"(Vom측
소자인데 반대쪽 Vop1을 지목)이라고 대칭적으로 확인해줘서, 이건 오타가 아니라 **의도된
교차결합(cross-coupling)** 구조임이 확정됐다 -- Vom측 2단 내부노드가 Vop측 1단 출력을,
Vop측 2단 내부노드가 Vom측 1단 출력을 각각 물고 있다.

상태: **APPLIED**.

### M10/M9b — Vg16을 Vop1과 병합 (위 Vg26/Vom1과 대칭, 교차결합 확정)
사용자 지시: "M10.drain=M9b.source=Vop1"

현재 JSON: `M10.drain = Vg16`, `M9b.source = Vg16` (서로 같은 net, 기존과 일치). 사용자는
이 net이 `Vg16`이 아니라 **`Vop1`**(Vop측 1단 출력, 현재 M2b.drain=M3b.drain)이라고 확정.
바로 위 `M19.drain=M18b.source=Vom1` 항목과 정확히 대칭 -- **교차결합 패턴 확정**:
- Vom측 2단 Class-AB 내부노드(현재 이름 `Vg16`) = `Vop1`
- Vop측 2단 Class-AB 내부노드(현재 이름 `Vg26`) = `Vom1`

**반영 시 영향(두 항목 함께 처리)**:
- `Vg16` net(현재 M10.drain, M9a.drain, M9b.source, M14a.source[M14 PENDING 반영 후],
  M14b.drain, M16.gate)을 전부 `Vop1`에 병합 -- `Vop1` net은 M2b.drain, M3b.drain +
  위 6개 단자 전부.
- `Vg26` net(현재 M18a.drain, M18b.source, M19.drain, M23a.drain, M23a.gate, M24b.source,
  M26.gate)을 전부 `Vom1`에 병합 -- `Vom1` net은 M2a.drain, M3a.drain + 위 7개 단자 전부.
- `Vg16`/`Vg26`이라는 net 이름 자체가 없어지고 `Vom1`/`Vop1`로 완전 대체됨.
- `Vg15`/`Vg25`(M8/M22-M9a/M18a 쪽 노드)는 이번 지시에 언급 없음 -- 그대로 유지, 임의 확장 안 함.

상태: **APPLIED**.

### M1a/M2a/M3a/M4a/M5 (Vom측 1단) — 확인(변경 없음)
사용자 지시: "M1a.drain=M2a.source, M2a.drain=M3a.drain=Vom1, M3a.source=M4a.drain,
M1a.gate=M4a.gate=Vip, M4a.source=M5.drain"

현재 JSON과 전부 대조 완료 -- **전부 이미 일치, 변경 불필요**:
- `M1a.drain=M2a.source` = `N1a2a` (일치)
- `M2a.drain=M3a.drain` = `Vom1` (일치)
- `M3a.source=M4a.drain` = `N3a4a` (일치)
- `M1a.gate=M4a.gate` = `Vip` (일치)
- `M4a.source=M5.drain` = `Vy` (일치)

참고: 위 Vg16/Vg26↔Vop1/Vom1 교차결합 병합과는 별개 -- 이 `Vom1`(M2a.drain=M3a.drain)
정의 자체는 그대로 유지되고, 교차결합 병합 때 Vom1에 단자가 "추가"될 뿐 이 관계는 안 바뀜.

상태: **CONFIRMED, NO-OP**.

### M2a/M3a 게이트 — 확인(변경 없음)
사용자 지시: "M2a.gate=Vbias2, M3a.gate=Vbias3"

현재 JSON: `M2a.gate=Vbias2`, `M3a.gate=Vbias3` -- 이미 일치, 변경 불필요.

상태: **CONFIRMED, NO-OP**.

### M1b/M2b/M3b/M4b/M5 (Vop측 1단) — 확인(변경 없음)
사용자 지시: "M1b.drain=M2b.source, M2b.drain=M3b.drain=Vop1, M3b.source=M4b.drain,
M4b.source=M5.drain"

현재 JSON과 전부 대조 완료 -- **전부 이미 일치, 변경 불필요**:
- `M1b.drain=M2b.source` = `N1b2b` (일치)
- `M2b.drain=M3b.drain` = `Vop1` (일치)
- `M3b.source=M4b.drain` = `N3b4b` (일치)
- `M4b.source=M5.drain` = `Vy` (일치, M5는 Vom/Vop 공유 tail로 이미 등록됨)

상태: **CONFIRMED, NO-OP**.

### M1b/M4b 게이트 — 확인(변경 없음)
사용자 지시: "M1b.gate=M4b.gate=Vim"

현재 JSON: `M1b.gate=Vim`, `M4b.gate=Vim` -- 이미 일치, 변경 불필요.

상태: **CONFIRMED, NO-OP**.

### M6/M7/M5 (1단 tail 전류원) — 확인(변경 없음)
사용자 지시: "M6.source=M7.source=vdd, M6.gate=Vbias1, M7.gate=Vcmfb, M6.drain=M7.drain=Vx,
M5.drain=Vy"

현재 JSON과 전부 일치, 변경 불필요:
- `M6: source=vdd, drain=Vx, gate=Vbias1` (일치)
- `M7: source=vdd, drain=Vx, gate=Vcmfb` (일치)
- `M5.drain=Vy` (일치)

상태: **CONFIRMED, NO-OP**.

## 2026-08-03 (세션 4, 후속 라운드 — bias-gen)

### M60/M66/M61 — drain 재배정
사용자 지시: "M60.drain=M66.drain이고, M60.drain은 M61.drain에 연결 안 되었어."

현재 JSON: `M60: source=vdd, drain=N60_64, gate=Vbias1`, `M61: source=vdd, drain=N_bg_61,
gate=Vbias1`, `M66: source=gnd, drain=Vbias4, gate=Vbias4`.

- `M60.drain`이 `M61.drain`과 다르다는 부분은 이미 현재 JSON과 일치(`N60_64` ≠ `N_bg_61`) —
  변경 불필요.
- **실제 변경**: `M60.drain = M66.drain`. 현재는 `M60.drain=N60_64`(M64/M63 stacked-diode로
  이어짐), `M66.drain=Vbias4`로 서로 다른 net. 문자 그대로 반영하면 `M60.drain`이 `N60_64`가
  아니라 **`Vbias4`**가 됨 — 즉 M60이 더 이상 M64/M63 stacked-diode 체인을 안 먹이고
  대신 Vbias4 net에 합류한다는 뜻으로 읽힌다.

⚠️ 구조적 영향이 커서(M60이 지금 먹이는 N60_64→M64→M63 체인 전체가 붕 뜨게 됨) 일괄 반영
전 재확인 필요 — 지금은 원문 그대로만 기록, 임의 해석/반영 안 함.

**업데이트(사용자 확인)**: "M60.drain=M66.drain=M66.gate=Vbias4" — 값 확정. `M66.gate=M66.drain=
Vbias4`는 이미 현재 JSON과 일치(변경 없음), **`M60.drain=Vbias4`(기존 `N60_64`에서 이동)만
실제 변경**. `N60_64` net은 이 정정 + 아래 M64 정정(M64.source도 더 이상 N60_64 안 씀)이
함께 반영되면 완전히 소멸.

상태: **APPLIED** — topology.json 미반영.

### M64/M63 — diode 위치 재확정 (M63가 아니라 M64가 diode)
사용자 지시: "M64.drain=M64.gate=M63.gate, M64.source=M63.drain, M63.source=Vbias3."

현재 JSON: `M64: source=N60_64, drain=N64_63, gate=Vbias3`, `M63: source=N64_63, drain=Vbias3,
gate=Vbias3` (_correction_log_2 근거: "둘 다 게이트가 스택 맨 아래 M63의 drain=Vbias3로
묶임" — 즉 기존 모델은 **M63가 diode**라고 가정했었다).

사용자 지시대로면 정반대: **M64가 diode**(gate=drain, 자기 자신)이고 그 diode 노드에
`M63.gate`도 같이 묶인다. 정리하면:
- `M64.drain = M64.gate = M63.gate` → 새 노드(가칭, 값 미확정). 기존 `M63.gate=Vbias3`였는데
  이 노드가 `Vbias3`인지 아닌지 사용자가 명시하지 않음 — **임의로 Vbias3로 단정 안 함**
  (M63.source가 별도로 Vbias3라고 지정됐는데 gate=source면 Vgs=0인 퇴화 diode가 되므로
  오히려 Vbias3가 아닐 가능성이 큼).
- `M64.source = M63.drain` → 또 다른 새 노드(가칭 `N64_63` 재사용 가능, 기존 이름이 이
  위치에 있던 노드와 동일 역할이라 이름만 유지해도 무방해 보이지만 확정 아님).
- `M63.source = Vbias3` — 기존엔 `M63.drain=Vbias3`였는데 이번엔 **source**가 Vbias3.

**업데이트(사용자가 바로 다음에 "M61.drain=M64.drain" 확인)**: 이걸로 두 미해결 항목이
동시에 풀렸다:
1. **전류원 확정**: `M61`(pmos, source=vdd, gate=Vbias1)이 이 diode 스택을 먹인다 —
   `M61.drain = M64.drain = M64.gate = M63.gate` (가칭 새 net, 이름은 아직 미정 — Vbias3는
   아님, 사용자가 이후 실제 이름을 알려줄 때까지 임시로 `N61_64`로 표기).
2. **N_bg_61 고아화 문제 해소**: 아래 M58/M57 항목에서 `M58.source`가 Vbias2로 옮겨가며
   `N_bg_61`엔 `M61.drain`만 남을 거라 걱정했는데, 이제 `M61.drain`도 이 새 net(`N61_64`)로
   옮겨가므로 **`N_bg_61` net 자체가 완전히 소멸**(양쪽 단자가 다 다른 곳으로 이동) — 정합적.

정리하면 이 서브블록 전류경로가 재구성됨: `vdd -> M61 -> N61_64(=M64.gate=M64.drain=
M63.gate, diode는 M64) -> M63 -> M63.source`이고, `M64.source = M63.drain`(별도 노드, 임시
`N64_63` 유지)이 스택 중간에 낀다. `M60`은 이 스택에서 완전히 빠지고 대신 `Vbias4`로
직결(위 항목).

⚠️ **정정(사용자가 바로 다음에 "M63.source=Vy"로 다시 지시)**: 위에서 "M63.source=Vbias3"로
기록했던 것이 **`Vy`로 정정됨**(직전 지시를 덮어씀 -- Vbias3 아님). `Vy`는 1단 NMOS tail
net(현재 M4a.source, M4b.source, M5.drain). 아래 M58.source=Vx 정정과 정확히 대칭
(PMOS쪽 bias-gen은 Vx로, NMOS쪽은 Vy로 각각 1단 tail에 물림) -- 최종값은
**`M63.source=Vy`**로 갱신, `Vbias3` 언급은 폐기.

상태: **APPLIED** — topology.json 미반영.

**최종 net 이름 확정(사용자 확인 "M64.drain=Vbias3")**: 가칭 `N61_64`는 실제로 **`Vbias3`**
그대로였다 -- `M61.drain = M64.drain = M64.gate = M63.gate = Vbias3`. 앞서 "Vbias3는 아닐
것"이라고 우려했던 근거(M63.source=Vbias3면 gate=source 퇴화)는 이제 `M63.source=Vy`로
정정되며 해소됐다(더 이상 충돌 없음) -- 원래 옛 JSON도 `M64.gate=Vbias3`/`M63.gate=Vbias3`였던
것과 자연스럽게 이어진다(diode가 M63→M64로 바뀌고 M61.drain이 직결된 것만 다름).

**최종 확정 요약(M60/M66/M61/M64/M63/M58/M57/M68/M66)**:
- `M60: drain=Vbias4`(N60_64 폐기, 위 항목)
- `M61: drain=Vbias3`(N_bg_61 폐기)
- `M64: source=N64_63(=M63.drain), drain=Vbias3, gate=Vbias3`(diode)
- `M63: source=Vy, drain=N64_63(=M64.source), gate=Vbias3`
- `M58: source=Vx, drain=N58_57(=M57.source), gate=Vbias_p`
- `M57: source=N58_57(=M58.drain), drain=Vbias_p, gate=Vbias_p`(diode)
- `M68: source=gnd, drain=Vbias_p, gate=Vbias4`(변경 없음)
- `M66: source=gnd, drain=Vbias4, gate=Vbias4`(변경 없음)
- 소멸 net: `N60_64`, `N_bg_61`

상태: **APPLIED** — topology.json 미반영.

### M18? — 이름 모호, 확인 필요
사용자 지시: "m18.drain=vbias2"

이 회로엔 "M18"이라는 이름의 소자가 없다 -- 후보는 `M18_bg`(bias-gen, 현재
source=vdd, drain=Vbias1, gate=Vbias1) 또는 `M18a`/`M18b`(Vop측 Monticelli, 이번 세션
초반에 이미 다른 내용으로 확정됨: M18a drain=Vom1, M18b source=Vom1). bias-gen 블록을
다루던 직전 흐름상 `M18_bg`일 가능성이 높지만, 임의로 단정하지 않고 사용자 확인 대기.

상태: **APPLIED** — topology.json 미반영.

**업데이트(사용자 재확인)**: "m18.drain=vbias1" -- 즉 `M18_bg`가 맞았고, 값도
`Vbias1`(현재 JSON과 동일) -- **변경 없음, CONFIRMED NO-OP**로 종결. 앞선 "vbias2" 언급은
오타였던 것으로 보임.

### M57.drain — 재정정(Vbias_p → Vbias2), 기존 "전체 확정" 요약과 충돌 주의
사용자 지시(같은 메시지): "m57.drain=vbias2"

⚠️ 이건 바로 위 bias-gen "최종 확정 요약"에서 `M57: drain=Vbias_p`(변경 없음)로 이미 정리한
내용과 **충돌**한다. 문자 그대로 받아들이면:
- `M57.drain`: `Vbias_p` → **`Vbias2`**.
- 그런데 그 확정 요약에서 `M58.gate=M57.drain=M57.gate=Vbias_p`로 묶어놨었다 -- `M57.drain`이
  Vbias2로 바뀌면 이 등식대로는 `M57.gate`/`M58.gate`도 같이 Vbias2로 딸려가야 하는지,
  아니면 `M57.drain`만 따로 떨어져 나가고 `M57.gate`는 그대로 Vbias_p로 남는지 **불명확** --
  임의로 cascade 적용하지 않고 원문 그대로만 기록.
- `M68.drain`도 현재 Vbias_p를 공유하는데, 이것도 같이 바뀌는지 별도 확인 필요.

상태: **PENDING, 확인 필요(cascade 범위 불명 -- M57.gate/M58.gate/M68.drain도 같이
바뀌는지)** — topology.json 미반영.

**업데이트(사용자 확인)**: "m58.gate=m57.drain=m57.gate=vbias2" -- cascade 확정.
`M58.gate = M57.drain = M57.gate = Vbias2`(전부 하나의 net, `Vbias_p` 완전 대체). `M68.drain`도
같이 바뀌는지는 아직 별도 확인 안 됨 -- 다음 지시 대기.

**최종 확정(M58/M57)**: `M58: source=Vx, drain=N58_57(=M57.source), gate=Vbias2`,
`M57: source=N58_57(=M58.drain), drain=Vbias2, gate=Vbias2`(diode). `Vbias_p`라는 net
이름은 이번 정정으로 사라지는 것으로 보임(M68.drain 확인 후 최종 결론).

상태: **APPLIED** — topology.json 미반영.

**업데이트(사용자 확인 "m68.drain=vbias2")**: 완전 확정. `M68.drain: Vbias_p → Vbias2`.
`Vbias_p` net(기존 4단자: M57.drain, M57.gate, M58.gate, M68.drain)이 **전부 Vbias2로
이동해 완전히 소멸** -- `Vbias_p`라는 이름 자체가 이번 정정으로 없어짐.

**최종 확정(M57/M58/M68)**: `M58: source=Vx, drain=N58_57, gate=Vbias2`,
`M57: source=N58_57, drain=Vbias2, gate=Vbias2`(diode), `M68: source=gnd, drain=Vbias2,
gate=Vbias4`.

상태: **APPLIED** — topology.json 미반영.

### M58/M57 — source 재배정
사용자 지시: "M58.source=Vbias2, M58.gate=M57.drain=M57.gate, M58.drain=M57.source."

현재 JSON: `M58: source=N_bg_61, drain=N58_57, gate=Vbias_p`, `M57: source=N58_57,
drain=Vbias_p, gate=Vbias_p`.

- `M58.gate=M57.drain=M57.gate` = `Vbias_p` — 이미 현재 JSON과 일치, 변경 불필요.
- `M58.drain=M57.source` = `N58_57` — 이미 일치, 변경 불필요.
- **실제 변경**: `M58.source`: `N_bg_61` → **`Vbias2`**(기존에 M2a.gate/M2b.gate가 쓰던
  그 cascode bias net). bias-gen 블록이 신호 경로의 Vbias2 net과 직접 연결된다는 뜻.

⚠️ **부수 영향**: `N_bg_61` net은 현재 `{M58.source, M61.drain}` 2단자인데, `M58.source`가
Vbias2로 옮겨가면 `M61.drain`만 남아 **고아 net이 됨** — `M61.drain`도 같이 바뀌는지,
아니면 다른 소자가 추가로 N_bg_61을 쓰는지 아직 안 나옴. 임의로 M61.drain을 건드리지 않고
다음 지시를 기다림.

**업데이트(해소됨)**: 사용자가 이후 "M61.drain=M64.drain"이라고 확인 -- `M61.drain`이
`N_bg_61`이 아니라 위 M64/M63 항목의 새 net(가칭 `N61_64`)으로 옮겨간다. 즉 `N_bg_61`은
두 단자가 전부 다른 곳으로 이동해 **완전히 소멸** -- 고아 net 걱정 해소.

⚠️ **정정(사용자가 바로 다음에 "M58.source=Vx"로 다시 지시)**: 방금 위에서 확정했던
`M58.source=Vbias2`가 **`Vx`로 정정됨**(직전 지시를 덮어씀 -- Vbias2 아님). `Vx`는 1단
tail net(현재 M1a.source, M1b.source, M6.drain, M7.drain). 최종값은 **`M58.source=Vx`**로
갱신, `Vbias2` 언급은 폐기.

상태: **APPLIED** — topology.json 미반영.

## 2026-08-04 (세션 5)

### M13/M14a/M14b — Vop1과 완전 무관한 독립 3단 직렬 체인으로 재확정 (기존 "M14a/M14b — diode 스택 재확정" 항목의 Vop1 연결 부분을 대체)
경위: 위 M22/M23a/M24b 정정(Vom1과 무관한 독립 체인) 확정 후, 사용자가 "vop1는 아까
뺀 것이 왜 또 들어가 있어. M14a와 M14b는 vop1와 무관해"로 대칭되는 문제를 지적 —
Vom1측(M23a/M24b)에서 드러난 "옛 Vg16/Vg26 블랭킷 병합 오류"가 Vop1측(M14a/M14b)에도
똑같이 있었음이 확정됨. artifact가 이 연결을 "확정"으로 기록했던 건 독립 재검증이
아니라 그 블랭킷 병합을 그대로 문서화한 것뿐이었다(제가 이걸 "재검증됨"으로
오판했던 이전 턴 참고).

**최종 구조**: `M13(vdd)→N14a14b→M14a(diode)→N14a_14b(신설)→M14b(diode)→gnd` —
`Vop1`과 전혀 안 닿는 독립 체인(M22-M23a-M24b와 정확히 같은 유형). `M14a.drain=gate=
N14a14b`(M13와 공유하는 상단 net)는 변경 없음, `M14b.source=gnd`(세션4 정정)도
변경 없음 — `M14a.source`/`M14b.drain`/`M14b.gate`만 `Vop1`에서 신설 사설net으로 이동.

**신설 net**: `N14a_14b` (Claude 명명, 사용자 위임 — 기존 `N58_57`/`N64_63`/`N60_64`
언더스코어 관례를 따름, 기존 `N14a14b`와 혼동 방지).

**정정 후 값**:
```
M14a: source=N14a_14b, drain=N14a14b, gate=N14a14b
M14b: source=gnd,      drain=N14a_14b, gate=N14a_14b
```
(M13는 변경 없음: source=vdd, drain=N14a14b, gate=Vbias1)

**현재 JSON과 비교**:
```
M14a(현재): source=Vop1, drain=N14a14b, gate=N14a14b   → source만 변경
M14b(현재): source=gnd,  drain=Vop1,    gate=Vop1        → drain/gate만 변경
```

**net 영향**:
- `Vop1`(현재 10단자: M10.drain, **M14a.source, M14b.drain, M14b.gate**, M16.gate,
  M2b.drain, M3b.drain, M9a.drain, M9b.source, Rz1.t1) → 굵은 글씨 3개 제거,
  **7단자**로 축소(M10.drain, M16.gate, M2b.drain, M3b.drain, M9a.drain, M9b.source,
  Rz1.t1).
- `N14a14b`(현재 4단자: M13.drain, M14a.drain, M14a.gate, M9b.gate) → **변경 없음**
  (M14a.drain/gate는 그대로 이 net).
- `N14a_14b`(신설): `M14a.source`, `M14b.drain`, `M14b.gate` — **3단자**.
- `gnd`: 변경 없음(`M14b.source`는 이미 gnd였음).

⚠️ **후속조치 필요**: `symmetry.matching_pairs`의 `{"M11a","M14a"}`/`{"M11b","M14b"}`
선언도 이 구조 변경 후 `rerun_symmetry.py` 재확인 대상(M22/M23a/M24b와 동일 사유).

상태: **APPLIED** (2026-08-04, `N14a_14b` 신설 반영, `_correction_log_8` 참고).

### M22/M23a/M24b — Vom1과 완전 무관한 독립 3단 직렬 체인으로 재확정 (위 두 건 최종 대체)
경위: 여러 차례 조각난 확인("m24b.source=gnd" → "vom1은 m23a.drain/gate에 연결 안 됨"
→ 대칭 표 대조 중 일시적으로 "M23a=M14a자리/M24b=M14b자리" 가설 → "m24b는 vom1과
완전히 무관해"로 그 가설도 기각 → "m23a.drain=m23a.gate=m22.drain" 최종 확인 → X는
"새 사설net"으로 확정)을 거쳐 아래로 수렴. **이 항목이 최종본이며 위 "역할 통째로
교환" 항목을 대체한다.**

**최종 구조**: `M22(vdd)→N24b23a→M23a(diode)→N23a24b(신설)→M24b(diode)→gnd` —
`Vom1`과 전혀 안 닿는 독립 체인. Vom측 `M11a-M11b-M12`(Vop1과 무관한 독립 체인)와
대칭이고, `M13-M14a-M14b`(Vop1에 물리는 체인)와는 다른 패턴 — 즉 Vop측의
"M20a-M20b-M21 ↔ M22-M23a-M24b" 두 체인이, Vom측의 "M11a-M11b-M12 ↔ M13-M14a-M14b"
두 체인과 각각 대응하되, **어느 쪽도 상대 극의 출력버스(Vom1/Vop1)에 물리지 않는
동일한 유형**이 된다(둘 다 "무관 독립 체인" 유형 — Vom측만 그중 하나(M13/M14a/M14b)가
Vop1에 물리는 예외였던 게 아니라, 이 재확인으로 Vop측엔 그런 예외가 없음이 확정됨).

**신설 net**: `N23a24b` (기존 `N11a11b`/`N20a20b` 명명 관례 그대로 적용).

**정정 후 값**:
```
M23a: source=N23a24b, drain=N24b23a, gate=N24b23a
M24b: source=gnd,     drain=N23a24b, gate=N23a24b
```
(M22는 변경 없음: source=vdd, drain=N24b23a, gate=Vbias1)

**현재 JSON과 비교**:
```
M23a(현재): source=N24b23a, drain=Vom1,    gate=Vom1       → source/drain/gate 전부 변경
M24b(현재): source=Vom1,    drain=N24b23a, gate=N24b23a    → source/drain/gate 전부 변경
```

**net 영향**:
- `Vom1`(현재 10단자: M18a.drain, M18b.source, M19.drain, **M23a.drain, M23a.gate,
  M24b.source**, M26.gate, M2a.drain, M3a.drain, Rz2.t1) → 굵은 글씨 3개 전부 제거,
  **7단자**로 축소(M18a.drain, M18b.source, M19.drain, M26.gate, M2a.drain, M3a.drain,
  Rz2.t1).
- `N24b23a`(현재 5단자: M18b.gate, M22.drain, **M23a.source**, M24b.drain, M24b.gate) →
  `M23a.source`/`M24b.drain`/`M24b.gate` 제거, `M23a.drain`/`M23a.gate` 추가 →
  **4단자**(M18b.gate, M22.drain, M23a.drain, M23a.gate).
- `N23a24b`(신설): `M23a.source`, `M24b.drain`, `M24b.gate` — **3단자**.
- `gnd`(현재 14단자) → `M24b.source` 추가, **15단자**.

⚠️ **후속조치 필요**: `symmetry.matching_pairs`의 `{"M20a","M24b"}`/`{"M20b","M23a"}`
선언이 이 구조 변경으로 stale해질 가능성 — `rerun_symmetry.py`는 이 kind(branch_symmetric)를
자동 탐지 못 하므로(手동 판단 영역), 다음 세션에서 구조적으로 재검토 필요.

상태: **APPLIED** (2026-08-04, `N23a24b` 신설 반영, `_correction_log_8` 참고). `symmetry.
dispositions`의 `current_mirror/nmos/N24b23a`(M24b→M23a로 멤버 갱신), `hub_merge/nmos/
Vom1`·`hub_merge/nmos/Vop1`(멤버 갱신), 그리고 `M14b`쪽의 죽은 `current_mirror/nmos/Vop1`
디스포지션 삭제까지 `rerun_symmetry.py` 재실행 결과에 맞춰 같이 반영 완료(stale 0건,
무관한 `Voc_des` 1건만 남음). `run_harness.py` 재실행 결과: 처음 발견됐던 KCL 충돌
(`derive_stack_groups()`가 branch_symmetric을 stack_id에 잘못 재사용하던 버그, `sizing_recipe.py`
엔진 수정 병행)은 해소됐고, 대신 `M10`(그리고 대칭상 `M19`)이 A엔진으로 전류를 못 정하는
새 에러가 나옴 — `{"M12","M10"}`/`{"M21","M19"}` branch_symmetric 병합이 버그 상태에서
우연히 M10/M19에 전류를 흘려주고 있었을 뿐, 원래 이 둘을 위한 theta/seed 선언 자체가
없었다는 뜻(진짜 gap, 다음 세션 과제).

### M14a.source/M14b.drain — 검토 후 철회(오판)
2026-08-04, `M14a.source`/`M14b.drain`이 `Vop1`에서 잘못 병합된 것 아니냐는 가설을
세웠으나, artifact(`current_reuse_telescopic_ota — connectivity review`,
https://claude.ai/code/artifact/a00dad7b-e1db-4b28-8c60-748ea76cca45, 2026-08-03
확정본)를 다시 확인한 결과 **`N14a14b`–M14a–`Vop1`–M14b–`gnd` 구조와 `Vop1`에
`M14a.source`/`M14b.drain`/`M14b.gate`가 포함되는 것 자체가 이미 사용자가 명시적으로
확인한 정답**이었다("Vop측 대응(M23a/M24b)은 이 정정 대상이 아님"과 같은 배치에서
확정). pending_topology_corrections.md 과거 이력 텍스트만 보고 "과잉병합 실수"라는
그럴듯한 서사를 재구성한 게 잘못 — 최종 확정본(artifact)과 대조 없이 진행한 사례.

상태: **철회(WITHDRAWN)** — 정정 불필요, topology.json 현재 상태가 맞음.

### M57/M68/M66 — 확인(변경 없음)
사용자 지시: "M57.drain=M68.drain, M68.gate=M66.gate=Vbias4, M68.source=gnd."

현재 JSON과 전부 대조 완료 -- **전부 이미 일치, 변경 불필요**:
- `M57.drain=M68.drain` = `Vbias_p` (일치)
- `M68.gate=M66.gate` = `Vbias4` (일치)
- `M68.source` = `gnd` (일치)

상태: **CONFIRMED, NO-OP**.
