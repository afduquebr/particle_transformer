# import h5py
# import awkward as ak
# import numpy as np
# import glob
# import os
# import hep_ml.reweight as reweight

# def match_weights(pt, target, n_bins=200):
#     """ match_weights - This function will use the hepml reweight function
#     to calculate weights which match the pt distribution to the target
#     distribution. Usually used to match the bkg pt distribution to the
#     signal.

#     Arguments:
#     pt (array) - Distribution to calculate weights for
#     target (array) - Distribution to match
#     n_bins (int)

#     Returns:
#     (array) - vector of weights for pt
#     """

#     # Fit reweighter to target distribution
#     reweighter = reweight.BinsReweighter(n_bins=n_bins)
#     reweighter.fit(pt, target=target)

#     # Predict new weights
#     weights = reweighter.predict_weights(pt)
#     weights /= weights.mean()

#     return weights

# def shuffle_and_merge(file_dir, sig_tag, bkg_tag, filename):
#     out_dir = "/AtlasDisk/user/duquebran/particle_transformer/PFN/data_train"
#     sig_files = glob.glob(file_dir + sig_tag + "*.h5")
#     bkg_files = []
    
#     for sig_file in sig_files:
#         bkg_file = sig_file.replace(sig_tag, bkg_tag)
#         if not os.path.exists(bkg_file):
#             raise Exception("Matching background file not found for:", sig_file)
#         bkg_files.append(bkg_file)
    
#     test_data, train_data = {}, {}
#     for sig_file, bkg_file in zip(sig_files, bkg_files):
#         print(f"Combining {sig_file} and {bkg_file}...", end="", flush=True)
        
#         with h5py.File(sig_file, "r") as sf, h5py.File(bkg_file, "r") as bf:
#             sig_data = {k: sf[k][:] for k in sf.keys()}
#             bkg_data = {k: bf[k][:] for k in bf.keys()}
        
#         combined_data = {key: np.concatenate([sig_data[key], bkg_data[key]]) for key in sig_data.keys()}
#         indices = np.arange(len(combined_data["jet_pt"]))
#         np.random.default_rng(0).shuffle(indices)
        
#         if "test" in sig_file:
#             for key, values in combined_data.items():
#                 test_data.setdefault(key, []).extend(values[indices])
#         else:
#             for key, values in combined_data.items():
#                 train_data.setdefault(key, []).extend(values[indices])
        
#         print("Completed!")

#     # Save merged data
#     with h5py.File(f"{out_dir}/test_{filename}.part.h5", "w") as test_file, h5py.File(f"{out_dir}/train_{filename}.part.h5", "w") as train_file:
#         for key in test_data:
#             test_file.create_dataset(key, data=np.array(test_data[key]))
#         for key in train_data:
#             train_file.create_dataset(key, data=np.array(train_data[key]))

# def open_sig_and_bkg(file_dir, sig_tag, bkg_tag, filename="", labelname="label_sig"):
#     out_dir = "/AtlasDisk/user/duquebran/particle_transformer/PFN/data_train"
#     shuffle_and_merge(file_dir, sig_tag, bkg_tag, filename)
    
#     print("TEMPORARY FILES CREATED. REWEIGHTING TRAIN FILE.")
    
#     with h5py.File(f"{out_dir}/train_{filename}.h5", "r+") as train_file:
#         pt = train_file["jet_pt"][:]
#         labels = train_file[labelname][:]
#         bkg_weight = match_weights(pt[labels == 0], pt[labels == 1])
        
#         weights = train_file["weight"][:]
#         bkg_indices = np.where(labels == 0)[0]
#         weights[bkg_indices] = bkg_weight[:len(bkg_indices)]
#         train_file["weight"][:] = weights
    
#     os.rename(f"{out_dir}/train_{filename}.part.h5", f"{out_dir}/train_{filename}.h5")
#     os.rename(f"{out_dir}/test_{filename}.part.h5", f"{out_dir}/test_{filename}.h5")
    
#     print("COMPLETED!")

# input_dir = "/AtlasDisk/user/duquebran/particle_transformer/PFN/data_out/"
# open_sig_and_bkg(input_dir, "H", "qcd", filename="qcd", labelname="label_QCD")
# open_sig_and_bkg(input_dir, "H", "top", filename="top", labelname="label_top")
# open_sig_and_bkg(input_dir, "H", "WZ", filename="WZ", labelname="label_WZ")

