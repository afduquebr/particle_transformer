# import uproot
# import awkward as ak
# import numpy as np
# import glob
# import json
# from prep_functions import common_cuts, signal_cuts, simple_angular
# import h5py
# import pickle

# def selection_cuts(batch, signal_bool, R22TruthLabelValues = []):
#     #Apply selections cuts depending on sig/bkg
#     cuts = signal_cuts(batch,R22TruthLabelValues=R22TruthLabelValues) if signal_bool else common_cuts(batch)
#     batch = {kw: batch[kw][cuts,...] for kw in batch.fields}
#     return batch
    
# def preprocess(jets,branches):
#     #sort constits by pt
#     pt = ak.nan_to_none(jets["fjet_clus_pt"])
#     pt_pad = ak.pad_none(pt,3, axis=1)
#     pt_pad = ak.fill_none(pt_pad, 0, axis=1)
#     sort_indeces = ak.argsort(pt_pad, axis=1,ascending=False) #decreasing pt

#     #centre jets using 3 lead jets
#     jets = simple_angular(
#         jets,
#         sort_indeces
#         )

#     #sort by decreasing pt
#     for branch in branches:
#         if "_clus_" in branch:
#             jets[branch] = jets[branch][sort_indeces]
        
#     return jets

# def define_jet_level_quantities(dset, data=None):
#     if data is None:
#         data = ak.zip({'fjet_truthJet_eta':np.array([i[26] for i in dset[:]])})
#     else:
#         data['fjet_truthJet_eta'] = np.array([i[26] for i in dset[:]]) 
#     data['fjet_truthJet_pt'] = np.array([i[25] for i in dset[:]])
#     data['fjet_pt'] = np.array([i[0] for i in dset[:]])
#     data['fjet_m'] = np.array([i[3] for i in dset[:]])
#     data['R10TruthLabel_R22v1'] = np.array([i[38] for i in dset[:]])
#     return data

# def split_input_files(config):
#     max_jets = config["max_jets"]
#     num_outputs = config["num_outputs"]
#     #get filenames
#     filenames = []
#     for i_f in config["in_file"]:
#         filenames = np.append(filenames,glob.glob(i_f))
#     jet_count_dict = dict((fn,0) for fn in filenames)
    
#     # Try Loading data from pickle
#     try:
#         with open(config["pickle_dict_file"], 'rb') as pickle_file:
#             jet_count_dict = pickle.load(pickle_file)
#     except Exception:
#         jet_count_dict = {}

#     #Find the number of jets in each file
#     for fn in filenames:
#         if not (fn in list(jet_count_dict.keys())):
#             jet_count_dict[fn] = 0
        
#             print("Opening File:",fn)
#             dset = h5py.File(fn, 'r')
#             for chunk in dset["flow"].iter_chunks():
#                 _data = define_jet_level_quantities(dset["jets"][chunk[0]])
#                 _data['fjet_numConstituents'] = ak.count_nonzero(dset['flow'][chunk][:]["valid"], axis=-1)
#                 _data = selection_cuts(_data,config["signal"],R22TruthLabelValues=config["R22TruthLabelValues"]) #Apply selection cuts to avoid later problems with jets being cut
#                 jet_count_dict[fn]+=len(_data["fjet_m"])
#             dset.close()
#         else: print("Using Saved Jet Numbers for File:",fn)

#     #Overwrite pickle file
#     with open(config["pickle_dict_file"], 'wb') as pickle_file:
#         pickle.dump(jet_count_dict, pickle_file, protocol=pickle.HIGHEST_PROTOCOL)

#     jet_count_dict = {i:jet_count_dict[i] for i in jet_count_dict if i in filenames}
#     num_jets_in_samples = sum(jet_count_dict.values())

#     if max_jets is None: max_jets = num_jets_in_samples #if None, take all jets
    
#     #ensure max_jets is smaller or equal than num_jets_in_sample
#     if max_jets > num_jets_in_samples:
#         print("\nWARNING: max_jets too high. Instead saving max number of jets in sample:",num_jets_in_samples,"\n")
#         max_jets = num_jets_in_samples
        
#     #Take fraction of jets determined by max_jets
#     for key in jet_count_dict.keys():
#         jet_count_dict[key] = int(jet_count_dict[key]*max_jets/num_jets_in_samples) #Round down
#     len_output = np.floor(max_jets/num_outputs)
        
