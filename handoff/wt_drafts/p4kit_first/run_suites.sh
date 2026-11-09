#!/usr/bin/bash
# 전체 suite를 base(wB)와 모의 병합본(wM)에서 차례로 돌린다(측정 전용). 결과는 /c/g204/out_suite_*.txt
export TMP=/c/g204/tmp TEMP=/c/g204/tmp PYTHONIOENCODING=utf-8 APPDATA='C:\Users\HSLEE\AppData\Roaming'
cp /c/g204/base/tools/gates/pytest_gate.ini /c/g204/tmp/pytest_gate.ini
for w in wB wM; do
  cd /c/g204/$w || exit 2
  /c/Python314/python.exe -B -m pytest -q -p no:cacheprovider -c /c/g204/tmp/pytest_gate.ini --rootdir=/c/g204/$w --confcutdir=/c/g204/$w --gmid-phase=2 -rfE > /c/g204/out_suite_$w.txt 2>&1
  echo "exit=$?" >> /c/g204/out_suite_$w.txt
done
