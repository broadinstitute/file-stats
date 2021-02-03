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
import cProfile


####################################################################
# Global variables
####################################################################

debug = False
verbose = False
inodeset = set()  # For tracking hard linked files.
group_name_by_id = {}


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



def write_to_csv(outpath, info_list, new_file):
    if info_list == []:
        return
    fieldnames = info_list[0].keys() #assume keys already sorted appropriately
    if new_file:
        with open(outpath, 'w') as csvfile:
            outdict = csv.DictWriter(csvfile, dialect='excel-tab', lineterminator='\n', fieldnames=fieldnames)
            outdict.writeheader()

    with open(outpath,'a') as csvfile:
        outdict = csv.DictWriter(csvfile,dialect='excel-tab',lineterminator='\n',fieldnames=fieldnames)
        #try:
        outdict.writerows(info_list)
        #except:
        #    print(info_list)
        #    sys.exit(1)

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
    fixed_filepath = fixed_filepath.replace(r',',  r"\x2c") # comma - won't hurt us, but may mess up other downstream stuff

    if filepath != fixed_filepath:
        filepath_escaped = '1'
    else:
        filepath_escaped = '0'

    return fixed_filepath, filepath_escaped


def fix_filepath_old(filepath):
    fixed_filepath = filepath.replace('\n',r'\n')  # Add more fixes, perhaps from ejon and Sam Novod experiences.
    fixed_filepath = fixed_filepath.replace('\t',r'\t')
    fixed_filepath = fixed_filepath.replace('"',r'\"')
# Now remove all characters not in a whitelist. 
    fixed_filepath = re.sub('[^a-zA-Z0-9_\. \/\\\-]','', fixed_filepath )
    return fixed_filepath

def get_login_name(id):
    global login_by_userid

    login_name = login_by_userid.get(id)
    if login_name is None:
        try:
            uid_struct = pwd.getpwuid(id)
            login_name = uid_struct[0]
        except:
            login_name = str(id)
        login_by_userid[id] = login_name  # add to cache
    return login_name
    
def get_group_name(id):  # id of group that owns file. An int

    group_name = group_name_by_id.get(id)
    if group_name is None:
        try:
            gid_struct = grp.getgrgid(id)
            group_name = gid_struct[0]
        except:
            group_name = str(id)
        group_name_by_id[id] = group_name
    return group_name

def get_group_readable(mode):
    if bool(mode & stat.S_IRGRP): # Boolean and with mask for group readable.
        group_readable = '1'
    else:
        group_readable = '0'
    return group_readable

def get_all_readable(mode):
    if bool(mode & stat.S_IROTH):  # Boolean and with mask for others-readable.
        all_readable = '1'
    else:
        all_readable = '0'
    return all_readable

def get_is_symlink(mode):
    if stat.S_ISLNK(mode):
        is_symlink = '1'
    else:
        is_symlink = '0'
    return is_symlink

def get_inode_str(inode):
    # prepend a non-numeric character to force downstream sw to recognize inode as a string, not something that would be clever to convert to floating point.
    return 'i%d'%inode

def get_dupe_boolean(numlinks,inodenum):
    dupe = '0'
    if numlinks > 1:
        if inodenum in inodeset:
            dupe = '1'
        else:
            inodeset.add(inodenum)
    return dupe

def skip_dir(basedir, subdir):
    do_all = False
    


    if do_all:
        return False

    if subdir.endswith('-genepattern') or \
        subdir == 'tags' and basedir.endswith('CancerGenomeAnalysis') or \
        subdir == 'outfolder' and basedir == '/xchip/cga_home/zlin/CLL_PO1/Curveball/python_scripts' :
        return True
    return False

info_by_dir = {}
dir_stats = []
global dir_new_file
dir_new_file = True