#     print("Processing into",num_outputs,"output files: Each with length",len_output,"Jets")
#     print("TOTAL JETS:",int(num_outputs*len_output)) #Number of jets may have been rounded down
    
#     return jet_count_dict, len_output

# def skim(in_file_name, out_file_names, signal, branches_to_keep, max_constits=80, max_jets=None, truth_labels=None, R22TruthLabelValues=[], out_file=None, output_length=None,out_file_index=0,num_jets_file = 0,metadata=None):
#     num_jets_total = 0
#     dset = h5py.File(in_file_name, 'r')
#     # read
#     for chunk in dset['flow'].iter_chunks():
        
#         h5_data = dset['flow'][chunk]
#         jet_eta = np.array([i[1] for i in dset['jets'][chunk[0]][:]])
#         input_data=ak.zip({"jet_pt":ak.sum(ak.mask(h5_data[:]["flow_pt"],h5_data[:]["valid"]==True),axis=-1),
#             "jet_energy":ak.sum(ak.mask(h5_data[:]["flow_energy"],h5_data[:]["valid"]==True),axis=-1)})

#         input_data["fjet_clus_E"] = h5_data[:]["flow_energy"]
#         input_data["fjet_clus_pt"] = h5_data[:]["flow_pt"]
#         input_data["fjet_clus_phi"]= h5_data[:]["flow_phi"]
#         input_data["fjet_clus_eta"]= h5_data[:]["flow_eta"]
#         input_data["fjet_clus_deltaphi"]= h5_data[:]["flow_dphi"]
#         input_data["fjet_clus_deltaeta"]= h5_data[:]["flow_deta"]
#         input_data["valid"] = h5_data[:]["valid"]
        
#         #Define other training quantities
#         if truth_labels is None:
#             input_data["label_QCD"]=not signal
#             input_data["label_sig"]=signal
#         else:
#             for lab in truth_labels.keys():
#                 input_data[lab] = truth_labels[lab]
#         input_data['fjet_numConstituents'] = ak.count_nonzero(input_data["valid"], axis=-1)
#         input_data["jet_pt"] = ak.sum(ak.mask(input_data["fjet_clus_pt"],input_data['valid']==True),axis=-1)
#         input_data["jet_energy"] = ak.sum(ak.mask(input_data["fjet_clus_E"],input_data['valid']==True),axis=-1)
        
#         #Calculate test weights (WITHOUT luminosity at the moment (overall norm, so only important when comparing to data))
#         mcEventWeight = np.array([i[39] for i in dset["jets"][chunk[0]][:]])
#         input_data["fjet_testing_weight_pt"] = mcEventWeight*metadata["XSection_pb"]*metadata["kFactor"]*metadata["genFilterEff"]/metadata["sumWeights"]
#         input_data["weight"]=1.0 #SET WEIGHTS TO 1, USE MATCH_WEIGHTS.PY TO CHANGE THIS LATER
        
#         #Preprocess and selection cuts
#         input_data = define_jet_level_quantities(dset["jets"][chunk[0]], data=input_data)   
#         input_data = preprocess(input_data,branches_to_keep)
#         input_data = selection_cuts(input_data,signal,R22TruthLabelValues=R22TruthLabelValues) #CUTTING AWAY EVENTS MAY CAUSE PROBLEMS IF MAX_JETS IS TOO HIGH
#         #ADD EVENTS UNTIL MAX_JETS PASSED
#         if not (max_jets is None):
#             new_num_jets = num_jets_total+len(input_data["fjet_clus_pt"])
#             if  new_num_jets < max_jets:
#                 num_jets_total = new_num_jets
#             else:
#                 for branch in branches_to_keep:
#                     input_data[branch] = input_data[branch][:max_jets-num_jets_total]
#                 num_jets_total=max_jets
        
#         for branch in branches_to_keep:
#             if "_clus_" in branch:
#                 #PAD and CLIP
#                 input_data[branch] = ak.nan_to_none(input_data[branch])
#                 input_data[branch] = ak.pad_none(input_data[branch],max_constits,axis=1,clip=True)
#                 input_data[branch] = ak.fill_none(input_data[branch],-999,axis=1)
#                 input_data[branch] = ak.values_astype(input_data[branch], "float32")
                       
