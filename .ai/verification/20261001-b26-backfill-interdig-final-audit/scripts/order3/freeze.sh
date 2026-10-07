set -euo pipefail
I=C:/g393/iso
B=863a037cc0d774bb984006ea39966c5e4dd741ab
T=3004096c81b839998518c14c16d3cd2d6ec6c9bf
echo "== log B..T (%H %P)"
git -C $I log --format='%H %P' $B..$T
echo "== first-parent"
git -C $I log --first-parent --format='%H' $B..$T
echo "== trailers"
for c in $(git -C $I rev-list $B..$T); do
  echo "-- $c"
  git -C $I log -1 --format=%B $c | git -C $I interpret-trailers --parse
done
echo "== diff names"
git -C $I diff --name-only $B $T
echo "== merge-base"
git -C $I merge-base --is-ancestor $B $T && echo "B ancestor of T"
echo "== diff numstat"
git -C $I diff --numstat $B $T
