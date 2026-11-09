#!/bin/bash
# v8.3 실측(판정 아님): §10 E5 판정 python(design에서 PYEOF 블록을 그대로 뽑은 것)을 시제품 출력에 돌려 수용·거부를 본다.
# 사용: bash p3v83_judge_scenarios.sh <design v8.3> <design v8.2 사본> <측정 출력 E> <scratch S> <ISO = P2D 대용 git 저장소> <P2D 커밋> <시제품 루트 접두(el_ 앞)> > out.txt
# P2D 대용 = a796468 판(el_base). HEAD 대용 = 계약 1·2 모양 B26-1 시제품 p1 / nets 틀림 p2 / meta 키 하나 더 p3 /
#   RailDeclaration에 계약 밖 필드(polarity) p4(7차 검토 S1) / two_stage_ota library supply_nets에 agnd 추가 p5(7차 검토 m1).
# v8.3 판정 python 인자 = O ISO P2D(supply_nets를 P2D library에서 git show). v8.2 판정 python 인자 = O HEAD트리(supply_nets를 HEAD library에서) -- 대조용.
set -u
DES=$1; DES82=$2; E=$3; S=$4; ISO=$5; P2D=$6; PR=$7; PY="C:/Python314/python.exe -B"
mkdir -p "$S"
ext() {  # 판정 python 추출: '# ---- E5:' 다음 첫 `<<'PYEOF'` 줄부터 PYEOF 줄까지
$PY - "$1" "$2" <<'EOF'
import sys
t = open(sys.argv[1], encoding="utf-8").read()
i = t.index("# ---- E5:"); j = t.index("<<'PYEOF'\n", i) + len("<<'PYEOF'\n"); k = t.index("\nPYEOF\n", j)
open(sys.argv[2], "w", encoding="utf-8", newline="\n").write(t[j:k + 1])
EOF
}
ext "$DES" "$S/judge_v83.py"; ext "$DES82" "$S/judge_v82.py"
echo "judge v8.3 sha256: $(sha256sum < "$S/judge_v83.py" | cut -c1-16)"
echo "judge v8.2 sha256: $(sha256sum < "$S/judge_v82.py" | cut -c1-16)"
for v in p1 p2 p3 p4 p5; do
  O="$S/sc_$v"; rm -rf "$O"; mkdir -p "$O"
  for c in current_reuse_telescopic_ota folded_cascode; do
    cp "$E/base_df36_$c.json" "$O/p2d_df36_$c.json"; cp "$E/base_df36_$c.json.stdout.txt" "$O/p2d_df36_$c.json.stdout.txt"
    cp "$E/base_p3_$c.json"   "$O/p2d_p3_$c.json";   cp "$E/base_p3_$c.json.stdout.txt"   "$O/p2d_p3_$c.json.stdout.txt"
    cp "$E/p1_p3_$c.json"     "$O/h_p3_$c.json"      # E-INST HEAD 대용은 모든 시나리오에서 p1 실측(rails가 instance.json에 닿지 않음 -- F3v82와 같은 모양)
  done
  cp "$E/base_elib.json" "$O/p2d_elib.json"; cp "$E/base_elibp3_nomask.json" "$O/p2d_elibp3_nomask.json"
  cp "$E/base_elibp3.json" "$O/p2d_elibp3.json"; cp "$E/${v}_elibp3.json" "$O/h_elibp3.json"
  echo "== scenario $v [v8.3 judge]"; $PY "$S/judge_v83.py" "$O" "$ISO" "$P2D"; echo "rc=$?"
  echo "== scenario $v [v8.2 judge, 대조]"; $PY "$S/judge_v82.py" "$O" "${PR}$v" | tail -1; echo "rc=$?"
done
# 고장 입력: P2D 쪽 e_lib_p3(MASK 없음)가 e_lib와 다르면 INVALID인가(e_lib 출력의 hash 한 글자 바꿈)
O="$S/sc_bad_equiv"; rm -rf "$O"; cp -r "$S/sc_p1" "$O"
$PY -c "import json,sys; p=sys.argv[1]; d=json.load(open(p,encoding='utf-8')); d['hash']=d['hash'][:-1]+'0'; json.dump(d,open(p,'w',encoding='utf-8'))" "$O/p2d_elib.json"
echo "== scenario bad_equiv [v8.3 judge]"; $PY "$S/judge_v83.py" "$O" "$ISO" "$P2D"; echo "rc=$?"
# 고장 입력: P2D 커밋이 없는 값이면(git show 실패) 계약값을 읽지 못해 FAIL인가(fail-closed)
echo "== scenario bad_p2d [v8.3 judge]"; $PY "$S/judge_v83.py" "$S/sc_p1" "$ISO" "0000000000000000000000000000000000000000" | tail -2; echo "rc=$?"
