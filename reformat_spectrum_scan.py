#!/bin/env python

import os
import sys
import csv

# SAMPLE SPECTRUM DISCOVER OUTPUT
#
# PATH,FILENAME,FILETYPE,DATASOURCE,OWNER,GROUP,REVISION,SITE,PLATFORM,CLUSTER,INODE,PERMISSIONS,FILESET,UID,GID,RECORDVERSION,MIGSTATUS,MIGLOC,MTIME,ATIME,CTIME,TIER,SIZE,FKEY,COLLECTION,TEMPERATURE,DUPLICATE,SIZECONSUMED,TAG1,TAG2
# /ifs/data/x400/cancer/cga/gdac-prod/genepattern/jobResults/399516/scatter.0000000007/3017/,splitreads.helper2,helper2,/ifs/data/x400/cancer/cga,5255,2023,MO1,Broad-hydrogen,NFS,hydrogen-nfs.broadinstitute.org,8520143752,-rw-r--r--,NA,5255,2023,,resdnt,,2010-09-01 17:45:36.0,2013-11-08 01:43:59.0,2018-11-16 07:34:13.0,system,1852,hydrogen-nfs.broadinstitute.org/ifs/data/x400/cancer/cga8520143752,,,,65536,,
#
# SAMPLE CATALOG_DISK_USAGE OUTPUT
#
# filepath	size	last_access	last_modified	username	groupname	group_readable	all_readable	symlink	nlink	inode	dupe
# /xchip/cga/.DS_Store	22532	2019_05_23__18_14_50	2019_03_05__18_17_17	xmu	xchipgrp	True	True	False	1	"8214413417"	False
#



infile = "/sysman/scratch/apsg/alosada/gsaksena/ResultSet1-1.csv"
outfile = "/sysman/scratch/apsg/alosada/gsaksena/dev/file-stats/output_test/xchip_cga_reformatted_ibm__2019_07_26__12_00_00.txt"



def convert_date(date_in):
    #in 2010-09-01 17:45:36.0
    #out 2019_05_23__18_14_50
    d=date_in
    date_out = '%s_%s_%s__%s_%s_%s'%(d[:4], d[5:7], d[8:10], d[11:13], d[14:16], d[17:19])
    return date_out

def get_read_permission(permission_string, permission_type):
    # permission string format: -rw-r--r--
    if permission_type == 'group':
        permission_bit = permission_string[4]
    elif permission_type == 'all':
        permission_bit = permission_string[7]
    read_permission = str(permission_bit == 'r') # 'True' or 'False'
    return read_permission


with open(infile, 'r', encoding='ascii', errors='backslashreplace') as csvfile:
    with open(outfile,'w') as ofid:

        fieldnames = ['filepath', 'size', 'last_access', 'last_modified', 'username', 'groupname', 'group_readable',
                      'all_readable', 'symlink', 'nlink', 'inode', 'dupe']
        writer = csv.DictWriter(ofid, dialect='excel-tab', lineterminator='\n', fieldnames=fieldnames, restval='NA')
        writer.writeheader()

        reader = csv.DictReader(f=csvfile,dialect='excel')
        for i,line in enumerate(reader):
            if i%1000000 == 0:
                print(i)

            try:
                #TBD symlink, nlink, dupe fields
                oline = {
                    'filepath':line['PATH']  + line['FILENAME'],
                    'size':line['SIZE'],
                    'last_access':convert_date(line['ATIME']),
                    'last_modified':convert_date(line['MTIME']),
                    'username':line['OWNER'],
                    'groupname':line['GROUP'],
                    'group_readable':get_read_permission(line['PERMISSIONS'],'group'),
                    'all_readable':get_read_permission(line['PERMISSIONS'],'all'),
                    'inode':line['INODE'],
                }
                writer.writerow(oline)
            except:
                print(line)
