#!/usr/bin/env bash
# E-INST(P9, df36 e_inst_df36.py 재사용). 사용: einst.sh <복제본> <태그> <회로> <반복 수>
# 회마다 실행 전·후 복제본 workspaces를 되돌리고 미추적 파일을 지운다. 산출 instance.json 사본을 C:/g47/out/einst/<태그>_<회로>_r<i>.instance.json에.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
R=$1; TAG=$2; CIR=$3; N=$4
O=C:/g47/out/einst; mkdir -p $O
for i in $(seq 1 $N); do
git -C $R checkout -q -- workspaces && git -C $R clean -fdxq
s=$(date +%s.%N)
PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g47/scripts/e_inst_df36.py $R $CIR $O/${TAG}_${CIR}_r$i.json > $O/${TAG}_${CIR}_r$i.log 2>&1
rc=$?
e=$(date +%s.%N)
el=$(C:/Python314/python.exe -c "print(f'{$e-$s:.2f}')")
st=$(git -C $R status --porcelain | tr '\n' ';')
IP=$(C:/Python314/python.exe -c "import json;print(json.load(open('$O/${TAG}_${CIR}_r$i.json',encoding='utf-8')).get('instance_path',''))" 2>/dev/null); [ -f "$IP" ] && cp "$IP" $O/${TAG}_${CIR}_r$i.instance.json
sh=$(C:/Python314/python.exe -c "import json;d=json.load(open('$O/${TAG}_${CIR}_r$i.json',encoding='utf-8'));print(d.get('raw_sha256'), d.get('file_bytes_sha256'), d.get('topology_ref_raw'))" 2>/dev/null)
echo "$TAG $CIR r$i exit=$rc elapsed_s=$el raw/file/topology_ref=$sh status_after=[$st]" | tee -a C:/g47/out/einst.txt
git -C $R checkout -q -- workspaces && git -C $R clean -fdxq
done
