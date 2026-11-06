#!/bin/bash
#SBATCH --job-name=netzfix-tests
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=03:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# alpha* run + yardsticks T6 and T7 for one calibrated variant (pre-registered in Validation).
# Usage: NETZFIX_SCENARIO=v9.yaml ALPHA=1.069 OUT=results/calibration_v9b_std \
#        sbatch --export=ALL jobs/tests.sh
cd ~/netzfix
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
.venv/bin/python -W ignore scripts/calibrate_margin.py --alpha "$ALPHA" --out "$OUT"
.venv/bin/python -W ignore scripts/t6_yardstick.py --alpha "$ALPHA" --out "$OUT"
.venv/bin/python -W ignore scripts/t7_bottlenecks.py --alpha "$ALPHA" --out "$OUT"
.venv/bin/python scripts/calibration_report.py --dir "$OUT" --test "$ALPHA" > "$OUT/report_stdout.txt"
