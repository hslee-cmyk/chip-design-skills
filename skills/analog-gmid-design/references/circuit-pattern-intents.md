# 회로 패턴 의도 카탈로그 (연결 서명 기준)

회로 해석(소자가 무슨 역할로 어떤 영역에서 일하도록 설계됐는가)에 쓰는 패턴 지식 모음. 패턴은 **소자·회로 이름이 아니라 연결 서명**으로 찾는다.

## 규칙

- **해석은 연결과 원문만으로 한다.** netlist 연결(`netlist`·`ports`·`supply_nets`)에서 서명을 찾고, 의도와 수치는 원문(`assets/*/sources/`)으로 확인한다. topology 메타데이터(`device_roles`·`symmetry`·`sizing_roles`·`compensation`·`_comment` 류)는 근거로 쓰지 않는다 -- 그 태그가 틀렸는지를 이 카탈로그로 검사하는 쪽이다.
- **analog-grammar skill(`skills/analog-grammar/assets/idioms.py`)은 쓰지 않는다** -- 그 `m_diode_cascode` idiom은 P-1의 source 쪽 소자를 CASCODE로 부르며 승인 해석(triode 레벨 시프터)과 다르다(사용자 결정 user_decisions G-1, 2026-10-16).
- **topology 태그 키(`device_roles`·`symmetry`·`sizing_roles`·`compensation`)를 근거로 쓰지 않는다**(analog-grammar 근거로 만든 태그, 제거 예정 -- 사용자 결정 user_decisions G-1, 2026-10-16). 설계 의도 기록은 topology 최상위 `_design_intent` 주석 키(`_pattern` + 소자별 문자열)에 둔다.
- **엔진이 쓰는 패턴 정의는 해당 계획이 정본이고, 이 카탈로그는 그 정의를 따른다**(P-1 = `docs/01-plan/features/headroom-chain.plan.md` N3.2-1). 계획 정의가 바뀌면 이 문서를 같이 고친다.
- **새 패턴은 아래와 같은 칸을 같은 순서로 채운다**: 연결 서명 / 변형 / KVL / 의도된 영역 / 목적 / 엔진에 주는 결과 / 사례 / 출처 / 확신도. 칸을 비우지 않는다(모르면 '확인 안 함'으로 적는다).
- **소자·회로 이름은 '사례' 칸에만** 쓴다. 다른 칸은 단자·넷 관계로만 적는다.
- 출처 칸에는 보관 폴더 경로와 쪽(그림·열·행) 번호, 웹 링크를 같이 적는다. 원문 보관 규칙은 `assets/library/sources/README.md`.
- 엔진에 주는 결과가 아직 구현되지 않았으면 그렇다고 적는다(구현된 것처럼 쓰지 않는다).

---

## P-1. gate 공유 직렬 적층 (stacked diode / Sooch 셀 / self-cascode)

