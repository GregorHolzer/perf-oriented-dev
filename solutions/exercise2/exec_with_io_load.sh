#!/usr/bin/bash
mkdir -p /tmp/cb761230
cd /tmp/cb761230
killall loadgen_io &> /dev/null

DIR=/scratch/cb761230/perf-oriented-dev/solutions/exercise2
gcc $DIR/loadgen_io.c -o $DIR/loadgen_io -fopenmp
$DIR/loadgen_io 10 10 1000 1000 1234 10 &
export PYTHONUNBUFFERED=1
python3 /scratch/cb761230/perf-oriented-dev/solutions/exercise2/benchmark.py /scratch/cb761230/perf-oriented-dev/solutions/exercise2/taskB/lcc3/config.yaml
killall loadgen_io &> /dev/null
#rm loadgen_io