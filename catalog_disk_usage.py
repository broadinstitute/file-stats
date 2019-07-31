#!/bin/env python

'''
Given a directory to begin from, and a directory to write an output file into, gather metadata about all files within that directory. 
Walks all subdirectories.

To Do:

- Create functions to validate the input file paths. Also add a trailing slash only if missing.
- For all code that modifies input values or values read from system, insert into new var name, do not change original.
- Set a default output path, perhaps to current working directory, or else make output path a required option.
- Try creating the designated output path if it is designated and does not exist.
- Make this file runnable as a command.
- Consider adding a log file option.
- If log file option exists, add error writing to there for failure of (try lstat).
    - What is good practice --  Designating a log file path writes errors to a log at that path, otherwise they silently fail?

-----------
Changes:
- Mitigate bad characters such as *!"#$%&'()/:;<=>?@[]\^`{|}~ by using whitelist.
- Remove any meta character. Ejon saw a ^M in some files. 
- Removed one of the stat calls because its output wasn't used.
- Added group name in report.
- Reports group name, if available, or just as id (via try/catch same as for uid). 
- Changed stat to lstat, so symlinks are not followed.
- Refactor, coupling the fieldnames with value retrievals, to prevent sync problem as this code is modified. (Build as Dict)
- Parameterize the paths, maybe putting them at the top of this file. 
- Improve performance by stat'ing each file once rather than twice.
- Report whether group readable, whether world readable, whether a symlink.
- Report whether a symlink.
- Make designating the root directory a required option.
- Make designating the output directory a required option.
- Make inode output the int quoted with single quotes.
- Fix the file path arguments so they accommodate a trailing slash and an absent trailing slash. 
- Also replace tabs in filenames
- Tag second and following hard links to the same inode. (desirable but might be memory intensive)
- SEEMS FIXED - Fix bug that caused scan to miss 5% of the files on cga_home, compared to IBM Spectrum. (https://docs.google.com/spreadsheets/d/1OQIcKYJfL8oO2wTtVP9TrfyWPA55Iurf1Bv6vXiWS9E/edit#gid=0)
- SEEMS FIXED - Fix memory leak that causes RAM consumption to hit 30GB (maybe just by moving to 3.x)
'''

# TESTED USING PYTHON 3.7.3 (from Dotkit .anaconda3-5.3.1
# N.B. - Dict in Python 3.6+ is ordered by default. 

import os
import sys
import csv
import stat  # The stat.py module, not os.stat() method.
import pwd  # To retrieve user name using uid.
import grp  # To retrieve group name using gid.
import collections
import argparse
import cga_util  # Be sure to put cga_util in a findable location.
import re


####################################################################
# Global variables
####################################################################

debug = False
verbose = False
inodeset = set()  # For tracking hard linked files. 


####################################################################
# Accept the start directory and the directory for the output file
####################################################################

def parse_args():
    parser = argparse.ArgumentParser(description='Catalog metadata of files within a given directory')
    parser.add_argument('-r', '--rootdir', required=True, help='Top directory to begin from')
    parser.add_argument('-o', '--outpath', required=True, help='Directory in which to put the catalog file.')
    parser.add_argument('-v', '--verbose', help='Report status', action="store_true")  # Verbose mode on if designated, off if absent. 
    parser.add_argument('-d', '--debug', help='Debug mode', action="store_true")  # Debug mode on if designated, off if absent. 
    args=parser.parse_args()
    return args

####################################################################
# Utility functions
####################################################################

def initialize_csv(outpath, info_list):
    with open(outpath,'w', newline='') as csvfile:  # Per recommendation https://docs.python.org/3/library/csv.html
        fieldnames = info_list[0].keys()
        outdict = csv.DictWriter(csvfile,dialect='excel-tab',lineterminator='\n',fieldnames=fieldnames,quoting=csv.QUOTE_NONE)
        outdict.writeheader()

def write_to_csv(outpath, info_list):
    with open(outpath,'a', newline='') as csvfile:  # Per recommendation https://docs.python.org/3/library/csv.html
        fieldnames = info_list[0].keys()
        outdict = csv.DictWriter(csvfile,dialect='excel-tab',lineterminator='\n',fieldnames=fieldnames,quoting=csv.QUOTE_NONE,quotechar="'",escapechar='\\')
        outdict.writerows(info_list)

