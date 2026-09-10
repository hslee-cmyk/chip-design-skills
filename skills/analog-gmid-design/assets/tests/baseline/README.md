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

### 2026-09-09 — B25(적층 diode 연립) + B9(vsb 노드전압 유도)로 `sizing_recipe` **1줄** 갱신

`stick_diagram` 기준선은 **바뀌지 않았다**(diff 0줄).

바뀐 줄은 L5 전체회로 PASS 줄 하나다:

    gain_db          76.38 -> 76.23
    mismatch_sigma_mV 3.01 -> **2.19**   (27% 개선)
    cmrr_estimate_db 80.37 -> 80.02
    psrr_estimate_db 92.21 -> 92.48

무엇이 바뀌었나:

1. **B9** -- `vsb`를 노드전압에서 유도하도록 배선했다(`reconcile_vsb_from_nodes()` 신설 +
   `audit_vsb_consistency()`를 게이트로). 그 전까지 파일럿 51소자 중 **26개**의 vsb가
   물리와 어긋나 있었다(레일 소스인데 0이 아닌 것 4개, 비레일인데 0인 것 15개, 값이 서로
   바뀐 것 등 7개). vsb는 LUT의 VS 축이라 **모든 조회를 틀리게** 했다.
2. **B25** -- 적층 diode(아래쪽 소스가 위쪽 드레인)의 vds를 **함께** 푼다. 아래쪽의 vsb가
   `vsb_up + v_up`으로 누적되므로 독립으로 풀면 안 된다.
3. `L_role: bias_replica`(M11a/M11b/M20a/M20b) -- class-AB 배터리의 전압기준이지 신호경로
   미러가 아니다(사용자 확정).
4. L5c 픽스처의 `r_cmfb_vocdes`를 중점(0.11) 대신 **하한(0.02)**에 고정 -- 중점은 M39/M40에
   실제 최적점의 **17배** 전류를 흘려 바디효과를 넣은 뒤로는 도달 불가능한 점이 됐다.

mismatch가 좋아진 것은 우연이 아니다: 적층 쌍을 고를 때 **W가 서로 가까운 쌍**을 고르도록
했기 때문이다(같은 60개 성립 쌍 중 min-sum은 W 2.320/1.415µm으로 비 1.64라 레이아웃이
공통 finger 폭을 못 찾았고, W 균형 쌍은 4.305/4.802로 비 1.12다). 배터리 기준으로서
매칭에도 유리한 선택이다.

파일럿 재평가: gain_db 65.5547(>=54), **area_um2 517.61µm²(925.52에서 44% 감소)**,
cmrr 66.11(>=60), psrr 81.35(>=60). vsb 감사 게이트도 통과한다.

### 2026-09-09 — B19'(미러 15소자 배선)으로 `sizing_recipe` **2줄** 갱신

`stick_diagram` 기준선은 또 바뀌지 않았다(diff 0줄).

    M18_bg(diode) vds   0.75  -> **0.825V**
    gain_db            76.23  -> 76.35
    mismatch_sigma_mV   2.19  -> **1.74**   (누적 3.01 -> 1.74, 42% 개선)
    cmrr_estimate_db   80.02  -> 76.12
    psrr_estimate_db   92.48  -> 96.03

`M18_bg`가 0.75V에서 **0.825V**로 오른 것은 B22가 미리 계산한 값과 **정확히 일치**한다 --
미러 인식 창이 "VGS를 공유하는 소자 7개의 W 한계까지 함께 만족"하도록 하한을 올린 결과다
(계획 §10.3 B22의 실측표: pmos:Vbias1의 `lo_group`이 0.7875, 보수적 바닥으로는 0.8250).

미러가 실제로 강제됐음은 VGS 퍼짐으로 확인된다:

    그룹(레퍼런스)   소자   배선 전      배선 후
    M18_bg           8     464.2 mV    **0.0000 mV**
    M66              8     663.2 mV    **0.0000 mV**
    M36a             2       9.2 mV    **0.0000 mV**

미러비(ID비 vs W비)도 대부분 1.0배 근처(0.877~1.106)로 맞는다. 어긋나는 셋(M6 14.9x,
M7 13.4x, M5 0.58x)은 전부 **tail**인데 `L_role`이 `bias_replica`(0.18µm)라 나머지
(`mirror`, 0.375µm)와 L도 vds도 다르다 -- `W = L·ID/IDu(VGS,L,vds)`이므로 VGS가 같아도
W비가 ID비와 다른 것이 정상이다(§10.2 A4가 이미 짚은 내용: "미러에 VDS도 같게 강제하라"는
물리적으로 틀리다).

파일럿: gain_db 65.5547(>=54), area_um2 584.59µm², cmrr 62.82(>=60), psrr **104.30**(>=60).

- **2026-09-10** -- `sizing_recipe.selftest.baseline.log` **13줄 추가**(삭제 0줄).
  `require_declared_spec_source()` 게이트의 자기시험 4건이 새로 들어갔다. 이 게이트는
  라이브러리 회로를 출처 선언 없는 spec으로 사이징하는 것을 거부한다 -- 조사 스크립트들이
  spec을 손으로 복붙해 쓰다가 정본(`workspaces/run_harness.py`의 `SPECS`)과 갈린 사고의
  재발 방지 장치다. 자기시험을 같이 넣은 이유는 **게이트를 처음 만들었을 때 그것이 조용히
  죽어 있었기** 때문이다(모듈이 `os`를 최상위 import하지 않아 NameError가 났고
  `except Exception: return`이 그걸 삼켜 늘 통과했다). 그 광범위 except는 제거했다.

- **2026-09-10 (2)** -- L5c 완주 줄의 수치가 바뀌었다(**1줄**, 삭제 0/추가 0):

      gain_db 76.35 -> 61.30, mismatch 1.74 -> 3.01, cmrr 76.12 -> 60.04, psrr 96.03 -> 80.16

  class-AB 배터리 KVL(`stack_kvl_vgs_limit()`)을 gm_id 탐색에 배선한 결과다. **옛 수치는
  물리적으로 불가능한 동작점에서 잰 값이었다** -- 그 점(L_stage2out=0.575um)에서는
  `V_bat = vdd - VGS(M15) - VGS(M16) = -0.024V`로 Monticelli floating battery의 전압이
  음수였는데, 그 KVL을 아무도 안 봐서 통과했었다. 새 수치는 `V_bat > 0`인 점의 값이다.
  픽스처는 `stop_after_sizing=True`로 사이징까지만 본다(레이아웃 핑거 배정은 별개 항목).
