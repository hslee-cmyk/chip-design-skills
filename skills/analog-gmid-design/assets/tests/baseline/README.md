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

## 갱신 이력

### 2026-09-09 — B20(`_solve_vgs` 비단조 역보간) 수정으로 각 로그 **1줄** 갱신

`SemiEmpiricalGmIdLUT._solve_vgs()`가 "gm/ID는 VGS에 단조감소"를 전제로 `np.argsort` 후
전역 역보간하던 것을 **rightmost root**(목표를 품는 가장 오른쪽 구간에서만 보간)로 고쳤다.
실측 LUT는 PMOS가 비단조라 그 전제가 깨져 있었고(`tests/probe_gm_id_monotonicity.py`),
서로 다른 branch의 VGS가 정렬에서 뒤섞여 **W가 조용히 틀리고 있었다**.

바뀐 줄은 각 로그에서 정확히 1줄이다:

    sizing_recipe   L5 전체회로 PASS 줄 -- cmrr 80.68 -> 80.37 dB, psrr 92.58 -> 92.21 dB
                    (gain_db=76.38 / mismatch_sigma_mV=3.01은 불변)
    stick_diagram   two_stage_ota known-limitation 안내 줄 -- 'stage1_out' VDS 합
                    2.15465 -> 2.37965V. 추적하니 `stage1_ref` 스택에서 M3(0.5625)와
                    M5(0.3375)의 값이 **서로 맞바뀐 것**이고, 그 스택의 KVL 합은 양쪽 다
                    정확히 1.8V로 불변이다. 이 테스트는 원래부터 KVL ValueError로 실패하도록
                    문서화된 known-limitation이고, 판정(같은 이유로 실패)은 그대로 통과한다.

**단조 구간은 한 비트도 안 바뀐다**: NMOS 전 격자 16,186건 대조에서 구/신 결과가 완전히
동일함을 확인했다(같은 방향·같은 연산 순서 `slope*(x-x0)+y0`로 보간하도록 구현). 값이
달라지는 것은 PMOS의 비단조 구간뿐이고, `two_stage_ota` 실주행에서 달라진 조회 1,895건은
**전부 긴 L(2.9~3.7µm)**이며 **Δ가 전부 양(+)**이다(물리적으로 옳은 강반전 해로 이동).
최악은 `gm_id=6, L=3.71µm, vds=0.30`에서 VGS 0.719 -> 1.333V다.

파일럿 재탐색도 정상 완주하고 선언된 제약 5개를 전부 만족한다(gain_db 65.75>=54,
mismatch 3.34<=5.0, cmrr 66.17>=60, psrr 81.06>=60, classab 0.1408<=0.15).
