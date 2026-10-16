# 회로 패턴 의도 카탈로그 (연결 서명 기준)

회로 해석(소자가 무슨 역할로 어떤 영역에서 일하도록 설계됐는가)에 쓰는 패턴 지식 모음. 패턴은 **소자·회로 이름이 아니라 연결 서명**으로 찾는다.

## 규칙

- **해석은 연결과 원문만으로 한다.** netlist 연결(`netlist`·`ports`·`supply_nets`)에서 서명을 찾고, 의도와 수치는 원문(`assets/*/sources/`)으로 확인한다. topology 메타데이터(`device_roles`·`symmetry`·`sizing_roles`·`compensation`·`_comment` 류)는 근거로 쓰지 않는다 -- 그 태그가 틀렸는지를 이 카탈로그로 검사하는 쪽이다.
- **analog-grammar skill(`skills/analog-grammar/assets/idioms.py`)은 쓰지 않는다** -- 그 `m_diode_cascode` idiom은 P-1의 source 쪽 소자를 CASCODE로 부르며 승인 해석(triode 레벨 시프터)과 다르다.
- **topology 태그 키(`device_roles`·`symmetry`·`sizing_roles`·`compensation`)를 근거로 쓰지 않는다**(analog-grammar 근거로 만든 태그, 제거 예정 -- 사용자 2026-10-16). 설계 의도 기록은 topology 최상위 `_design_intent` 주석 키(`_pattern` + 소자별 문자열)에 둔다.
- **새 패턴은 아래와 같은 칸을 같은 순서로 채운다**: 연결 서명 / KVL / 의도된 영역 / 목적 / 엔진에 주는 결과 / 사례 / 출처 / 확신도. 칸을 비우지 않는다(모르면 '확인 안 함'으로 적는다).
- **소자·회로 이름은 '사례' 칸에만** 쓴다. 다른 칸은 단자·넷 관계로만 적는다.
- 출처 칸에는 보관 폴더 경로와 쪽(그림·열·행) 번호, 웹 링크를 같이 적는다. 원문 보관 규칙은 `assets/library/sources/README.md`.
- 엔진에 주는 결과가 아직 구현되지 않았으면 그렇다고 적는다(구현된 것처럼 쓰지 않는다).

---

## P-1. gate 공유 직렬 적층 (stacked diode / Sooch 셀 / self-cascode)

