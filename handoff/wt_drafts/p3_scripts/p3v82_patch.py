"""v8.1 -> v8.2 본문 교체(design §10 E5 블록·행, D-28, §9.2 UD-0, 2.4 표 E-LIB 행, 머리). 각 '현재' 문자열이 정확히 1번 있어야 한다.
사용: python -B p3v82_patch.py <design.md> <judge.py>   (제자리 수정)"""
import sys
P, J = sys.argv[1], sys.argv[2]
t = open(P, encoding="utf-8", newline="").read()
judge = open(J, encoding="utf-8").read()
assert "\r\n" not in t

def rep(old, new):
    global t
    n = t.count(old)
    assert n == 1, (n, old[:80])
    t = t.replace(old, new, 1)

def rep_span(start, end_incl, new):
    global t
    i = t.index(start); j = t.index(end_incl, i) + len(end_incl)
    assert t.count(start) == 1
    t = t[:i] + new + t[j:]

# 머리
rep("> **[초안 v8.1 -- 저장소 미반영]**", "> **[초안 v8.2 -- 저장소 미반영]**")
rep("> **v8.1(2026-10-01)**: 6차 검토", "> **v8.2(2026-10-01)**: 오케스트레이터 결정(원칙: 같은 상황의 사용자 선택을 따른다 -- 승인 `20260930-phase2-e4-baseline`, 사용자 \"둘다 기본안으로 진행해\") -- "
    "**UD-0 (c) E5 비교 판의 기본안을 선례 모양으로 바꿈**: Phase 2 DoD 대상 커밋 `P2D`와 Phase 3 마지막 병합본을 같은 경로에서 비교하고, 사이 card가 의도적으로 바꾼 필드만 그 card 계약값으로 따로 판정, "
    "나머지는 해시 같음. B0 비교는 대안. 빼는 필드 목록을 card 초안 계약에서 유도하고 실측(E-INST instance.json 키 없음 -- backfill `interdig_ok`는 `pipeline_result`까지만 가고 instance.json·report에 닿지 않는다; "
    "E-LIB `load_topology` `meta[\"rails\"]` 하나), E-LIB용 `e_lib_p3.py`(`e_lib.py` + meta 키 빼기 인자 한 곳)를 design 커밋에 더함(D-28 (e)·§10 E5 블록·행·§9.2 UD-0·승인 질문 UD-0 (c)). "
    "측정 = `a796468`(엔진은 `0f23786`과 같다), 스크래치 `C:/g135`, 스크립트 `_drafts/p3_scripts/p3v82_*`·`e_lib_p3_proposed/`. 사본 `draft_phase3_design_v8.1.md`, 실측 부록 A F1v82~F3v82, "
    "대응표 `phase3_revision_log.md` '초안 v8.1 → v8.2' 절, 정정 요약 부록 J.\n> **v8.1(2026-10-01)**: 6차 검토")

# 2.x 판정식 표 E-LIB 행
rep("E-LIB는 `e_lib.py` 사본 그대로(§10 E5) |",
    "E-LIB는 M card에서 `e_lib.py` 사본 그대로, DoD E5에서 `e_lib_p3.py`(v8.2 -- `e_lib.py`에 meta 키를 빼는 인자 하나를 더한 사본, D-28·§10 E5) |")

