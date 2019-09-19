#!/bin/env python

import os
import sys
import csv
import glob
import cga_util

#whitelist_glob = sys.argv[1]
#dirscans_glob = sys.argv[2]

#whitelist_glob = '/xchip/tcga/cleanup/whitelists/*.txt'
whitelist_glob = '/xchip/tcga/cleanup/whitelists2/*/*.txt'
#dirscan_glob = '/xchip/tcga/cleanup/cga_home_2019-08-07/getzlab_scans/*dirs.txt'
dirscan_glob2 = '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans7_cga_home/*dirs.txt'
dirscan_glob1 = '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans3/*dirs.txt'
#dirscan_glob = '/xchip/tcga/cleanup/cga_home_2019-08-07/getzlab_scans/xchip_cga_home_gadgetz__2019_08_07__11_21_13.dirs.txt'
outpath = '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/whitelist_sum.txt'
outpath = '/xchip/tcga/cleanup/whitelist_sum_2019-08-19.txt'

info_by_path = {}
whitelist_paths = glob.glob(whitelist_glob)
whitelist_paths.sort()
for inpath in whitelist_paths:
    in_path_list = inpath.split('/')
    infn = '/'.join(in_path_list[-2:])
    with open(inpath) as ifid:
        reader = csv.reader(ifid, dialect='excel-tab')
        for line in reader:
            if len(line) < 1:
                continue
            raw_path = line[0]
            if not raw_path.endswith('/*'):
                raise Exception('path does not end with /*: %s  %s'%(inpath, raw_path))
            fixed_path = raw_path[:-2]
            info_by_path[fixed_path] = {'source': infn, 'dir': fixed_path}

max_path_len = 0
for path in info_by_path:
    if len(path) > max_path_len:
        max_path_len = len(path)

dirscan_paths = glob.glob(dirscan_glob1) + glob.glob(dirscan_glob2)
dirscan_paths.sort()
for inpath in dirscan_paths:
    if '.annot.' in inpath:
        continue
    print (inpath)
    with open(inpath) as ifid:
        reader = csv.DictReader(ifid, dialect='excel-tab')
        for line in reader:
            path = line['dir']
            if path in info_by_path:
                sz = float(line['size'])
                sztb = sz / 1.12e12
                sztb_str = '%6.2f' % sztb
                info_by_path[path]['sizeTB'] = sztb_str
                info_by_path[path].update(line)


for path in info_by_path:
    print(info_by_path[path])

fieldnames = ['source','dir', 'files', 'sizeTB', 'size', 'last_access', 'last_modified', 'fract', 'fractcat']
cga_util.dump_dict_table(outpath, info_by_path, fields=fieldnames)
