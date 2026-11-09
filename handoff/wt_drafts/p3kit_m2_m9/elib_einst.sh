#!/usr/bin/env bash
# scratch: E-LIB / E-INST on the same checkout path for base and head (FU kit shape)
set -u
ISO="$1"; B="$2"; H="$3"; EL="$4"; EI="$5"; O="$6"
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" TMP=/c/g226/tmp TEMP=/c/g226/tmp
PY="C:/Python314/python.exe"
for pair in "base:$B" "head:$H"; do
  L="${pair%%:*}"; C="${pair#*:}"
  git -C "$ISO" checkout -q --detach "$C" || exit 9
  git -C "$ISO" clean -qfdx || exit 9
  PYTHONPYCACHEPREFIX="$(mktemp -d)" $PY -B -P "$EL" "$ISO" "$O/$L.elib.json" >> "$O/elib_einst.txt" 2>&1
  echo "$L elib exit=$? commit=$C" >> "$O/elib_einst.txt"
  for c in current_reuse_telescopic_ota folded_cascode; do
    s=$(date +%s)
    PYTHONPYCACHEPREFIX="$(mktemp -d)" $PY -B -P "$EI" "$ISO" "$c" "$O/$L.$c.einst.json" >> "$O/elib_einst.txt" 2>&1
    echo "$L einst $c exit=$? seconds=$(( $(date +%s) - s ))" >> "$O/elib_einst.txt"
  done
  git -C "$ISO" clean -qfdx
done