# §9.2 UD-0
rep("**D-28 E5 비교 판**(v8.1, 6차 검토 N1 -- 기본안 B0(M1 base), Phase 2 DoD와는 card 판정 기록이 잇는다; 대안 = 선례 `20260930-phase2-e4-baseline` 기본안 모양: Phase 2 DoD 대상 커밋과 비교하고 B34·B26-1·backfill이 의도적으로 바꾼 필드만 계약값으로 따로 판정. 선례와 일치하는 쪽은 대안).",
    "**D-28 E5 비교 판**(v8.2 -- **기본안 = 선례 `20260930-phase2-e4-baseline` 기본안 모양**: Phase 2 DoD 대상 커밋 P2D와 Phase 3 마지막 병합본을 같은 경로에서 비교하고, 사이 card가 의도적으로 바꾼 필드"
    "(E-LIB `load_topology` `meta[\"rails\"]` 하나, E-INST 없음 -- D-28 (e))만 빼서 그 card 계약값으로 따로 판정, 나머지 해시 같음; **대안 = B0(M1 base)와 비교** + Phase 2 DoD 판과는 card 판정 기록 사슬. "
    "v8.1까지는 반대였다 -- 6차 검토 N1이 드러낸 선례 불일치를 선례 쪽으로 풀었다). 새 측정 스크립트 `e_lib_p3.py`도 이 승인이 덮는다(문서 개정 §8).")
rep("기준 예외(D-9·D-17)와 선례와 다른 비교 판(D-28)은 사용자 몫",
    "기준 예외(D-9·D-17)와 판정 기준인 비교 판·빼는 필드 목록(D-28)은 사용자 몫")

# D-28 가운데
rep("동등은 DoD E5 (i)이 B0(F1 전 판)에서 먼저 잰다(다르면 INVALID). E-LIB는 `e_lib.py` 사본 그대로. E5 비교 판 = B0(M1 판정 기록 `base_commit`) -- **v8.1(6차 검토 N1): 이 비교 판은 '기준에 닿는 기본값'(UD-0 (c))이라 승인 질문에 대안과 함께 드러낸다**(아래 (e)).",
    "동등은 DoD E5 (i)이 P2D(F1 전 판)에서 먼저 잰다(다르면 INVALID). **E-LIB(v8.2)**: M card equivalence는 `e_lib.py` 사본 그대로(card base와 병합본이 모두 B26-1 뒤라 뺄 키가 없다), "
    "DoD E5는 같은 design 커밋에 넣는 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_lib_p3.py`(문안 `_drafts/p3_scripts/e_lib_p3_proposed/e_lib_p3.py`) -- `e_lib.py`와 한 곳만 다르다"
    "(인자로 받은 meta 키를 `load` 값 정규화 전에 빼고 그 값을 `circuits.<회로>.masked`에 따로 싣는다; 키를 주지 않으면 `hash`와 나머지 출력이 `e_lib.py`와 같다 -- 동등은 E5 (i)이 P2D에서 먼저 잰다, 실측 부록 A F2v82). "
    "E5 비교 판 = **P2D**(Phase 2 DoD 측정 기록 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md`의 '대상' 커밋) -- **v8.2: UD-0 (c)의 기본안을 선례 모양으로 옮겼다**(아래 (e)), B0 비교는 대안.")

