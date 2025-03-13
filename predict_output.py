import uproot as up
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, roc_curve, auc

def plot(sample, model, labels):
    # Define input and output paths
    input_path = os.path.join("training", "Pythia", "kin", model, "predict_output", f"pred_sample_{sample}.root")
    output_path = os.path.join("figs", model, sample)

    # Create output directory if not exists
    os.makedirs(output_path, exist_ok=True)

    try:
        # Open ROOT file
        with up.open(input_path) as file:
            if not file.keys():
                raise ValueError(f"Empty ROOT file: {input_path}")

            # Assuming only one tree
            tree_name = file.keys()[0]
            tree = file[tree_name]

            # Load data as a Pandas DataFrame
            data = tree.arrays(library="pd")

    except Exception as e:
        print(f"Error loading file {input_path}: {e}")
        return

    # Handling true labels and predictions
    tags = [f"label_{label}" for label in labels]
    score_tags = [f"score_{tag}" for tag in tags]

    # Convert boolean columns to `bool` type
    data[tags] = data[tags].replace({"True": True, "False": False}).astype(bool)

    # Extract true and predicted labels
    data["true_label"] = data[tags].idxmax(axis=1).str.split("_").str[1]
    data["predict_label"] = data[score_tags].idxmax(axis=1).str.split("_").str[2]

    # 1. Plot Confusion Matrix
    cm = confusion_matrix(data["true_label"], data["predict_label"], labels=labels, normalize='true')
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap='Blues')
    plt.title("Confusion Matrix")
    plt.savefig(f"{output_path}/Confusion_Matrix.pdf")
    plt.clf()

    # 2. Distribution of DNN outputs for all classes
    plt.figure()
    for score_tag in score_tags:
        plt.hist(data[score_tag], bins=30, range=[0, 1], histtype='step', label=score_tag.split("_")[2])
    plt.xlabel("DNN output")
    plt.ylabel("Number of jets")
    plt.yscale('log')
    plt.title("Histograms of QCD, WZ, top, and H")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig(f"{output_path}/output_distribution.pdf")
    plt.clf()

    # 3. ROC Curve (Background rejection for each class)
    linestyles = ['solid', 'dashed', 'dotted', 'dashdot', (5, (10, 3))]
    for label in labels:
        plt.figure()
        for i, label2 in enumerate(labels):
            if label == label2:
                continue

            # Select only events of class `label` and `label2`
            mask = (data["true_label"] == label) | (data["true_label"] == label2)

            # Calculate ROC curve
            fpr, tpr, _ = roc_curve(data["true_label"][mask], data[f"score_label_{label}"][mask], pos_label=label)
            
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                inv_fpr = 1. / fpr
                inv_fpr[np.isinf(inv_fpr)] = 1e6  # Replace infinities for better plotting
            
            plt.plot(tpr, inv_fpr, label=label2, linestyle=linestyles[i])

        plt.xlim(0, 1)
        plt.xlabel('Signal efficiency')
        plt.ylabel('Background rejection (1/FPR)')
        plt.yscale('log')
        plt.legend()
        plt.title(f'ROC curve for {label} vs others')
        plt.savefig(f"{output_path}/{label}_ROC.pdf")
        plt.clf()

    # 4. Discriminant for each class
    for label, score_tag in zip(labels, score_tags):
        plt.figure()
        for label2 in labels:
            disc = data[score_tag][(data["true_label"] == label2)]
            plt.hist(disc, bins=40, range=(0, 1), histtype='step', label=label2)
        plt.xlabel('DNN output')
        plt.ylabel('Number of jets')
        plt.yscale('log')
        plt.title(f'Discriminant for {label}')
        plt.legend()
        plt.savefig(f"{output_path}/{label}_output_dist.pdf")
        plt.clf()

    print(f"Plots saved in {output_path}")

# Define the labels and samples
labels = ['QCD', 'WZ', 'top', 'higgs']
models = ["PN", "ParT"]
sample = "1M"

# Run the plot function for each sample
for model in models:
    plot(sample, model, labels)
