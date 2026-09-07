# self-test 회귀 기준선 (2026-09-07 캡처)

계획 문서 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` §8.8이 요구하는
"이관 전/후 동일 PASS/FAIL 집합" 대조의 **기준선**이다. 대조 단위는 **stdout 전체 diff**다.

## 왜 새로 떴나

§8.8이 기준선으로 지목했던 `assets/selftest_session6*.log` 6개는 전부
**`sizing_recipe.py`의 출력**이고 날짜도 2026-08-04로 오래됐다 -- `stick_diagram.py`의
기준선은 저장소에 아예 없었다. 그 상태로는 self-test 분리 작업의 회귀를 판정할 수 없다.

## 재생성 / 대조 방법

```bash
cd skills/analog-gmid-design/assets
/c/Python314/python.exe stick_diagram.py  > /tmp/sd.log 2>&1
/c/Python314/python.exe sizing_recipe.py  > /tmp/sr.log 2>&1
diff tests/baseline/stick_diagram.selftest.baseline.log /tmp/sd.log
diff tests/baseline/sizing_recipe.selftest.baseline.log /tmp/sr.log
```

차이가 0줄이어야 회귀 없음이다.

## 결정론 전제

이 대조가 성립하려면 출력이 실행마다 같아야 한다. 캡처 시점에 `stick_diagram.py`의
출력 **7줄**이 파이썬 문자열 해시 랜덤화 때문에 실행마다 흔들리는 것을 발견해
`_sorted_setmap()` 신설 + 정렬 출력으로 고쳤다(표시 전용 수정, 판정 로직 무변경).
`PYTHONHASHSEED`를 1/2/3/4/5로 바꿔 돌려도 두 로그 모두 바이트 동일함을 확인했다.
새 비결정 출력이 들어오면 이 대조가 먼저 깨지므로, 그 자체가 회귀 감지기 역할을 한다.