rep_span("(e) **비교 판 B0**:", "그래서 원칙 기본값이 아니라 기준에 닿는 기본값으로 묻는다. §10 E5 행 |",
    "(e) **비교 판 P2D(v8.2, 선례 모양)**: P2D와 Phase 3 마지막 병합본 사이 card가 의도적으로 바꾸는 E-LIB·E-INST 필드를 그 card 초안의 계약에서 유도해, 그 필드만 빼고 계약값으로 따로 판정하고 나머지는 해시 같음을 요구한다"
    "(선례 `20260930-phase2-e4-baseline` 기본안 -- da03c0e와 Phase 2 마지막 병합본을 같은 경로에서 비교하고 `topology_ref`만 DF-36 계약값으로 판정; 사용자 \"둘다 기본안으로 진행해\"). "
    "사이 card 중 면제 묶기(34)·범위 정책(35)·B33·G1·T0·D0a·D0b는 게이트·도구·test·레지스트리라 E-LIB·E-INST 입력이 아니고, Phase 3 card 자신은 동작을 바꾸지 않는 것이 E5의 판정 대상이다. "
    "**의도된 변경 목록**: ① B34(`draft_b34.final.spec.md` 계약 7): analog-grammar가 있으면 E-LIB 9/9·E-INST가 base와 같다 -- 빼는 필드 없음 ② b26pre: test-only, 엔진 무변경 -- 없음 "
    "③ backfill(`draft_b26_backfill_audit.spec.md` 계약 1·2, 'library 회로 적용 여부'): 바뀌는 값은 `run_matching_safety_with_finger_growth` 반환 `relaxed_pairs[i][\"interdig_ok\"]`뿐이고 그 값은 "
    "`optimize_full_circuit_budget`의 `pipeline_result[\"relaxed_pairs\"]`까지만 간다 -- `save_instance_json`(SD 8973)은 고정 키(`schema_version`·`topology_ref`·`sizing`·`netlist`·`floorplan`·`box_shape`·"
    "`audit_row_split`·`coverage`, 선택 `scope_note`)만 쓰고 report는 그 instance.json에서 만든다(`run_harness.py` 505행), E-LIB 함수(`load_topology`·`run_topology_pipeline`)는 이 def에 닿지 않는다. "
    "실측(부록 A F1v82, `a796468`, SPECS 4회로): 파일럿은 `relaxed_pairs` 2쌍(`M4a/M4b` `interdig_ok` True, `M3a/M3b` False)이 `save_instance_json`에 넘어가지만 instance.json·report.html·stdout에서 "
    "`relaxed`·`interdig_ok` 문자열 0(있는 `interdigitation`은 audit 3b 체크 이름), `folded_cascode`는 `relaxed_pairs` 빈 목록, `two_stage_ota`·`nmcnr_amplifier`는 이 def 전에 멈춘다 -- 빼는 필드 없음 "
    "④ B26-1(`draft_b26_1.spec.md` 계약 2·8): `load_topology` `meta`에 새 키 `\"rails\"` -- E-LIB `load` 값에서 그 키만 빼고(`e_lib_p3.py` 인자 `rails`) 계약값 "
    "`RailDeclaration(nets = 그 회로 topology의 supply_nets)`(계약 1)로 따로 판정한다; `meta`의 다른 키·`transistors`, `run_topology_pipeline` 반환(`transistors`·`box_shape`·`audit_row_split`·`floorplan`·`coverage` -- "
    "meta를 담지 않는다), instance.json은 같아야 한다(계약 8). 실측(부록 A F2v82·F3v82, `a796468` + 계약 1·2 모양 시제품): 원래 `e_lib.py` 해시는 9회로 모두 `load`만 달라(V1·V2 같음) raw 비교는 성립하지 않고, "
    "`rails`를 뺀 해시는 base와 같고 계약 판정 PASS, E-INST 두 회로 해시 base와 같음. **결론: E-INST 빼는 키 = 없음, E-LIB 빼는 키 = `meta[\"rails\"]` 하나** -- §10 E5 판정 python의 `EXCL_INST`·`MASK_META` 상수가 "
    "이 목록이다. 사이 card의 계약이 바뀌면(재작성·새 엔진 card) 이 목록과 상수를 고치는 design 개정(승인 대상 diff)이 필요하다 -- 목록은 판정 기준이라 auditor가 늘리지 않는다. "
    "**A2-③ 답과의 관계**: (나)로 네 card가 P2D 앞에 오면 `rails`가 P2D에도 있으므로 판정 python은 P2D `masked.rails`를 '없음 또는 HEAD와 같음'으로 받는다. "
    "**대안(c-2) = B0 비교**: 같은 블록의 `P2D=`에 B0(M1 판정 기록 `base_commit`)를 넣는다 -- B0에 이미 `rails`가 있어 빼는 필드와 계약값 판정은 두 판에서 같은 값을 보고, Phase 2 DoD 판과의 연결은 "
    "B34·b26pre·backfill·B26-1 판정 기록이 잇는다. v8.1까지 기본안이던 이 모양은 선례에서 고르지 않은 대안('card별 판정 기록 사슬로 갈음')과 같다. §10 E5 행 |")

