# library topology 원문

library 회로(`assets/library/<회로>.*`)의 topology·spec 근거가 된 원문을 그대로 보관한다. spec 출처(`source`·`record`)와 topology 판독은 이 폴더의 경로와 쪽·그림 번호를 인용한다.

## 규칙
- 원문 하나 = 폴더 하나: `<엔진 회로 이름>__<제1저자>_<연도>/`. 원문 하나를 여러 회로가 쓰면 회로 이름을 `+`로 잇는다(사본은 하나만).
  - `source.pdf`: 원본 사본 (`paper.md` 머리에 원래 위치와 sha256)
  - `paper.md`: 쪽 단위 텍스트 + 쪽 렌더 이미지 링크. 수식·표·그림은 텍스트가 깨질 수 있으니 `pages/pNN.png`로 확인한다.
  - `pages/`(150 dpi 쪽 렌더), `images/`(내장 이미지)
- 변환: `python tools/pdf_to_md.py convert <pdf> assets/library/sources/<폴더> "<제목>" "<웹 출처>"` (skill 폴더에서, PyMuPDF)
- 새 원문을 넣으면 아래 표에 한 줄 추가한다. 웹 링크를 못 찾았으면 '찾지 못함'으로 적는다.
- 원본 우선순위: `G:/내 드라이브/work/Todoc/논문모음/`·`G:/내 드라이브/work/Todoc/기술문서/Gm_over_Id/`(하위 폴더 포함) → 다른 로컬 → 합법 공개본 다운로드. `paper.md` 머리의 원본 위치는 이 순서로 찾은 첫 파일.
- held-out 시험 회로의 원문은 `assets/heldout/sources/`(같은 형식).

## 목록

| 엔진 회로 | 원문 | 웹 | 파일 | 핵심 위치 |
|---|---|---|---|---|
| current_reuse_telescopic_ota | Xie, Chen, "A 126µW Current-Reuse Telescopic OTA with Class-AB Output Stage" (UT Austin, 2019) | 찾지 못함 | [paper.md](current_reuse_telescopic_ota__xie_chen_2019/paper.md) · [source.pdf](current_reuse_telescopic_ota__xie_chen_2019/source.pdf) | Table I p.1, Fig.1·2 p.2, Fig.3~5 p.3, Fig.6~9(치수·DC) p.6~9 |
| common_gate_amplifier | P.E. Allen, CMOS Analog Circuit Design, Lecture 20 'Low Input Resistance Amplifiers' (6/24/14), 강의자료 | [aicdesign.org lecture20-140624.pdf](https://aicdesign.org/wp-content/uploads/2018/08/lecture20-140624.pdf) | [paper.md](common_gate_amplifier__allen_2014/paper.md) · [source.pdf](common_gate_amplifier__allen_2014/source.pdf) | Page 20-2 = p.2 그림 060609-01 오른쪽(M1~M3) |
| pushpull_follower_buffer, sf_pushpull_output_opamp, two_stage_ota_sf | P.E. Allen, CMOS Analog Circuit Design, Lecture 26 'Buffered Op Amps' (6/25/14), 강의자료 | [aicdesign.org lecture26-140625.pdf](https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf) | [paper.md](pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/paper.md) · [source.pdf](pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf) | p.4 Push-Pull Follower(060706-02) · p.5 Two-Stage with Follower(060706-03) · p.6 Fig. 7.1-1 SF Push-Pull Output |
| two_stage_ota, folded_cascode | F. Maloberti, 'Layout of Analog CMOS Integrated Circuit, Part 2: Transistors and Basic Cells Layout' (강의 슬라이드, 2004) | 저자 게시처 찾지 못함(제3자 재게시만: slideshare layout02-1) | [paper.md](two_stage_ota+folded_cascode__maloberti_2004/paper.md) · [source.pdf](two_stage_ota+folded_cascode__maloberti_2004/source.pdf) | p.28 Example 1 2단 OTA(~p.33) · p.34 Example 2 Folded Cascode(~p.38) |
| ngcc_3stage_ff | J.-S. Lee, J. H. Bae, H.-Y. Kim, J.-Y. Um, J.-Y. Sim, H. J. Park, 'A Design Guide of 3-stage CMOS Operational Amplifier with Nested Gm-C Frequency Compensation', JSTS 7(1):20-27, 2007 | [doi:10.5573/JSTS.2007.7.1.020](https://doi.org/10.5573/JSTS.2007.7.1.020) | [paper.md](ngcc_3stage_ff__lee_2007/paper.md) · [source.pdf](ngcc_3stage_ff__lee_2007/source.pdf) | Fig. 3 저널 p.24 = PDF p.5 · Table 5 저널 p.25 = PDF p.6 |
| nmcnr_amplifier | K. N. Leung, P. K. T. Mok, W.-H. Ki, 'Right-Half-Plane Zero Removal Technique for Low-Voltage Low-Power Nested Miller Compensation CMOS Amplifier', ICECS 1999, pp.599-602 | IEEE Xplore(유료) 링크 찾지 못함 | [paper.md](nmcnr_amplifier__leung_1999/paper.md) · [source.pdf](nmcnr_amplifier__leung_1999/source.pdf) | Fig. 3·Table 1 저널 p.602 = PDF p.4 (topology의 'p.601'은 오기) |

## pages/·images/
각 원문 폴더의 `pages/`(쪽 렌더)·`images/`(PDF 내장 비트맵)는 `source.pdf`에서 다시 만들 수 있는 생성물이라 git에 넣지 않는다(`.gitignore`, 사용자 2026-10-14). 없으면 skill 폴더에서 `python tools/pdf_to_md.py ensure`를 실행하면 없는 파일만 만든다(같은 PyMuPDF에서 바이트 동일 확인). 새 원문 변환은 `python tools/pdf_to_md.py convert <pdf> <출력폴더> "<제목>" "<웹 출처>"`.
