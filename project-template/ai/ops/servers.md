# Servers / Simulation Access — {{PROJECT_NAME}}

## 원격 빌드/검증 서버 (있으면)

| 항목 | 값 |
|------|-----|
| SSH alias | <!-- 예: cloud0 (~/.ssh/config 등록) --> |
| Host / Port / User | <!-- ... --> |
| OS / login shell | <!-- 예: CentOS 7 / tcsh --> |
| Key | <!-- 예: ~/.ssh/id_ed25519_nopass (passphrase 없는 키) --> |

## AI 작업 표준 — ssh-mcp 사용 (raw SSH 금지)

프롬프트에서 `<server>에서 X해줘` → `mcp__ssh__ssh_run(command='<shell> -lc "X"')`.

- login shell이 **tcsh**면 `tcsh -lc "..."` 로 래핑해야 EDA PATH(`~/.tcshrc`)가 적용된다.
- ⚠️ **tcsh `2>&1` 금지** — `&1`을 파일명으로 해석해 파일 `1` 생성. stdout+stderr 합치기는 **`>&`** (tcsh/bash 공통).
- ⚠️ tcsh `2>/dev/null` 도 Ambiguous redirect.

### 실행 패턴
```
# 단기(<2분): ssh_run + timeout
mcp__ssh__ssh_run  command='tcsh -lc "cd <sim dir> && source eda.env && ./run_compile"'  timeout=120
# 장기(세션 초과): ssh_bg_run + ssh_bg_poll
job = mcp__ssh__ssh_bg_run(command='tcsh -lc "..."'); mcp__ssh__ssh_bg_poll(job_id=job.job_id)
```

## 시뮬레이션 디버깅 — xcelium-mcp (ssh 불필요)
```
# Batch: 비대화형 + dump
mcp__xcelium-mcp__sim_batch_run  test_name='TEST'  dump_signals=['sig1','sig2']
# Bridge: interactive probing
mcp__xcelium-mcp__sim_start test_name='TEST' mode='debug' → connect_simulator → sim_run duration='20ms' → shutdown
```
정적 분석만으로 순환하지 말고, 원인 미특정 시 **즉시 xcelium-mcp 프로빙**. 상세: `.ai/knowledge/`.

## 검증 작업 경로 (서버)
| 구분 | 경로 |
|------|------|
| 저장소 루트 | <!-- ~/git.clone/<repo>/ --> |
| 시뮬 환경 | <!-- .../sim/ncsim, .../sim/uvm --> |
