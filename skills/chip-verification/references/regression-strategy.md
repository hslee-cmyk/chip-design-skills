# Regression Strategy for RTL Changes

## RTL 변경 영향 분석

### 변경 유형별 검증 전략

| RTL 변경 유형 | 영향 범위 | 필수 테스트 |
|--------------|----------|------------|
| 버그 수정 (로직) | 해당 기능 | 실패 테스트 + 관련 기능 |
| 타이밍 변경 | 파이프라인 | 사이클 정확 테스트 전체 |
| 인터페이스 변경 | TB 수정 필요 | 전체 회귀 |
| 새 기능 추가 | 새 기능 | 새 테스트 + 기존 회귀 |
| 리팩토링 | 전체 | 전체 회귀 |

## 변경 전 체크리스트

### 1. RTL 변경 사항 문서화
```
변경 파일: my_module.v
변경 내용: stage2 레지스터 추가
이유: 타이밍 개선
영향: latency 1 → 2 cycles
```

### 2. TB 영향 분석
```
[ ] Interface 변경 필요?
[ ] Reference Model 수정 필요?
[✓] Scoreboard 타이밍 조정 필요?
[ ] Coverage 추가 필요?
[ ] 새 테스트 시나리오 필요?
```

### 3. Reference Model 동기화
```systemverilog
// RTL 변경 전
class ref_model;
    int pipeline_depth = 1;  // 기존
endclass

// RTL 변경 후
class ref_model;
    int pipeline_depth = 2;  // 수정됨
endclass
```

## 회귀 테스트 레벨

### Level 1: Sanity (5분)
```bash
# 기본 기능 확인
make sanity
```
- 리셋 동작
- 기본 read/write
- 단일 트랜잭션

### Level 2: Focused (30분)
```bash
# 변경 관련 테스트
make focused AREA=pipeline
```
- 변경된 기능 집중 테스트
- 관련 에지 케이스
- 실패했던 시드 재실행

### Level 3: Full Regression (4시간+)
```bash
# 전체 테스트
make regress
```
- 모든 테스트 케이스
- 다양한 시드
- 코너 케이스

## 테스트 우선순위

### 변경 유형별 필수 테스트

#### 파이프라인/타이밍 변경
```
[1순위]
- back_to_back_transaction_test
- pipeline_stall_test  
- latency_check_test

[2순위]
- random_delay_test
- throughput_test
```

#### FSM 변경
```
[1순위]
- all_state_transition_test
- illegal_state_test
- reset_during_operation_test

[2순위]
- random_sequence_test
```

#### 데이터 경로 변경
```
[1순위]
- boundary_value_test (0, MAX, overflow)
- all_opcodes_test

[2순위]
- random_data_test
```

## Coverage 기반 회귀

### 변경 후 Coverage 확인
```tcl
# 변경 전후 coverage 비교
urg -dir baseline.vdb -dir new.vdb -diff -report diff_report

# Hole 확인
grep "0%" coverage_report.txt
```

### Coverage 목표
```
변경 후 확인 사항:
- [ ] 기존 coverage 유지 (regression 없음)
- [ ] 새 기능 coverage 100% (해당 시)
- [ ] 변경된 로직 coverage 100%
```

## 자동화 스크립트

### 회귀 실행 스크립트
```bash
#!/bin/bash
# run_regression.sh

CHANGE_TYPE=$1  # sanity, focused, full

case $CHANGE_TYPE in
    sanity)
        TESTS="sanity_*"
        TIMEOUT=300
        ;;
    focused)
        TESTS="*pipeline* *timing*"
        TIMEOUT=1800
        ;;
    full)
        TESTS="*"
        TIMEOUT=14400
        ;;
esac

# 실행
for test in $TESTS; do
    timeout $TIMEOUT make run TEST=$test
    if [ $? -ne 0 ]; then
        echo "FAIL: $test" >> failures.log
    fi
done

# 결과 요약
echo "=== Regression Summary ==="
echo "Total: $(ls -1 *.log | wc -l)"
echo "Pass:  $(grep -l PASS *.log | wc -l)"
echo "Fail:  $(grep -l FAIL *.log | wc -l)"
```

### CI/CD 통합
```yaml
# .gitlab-ci.yml 예시
stages:
  - sanity
  - regression

sanity_test:
  stage: sanity
  script:
    - make sanity
  timeout: 10m
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

full_regression:
  stage: regression
  script:
    - make regress
  timeout: 6h
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

## 실패 분석 프로세스

### 새로운 실패 발생 시
```
1. 기존 테스트가 실패?
   → RTL 변경이 기존 기능 깨뜨림 (regression bug)
   → 변경 롤백 또는 수정 필요

2. 새 테스트가 실패?
   → 테스트 오류 또는 spec 불일치
   → 테스트와 RTL 모두 검토

3. 랜덤 시드에서만 실패?
   → 에지 케이스 발견
   → 시드 저장 후 디버그
```

### 실패 기록 템플릿
```
Test: pipeline_stall_test
Seed: 12345
Fail Type: Scoreboard mismatch
Root Cause: RTL stage2 latency 변경 미반영
Fix: ref_model pipeline_depth 2로 수정
Verified: 2024-01-15
```
