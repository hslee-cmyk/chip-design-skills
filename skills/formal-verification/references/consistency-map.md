# Formal Verification Skill Consistency Map

## 이력

| 차수 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1차 | 2026-04-17 | 초기 생성: SKILL.md + 4 references |
| 2차 | 2026-04-17 | SVA 추가: §10 + sva-patterns.md, triggers 6개 추가 |
| 3차 | 2026-04-17 | §6 환경 설정: MSYS2 → OSS CAD Suite로 전면 교체, SMT solver 5개 버전 테이블 추가 |
| 4차 | 2026-04-17 | 6-Check 수정: .sby/ifdef FORMAL 블록→포인터(Check2/6), SVA 코드블록 압축, FV-07 OSS CAD Suite 원칙으로 교체(Check5) |
| 5차 | 2026-04-17 | 6-Check FAIL 수정: FV-11 §5 .sby 제거(§5는 포인터만), SKILL.md §3 Cover "depth 없이"→"depth 범위 내에서", sby-workflow.md MSYS2→OSS CAD Suite 트러블슈팅 교체 |

---

## 원칙 위치 매핑

| 원칙 ID | 원칙 | SKILL.md 위치 | Reference 위치 |
|---------|------|--------------|----------------|
| FV-01 | assert → state space 증가 | §2 표 | directives.md §assert |
| FV-02 | assume → state space 감소 | §2 표 | directives.md §assume |
| FV-03 | assume은 satisfiable이어야 함 | §2 핵심규칙 | directives.md Vacuous 경고 |
| FV-04 | f_past_valid 첫 사이클 보호 | §5 `ifdef FORMAL 패턴 | directives.md §f_past_valid |
| FV-05 | `[script]` 경로는 파일명만 | §5 주의 | sby-workflow.md 흔한 실수 |
| FV-06 | Windows: mode prove 실패 | §6 주의사항 | sby-workflow.md Windows 트러블슈팅 |
| FV-07 | OSS CAD Suite: bin+lib 모두 PATH 필요 | §6 Windows 주의사항 | sby-workflow.md Windows 트러블슈팅 |
| FV-08 | anyseq = 매 사이클 임의값 | §5 Black-box Stub | sby-workflow.md Black-box Stub |
| FV-09 | k-induction unreachable CEX → assume 추가 | §3 Prove | bmc-prove-cover.md Prove 실패 디버깅 |
| FV-10 | cover UNREACHABLE → depth 증가 | §3 Cover | bmc-prove-cover.md Cover UNREACHABLE |
| FV-11 | Z3 = RTL 검증 기본 권장 solver | §1 표 | smt-solvers.md 주요 비교 |
| FV-12 | SVA `\|->` = overlapping, `\|=>` = non-overlapping | §10 표 | sva-patterns.md §Implication |
| FV-13 | SVA에서 disable iff = 절차적 if(!rst_n) | §10 disable iff | sva-patterns.md §disable iff |
| FV-14 | sby + SVA: read -sv 사용 (-formal 아님) | §10 sby 주의 | sva-patterns.md §sby 설정 |

---

## Cross-Reference 검증

| SKILL.md 참조 | 실제 파일 | 섹션 |
|--------------|-----------|------|
| `references/smt-solvers.md` | smt-solvers.md | 존재 |
| `references/directives.md` | directives.md | 존재 |
| `references/bmc-prove-cover.md` | bmc-prove-cover.md | 존재 |
| `references/sby-workflow.md` | sby-workflow.md | 존재 |
| `references/sva-patterns.md` | sva-patterns.md | 존재 |

---

## 수정 시 체크리스트

수정 후 반드시 확인:
- [ ] 원칙 변경 시 위 매핑 테이블 갱신
- [ ] SKILL.md 포인터 경로와 실제 파일명 일치 여부
- [ ] skill-validation-prompt.md Check 항목 반영 여부
- [ ] 이력 차수 업데이트
