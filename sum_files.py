#!/bin/env python

import csv
import glob

inglob = '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans3/*files.txt'
inglob = '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/old_but_popular/*.files.txt'
inglob = '/sysman/scratch/apsg/alosada/gsaksena/cgastorage/scans/cga_tcga-gsc__2019_06_26__10_09_12.txt'
f_paths = glob.glob(inglob)

total_size = 0
for f_path in f_paths:
    if '.annot.' in f_path:
        continue
    print(f_path)
    subtotal = 0

    fid = open(f_path)
    indict = csv.DictReader(fid,dialect='excel-tab')

    for i,line in enumerate(indict):
        #path = line['filepath']
        size = line['size']
        #dupe = line['dupe']
        #path_list = path.split('/')
        #if len(path_list)>4 and path_list[4] in subdirs and dupe != 'True':
        total_size += int(size)
        subtotal += int(size)
        if i%1000000 == 0:
            print (int(i/1e6))
    print ('mount total: %d  %7.3f'%(subtotal,subtotal/1.1e12))
print ('global total: %d  %7.3f'%(total_size,total_size/1.1e12))

