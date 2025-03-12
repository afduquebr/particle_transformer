import tables
import numpy as np

# Path
path = "/sps/atlas/a/aduque/particle_transformer/PFN/data_train5"

# File paths
file_path = f"{path}/train_25M_prov.h5"
output_file = f"{path}/train_5M_prov.h5"

# Define labels and chunk size
# labels = ['label_QCD', 'label_WZ', 'label_top', 'label_higgs']
labels = ['label_QCD', 'label_W', 'label_Z', 'label_top', 'label_higgs']
chunk_size = 1000000  # Adjust based on available memory

print("Opening source HDF5 file: ", file_path)
file = tables.open_file(file_path, mode="r")

print("Finding indices for each label...")
# Get the indices where each label is 1
idx = [np.where(file.root[label][:] == 1)[0] for label in labels]

# Define number of samples per class
# num_samples = min(id.size for id in idx)
num_samples = 1000000
print(f"Number of samples per class: {num_samples}")

print("Sampling indices from each class...")
# Sample indices from each class without replacement
random_indices = np.concatenate([np.random.choice(id, num_samples, replace=False) for id in idx])

# Shuffle the sampled indices
np.random.shuffle(random_indices)
num_chunks = int(np.ceil(random_indices.size / chunk_size))

print(f"Total number of chunks: {num_chunks}")

print("Opening output HDF5 file: ", output_file)
# Create a new HDF5 file for sampled data
with tables.open_file(output_file, mode="w") as outfile:
    for key in file.root._v_children:  # Loop through datasets
        print(f"Processing dataset: {key}")
        dataset_shape = (random_indices.size,) + file.root[key].shape[1:]
        atom = tables.Atom.from_dtype(file.root[key].dtype)

        # Create the output dataset
        output_array = outfile.create_carray(
            outfile.root, 
            key, 
            atom, 
            dataset_shape,
            chunkshape=(chunk_size,) + file.root[key].shape[1:]
        )
        
        # Process data in chunks
        for chunk_idx in range(num_chunks):
            start = chunk_idx * chunk_size
            stop = min((chunk_idx + 1) * chunk_size, random_indices.size)
            
            print(f"Processing chunk {chunk_idx+1}/{num_chunks} (indices {start}-{stop})")
            
            # Select and sort chunk indices
            chunk_indices = np.sort(random_indices[start:stop])
            
            # Extract the data for the chunk
            chunk_data = file.root[key][:][chunk_indices]
            
            # Save the chunk to the output dataset
            output_array[start:stop] = chunk_data

print(f"Created sampled file with {num_samples} entries per class at {output_file}")
print("Closing source HDF5 file...")
file.close()
print("Process completed successfully!")