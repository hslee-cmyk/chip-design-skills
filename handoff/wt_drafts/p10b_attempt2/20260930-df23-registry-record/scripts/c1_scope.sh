#!/usr/bin/env bash
# 계약 1(§0~§7 바이트 동일·끝 추가)·계약 6(범위)·커밋 사슬 측정. 병합본 복제본 C:/g88/m2t. 결과 C:/g88/out3/c1_scope.txt
I=C:/g88/m2t; B=0f237862c007f6a53122f2bdfb3c87e6366ec133; M=e67211cd528850d14b585298cb499f8a76767182
REG=docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
O=C:/g88/out3/c1_scope.txt
{
echo "## chain"; git -C $I log --format='%H %P | %(trailers:key=Role,valueonly,separator=) | %(trailers:key=Change-Id,valueonly,separator=)' $B..$M
echo "## M tree vs M^2 tree"; git -C $I rev-parse $M^{tree} $M^2^{tree}
echo "## diff base M name-status"; git -C $I diff --name-status $B $M
echo "## numstat"; git -C $I diff --numstat $B $M
echo "## diff T M name-status"; git -C $I diff --name-status $M^1 $M
echo "## test file blob T vs M"; git -C $I rev-parse $M^1:skills/analog-gmid-design/assets/tests/contracts/test_reg_check_df23.py $M:skills/analog-gmid-design/assets/tests/contracts/test_reg_check_df23.py
echo "## engine/library/inventory/old tests diff"; git -C $I diff --name-only $B $M -- 'skills/analog-gmid-design/assets/*.py' workspaces/run_harness.py docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json skills/analog-gmid-design/assets/tests/contracts/test_reg_check.py 'skills/analog-gmid-design/assets/library' | wc -l
echo "## registry blob prefix"
git -C $I cat-file blob $B:$REG > C:/g88/out3/reg_base_blob.md
git -C $I cat-file blob $M:$REG > C:/g88/out3/reg_m_blob.md
wc -l C:/g88/out3/reg_base_blob.md C:/g88/out3/reg_m_blob.md
n=$(wc -c < C:/g88/out3/reg_base_blob.md); head -c $n C:/g88/out3/reg_m_blob.md | cmp - C:/g88/out3/reg_base_blob.md && echo "base blob is byte prefix of M blob"
echo "CR in M blob: $(tr -cd '\r' < C:/g88/out3/reg_m_blob.md | wc -c)"
echo "worktree eol M: CRLF $(grep -c $'\r$' $I/$REG) / lines $(wc -l < $I/$REG)"
echo "## appended section"; tail -n +$(( $(wc -l < C:/g88/out3/reg_base_blob.md) + 1 )) C:/g88/out3/reg_m_blob.md | head -20
} > $O 2>&1
