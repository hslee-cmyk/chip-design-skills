# gm/ID 방법론 원본 (사용자 지정 2026-11-06)

사용자 지시: "gmid방법론 원본이야. 이걸 이 repository에 따로 보관해두고 필요할 때 항상 참고해".
gm/ID 방법론에 관한 판단(LUT 생성·열 정의·V* 정의·설계 절차 등)은 이 원본을 먼저 확인하고 쪽 번호와 로컬 경로를 붙여 인용한다.

원본 파일(PDF·zip)은 출판 서적이라 git 에 넣지 않는다(`.gitignore`). 이 폴더에 파일이 없으면 아래 '원래 경로'에서 다시 복사하고 sha256 으로 확인한다.

| 자리 | 서적 | sha256 | 원래 경로 |
|---|---|---|---|
| `jespers_2010/gmid_methodology_jespers_2010.pdf` | P. G. A. Jespers, *The gm/ID Methodology, a sizing tool for low-voltage analog CMOS Circuits*, Springer 2010 | `8f2de521240091b77bbcd3d365fa033765eee812f6c4b76746a3780819c9e21b` | `G:\내 드라이브\work\Todoc\기술문서\Gm_over_Id\(E-book) The gm_ID Methodology, a sizing tool for low-voltage analog CMOS Circuits.pdf` |
| `jespers_murmann_2017/systematic_design_jespers_murmann_2017.zip` | P. G. A. Jespers, B. Murmann, *Systematic Design of Analog CMOS Circuits Using Pre-Computed Lookup Tables*, Cambridge 2017 | `94784b7e2e3b0022eef1545b8f1c006ec4265a66376cdc79ab4a71f37bcd32a2` | `G:\내 드라이브\work\Todoc\기술문서\Gm_over_Id\(E-book) systematic design of analog CMOS circuits\systematic design of analog CMOS circuits.zip` |

`jespers_murmann_2017/extracted/` = zip 을 푼 장별 PDF:

| 파일 | 내용 |
|---|---|
| `contents.pdf`, `titles.pdf`, `index.pdf`, `symbols and acnonyms.pdf` | 목차·표제·색인·기호 |
| `1 introduction.pdf` | 1장 서론 |
| `2 basic-transistor-modeling.pdf` | 2장 트랜지스터 모델(EKV 등) |
| `3 basic-sizing-using-the-gmid-methodology.pdf` | 3장 gm/ID 기본 사이징 |
| `4 noise-distortion-and-mismatch.pdf` | 4장 잡음·왜곡·mismatch |
| `5 practical-circuit-examples-i.pdf`, `6 practical-circuit-examples-ii.pdf` | 5·6장 회로 예 |
| `lookup-table-generation-and-usage.pdf` | 부록: LUT 생성과 사용(열 정의·생성 방법) |
| `the-ekv-parameter-extraction-algorithm.pdf` | 부록: EKV 파라미터 추출 |
| `layout-dependence.pdf` | 부록: 레이아웃 의존성 |

공개 보조 자료: https://github.com/bmurmann/Book-on-gm-ID-design (techsweep 설정 파일 등).