| 칸 | 내용 |
|---|---|
| 연결 서명 | headroom-chain 계획 N3.2-1과 같다: 같은 kind의 MOS X, Y가 (a) gate 넷이 같고(G) (b) X의 drain 넷 = Y의 source 넷(중간 넷 M)이며 (c) M의 DC 전류 단자가 X.drain·Y.source 둘뿐(직렬)일 때 X(아래, source 쪽 소자)를 **적층 triode 소자**로 본다. gate 넷 G가 레일이면 대상이 아니다(gate가 레일이면 레벨 시프터가 아니다). diode 조건은 서명에 없다. X.source = 기준 넷 R. |
| 변형 | (V1) **위 소자 Y가 diode**(Y.gate = Y.drain = G): stacked diode·Sooch 셀·바이어스 셀. 응용 A(레벨 시프터): cascode 소자 C의 gate = G, 지켜지는 아래 소자 B의 source = R, B.drain = C.source. 응용 B(Sooch 미러 바이어스): C의 gate = M, B의 gate = R. (V2) **위 소자 Y의 drain이 출력**(Y는 diode 아님): self-cascode 합성 트랜지스터(두 소자가 긴 L의 소자 하나처럼 동작). |
| KVL | NMOS 기준(PMOS는 VSG·VSD로 부호 반전). 서명: **VDS(X) = VGS(X) − VGS(Y)** (G−R = VGS(X), G−M = VGS(Y)). V1 응용 A: **VDS(B) = VGS(X) − VGS(C)** (G−R = VGS(X), G−B.drain = VGS(C)). V1 응용 B: VDS(B) = V(M) − VGS(C)(B.source 기준). |
| 의도된 영역 | Y: 포화(V1은 diode라 VDS = VGS). **X: 강반전에서 triode가 필연** -- 유도: X 포화 조건 VDS(X) ≥ VGS(X) − Vth(X)에 KVL을 넣으면 VGS(X) − VGS(Y) ≥ VGS(X) − Vth(X) ⇔ VGS(Y) ≤ Vth(X). Y가 강반전으로 도통하면 VGS(Y) > Vth(Y)이다. **전제: 두 소자의 bulk가 같은 넷**(같은 kind·같은 모델 bin). 그러면 Y의 source(M)가 X의 source(R)보다 bulk에서 멀어 VSB(Y) ≥ VSB(X), body 효과로 Vth(Y) ≥ Vth(X)이므로 조건이 깨진다 → X는 triode. bulk가 다른 넷이면 Vth(Y) < Vth(X)가 될 수 있어 유도가 성립하지 않는다 -- LUT로 확인한다(서로 다른 L bin·짧은 채널 효과도 같음). **약반전·moderate에서는 경계 가능**: 약반전 포화 조건은 VDS > 약 3~4 UT로 Vth와 무관하므로 VGS(X) − VGS(Y)가 그보다 크면 X가 포화일 수도 있다 -- LUT로 영역을 확인한다. |
| 목적 | V1 응용 A: 지켜지는 아래 소자 B의 VDS를 X의 VGS로 정하고 기준 넷 R을 따라가게 한다(R이 움직여도 cascode gate G가 R 기준으로 같이 움직임). X의 W/L을 Y보다 작게 해 VDS(X)·VDS(B)를 정한다 -- Sooch: 제곱 법칙에서 X의 Z/L = 1/3이면 VDS(X) = VON(원문 명시). B의 VDS를 '최소 포화 경계'에 둔다는 것은 해석이다(확신도 중간 -- 사례 원문에 명시 없음). V2: 합성 트랜지스터의 출력 컨덕턴스 감소. |
| 엔진에 주는 결과 | R-3(사용자 결정 C-2, headroom-chain 계획 N3.2·N3.3): 적층 triode 소자 X는 의도된 triode로 보고 **포화 검사(봉인 7·입력 창), SPICE `all_saturated`, 사슬 VDsat 합에서 뺀다.** 대신 X가 VDS를 정해 주는 **지켜지는 아래 소자의 포화 검사**를 남기고(남지 않으면 거부), X의 LUT 조회가 **LUT VDS 축 정의역 안인지 확인하는 게이트(fail-closed)**를 둔다. **계획 headroom-chain 진행 중 -- 아직 미구현.** 지금 엔진은 이 패턴을 알지 못한다. |
| 사례 | `current_reuse_telescopic_ota` bias-gen(둘 다 V1 응용 A): NMOS Y = M64(diode), X = M63, G = Vbias3, M = N64_63, R = Vy, C = M3a/M3b, B = M4a/M4b. PMOS Y = M57(diode), X = M58, G = Vbias2, M = N58_57, R = Vx, C = M2a/M2b, B = M1a/M1b. 원문 동작점(Xie·Chen Fig.8(b) p.8, Fig.6(b) p.6): VDS(M63) = 117.5 mV(차 계산 699.1 − 581.7 = 117.4), VDS(B) = 82.26 mV(차 계산 699.1 − 616.9 = 82.2); VSD(M58) = 189.3 mV(차 계산 748.3 − 559 = 189.3), VSD(B) = 99.72 mV(차 계산 748.3 − 648.6 = 99.7). Sooch 특허 Fig.3(V1 응용 B): Y = 40(diode), X = 42(Z/L 1/3), M = node A(= VT+2VON, 44·48의 gate), R = node B(= VT+VON, 46·50의 gate); 출력 cascode C = 48, 아래 소자 B = 50, VDS(50) = (VT+2VON) − (VT+VON) = VON. Sánchez-Sinencio p.19의 self-cascode(V2): 아래 M1 = X, 위 M2 = Y. |
| 출처 | headroom-chain 계획 N3.2-1(정의)·N3.2-2·N3.3(R-3 처리), 사용자 결정 C-1·C-2·G-1(user_decisions, 2026-10-16). Sooch, US 4,550,284 (1985): `assets/library/sources/current_reuse_telescopic_ota__sooch_1985/` -- Fig.3 PDF p.3, 42 Z/L 1/3 = PDF p.5 3열 60~64행, node A = VT+2VON = 3열 66행~4열 2행, "transistor 42 in its resistive region" = 4열 24~29행, 식 (1)~(7) = 4열 36행~. [Google Patents](https://patents.google.com/patent/US4550284A/en) · [USPTO PDF](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4550284). Sánchez-Sinencio, LV tutorial (2000): `assets/library/sources/current_reuse_telescopic_ota__sanchez_sinencio_2000/` -- p.19 self-cascode 정의, p.20 "M2 saturation, M1 linear", p.21 "M1 always operates in linear region", p.22 참고문헌 1. [TAMU PDF](https://people.engr.tamu.edu/s-sanchez/LV-Dallas-IEEE-Tutorial.PDF). Galup-Montoro et al., JSSC 29(9) 1994: 원본 미보관(유료, 위 tutorial p.22가 인용). 사례 수치: `assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/` Fig.8 p.8·Fig.6 p.6. |
| 확신도 | 서명·KVL·강반전 triode 유도(bulk 같은 넷 전제): 높음(연결과 식만으로 성립). '최소 포화 경계' 목적: 중간(해석, 원문 명시 없음). 사례 회로 원문 동작점의 실제 영역: 낮음~중간 -- VDS(M63) 117.5 mV ≈ 4.5 UT, VSD(M58) 189.3 mV ≈ 7.3 UT(UT ≈ 25.9 mV, 300 K)로 약반전·moderate라면 포화 문턱(약 3~4 UT)을 넘을 수 있다(LUT 확인 전). 사용자 승인 2026-10-16(C-1/I-1). |
