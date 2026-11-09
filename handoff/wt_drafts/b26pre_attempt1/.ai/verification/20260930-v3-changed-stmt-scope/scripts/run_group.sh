#!/usr/bin/env bash
# usage: run_group.sh <group-name> [--cases 0.5 | <case> ...]
# runs base-gate redteam on the isolated clone C:/g244/iso and appends the result line to C:/g244/out/runs.txt
set -uo pipefail
G="$1"; shift
export TMP=C:/g244/tmp/$G TEMP=C:/g244/tmp/$G TMPDIR=C:/g244/tmp/$G PYTHONDONTWRITEBYTECODE=1 APPDATA=C:/Users/HSLEE/AppData/Roaming
mkdir -p "$TMP"
ARGS=()
if [ "${1:-}" = "--cases" ]; then
  ARGS=(--cases 0.5)
else
  ARGS=(--phase 0.5)
  for c in "$@"; do ARGS+=(--only "$c"); done
fi
cd C:/g244/iso || exit 9
start=$(date -Iseconds)
C:/Python314/python.exe -u -B tools/gates/redteam/run_all.py "${ARGS[@]}" --mode direct --repo C:/g244/iso > C:/g244/out/run_$G.txt 2>&1
rc=$?
end=$(date -Iseconds)
log=$(sed -n 's/^log=//p' C:/g244/out/run_$G.txt | head -1)
sha=$(sha256sum "$log" | cut -d' ' -f1)
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$G" "$rc" "$start" "$end" "$log" "$sha" >> C:/g244/out/runs.txt
echo "done $G rc=$rc log=$log sha=$sha"
