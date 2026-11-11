# 20261110-nfr4-crossenv -- 다른 실행 환경의 결정성 측정 (CPU 커널 차이)

**측정 증거 폴더이며 판정 기록(auditor)이 아니다.** 작성자 = 측정한 Claude 세션, 독립 판정 전. 결과는 `summary.json`.

## 질문
같은 코드·같은 입력을 OpenBLAS 커널만 달리해(기본 Sandybridge 대 `OPENBLAS_CORETYPE=Nehalem`) 돌리면 산출물이 같은가? (EP-9 '다른 실행 환경' 기준)

## 결과 (summary.json)
- 같은 환경 두 번: 필드 8257개 비트 동일 (PASS).
- 커널이 다르면: 탐색이 갈라진다. `common_gate_amplifier` 는 9068 필드가 다르고 front 1점 대 0점. 평가 예산 300·1000·3000 에서 같다(탐색이 스스로 끝남 -- `slsqp_4/8`).
- 층 0 의 시작점부터 상대 1e-12~1e-8 차이가 있고, 이 작은 차이가 이산 값(이득 예산 행 수, 보정 소자 이름)과 front 유무를 바꾼다.
- 7개 회로 중 front 점을 낸 것은 1개. 나머지 6개는 `cross_env` 가 `vacuous` (아무것도 검증하지 못함).
- 순수 Python SQP 프로토타입(엔진 미반영): 두 커널에서 65455 필드 비트 동일. 그러나 ε 풀이 미수렴. 채택하지 않음.

## 결론 -> 개정
설계 40 §2.4.13 (2)·EP-9·계획 NFR-4 를 개정(사용자 승인 2026-11-10): 다른 실행 환경은 산출물 동치가 아니라 **타당성**(`nfr4_compare.cross_env`). 경위 = design 이력 H40-42.

## 파일
- `summary.json` -- 비교 14건 요약, 원본 기록 26개의 sha256·크기.
- `reports/cross_<회로>.json` -- `cross_env` 비교 보고(7개 회로).
- `scripts/` -- 실행 스크립트 `launch*.sh`(`nfr4_run_dump.py` 호출), 순수 SQP 실험 `pure_sqp.py`·`run_dump_sqp.py`·`test_pure_sqp.py`. 경로는 `/usrdata/hoseung.lee/claude.run/scratch/nfr4_work` 기준이다.
- 원본 실행 기록(`*.json`, 최대 수십 MB)은 저장소 밖 `scratch/nfr4_work/` 에 있고 sha256 만 summary 에 둔다.

## 재현 (요지)
`BUDGET=1000 CIRCUIT=<회로> launch.sh <이름> [Nehalem]` 로 두 번 돌리고 `nfr4_compare.py <기준> <비교> same_env|cross_env <보고>`.
환경: 서버 CentOS 7(glibc 2.17), Xeon E5-2687W(AVX2 없음) -- Windows Haswell 커널 대 비교는 못 했다. numpy SIMD 경로·libm 차이는 측정하지 못했다.
