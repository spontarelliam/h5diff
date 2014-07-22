#!/usr/bin/env python
from __future__ import print_function
import tables as tb
import shutil, os, fnmatch
from subprocess import Popen, PIPE, call
import numpy as np
from numpy import linalg as LA
import matplotlib.pyplot as plt
import sys


def relative_error(data1, data2):
    """
    Calculate relative error using Frobenius norm
    """
    diff = data1 - data2
    return LA.norm(diff) / LA.norm(data1)

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
    {filename: (path_old, path_new)}
    """
    matches = {}
    for root, dirs, filenames in os.walk(dir_old):
        for filename in fnmatch.filter(filenames, '*.h5'):
            path_old = os.path.join(root, filename)
            path_new = os.path.join(root.replace(dir_old, dir_new), filename)
            if os.path.exists(path_new):
                matches[filename] = (path_old, path_new)
    return matches

def diff_all_files(oldDir, newDir):
    """
    Calculate a mean std dev for every h5 file in the target directory.
    Return a list of sorted results.
    """
    results = {}
    h5_files = find_h5_files(oldDir, newDir)
    for filename, paths in h5_files.items():
        data1 = get_data(paths[0])
        data2 = get_data(paths[1])
        results[filename.split('.')[0]] = round(relative_error(data1, data2), 3)
    return results

def plot(results):
    """
    plot the results in a sorted bar chart.
    """
    values = [value for value, file in results]
    files = [file for value, file in results]
    index = np.arange(len(results))
    plt.bar(index,values,0.3)
    plt.xticks(index, files)

    plt.title('Relative Error Between Matching H5 Files')
    plt.xlabel('File Name')
    plt.ylabel('Relative Error')
    plt.show()

def main():
    """
    Given two directories, find and compare all matching h5 files, returning sorted
    list of normalized differences calculted with Frobenius norm.
    """
    dir_old = sys.argv[1]
    dir_new = sys.argv[2]
    print(dir_old, dir_new)

    results = diff_all_files(dir_old, dir_new)

    # present results
    for error, file in sorted(zip(results.values(), results.keys())):
        print(error, file)
    plot(sorted(zip(results.values(), results.keys()), reverse=True)[:10])


if __name__ == '__main__':
    # import cProfile
    # cProfile.run('main()',sort='cumtime')
    main()