#         branches = {}
#         for column in input_data.keys():
#             # Define branch data types for writing to HDF5
#             if not input_data[column].ndim > 2 and column in branches_to_keep:
#                 branches[column] = input_data[column]
                       
#         # Split data before opening files
#         branch_splits = {branch: np.array_split(branch_data, len(out_file_names)) for branch, branch_data in branches.items()}

#         print(f"Writing {len(input_data['fjet_clus_pt'])} Jets to target files...", end="")

#         # Open files and write datasets
#         for i, fn in enumerate(out_file_names):
#             with h5py.File(fn, 'w') as out:
#                 for branch, split_data in branch_splits.items():
#                     out.create_dataset(branch, data=split_data[i], compression='gzip')  # Add compression if needed
#             print(f"File {fn} written.")

#         print("Done")
            
#         if num_jets_total == max_jets:
#             break # If max jets from input file reached, stop

#     return out_file, out_file_index, num_jets_file

# def run(config):
#     with open(config["metadata_file"]) as f:
#         metadata = json.load(f)
    
#     # Create output file names for HDF5
#     out_file_names = [config["out_file_dir"] + config["out_file_tag"] + "_" + ("test" if i < config["num_test"] else "train") + "_" + str(i) + ".h5" for i in range(config["num_outputs"])]

#     # Get number of jets to save per input file and the number to save per output file
#     jet_count_dict, output_length = split_input_files(config)
    
#     out_file = None
#     out_file_index = 0
#     num_jets_file = 0

#     # Skim each input file
#     for key in jet_count_dict.keys():
#         print("Loading file:", key)
#         dsid = key.split("user.rles.")[1].split(".")[0]
#         try:
#             file_metadata = metadata[dsid]
#         except Exception:
#             print("Key:", dsid, "not present in metadata file. Terminating!")
#             raise SystemExit
#         print(config["labels"])
#         out_file, out_file_index, num_jets_file = skim(
#             key, out_file_names, config["signal"], config["branches_to_keep"],
#             config["max_constits"], jet_count_dict[key], truth_labels=config["labels"],
#             R22TruthLabelValues=config["R22TruthLabelValues"], out_file=out_file,
#             output_length=output_length, out_file_index=out_file_index,
#             num_jets_file=num_jets_file, metadata=file_metadata)

#     print("\nNOTE: WEIGHTS HAVE BEEN ALL SET TO 1. USE MATCH_WEIGHTS.PY TO MATCH WEIGHTS OF SIG AND BKG USING PT.")

import awkward as ak
import numpy as np
import glob
import json
from prep_functions import common_cuts, signal_cuts, simple_angular
import tables
import pickle

def selection_cuts(batch, signal_bool, R22TruthLabelValues=[]):
    cuts = signal_cuts(batch, R22TruthLabelValues=R22TruthLabelValues) if signal_bool else common_cuts(batch)
    batch = {kw: batch[kw][cuts, ...] for kw in batch.fields}
    return batch

def preprocess(jets, branches):
    pt = ak.nan_to_none(jets["fjet_clus_pt"])
    pt_pad = ak.pad_none(pt, 3, axis=1)
    pt_pad = ak.fill_none(pt_pad, 0, axis=1)
    sort_indices = ak.argsort(pt_pad, axis=1, ascending=False)
    jets = simple_angular(jets, sort_indices)

    for branch in branches:
        if "_clus_" in branch:
            jets[branch] = jets[branch][sort_indices]

    return jets

def define_jet_level_quantities(dset, data=None):
    if data is None:
        data = ak.zip({'fjet_truthJet_eta': np.array([i[26] for i in dset[:]])})
    else:
        data['fjet_truthJet_eta'] = np.array([i[26] for i in dset[:]])
    data['fjet_truthJet_pt'] = np.array([i[25] for i in dset[:]])
    data['fjet_pt'] = np.array([i[0] for i in dset[:]])
    data['fjet_m'] = np.array([i[3] for i in dset[:]])
    data['R10TruthLabel_R22v1'] = np.array([i[38] for i in dset[:]])
    return data

