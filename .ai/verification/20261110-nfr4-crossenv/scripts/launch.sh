#!/bin/bash
# usage: launch.sh <name> [OPENBLAS_CORETYPE]
W=/usrdata/hoseung.lee/claude.run/scratch/nfr4_work
N=$1; CORE=${2:-}
mkdir -p $W/$N $W/cache_$N
export GMID_PDK_ROOT=/usrdata/hoseung.lee/claude.run/pdk
export GMID_LUT_V2_ROOT=/usrdata/hoseung.lee/claude.run/gmid-lut-data/sky130_lut_v2
export GMID_LUT_TABLE_CACHE_DIR=$W/cache_$N
[ -n "$CORE" ] && export OPENBLAS_CORETYPE=$CORE
S=/usrdata/hoseung.lee/claude.run/chip-design-skills/skills/analog-gmid-design/gmid_engine/tests/integration/nfr4_run_dump.py
export PYTHONPATH=/usrdata/hoseung.lee/claude.run/chip-design-skills/skills/analog-gmid-design/gmid_engine/tests
cd $W
/usrdata/hoseung.lee/envs/oss-eda/bin/python3 -P $S ${CIRCUIT:-common_gate_amplifier} $W/$N.json $W/$N ${BUDGET:+--eval-budget $BUDGET} > $W/$N.log 2>&1
echo "exit=$?" >> $W/$N.log
