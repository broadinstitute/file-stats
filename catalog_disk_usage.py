'''
Given a directory to begin from, and a directory to write an output file into, gather metadata about all files within that directory. 
Walks all subdirectories.

To Do:
- Additional data to collect: permissions (group name, group readable? others readable?), soft links.

- Mitigate bad characters in the filenames, eg newline, tab, doublequote, others that are not allowed as bucket object names.

- Tag second and following hard links to the same inode. (desirable but might be memory intensive)

- Fix bug that caused scan to miss 5% of the files on cga_home, compared to IBM Spectrum. (https://docs.google.com/spreadsheets/d/1OQIcKYJfL8oO2wTtVP9TrfyWPA55Iurf1Bv6vXiWS9E/edit#gid=0)

- Fix memory leak that causes RAM consumption to hit 30GB (maybe just by moving to 3.x)

-----------
Changes:
- Removed one of the stat calls because its output wasn't used.
- Added group name in report.
- Reports group name, if available, or just as id (via try/catch same as for uid). 
- Changed stat to lstat, so symlinks are not followed.
- Refactor, coupling the fieldnames with value retrievals, to prevent sync problem as this code is modified. (Build as Dict)
- Parameterize the paths, maybe putting them at the top of this file. 
- Improve performance by stat'ing each file once rather than twice.
- Report whether group readable and whether world readable.
- Report whether a symlink.
-----------
Pete's additional To Do:
- Create output path if does not exist.
'''

import os
import sys
import csv
import stat  # The stat.py module, not os.stat() method.
import pwd  # To retrieve user name using uid.
import grp  # To retrieve group name using gid.
import collections
import argparse

#requires use .genetorrent-3.8.3

scr = sys.argv[0]  # Name of this program as it was invoked.
scr = os.path.abspath(scr)  # Include the full path of the invoked command.
scr_list = scr.split('/')  # Create a list from the directory names of the path.
util_path = '/'.join(scr_list[:-4] + ['trunk','Python','util'])  # Create a string /trunk/Python/util.
sys.path.append(util_path)  # Postpend the util path to the current shells PATH environment variable. 

# output_prefix = "/broad/hptmp/ragone/disk_clearing_2019/"  # Path must exist.

cga_util_path = "/xchip/cga_home/gsaksena/svn/CancerGenomeAnalysis/trunk/Python/util/"
sys.path.append(cga_util_path)

import cga_util

####################################################################
# Accept the start directory and the directory for the output file
####################################################################

parser = argparse.ArgumentParser(description='Catalog metadata of files within a given directory')
parser.add_argument('-r', '--rootdir', help='Top directory to begin from')
parser.add_argument('-o', '--outpath', help='Directory in which to put the catalog file.')
parser.add_argument('-v', '--verbose', help='Report status', action="store_true")  # Verbose mode on if designated, off if absent. 
parser.add_argument('-d', '--debug', help='Debug mode', action="store_true")  # Debug mode on if designated, off if absent. 
args=parser.parse_args()

####################################################################
# Utility functions
####################################################################

def initialize_csv(outpath, info_list):
    with open(outpath,'w', newline='') as csvfile:  # Per recommendation https://docs.python.org/3/library/csv.html
        fieldnames = info_list[0].keys()
        outdict = csv.DictWriter(csvfile,dialect='excel-tab',lineterminator= '\n',fieldnames=fieldnames,quoting=csv.QUOTE_NONE)
        outdict.writeheader()

def write_to_csv(outpath, info_list):
    with open(outpath,'a', newline='') as csvfile:  # Per recommendation https://docs.python.org/3/library/csv.html
        fieldnames = info_list[0].keys()
        outdict = csv.DictWriter(csvfile,dialect='excel-tab',lineterminator= '\n',fieldnames=fieldnames,quoting=csv.QUOTE_NONE,escapechar='\\')
        outdict.writerows(info_list)

def get_login_name(id):
    try:
        uid_struct = pwd.getpwuid(id)
        login_name = uid_struct[0]
#        owner = uid_struct[4]
    except:
        login_name = str(id)
#        owner = str(id)
    return login_name
    
def get_group_name(id):  # id of group that owns file. An int
    try:
        gid_struct = grp.getgrgid(id)
        group_name = gid_struct[0]
#        group = gid_struct[2]
    except:
        group_name = str(id)
#        group = str(id)
    return group_name

def get_group_readable(mode):
#    mode_string = stat.filemode(mode)  # String of form -rwxrwxrwx
#    return mode_string[4]
    return bool(mode & stat.S_IRGRP)  # Boolean and with mask for group readable.

def get_all_readable(mode):
#    mode_string = stat.filemode(mode)  # String of form -rwxrwxrwx
#    return mode_string[7]
    return bool(mode & stat.S_IROTH)  # Boolean and with mask for others-readable.


def get_inode_str(inode):
    return '"%d"'%inode


####################################################################
# Walk the directories and build the file information.
####################################################################

def catalog_disk_usage(rootdir, outpath):
    file_info_list = []
    i = 0
    new_file = True
#    fieldnames = ['filepath','size','ext','last_access','last_modified','username','nlink','inode','groupname','parentdir0','parentdir1','parentdir2','parentdir3']

    for (basedir, dirs, fns) in os.walk(rootdir):

        if args.debug:
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
#            if stat.S_ISLNK(statinfo.st_mode):  # Ignore file because it is a symlink.  
#                continue
            
            file_info = collections.OrderedDict({  # Py 3.6 dicts are ordered, but do this to ensure order in any py version.
                "filepath": filepath.replace('\n',r'\n'),
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
            })
                
            #if not stat.S_ISREG(statinfo.st_mode):
                #continue

            file_info_list.append(file_info)

            if args.verbose and (i % 1000 == 0):  # Track progress by viewing occasional output. 
                print(i)

            if i%10000 == 0:  # Write to file in batches, trying to maximize efficiency.
                if new_file == True:
                    initialize_csv(outpath, file_info_list)
                write_to_csv(outpath, file_info_list)
                file_info_list = []
                new_file = False

            i += 1
            #size? link/dir/file?

    write_to_csv(outpath, file_info_list)


####################################################################
# Main
####################################################################

if __name__ == '__main__':
    rootdir = args.rootdir
    output_prefix = args.outpath
    #outpath = sys.argv[2]
    #rootdir = '/cga/fh/pcawg_pipeline'
    #outpath = '/xchip/cga_home/gsaksena/prj/2014/disk_clearing_2014-11-23/cga_fh_pcawg_pipeline_2015-02-20.txt'
    #rootdir = '/cgaext/tcga'
    #outpath = '/xchip/cga_home/gsaksena/prj/2014/disk_clearing_2014-11-23/cgaext_tcga_2015-04-20.txt'
    #rootdir = '/cga/fh'
    #outpath = '/xchip/cga_home/gsaksena/prj/2014/disk_clearing_2014-11-23/cga_fh_2015-03-30.txt'

    #rootdir='/opt2'
    #outpath = '/opt2/usage.txt'
    
    rootdir_cleaned = rootdir.replace('/','_')
    rootdir_cleaned = rootdir_cleaned[1:]
#    outpath = '/xchip/cga_home/gsaksena/prj/2014/disk_clearing_2014-11-23/' + rootdir_cleaned + '_' + cga_util.get_timestamp() + '.txt'
    outpath = output_prefix + rootdir_cleaned + '_' + cga_util.get_timestamp() + '.txt'
    
    catalog_disk_usage(rootdir, outpath)
 