# §10 E5 블록
i = t.index("# ---- E5: 동작 보존(v8 -- 5차 검토 B1·S1, D-28) ----"); j = t.index("# ---- E6: 정의 보존(MOVE-TOTAL) ----")
block = '''# ---- E5: 동작 보존(v8.2 -- UD-0 (c) 기본안 = 선례 모양, D-28) ----
PT3;              echo "E5 PT3 exit=$?"          # 전체(수집 1개 이상, 실패 0)
PT3 --gmid-dod;   echo "E5 PT3-dod exit=$?"      # 전체, DoD 모드(실패 0)
# E-LIB·E-INST: P2D(Phase 2 DoD 측정 기록 docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md의 '대상' 커밋)와 이 병합본(HEAD)을 같은 <iso>에서 차례로 떠 같은 사본으로 잰다
# (design 20 §10 E4 절차 선례, 승인 20260930-phase2-e4-baseline). 사이 card가 의도적으로 바꾼 필드(D-28 (e) 목록 = 아래 판정 python의 EXCL_INST·MASK_META)만 빼고 그 card 계약값으로 따로 판정한다.
# 대안(c-2)을 고르면 P2D 자리에 B0(M1 판정 기록 base_commit)를 넣는다 -- 나머지 명령·판정 python 그대로.
# 스크립트는 판을 바꾸기 전에 <iso> 밖 X로 복사하고(sha256 기록) 두 판에 같은 사본을 쓴다. 출력 O도 <iso> 밖(clean -fdx가 지운다).
P2D=<phase2-dod.md '대상' 커밋>; H=$(git -C "$ISO" rev-parse HEAD); X=<iso 밖 임시 경로>; O=<iso 밖 출력 경로>
git -C "$ISO" show "$H:docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py" > "$X/e_inst_p3.py"
git -C "$ISO" show "$H:docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_lib_p3.py"  > "$X/e_lib_p3.py"
git -C "$ISO" show "$P2D:.ai/verification/20260930-df36-instance-relpath/scripts/e_inst_df36.py"     > "$X/e_inst_df36.py"
git -C "$ISO" show "$P2D:.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py"          > "$X/e_lib.py"
sha256sum "$X"/e_inst_p3.py "$X"/e_lib_p3.py "$X"/e_inst_df36.py "$X"/e_lib.py > "$O/scripts.sha256"
fresh() { git -C "$ISO" checkout -q --detach "$1" && git -C "$ISO" checkout -q -- . && git -C "$ISO" clean -q -fdx; }
for c in current_reuse_telescopic_ota folded_cascode; do                      # E-INST 회로 집합(20 §3)
  fresh "$P2D"; $PY -P "$X/e_inst_df36.py" "$ISO" "$c" "$O/p2d_df36_$c.json"; echo "E5 p2d df36 $c exit=$?"   # 동등 확인용(F1 전 판)
  fresh "$P2D"; $PY -P "$X/e_inst_p3.py"   "$ISO" "$c" "$O/p2d_p3_$c.json";   echo "E5 p2d p3 $c exit=$?"
  fresh "$H";   $PY -P "$X/e_inst_p3.py"   "$ISO" "$c" "$O/h_p3_$c.json";     echo "E5 head p3 $c exit=$?"
done
fresh "$P2D"
$PY -P "$X/e_lib.py"    "$ISO" "$O/p2d_elib.json";              echo "E5 p2d elib exit=$?"          # 동등 확인용
$PY -P "$X/e_lib_p3.py" "$ISO" "$O/p2d_elibp3_nomask.json";     echo "E5 p2d elibp3 nomask exit=$?" # 동등 확인용(빼는 키 없음)
$PY -P "$X/e_lib_p3.py" "$ISO" "$O/p2d_elibp3.json" rails;      echo "E5 p2d elibp3 exit=$?"        # rails = MASK_META(D-28 (e))
fresh "$H"
$PY -P "$X/e_lib_p3.py" "$ISO" "$O/h_elibp3.json" rails;        echo "E5 head elibp3 exit=$?"
$PY - "$O" "$ISO" <<'PYEOF'
''' + judge + '''PYEOF

'''
t = t[:i] + block + t[j:]

