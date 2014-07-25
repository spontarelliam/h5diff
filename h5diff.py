#!/usr/bin/env python
from __future__ import print_function
import tables as tb
import shutil, os, fnmatch
from subprocess import Popen, PIPE, call
import numpy as np
from numpy import linalg as LA
import matplotlib.pyplot as plt
import operator
import sys
import pandas as pd
import multiprocessing

def relative_error(paths, node, queue):
    """
    Calculate relative error using Frobenius norm
    """
    data1 = get_data(paths[0], node)
    data2 = get_data(paths[1], node)
    diff = (data1 - data2).fillna(0)
    queue.put(LA.norm(diff) / LA.norm(data1))
    return

def get_data(filename, node):
    """
    Accepts filename and returns respective data arrays
    """
    pytfile = tb.File(filename)
    group = str(pytfile.listNodes('/')[0]).split()[0]
    data = pd.DataFrame(pytfile.getNode(group, node)[:,:])
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

def diff_all_files(h5_files, node):
    """
    Calculate a relative error for every h5 file in the target directory.
    Return a list of sorted results.
    """
    results = {}
    result_queue = multiprocessing.Queue()
    for filename, paths in h5_files.items():
        job = multiprocessing.Process(target=relative_error,
                                      args=(paths, node, result_queue))
        job.start()
        results[filename.split('.')[0]] = round(result_queue.get(), 3)
        job.join()
    return results 

def plot(results):
    """
    plot the results in a sorted bar chart.
    """
    values = [value for value, file in results]
    files = [file for value, file in results]
    index = np.arange(len(results))

    fig, ax = plt.subplots(1,1)
    plt.subplots_adjust(bottom=0.4)

    ax.bar(index, values)

    # Axes and labels
    ax.set_title('Relative Error Between Matching H5 Files')
    ax.set_xlabel('File Name')
    ax.set_ylabel('Relative Error')
    # ax.set_xlim(0,20)
    ax.set_xticks(index, files)
    ax.set_xticklabels(files, rotation=80, fontsize=10)

    plt.savefig('h5diff.png')
    # plt.show()

def main():
    """
    Given two directories, find and compare all matching h5 files, returning sorted
    list of normalized differences calculted with Frobenius norm.
    """
    dir_old = sys.argv[1]
    dir_new = sys.argv[2]
    node = sys.argv[3]

    h5_files = find_h5_files(dir_old, dir_new)
    results = diff_all_files(h5_files, node)

    for error, file in sorted(zip(results.values(), results.keys())):
        print(error, file)
    plot(sorted(zip(results.values(), results.keys()), reverse=True)[:10])


if __name__ == '__main__':
    import cProfile
    # cProfile.run('main()',sort='cumtime')
    main()
