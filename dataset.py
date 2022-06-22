import torch
from torch.utils.data import Dataset, DataLoader
import random
import numpy as np
CHARISOSMISET = {"#": 29, "%": 30, ")": 31, "(": 1, "+": 32, "-": 33, "/": 34, ".": 2,
                 "1": 35, "0": 3, "3": 36, "2": 4, "5": 37, "4": 5, "7": 38, "6": 6,
                 "9": 39, "8": 7, "=": 40, "A": 41, "@": 8, "C": 42, "B": 9, "E": 43,
                 "D": 10, "G": 44, "F": 11, "I": 45, "H": 12, "K": 46, "M": 47, "L": 13,
                 "O": 48, "N": 14, "P": 15, "S": 49, "R": 16, "U": 50, "T": 17, "W": 51,
                 "V": 18, "Y": 52, "[": 53, "Z": 19, "]": 54, "\\": 20, "a": 55, "c": 56,
                 "b": 21, "e": 57, "d": 22, "g": 58, "f": 23, "i": 59, "h": 24, "m": 60,
                 "l": 25, "o": 61, "n": 26, "s": 62, "r": 27, "u": 63, "t": 28, "y": 64}

CHARISOSMILEN = 64

CHARPROTSET = {"A": 1, "C": 2, "B": 3, "E": 4, "D": 5, "G": 6,
               "F": 7, "I": 8, "H": 9, "K": 10, "M": 11, "L": 12,
               "O": 13, "N": 14, "Q": 15, "P": 16, "S": 17, "R": 18,
               "U": 19, "T": 20, "W": 21, "V": 22, "Y": 23, "X": 24, "Z": 25}

CHARPROTLEN = 25

# kmer_AAS = {}
# i = 1
# for i in CHARPROTSET.keys():
#     for j in CHARPROTSET.keys():
#         for k in CHARPROTSET.keys():
#             kmer_AAS[i+j+k] = i
#             i = i+1

def label_smiles(line, smi_ch_ind, MAX_SMI_LEN=100):
    X = np.zeros(MAX_SMI_LEN,dtype=np.int64())
    for i, ch in enumerate(line[:MAX_SMI_LEN]):
        X[i] = smi_ch_ind[ch]
    return X

def label_sequence(line, smi_ch_ind, MAX_SEQ_LEN=1000):
    X = np.zeros(MAX_SEQ_LEN,np.int64())
    for i, ch in enumerate(line[:MAX_SEQ_LEN]):
        X[i] = smi_ch_ind[ch]
    return X

def kmer_encode(line, kmer_AAS, MAX_SEQ_LEN=1000):
    X = np.zeros(MAX_SEQ_LEN,np.int64())
    for i, ch in enumerate(line[:MAX_SEQ_LEN]):
        X[i] = kmer_AAS[line[i:i+3]]
    return X

class CustomDataSet(Dataset):
    def __init__(self, pairs):
        self.pairs = pairs

    def __getitem__(self, item):
        return self.pairs[item]

    def __len__(self):
        return len(self.pairs)

def collate_fn(batch_data):
    N = len(batch_data)
    # drug_ids, protein_ids = [],[]
    compound_max = 100
    protein_max = 1000
    compound_new = torch.zeros((N, compound_max), dtype=torch.long)
    compound_mask = torch.zeros((N, compound_max))
    protein_new = torch.zeros((N, protein_max), dtype=torch.long)
    protein_mask = torch.zeros((N, protein_max))
    labels_new = torch.zeros(N, dtype=torch.long)
    for num, pair in enumerate(batch_data):
        pair = pair.strip().split()
        compoundstr, proteinstr, label = pair[-3], pair[-2], pair[-1]

        smiles_len = len(compoundstr)
        compoundint = torch.from_numpy(label_smiles(compoundstr, CHARISOSMISET, compound_max))
        compound_new[num] = compoundint
        if smiles_len > compound_max:
            compound_mask[num, :] = 1
        else:
            compound_mask[num, :smiles_len] = 1

        pro_len = len(proteinstr)
        proteinint = torch.from_numpy(label_sequence(proteinstr, CHARPROTSET, protein_max))
        # proteinint = torch.from_numpy(kmer_encode(proteinstr, kmer_AAS, protein_max))
        protein_new[num] = proteinint
        if pro_len > protein_max:
            protein_mask[num, :] = 1
        else:
            protein_mask[num, :pro_len] = 1

        labels_new[num] = np.int(float(label))

    return (compound_new, protein_new, compound_mask, protein_mask, labels_new)

class collate_class():
    def __init__(self, dict, compound_max = 100,protein_max=1000):
        self.protein_max = protein_max
        self.compound_max = compound_max
        self.word_dict = dict

    def split_sequence(self, sequence, ngram=3,max_lengh = 1000):
        words = [int(float(self.word_dict[sequence[i:i + ngram]]))
                 for i in range(len(sequence) - ngram + 1)]
        return np.array(words[:max_lengh])

    def __call__(self, batch_data):
        N = len(batch_data)
        compound_new = torch.zeros((N, self.compound_max), dtype=torch.long)
        compound_mask = torch.zeros((N, self.compound_max))
        protein_new = torch.zeros((N, self.protein_max), dtype=torch.long)
        protein_mask = torch.zeros((N, self.protein_max))
        labels_new = torch.zeros(N, dtype=torch.long)
        for num, pair in enumerate(batch_data):
            pair = pair.strip().split()
            compoundstr, proteinstr, label = pair[-3], pair[-2], pair[-1]

            smiles_len = len(compoundstr)
            compoundint = torch.from_numpy(label_smiles(compoundstr, CHARISOSMISET, self.compound_max))
            compound_new[num] = compoundint
            if smiles_len > self.compound_max:
                compound_mask[num, :] = 1
            else:
                compound_mask[num, :smiles_len] = 1

            pro_len = len(proteinstr)
            proteinint = torch.from_numpy(self.split_sequence(proteinstr))
            # proteinint = torch.from_numpy(kmer_encode(proteinstr, kmer_AAS, protein_max))
            protein_new[num,:len(proteinint)] = proteinint
            if pro_len > self.protein_max:
                protein_mask[num, :] = 1
            else:
                protein_mask[num, :pro_len] = 1

            labels_new[num] = np.int(float(label))
        return (compound_new, protein_new, compound_mask, protein_mask, labels_new)