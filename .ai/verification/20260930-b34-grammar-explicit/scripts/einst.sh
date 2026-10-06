#!/usr/bin/env bash
# E-INST(DF-36). 사용: einst.sh <복제본> <태그> <회로>
# 실행 전·후에 복제본 workspaces 추적 파일을 되돌리고 미추적 파일을 지운다(산출은 복제본 workspaces/<report_dir>에 쓰인다).
# 산출 instance.json 사본을 C:/g299/out/einst/<태그>_<회로>.instance.json에 남긴다.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
R=$1; TAG=$2; CIR=$3
O=C:/g299/out/einst; mkdir -p $O
git -C $R checkout -q -- workspaces && git -C $R clean -fdxq
s=$(date +%s.%N)
PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g299/scripts/e_inst_df36.py $R $CIR $O/${TAG}_${CIR}.json > $O/${TAG}_${CIR}.log 2>&1
rc=$?
e=$(date +%s.%N)
el=$(C:/Python314/python.exe -c "print(f'{$e-$s:.2f}')")
st=$(git -C $R status --porcelain | tr '\n' ';')
IP=$(C:/Python314/python.exe -c "import json;print(json.load(open('$O/${TAG}_${CIR}.json',encoding='utf-8')).get('instance_path',''))" 2>/dev/null); [ -f "$IP" ] && cp "$IP" $O/${TAG}_${CIR}.instance.json
echo "$TAG $CIR exit=$rc elapsed_s=$el status_after=[$st]" | tee -a C:/g299/out/einst.txt
git -C $R checkout -q -- workspaces && git -C $R clean -fdxq