def process_new_dir(basedir, outpath_dirs):
    # assumes topdown=True processing
    # call with '' at the end for final flush

    global dir_new_file
    (fixed_basedir, filename_escaped) = fix_filepath(basedir)
    # identify dirs that are done, ie dirs in our list that are not parents of the current dir
    completed_dirs = []
    for dir in info_by_dir:
        if not fixed_basedir.startswith(dir):
            completed_dirs.append(dir)

    # flush completed dirs as we go, keep just active parent dirs around
    for dir in completed_dirs:
        #print("%s: size %d count %d last_access %s last_modified %s "%(dir,info_by_dir[dir]['size'],info_by_dir[dir]['file_count'],info_by_dir[dir]['last_access'],info_by_dir[dir]['last_modified']))
        dir_stat = {
            'dir': dir,
            'size': info_by_dir[dir]['size'],
            'numfiles': info_by_dir[dir]['file_count'],
            'last_access': info_by_dir[dir]['last_access'],
            'last_modified': info_by_dir[dir]['last_modified'],
        }
        dir_stats.append(dir_stat)
        del info_by_dir[dir]

    # add new dir
    info_by_dir[fixed_basedir] = collections.Counter()
    # Give date fields a string to sort on
    info_by_dir[fixed_basedir]['last_access'] = '0'
    info_by_dir[fixed_basedir]['last_modified'] = '0'

    # flush to disk when we have built up enough
    if len(dir_stats) >= 1000000 or basedir == '':
        # sort what we've got by dirname, which might not be the whole disk worth
        table = {}
        for dir_stat in dir_stats:
            table[dir_stat['dir']] = dir_stat
        keys = list(table.keys())
        keys.sort()
        table2 = []
        for key in keys:
            line = table[key]
            table2.append(line)
        # dump the sorted info
        write_to_csv(outpath_dirs, table2, dir_new_file)
        dir_new_file = False
        # clear the list for more
        dir_stats.clear()


def process_new_file(filesize, last_access, last_modified):
    # add this file to the stats of all parent directories
    # TBD would be nice to add more detailed stats on dates, and stats on file owners

    for dir in info_by_dir:
        info_by_dir[dir]['size'] += filesize
        info_by_dir[dir]['file_count'] += 1
        if last_access > info_by_dir[dir]['last_access']:
            info_by_dir[dir]['last_access'] = last_access
        if last_modified > info_by_dir[dir]['last_modified']:
            info_by_dir[dir]['last_modified'] = last_modified



####################################################################
# Walk the directories and build the file information.
####################################################################

