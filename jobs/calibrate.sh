#!/bin/bash
#SBATCH --job-name=netzfix-calib
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --array=0-6%7
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err

# Line-margin calibration grid (pre-registered in vault/project/Validation.md).
# Usage (from ~/netzfix):  sbatch jobs/calibrate.sh            (grid 0.70 ... 1.00)
#                          sbatch --array=0 --export=ALL,ALPHA=0.83 jobs/calibrate.sh   (one alpha)
#                          OUT=results/calibration_v2 sbatch --export=ALL jobs/calibrate.sh
cd ~/netzfix
GRID=(0.70 0.75 0.80 0.85 0.90 0.95 1.00)
A=${ALPHA:-${GRID[$SLURM_ARRAY_TASK_ID]}}
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
.venv/bin/python -W ignore scripts/calibrate_margin.py --alpha "$A" ${OUT:+--out "$OUT"}