| 칸 | 내용 |
|---|---|
| 연결 서명 | 같은 종류 MOS 두 개 D(diode 쪽)·S(source 쪽). (1) D: gate = drain(diode 연결). (2) S: gate = D의 gate와 같은 넷(G). (3) D.source = S.drain = 넷 X이고, **X의 drain·source 단자는 이 둘뿐**이다(진짜 직렬 -- gate는 붙을 수 있다). (4) S.source = 기준 노드 R. 응용 A(레벨 시프터)일 때 추가로: cascode 소자 C의 gate = G, 보호되는 아래 소자 B의 source = R, B.drain = C.source. 응용 B(Sooch 미러 바이어스)는 C의 gate = X, B의 gate = R(아래 '사례'). |
| KVL | NMOS 기준(PMOS는 VSG·VSD로 부호 반전). 셀: **VDS(S) = VGS(S) − VGS(D)** (G−R = VGS(S), G−X = VGS(D)). 응용 A: **VDS(B) = VGS(S) − VGS(C)** (G−R = VGS(S), G−B.drain = VGS(C)). 응용 B: VDS(B) = V(X) − VGS(C) (B.source 기준). |
| 의도된 영역 | D: 포화(diode 연결이라 VDS = VGS). **S: 강반전에서 triode가 필연** -- 유도: S 포화 조건 VDS(S) ≥ VGS(S) − Vth(S)에 KVL을 넣으면 VGS(S) − VGS(D) ≥ VGS(S) − Vth(S) ⇔ VGS(D) ≤ Vth(S). D가 강반전으로 도통하면 VGS(D) > Vth(D)이고, Vth(D) ≥ Vth(S)(같은 종류·같은 모델 bin, D 쪽 body 효과는 Vth를 올리기만 함)이면 조건이 깨진다 → S는 triode. **약반전·moderate에서는 경계 가능**: 약반전 포화 조건은 VDS > 약 3~4 UT로 Vth와 무관하므로 VGS(S) − VGS(D)가 그보다 크면 S가 포화일 수도 있다 -- 이때는 LUT로 영역을 확인한다. Vth(D) < Vth(S)가 될 수 있는 경우(서로 다른 L bin·짧은 채널 효과)도 LUT 확인 대상. |
| 목적 | 아래 소자 B의 VDS를 **최소 포화 경계로 고정**하고 기준 노드 R을 따라가게 한다(R이 움직여도 cascode gate G가 R 기준으로 같이 움직임). S의 W/L을 D보다 작게 하면 VDS(S)·VDS(B)를 정할 수 있다 -- Sooch: 제곱 법칙에서 S의 Z/L = 1/3이면 VDS(S) = VON. self-cascode 단독(응용 없음)일 때는 두 소자가 긴 L의 합성 트랜지스터 하나로 동작(출력 컨덕턴스 감소). |
| 엔진에 주는 결과 | R-3: S는 포화 검사에서 제외하고, 대신 **아래 소자 B의 VDS 검사**(VDS(B) ≥ 포화 경계)로 대체한다. **계획 headroom-chain 진행 중 -- 아직 미구현.** 지금 엔진은 이 패턴을 알지 못한다. |
| 사례 | `current_reuse_telescopic_ota` bias-gen: NMOS D = M64, S = M63, G = Vbias3, X = N64_63, R = Vy, C = M3a/M3b, B = M4a/M4b. PMOS D = M57, S = M58, G = Vbias2, X = N58_57, R = Vx, C = M2a/M2b, B = M1a/M1b. 원문 동작점(Xie·Chen Fig.8(b) p.8, Fig.6(b) p.6): VDS(M63) = 117.5 mV = 699.1 − 581.7, VDS(B) = 82.26 mV = 699.1 − 616.9; VSD(M58) = 189.3 mV = 748.3 − 559, VSD(B) = 99.72 mV ≈ 748.3 − 648.6. (둘 다 응용 A.) Sooch 특허 Fig.3(응용 B): D = 40, S = 42(Z/L 1/3), X = node A(= VT+2VON, 44·48의 gate), R = node B(= VT+VON, 46·50의 gate); 출력 cascode C = 48, 아래 소자 B = 50, VDS(50) = (VT+2VON) − (VT+VON) = VON. |
| 출처 | Sooch, US 4,550,284 (1985): `assets/library/sources/current_reuse_telescopic_ota__sooch_1985/` -- Fig.3 PDF p.3, 42 Z/L 1/3 = PDF p.5 3열 60~64행, node A = VT+2VON = 3열 66행~4열 2행, "transistor 42 in its resistive region" = 4열 24~29행, 식 (1)~(7) = 4열 36행~. [Google Patents](https://patents.google.com/patent/US4550284A/en) · [USPTO PDF](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4550284). Sánchez-Sinencio, LV tutorial (2000): `assets/library/sources/current_reuse_telescopic_ota__sanchez_sinencio_2000/` -- p.19 self-cascode 정의, p.20 "M2 saturation, M1 linear", p.21 "M1 always operates in linear region", p.22 참고문헌 1. [TAMU PDF](https://people.engr.tamu.edu/s-sanchez/LV-Dallas-IEEE-Tutorial.PDF). Galup-Montoro et al., JSSC 29(9) 1994: 원본 미보관(유료, 위 tutorial p.22가 인용). 사례 수치: `assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/` Fig.8 p.8·Fig.6 p.6. |
| 확신도 | 서명·KVL·강반전 triode 유도: 높음(연결과 식만으로 성립). 사례 회로 원문 동작점의 실제 영역: 중간(LUT 확인 전). 사용자 승인 2026-10-16(C-1/I-1). |
