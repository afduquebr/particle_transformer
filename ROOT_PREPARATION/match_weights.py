import uproot
import awkward as ak
import numpy as np
import glob
import os
import hep_ml.reweight as reweight

def match_weights(pt, target, n_bins=200):
    """ Calculate weights to match pt distribution to the target distribution. """
    reweighter = reweight.BinsReweighter(n_bins=n_bins)
    reweighter.fit(pt, target=target)
    weights = reweighter.predict_weights(pt)
    return weights / weights.mean()  # Normalize weights

def process_files(file_dir, tree, sig_tag, bkg_tag, filename, step_size=256, labelname="label_sig"):
    out_dir = "/sps/atlas/a/aduque/particle_transformer/PFN/data_train_no_sig"
    
    # Get corresponding signal and background files
    sig_files = glob.glob(file_dir + sig_tag + "*")
    bkg_files = [sig_f.replace(sig_tag, bkg_tag) for sig_f in sig_files if glob.glob(sig_f.replace(sig_tag, bkg_tag))]

    # Process training data
    print("Processing training files to compute reweighting...")
    sig_pt = []
    bkg_pt = []
    
    for sig_f, bkg_f in zip(sig_files, bkg_files):
        with uproot.open(f"{sig_f}:{tree}") as sig, uproot.open(f"{bkg_f}:{tree}") as bkg:
            sig_pt.append(sig["jet_pt"].array())
            bkg_pt.append(bkg["jet_pt"].array())

    sig_pt = ak.flatten(ak.Array(sig_pt))
    bkg_pt = ak.flatten(ak.Array(bkg_pt))
    
    bkg_weights = match_weights(bkg_pt, sig_pt)

    # Save reweighted background
    print("Reweighting and saving background files...")
    out_file = uproot.recreate(f"{out_dir}/train_{filename}.root")
    
    count = 0
    for bkg_f in bkg_files:
        for array in uproot.iterate(f"{bkg_f}:{tree}", step_size=step_size):
            if count == 0:
                branches = {col: ak.type(array[col]) for col in array.fields if array[col].ndim <= 2}
                out_file.mktree("tree", branches)
            
            n_bkg = len(array["weight"])
            weight_slice = bkg_weights[count : count + n_bkg]
            array["weight"] = weight_slice
            out_file["tree"].extend(array)
            count += n_bkg

    out_file.close()
    print("Completed reweighted background file.")

    # **Merge all signal files into one**
    print("Merging all signal files into a unified train_sig file...")
    out_sig_file = uproot.recreate(f"{out_dir}/train_sig_{filename}.root")
    
    count = 0
    for sig_f in sig_files:
        for array in uproot.iterate(f"{sig_f}:{tree}", step_size=step_size):
            if count == 0:
                branches = {col: ak.type(array[col]) for col in array.fields if array[col].ndim <= 2}
                out_sig_file.mktree("tree", branches)
            
            out_sig_file["tree"].extend(array)
            count += len(array["weight"])

    out_sig_file.close()
    print("Completed unified signal file.")

    print("Done!")

input_dir = "/sps/atlas/a/aduque/particle_transformer/PFN/data_out/"
process_files(input_dir, "tree", "H", "qcd", step_size=256, filename="qcd", labelname="label_QCD")    
process_files(input_dir, "tree", "H", "top", step_size=256, filename="top", labelname="label_top")    
process_files(input_dir, "tree", "H", "WZ", step_size=256, filename="WZ", labelname="label_WZ")    


# input_dir = "/sps/atlas/a/aduque/particle_transformer/PFN/data_out5/"
# process_files(input_dir, "tree", "H", "qcd", step_size=256, filename="qcd", labelname="label_QCD")    
# process_files(input_dir, "tree", "H", "top", step_size=256, filename="top", labelname="label_top")    
# process_files(input_dir, "tree", "H", "W", step_size=256, filename="W", labelname="label_W")    
# process_files(input_dir, "tree", "H", "Z", step_size=256, filename="Z", labelname="label_Z")    