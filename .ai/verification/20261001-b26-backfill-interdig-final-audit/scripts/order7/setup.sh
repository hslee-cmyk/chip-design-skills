set -euo pipefail
# 순서 7 준비: 실제 저장소 상태 기록, 게이트 캐시 추출(base 판)·오케스트레이터 캐시 cmp, 격리 복제본 iso(M)·isob(base)
W=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-audit
R=C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
B=863a037cc0d774bb984006ea39966c5e4dd741ab
M=0bb22782775fd759f9478aeae16e8202095d09a9
C=C:/g394/gmid-gate-cache/$B
OC=$R/.git/gmid-gate-cache/$B
mkdir -p C:/g394/out C:/g394/tmp $C
{
echo "real_repo HEAD $(git -C $R rev-parse HEAD)"
echo "real_repo status_md5 $(git -C $R status --porcelain | md5sum | cut -d' ' -f1)"
echo "real_repo reflog_lines $(git -C $R reflog | wc -l)"
echo "real_repo for_each_ref_md5 $(git -C $R for-each-ref | md5sum | cut -d' ' -f1)"
echo "real_repo gate/master $(git -C $R rev-parse refs/remotes/gate/master)"
echo "audit_wt HEAD $(git -C $W rev-parse HEAD)"
echo "audit_wt M parents $(git -C $W log -1 --format=%P $M)"
echo "audit_wt M trailers: $(git -C $W log -1 --format=%B $M | git interpret-trailers --parse | tr '\n' ';')"
echo "M tree $(git -C $W rev-parse $M^{tree}) K tree $(git -C $W rev-parse 495bb0ea12fa859bea38685851ee46a84e2af039^{tree})"
echo "K trailers: $(git -C $W log -1 --format=%B 495bb0ea12fa859bea38685851ee46a84e2af039 | git interpret-trailers --parse | tr '\n' ';')"
echo "K parent $(git -C $W log -1 --format=%P 495bb0ea12fa859bea38685851ee46a84e2af039)"
echo "first-parent M..HEAD: [$(git -C $W log --oneline --first-parent $M..HEAD)]"
} > C:/g394/out/start_state.txt
for f in $(git -C $W ls-tree --name-only $B tools/gates/ | grep -E '\.(py|ini|json|txt)$'); do
  n=$(basename $f)
  git -C $W cat-file blob $B:$f > $C/$n
  if [ -e $OC/$n ]; then if cmp -s $C/$n $OC/$n; then echo "same $n"; else echo "DIFF $n"; fi; else echo "missing-in-orch $n"; fi
done > C:/g394/out/cache_cmp.txt
for pair in "iso $M" "isob $B"; do
  set -- $pair
  git clone -q --no-hardlinks --no-local -c core.autocrlf=false -c core.longpaths=true --no-checkout $W C:/g394/$1
  git -C C:/g394/$1 remote remove origin
  test -z "$(git -C C:/g394/$1 remote)"
  git -C C:/g394/$1 -c advice.detachedHead=false checkout -q --detach $2
  echo "$1 HEAD $(git -C C:/g394/$1 rev-parse HEAD) remotes=[$(git -C C:/g394/$1 remote)] status=[$(git -C C:/g394/$1 status --porcelain | wc -l)]" >> C:/g394/out/start_state.txt
done
cat C:/g394/out/start_state.txt C:/g394/out/cache_cmp.txt
grep -c targets_by_def $C/mutate_changed.py
