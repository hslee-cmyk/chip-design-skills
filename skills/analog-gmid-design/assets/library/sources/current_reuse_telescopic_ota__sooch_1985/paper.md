# MOS Cascode Current Mirror (N. S. Sooch, US Patent 4,550,284, 1985)

- 원본 PDF: 로컬(G:/내 드라이브/work/Todoc/논문모음/·기술문서/Gm_over_Id/) 없음 → USPTO 공개본 다운로드 `https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4550284` (2026-10-16)
- 사본: `source.pdf` (sha256 `288d069bae492ac3a6191bc71ebb735aa695b899e5f375c670b6e47ff7e7d421`)
- 웹 출처: https://patents.google.com/patent/US4550284A/en
- 서지: N. S. Sooch, "MOS cascode current mirror", US Patent 4,550,284, 1985-10-29
- 핵심 위치(PDF 쪽 = 특허 쪽, 열:행):
  - Fig.3(발명 회로: 40 diode, 42 = 1/3 Z/L, node A = VT+2VON, node B = VT+VON, 출력 48·50): PDF p.3 (Sheet 2 of 2) 위 그림. Fig.4(3단 확장, 62 = 1/3, 64 = 1/5)는 같은 쪽 아래.
  - "transistor 42 is formed to comprise a channel width-to-length ratio, Z/L, one-third that of the remaining transistors": PDF p.5, 3열 60~64행
  - node A 전압 "a voltage at node A equal to VT+2VON and a voltage at node B equal to VT and VON": PDF p.5, 3열 66행~4열 2행
  - "operating transistor 42 in its resistive region, where connecting the gates of transistors 40 and 42 forces transistor 42 to remain in its resistive region": PDF p.5, 4열 24~29행 (같은 문장의 "Providing a VDS of transistor 43 equal to VON"의 43은 Fig.3·식 (4)(VDS1 = 42의 VDS = VON)로 보아 42의 오기로 보임)
  - 식 (1)~(7)(triode 42 = 포화 40 전류 등식 → VDS1 = VGS1−VGS2 = VON → (Z/L)1 = (Z/L)2/3): PDF p.5, 4열 36행~끝
- 엔진 연결: `assets/library/current_reuse_telescopic_ota.topology.json` device_roles M63·M64·M57·M58 의 `_design_intent_comment`(gate 공유 직렬 적층의 source 쪽 소자 triode 의도 근거)
- 쪽 수: 7
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 이 PDF는 스캔 이미지라 텍스트 층이 없다 -- 내용은 `pages/pNN.png`로 확인할 것.
- `pages/`·`images/` 는 git 에 없다. 없으면 skill 폴더에서 `python tools/pdf_to_md.py ensure` 로 만든다.

---

## p.1

![p.1](pages/p01.png)

![p.1 내장 이미지 1](images/p01_1.png)

---

## p.2

![p.2](pages/p02.png)

![p.2 내장 이미지 1](images/p02_1.png)

---

## p.3

![p.3](pages/p03.png)

![p.3 내장 이미지 1](images/p03_1.png)

---

## p.4

![p.4](pages/p04.png)

![p.4 내장 이미지 1](images/p04_1.png)

---

## p.5

![p.5](pages/p05.png)

![p.5 내장 이미지 1](images/p05_1.png)

---

## p.6

![p.6](pages/p06.png)

![p.6 내장 이미지 1](images/p06_1.png)

---

## p.7

![p.7](pages/p07.png)

![p.7 내장 이미지 1](images/p07_1.png)
