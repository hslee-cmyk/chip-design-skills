# held-out 시험 회로 원문

held-out 시험 회로(`assets/heldout/<회로>.*`, library 미등록)의 topology·spec 근거가 된 원문을 그대로 보관한다. 형식은 `assets/library/sources/README.md`와 같다.

## 규칙
- 원문 하나 = 폴더 하나: `<엔진 회로 이름>__<제1저자>_<연도>/`
  - PDF 원문: `source.pdf` + `paper.md`(쪽 단위 텍스트, 머리에 원본 위치·sha256·웹 출처·그림·표 위치·엔진 연결) + `pages/`(150 dpi 쪽 렌더) + `images/`(내장 이미지)
  - PDF가 아닌 원문(회로도 저장소 등): 원본 파일을 바이트 그대로 복사 + `source.md`(파일별 원본 경로·sha256·내용)
- 변환: `python tools/pdf_to_md.py <pdf> assets/heldout/sources/<폴더> "<제목>" "<웹 출처>"` (skill 폴더에서, PyMuPDF)

## 목록

| 엔진 회로 | 원문 | 웹 | 파일 | 핵심 위치 |
|---|---|---|---|---|
| rfc_ota | P. J. I. Matibag (지도 J. Cosp Vilella), 'Design and test of a CMOS folded cascode OTA with current recycling', UPC 석사논문 2024 | [upcommons PDF](https://upcommons.upc.edu/bitstreams/a99028f7-5d7f-447a-b086-c1f4effcdb1b/download) | [paper.md](rfc_ota__matibag_2024/paper.md) · [source.pdf](rfc_ota__matibag_2024/source.pdf) | p.22 Fig.5 · p.27 Table 2 · p.28 Fig.6 · p.32 Fig.8 · p.34 Fig.9 · p.37 Fig.11 |
| erfc_ota | C. Wu, P. Cai, J. Li, J. Xie, Z. Luo, 'Power-Efficient Recycling Folded Cascode OTA Based on Nested Local Feedback and Adaptive Biasing', Sensors 25(8):2523, 2025 | [PMC12031453 PDF](https://pmc-oa-opendata.s3.amazonaws.com/PMC12031453.1/PMC12031453.1.pdf) · [MDPI](https://www.mdpi.com/1424-8220/25/8/2523) | [paper.md](erfc_ota__wu_2025/paper.md) · [source.pdf](erfc_ota__wu_2025/source.pdf) | p.8 Figure 6 · p.9 Table 1 · p.5 Fig.3b · p.6 Fig.4a · p.14 Table 2 |
| r2r_opamp | R. Hogervorst, J. P. Tero, R. G. H. Eschauzier, J. H. Huijsing, 'A Compact Power-Efficient 3 V CMOS Rail-to-Rail Input/Output Operational Amplifier for VLSI Cell Libraries', IEEE JSSC 29(12):1505-1513, 1994 | [TU Delft repository](https://repository.tudelft.nl/file/File_0fc107fa-6796-4bae-9159-8537a431f171) | [paper.md](r2r_opamp__hogervorst_1994/paper.md) · [source.pdf](r2r_opamp__hogervorst_1994/source.pdf) | PDF p.6 (저널 p.1510) Fig. 13 · PDF p.8 Table I |
| cnr_ota | C. Wulff, cnr_ota_sky130nm (xschem 회로도, **PDF 아님**) @8c839f7, 2024 | [GitHub](https://github.com/wulffern/cnr_ota_sky130nm/tree/8c839f7) | [source.md](cnr_ota__wulff_2024/source.md) · [CNR_OTA.sch](cnr_ota__wulff_2024/CNR_OTA.sch) · [CNR_OTA.svg](cnr_ota__wulff_2024/CNR_OTA.svg) | `CNR_OTA.sch` 줄 번호(topology `_src`) · README Signal interface · `sim/load.spi` |