def catalog_disk_usage(rootdir, outpath_files, outpath_dirs, outpath_symlinks):
    global verbose
    file_info_list = []
    symlink_info_list = []
    i = 0
    new_file = True
    symlink_new_file = True

    for (basedir, subdirs, fns) in os.walk(rootdir[:-1], topdown=True):

        if debug:
            if i>1000:  # Stop short because we're just debugging.
                break  #break


        if verbose:
            print('dir; %s'%basedir)

        # remove problematic directories from scan
        skip_subdirs = []
        for subdir in subdirs:
            if skip_dir(basedir, subdir):
                skip_subdirs.append(subdir)
        if skip_subdirs:
            for subdir in skip_subdirs:
                subdirs.remove(subdir)
        subdirs.sort() # might as well walk tree in a predictable order

        process_new_dir(basedir, outpath_dirs)


        for fn in fns:
            i += 1
            filepath = os.path.join(basedir,fn)
            
            try:
                statinfo = os.lstat(filepath)  # Want lstat because that does not follow symlinks.
            except:
                print('lstat error on %s'%filepath)
                continue

            (fixed_filepath, filepath_escaped) = fix_filepath(filepath)
            if stat.S_ISLNK(statinfo.st_mode):
                link_target = os.path.realpath(filepath)
                (fixed_link_target, link_target_escaped) = fix_filepath(link_target)
                symlink_info = collections.OrderedDict({
                    "filepath": fixed_filepath,
                    "target": fixed_link_target,
                    "filepath_escaped": filepath_escaped,
                    "target_escaped": filepath_escaped,
                })
                symlink_info_list.append(symlink_info)

                if len(symlink_info_list) >= 1000:
                    write_to_csv(outpath_symlinks,symlink_info_list,symlink_new_file)
                    symlink_new_file = False
                    symlink_info_list.clear()

            elif stat.S_ISREG(statinfo.st_mode):  # Only report for regular files

                filesize = statinfo.st_size
                # filesize is actual consumeb bytes.  matches Google bucket charges, and 'byte_usage_no_overhead' in Bitstore
                last_access = cga_util.get_timestamp(statinfo.st_atime)
                last_modified = cga_util.get_timestamp(statinfo.st_mtime)
                process_new_file(filesize, last_access, last_modified)
                #TODO - allocated disk space as st_blksize * st_blocks
                # This matches 'dr_byte_usage' but not 'byte_usage' which billing currently uses
                # Doesn't make much sense to give block-based usage if billing doesn't use that either
                #size_allocated = statinfo.st_blksize * statinfo.st_blocks

                file_info = collections.OrderedDict({  # Py 3.6 dicts are ordered, but do this to ensure order in any py version.
                    "filepath": fixed_filepath,
                    "size": str(filesize),
                    "last_access": last_access,
                    "last_modified": last_modified,
                    "uid": statinfo.st_uid,
                    "username": get_login_name(statinfo.st_uid),
                    "gid": statinfo.st_gid,
                    "groupname": get_group_name(statinfo.st_gid),
                    "group_readable": get_group_readable(statinfo.st_mode),
                    "all_readable": get_all_readable(statinfo.st_mode),
                    "symlink": get_is_symlink(statinfo.st_mode),
                    "nlink": statinfo.st_nlink,
                    "inode": get_inode_str(statinfo.st_ino),
                    "dupe": get_dupe_boolean(statinfo.st_nlink,get_inode_str(statinfo.st_ino)),
                    "filepath_escaped": filepath_escaped,
                    #"size_allocated": size_allocated
                })

                file_info_list.append(file_info)

                if verbose: # and (i % 1000 == 0):  # Track progress by viewing occasional output.
                    print("%d: %s"%(i,fixed_filepath))

                if i%100000 == 0:  # Write to file in batches to keep file usually with complete lines
                    print("%d: %s"%(i,fixed_filepath))
                    write_to_csv(outpath_files, file_info_list, new_file)
                    new_file = False
                    file_info_list = []


    write_to_csv(outpath_files, file_info_list, new_file)
    if len(symlink_info_list) > 0:
        write_to_csv(outpath_symlinks, symlink_info_list, symlink_new_file)
    elif symlink_new_file:
        # if no symlinks, make a stub file with just the header
        with open(outpath_symlinks,'w') as ofid:
            #TODO - clean up this bad form- header fields need to be kept in sync with above
            ofid.write('filepath\ttarget\tfilepath_escaped\ttarget_escaped\n')
    # finish dir processing
    process_new_dir('',outpath_dirs)


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
    outpath = args.outpath
    
# Quick and dirty file paths fix.
    if rootdir[-1] != '/':
        rootdir += '/'
    if outpath[-1] != '/':
        outpath += '/'

    rootdir_cleaned = rootdir.replace('/','_')
    rootdir_cleaned = rootdir_cleaned[1:]
    outpath_prefix = outpath + rootdir_cleaned + '_' + cga_util.get_timestamp()
    outpath_files = outpath_prefix + '.files.txt'
    outpath_dirs = outpath_prefix + '.dirs.txt'
    outpath_symlinks = outpath_prefix + '.symlinks.txt'
    outpath_files_part = outpath_files + '.part'
    outpath_dirs_part = outpath_dirs + '.part'
    outpath_symlinks_part = outpath_symlinks + '.part'

    global login_by_userid
    login_by_userid = {}
    username_by_login = {}
    userdb_path = '/sysman/scratch/apsg/alosada/gsaksena/dev/users.csv' #'../users.csv'
    with open(userdb_path) as fid:
        reader = csv.reader(fid,dialect='excel')
        for line in reader:
            login_by_userid[line[0]] = line[1]
            username_by_login[line[1]] = line[2]
    
    catalog_disk_usage(rootdir, outpath_files_part, outpath_dirs_part, outpath_symlinks_part)

    # strip .part from output filenames
    os.rename(outpath_files_part, outpath_files)
    os.rename(outpath_dirs_part, outpath_dirs)
    os.rename(outpath_symlinks_part, outpath_symlinks)


if __name__ == '__main__':
    main()

    #cProfile.run('main()')