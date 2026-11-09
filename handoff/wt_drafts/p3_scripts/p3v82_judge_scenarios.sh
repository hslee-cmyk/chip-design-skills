#!/bin/bash
# v8.2 실측(판정 아님): §10 E5 판정 python(design에서 PYEOF 블록을 그대로 뽑은 것)을 시제품 출력에 돌려 수용·거부를 본다.
# 사용: bash p3v82_judge_scenarios.sh <design.md> <측정 출력 E(run_elib.sh의 O)> <scratch S> <HEAD 대용 트리(supply_nets를 읽음)> > out.txt
# P2D 대용 = a796468 판(el_base), HEAD 대용 = 계약 1·2 모양 B26-1 시제품(p1) / nets 틀림(p2) / meta 키 하나 더(p3).
set -u
DES=$1; E=$2; S=$3; HT=$4; PY="C:/Python314/python.exe -B"
mkdir -p "$S"
# 판정 python 추출: '# ---- E5:' 다음 첫 `<<'PYEOF'` 줄부터 PYEOF 줄까지
$PY - "$DES" "$S/judge_from_design.py" <<'EOF'
import sys
t = open(sys.argv[1], encoding="utf-8").read()
i = t.index("# ---- E5:"); j = t.index("<<'PYEOF'\n", i) + len("<<'PYEOF'\n"); k = t.index("\nPYEOF\n", j)
open(sys.argv[2], "w", encoding="utf-8", newline="\n").write(t[j:k + 1])
EOF
echo "judge sha256: $(sha256sum < "$S/judge_from_design.py" | cut -c1-16)"
for v in p1 p2 p3; do
  O="$S/sc_$v"; rm -rf "$O"; mkdir -p "$O"
  for c in current_reuse_telescopic_ota folded_cascode; do
    cp "$E/base_df36_$c.json" "$O/p2d_df36_$c.json"; cp "$E/base_df36_$c.json.stdout.txt" "$O/p2d_df36_$c.json.stdout.txt"
    cp "$E/base_p3_$c.json"   "$O/p2d_p3_$c.json";   cp "$E/base_p3_$c.json.stdout.txt"   "$O/p2d_p3_$c.json.stdout.txt"
    cp "$E/p1_p3_$c.json"     "$O/h_p3_$c.json"      # E-INST HEAD 대용은 세 시나리오 모두 p1 실측(rails가 instance.json에 닿지 않음을 같은 실측이 보인다)
  done
  cp "$E/base_elib.json" "$O/p2d_elib.json"; cp "$E/base_elibp3_nomask.json" "$O/p2d_elibp3_nomask.json"
  cp "$E/base_elibp3.json" "$O/p2d_elibp3.json"; cp "$E/${v}_elibp3.json" "$O/h_elibp3.json"
  echo "== scenario $v"; $PY "$S/judge_from_design.py" "$O" "$HT"; echo "rc=$?"
done
# 고장 입력: P2D 쪽 e_lib_p3(MASK 없음)가 e_lib와 다르면 INVALID인가(e_lib 출력의 hash 한 글자 바꿈)
O="$S/sc_bad_equiv"; rm -rf "$O"; cp -r "$S/sc_p1" "$O"
$PY -c "import json,sys; p=sys.argv[1]; d=json.load(open(p,encoding='utf-8')); d['hash']=d['hash'][:-1]+'0'; json.dump(d,open(p,'w',encoding='utf-8'))" "$O/p2d_elib.json"
echo "== scenario bad_equiv"; $PY "$S/judge_from_design.py" "$O" "$HT"; echo "rc=$?"