def split_input_files(config):
    max_jets = config["max_jets"]
    num_outputs = config["num_outputs"]
    filenames = [glob.glob(i_f) for i_f in config["in_file"]]
    filenames = [item for sublist in filenames for item in sublist]  # Flatten list
    jet_count_dict = {fn: 0 for fn in filenames}

    try:
        with open(config["pickle_dict_file"], 'rb') as pickle_file:
            jet_count_dict.update(pickle.load(pickle_file))
    except Exception:
         jet_count_dict = {}

    for fn in filenames:
        if fn not in jet_count_dict:
            jet_count_dict[fn] = 0
            print("Opening File:", fn)

            with tables.open_file(fn, 'r') as dset:
                flow_table = dset.root.flow
                num_rows = flow_table.nrows  # Total number of rows
                chunk_size = flow_table.chunkshape[0]

                for start in range(0, num_rows, chunk_size):
                    stop = min(start + chunk_size, num_rows)

                    # Read chunk of data
                    chunk = flow_table.read(start=start, stop=stop) 

                    # Process the chunk
                    _data = define_jet_level_quantities(chunk)
                    _data['fjet_numConstituents'] = ak.count_nonzero(chunk["valid"], axis=-1)
                    _data = selection_cuts(_data, config["signal"], R22TruthLabelValues=config["R22TruthLabelValues"])

                    # Update jet count
                    jet_count_dict[fn] += len(_data["fjet_m"])


    with open(config["pickle_dict_file"], 'wb') as pickle_file:
        pickle.dump(jet_count_dict, pickle_file, protocol=pickle.HIGHEST_PROTOCOL)

    num_jets_in_samples = sum(jet_count_dict.values())
    max_jets = min(max_jets, num_jets_in_samples) if max_jets else num_jets_in_samples
    for key in jet_count_dict:
        jet_count_dict[key] = int(jet_count_dict[key] * max_jets / num_jets_in_samples)

    len_output = max_jets // num_outputs
    print("Processing into", num_outputs, "output files, each with", len_output, "jets")
    return jet_count_dict, len_output

