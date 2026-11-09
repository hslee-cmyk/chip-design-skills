set -u
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" TMP=C:/g202/tmp TEMP=C:/g202/tmp
ISO=C:/g202/r; O=C:/g202/einst; PY=C:/Python314/python.exe
for pair in "m9:3f61526" "f1:2fd53cc" "f2:3bcab98"; do
  L="${pair%%:*}"; C="${pair#*:}"
  git -C "$ISO" checkout -q -f --detach "$C" || exit 9
  git -C "$ISO" clean -qfdx || exit 9
  PYTHONPYCACHEPREFIX="$(mktemp -d -p C:/g202/tmp)" $PY -B -P C:/g202/tools/e_lib.py "$ISO" "$O/$L.elib.json" >> "$O/log.txt" 2>&1
  echo "$L elib exit=$? commit=$C" >> "$O/log.txt"
  for c in current_reuse_telescopic_ota folded_cascode; do
    s=$(date +%s)
    PYTHONPYCACHEPREFIX="$(mktemp -d -p C:/g202/tmp)" $PY -B -P C:/g202/tools/e_inst_p3.py "$ISO" "$c" "$O/$L.$c.einst.json" >> "$O/log.txt" 2>&1
    echo "$L einst $c exit=$? seconds=$(( $(date +%s) - s ))" >> "$O/log.txt"
  done
  git -C "$ISO" clean -qfdx
done
echo EDONE >> "$O/log.txt"
