#!/usr/bin/bash
# 끝: 실제 저장소 상태 재기록·대조, C:/g412 삭제
set -euo pipefail
A=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b26-rail-accessor-set-audit
R=C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
O=$A/.ai/verification/20260930-b26-rail-accessor-set/out
{
  echo "HEAD $(git -C $R rev-parse HEAD)"
  echo "status_md5 $(git -C $R status --porcelain | md5sum | cut -d' ' -f1)"
  echo "reflog_lines $(git -C $R reflog | wc -l)"
  echo "refs_md5 $(git -C $R for-each-ref | md5sum | cut -d' ' -f1)"
} > $O/repo_state_end.txt
if cmp -s $O/repo_state_start.txt $O/repo_state_end.txt; then echo "repo state same"; else echo "repo state DIFF"; diff $O/repo_state_start.txt $O/repo_state_end.txt || true; fi
git -C $A status --porcelain
git -C $A log --oneline refs/heads/role/test/20260930-b26-rail-accessor-set..HEAD
rm -rf C:/g412
test ! -e C:/g412 && echo "g412 removed"
