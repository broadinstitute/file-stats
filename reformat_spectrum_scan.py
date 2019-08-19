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
outfile = "/sysman/scratch/apsg/alosada/gsaksena/cgastorage/old/scans_a/xchip_cga_reformatted_ibm_b__2019_07_26__12_00_00.files.txt"
userdb_path = '/sysman/scratch/apsg/alosada/gsaksena/dev/users.csv' #'../users.csv'



def convert_date(date_in):
    #in 2010-09-01 17:45:36.0
    #out 2019_05_23__18_14_50
    d=date_in
    date_out = '%s_%s_%s__%s_%s_%s'%(d[:4], d[5:7], d[8:10], d[11:13], d[14:16], d[17:19])
    if date_out[0] != '2':
        raise Exception('Invalid date: %s'%date_in)
    return date_out

def get_read_permission(permission_string, permission_type):
    # permission string format: -rw-r--r--
    if permission_type == 'group':
        permission_bit = permission_string[4]
    elif permission_type == 'all':
        permission_bit = permission_string[7]
    read_permission = str(permission_bit == 'r') # 'True' or 'False'
    if read_permission:
        return '1'
    else:
        return '0'

def fix_filepath(filepath):
    # Replace problematic characters with their escaped version, so the process is fully reversible
    fixed_filepath = ascii(filepath) # escape most problematic chars, eg \n,\r,\t, foreign chars, except quotes
    # space, &, #, etc that are meaningful to the shell are still there, so result will still need to be quoted if sent to the shell.
    fixed_filepath = fixed_filepath[1:-1] # remove surrounding quotes added by ascii()
    # escape single and double quotes left by ascii() in a consistent way that nothing downstream should complain about.
    fixed_filepath = fixed_filepath.replace(r"\'", r"\x27") # case used for sq if dq also in path
    fixed_filepath = fixed_filepath.replace(r"'",  r"\x27") # case used for sq if dq not in path
    fixed_filepath = fixed_filepath.replace(r'\"', r"\x22") # case should never be used
    fixed_filepath = fixed_filepath.replace(r'"',  r"\x22") # dq case

    if filepath != fixed_filepath:
        filepath_escaped = '1'
    else:
        filepath_escaped = '0'

    return fixed_filepath, filepath_escaped


login_by_userid = {}
username_by_login = {}
with open(userdb_path) as fid:
    reader = csv.reader(fid,dialect='excel')
    for line in reader:
        login_by_userid[line[0]] = line[1]
        username_by_login[line[1]] = line[2]

with open(infile, 'r') as csvfile:
#with open(infile, 'r', encoding='ascii', errors='backslashreplace') as csvfile:
    with open(outfile,'w') as ofid:

        fieldnames = ['filepath', 'size', 'last_access', 'last_modified', 'username', 'groupname', 'group_readable',
                      'all_readable', 'symlink', 'nlink', 'inode', 'dupe', 'filepath_escaped']
        writer = csv.DictWriter(ofid, dialect='excel-tab', lineterminator='\n', fieldnames=fieldnames, restval='NA')
        writer.writeheader()

        reader = csv.DictReader(f=csvfile,dialect='excel')
        in_fieldnames = reader.fieldnames
        num_in_fieldnames = len(in_fieldnames)
        for i,line in enumerate(reader):
            if i%1000000 == 0:
                print(i)

            if len(line) != num_in_fieldnames:
                print ('num_fieldnames mismatch: %s'%line)
                continue
            try:
                #TBD symlink, nlink, dupe fields
                filepath = line['PATH']  + line['FILENAME']
                fixed_filepath, filepath_escaped = fix_filepath(filepath)
                user_id = line['OWNER']
                user_login = login_by_userid.get(user_id,user_id)
                oline = {
                    'filepath':line['PATH']  + line['FILENAME'],
                    'size':line['SIZE'],
                    'last_access':convert_date(line['ATIME']),
                    'last_modified':convert_date(line['MTIME']),
                    'username':user_login,
                    'groupname':line['GROUP'],
                    'group_readable':get_read_permission(line['PERMISSIONS'],'group'),
                    'all_readable':get_read_permission(line['PERMISSIONS'],'all'),
                    'inode':'i' + line['INODE'],
                    'filepath_escaped':filepath_escaped,
                }
                writer.writerow(oline)
            except:
                # exceptions on /xchip/cga caused by comma  in filename
                print('parse error %s'%line)