def skim( in_file_name, out_file_names, signal, branches_to_keep, max_constits=80, max_jets=None, truth_labels=None, R22TruthLabelValues=[], out_file=None, output_length=None, out_file_index=0, num_jets_file=0, metadata=None):
    num_jets_total = 0

    # Open input PyTables file
    with tables.open_file(in_file_name, mode="r") as dset:
        jets_table = dset.root.jets
        flow_table = dset.root.flow
        chunk_size = dset.root.flow.chunkshape[0]
        
        num_entries = jets_table.nrows
        chunk_indices = list(range(0, num_entries, chunk_size))

        # Process data in chunks
        for start in chunk_indices:
            stop = min(start + chunk_size, num_entries)

            # Load chunk data
            print(f"Dataset shape: {flow_table.shape}, Reading range: {start}:{stop}")
            print(flow_table.colnames)  # Check available field names
            print("")
            print(jets_table.colnames)  # Check available field names
            flow_pt = flow_table.read(start=start, stop=stop, field="flow_pt")
            flow_energy = flow_table.read(start=start, stop=stop, field="flow_energy")
            valid = flow_table.read(start=start, stop=stop, field="valid")

            jet_eta = np.array([i[1] for i in jets_table.read(start=start, stop=stop)])
            input_data = ak.zip({
                "jet_pt": ak.sum(ak.mask(flow_pt, valid == True), axis=-1),
                "jet_energy": ak.sum(ak.mask(flow_energy, valid == True), axis=-1),
                "fjet_clus_E": flow_energy,
                "fjet_clus_pt": flow_pt,
                "fjet_clus_phi": flow_table.read(start=start, stop=stop, field="flow_phi"),
                "fjet_clus_eta": flow_table.read(start=start, stop=stop, field="flow_eta"),
                "fjet_clus_deltaphi": flow_table.read(start=start, stop=stop, field="flow_dphi"),
                "fjet_clus_deltaeta": flow_table.read(start=start, stop=stop, field="flow_deta"),
                "valid": valid,
            })

            # Define truth labels
            if truth_labels is None:
                input_data["label_QCD"] = not signal
                input_data["label_sig"] = signal
            else:
                for lab in truth_labels.keys():
                    input_data[lab] = truth_labels[lab]

            input_data['fjet_numConstituents'] = ak.count_nonzero(input_data["valid"], axis=-1)
            input_data["jet_pt"] = ak.sum(ak.mask(input_data["fjet_clus_pt"], input_data['valid'] == True), axis=-1)
            input_data["jet_energy"] = ak.sum(ak.mask(input_data["fjet_clus_E"], input_data['valid'] == True), axis=-1)

            # Test weights
            mcEventWeight = np.array([i[39] for i in jets_table.read(start=start, stop=stop)])
            input_data["fjet_testing_weight_pt"] = mcEventWeight * metadata["XSection_pb"] * metadata["kFactor"] * metadata["genFilterEff"] / metadata["sumWeights"]
            input_data["weight"] = 1.0  # Set weights to 1 for now

            # Preprocess and selection cuts
            input_data = define_jet_level_quantities(jets_table.read(start=start, stop=stop), data=input_data)
            input_data = preprocess(input_data, branches_to_keep)
            input_data = selection_cuts(input_data, signal, R22TruthLabelValues=R22TruthLabelValues)

            # Enforce max_jets
            if max_jets is not None:
                new_num_jets = num_jets_total + len(input_data["fjet_clus_pt"])
                if new_num_jets < max_jets:
                    num_jets_total = new_num_jets
                else:
                    for branch in branches_to_keep:
                        input_data[branch] = input_data[branch][:max_jets - num_jets_total]
                    num_jets_total = max_jets

            for branch in branches_to_keep:
                if "_clus_" in branch:
                    # Pad and clip
                    input_data[branch] = ak.nan_to_none(input_data[branch])
                    input_data[branch] = ak.pad_none(input_data[branch], max_constits, axis=1, clip=True)
                    input_data[branch] = ak.fill_none(input_data[branch], -999, axis=1)
                    input_data[branch] = ak.values_astype(input_data[branch], "float32")

            # Split branches for writing
            branches = {}
            for column in input_data.keys():
                if not input_data[column].ndim > 2 and column in branches_to_keep:
                    branches[column] = input_data[column]

            branch_splits = {branch: np.array_split(branch_data, len(out_file_names)) for branch, branch_data in branches.items()}

            # Write to output files
            print(f"Writing {len(input_data['fjet_clus_pt'])} Jets to target files...", end="")
            for i, fn in enumerate(out_file_names):
                with tables.open_file(fn, mode="w") as out:
                    for branch, split_data in branch_splits.items():
                        atom = tables.Atom.from_dtype(split_data[i].dtype)
                        shape = split_data[i].shape
                        out.create_carray(out.root, branch, atom, shape)
                        out.root[branch][:] = split_data[i]
                print(f"File {fn} written.")
            print("Done.")

            if num_jets_total == max_jets:
                break  # Stop if max_jets is reached

    return out_file, out_file_index, num_jets_file

def run(config):
    with open(config["metadata_file"]) as f:
        metadata = json.load(f)

    out_file_names = [config["out_file_dir"] + config["out_file_tag"] + "_" + ("test" if i < config["num_test"] else "train") + f"_{i}.h5" for i in range(config["num_outputs"])]
    jet_count_dict, output_length = split_input_files(config)

    for key in jet_count_dict.keys():
        print("Processing file:", key)
        dsid = key.split("user.rles.")[1].split(".")[0]
        file_metadata = metadata.get(dsid, None)
        if file_metadata is None:
            raise ValueError(f"Metadata for DSID {dsid} is missing.")

        skim(key, out_file_names, config["signal"], config["branches_to_keep"], config["max_constits"], jet_count_dict[key], config["labels"], config["R22TruthLabelValues"], file_metadata)




############################################################################################

import awkward as ak
import numpy as np
import glob
import json
from prep_functions import common_cuts, signal_cuts, simple_angular
import tables
import pickle

def selection_cuts(batch, signal_bool, R22TruthLabelValues=[]):
    cuts = signal_cuts(batch, R22TruthLabelValues=R22TruthLabelValues) if signal_bool else common_cuts(batch)
    batch = {kw: batch[kw][cuts, ...] for kw in batch.fields}
    return batch

def preprocess(jets, branches):
    pt = ak.nan_to_none(jets["fjet_clus_pt"])
    pt_pad = ak.pad_none(pt, 3, axis=1)
    pt_pad = ak.fill_none(pt_pad, 0, axis=1)
    sort_indices = ak.argsort(pt_pad, axis=1, ascending=False)
    jets = simple_angular(jets, sort_indices)

    for branch in branches:
        if "_clus_" in branch:
            jets[branch] = jets[branch][sort_indices]

    return jets

