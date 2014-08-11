#!/usr/bin/env python
from __future__ import print_function
import tables as tb
import shutil, os, fnmatch
import numpy as np
from numpy import linalg as LA
import matplotlib.pyplot as plt
import pandas as pd
import multiprocessing
import argparse

def relative_error(paths, node, filename, queue):
    """
    Calculate relative error using Frobenius norm
    """
    data1 = get_data(paths[0], node)
    data2 = get_data(paths[1], node)
    diff = (data1 - data2).fillna(0)
    queue.put((filename, LA.norm(diff) / (LA.norm(data1) + 1E-20)))

    detail = False
    results = {}
    if detail:
        for c in range(data1.iloc[0].count()):
            col_diff = (data1[c] - data2[c]).fillna(0)
            results[c] = LA.norm(col_diff) / (LA.norm(data1[c]) + 1E-20)

        for error, file in sorted(zip(results.values(), results.keys())):
            print(error, file)
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

def find_h5_files(dir_old, dir_new, recursive):
    """
    Find matching h5 files from two directories. Return dictionary of the form,
    {filename: (path_old, path_new)}
    """
    matches = {}
    for root, dirs, filenames in os.walk(dir_old):
        if root.count(os.sep) >= 1 and not recursive:
            break
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
    proc_list = list()
    result_queue = multiprocessing.Queue()
    for filename, paths in h5_files.items():
        job = multiprocessing.Process(target=relative_error,
                                      args=(paths, node, filename, result_queue))
        proc_list.append(job)
        job.start()
    [p.join() for p in proc_list]
    while not result_queue.empty():
        filename, one_proc_data = result_queue.get()
        results[filename.split('.')[0]] = round(one_proc_data, 3)
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

    plt.savefig('h5diff_results.png')


def main():
    """
    Given two directories, find and compare all matching h5 files, returning sorted
    list of normalized differences calculted with Frobenius norm.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=str, nargs='+',
                        help='two files to be differenced')
    parser.add_argument('-n', '--node',
                        help='name of the node or group to be differenced')
    parser.add_argument('-r', '--recursive',
                        help='difference all matching .h5 files recursively',
                        action='store_true')
    parser.add_argument('-p', '--plot',
                        help='generate a plot of the results',
                        action='store_true')
    parser.add_argument('-d', '--detail',
                        help='generate a detailed report of the largest differences',
                        action='store_true')
    args = parser.parse_args()

    dir_old = args.files[0]
    dir_new = args.files[1]
    node = args.node

    if os.path.isfile(dir_old):
        filename = dir_old.split('/')[-1]
        h5_files = {filename: (dir_old, dir_new)}
    if os.path.isdir(dir_old):
        h5_files = find_h5_files(dir_old, dir_new, args.recursive)

    print('Processing {} pairs of .h5 files.'.format(len(h5_files)))
    
    results = diff_all_files(h5_files, node)

    for error, file in sorted(zip(results.values(), results.keys())):
        print(error, file)

    if args.plot:
        plot(sorted(zip(results.values(), results.keys()), reverse=True)[:10])
    if os.path.isfile(dir_old) and args.detail:
        pass
        


if __name__ == '__main__':
    import cProfile
    # cProfile.run('main()',sort='cumtime')
    main()
