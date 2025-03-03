#!/bin/bash
#SBATCH -o ./output/train.%j.txt      # Standard output file (%j = Job ID)
#SBATCH -e ./error/train.%j.txt       # Standard error file (%j = Job ID)
#SBATCH --mem=128G                    # Memory allocation
#SBATCH --time=96:00:00               # Walltime (96 hours)
#SBATCH --ntasks=2                    # Number of tasks (typically 1 for a Python script)
#SBATCH --gpus=1                      # CPUs per task (adjust as needed)
#SBATCH --job-name=train              # Job name
#SBATCH --partition=htc               # Partition name (check available partitions)
#SBATCH --account=atlas               # Explicitly specify account

# Load Conda environment
module add conda

# Define the name of the Conda environment
conda_env="/sps/atlas/a/aduque/conda/weaver"

# Activate the Conda environment
if ! conda activate $conda_env; then
    echo "Error: Failed to activate Conda environment."
    exit 1
fi

suffix=${COMMENT}
DATADIR_JetClass="/sps/atlas/a/aduque/particle_transformer/PFN/data_train"

export DATADIR=${DATADIR_JetClass}
NGPUS=1
if ((NGPUS > 1)); then
    CMD="torchrun --standalone --nnodes=1 --nproc_per_node=$NGPUS $(which weaver) --backend nccl"
else
    CMD="weaver"
fi

# Go to directory
cd /pbs/home/a/aduque/private/particle_transformer/ || exit

epochs=50
dataopts="--num-workers 2 --fetch-step 0.01"

# PN, PFN, PCNN, ParT
model="PFN"
if [[ "$model" == "ParT" ]]; then
    modelopts="networks/example_ParticleTransformer.py --use-amp"
    batchopts="--batch-size 512 --start-lr 1e-3"
elif [[ "$model" == "PELICAN" ]]; then
    modelopts="networks/example_Pelican.py"
    batchopts="--batch-size 128 --start-lr 1e-3"
elif [[ "$model" == "PN" ]]; then
    modelopts="networks/example_ParticleNet.py"
    batchopts="--batch-size 512 --start-lr 1e-2"
elif [[ "$model" == "PFN" ]]; then
    modelopts="networks/example_PFN.py"
    batchopts="--batch-size 4096 --start-lr 2e-2"
elif [[ "$model" == "PCNN" ]]; then
    modelopts="networks/example_PCNN.py"
    batchopts="--batch-size 4096 --start-lr 2e-2"
else
    echo "Invalid model $model!"
    exit 1
fi

# "kin", "kinpid", "full"
FEATURE_TYPE="kin"
[[ -z ${FEATURE_TYPE} ]] && FEATURE_TYPE="full"

if ! [[ "${FEATURE_TYPE}" =~ ^(full|kin|kinpid)$ ]]; then
    echo "Invalid feature type ${FEATURE_TYPE}!"
    exit 1
fi

# currently only Pythia
SAMPLE_TYPE=Pythia

$CMD --data-train ${DATADIR}/train_20M.h5 \
    --data-test ${DATADIR}/test_1M.h5 \
    --data-fraction 0.1 --train-val-split 0.9\
    --data-config data/JetClass/JetClass_${FEATURE_TYPE}.yaml --network-config $modelopts \
    --model-prefix training/${SAMPLE_TYPE}/${FEATURE_TYPE}/${model}/sample_20M \
    $dataopts $batchopts \
    --num-epochs $epochs --gpus 0 \
    --optimizer ranger --log logs/JetClass_${SAMPLE_TYPE}_${FEATURE_TYPE}_${model}_{auto}${suffix}.log --predict-output pred_sample_20M.root \
    --tensorboard JetClass_${SAMPLE_TYPE}_${FEATURE_TYPE}_${model}${suffix} \
    "${@:3}"

# $CMD --predict --data-test ${DATADIR}/test_1M.h5 \
#     --data-fraction 0.1 --train-val-split 0.9\
#     --data-config data/JetClass/JetClass_${FEATURE_TYPE}.yaml --network-config $modelopts \
#     --model-prefix training/${SAMPLE_TYPE}/${FEATURE_TYPE}/${model}/sample_10M \
#     $dataopts $batchopts \
#     --num-epochs $epochs --gpus 0 \
#     --optimizer ranger --log logs/JetClass_${SAMPLE_TYPE}_${FEATURE_TYPE}_${model}_{auto}${suffix}.log --predict-output pred_sample_10M.root \
#     --tensorboard JetClass_${SAMPLE_TYPE}_${FEATURE_TYPE}_${model}${suffix} \
#     "${@:3}"


    #--no-load_observers_during_training --no-data_config_print \
    #training/JetClass/Pythia/kin/ParT/20231027-135801_example_ParticleTransformer_ranger_lr0.001_batch512v1/net \
    #--load-epoch 4 \
    #--model-prefix training/JetClass/${SAMPLE_TYPE}/${FEATURE_TYPE}/${model}/{auto}${suffix}/net \
    #--model-prefix training/JetClass/Pythia/kin/PELICAN/20240202-121826_example_Pelican_ranger_lr0.01_batch128v1/net \

# Deactivate the Conda environment
if ! conda deactivate; then
    echo "Error: Failed to deactivate Conda environment."
    exit 1
fi

echo "Script executed successfully."
exit 0