def define_jet_level_quantities(dset, data=None):
    if data is None:
        data = ak.zip({'fjet_truthJet_eta': np.array(dset[:, 26])})
    else:
        data['fjet_truthJet_eta'] = np.array(dset[:, 26])
    data['fjet_truthJet_pt'] = np.array(dset[:, 25])
    data['fjet_pt'] = np.array(dset[:, 0])
    data['fjet_m'] = np.array(dset[:, 3])
    data['R10TruthLabel_R22v1'] = np.array(dset[:, 38])
    return data

def process_file(fn, config, jet_count_dict):
    print("Opening File:", fn)
    with tables.open_file(fn, 'r') as dset:
        flow_table = dset.root.flow
        chunk = flow_table.read()  # Read entire dataset at once
        
        _data = define_jet_level_quantities(chunk)
        _data['fjet_numConstituents'] = ak.count_nonzero(chunk["valid"], axis=-1)
        _data = selection_cuts(_data, config["signal"], R22TruthLabelValues=config["R22TruthLabelValues"])
        
        jet_count_dict[fn] = len(_data["fjet_m"])
    return jet_count_dict

def split_input_files(config):
    filenames = [glob.glob(i_f) for i_f in config["in_file"]]
    filenames = [item for sublist in filenames for item in sublist]
    jet_count_dict = {fn: 0 for fn in filenames}

    try:
        with open(config["pickle_dict_file"], 'rb') as pickle_file:
            jet_count_dict.update(pickle.load(pickle_file))
    except Exception:
        jet_count_dict = {}

    for fn in filenames:
        if fn not in jet_count_dict:
            jet_count_dict = process_file(fn, config, jet_count_dict)

    with open(config["pickle_dict_file"], 'wb') as pickle_file:
        pickle.dump(jet_count_dict, pickle_file, protocol=pickle.HIGHEST_PROTOCOL)

    return jet_count_dict


############################################################################################

import uproot
import awkward as ak
import numpy as np
import glob
import json
from prep_functions import common_cuts, signal_cuts, simple_angular
import h5py
import pickle

def selection_cuts(batch, signal_bool, R22TruthLabelValues = []):
    #Apply selections cuts depending on sig/bkg
    cuts = signal_cuts(batch,R22TruthLabelValues=R22TruthLabelValues) if signal_bool else common_cuts(batch)
    batch = {kw: batch[kw][cuts,...] for kw in batch.fields}
    return batch
    
def preprocess(jets,branches):
    #sort constits by pt
    pt = ak.nan_to_none(jets["fjet_clus_pt"])
    pt_pad = ak.pad_none(pt,3, axis=1)
    pt_pad = ak.fill_none(pt_pad, 0, axis=1)
    sort_indeces = ak.argsort(pt_pad, axis=1,ascending=False) #decreasing pt

    #centre jets using 3 lead jets
    jets = simple_angular(
        jets,
        sort_indeces
        )

    #sort by decreasing pt
    for branch in branches:
        if "_clus_" in branch:
            jets[branch] = jets[branch][sort_indeces]
        
    return jets

def define_jet_level_quantities(dset, data=None):
    if data is None:
        data = ak.zip({'fjet_truthJet_eta':np.array([i[26] for i in dset[:]])})
    else:
        data['fjet_truthJet_eta'] = np.array([i[26] for i in dset[:]]) 
    data['fjet_truthJet_pt'] = np.array([i[25] for i in dset[:]])
    data['fjet_pt'] = np.array([i[0] for i in dset[:]])
    data['fjet_m'] = np.array([i[3] for i in dset[:]])
    data['R10TruthLabel_R22v1'] = np.array([i[38] for i in dset[:]])
    return data

