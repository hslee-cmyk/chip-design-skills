#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "########## Fig.2 current-reuse telescopic OTA ##########"
python3 analyze.py ../examples/fig2_telescopic.json \
    --inputs Vip,Vim --feedback Vcmfb --outputs Vom1,Vop1
echo
echo "########## Fig.3 class-AB 출력단 (부분 성공 사례) ##########"
echo "# push-pull-output 미검출이 정상이다 — 상류 추출기의 수동소자 미지원 때문."
echo "# Stage 3 coverage 저하가 상류 netlist 오류의 지표로 작동하는 예."
python3 analyze.py ../examples/fig3_classab.json --inputs Vop1 --outputs Vom
