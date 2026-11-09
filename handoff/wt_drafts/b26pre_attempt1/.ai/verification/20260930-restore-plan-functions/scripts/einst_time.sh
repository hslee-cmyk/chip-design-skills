#!/usr/bin/env bash
# E-INST 기준값 + 실행 시간(계약 5 관찰값). 사용: einst_time.sh <복제본> <태그> <회로> <반복 수>
# 회마다 작업 디렉터리를 지우고 같은 경로에서 e_inst.py를 새 프로세스로 돌린다. 벽시계 초(date +%s.%N 차).
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
R=$1; TAG=$2; CIR=$3; N=$4
O=C:/g13/out/einst_$TAG; mkdir -p $O
for i in $(seq 1 $N); do
  rm -rf C:/g13/ws_eq
  s=$(date +%s.%N)
  PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g13/scripts/e_inst.py $R $CIR C:/g13/ws_eq $O/einst_${CIR}_r$i.json > $O/einst_${CIR}_r$i.log 2>&1
  rc=$?
  e=$(date +%s.%N)
  el=$(C:/Python314/python.exe -c "print(f'{$e-$s:.2f}')")
  sh=$(C:/Python314/python.exe -c "import json;print(json.load(open('$O/einst_${CIR}_r$i.json',encoding='utf-8')).get('sha256'))")
  echo "$TAG $CIR r$i exit=$rc elapsed_s=$el sha256=$sh" | tee -a C:/g13/out/einst_time.txt
done