def split_input_files(config):
    max_jets = config["max_jets"]
    num_outputs = config["num_outputs"]
    #get filenames
    filenames = []
    for i_f in config["in_file"]:
        filenames = np.append(filenames,glob.glob(i_f))
    jet_count_dict = dict((fn,0) for fn in filenames)
    
    # Try Loading data from pickle
    try:
        with open(config["pickle_dict_file"], 'rb') as pickle_file:
            jet_count_dict = pickle.load(pickle_file)
    except Exception:
        jet_count_dict = {}

    #Find the number of jets in each file
    for fn in filenames:
        if not (fn in list(jet_count_dict.keys())):
            jet_count_dict[fn] = 0
        
            print("Opening File:",fn)
            dset = h5py.File(fn, 'r')
            for chunk in dset["flow"].iter_chunks():
                _data = define_jet_level_quantities(dset["jets"][chunk[0]])
                _data['fjet_numConstituents'] = ak.count_nonzero(dset['flow'][chunk][:]["valid"], axis=-1)
                _data = selection_cuts(_data,config["signal"],R22TruthLabelValues=config["R22TruthLabelValues"]) #Apply selection cuts to avoid later problems with jets being cut
                jet_count_dict[fn]+=len(_data["fjet_m"])
            dset.close()
        else: print("Using Saved Jet Numbers for File:",fn)

    #Overwrite pickle file
    with open(config["pickle_dict_file"], 'wb') as pickle_file:
        pickle.dump(jet_count_dict, pickle_file, protocol=pickle.HIGHEST_PROTOCOL)

    jet_count_dict = {i:jet_count_dict[i] for i in jet_count_dict if i in filenames}
    num_jets_in_samples = sum(jet_count_dict.values())

    if max_jets is None: max_jets = num_jets_in_samples #if None, take all jets
    
    #ensure max_jets is smaller or equal than num_jets_in_sample
    if max_jets > num_jets_in_samples:
        print("\nWARNING: max_jets too high. Instead saving max number of jets in sample:",num_jets_in_samples,"\n")
        max_jets = num_jets_in_samples
        
    #Take fraction of jets determined by max_jets
    for key in jet_count_dict.keys():
        jet_count_dict[key] = int(jet_count_dict[key]*max_jets/num_jets_in_samples) #Round down
    len_output = np.floor(max_jets/num_outputs)
        
    print("Processing into",num_outputs,"output files: Each with length",len_output,"Jets")
    print("TOTAL JETS:",int(num_outputs*len_output)) #Number of jets may have been rounded down
    
    return jet_count_dict, len_output

