#!/bin/bash
#PBS -o ./output/skim.$PBS_JOBID.txt
#PBS -e ./error/skim.$PBS_JOBID.txt

# Source Conda environment
source /atlas/tools/anaconda/anaconda3/etc/profile.d/conda.sh

# Define the name of the Conda environment
conda_env="/AtlasDisk/user/duquebran/conda/weaver"

# Activate the Conda environment
if ! conda activate $conda_env; then
    echo "Error: Failed to activate Conda environment."
    exit 1
fi

# Go to directory
cd /AtlasDisk/home2/duquebran/particle_transformer/ROOT_PREPARATION/ || exit

# Run Training Python script
# if ! python run_skim_5.py; then
if ! python run_skim_multiclass.py; then
    echo "Error: Failed to run Python script."
    exit 1
fi

# Deactivate the Conda environment
if ! conda deactivate; then
    echo "Error: Failed to deactivate Conda environment."
    exit 1
fi

echo "Script executed successfully."
exit 0