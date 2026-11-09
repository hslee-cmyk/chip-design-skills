export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONPYCACHEPREFIX=C:/g149/pyc
PY="C:/Python314/python.exe -B"; X=C:/g149/work; O=C:/g149/out_e; c=$1; L=$O/log_einst_$c.txt
t() { s=$(date +%s); "$@" >> $L 2>&1; echo "rc=$? t=$(( $(date +%s)-s ))s :: $*" >> $L; }
t $PY -P $X/e_inst_df36.py C:/g149/el_base $c $O/base_df36_$c.json
t $PY -P $X/e_inst_p3.py C:/g149/el_base $c $O/base_p3_$c.json
t $PY -P $X/e_inst_p3.py C:/g149/el_p1 $c $O/p1_p3_$c.json
echo DONE >> $L
