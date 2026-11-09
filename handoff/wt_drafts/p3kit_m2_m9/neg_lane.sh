#!/usr/bin/env bash
# measure only: run neg226.py for the given cards in order, each after its chain head exists
set -u
for c in "$@"; do
  h=""
  while [ -z "$h" ]; do
    h=$(C:/Python314/python.exe -B -c "
import json,sys
for l in open('C:/g226/out/chain.jsonl',encoding='utf-8'):
    r=json.loads(l)
    if r['card']==sys.argv[1]: print(r['head']); break" "$c" | tr -d '\r')
    [ -z "$h" ] && sleep 30
  done
  [ -d /c/g226/ng_$c ] || git -C C:/g226/r worktree add -q --detach C:/g226/ng_$c $h
  C:/Python314/python.exe -B C:/g226/kit/neg226.py $c > C:/g226/out/neg_$c.log 2>&1
  echo "$c neg done" >> C:/g226/out/neg_lanes.txt
done
