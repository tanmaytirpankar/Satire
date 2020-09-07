#!/bin/bash
#SBATCH --time=72:00:00
#SBATCH --partition=soc-kp
#SBATCH --account=soc-kp
#SBATCH -N 1 
#SBATCH -J satern-serial-sim
#SBATCH -o satern-serial-sim.log
#SBATCH -e err-satern-serial-sim.log
#set CC=/uufs/chpc.utah.edu/sys/installdir/gcc/5.4.0/bin/gcc
#set CXX=/uufs/chpc.utah.edu/sys/installdir/dcc/5.4.0/bin/g++

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
set -x

for i in {0..4}
do
    python3 ../src/satern.py --file ${FILES[i]} --logfile ${OUTPUTFILES[i]}_10.log --std  --outfile ${OUTPUTFILES[i]}_10.out --compress
    python3 ../src/satern.py --file ${FILES[i]} --logfile ${OUTPUTFILES[i]}_20.log --std  --outfile ${OUTPUTFILES[i]}_20.out --compress
    python3 ../src/satern.py --file ${FILES[i]} --logfile ${OUTPUTFILES[i]}_30.log --std  --outfile ${OUTPUTFILES[i]}_30.out --compress
done
cd ..
