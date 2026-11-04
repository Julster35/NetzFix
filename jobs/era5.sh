#!/bin/bash
#SBATCH --job-name=netzfix-era5
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=23:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# ERA5 cutout download (input data, not a result). Mostly waiting in the Copernicus queue.
# atlite resumes missing features, so after a timeout just resubmit: sbatch jobs/era5.sh
# Needs ~/.cdsapirc (never in the repo) and data/raw/gisco/NUTS3_2024.geojson +
# data/processed/mastr_units_*.parquet for the cutout box.
cd ~/netzfix
mkdir -p data/raw/era5/tmp
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
.venv/bin/python -u -W ignore -m netzfix.data.era5 --tmpdir data/raw/era5/tmp
