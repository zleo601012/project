from __future__ import annotations
import pickle

def dump(obj, filename):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)


def load(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)
