#!/usr/bin/env python
import tables as tb
import shutil, os, fnmatch
from subprocess import Popen, PIPE, call
import numpy as np
import math
from numpy import linalg as LA
import threading, Queue
import operator
import matplotlib.pyplot as plt

def find_diffs_fast(data1, data2):
    """Return list of nonmatching column numbers"""
    diff = data1[:,:] - data2[:,:]
    columns = (diff != 0).sum(0)
    # index = [i for i, col in enumerate(columns) if col !=0]
    for col in columns:
        if col != 0:
            print r_squared(data1[:,col], data2[:,col])
    # return index

def squared_row_norms(X):
    # From http://stackoverflow.com/q/19094441/166749
    return np.einsum('ij,ij->i', X, X)

def squared_euclidean_distances(data, vec):
    data2 = squared_row_norms(data)
    vec2 = squared_row_norms(vec)
    d = np.dot(data, vec2).ravel()
    # d *= -2
    # d += data2
    # d += vec2
    return d

def relative_error(data1, data2):
    """
    Calculate relative error using L1 norm of matrices
    """
    diff = data1 - data2
    return LA.norm(diff, ord=1) / LA.norm(data1, ord=1)

def get_data(filename):
    """
    Accepts filename and returns respective data arrays
    """
    pytfile = tb.File(filename)
    group = str(pytfile.listNodes('/')[0]).split()[0]
    data = pytfile.getNode(group, 'Transient_Data')[:,:]
    pytfile.close() 
    return data

def find_h5_files(dir_old, dir_new):
    """
    Find matching h5 files from two directories. Return dictionary of the form,
    {casename: (path_old, path_new)}
    """
    matches = {}
    for root, dirs, filenames in os.walk(dir_old):
        for filename in fnmatch.filter(filenames, '*.h5'):
            path_old = os.path.join(root, filename)
            path_new = os.path.join(root.replace(dir_old, dir_new), filename)
            if os.path.exists(path_new):
                matches[filename] = (path_old, path_new)
    return matches

def diff_all_cases(oldDir, newDir):
    """
    Calculate a mean std dev for every case in the target directory.
    Return a list of sorted results.
    """
    results = {}
    h5_files = find_h5_files(oldDir, newDir)
    for filename, paths in h5_files.items():
        data1 = get_data(paths[0])
        data2 = get_data(paths[1])

        print relative_error(data1, data2)
        print squared_euclidean_distances(data1, data2)

        results[filename.split('.')[0]] = round(relative_error(data1, data2), 4)
    return results

def plot(results):
    """
    plot the results in a sorted bar chart.
    """
    print results[1,0]
    index = np.arange(len(results))
    plt.bar(index,results,0.3)
    plt.xticks(index, results[0])
    plt.show()

def main():
    """
    Given two directories, find and compare all matching h5 files, returning sorted list of L2 norms.
    """
    file1 = "2dtestcases_udec13.h5"
    file2 = "2dtestcases_ujun14_row.h5"

    dir_old = '/nfs/home/aspontarelli/S-RELAP5/runCOA/results.tmp/udec13'
    dir_new = '/nfs/home/aspontarelli/S-RELAP5/runCOA/results.tmp/uaug13'
    dir_old = '/nfs/home/aspontarelli/S-RELAP5/runCOA/results.tmp/udec13/cctf/pwrlbrv2'
    dir_new = '/nfs/home/aspontarelli/S-RELAP5/runCOA/results.tmp/uaug13/cctf/pwrlbrv2'

    results = diff_all_cases(dir_old, dir_new)
    for case, error in sorted(results.iteritems(), key=operator.itemgetter(1)):
        print error, case

    # plot(sorted(results.iteritems(), key=operator.itemgetter(1), reverse=True)[:10])


if __name__ == '__main__':
    import cProfile
    # cProfile.run('main()',sort='tottime')
    # cProfile.run('main()',sort='cumtime')
    main()
