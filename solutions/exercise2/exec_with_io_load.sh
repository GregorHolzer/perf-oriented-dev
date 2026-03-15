#!/usr/bin/bash
killall loadgen_io &> /dev/null
gcc loadgen_io.c -o loadgen_io -fopenmp
./loadgen_io 10 10 1000 1000 1234 10 &
$@
killall loadgen_io &> /dev/null
rm loadgen_io