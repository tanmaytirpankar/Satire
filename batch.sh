#!/bin/bash

FILES[0]="../large_benchmarks/FFT_1024/fft_1024pt_sat.txt"
FILES[1]="../large_benchmarks/advect3d/advect3d_20.txt"
FILES[2]="../large_benchmarks/horner/f_horner_50.txt"
FILES[3]="../large_benchmarks/reduction/Reduction_1024.txt"
FILES[4]="../tests/satern-test/dqmom.txt"
OUTPUTFILES[0]="fft_1024pt_sat"
OUTPUTFILES[1]="advect3d_20"
OUTPUTFILES[2]="f_horner_50"
OUTPUTFILES[3]="Reduction_1024"
OUTPUTFILES[4]="dqmom"

cd "without_abstraction_tests"

for i in {0..4}
do
    python3 ../src/satern.py --file ${FILES[i]} --logfile ${OUTPUTFILES[i]}_10.log --std  --outfile ${OUTPUTFILES[i]}_10.out
done
cd ..

