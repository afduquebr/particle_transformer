import numpy as np
import uproot as up
import tables

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

# Define a helper function to get the proper atom type
def get_atom(array):
    """Returns the appropriate PyTables atom type based on the dtype of the array."""
    dtype = array.dtype
    if np.issubdtype(dtype, np.floating):
        return tables.Float64Atom() if dtype == np.float64 else tables.Float32Atom()
    elif np.issubdtype(dtype, np.integer):
        return tables.Int64Atom() if dtype == np.int64 else tables.Int32Atom()
    elif np.issubdtype(dtype, np.bool_):
        return tables.BoolAtom()
    else:
        raise TypeError(f"Unsupported dtype: {dtype}")

for file in files:
    # Load the ROOT file and tree
    root_filename = f"{folder}/{file}.root"
    tree_name = "tree"  # Replace with your actual tree name
    output_hdf5_filename = f"{folder}/{file}.h5"

    print(f"Converting '{root_filename}'")

    # Open the ROOT file and access the tree
    with up.open(root_filename) as file:
        tree = file[tree_name]
        
        # Save to HDF5 format using PyTables
        with tables.open_file(output_hdf5_filename, mode="w") as hdf5_file:
            group = hdf5_file.root  # Root group in the PyTables file
            i = 0
            for data in tree.iterate(library="np", step_size="100MB"):
                i += 1
                print(f"Step quantity: {i}")
                for branch_name, array in data.items():
                    # Handle fixed-size arrays and scalars differently
                    if branch_name not in hdf5_file.root:
                        atom = get_atom(array)
                        if isinstance(array[0], np.ndarray):
                            # Create an EArray for fixed-size arrays
                            shape = (0,) + array.shape[1:]
                            # filters = tables.Filters(complevel=5, complib="zlib")  # GZIP compression
                            dataset = hdf5_file.create_earray(group, branch_name, atom, shape) #, filters=filters)
                            dataset.append(array)
                        else:
                            # Create an EArray for scalar values
                            shape = (0,)
                            # filters = tables.Filters(complevel=5, complib="zlib")
                            dataset = hdf5_file.create_earray(group, branch_name, atom, shape) #, filters=filters)
                            dataset.append(array)
                    else:
                        # Append data to existing datasets
                        dataset = getattr(hdf5_file.root, branch_name)
                        dataset.append(array)

    print(f"ROOT file '{root_filename}' successfully converted to HDF5 '{output_hdf5_filename}'")

print("All ROOT files converted successfully.")