##################################################################################################

import tables
import awkward as ak
import numpy as np
import glob
import os
import hep_ml.reweight as reweight

def match_weights(pt, target, n_bins=200):
    """ match_weights - This function will use the hepml reweight function
    to calculate weights which match the pt distribution to the target
    distribution. Usually used to match the bkg pt distribution to the
    signal.

    Arguments:
    pt (array) - Distribution to calculate weights for
    target (array) - Distribution to match
    n_bins (int)

    Returns:
    (array) - vector of weights for pt
    """
    reweighter = reweight.BinsReweighter(n_bins=n_bins)
    reweighter.fit(pt, target=target)

    weights = reweighter.predict_weights(pt)
    weights /= weights.mean()

    return weights

def read_data_pytables(file_path):
    """Read data from a PyTables file."""
    with tables.open_file(file_path, mode="r") as file:
        data = {node.name: node[:] for node in file.root}
    return data

def write_data_pytables(file_path, data_dict):
    """Write data to a PyTables file."""
    with tables.open_file(file_path, mode="w") as file:
        for key, values in data_dict.items():
            atom = tables.Atom.from_dtype(values.dtype)
            array_shape = values.shape
            file.create_array(file.root, key, values, title=key)

def shuffle_and_merge(file_dir, sig_tag, bkg_tag, filename):
    out_dir = "/AtlasDisk/user/duquebran/particle_transformer/PFN/data_train"
    sig_files = glob.glob(file_dir + sig_tag + "*.h5")
    bkg_files = []
    
    for sig_file in sig_files:
        bkg_file = sig_file.replace(sig_tag, bkg_tag)
        if not os.path.exists(bkg_file):
            raise Exception("Matching background file not found for:", sig_file)
        bkg_files.append(bkg_file)
    
    test_data, train_data = {}, {}
    for sig_file, bkg_file in zip(sig_files, bkg_files):
        print(f"Combining {sig_file} and {bkg_file}...", end="", flush=True)
        
        sig_data = read_data_pytables(sig_file)
        bkg_data = read_data_pytables(bkg_file)

        combined_data = {key: np.concatenate([sig_data[key], bkg_data[key]]) for key in sig_data.keys()}
        indices = np.arange(len(combined_data["jet_pt"]))
        np.random.default_rng(0).shuffle(indices)
        
        if "test" in sig_file:
            for key, values in combined_data.items():
                test_data.setdefault(key, []).extend(values[indices])
        else:
            for key, values in combined_data.items():
                train_data.setdefault(key, []).extend(values[indices])
        
        print("Completed!")

    write_data_pytables(f"{out_dir}/test_{filename}.part.h5", {k: np.array(v) for k, v in test_data.items()})
    write_data_pytables(f"{out_dir}/train_{filename}.part.h5", {k: np.array(v) for k, v in train_data.items()})

def open_sig_and_bkg(file_dir, sig_tag, bkg_tag, filename="", labelname="label_sig"):
    out_dir = "/AtlasDisk/user/duquebran/particle_transformer/PFN/data_train"
    shuffle_and_merge(file_dir, sig_tag, bkg_tag, filename)
    
    print("TEMPORARY FILES CREATED. REWEIGHTING TRAIN FILE.")
    
    with tables.open_file(f"{out_dir}/train_{filename}.part.h5", mode="r+") as train_file:
        pt = train_file.root.jet_pt[:]
        labels = train_file.root[labelname][:]
        bkg_weight = match_weights(pt[labels == 0], pt[labels == 1])
        
        weights = train_file.root.weight[:]
        bkg_indices = np.where(labels == 0)[0]
        weights[bkg_indices] = bkg_weight[:len(bkg_indices)]
        
        # Update weights in the file
        train_file.root.weight[:] = weights

    os.rename(f"{out_dir}/train_{filename}.part.h5", f"{out_dir}/train_{filename}.h5")
    os.rename(f"{out_dir}/test_{filename}.part.h5", f"{out_dir}/test_{filename}.h5")
    
    print("COMPLETED!")

input_dir = "/AtlasDisk/user/duquebran/particle_transformer/PFN/data_out/"
open_sig_and_bkg(input_dir, "H", "qcd", filename="qcd", labelname="label_QCD")
open_sig_and_bkg(input_dir, "H", "top", filename="top", labelname="label_top")
open_sig_and_bkg(input_dir, "H", "WZ", filename="WZ", labelname="label_WZ")
