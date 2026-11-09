export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
PY="C:/Python314/python.exe -B"; X=C:/g135/x; O=C:/g135/out_e; mkdir -p $O; L=$O/log.txt
t() { s=$(date +%s); "$@" >> $L 2>&1; echo "rc=$? t=$(( $(date +%s)-s ))s :: $*" >> $L; }
t $PY -P $X/e_lib.py C:/g135/el_base $O/base_elib.json
t $PY -P $X/e_lib_p3.py C:/g135/el_base $O/base_elibp3_nomask.json
t $PY -P $X/e_lib_p3.py C:/g135/el_base $O/base_elibp3.json rails
for v in p1 p2 p3; do
  t $PY -P $X/e_lib.py C:/g135/el_$v $O/${v}_elib.json
  t $PY -P $X/e_lib_p3.py C:/g135/el_$v $O/${v}_elibp3.json rails
done
for c in folded_cascode current_reuse_telescopic_ota; do
  t $PY -P $X/e_inst_df36.py C:/g135/el_base $c $O/base_df36_$c.json
  t $PY -P $X/e_inst_p3.py C:/g135/el_base $c $O/base_p3_$c.json
  t $PY -P $X/e_inst_p3.py C:/g135/el_p1 $c $O/p1_p3_$c.json
done
echo DONE >> $L
