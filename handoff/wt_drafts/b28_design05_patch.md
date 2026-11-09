# B28 문서 커밋: design 05 §10 V3 행(317행) 교체

old: `④ 변이마다 임시 복사본에서 그 test만`
new: `④ 변이마다 \`--head\` 커밋의 격리 복제본(\`git clone --no-hardlinks --no-local\`, 이력 포함, origin 없음 -- §12-7과 같은 형태, 끝나면 지운다)에서 그 test만. 인벤토리의 변이 없는 기준 실행이 실패하면 그 변이를 생존으로 세지 않고 \`ERROR\`(exit 2, 실패 인벤토리 출력)`

커밋 순서(DF-36 push 뒤): spec card `docs/02-design/specs/20260930-v3-history-clone.spec.md` + design 05 317행 → 커밋 `Role: doc` → 사용자 승인 → 승인 기록
`.ai/approvals/20260930-v3-history-clone.md`(target_kind diff, diff_base = gate master, diff_head = 문서 커밋, diff_path 두 줄, target = weakening_diff.diff_hash) → push gate.
