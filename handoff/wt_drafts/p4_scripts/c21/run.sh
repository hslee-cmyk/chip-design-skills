# #21 meta/instance 영향 실측 (a796468 엔진 + 시제품 트리 C:/g148/{base,p1,p20,p21,x1,x2,x3})
# 사용: bash run.sh elib|gate|einst
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONHASHSEED=1
PY="C:/Python314/python.exe -B"
D=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts
X=$D/p4_scripts/c21; O=$X/out; ELIB=$D/p3_scripts/e_lib_p3_proposed/e_lib_p3.py
mkdir -p $O; L=$O/log_$1.txt
t() { s=$(date +%s); "$@" >> $L 2>&1; echo "rc=$? t=$(( $(date +%s)-s ))s :: $*" >> $L; }
case "$1" in
elib)
  for v in base p1 p20 p21 x1 x2; do
    t $PY -P $ELIB C:/g148/$v $O/elib_${v}_nomask.json
    t $PY -P $ELIB C:/g148/$v $O/elib_${v}_mask.json rails
  done ;;
gate)
  for v in base p1 p20 p21 x1 x3; do t $PY -P $X/gate_check.py C:/g148/$v $O/gate_$v.json; done ;;
einst)
  for c in folded_cascode current_reuse_telescopic_ota; do
    for v in p1 p21; do t $PY -P $X/e_inst_c21.py C:/g148/$v $c $O/einst_${v}_$c.json; done
  done ;;
esac
echo "DONE $1" >> $L
