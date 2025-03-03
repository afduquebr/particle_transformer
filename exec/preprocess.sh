#!/bin/bash
#SBATCH -o ./output/resample.%j.txt   # Standard output file (%j = Job ID)
#SBATCH -e ./error/resample.%j.txt    # Standard error file (%j = Job ID)
#SBATCH --mem=128G                    # Memory allocation
#SBATCH --time=96:00:00               # Walltime (48 hours)
#SBATCH --ntasks=1                    # Number of tasks (typically 1 for a Python script)
#SBATCH --cpus-per-task=2             # CPUs per task (adjust as needed)
#SBATCH --job-name=resample           # Job name
#SBATCH --partition=htc               # Partition name (check available partitions)
#SBATCH --account=atlas               # Explicitly specify account

# Load Conda environment
module add conda

# Define and activate Conda environment
conda_env="/sps/atlas/a/aduque/conda/weaver"
if ! conda activate "$conda_env"; then
    echo "Error: Failed to activate Conda environment."
    exit 1
fi

# Move to the working directory
cd /pbs/home/a/aduque/private/particle_transformer/ || exit

# Run the Python script
# if ! python num_sample.py; then
# if ! python balance_sample.py; then
# if ! python to_hdf5.py; then
if ! python resample.py; then
    echo "Error: Failed to run Python script."
    exit 1
fi

# Deactivate Conda environment
if ! conda deactivate; then
    echo "Error: Failed to deactivate Conda environment."
    exit 1
fi

echo "Script executed successfully."
exit 0
