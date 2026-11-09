# usage: runpt.sh <outfile> [extra pytest args]
export APPDATA=C:/Users/HSLEE/AppData/Roaming USERPROFILE=C:/Users/HSLEE
out=$1; shift
cd /c/g136 && TMP=/c/g136/tmp TEMP=/c/g136/tmp PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -B -P -m pytest -c /c/g136/gates/tools/gates/pytest_gate.ini --rootdir=/c/g136/repo --confcutdir=/c/g136/repo -q -p no:cacheprovider --gmid-phase=2 --gmid-strict= "$@" > $out 2>&1; echo "rc=$?" >> $out
