export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONPYCACHEPREFIX=C:/g149/pyc
PY="C:/Python314/python.exe -B"; X=C:/g149/work; O=C:/g149/out_e; L=$O/log_elib.txt
t() { s=$(date +%s); "$@" >> $L 2>&1; echo "rc=$? t=$(( $(date +%s)-s ))s :: $*" >> $L; }
t $PY -P $X/e_lib.py C:/g149/el_base $O/base_elib.json
t $PY -P $X/e_lib_p3.py C:/g149/el_base $O/base_elibp3_nomask.json
t $PY -P $X/e_lib_p3.py C:/g149/el_base $O/base_elibp3.json rails
for v in p1 p2 p3 p4 p5; do
  t $PY -P $X/e_lib.py C:/g149/el_$v $O/${v}_elib.json
  t $PY -P $X/e_lib_p3.py C:/g149/el_$v $O/${v}_elibp3.json rails
done
echo DONE >> $L