# §10 E5 행
rep_span("**v8(5차 검토 S1, D-28)**: §10 E5 블록 출력에", "(측정 명령은 그때 쓴다). ",
    "**v8.2(UD-0 (c) 기본안 = 선례 모양, D-28)**: §10 E5 블록 출력에 `E5 INVALID` 줄이 없고 `E5 E-LIB/E-INST PASS` -- (i) **동등 확인(먼저, P2D = F1 전 판)**: `e_inst_p3.py`와 `e_inst_df36.py`의 출력 JSON이 "
    "`engine_origin` 키 하나만 다르고(p3가 df36 항목을 모두 포함) stdout 사본이 같다(`elapsed=<초>s`만 가림); `e_lib_p3.py`(인자 없음) 출력이 더한 두 키(`masked_meta_keys`·`circuits.*.masked`) 밖에서 "
    "`e_lib.py` 출력과 같다 -- 아니면 INVALID (ii) E-INST(파일럿·`folded_cascode`): HEAD의 `e_inst_p3.py` 출력이 P2D의 같은 스크립트 출력과 최상위 키별 `field_sha256`(빼는 키 `EXCL_INST` = 없음)·`raw_sha256`·"
    "`without_topology_ref_sha256`이 같고, `exists`, `[FAIL]` 없음, 두 판 `topology_ref_equals_expected_contract1`, 경로 문자열 잎 0 (iii) E-LIB: `e_lib_p3.py … rails`(`MASK_META`) 결과 `hash`가 P2D와 HEAD에서 같고 "
    "회로 집합이 같고 HEAD에서 회로마다 `load` 성공 (iv) **빼낸 필드의 계약값(B26-1 계약 1·2·8)**: 회로마다 HEAD `masked.rails` = `{\"__dc__\": \"RailDeclaration\", \"nets\": <그 회로 HEAD topology `supply_nets`의 정렬 집합>}`이고 "
    "P2D `masked.rails`는 `<ABSENT>` 또는 HEAD와 같다 -- 아니면 `E5 E-LIB rails 계약 FAIL <회로>`. **비교 판 = P2D**: 선례 승인 `20260930-phase2-e4-baseline`(design 20 §10 E4 2026-09-30 정정, 사용자 \"둘다 기본안으로 진행해\")의 "
    "기본안 모양 -- 직전 Phase DoD 대상 커밋과 마지막 병합본을 같은 경로에서 비교하고 의도적으로 바뀐 필드만 계약값으로 따로 판정한다. 빼는 필드 목록의 유도·실측은 D-28 (e)·부록 A F1v82~F3v82. "
    "**대안(c-2)을 고르면** 블록의 `P2D=`에 B0(M1 판정 기록 `base_commit`)를 넣는다(그 밖의 명령·판정 python 그대로). "
    "실측(부록 A F3v82 -- `a796468` 판을 P2D 대용, 계약 1·2 모양 B26-1 시제품을 HEAD 대용, 이 행의 판정 python을 design에서 그대로 뽑아 실행): 시제품 = `E5 E-LIB/E-INST PASS`, nets를 틀리게 만든 시제품 = "
    "`E5 E-LIB rails 계약 FAIL` 9줄 + `FAIL`, `rails`와 함께 meta 키를 하나 더 바꾼 시제품 = `E5 E-LIB(rails 뺀 해시) 다름/실패` + `FAIL`, P2D `e_lib.py` 해시를 바꾼 고장 입력 = `E5 INVALID: e_lib_p3(MASK 없음) ≠ e_lib on P2D`. ")

open(P, "w", encoding="utf-8", newline="").write(t)
print("patched", P)