def skim(in_file_name, out_file_names, signal, branches_to_keep, max_constits=80, max_jets=None, truth_labels=None, R22TruthLabelValues=[], out_file=None, output_length=None,out_file_index=0,num_jets_file = 0,metadata=None):
    num_jets_total = 0
    dset = h5py.File(in_file_name, 'r')
    # read
    for chunk in dset['flow'].iter_chunks():
        
        h5_data = dset['flow'][chunk]
        jet_eta = np.array([i[1] for i in dset['jets'][chunk[0]][:]])
        input_data=ak.zip({"jet_pt":ak.sum(ak.mask(h5_data[:]["flow_pt"],h5_data[:]["valid"]==True),axis=-1),
            "jet_energy":ak.sum(ak.mask(h5_data[:]["flow_energy"],h5_data[:]["valid"]==True),axis=-1)})

        input_data["fjet_clus_E"] = h5_data[:]["flow_energy"]
        input_data["fjet_clus_pt"] = h5_data[:]["flow_pt"]
        input_data["fjet_clus_phi"]=h5_data[:]["flow_phi"]
        input_data["fjet_clus_eta"]=h5_data[:]["flow_eta"]
        input_data["fjet_clus_deltaphi"]=h5_data[:]["flow_dphi"]
        input_data["fjet_clus_deltaeta"]=h5_data[:]["flow_deta"]
        input_data["valid"] = h5_data[:]["valid"]
        
        #Define other training quantities
        if truth_labels is None:
            input_data["label_QCD"]=not signal
            input_data["label_sig"]=signal
        else:
            for lab in truth_labels.keys():
                input_data[lab] = truth_labels[lab]
        input_data['fjet_numConstituents'] = ak.count_nonzero(input_data["valid"], axis=-1)
        input_data["jet_pt"] = ak.sum(ak.mask(input_data["fjet_clus_pt"],input_data['valid']==True),axis=-1)
        input_data["jet_energy"] = ak.sum(ak.mask(input_data["fjet_clus_E"],input_data['valid']==True),axis=-1)
        
        #Calculate test weights (WITHOUT luminosity at the moment (overall norm, so only important when comparing to data))
        mcEventWeight = np.array([i[39] for i in dset["jets"][chunk[0]][:]])
        input_data["fjet_testing_weight_pt"] = mcEventWeight*metadata["XSection_pb"]*metadata["kFactor"]*metadata["genFilterEff"]/metadata["sumWeights"]
        input_data["weight"]=1.0 #SET WEIGHTS TO 1, USE MATCH_WEIGHTS.PY TO CHANGE THIS LATER
        
        #Preprocess and selection cuts
        input_data = define_jet_level_quantities(dset["jets"][chunk[0]], data=input_data)   
        input_data = preprocess(input_data,branches_to_keep)
        input_data = selection_cuts(input_data,signal,R22TruthLabelValues=R22TruthLabelValues) #CUTTING AWAY EVENTS MAY CAUSE PROBLEMS IF MAX_JETS IS TOO HIGH
        #ADD EVENTS UNTIL MAX_JETS PASSED
        if not (max_jets is None):
            new_num_jets = num_jets_total+len(input_data["fjet_clus_pt"])
            if  new_num_jets < max_jets:
                num_jets_total = new_num_jets
            else:
                for branch in branches_to_keep:
                    input_data[branch] = input_data[branch][:max_jets-num_jets_total]
                num_jets_total=max_jets
        
        for branch in branches_to_keep:
            if "_clus_" in branch:
                #PAD and CLIP
                input_data[branch] = ak.nan_to_none(input_data[branch])
                input_data[branch] = ak.pad_none(input_data[branch],max_constits,axis=1,clip=True)
                input_data[branch] = ak.fill_none(input_data[branch],-999,axis=1)
                input_data[branch] = ak.values_astype(input_data[branch], "float32")
                       
        branches = {}
        for column in input_data.keys():
            # can only write out 2D awkward arrays annoyingly
            if not input_data[column].ndim > 2 and column in branches_to_keep:
                branches[column] = ak.type(input_data[column])
                       
        #Open Target Files
        if out_file is None:
            out_file = []
            for fn in out_file_names:
                out = uproot.recreate(fn)
                out.mktree("tree", branches)    
                out_file.append(out)

        if out_file is None:
            out_file = []
            for fn in out_file_names:
                out = tables.open_file(fn, mode="w")
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
        
        #Write Jets
        branch_splits = {branch:np.array_split(np.array(input_data[branch]), len(out_file)) for branch in list(branches.keys())}
        print("Writing",len(input_data["fjet_clus_pt"]),"Jets to target files...",end="")
        for i in range(len(out_file)):
            out_file[i]["tree"].extend({branch: branch_splits[branch][i] for branch in branches.keys()})
        print("Done")
        #out_file,out_file_index,num_jets_file = write(input_data, out_file_names, out_file, branches, output_length, num_jets_file,out_file_index)
            
        if num_jets_total == max_jets: break #If max jets from input file reached, stop uproot.iterate(...)
    return out_file, out_file_index, num_jets_file

def run(config):
    with open(config["metadata_file"]) as f:
        metadata = json.load(f)
    
    #create output file names
    out_file_names = [config["out_file_dir"]+config["out_file_tag"]+"_"+("test" if i < config["num_test"] else "train")+"_"+str(i)+".root" for i in range(config["num_outputs"])]

    #get number of jets to save per input file and the number to save per output file
    jet_count_dict, output_length = split_input_files(config)
    
    out_file = None
    out_file_index = 0
    num_jets_file = 0

    #Skim each input file
    for key in jet_count_dict.keys():
        print("Loading file:",key)
        dsid = key.split("user.rles.")[1].split(".")[0]
        try:
            file_metadata = metadata[dsid]
        except Exception:
            print("Key:",dsid,"not present in metadata file. Terminating!")
            raise SystemExit
        print(config["labels"])
        out_file,out_file_index, num_jets_file = skim(key, out_file_names, config["signal"], config["branches_to_keep"], config["max_constits"], jet_count_dict[key],truth_labels=config["labels"], R22TruthLabelValues=config["R22TruthLabelValues"],out_file=out_file,output_length=output_length,out_file_index=out_file_index,num_jets_file=num_jets_file,metadata=file_metadata)

    for f in out_file:
        f.close()
    print("\nNOTE: WEIGHTS HAVE BEEN ALL SET TO 1. USE MATCH_WEIGHTS.PY TO MATCH WEIGHTS OF SIG AND BKG USING PT.")
        
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
    
