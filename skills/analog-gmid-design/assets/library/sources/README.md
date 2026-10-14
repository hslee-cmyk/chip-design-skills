# library topology 원문

library 회로(`assets/library/<회로>.*`)의 topology·spec 근거가 된 원문을 그대로 보관한다. spec 출처(`source`·`record`)와 topology 판독은 이 폴더의 경로와 쪽·그림 번호를 인용한다.

## 규칙
- 원문 하나 = 폴더 하나: `<엔진 회로 이름>__<제1저자>_<연도>/`
  - `source.pdf`: 원본 사본 (`paper.md` 머리에 원래 위치와 sha256)
  - `paper.md`: 쪽 단위 텍스트 + 쪽 렌더 이미지 링크. 수식·표·그림은 텍스트가 깨질 수 있으니 `pages/pNN.png`로 확인한다.
  - `pages/`(150 dpi 쪽 렌더), `images/`(내장 이미지)
- 변환: `python tools/pdf_to_md.py <pdf> assets/library/sources/<폴더> "<제목>" "<웹 출처>"` (skill 폴더에서, PyMuPDF)
- 새 원문을 넣으면 아래 표에 한 줄 추가한다. 웹 링크를 못 찾았으면 '찾지 못함'으로 적는다.

## 목록

| 엔진 회로 | 원문 | 웹 | 파일 | 핵심 위치 |
|---|---|---|---|---|
| current_reuse_telescopic_ota | Xie, Chen, "A 126µW Current-Reuse Telescopic OTA with Class-AB Output Stage" (UT Austin, 2019) | 찾지 못함 | [paper.md](current_reuse_telescopic_ota__xie_chen_2019/paper.md) · [source.pdf](current_reuse_telescopic_ota__xie_chen_2019/source.pdf) | Table I p.1, Fig.1·2 p.2, Fig.3~5 p.3, Fig.6~9(치수·DC) p.6~9 |
