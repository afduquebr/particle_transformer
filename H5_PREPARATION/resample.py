
import tables
import numpy as np
import time

# Path
path = "/sps/atlas/a/aduque/particle_transformer/PFN/data_train5"

# Files
input_files = [
    f"{path}/train_files/train_qcd.h5",
    f"{path}/train_files/train_W.h5",
    f"{path}/train_files/train_Z.h5",
    f"{path}/train_files/train_top.h5",
    f"{path}/train_files/train_higgs.h5"
]

output_file = f"{path}/train_25M_prov.h5"

labels = ['label_QCD', 'label_W', 'label_Z', 'label_top', 'label_higgs']
chunk_size = 1000000  # Define a chunk size suitable for your memory constraints

print("Opening input HDF5 files...")
files = [tables.open_file(input_file, mode="r") for input_file in input_files]
print("Files opened successfully!")

# Get the indices where each label is 1
print("Extracting indices for each label...")
idx = [np.where(file.root[label][:] == 1)[0] for file, label in zip(files, labels)]

# Find the minimum number of samples across all labels
num_samples = 5000000
num_total = num_samples * len(labels)
print(f"Selected {num_samples} samples per class, total {num_total} samples.")

# Sample indices from each class
print("Sampling random indices...")
random_indices = np.array([np.random.choice(id, num_samples, replace=False) for id in idx])
print("Random indices sampled.")

num_chunks = int(np.ceil(num_samples / chunk_size))
print(f"Processing in {num_chunks} chunks of size {chunk_size}.")

# Open the output HDF5 file
with tables.open_file(output_file, mode="w") as outfile:
    print(f"Creating output file: {output_file}")

    for key in files[0].root._v_children:  # Loop through datasets
        print(f"Processing dataset: {key}")
        dataset_shape = (num_total,) + files[0].root[key].shape[1:]
        atom = tables.Atom.from_dtype(files[0].root[key].dtype)

        # Create the output dataset
        output_array = outfile.create_carray(
            outfile.root, 
            key, 
            atom, 
            dataset_shape,
            chunkshape=(chunk_size,) + files[0].root[key].shape[1:]
        )
        print(f"Created dataset '{key}' with shape {dataset_shape}")

        # Process data in randomly split chunks
        for chunk_idx in range(num_chunks):
            start_time = time.time()
            start = chunk_idx * chunk_size
            stop = min((chunk_idx + 1) * chunk_size, num_total)

            # Select random chunk indices
            chunk_indices = np.sort(random_indices[:, start:stop])

            # Extract the data for the chunk
            chunk_data = [file.root[key][:][chunk_id] for file, chunk_id in zip(files, chunk_indices)]

            # Save the chunk to the output dataset
            output_array[(start * len(labels)):(stop * len(labels))] = np.concatenate(chunk_data)

            elapsed_time = time.time() - start_time
            print(f"Processed chunk {chunk_idx+1}/{num_chunks} for '{key}' in {elapsed_time:.2f} sec.")

    print(f"Finished processing. Output file saved at: {output_file}")

# Close input files
for file in files:
    file.close()
print("All input files closed. Script completed successfully!")


# Create a new HDF5 file for sampled data
# outfile = h5py.File(output_file, "w")
# for key in file.root._v_children:
#     data = file.root[key][:][random_indices]
#     outfile.create_dataset(key, data=data)

# print(f"Created sampled file with {num_samples} entries per class at {output_file}")
