#!/usr/bin/env bash
#SBATCH -A m4411
#SBATCH -q regular
#SBATCH -C gpu
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -c 128
#SBATCH --gpus-per-task=4
#SBATCH --gpu-bind=none
#SBATCH -t 04:00:00
#SBATCH -J repart_sweep
#SBATCH -o /pscratch/sd/r/rchanani/LegionSolvers/repart_sweep-%j.out
#SBATCH -e /pscratch/sd/r/rchanani/LegionSolvers/repart_sweep-%j.err

set -euo pipefail

cd /pscratch/sd/r/rchanani/LegionSolvers
mkdir -p scratch/profiles/repart_initial_sweep_n100m

module load PrgEnv-gnu
module load gcc-native/14
module load cudatoolkit/12.9
module load cmake/3.30.2
module load craype-x86-milan
module load craype-accel-nvidia80
module load craype-network-ofi

cmake --build scratch/LegionSolversBuild/pm_a100_ofi_cuda_release -j --target Test06CSRSolveCG
./repart_initial_sweep --rps 0,1,2,5,10,25,50,100,500,1000,1500,2000 --out-dir scratch/profiles/repart_initial_sweep_n100m
