#!/usr/bin/bash
mkdir -p /tmp/cb761230
cd /tmp/cb761230
killall loadgen &> /dev/null

#LOAD_PROFILE=/scratch/cb761230/perf-oriented-dev/tools/load_generator/workstation/sys_load_profile_workstation_excerpt.txt

#LOAD_GEN=/scratch/cb761230/perf-oriented-dev/tools/build/loadgen

#$LOAD_GEN mc3 $LOAD_PROFILE &> /dev/null &
#$LOAD_GEN mc3 $LOAD_PROFILE &> /dev/null &
#$LOAD_GEN mc3 $LOAD_PROFILE &> /dev/null &
#$LOAD_GEN mc3 $LOAD_PROFILE &> /dev/null &
#$LOAD_GEN mc3 $LOAD_PROFILE &> /dev/null &
#$LOAD_GEN mc3 $LOAD_PROFILE &> /dev/null &

#time -p nice -n 100 $1
export PYTHONUNBUFFERED=1
#nice -n 1000 
python3 /scratch/cb761230/perf-oriented-dev/solutions/exercise2/benchmark.py /scratch/cb761230/perf-oriented-dev/solutions/exercise2/taskA/lcc3/config.yaml
killall loadgen &> /dev/null
