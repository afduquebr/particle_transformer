import tables as tb
import numpy as np
import matplotlib.pyplot as plt

path = "/sps/atlas/a/aduque/particle_transformer/PFN/data_train/test_1M.h5"

labels = ['label_QCD', 'label_WZ', 'label_top', 'label_higgs']

# Open the source HDF5 file
file = tb.open_file(path, mode="r")

# Get the indices where each label is 1
idx = [np.where(file.root[label][:] == 1)[0] for label in labels]

# Find the minimum number of samples across all labels
num_samples = [id.size for id in idx]

bins = np.linspace(0, 1000000, 1000)

plt.figure(figsize=(15, 8))
for i, label in enumerate(labels):
    plt.hist(idx[i], bins=bins, alpha=0.5, label=label, histtype='stepfilled')

plt.xlabel('Index values')
plt.ylabel('Frequency')
plt.title('Index Distribution of 4 Classes')
plt.legend()
plt.grid(True)

# Save the figure as a PNG file
plt.savefig('class_index_distribution.png', dpi=300)  # dpi=300 for high resolution