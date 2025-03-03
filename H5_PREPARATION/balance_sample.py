# import tables
# import numpy as np

# # File paths
# file_path = "/sps/atlas/a/aduque/particle_transformer/PFN/data_train/train_20M_prov.h5"
# output_file = "/sps/atlas/a/aduque/particle_transformer/PFN/data_train/train_20M.h5"

# labels = ['label_QCD', 'label_WZ', 'label_top', 'label_higgs']
# chunk_size = 1000  # Define a chunk size suitable for your memory constraints

# # Open the source HDF5 file
# file = tables.open_file(file_path, mode="r")

# # Get the indices where each label is 1
# idx = [np.where(file.root[label][:] == 1)[0] for label in labels]

# # Find the minimum number of samples across all labels
# num_samples = min(id.size for id in idx)
# # num_samples = 5000000
# print(f"Number of samples: {num_samples}")

# # Sample indices from each class
# random_indices = np.concatenate([np.random.choice(id, num_samples, replace=False) for id in idx])

# # Shuffle the combined indices
# np.random.shuffle(random_indices)

# num_chunks = int(np.ceil(random_indices.size / chunk_size))

# # Open the output HDF5 file
# with tables.open_file(output_file, mode="w") as outfile:
#     for key in file.root._v_children:  # Loop through datasets
#         dataset_shape = (random_indices.size,) + file.root[key].shape[1:]
#         atom = tables.Atom.from_dtype(file.root[key].dtype)
        
#         # Create the output dataset
#         output_array = outfile.create_carray(
#             outfile.root, 
#             key, 
#             atom, 
#             dataset_shape,
#             chunkshape=(chunk_size,) + file.root[key].shape[1:]
#         )
        
#         # Process data in randomly split chunks
#         for chunk_idx in range(num_chunks):
#             start = chunk_idx * chunk_size
#             stop = min((chunk_idx + 1) * chunk_size, random_indices.size)
            
#             # Select random chunk indices
#             chunk_indices = np.sort(random_indices[start:stop])
            
#             # Extract the data for the chunk
#             chunk_data = file.root[key][:][chunk_indices]
            
#             # Save the chunk to the output dataset
#             output_array[start:stop] = chunk_data

# print(f"Created sampled file with {num_samples} entries per class at {output_file}")
# file.close()


# Create a new HDF5 file for sampled data
# outfile = h5py.File(output_file, "w")
# for key in file.root._v_children:
#     data = file.root[key][:][random_indices]
#     outfile.create_dataset(key, data=data)

# print(f"Created sampled file with {num_samples} entries per class at {output_file}")

import tables
import numpy as np

# File paths
folder = "/sps/atlas/a/aduque/particle_transformer/PFN/data_train5"

files = [
    "test_higgs",
    "train_higgs",
    "test_top",
    "train_top",
    "test_qcd",
    "train_qcd",
    "test_W",
    "train_W",
    "test_Z",
    "train_Z",
]

output_file = "/sps/atlas/a/aduque/particle_transformer/PFN/data_train/train_20M.h5"

labels = ['label_QCD', 'label_WZ', 'label_top', 'label_higgs']
chunk_size = 1000  # Define a chunk size suitable for your memory constraints

# Open the source HDF5 file
file = tables.open_file(file_path, mode="r")

# Get the indices where each label is 1
idx = [np.where(file.root[label][:] == 1)[0] for label in labels]

# Find the minimum number of samples across all labels
num_samples = min(id.size for id in idx)
# num_samples = 5000000
print(f"Number of samples: {num_samples}")

# Sample indices from each class
random_indices = np.concatenate([np.random.choice(id, num_samples, replace=False) for id in idx])

# Shuffle the combined indices
np.random.shuffle(random_indices)

num_chunks = int(np.ceil(random_indices.size / chunk_size))

# Open the output HDF5 file
with tables.open_file(output_file, mode="w") as outfile:
    for key in file.root._v_children:  # Loop through datasets
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
        
        # Process data in randomly split chunks
        for chunk_idx in range(num_chunks):
            start = chunk_idx * chunk_size
            stop = min((chunk_idx + 1) * chunk_size, random_indices.size)
            
            # Select random chunk indices
            chunk_indices = np.sort(random_indices[start:stop])
            
            # Extract the data for the chunk
            chunk_data = file.root[key][:][chunk_indices]
            
            # Save the chunk to the output dataset
            output_array[start:stop] = chunk_data

print(f"Created sampled file with {num_samples} entries per class at {output_file}")
file.close()