def fix_filepath(filepath):
    fixed_filepath = filepath.replace('\n',r'\n')  # Add more fixes, perhaps from ejon and Sam Novod experiences.
    fixed_filepath = fixed_filepath.replace('\r',r'\r')
    fixed_filepath = fixed_filepath.replace('\t',r'\t')
    fixed_filepath = fixed_filepath.replace('"',r'\"')
# Now remove all characters not in a whitelist. 
    fixed_filepath = re.sub('[^a-zA-Z0-9_\. \/\\\-]','', fixed_filepath )
    return fixed_filepath

def get_login_name(id):
    try:
        uid_struct = pwd.getpwuid(id)
        login_name = uid_struct[0]
    except:
        login_name = str(id)
    return login_name
    
def get_group_name(id):  # id of group that owns file. An int
    try:
        gid_struct = grp.getgrgid(id)
        group_name = gid_struct[0]
    except:
        group_name = str(id)
    return group_name

def get_group_readable(mode):
    return bool(mode & stat.S_IRGRP)  # Boolean and with mask for group readable.

def get_all_readable(mode):
    return bool(mode & stat.S_IROTH)  # Boolean and with mask for others-readable.

def get_inode_str(inode):
    return '"%d"'%inode

def get_dupe_boolean(numlinks,inodenum):
    dupe = False
    if numlinks > 1:
        if inodenum in inodeset:
            dupe = True
        else:
            inodeset.add(inodenum)
    return dupe


####################################################################
# Walk the directories and build the file information.
####################################################################

def catalog_disk_usage(rootdir, outpath):
    file_info_list = []
    i = 0
    new_file = True

    for (basedir, dirs, fns) in os.walk(rootdir):

        if debug:
            if i>1000:  # Stop short because we're just debugging.
                break  #break

        for fn in fns:
            filepath = os.path.join(basedir,fn)
            
            try:
                statinfo = os.lstat(filepath)  # Want lstat because that does not follow symlinks.
            except:
                continue

            if not stat.S_ISREG(statinfo.st_mode):  # Only report for regular files.
                continue

            file_info = collections.OrderedDict({  # Py 3.6 dicts are ordered, but do this to ensure order in any py version.
                "filepath": fix_filepath(filepath),
                "size": str(statinfo.st_size),
                "last_access": cga_util.get_timestamp(statinfo.st_atime),
                "last_modified": cga_util.get_timestamp(statinfo.st_mtime),
                "username": get_login_name(statinfo.st_uid),
                "groupname": get_group_name(statinfo.st_gid), 
                "group_readable": get_group_readable(statinfo.st_mode),
                "all_readable": get_all_readable(statinfo.st_mode),
                "symlink": stat.S_ISLNK(statinfo.st_mode),
                "nlink": statinfo.st_nlink,
                "inode": get_inode_str(statinfo.st_ino),
                "dupe": get_dupe_boolean(statinfo.st_nlink,get_inode_str(statinfo.st_ino))
            })
                
            file_info_list.append(file_info)

            if verbose and (i % 1000 == 0):  # Track progress by viewing occasional output. 
                print(i)

            if i%10000 == 0:  # Write to file in batches, trying to maximize efficiency.
                if new_file == True:
                    initialize_csv(outpath, file_info_list)
                    new_file = False
                write_to_csv(outpath, file_info_list)
                file_info_list = []

            i += 1

    write_to_csv(outpath, file_info_list)


####################################################################
# Main
####################################################################
def main():
    if sys.version_info[0] < 3:
        raise Exception("Must be using Python 3")

    args = parse_args()
    
    global debug
    debug = args.debug
    global verbose
    verbose = args.verbose

    rootdir = args.rootdir
    output_prefix = args.outpath
    
# Quick and dirty file paths fix.
    rootdir += '/'
    output_prefix += '/'

    rootdir_cleaned = rootdir.replace('/','_')
    rootdir_cleaned = rootdir_cleaned[1:]
    outpath = output_prefix + rootdir_cleaned + '_' + cga_util.get_timestamp() + '.txt'
    
    catalog_disk_usage(rootdir, outpath)

if __name__ == '__main__':
    main() 

