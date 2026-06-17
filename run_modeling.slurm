#!/bin/bash
#SBATCH --job-name=nepal_landslide_github_try
#SBATCH --account=sloos0
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=36
#SBATCH --mem=128G
#SBATCH --time=24:00:00
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

set -euo pipefail

PROJECT_DIR="/home/majorz/Nepal_Landslide/Full_Run_Git"
VENV_DIR="${PROJECT_DIR}/.venv"

cd "${PROJECT_DIR}"

module purge
module load python/3.11

# Create venv on first run, reuse on later runs.
if [ ! -d "${VENV_DIR}" ]; then
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python run_modeling.py
